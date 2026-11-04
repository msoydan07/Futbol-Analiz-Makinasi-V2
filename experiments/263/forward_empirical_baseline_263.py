"""Deterministic per-league pre-kickoff empirical baseline from accepted history.

Consumes only completed results strictly before the fixture's local date.
It is a historical market frequency, NOT odds, EV or a calibrated prediction.
"""
from __future__ import annotations
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from forward_calibration_bridge_263 import MARKETS, _digest
from forward_baseline_provenance_263 import SCHEMA, _time

def produce(forecast, history_path, *, now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError("AWARE_TIME_REQUIRED")
    if forecast.get("schema")!="quad_forward_263_v1":
        raise ValueError("INVALID_FORECAST_SCHEMA")
    if _digest({k:v for k,v in forecast.items() if k!="payload_sha256"})!=forecast.get("payload_sha256"):
        raise ValueError("FORECAST_HASH_MISMATCH")
    if forecast.get("status")!="EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING":
        raise ValueError("SHADOW_NOT_ACCEPTED")
    data=forecast["data"]
    if data.get("snapshot_acceptance")!="APPEND_ONLY_HUMAN_SOURCE_ATTESTED_NOT_INDEPENDENTLY_RECHECKED" or data.get("human_source_acceptance") is not True or data.get("research_shadow_unverified_source") is not False:
        raise ValueError("UPDATED_SOURCE_NOT_HUMAN_ACCEPTED")
    if hashlib.sha256(Path(history_path).read_bytes()).hexdigest()!=data.get("snapshot_sha256"):
        raise ValueError("HISTORY_SHA_MISMATCH")
    asof=_time(forecast["created_at_utc"])
    ko=_time(forecast["fixture"]["kickoff_utc"])
    now=now.astimezone(timezone.utc)
    # Record actual calculation time, not the forecast's earlier timestamp.
    # Require immediate (<=10 minutes) prematch computation.
    if not asof<=now<ko or (now-asof).total_seconds()>600:
        raise ValueError("BASELINE_NOT_CALCULATED_PRE_KICKOFF")
    local_date=forecast["fixture"]["match_local_date"]
    league=forecast["fixture"]["league"]
    rows=[]
    ids=set()
    with Path(history_path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        for r in reader:
            if not r.get("fixture_id") or r["fixture_id"] in ids:
                raise ValueError("DUPLICATE_OR_MISSING_FIXTURE_ID")
            ids.add(r["fixture_id"])
            if r.get("league")!=league:continue
            day=r["match_date"]
            if day>=local_date:raise ValueError("FUTURE_LEAGUE_RESULTS_IN_SNAPSHOT")
            # Dates alone cannot prove result availability earlier the same day.
            if day>=asof.date().isoformat():
                raise ValueError("RESULT_NOT_PRIOR_TO_FORECAST_DATE")
            h=int(r["home_goals"]);a=int(r["away_goals"])
            if h<0 or a<0 or r["result"]!=("H" if h>a else "D" if h==a else "A"):
                raise ValueError("INVALID_HISTORICAL_RESULT")
            rows.append(r)
    from full_match_eligibility_263 import full_match_rows
    rows,excluded_partial,eligibility_sha=full_match_rows(rows)
    if data.get("training_excluded_partial_match_ids",[])!=excluded_partial:
        raise ValueError("BASELINE_TRAINING_EXCLUSION_MISMATCH")
    if (excluded_partial or data.get("full_match_policy_sha256") is not None) and data.get("full_match_policy_sha256")!=eligibility_sha:
        raise ValueError("BASELINE_EXCLUSION_POLICY_HASH_MISMATCH")
    if len(rows)<120:raise ValueError("INSUFFICIENT_LEAGUE_HISTORY")
    latest=max(x["match_date"] for x in rows)
    if latest!=data.get("league_latest_result_date"):
        raise ValueError("HISTORY_CUTOFF_MISMATCH")
    if len(rows)!=data.get("league_history_rows"):
        raise ValueError("HISTORY_COUNT_MISMATCH")
    counts=Counter()
    for row in rows:
        h=int(row["home_goals"]);a=int(row["away_goals"])
        counts["MS1"]+=h>a
        counts["MSX"]+=h==a
        counts["MS2"]+=h<a
        for line in (1.5,2.5,3.5):
            key=f"{line:g}"
            counts["OVER_"+key]+=h+a>line
            counts["UNDER_"+key]+=h+a<line
        counts["BTTS_YES"]+=h>0 and a>0
        counts["BTTS_NO"]+=h==0 or a==0
    n=len(rows)
    # Empirical league rates with one pseudocount per binary side,
    # and one pseudocount per outcome for the three-way result.
    values={m:((counts[m]+1)/(n+3) if m.startswith("MS") else (counts[m]+1)/(n+2)) for m in MARKETS}
    record={"schema":SCHEMA,"forecast_sha256":forecast["payload_sha256"],
        "league":league,"method":"PAST_RESULTS_LEAGUE_MARKET_RATE",
        "source_snapshot_sha256":data["snapshot_sha256"],
        "historical_match_count":n,"last_result_date":latest,
        "forecast_created_at_utc":forecast["created_at_utc"],
        "created_at_utc":now.isoformat(),
        "markets":values}
    record["payload_sha256"]=_digest(record)
    return record
