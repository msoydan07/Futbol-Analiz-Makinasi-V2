"""Strict read-only as-of baseline provenance gate for the experimental bridge.

No external live data is invented; accepts only an explicitly sealed pre-KO
baseline record. Does not independently establish that its source is truthful.
"""
from __future__ import annotations
from datetime import datetime, timezone
import math
from forward_calibration_bridge_263 import _digest, connect, MARKETS

SCHEMA="263_asof_market_baseline_v2"
def _time(value):
    d=datetime.fromisoformat(value.replace("Z","+00:00"))
    if d.tzinfo is None:raise ValueError("NAIVE_BASELINE_TIMESTAMP")
    return d.astimezone(timezone.utc)
def connect_verified_baseline(forecast, calibration_lock, baseline_record):
    if not isinstance(baseline_record,dict) or baseline_record.get("schema")!=SCHEMA:
        raise ValueError("BASELINE_PROVENANCE_REQUIRED")
    digest=baseline_record.get("payload_sha256")
    if not isinstance(digest,str) or digest!=_digest({k:v for k,v in baseline_record.items() if k!="payload_sha256"}):
        raise ValueError("BASELINE_HASH_MISMATCH")
    if baseline_record.get("forecast_sha256")!=forecast.get("payload_sha256"):
        raise ValueError("BASELINE_WRONG_FORECAST")
    grade=forecast.get("data",{}).get("snapshot_acceptance")
    if grade not in ("APPEND_ONLY_HUMAN_SOURCE_ATTESTED_NOT_INDEPENDENTLY_RECHECKED",
                     "APPEND_ONLY_4617_PUBLIC_RESULTS_ONLY_RESEARCH_NOT_OFFICIAL_ID_VERIFIED"):
        raise ValueError("UPSTREAM_PROVENANCE_GRADE_NOT_SUPPORTED")
    if forecast.get("data",{}).get("human_source_acceptance") is not (
        grade=="APPEND_ONLY_HUMAN_SOURCE_ATTESTED_NOT_INDEPENDENTLY_RECHECKED"):
        raise ValueError("PROVENANCE_LABEL_NOT_CONSISTENT")
    if baseline_record.get("league")!=forecast.get("fixture",{}).get("league"):
        raise ValueError("BASELINE_WRONG_LEAGUE")
    if baseline_record.get("method")!="PAST_RESULTS_LEAGUE_MARKET_RATE":
        raise ValueError("BASELINE_METHOD_UNSUPPORTED")
    if baseline_record.get("source_snapshot_sha256")!=forecast.get("data",{}).get("snapshot_sha256"):
        raise ValueError("BASELINE_WRONG_SOURCE_SNAPSHOT")
    if not isinstance(baseline_record.get("historical_match_count"),int) or baseline_record["historical_match_count"]<120:
        raise ValueError("BASELINE_INSUFFICIENT_HISTORY")
    if not isinstance(baseline_record.get("last_result_date"),str):
        raise ValueError("BASELINE_CUTOFF_MISSING")
    asof=_time(forecast["created_at_utc"])
    ko=_time(forecast["fixture"]["kickoff_utc"])
    created=_time(baseline_record["created_at_utc"])
    if baseline_record.get("forecast_created_at_utc")!=forecast["created_at_utc"]:
        raise ValueError("BASELINE_FORECAST_TIME_MISMATCH")
    # Retroactively stamped pre-forecast records are not proof of as-of.
    # This baseline is only accepted if created promptly before kickoff.
    if not asof<=created<ko or (created-asof).total_seconds()>600:
        raise ValueError("BASELINE_TIMESTAMP_LOOKAHEAD_OR_STALE")
    local_date=forecast["fixture"]["match_local_date"]
    if baseline_record["last_result_date"]>=min(local_date,asof.date().isoformat()):
        raise ValueError("BASELINE_RESULT_LEAKAGE")
    if baseline_record["last_result_date"]!=forecast.get("data",{}).get("league_latest_result_date"):
        raise ValueError("BASELINE_HISTORY_CUTOFF_MISMATCH")
    values=baseline_record.get("markets")
    if not isinstance(values,dict) or set(values)!=set(MARKETS):
        raise ValueError("BASELINE_MARKET_COVERAGE")
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 or x>1 for x in values.values()):
        raise ValueError("BASELINE_PROBABILITY_INVALID")
    result=connect(forecast,calibration_lock,asof_baselines=values)
    result["baseline_status"]="SHA_SEALED_ASOF_SOURCE_LINKED_NOT_INDEPENDENTLY_VERIFIED"
    result["baseline_sha256"]=digest
    return result
