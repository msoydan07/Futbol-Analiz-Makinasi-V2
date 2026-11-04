"""Read-only bridge from SHA-sealed four-model forecast to frozen DEV calibration.

This is research ONLY: neither a live source acceptance nor official S1/S2.
The calibration JSON must be separately frozen from Aug-Sep development data.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
from pathlib import Path
from forward_decision_candidate_263 import MARKETS, decide
def canonical_bytes(payload):
    return json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")

CAL_SCHEMA="263_forward_dev_calibration_lock_v1"
REPORT_SCHEMA="263_reuse_first_880_asof_C3_M4_calibration_research_v1"
FORECAST_SCHEMA="quad_forward_263_v1"
MODEL_TO_MARKET={
    "MS1":("1X2","H"),"MSX":("1X2","D"),"MS2":("1X2","A"),
    "BTTS_YES":("BTTS_YES",),"BTTS_NO":("BTTS_NO",),
    "OVER_1.5":("OVER_1.5",),"UNDER_1.5":("UNDER_1.5",),
    "OVER_2.5":("OVER_2.5",),"UNDER_2.5":("UNDER_2.5",),
    "OVER_3.5":("OVER_3.5",),"UNDER_3.5":("UNDER_3.5",)}
def _digest(payload):
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()
def lock_from_stage2(stage2, *, source_report_sha256, source_predictions_sha256):
    if stage2.get("schema")!=REPORT_SCHEMA or stage2.get("dev_n")!=587 or stage2.get("oct_test_n")!=293:
        raise ValueError("UNEXPECTED_STAGE2_COHORT")
    if stage2.get("S1_approved") is not False or stage2.get("model_promoted") is not False:
        raise ValueError("UNSAFE_STAGE2_STATUS")
    if any(not isinstance(v,str) or len(v)!=64 or any(c not in "0123456789abcdef" for c in v) for v in (source_report_sha256,source_predictions_sha256)):
        raise ValueError("MISSING_SOURCE_HASH")
    cal={}
    for model in ("M4","C3"):
        raw=stage2["model_calibration"][model]
        if set(raw)!=set(MARKETS):raise ValueError("CALIBRATION_MARKET_MISMATCH")
        cal[model]={k:raw[k] for k in MARKETS}
    out={"schema":CAL_SCHEMA,"source_stage2_sha256":source_report_sha256,
         "source_predictions_sha256":source_predictions_sha256,
         "development_period":"2026-08-01/2026-09-30",
         "evaluation_period_not_used_for_weights":"2026-10-01/2026-10-29",
         "calibration":cal,"official_approval":False}
    out["payload_sha256"]=_digest(out)
    return out
def connect(forecast, lock, *, asof_baselines):
    if forecast.get("schema")!=FORECAST_SCHEMA or forecast.get("status")!="EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING":
        raise ValueError("NOT_ACCEPTED_FORWARD_EXPERIMENTAL_FORECAST")
    fs=forecast.get("payload_sha256")
    if not fs or _digest({k:v for k,v in forecast.items() if k!="payload_sha256"})!=fs:
        raise ValueError("FORECAST_HASH_MISMATCH")
    ls=lock.get("payload_sha256")
    if not ls or _digest({k:v for k,v in lock.items() if k!="payload_sha256"})!=ls:
        raise ValueError("CALIBRATION_LOCK_HASH_MISMATCH")
    if lock.get("schema")!=CAL_SCHEMA or lock.get("official_approval") is not False:
        raise ValueError("INVALID_CALIBRATION_LOCK")
    if lock.get("development_period")!="2026-08-01/2026-09-30":
        raise ValueError("CALIBRATION_LEAKAGE")
    f=forecast["fixture"]
    model="M4"
    entry=forecast["model_predictions"].get(model)
    if not entry or entry.get("status")!="AVAILABLE":
        raise ValueError("M4_UNAVAILABLE_NO_SILENT_FALLBACK")
    if not isinstance(asof_baselines,dict) or set(asof_baselines)!=set(MARKETS):
        raise ValueError("ASOF_BASELINES_MISSING")
    if asof_baselines.get("recorded_after_kickoff") is True:
        raise ValueError("BASELINE_LOOKAHEAD")
    m=entry["goals"]["markets"]
    converted={}
    for market,path in MODEL_TO_MARKET.items():
        raw=m
        for part in path:raw=raw[part]
        converted[market]={"raw_probability":raw,
                           "asof_baseline":asof_baselines[market],
                           "development_calibration":lock["calibration"][model][market]}
    request={"record_type":"FORWARD_PREMATCH_LOCKED",
        "immutable_record_id":fs,
        "asof_utc":forecast["created_at_utc"],
        "kickoff_utc":f["kickoff_utc"],
        "fixture_verified":f.get("fixture_verification")=="VERIFIED_BY_LIVE_OFFICIAL_GATE",
        "source_fresh":forecast["data"].get("human_source_acceptance") is True and
            forecast["data"].get("research_shadow_unverified_source") is False,
        "model":model,"markets":converted}
    decision=decide(request)
    decision["forecast_sha256"]=fs
    decision["calibration_lock_sha256"]=ls
    decision["baseline_status"]="CALLER_SUPPLIED_ASOF_UNVERIFIED_BY_BRIDGE"
    decision["source_acceptance_status"]="ATTESTED_BY_UPSTREAM_NOT_INDEPENDENTLY_VERIFIED"
    decision["official_S1"]=None
    decision["official_S2"]=None
    return decision
