"""Strict safe aggregate-only public xG report; never reads raw match CSV values."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SCHEMA = "XG_AUDIT_PUBLIC_AGGREGATE_ONLY_V1"
LEAGUES = {"ENG1", "ESP1", "FRA1", "GER1", "ITA1"}
SEASONS = {"2025-2026", "2026-2027"}

def read_report(path):
    p = Path(path)
    if p.stat().st_size > 2_000_000:
        raise ValueError("input JSON unexpectedly large")
    obj = json.loads(p.read_text(encoding="utf8"))
    if not isinstance(obj, dict):
        raise ValueError("expected aggregate JSON object")
    return obj

def count(obj, key):
    v = obj[key]
    if type(v) is not int or v < 0:
        raise ValueError("invalid nonnegative count: " + key)
    return v

def sanitize(audit, history):
    matched = count(audit, "matched_unique")
    source = count(audit, "source_rows")
    eligible = count(audit, "historical_eligible")
    if history.get("prediction_engine_modified") is not False:
        raise ValueError("model state unexpectedly changed")
    if (count(history, "verified_xg_rows") != matched
        or count(history, "source_rows") != source
        or count(history, "audit_rows") != source or matched > source):
        raise ValueError("verification counts disagree")
    rows = audit["coverage_by_league_season"]
    if not isinstance(rows, list) or len(rows) != 10:
        raise ValueError("expected five leagues, two seasons")
    pairs = set()
    safe = []
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("nonaggregate coverage item")
        league, season = item["league"], item["season"]
        if league not in LEAGUES or season not in SEASONS:
            raise ValueError("unexpected league or season")
        if (league, season) in pairs:
            raise ValueError("duplicate league-season count")
        pairs.add((league, season))
        m, h = count(item, "matched"), count(item, "historical")
        if m > h:
            raise ValueError("matching larger than historical count")
        safe.append({"league": league, "season": season, "matched": m, "historical": h})
    if sum(x["matched"] for x in safe) != matched or sum(x["historical"] for x in safe) != eligible:
        raise ValueError("coverage total mismatch")
    status = audit["status_counts"]
    if not isinstance(status, list) or sum(count(x, "count") for x in status) != source:
        raise ValueError("source status count mismatch")
    if sum(count(x, "count") for x in status if x.get("status") == "MATCHED") != matched:
        raise ValueError("source matched status mismatch")
    # Positive allowlist: NEVER serialize entire input objects.
    return {"schema": SCHEMA,
            "status": "PUBLIC_AGGREGATE_ONLY_NO_LICENSE_APPROVAL",
            "coverage": sorted(safe, key=lambda x: (x["league"], x["season"])),
            "counts": {"source_rows": source,
                       "verified_matches": matched, "unmatched": source-matched,
                       "historical_eligible": eligible,
                       "historical_result_rows": count(history, "historical_rows")},
            "match_level_xg_exported": False,
            "asof_provider_vintage_proven": False,
            "rights_independently_verified": False}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--audit", default="data/understat_xg_match_report.json")
    p.add_argument("--verified", default="data/historical_verified_xg_report.json")
    p.add_argument("--out", default="data/xg_public_aggregate_safe.json")
    args = p.parse_args()
    safe = sanitize(read_report(args.audit), read_report(args.verified))
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(safe, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    print("SAFE_AGGREGATES_ONLY", safe["counts"])

if __name__ == "__main__":
    main()
