"""Append-only MANUAL bookmaker odds intake for the 96-candidate future pilot.

This is a human attestation pipeline, NOT a live scraping or price verification
service. It cannot independently verify the bookmaker page or GitHub commit.
Only sealed pre-kickoff four-model predictions can be linked.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from classification_odds_263 import GROUPS, odds_evidence
from forward_c3 import canonical_bytes, read_aware
from forward_quad import PILOT_GOAL
from market_fifth_baseline_263 import OBSERVATION_SCHEMA, fixture_key, sealed_payload
from forward_quad import SCHEMA as FORECAST_SCHEMA

REQUEST_SCHEMA = "263_manual_market_quote_request_v1"
BATCH_SCHEMA = "263_manual_market_quote_batch_report_v1"
ACCEPTED_DOMAINS = frozenset(("iddaa.com", "nesine.com", "bilyoner.com", "mackolik.com"))
ALLOWED_GROUPS = ("MS", "KG", "GOALS_2.5")
REQUEST_RE = re.compile(r"^experiments/263/market_quote_requests/[A-Za-z0-9_-]+\.json$")
FORECAST_RE = re.compile(r"^forward_quad_263/(2026-11-0[678])/([0-9a-f]{24})\.json$")
MAX_BATCH = 12


def _domain(url: str) -> str:
    if not isinstance(url, str):
        raise ValueError("SOURCE_URL_MISSING")
    u = urlparse(url)
    host = (u.hostname or "").lower().removeprefix("www.")
    if (u.scheme != "https" or u.username or u.password
            or host not in ACCEPTED_DOMAINS):
        raise ValueError("UNACCEPTED_OR_NON_HTTPS_BOOKMAKER_URL")
    return host


def _inside(relative: str, root: Path) -> Path:
    p = (root / relative).resolve()
    if not p.is_relative_to(root.resolve()) or not p.is_file():
        raise ValueError("MISSING_OR_ESCAPED_REPOSITORY_FILE")
    return p


def _valid_price(v) -> float:
    if (isinstance(v, bool) or not isinstance(v, (float, int))
            or not math.isfinite(v) or not 1 < v <= 1000):
        raise ValueError("INVALID_DECIMAL_ODDS")
    return float(v)


def ingest_one(relative_path: str, *, root: Path, output_dir: Path, now: datetime) -> dict:
    """Build one snapshot from a genuine human-supplied quote request.

    now must come from a trusted runtime clock, not an input field.
    The data itself is not automatically authenticated against bookmaker pages.
    """
    if not REQUEST_RE.fullmatch(relative_path):
        raise ValueError("WRONG_REQUEST_PATH")
    if now.tzinfo is None:
        raise ValueError("AWARE_RUNTIME_REQUIRED")
    now = now.astimezone(timezone.utc)
    request_path = _inside(relative_path, root)
    req = json.loads(request_path.read_text(encoding="utf-8"))
    allowed = {"schema", "forecast_path", "source_url", "source_domain",
               "reviewer", "reviewed_at_utc", "observed_at_utc",
               "visible_source_note", "market_prices"}
    if not isinstance(req, dict) or set(req) != allowed or req["schema"] != REQUEST_SCHEMA:
        raise ValueError("INVALID_REQUEST_SCHEMA_OR_FIELDS")
    match = FORECAST_RE.fullmatch(req["forecast_path"]) if isinstance(req["forecast_path"], str) else None
    if not match:
        raise ValueError("NOT_A_WEEKEND_PILOT_FORECAST_PATH")
    domain = _domain(req["source_url"])
    if req["source_domain"] != domain:
        raise ValueError("SOURCE_DOMAIN_AND_URL_DIFFER")
    if not isinstance(req["reviewer"], str) or not (2 <= len(req["reviewer"].strip()) <= 100):
        raise ValueError("HUMAN_REVIEWER_REQUIRED")
    note = req["visible_source_note"]
    if not isinstance(note, str) or not (15 <= len(note.strip()) <= 1000):
        raise ValueError("MANUAL_VISIBLE_SOURCE_NOTE_REQUIRED")
    observed, reviewed = read_aware(req["observed_at_utc"]), read_aware(req["reviewed_at_utc"])
    if not reviewed <= observed <= now:
        raise ValueError("OBSERVATION_TIMES_IN_FUTURE_OR_REVERSED")
    if (now - observed).total_seconds() > 600:
        raise ValueError("SOURCE_ODDS_STALE_MORE_THAN_10_MINUTES")
    forecast = json.loads(_inside(req["forecast_path"], root).read_text(encoding="utf-8"))
    sha = sealed_payload(forecast, FORECAST_SCHEMA)
    fx = forecast["fixture"]
    ko = read_aware(fx["kickoff_utc"])
    created = read_aware(forecast["created_at_utc"])
    fixture_checked = read_aware(fx["source_checked_at_utc"])
    if (fx.get("fixture_verification") != "VERIFIED_BY_LIVE_OFFICIAL_GATE"
            or not fixture_checked <= created <= reviewed <= observed <= now < ko):
        raise ValueError("NOT_AUTHENTIC_PREGAME_SEQUENCE")
    if fx["match_local_date"] != match.group(1):
        raise ValueError("FORECAST_PATH_LOCAL_DATE_MISMATCH")
    if set(forecast.get("model_predictions", {})) != {"B", "C2", "C3", "M4"}:
        raise ValueError("FOUR_MODEL_OUTPUTS_REQUIRED")
    market_prices = req["market_prices"]
    if (not isinstance(market_prices, dict) or not market_prices
            or not set(market_prices).issubset(ALLOWED_GROUPS)):
        raise ValueError("UNSUPPORTED_OR_EMPTY_MARKET_SET")
    key = fixture_key(fx)
    quotes = {}
    for group in ALLOWED_GROUPS:
        if group not in market_prices:
            continue
        values = market_prices[group]
        if not isinstance(values, dict) or set(values) != set(GROUPS[group]):
            raise ValueError("INCOMPLETE_OR_WRONG_OPPOSITE_PRICES_"+group)
        clean = {k: _valid_price(values[k]) for k in GROUPS[group]}
        quote = {
            "fixture_key": key, "market_group": group,
            "verification": "INDEPENDENTLY_CHECKED",  # Human ATTESTATION flag; not network proof.
            "stage": "PREMATCH",
            "source": domain, "source_url": req["source_url"],
            "checked_at_utc": observed.isoformat(),
            "decimal_odds": clean,
        }
        statuses = [odds_evidence(k, quote, key, ko.isoformat(), now.isoformat())
                    for k in GROUPS[group]]
        if any(s["status"] != "COMPLETE_PREMATCH_QUOTES_SOURCE_FLAGGED_AS_CHECKED"
               for s in statuses):
            raise ValueError("PRICE_GROUP_FAILS_EXISTING_CONTRACT_"+group)
        quotes[group] = quote
    payload = {
        "schema": OBSERVATION_SCHEMA,
        "fixture_key": key,
        "forecast_payload_sha256": sha,
        "analysis_at_utc": now.isoformat(),
        "source_domain": domain,
        "source_review": {
            "method": "MANUAL_PUBLIC_PAGE",
            "reviewer": req["reviewer"].strip(),
            "reviewed_at_utc": reviewed.isoformat(),
            "visible_source_note": note.strip(),
            "request_path": relative_path,
            "request_file_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
        },
        "quotes": quotes,
        "evidence_scope": "HUMAN_ATTESTED_NOT_EXTERNALLY_REVERIFIED",
        "price_provider_api_connected": False,
        "true_webpage_price_not_proven_by_code": True,
        "betting_authorized": False,
    }
    payload["payload_sha256"] = hashlib.sha256(
        canonical_bytes(payload | {})[:-0] if False else canonical_bytes(payload)
    ).hexdigest()
    destination = output_dir / fx["match_local_date"] / (match.group(2) + ".json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # An attempt to replace a stored quote for the same match is rejected.
    with destination.open("x", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        file.write("\n")
    return {
        "status": "MANUAL_ATTESTATION_SEALED_LOCALLY_AWAIT_GITHUB_PREKO_COMMIT",
        "path": destination.as_posix(),
        "fixture_key": key,
        "forecast_sha256": sha,
        "payload_sha256": payload["payload_sha256"],
        "market_groups": list(quotes),
    }


def ingest_batch(requests: list[str], *, root: Path, output_dir: Path,
                 report_path: Path, now: datetime) -> dict:
    if not 1 <= len(requests) <= MAX_BATCH or len(set(requests)) != len(requests):
        raise ValueError("INVALID_BATCH_SIZE_OR_DUPLICATE_REQUESTS")
    if now.tzinfo is None:
        raise ValueError("AWARE_RUNTIME_REQUIRED")
    rows = []
    for path in requests:
        try:
            rows.append({"request": path, **ingest_one(path, root=root,
                                                       output_dir=output_dir, now=now)})
        except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
            rows.append({"request": path, "status": "BLOCKED_NO_PRICE_LOCK",
                         "reason": str(exc)[:240]})
    result = {
        "schema": BATCH_SCHEMA,
        "runtime_at_utc": now.astimezone(timezone.utc).isoformat(),
        "requests": len(requests),
        "accepted": sum(x["status"].startswith("MANUAL_ATTESTATION_SEALED") for x in rows),
        "blocked": sum(x["status"] == "BLOCKED_NO_PRICE_LOCK" for x in rows),
        "items": rows,
        "true_source_check_is_manual_not_code_verified": True,
        "snapshot_is_not_github_commit_until_push": True,
        "betting_authorized": False,
        "pilot_goal": PILOT_GOAL,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-dir", default="experiments/263/market_quotes_locked")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    paths = [line.strip() for line in Path(args.manifest).read_text(encoding="utf-8").splitlines()
             if line.strip()]
    result = ingest_batch(paths, root=Path(args.root), output_dir=Path(args.out_dir),
                          report_path=Path(args.report), now=datetime.now(timezone.utc))
    print(json.dumps({"accepted": result["accepted"], "blocked": result["blocked"]},
                     ensure_ascii=False))
    if result["accepted"] == 0:
        raise SystemExit("NO_VALID_MARKET_OBSERVATIONS; review saved blocked report")


if __name__ == "__main__":
    main()
