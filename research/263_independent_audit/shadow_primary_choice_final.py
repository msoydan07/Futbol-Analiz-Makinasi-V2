"""Isolated, reproducible, operational-shaped 2.6.3 primary preference shadow.

Treat MS1/MSX/MS2 as one pre-calibrated M4 1X2 distribution, calibrate C3
KG and O2.5 probabilities with coefficients frozen on 2025/26 ONLY, then
choose one most likely event; all values require pre-kickoff market snapshots.

NEVER changes production choice, places bet or rewrites any original seal.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json,math
from pathlib import Path

POLICY_PATH=Path(__file__).with_name("20_shadow_choice_policy.json")
MS=("MS1","MSX","MS2")
KG=("BTTS_YES","BTTS_NO")
O25=("OVER_2.5","UNDER_2.5")
EVENTS=MS+KG+O25
POLICY_SCHEMA="263_C3_2025_FROZEN_BINARY_CALIBRATION_SHADOW_V1"

def bounded(p):
    if isinstance(p,bool) or not isinstance(p,(float,int)) or not math.isfinite(p):
        raise ValueError("MISSING_INVALID_PROB")
    if not 0<=p<=1:raise ValueError("PROB_OUTSIDE_0_1")
    return float(p)

def validate(p, expected):
    if not isinstance(p,dict) or set(p)!=set(expected):
        raise ValueError("MISSING_OR_EXTRA_FAMILY_PROB")
    out={k:bounded(p[k]) for k in expected}
    families=(KG,O25) if tuple(expected)==KG+O25 else (tuple(expected),)
    for keys in families:
        if abs(sum(out[k] for k in keys)-1)>1e-6:
            raise ValueError("NOT_A_COHERENT_FAMILY")
    return out

def logit(p):
    p=min(.9999,max(.0001,bounded(p)))
    return math.log(p/(1-p))

def sigmoid(z):
    if z>=0:
        return 1/(1+math.exp(-z))
    v=math.exp(z)
    return v/(1+v)

def local_time(s):
    if not isinstance(s,str):raise ValueError("MISSING_TIME")
    dt=datetime.fromisoformat(s.replace("Z","+00:00"))
    if dt.tzinfo is None:raise ValueError("NAIVE_TIME")
    return dt.astimezone(timezone.utc)

def policy_load(path=POLICY_PATH):
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    if (obj.get("schema")!=POLICY_SCHEMA or
        obj.get("status")!="RESEARCH_SHADOW_NOT_LIVE" or
        obj.get("production_promotion_permitted") is not False or
        obj.get("m4_ms_source")!="M4_AUG_JOINT_CALIBRATED" or
        obj.get("c3_binary_source")!="C3_RAW_UNCALIBRATED" or
        obj.get("n_train")!=2898 or
        obj.get("no_automatic_bet") is not True or
        obj.get("no_xg") is not True or
        obj.get("no_odds") is not True):
        raise ValueError("INCORRECT_OR_PROMOTED_CALIBRATION_POLICY")
    co=obj.get("coefficients")
    if not isinstance(co,dict) or set(co)!={"BTTS_YES","OVER_2.5"}:
        raise ValueError("WRONG_C3_CALIBRATION_KEYS")
    for a in co.values():
        if set(a)!={"intercept","coefficient_c3_logit","coefficient_league_logit"}:
            raise ValueError("WRONG_COEFFICIENT_SHAPE")
        for value in a.values():
            if not isinstance(value,(float,int)) or not math.isfinite(value):
                raise ValueError("WRONG_COEFFICIENT_VALUE")
    return obj

def frozen_binary(c3_positive,league_positive,key,policy):
    co=policy["coefficients"][key]
    z=co["intercept"]+co["coefficient_c3_logit"]*logit(c3_positive)
    z+=co["coefficient_league_logit"]*logit(league_positive)
    return sigmoid(z)

def decide(*,m4_joint_ms,c3_binary=None,league_asof,asof_utc,
           kickoff_utc,forecast_created_utc,
           m4_binaries_fallback=None,policy=None):
    """A match-specific shadow decision. NO final scores in the interface.

    m4_joint_ms: dict(MS1,MSX,MS2) from AUG frozen M4 goal calibration.
    c3_binary: dict(KG yes/no, O2.5 yes/no) from raw C3 predictions, optional.
    league_asof: same 7 event baseline probabilities, original day-before.
    Strictly before kickoff timestamp and after forecast-created timestamp.
    """
    if policy is None:policy=policy_load()
    if policy.get("schema")!=POLICY_SCHEMA:
        raise ValueError("WRONG_POLICY")
    created,now,ko=map(local_time,(forecast_created_utc,asof_utc,kickoff_utc))
    if not created<=now<ko:
        raise ValueError("ONLY_ORIGINAL_PREMATCH_FORECAST_WINDOW")
    m=validate(m4_joint_ms,MS)
    # Separate families share only top-level seven-event ranking, never mix
    # 1X2 probabilities from different anchor models.
    if not isinstance(league_asof,dict) or not set(EVENTS).issubset(league_asof):
        raise ValueError("BASELINE_ALL_SEVEN_REQUIRED")
    b={k:bounded(league_asof[k]) for k in EVENTS}
    for family in (MS,KG,O25):
        if abs(sum(b[k] for k in family)-1)>1e-6:
            raise ValueError("LEAGUE_BASE_NOT_NORMALIZED")
    if c3_binary is not None:
        c=validate(c3_binary,KG+O25)
        kg_yes=frozen_binary(c["BTTS_YES"],b["BTTS_YES"],"BTTS_YES",policy)
        o25_yes=frozen_binary(c["OVER_2.5"],b["OVER_2.5"],"OVER_2.5",policy)
        method="C3_2025_FROZEN_BINARY_LOGIT_AND_M4_AUG_CALIBRATED_MS"
        stat="SHADOW_CALIBRATED_CHOICE"
    elif m4_binaries_fallback is not None:
        c=validate(m4_binaries_fallback,KG+O25)
        kg_yes,o25_yes=c["BTTS_YES"],c["OVER_2.5"]
        method="M4_RAW_BINARY_FALLBACK_NOT_C3_CALIBRATED"
        stat="SHADOW_FALLBACK_UNCALIBRATED"
    else:
        return {
            "status":"SHADOW_PAS_NO_COMPARABLE_BINARY_MODEL",
            "main_choice":None,"reason":"C3_MISSING_AND_M4_FALLBACK_MISSING",
            "production_promotion_permitted":False,"betting_authorized":False}
    p={**m,"BTTS_YES":kg_yes,"BTTS_NO":1-kg_yes,
          "OVER_2.5":o25_yes,"UNDER_2.5":1-o25_yes}
    order=sorted(EVENTS,key=lambda k:(-p[k],k))
    first,runner=order[:2]
    first_family=next(group for group in (MS,KG,O25) if first in group)
    alternate=next((k for k in order[1:] if k not in first_family),None)
    gap=p[first]-p[runner]
    return {
        "status":stat,
        "main_choice":first,"main_probability":round(p[first],9),
        "second_choice":runner,"second_probability":round(p[runner],9),
        "alternative_different_family":alternate,
        "alternative_probability":round(p[alternate],9) if alternate else None,
        "gap_percentage_points":round(100*gap,4),
        "near_tie":gap<=policy["near_tie_threshold_absolute"],
        "near_tie_means_uncertain_not_automatic_pas":True,
        "all_market_probabilities":{k:round(p[k],9) for k in EVENTS},
        "probability_method":method,
        "evidence_class":"RESEARCH_SHADOW_CALIBRATED_NOT_BLIND_VALIDATED",
        "research_only":True,"production_promotion_permitted":False,
        "betting_authorized":False,"odds_used":False,"xg_used":False,
        "forecast_unchanged":True,"original_sha_unchanged":True,
    }
