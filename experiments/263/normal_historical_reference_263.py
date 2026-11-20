"""Read-only real pre-kickoff probability/result reference for NORMAL 2.6.3 selection.

Only uses original SHA-sealed 08-Nov new100 predictions and the reviewed
12-Nov terminal results. Does NOT backfill models from completed scores.
Past archive was available by the end of 12 Nov; make it eligible only from
13 Nov 00:00 UTC (a conservative as-of bound, NOT a measured result timestamp).
Past seals/old decisions are read-only and never regenerated.
"""
from __future__ import annotations
import json
import re
from datetime import datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ARCHIVE="data/results_only_263/nov8_new100_terminal_archive_20261112.json"
AVAILABLE_FROM="2026-11-13T00:00:00+00:00"
MARKETS=("MS1","MSX","MS2","BTTS_YES","BTTS_NO","OVER_2.5","UNDER_2.5")
class HistoricalEvidenceError(ValueError):pass

def available_asof(*,asof):
    from model_first_decision_263 import aware
    return aware(asof)>=aware(AVAILABLE_FROM)

def load(*,asof,root=ROOT,lock=None):
    """Return 273 paired market observations; 0 before Nov13, no invented data.

    This is retrospective read-only source evidence, not independent validation
    of predictive reliability. Every pair reuses original forecast SHA.
    """
    from model_first_decision_263 import aware,digest,canonical,joint_poisson,verified
    from postmatch_terminal_archive_263 import checked
    if not available_asof(asof=asof):return []
    root=Path(root)
    archive=json.loads((root/ARCHIVE).read_text(encoding="utf-8"))
    if lock is None:
        lock=json.loads((root/"experiments/263/model_first_selection_lock_20261120.json").read_text(encoding="utf-8"))
    if not (isinstance(lock.get("m4_joint_calibration_august"),list)
            and len(lock["m4_joint_calibration_august"])==3):
        raise HistoricalEvidenceError("FROZEN_AUG_CALIBRATION_REQUIRED")
    forecasts={};named={}
    rows=archive.get("rows",[])
    if len(rows)!=40:raise HistoricalEvidenceError("TERMINAL_ARCHIVE_NOT_40")
    for r in rows:
        path=r["forecast_path"]
        if not re.fullmatch(r"forward_morning_263/2026-11-08/[0-9a-f]{24}\\.json",path):
            raise HistoricalEvidenceError("UNSAFE_HISTORICAL_FORECAST_PATH")
        f=json.loads((root/path).read_text(encoding="utf-8"))
        verified(f,"quad_forward_263_v1")
        sha=f["payload_sha256"]
        if sha!=r["forecast_sha256"] or sha in forecasts:
            raise HistoricalEvidenceError("HISTORICAL_SHA_MISMATCH_OR_DUPLICATE")
        fx=f["fixture"]
        if (f["status"]!="EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING"
            or fx["fixture_verification"]!="VERIFIED_BY_LIVE_OFFICIAL_GATE"
            or fx["league"]!=r["league"]
            or fx["kickoff_utc"]!=r["kickoff_utc"]
            or not aware(f["created_at_utc"])<aware(fx["kickoff_utc"])
            or not aware(fx["kickoff_utc"])<aware(AVAILABLE_FROM)):
            raise HistoricalEvidenceError("NOT_ORIGINAL_PREMATCH_GATE")
        forecasts[sha]=f
        named[sha]={"league":r["league"],"home":r["home"],"away":r["away"],
                    "kickoff_utc":r["kickoff_utc"],"forecast_path":path}
    checked(root,forecasts,named,doc=archive)
    theta=lock["m4_joint_calibration_august"]
    observations=[]
    for r in rows:
        if r["match_state"]!="FINISHED_ARCHIVED":continue
        sha=r["forecast_sha256"]
        forecast=forecasts[sha]
        models=forecast["model_predictions"]
        m4=models.get("M4",{})
        if m4.get("status")!="AVAILABLE":
            raise HistoricalEvidenceError("HISTORICAL_M4_REQUIRED")
        from math import exp,log
        goals=m4["goals"]
        lh=max(.05,min(5.,exp(theta[0]+theta[2]*log(goals["lambda_home"]))))
        la=max(.05,min(5.,exp(theta[1]+theta[2]*log(goals["lambda_away"]))))
        ms=joint_poisson(lh,la)
        c3=models.get("C3",{})
        use_c3=c3.get("status")=="AVAILABLE"
        raw=canonical((c3 if use_c3 else m4)["goals"]["markets"])
        p={**{m:ms[m] for m in ("MS1","MSX","MS2")},
           **{m:raw[m] for m in ("BTTS_YES","BTTS_NO","OVER_2.5","UNDER_2.5")}}
        identities={m:"M4_AUG_JOINT_CALIBRATED" for m in ("MS1","MSX","MS2")}
        identities.update({m:("C3_RAW_UNCALIBRATED" if use_c3
                              else "M4_RAW_FALLBACK_UNCALIBRATED")
                           for m in ("BTTS_YES","BTTS_NO","OVER_2.5","UNDER_2.5")})
        h,a=r["score"]
        actual={"MS1":h>a,"MSX":h==a,"MS2":h<a,
                "BTTS_YES":h>0 and a>0,"BTTS_NO":h==0 or a==0,
                "OVER_2.5":h+a>=3,"UNDER_2.5":h+a<=2}
        for market in MARKETS:
            observations.append({
                "fixture_id":sha,"league":r["league"],"market":market,
                "model_identity":identities[market],
                "model_probability":p[market],"occurred":actual[market],
                "forecast_created_at_utc":forecast["created_at_utc"],
                "kickoff_utc":r["kickoff_utc"],
                "result_known_at_utc":AVAILABLE_FROM,
                "result_availability_kind":"CONSERVATIVE_ARCHIVE_CUTOFF_NOT_ACTUAL_FINAL_WHISTLE",
                "result_source_grade":r["evidence_grade"],
                "forecast_origin":"SEALED_BEFORE_KICKOFF",
                "forecast_sha256":sha})
    if len(observations)!=39*len(MARKETS):
        raise HistoricalEvidenceError("HISTORICAL_39_COMPLETED_REQUIRED")
    return observations
