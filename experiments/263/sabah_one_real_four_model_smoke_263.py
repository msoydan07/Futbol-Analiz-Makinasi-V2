"""One live official 2.6.3 four-model test in /tmp, never the 96 pilot.

One predeclared fixture, one actual data/model/decision path, zero odds.
The temporary model output is DELETED; evidence is a separate research-only
smoke report. The named-match identity gate remains unchanged.
"""
from __future__ import annotations
import argparse,hashlib,json,tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from sabah_named_source_acceptance_263 import (
    named_only_runner,read_source_readiness,HISTORY,ACCEPTANCE,M4LOCK,DEVLOCK)
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway

SCHEMA="263_ONE_LIVE_FOUR_MODEL_DRY_RUN_V1"
TR=ZoneInfo("Europe/Istanbul")
SAMPLE=("ESP1","Valencia","Real Madrid")
class DryRunBlocked(ValueError):pass

def run(root=".",now=None,lookup=None,predictor=None,baseliner=None,decider=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise DryRunBlocked("AWARE_TIME_REQUIRED")
    now=now.astimezone(timezone.utc)
    result={"schema":SCHEMA,"created_at_utc":now.isoformat(),
            "match":{"league":SAMPLE[0],"home":SAMPLE[1],"away":SAMPLE[2]},
            "status":"BLOCKED_NOT_RUN","reason":None,
            "model_results":{},"sample_is_pilot_record":False,
            "new_forward_registrations":0,"pinnacle_or_bookmaker_calls":0,
            "price_observation":None,"betting_authorized":False,
            "source_acceptance_class":"NOT_CHECKED",
            "forecast_sha256":None,"decision_sha256":None,
            "temporary_output_destroyed_after_run":True}
    try:
        research=read_source_readiness(root,now)
        result["source_acceptance_class"]=research["status"]
        if research["status"]!="OWNER_ACCEPTED_LIMITED_EXPERIMENTAL_INPUTS_ONLY":
            raise DryRunBlocked("SOURCE_NOT_ACCEPTED_FOR_LIMITED_RESEARCH")
        if lookup is None:
            g=OfficialFixtureGateway(gate_runner=named_only_runner)
            gate=g.lookup(*SAMPLE)
            result["page_evidence"]=g.latest_match_evidence(*SAMPLE)
        else:gate=lookup(*SAMPLE)
        if not isinstance(gate,dict) or gate.get("status")!="VERIFIED":
            raise DryRunBlocked("LIVE_NAMED_MATCH_GATE:"+str(gate.get("reason") if isinstance(gate,dict) else "INVALID"))
        ko=datetime.fromisoformat(gate["kickoff_utc"].replace("Z","+00:00")).astimezone(timezone.utc)
        if ko.astimezone(TR).date()!=now.astimezone(TR).date():
            raise DryRunBlocked("NOT_TODAYS_MATCH")
        if now+timedelta(minutes=20)>=ko:
            raise DryRunBlocked("LESS_THAN_20_MINUTES_TO_KICKOFF")
        if predictor is None:
            from forward_quad import predict_quad_from_verified_gate as predictor
        if baseliner is None:
            from forward_empirical_baseline_263 import produce as baseliner
        if decider is None:
            from four_model_value_policy_263 import decide as decider
        root=Path(root)
        with tempfile.TemporaryDirectory(prefix="263_smoke_only_") as scratch:
            now=datetime.now(timezone.utc)
            if now+timedelta(minutes=20)>=ko:
                raise DryRunBlocked("NOT_ENOUGH_PRE_KO_TIME_AT_MODEL_START")
            target,forecast=predictor(
                gate,root/HISTORY,scratch,root/M4LOCK,now=now,
                base=root/"m4_quad_base/historical_results.csv",
                source_audit=root/ACCEPTANCE)
            from market_fifth_baseline_263 import sealed_payload
            from classification_odds_263 import canonical_markets
            sealed_payload(forecast,"quad_forward_263_v1")
            actual_models={}
            for name in ("B","C2","C3","M4"):
                model=forecast["model_predictions"][name]
                if model.get("status")!="AVAILABLE":
                    actual_models[name]={"status":model.get("status","UNAVAILABLE")}
                else:
                    vals=canonical_markets(model["goals"]["markets"])
                    actual_models[name]={"status":"AVAILABLE",
                                         "MS1":vals["MS1"],"MSX":vals["MSX"],
                                         "MS2":vals["MS2"],"KG_VAR":vals["BTTS_YES"],
                                         "OVER_2_5":vals["OVER_2.5"]}
            if not all(actual_models[x]["status"]=="AVAILABLE" for x in ("B","C3","M4")):
                raise DryRunBlocked("CORE_THREE_MODELS_UNAVAILABLE")
            t=datetime.now(timezone.utc)
            baseline=baseliner(forecast,root/HISTORY,now=t)
            dev=json.loads((root/DEVLOCK).read_text(encoding="utf-8"))
            decision=decider(forecast,baseline,dev,observation=None,now=t)
            sealed_payload(decision,"263_four_model_value_decision_research_v1")
            if (decision.get("status")!="RESEARCH_PAS" or
                decision.get("quote_sha256") is not None or
                decision.get("main_candidate") is not None):
                raise DryRunBlocked("NO_ODDS_MUST_BE_RESEARCH_PAS")
            if not (forecast["fixture"]["fixture_verification"]=="VERIFIED_BY_LIVE_OFFICIAL_GATE"
                and t<ko):
                raise DryRunBlocked("INVALID_OFFICIAL_FIXTURE_OR_POSTKICKOFF")
            result.update(status="RESEARCH_DRY_RUN_PASS",reason=None,
                live_kickoff_utc=ko.isoformat(),
                source_snapshot_sha256=forecast["data"]["snapshot_sha256"],
                source_acceptance_engine=forecast["data"]["snapshot_acceptance"],
                model_results=actual_models,
                forecast_sha256=forecast["payload_sha256"],
                decision_sha256=decision["payload_sha256"],
                baseline_sha256=baseline["payload_sha256"],
                decision_status=decision["status"],
                temporary_model_path_not_persisted=True)
    except Exception as err:
        result["status"]="BLOCKED_DIAGNOSTIC_ONLY"
        result["reason"]=type(err).__name__+":"+str(err)[:260]
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    args=p.parse_args()
    result=run()
    target=Path(args.out);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")
    print(json.dumps({"status":result["status"],
                      "reason":result["reason"],
                      "models":{k:v.get("status") for k,v in result["model_results"].items()},
                      "decision":result.get("decision_status"),
                      "forecasts_recorded":result["new_forward_registrations"],
                      "odds_calls":result["pinnacle_or_bookmaker_calls"]},ensure_ascii=False))
    if result["status"]!="RESEARCH_DRY_RUN_PASS":
        raise SystemExit("OFFICIAL_FOUR_MODEL_SMOKE_BLOCKED_SEE_ARTIFACT")
if __name__=="__main__":main()
