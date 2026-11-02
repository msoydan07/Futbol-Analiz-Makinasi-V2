"""User-named four-model forward queue, isolated from the frozen C3 queue.

Only Git-added new request files are accepted by the GitHub workflow.
No autonomous match discovery, fixture JSON, odds, model re-tuning or replay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from forward_c3 import canonical_bytes, read_aware
from forward_quad import predict_quad_from_verified_gate, SCHEMA

REQUEST_SCHEMA = "quad_named_match_batch_request_v1"
REPORT_SCHEMA = "quad_named_match_batch_report_v1"
REQUEST_RE = re.compile(r"^experiments/263/quad_requests/[A-Za-z0-9_-]+\.json$")
MAX_MATCHES = 12


def read_request(relative_path, root):
    rel = Path(relative_path).as_posix()
    if not REQUEST_RE.fullmatch(rel):
        raise ValueError("outside_quad_request_queue")
    home = Path(root).resolve()
    file = (home / rel).resolve()
    if not file.is_relative_to(home) or not file.is_file():
        raise ValueError("request_missing_or_escaped_root")
    request = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(request, dict) or set(request) != {"schema", "matches"}:
        raise ValueError("invalid_request_shape")
    if request["schema"] != REQUEST_SCHEMA:
        raise ValueError("invalid_request_version")
    matches = request["matches"]
    if not isinstance(matches, list) or not (1 <= len(matches) <= MAX_MATCHES):
        raise ValueError("invalid_request_count")
    seen = set()
    for match in matches:
        if not isinstance(match, dict) or set(match) != {"league", "home", "away"}:
            raise ValueError("invalid_match_fields")
        if not all(isinstance(match[k], str) and 1 <= len(match[k].strip()) <= 100
                   for k in ("league", "home", "away")):
            raise ValueError("invalid_match_values")
        key = (match["league"], match["home"].casefold().strip(),
               match["away"].casefold().strip())
        if key[1] == key[2] or key in seen:
            raise ValueError("duplicate_or_same_team")
        seen.add(key)
    return matches, hashlib.sha256(file.read_bytes()).hexdigest()


def prior_keys(records_dir):
    """Reject corrupted or repeated records before allowing an append."""
    keys = set()
    for filename in sorted(Path(records_dir).glob("*/*.json")):
        record = json.loads(filename.read_text(encoding="utf-8"))
        if record.get("schema") != SCHEMA:
            raise ValueError("invalid_existing_record_schema")
        digest = record.pop("payload_sha256", None)
        if not digest or hashlib.sha256(canonical_bytes(record)).hexdigest() != digest:
            raise ValueError("tampered_existing_pilot_record")
        f = record["fixture"]
        key = (f["league"], f["home_id"], f["away_id"], f["match_local_date"])
        if key in keys:
            raise ValueError("duplicate_existing_pilot_fixture")
        keys.add(key)
    if len(keys) > 100:
        raise ValueError("pilot_limit_exceeded")
    return keys


def record_batch(request_paths, *, root, history, baseline, acceptance, lock,
                 records_dir, report_path, lookup=None, now=None):
    now = now or datetime.now(timezone.utc)
    now = read_aware(now.isoformat())
    if not request_paths:
        raise ValueError("empty_new_request_manifest")
    if lookup is None:
        from analyze_named_match_gate import run as lookup
    requests = []
    matches = []
    for request_path in request_paths:
        items, digest = read_request(request_path, root)
        requests.append({"path": str(request_path), "sha256": digest})
        matches.extend(items)
    if len(matches) > MAX_MATCHES or len(set((m["league"], m["home"].casefold(), m["away"].casefold()) for m in matches)) != len(matches):
        raise ValueError("batch_too_large_or_repeated_matches")

    keys = prior_keys(records_dir)
    sources_ready = all(Path(p).is_file() for p in (history, baseline, acceptance, lock))
    results = []
    for match in matches:
        entry = {"requested": match, "status": "BLOCKED_NO_PREDICTION"}
        try:
            # Fresh accepted input is mandatory. Never silently use the October archive
            # as if it contained November's completed matches.
            if not sources_ready:
                raise ValueError("UPDATED_SOURCE_NOT_HUMAN_ACCEPTED_YET")
            gate = lookup(match["league"], match["home"], match["away"])
            if not isinstance(gate, dict) or gate.get("status") != "VERIFIED":
                reason = gate.get("reason", gate.get("status")) if isinstance(gate, dict) else "invalid_gate"
                raise ValueError("LIVE_OFFICIAL_FIXTURE_NOT_VERIFIED:" + str(reason))
            from forward_c3 import valid_gate
            league, home, away, _, _, local_date = valid_gate(gate, now)
            key = (league, home, away, local_date)
            if key in keys:
                entry["status"] = "ALREADY_RECORDED_NOT_OVERWRITTEN"
                results.append(entry)
                continue
            dest, prediction = predict_quad_from_verified_gate(
                gate, history, records_dir, lock, now=now,
                base=baseline, source_audit=acceptance)
            entry.update(status="REGISTERED_FOUR_MODELS_EXPERIMENTAL",
                         path=dest.as_posix(), payload_sha256=prediction["payload_sha256"],
                         fixture=prediction["fixture"])
            keys.add(key)
        except (OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
            entry["reason"] = str(exc)[:280]
        results.append(entry)

    status_counts = {kind: sum(x["status"] == kind for x in results) for kind in (
        "REGISTERED_FOUR_MODELS_EXPERIMENTAL", "ALREADY_RECORDED_NOT_OVERWRITTEN",
        "BLOCKED_NO_PREDICTION")}
    report = {"schema": REPORT_SCHEMA, "created_at_utc": now.isoformat(),
              "requests": requests, "statuses": status_counts, "outcomes": results,
              "accepted_snapshot_required": True, "pilot_goal": 100,
              "production_modified": False, "betting_authorized": False}
    target = Path(report_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--history", required=True)
    p.add_argument("--baseline", required=True)
    p.add_argument("--source-acceptance", required=True)
    p.add_argument("--m4-lock", default="experiments/263/m4_lock.json")
    p.add_argument("--records", default="forward_quad_263")
    p.add_argument("--report", required=True)
    a = p.parse_args()
    request_paths = [s.strip() for s in Path(a.manifest).read_text(encoding="utf-8").splitlines() if s.strip()]
    report = record_batch(request_paths, root=".", history=a.history, baseline=a.baseline,
                          acceptance=a.source_acceptance, lock=a.m4_lock,
                          records_dir=a.records, report_path=a.report)
    print(json.dumps({"statuses": report["statuses"], "report": a.report}, ensure_ascii=False))
    if report["statuses"]["REGISTERED_FOUR_MODELS_EXPERIMENTAL"] == 0:
        raise SystemExit("NO_NEW_VALID_SEALED_RECORDS: inspect preserved report; do not blindly rerun")


if __name__ == "__main__":
    main()
