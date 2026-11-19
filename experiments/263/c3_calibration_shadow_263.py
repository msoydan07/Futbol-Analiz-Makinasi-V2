"""SHA-tracked frozen C3 KG/O25 calibration SHADOW (not the decision).

The shadow compares raw C3 to pre-existing Aug-Sep shrinkage weights using
only an AS-OF league-frequency baseline. It does not alter original model,
probabilities used for market selection, odds, PAS, seals, or main M4.
"""
from __future__ import annotations
import math
from model_first_decision_263 import verified,digest,canonical

SCHEMA="263_C3_KG_O25_SHADOW_NOT_DECISION_V1"
DEV_SCHEMA="263_forward_dev_calibration_lock_v1"
PAIR={
 "KG":("BTTS_YES","BTTS_NO"),
 "O25":("OVER_2.5","UNDER_2.5"),
}

def _lock(d):
    if (d.get("schema")!=DEV_SCHEMA or
        d.get("official_approval") is not False or
        d.get("development_period")!="2026-08-01/2026-09-30" or
        d.get("evaluation_period_not_used_for_weights")!="2026-10-01/2026-10-29" or
        d.get("payload_sha256")!=digest({k:v for k,v in d.items() if k!="payload_sha256"})):
        raise ValueError("C3_SHADOW_DEV_LOCK_UNTRUSTED")
    cal=d.get("calibration",{}).get("C3",{})
    weights={}
    for fam,(yes,no) in PAIR.items():
        a=cal[yes]
        if (a!=cal[no] or a.get("n")!=580 or a.get("available") is not True):
            raise ValueError("C3_SHADOW_NOT_COMPLETE_PAIR")
        w=a.get("weight")
        if (isinstance(w,bool) or not isinstance(w,(int,float)) or
            not math.isfinite(w) or not 0<w<1):
            raise ValueError("C3_SHADOW_INVALID_FROZEN_WEIGHT")
        weights[fam]=w
    return weights

def make_shadow(forecast,baseline,model_decision,frozen_development):
    verified(forecast,"quad_forward_263_v1")
    verified(baseline,"263_asof_market_baseline_v2")
    verified(model_decision,"263_MODEL_FIRST_FOUR_MODEL_DECISION_RESEARCH_V2")
    if (baseline["forecast_sha256"]!=forecast["payload_sha256"] or
        model_decision["forecast_sha256"]!=forecast["payload_sha256"] or
        model_decision["baseline_sha256"]!=baseline["payload_sha256"] or
        model_decision.get("price_used_in_decision") is not False):
        raise ValueError("C3_SHADOW_CROSS_RECORD_SHA_MISMATCH")
    weights=_lock(frozen_development)
    c3=forecast["model_predictions"].get("C3",{})
    families={}
    if c3.get("status")=="AVAILABLE":
        p=canonical(c3["goals"]["markets"])
        b=baseline["markets"]
        for fam,(yes,no) in PAIR.items():
            raw=p[yes]
            base=b[yes]
            if (not isinstance(base,(float,int)) or isinstance(base,bool)
                or not math.isfinite(base) or not 0<=base<=1 or
                abs(b[yes]+b[no]-1)>1e-7):
                raise ValueError("C3_SHADOW_ASOF_BASELINE_NOT_COMPLEMENTARY")
            weight=weights[fam]
            q=base+weight*(raw-base)
            if not 0<=q<=1:
                raise ValueError("C3_SHADOW_OUT_OF_BOUNDS")
            families[fam]={
                "model":"C3","raw_positive":raw,"raw_negative":p[no],
                "frozen_shrunken_positive":q,
                "frozen_shrunken_negative":1-q,
                "asof_league_positive":base,
                "source_dev_weight":weight,
                "source_dev_matches":580,
                "production_calibration_promoted":False}
    result={"schema":SCHEMA,
        "status":"RESEARCH_SHADOW_ONLY" if families else "C3_UNAVAILABLE_SHADOW_SKIPPED",
        "forecast_sha256":forecast["payload_sha256"],
        "baseline_sha256":baseline["payload_sha256"],
        "model_decision_sha256":model_decision["payload_sha256"],
        "dev_lock_sha256":frozen_development["payload_sha256"],
        "families":families,
        "selection_changed":False,"model_probabilities_changed":False,
        "main_or_alternative_changed":False,"pas_changed":False,
        "market_odds_used":False,"new_forecast_seal_created":False,
        "do_not_use_to_pick":True,"research_only":True}
    result["payload_sha256"]=digest(result)
    return result
