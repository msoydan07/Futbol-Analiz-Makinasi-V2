"""ONE-OFF user-requested 20 Nov evening research, NOT morning new100 sealing.

Exact three pre-kickoff fixtures only. Official fixture gateway, accepted
quad history/model code, current model-first specialists and as-of baseline.
No price/API input. Artifacts remain uncommitted research and cannot be
described as official SHA-locked pilot forecasts.
"""
import argparse,json,traceback
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway
from forward_quad import predict_quad_from_verified_gate
from forward_empirical_baseline_263 import produce as empirical
from model_first_decision_263 import select as model_first
from check_active_decisions_263 import verify_active_policy

DAY="2026-11-20"
TR=ZoneInfo("Europe/Istanbul")
GAMES=[
    ("GER1","FC Bayern München","1. FC Köln"),
    ("FRA1","ESTAC Troyes","Havre AC"),
    ("ESP1","Athletic Club","RCD Espanyol de Barcelona")
]
HISTORY="data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
BASE="m4_quad_base/historical_results.csv"
ACCEPTANCE="data/results_only_263/4617_research_input_provenance.json"
M4LOCK="experiments/263/m4_lock.json"
SELECTLOCK="experiments/263/model_first_selection_lock_20261120.json"

def run(out="."):
    verify_active_policy()
    now=datetime.now(timezone.utc)
    if now.astimezone(TR).date().isoformat()!=DAY:
        raise ValueError("NO_RETROACTIVE_LATE_REQUEST")
    root=Path(out);root.mkdir(parents=True,exist_ok=True)
    gateway=OfficialFixtureGateway()
    lock=json.loads(Path(SELECTLOCK).read_text(encoding="utf-8"))
    items=[]
    for league,home,away in GAMES:
        row={"league":league,"home":home,"away":away,"state":"BLOCKED",
             "source":"LIVE_OFFICIAL_LEAGUE_GATE","price_used":False}
        try:
            gate=gateway.lookup(league,home,away)
            row["official_evidence"]=gateway.latest_match_evidence(league,home,away)
            if gate.get("status")!="VERIFIED":
                raise ValueError("OFFICIAL_GATE:"+str(gate.get("reason")))
            ko=datetime.fromisoformat(gate["kickoff_utc"].replace("Z","+00:00"))
            if not now<ko or ko.astimezone(TR).date().isoformat()!=DAY:
                raise ValueError("PREKICKOFF_TODAY_ONLY")
            row["kickoff_utc"]=ko.isoformat()
            fc_path,fc=predict_quad_from_verified_gate(
                 gate,HISTORY,root/"forecasts",M4LOCK,now=now,
                 base=BASE,source_audit=ACCEPTANCE)
            row["forecast_sha256"]=fc["payload_sha256"]
            row["forecast_path"]=str(fc_path)
            row["model_states"]={k:v["status"] for k,v in fc["model_predictions"].items()}
            available=sum(x=="AVAILABLE" for x in row["model_states"].values())
            if (available<3 or any(row["model_states"][m]!="AVAILABLE" for m in ("C3","M4"))):
                raise ValueError("CURRENT_SPECIALIST_COVERAGE_GATE")
            base=empirical(fc,HISTORY,now=now)
            decision=model_first(fc,base,lock,now=now)
            row.update(state="PREMATCH_RESEARCH_ONLY_NOT_SEALED",
                       baseline_sha256=base["payload_sha256"],
                       decision_sha256=decision["payload_sha256"],
                       selection_status=decision["status"],
                       main=decision["main_candidate"],
                       alternative=decision["alternative_candidate"],
                       diagnostics=decision["model_market_diagnostics"],
                       brier_family_anchors=decision["fixed_family_experts"],
                       price_used=False)
            (root/(league+"_research.json")).write_text(json.dumps(
                {"forecast":fc,"baseline":base,"model_first_decision":decision},
                ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
        except Exception as exc:
            row.update(state="BLOCKED",error=type(exc).__name__+":"+str(exc)[:240])
        items.append(row)
    result={"research_type":"NOV20_USER_EXPLICIT_EVENING_NOT_NEW100",
            "created_at_utc":now.isoformat(),
            "official_forecast_seals_committed":0,
            "odds_scrapes":0,
            "odds_used_for_choice":False,
            "items":items}
    (root/"summary.json").write_text(json.dumps(result,ensure_ascii=False,
                  indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,allow_nan=False))
    return result

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--out",default="/tmp/nov20_evening_user_research")
    run(a.parse_args().out)
