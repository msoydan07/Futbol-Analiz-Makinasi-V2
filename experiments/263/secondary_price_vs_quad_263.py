"""Read-only secondary quoted odds vs SHA-sealed REAL early pre-KO model.

NEVER an executable bookmaker quote, value-bet recommendation, T-60 lock,
live provider check, S1/S2 acceptance, or accepted 96-cohort entry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlparse

QUOTES_SCHEMA = "263_secondary_market_price_research_v1"
REPORT_SCHEMA = "263_secondary_price_vs_early_quad_v1"
FORECAST_SHA = "1038b6e9cd1f0bcbceb97367e261bc579b07a56e4e2dc5193c2f247e51e18ffb"
MARKET_KEYS = {
    "MS": ("MS1","MSX","MS2"),
    "GOALS_2.5": ("UNDER_2.5","OVER_2.5"),
    "KG": ("BTTS_YES","BTTS_NO"),
}
MS_TRANSLATION = {"MS1":"H","MSX":"D","MS2":"A"}


def canonical(payload):
    return json.dumps(payload,ensure_ascii=False,sort_keys=True,
                      separators=(",",":"),allow_nan=False).encode("utf-8")


def no_vig(odds):
    if not odds or any(isinstance(x,bool) or not isinstance(x,(float,int))
                       or not math.isfinite(x) or x<=1 or x>1000 for x in odds.values()):
        raise ValueError("invalid_secondary_odds")
    overround=sum(1/float(x) for x in odds.values())
    if not (1.0 < overround < 1.45):
        raise ValueError("invalid_or_implausible_bookmaker_margin")
    return {key:(1/float(value))/overround for key,value in odds.items()},overround-1


def compare(forecast,price):
    if forecast.get("payload_sha256") != FORECAST_SHA:
        raise ValueError("wrong_previously_committed_forecast_sha")
    without_sha={k:v for k,v in forecast.items() if k!="payload_sha256"}
    if hashlib.sha256(canonical(without_sha)).hexdigest()!=FORECAST_SHA:
        raise ValueError("pre_kickoff_forecast_integrity_failed")
    if forecast.get("status") != "EXPERIMENTAL_EARLY_SHADOW_UNVERIFIED_SOURCE_NO_BETTING":
        raise ValueError("not_actual_early_shadow_forecast")
    if (forecast.get("data",{}).get("human_source_acceptance") is not False
        or forecast["data"].get("research_shadow_unverified_source") is not True):
        raise ValueError("research_shadow_label_changed")
    fixture=forecast["fixture"]
    if (price.get("schema")!=QUOTES_SCHEMA or price.get("quote_source_tier")!="SECONDARY_AGGREGATOR_UNVERIFIED"
        or urlparse(price.get("source_url","")).hostname!="oddsfilter.com"
        or price.get("source_provider")!="OddsFilter (aggregator; not bookmaker)"
        or price.get("bookmaker_as_listed")!="Betano"):
        raise ValueError("bad_secondary_quote_origin")
    if (price.get("direct_bookmaker_confirmation") is not False
        or price.get("single_synchronized_market_observation_proven") is not False
        or price.get("eligible_for_live_quote_lock") is not False
        or price.get("eligible_for_S1_S2") is not False):
        raise ValueError("secondary_quote_cannot_claim_official_or_live_eligibility")
    if (price["price_1x2_capture_time_claim_utc"]!="2026-11-02T16:52:00+00:00"
        or price["price_ou25_capture_time_claim_utc"] is not None
        or price["price_btts_capture_time_claim_utc"] is not None):
        raise ValueError("price_capture_time_not_proven")
    if (price["fixture"].get("kickoff_utc")!=fixture["kickoff_utc"]
        or price["fixture"].get("league")!=fixture["league"]):
        raise ValueError("source_quote_fixture_wrong")
    market_inputs=price["price_markets"]
    if set(market_inputs)!=set(MARKET_KEYS):
        raise ValueError("exact_three_secondary_market_groups_required")
    if set(forecast.get("model_predictions",{}))!={"B","C2","C3","M4"}:
        raise ValueError("four_source_predictions_required")
    markets={}
    for group,keys in MARKET_KEYS.items():
        odds=market_inputs[group]
        if not isinstance(odds,dict) or set(odds)!=set(keys):
            raise ValueError("incomplete_market_or_wrong_counterprices")
        fair,margin=no_vig(odds)
        if abs(sum(fair.values())-1)>1e-10:
            raise ValueError("marj_not_removed")
        models={}
        for model,record in forecast["model_predictions"].items():
            if record["status"]!="AVAILABLE":raise ValueError("unavailable_model")
            m=record["goals"]["markets"]
            comparisons={}
            for key in keys:
                p=(m["1X2"][MS_TRANSLATION[key]] if group=="MS" else m[key])
                if not isinstance(p,(float,int)) or not 0<=p<=1:
                    raise ValueError("invalid_model_probability")
                comparisons[key]={
                    "model_probability_pct":round(100*p,2),
                    "reference_no_vig_pct":round(100*fair[key],2),
                    "difference_percentage_points":round(100*(p-fair[key]),2),
                    "indicative_math_EV_pct_NOT_BET_SIGNAL":round(100*(p*odds[key]-1),2)}
            models[model]=comparisons
        markets[group]={"listed_price_odds":odds,
                        "bookmaker_overround_pct":round(100*margin,2),
                        "no_vig_reference_pct":{key:round(100*v,2) for key,v in fair.items()},
                        "model_comparison":models}
    return {"schema":REPORT_SCHEMA,
            "status":"SECONDARY_RESEARCH_COMPARISON_ONLY_NOT_CURRENT_BETTABLE_ODDS",
            "fixture":price["fixture"],"early_forecast_created_at_utc":forecast["created_at_utc"],
            "early_forecast_sha256":FORECAST_SHA,
            "secondary_quote_source":price["source_url"],
            "listed_bookmaker":price["bookmaker_as_listed"],
            "single_same_time_multi_market_snapshot_proven":False,
            "direct_bookmaker_price_validation":False,
            "prices_may_be_stale_and_incompatible_with_T60":True,
            "qualified_96_cohort":False,"S1_S2_eligible":False,
            "official_pilot_count_increment":0,"betting_authorized":False,
            "markets":markets}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--forecast",required=True)
    ap.add_argument("--secondary-quote",required=True)
    ap.add_argument("--report",required=True)
    args=ap.parse_args()
    a=json.loads(Path(args.forecast).read_text(encoding="utf-8"))
    b=json.loads(Path(args.secondary_quote).read_text(encoding="utf-8"))
    result=compare(a,b)
    path=Path(args.report)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)
        f.write("\n")
    print(json.dumps({"status":result["status"],"markets":len(result["markets"]),
                      "S1_S2_eligible":False,"forecast_sha256":FORECAST_SHA},
                     ensure_ascii=False))


if __name__=="__main__":main()
