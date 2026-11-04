"""Experimental, read-only forward decision adapter. Never grants betting approval."""
from __future__ import annotations
import math
from datetime import datetime, timezone

VERSION="263_forward_decision_candidate_v1"
MARKETS=("MS1","MSX","MS2","OVER_1.5","UNDER_1.5","OVER_2.5","UNDER_2.5","OVER_3.5","UNDER_3.5","BTTS_YES","BTTS_NO")
def family(m):
    return "MS" if m.startswith("MS") else "BTTS" if m.startswith("BTTS") else "GOALS"
def probability(x):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or not 0<=x<=1:
        raise ValueError("INVALID_PROBABILITY")
    return float(x)
def decide(record):
    """Consume ONLY pre-KO as-of model and dev-only calibration inputs.
    This returns research candidates, not official S1/S2 or betting selections.
    """
    if record.get("record_type")!="FORWARD_PREMATCH_LOCKED" or not record.get("immutable_record_id"):
        raise ValueError("PREMATCH_LOCK_REQUIRED")
    stamp=datetime.fromisoformat(record["asof_utc"].replace("Z","+00:00"))
    ko=datetime.fromisoformat(record["kickoff_utc"].replace("Z","+00:00"))
    if stamp.tzinfo is None or ko.tzinfo is None or stamp>=ko:
        raise ValueError("INVALID_PREMATCH_TIME")
    if record.get("fixture_verified") is not True:
        return _pas(record,"FIXTURE_UNVERIFIED")
    if record.get("source_fresh") is not True:
        return _pas(record,"SOURCE_STALE")
    model=record.get("model","M4")
    if model not in ("M4","C3"):
        return _pas(record,"NO_MODEL_COVERAGE")
    entries=record.get("markets",{})
    if set(entries)!=set(MARKETS):
        return _pas(record,"NO_MODEL_COVERAGE")
    candidates=[]
    for market in MARKETS:
        x=entries[market]
        p=probability(x["raw_probability"])
        b=probability(x["asof_baseline"])
        cal=x.get("development_calibration",{})
        if cal.get("n",0)<120 or cal.get("available") is not True:
            continue
        skill=cal.get("development_brier_skill")
        if skill is None or not isinstance(skill,(int,float)) or not math.isfinite(skill) or skill<=0:
            continue
        w=probability(cal["weight"])
        q=b+w*(p-b)
        lift=q-b
        if q>=.60 and lift>=.025:
            candidates.append({"market":market,"family":family(market),
                "calibrated_probability":round(q,10),"baseline":b,
                "lift":round(lift,10),"rank_score":round(lift+.1*q,10)})
    candidates.sort(key=lambda x:(-x["rank_score"],-x["calibrated_probability"],x["market"]))
    if not candidates:
        return _pas(record,"NO_RELIABLE_CANDIDATE")
    main=candidates[0]
    # Correlated goal lines are never presented as independent alternatives.
    alt=next((x for x in candidates[1:] if x["family"]!=main["family"]),None)
    return {"schema":VERSION,"immutable_record_id":record["immutable_record_id"],
        "status":"RESEARCH_CANDIDATE_NOT_APPROVED","main_candidate":main,
        "alternative_candidate":alt,"pas_reasons":[],
        "official_S1":None,"official_S2":None,"betting_authorized":False,
        "pilot_count_increment":0,"production_modified":False,
        "odds_EV":None,"market_candidates_evaluated":len(MARKETS)}
def _pas(record,reason):
    return {"schema":VERSION,"immutable_record_id":record.get("immutable_record_id"),
        "status":"RESEARCH_PAS","main_candidate":None,"alternative_candidate":None,
        "pas_reasons":[reason],"official_S1":None,"official_S2":None,
        "betting_authorized":False,"pilot_count_increment":0,
        "production_modified":False,"odds_EV":None}
