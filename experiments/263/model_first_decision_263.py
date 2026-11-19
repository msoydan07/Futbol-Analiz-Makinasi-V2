"""Research-only 2.6.3 model FIRST decision. Prices are NOT selection inputs.

Frozen AUG calibrator and SEP model anchors; no new model fitting, no pilot.
M4 remains the reference until independent evidence justifies other anchors.
"""
from __future__ import annotations
import hashlib
import json
import math
from datetime import datetime, timezone

SCHEMA = "263_MODEL_FIRST_FOUR_MODEL_DECISION_RESEARCH_V1"
REF_SCHEMA = "263_MARKET_FIFTH_REFERENCE_RESEARCH_V1"
GROUPS = {"MS": ("MS1", "MSX", "MS2"), "KG": ("BTTS_YES", "BTTS_NO"),
          "O25": ("OVER_2.5", "UNDER_2.5")}

class EvidenceError(ValueError):
    pass

def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
           separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()

def verified(obj, schema):
    if not isinstance(obj, dict) or obj.get("schema") != schema:
        raise EvidenceError("SCHEMA_MISMATCH")
    old = obj.get("payload_sha256")
    if not isinstance(old, str) or old != digest({k:v for k,v in obj.items() if k != "payload_sha256"}):
        raise EvidenceError("SHA_TAMPERED_OR_MISSING")
    return obj

def aware(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None: raise ValueError("tz")
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise EvidenceError("BAD_AWARE_CLOCK") from exc

def validprob(value):
    if (isinstance(value, bool) or not isinstance(value, (int,float))
            or not math.isfinite(value) or not 0 <= value <= 1):
        raise EvidenceError("BAD_PROBABILITY")
    return float(value)

def canonical(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get("1X2"), dict):
        raise EvidenceError("MS_REQUIRED")
    ms = raw["1X2"]
    p = {"MS1":validprob(ms["H"]), "MSX":validprob(ms["D"]),
         "MS2":validprob(ms["A"])}
    if abs(sum(p.values())-1)>1e-6: raise EvidenceError("MS_NOT_NORMALIZED")
    for pos,neg in (("BTTS_YES","BTTS_NO"), ("OVER_2.5","UNDER_2.5")):
        p[pos] = validprob(raw[pos]); p[neg] = validprob(raw[neg])
        if abs(p[pos]+p[neg]-1)>1e-6: raise EvidenceError("BINARY_NOT_NORMALIZED")
    return p

def joint_poisson(lh, la):
    if any(not isinstance(x,(int,float)) or not math.isfinite(x)
           or not .05 <= x <= 5 for x in (lh,la)):
        raise EvidenceError("BAD_GOAL_LAMBDA")
    def pmf(mu):
        a=[math.exp(-mu)]
        for n in range(1,70):
            a.append(a[-1]*mu/n)
            if 1-sum(a)<1e-13: break
        return a
    h,a=pmf(lh),pmf(la)
    mass=sum(h)*sum(a)
    if 1-mass>1e-9: raise EvidenceError("GOAL_MATRIX_TAIL")
    p={x:0. for x in ("MS1","MSX","MS2","BTTS_YES","OVER_2.5")}
    for i,x in enumerate(h):
        for j,y in enumerate(a):
            v=x*y/mass
            p["MS1" if i>j else "MSX" if i==j else "MS2"]+=v
            if i and j: p["BTTS_YES"]+=v
            if i+j>=3: p["OVER_2.5"]+=v
    p["BTTS_NO"]=1-p["BTTS_YES"]
    p["UNDER_2.5"]=1-p["OVER_2.5"]
    return p

def select(forecast, baseline, lock, *, now):
    """One SHA-sealed model decision, WITHOUT an odds or price argument."""
    verified(forecast,"quad_forward_263_v1")
    verified(baseline,"263_asof_market_baseline_v2")
    if forecast.get("status")!="EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING":
        raise EvidenceError("NOT_APPROVED_FOUR_MODEL_RECORD")
    fx=forecast["fixture"];stamp=aware(forecast["created_at_utc"]);asof=aware(now)
    if not stamp<=asof<aware(fx["kickoff_utc"]): raise EvidenceError("NOT_PREKICKOFF")
    if fx.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE":
        raise EvidenceError("FIXTURE_UNVERIFIED")
    if baseline.get("forecast_sha256")!=forecast["payload_sha256"]:
        raise EvidenceError("BASELINE_FORECAST_SHA_MISMATCH")
    if (baseline.get("method")!="PAST_RESULTS_LEAGUE_MARKET_RATE"
        or baseline.get("source_snapshot_sha256")!=forecast.get("data",{}).get("snapshot_sha256")):
        raise EvidenceError("BASELINE_SOURCE_OR_METHOD_MISMATCH")
    if (baseline.get("league")!=fx["league"]
        or not baseline.get("last_result_date")
        or baseline["last_result_date"]>=fx["match_local_date"]):
        raise EvidenceError("HISTORICAL_LEAKAGE_OR_LEAGUE_MISMATCH")
    bt=aware(baseline.get("created_at_utc"))
    if not stamp<=bt<=asof or (bt-stamp).total_seconds()>600:
        raise EvidenceError("BASELINE_ASOF_TIME_INVALID")
    if lock.get("schema")!="263_MODEL_FIRST_RESEARCH_LOCK_V1" or lock.get("officially_approved") is not False:
        raise EvidenceError("WRONG_MODEL_LOCK")
    if lock.get("payload_sha256")!=digest({k:v for k,v in lock.items() if k!="payload_sha256"}):
        raise EvidenceError("MODEL_LOCK_SHA_MISMATCH")
    if set(lock["family_anchors"])!=set(GROUPS) or any(v!="M4" for v in lock["family_anchors"].values()):
        raise EvidenceError("UNPROVEN_MODEL_PROMOTION")
    mods=forecast.get("model_predictions")
    if not isinstance(mods,dict) or set(mods)!=set(("B","C2","C3","M4")):
        raise EvidenceError("FOUR_MODEL_SLOTS_REQUIRED")
    raw={}
    for name,m in mods.items():
        raw[name]=canonical(m["goals"]["markets"]) if m.get("status")=="AVAILABLE" else None
    if raw["M4"] is None: raise EvidenceError("ANCHOR_M4_UNAVAILABLE")
    goals=mods["M4"]["goals"]
    theta=lock["m4_joint_calibration_august"]
    if len(theta)!=3 or any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in theta):
        raise EvidenceError("MODEL_CALIBRATION_CORRUPT")
    lh,la=goals["lambda_home"],goals["lambda_away"]
    if any(not isinstance(x,(int,float)) or not math.isfinite(x) or not .05<=x<=5 for x in (lh,la)):
        raise EvidenceError("BAD_GOAL_LAMBDA")
    lh=max(.05,min(5.,math.exp(theta[0]+theta[2]*math.log(lh))))
    la=max(.05,min(5.,math.exp(theta[1]+theta[2]*math.log(la))))
    q=joint_poisson(lh,la)
    b=baseline.get("markets")
    if not isinstance(b,dict):raise EvidenceError("BASELINE_MARKETS_MISSING")
    details=[];qualifying=[]
    for family,keys in GROUPS.items():
        for key in keys:
            ref=validprob(b[key]);prob=q[key]
            available=[name for name,p in raw.items() if p is not None]
            agreeing=[name for name in available if raw[name][key]>=ref+lock["support_lift"]]
            why=[]
            if len(available)<lock["min_available_models"]:why.append("INSUFFICIENT_AVAILABLE_MODELS")
            if len(agreeing)<lock["min_support_models"]:why.append("INSUFFICIENT_MODEL_AGREEMENT")
            if prob<lock["min_probability"]:why.append("LOW_MODEL_PROBABILITY")
            if prob-ref<lock["min_lift"]:why.append("LOW_HISTORICAL_LIFT")
            rank=(prob-ref)/max(.25,math.sqrt(max(1e-9,ref*(1-ref))))
            item={"market":key,"family":family,"anchor_model":"M4",
                  "calibrated_probability":round(prob,10),"historical_base":round(ref,10),
                  "lift_pp":round(100*(prob-ref),6),"confidence_score":round(rank,8),
                  "agreeing_models":agreeing,"available_models":available,
                  "qualification_reasons":why}
            details.append(item)
            if not why:qualifying.append(item)
    qualifying.sort(key=lambda v:(-v["confidence_score"],-v["calibrated_probability"],v["market"]))
    main=qualifying[0] if qualifying else None
    alternate=next((x for x in qualifying[1:] if x["family"]!=main["family"]),None) if main else None
    out={"schema":SCHEMA,"status":"RESEARCH_CANDIDATE_NOT_APPROVED" if main else "RESEARCH_PAS_MODEL_ONLY",
         "forecast_sha256":forecast["payload_sha256"],"baseline_sha256":baseline["payload_sha256"],
         "model_policy_sha256":lock["payload_sha256"],"fixture":fx,
         "main_candidate":main,"alternative_candidate":alternate,"model_market_diagnostics":details,
         "reason":None if main else "NO_CONFIDENT_MODEL_ONLY_CANDIDATE",
         "odds_affected_selection":False,"price_used_in_decision":False,
         "new_model_fit":False,"forecast_unchanged":True,"betting_authorized":False,
         "production_modified":False,"official_S1_S2_approved":False}
    out["payload_sha256"]=digest(out)
    return out

