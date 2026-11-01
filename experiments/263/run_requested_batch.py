"""Append-only named-match C0/C1/C3 forward logger (isolated 2.6.3 experiment).

Do not select matches. Accept only *new Git-tracked* requests with explicit user-chosen
home/away names. Independently fetch official fixtures; never accept dates or gate
assertions from a request JSON. No bets, production changes, or historical tests.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from forward_c3 import (canonical_bytes, predict_from_verified_gate,
                        read_aware, sha256_file)

REQUEST_SCHEMA = "c3_named_match_batch_request_v1"
REPORT_SCHEMA = "c3_forward_batch_report_v1"
FROZEN_MODEL_SHA = "1a0c519b6c8f2947de43545fcd0c5d4e8abcc9a4f8b47f8372bee43f53beb96f"
FROZEN_FORWARD_SHA = "9a22a5671e37445957443e2d3b4bb12c8c283e0ea8351777f86f5229aac3d52f"
MAX_MATCHES = 12
REQUEST_NAME = re.compile(r"^experiments/263/requests/[A-Za-z0-9_-]+\.json$")


def load_request(path, repository_root):
    root = Path(repository_root).resolve()
    path = Path(path)
    rel = path.as_posix()
    if not REQUEST_NAME.fullmatch(rel):
        raise ValueError("request_path_outside_approved_queue")
    target = (root / path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise ValueError("request_file_unavailable")
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"schema", "matches"}:
        raise ValueError("bad_request_keys")
    if payload["schema"] != REQUEST_SCHEMA:
        raise ValueError("bad_request_schema")
    matches = payload["matches"]
    if not isinstance(matches, list) or not (1 <= len(matches) <= MAX_MATCHES):
        raise ValueError("bad_match_count")
    seen = set()
    for match in matches:
        if not isinstance(match, dict) or set(match) != {"league", "home", "away"}:
            raise ValueError("bad_match_keys")
        if not all(isinstance(match[k], str) and 1 <= len(match[k].strip()) <= 100
                   for k in ("league", "home", "away")):
            raise ValueError("bad_match_values")
        if match["home"].casefold().strip() == match["away"].casefold().strip():
            raise ValueError("same_team")
        key = (match["league"], match["home"].casefold().strip(), match["away"].casefold().strip())
        if key in seen:
            raise ValueError("duplicate_named_match")
        seen.add(key)
    return payload, hashlib.sha256(target.read_bytes()).hexdigest()


def existing_keys(records_dir):
    """Detect records that already exist, including tampering and shifted kickoffs."""
    keys = set()
    for path in sorted(Path(records_dir).glob("????-??-??/*.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        digest = item.pop("payload_sha256", None)
        if not digest or hashlib.sha256(canonical_bytes(item)).hexdigest() != digest:
            raise ValueError("tampered_existing_forecast:" + str(path))
        item["payload_sha256"] = digest
        fixture = item["fixture"]
        key = (fixture["league"], fixture["home_id"], fixture["away_id"], fixture["match_local_date"])
        if key in keys:
            raise ValueError("duplicated_existing_fixture:" + str(path))
        keys.add(key)
    return keys


def record_batch(request_paths, repository_root, history, records_dir, report_path,
                 lookup=None, now=None):
    """Write one immutable batch audit regardless of success; no silent retries."""
    now = now or datetime.now(timezone.utc)
    now = read_aware(now.isoformat())
    if lookup is None:
        from analyze_named_match_gate import run as lookup
    root = Path(repository_root)
    model_path = root / "experiments/263/exp_263_batch.py"
    forward_path = root / "experiments/263/forward_c3.py"
    if sha256_file(model_path) != FROZEN_MODEL_SHA:
        raise ValueError("frozen_C3_model_hash_mismatch")
    if sha256_file(forward_path) != FROZEN_FORWARD_SHA:
        raise ValueError("frozen_forecast_implementation_hash_mismatch")
    if not request_paths:
        raise ValueError("empty_request_manifest")
    all_matches = []
    requests = []
    for path in request_paths:
        p, digest = load_request(path, root)
        requests.append({"path": str(path), "sha256": digest})
        all_matches.extend(p["matches"])
    if len(all_matches) > MAX_MATCHES:
        raise ValueError("batch_exceeds_limit")
    keys = existing_keys(records_dir)
    outcomes = []
    for match in all_matches:
        outcome = {"requested": match, "status": "BLOCKED"}
        try:
            observed = lookup(match["league"], match["home"], match["away"])
            if not isinstance(observed, dict) or observed.get("status") != "VERIFIED":
                raise ValueError("official_gate_denied:" + str(observed.get("reason") if isinstance(observed, dict) else "invalid_gate"))
            # Only locally generated live gate values are ever used; request has no date/IDs.
            kickoff = read_aware(observed["kickoff_utc"])
            from zoneinfo import ZoneInfo
            from forward_c3 import TIMEZONES
            local_date = kickoff.astimezone(ZoneInfo(TIMEZONES[match["league"]])).date().isoformat()
            key = (observed["league"], observed["home_id"], observed["away_id"], local_date)
            if key in keys:
                outcome["status"] = "ALREADY_REGISTERED_NO_OVERWRITE"
            else:
                path, rec = predict_from_verified_gate(observed, history, records_dir, now=now)
                outcome.update(status="REGISTERED_EXPERIMENTAL", file=path.as_posix(),
                               payload_sha256=rec["payload_sha256"], fixture=rec["fixture"])
                keys.add(key)
        except (OSError, ValueError, KeyError, TypeError) as err:
            outcome.update(status="BLOCKED_NO_FORECAST", reason=str(err)[:240])
        outcomes.append(outcome)
    report = {"schema": REPORT_SCHEMA, "created_at_utc": now.isoformat(), "requests": requests,
              "source_model_sha256": FROZEN_MODEL_SHA, "source_forward_sha256": FROZEN_FORWARD_SHA,
              "statuses": {name: sum(x["status"] == name for x in outcomes)
                           for name in ("REGISTERED_EXPERIMENTAL", "BLOCKED_NO_FORECAST", "ALREADY_REGISTERED_NO_OVERWRITE")},
              "outcomes": outcomes, "production_unchanged": True,
              "note": "A successful GitHub Action proves only that a record was created, not that C3 predicts football reliably."}
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x", encoding="utf-8") as fp:
        json.dump(report, fp, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        fp.write("\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="newline-separated NEW git-added paths")
    parser.add_argument("--history", default="data/historical_results.csv")
    parser.add_argument("--records", default="forward_263")
    parser.add_argument("--report", required=True)
    cli = parser.parse_args()
    paths = [p.strip() for p in Path(cli.manifest).read_text(encoding="utf-8").splitlines() if p.strip()]
    result = record_batch(paths, ".", cli.history, cli.records, cli.report)
    print(json.dumps({"status": result["statuses"], "report": cli.report}, ensure_ascii=False))
    # Empty or entirely blocked batch is an operational failure, not green evidence.
    if not result["statuses"]["REGISTERED_EXPERIMENTAL"]:
        raise SystemExit("NO_NEW_PREDICTIONS; inspect archived batch report. No automatic retries.")


if __name__ == "__main__":
    main()