def market_reference(decision, market_groups, *, source_pdf_sha256):
    """Signed fifth-reference report only. NEVER updates model decision SHA."""
    verified(decision,SCHEMA)
    if not isinstance(source_pdf_sha256,str) or len(source_pdf_sha256)!=64:
        raise EvidenceError("PDF_SHA_INVALID")
    rows=[]
    for family,keys in GROUPS.items():
        group=market_groups.get("MS" if family=="MS" else "KG" if family=="KG" else "GOALS_2.5",{})
        if group.get("status")!="FULL_MARKET_QUOTE_AVAILABLE":
            rows.append({"family":family,"status":"NO_COMPLETE_GROUP"})
            continue
        pairs=[]
        for key in keys:
            p=validprob(group["no_vig"][key]);o=group["prices"][key]
            if not isinstance(o,(int,float)) or not math.isfinite(o) or o<=1:
                raise EvidenceError("INVALID_REFERENCE_PRICE")
            model=next(x for x in decision["model_market_diagnostics"] if x["market"]==key)
            pairs.append({"market":key,"odds":o,"market_no_vig":p,
                          "model_probability":model["calibrated_probability"],
                          "model_minus_market_pp":round((model["calibrated_probability"]-p)*100,4)})
        rows.append({"family":family,"status":"DESCRIPTIVE_FIFTH_REFERENCE","pairs":pairs})
    out={"schema":REF_SCHEMA,"decision_sha256":decision["payload_sha256"],
         "forecast_sha256":decision["forecast_sha256"],"source_pdf_sha256":source_pdf_sha256,
         "odds_used_for_model_selection":False,"rows":rows,"betting_authorized":False}
    out["payload_sha256"]=digest(out)
    return out
