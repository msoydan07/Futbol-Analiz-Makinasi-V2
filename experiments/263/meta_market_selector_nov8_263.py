"""Independent retrospective November 8 SHAs vs fixed/dynamic selectors.
The training features are 2026 Aug-Oct PREVIOUS predictions only; Nov results
are used ONLY for postmatch scoring. Research-only, not independent federation
verification of all archival results; never rewrite original seals.
"""
import argparse
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path

from chrono_goal_stage2_263 import load_predictions
from market_fifth_baseline_263 import sealed_payload
from meta_market_selector_263 import FAMILIES, choose, score, select_static, summary

ROOT=Path(__file__).resolve().parents[2]
ARCHIVE=Path("data/results_only_263/nov8_new100_terminal_archive_20261112.json")
MODELS=("C3","M4")

def _prediction_from_immutable(root, ref):
    path=root/ref["forecast_path"]
    if not path.is_file():raise ValueError("MISSING_ORIGINAL_FORECAST")
    f=json.loads(path.read_text(encoding="utf-8"))
    sealed_payload(f,"quad_forward_263_v1")
    if f["payload_sha256"]!=ref["forecast_sha256"]:
        raise ValueError("SHA_SEALED_FORECAST_MISMATCH")
    fx=f["fixture"]
    if any(fx[k]!=ref[k] for k in ("league","kickoff_utc")):
        raise ValueError("ORIGINAL_FIXTURE_CHANGED")
    if fx["match_local_date"]!="2026-11-08":
        raise ValueError("NOT_NOVEMBER_8")
    if not datetime.fromisoformat(f["created_at_utc"])<datetime.fromisoformat(fx["kickoff_utc"]):
        raise ValueError("FORECAST_WAS_NOT_PREMATCH")
    h,a=ref["score"]
    if any(not isinstance(n,int) or isinstance(n,bool) or not 0<=n<=20 for n in (h,a)):
        raise ValueError("INVALID_ARCHIVED_RESULT")
    goals=h+a
    obs={
        "MS1":int(h>a),"MSX":int(h==a),"MS2":int(h<a),
        "BTTS_YES":int(h>0 and a>0),"BTTS_NO":int(h==0 or a==0)}
    for line in ("1.5","2.5","3.5"):
        over=int(goals>float(line))
        obs["OVER_"+line]=over
        obs["UNDER_"+line]=1-over
    probabilities={}
    for model in MODELS:
        m=f["model_predictions"].get(model,{})
        if m.get("status")!="AVAILABLE":continue
        mks=m["goals"]["markets"]
        ps={"MS1":mks["1X2"]["H"],"MSX":mks["1X2"]["D"],"MS2":mks["1X2"]["A"]}
        for mk in ("BTTS_YES","BTTS_NO","OVER_1.5","UNDER_1.5",
                   "OVER_2.5","UNDER_2.5","OVER_3.5","UNDER_3.5"):
            ps[mk]=mks[mk]
        probabilities[model]=ps
    return {"date":"2026-11-08","league":ref["league"],"p":probabilities,"obs":obs,
            "evidence_grade":ref["evidence_grade"]}

def evaluate_nov(predictions,root=ROOT):
    history=load_predictions(predictions)
    if len(history)!=880 or any(x["date"]>="2026-11-08" for x in history):
        raise ValueError("TRAINING_NOT_STRICTLY_EARLIER")
    archive=json.loads((root/ARCHIVE).read_text(encoding="utf-8"))
    if (archive.get("schema")!="263_NOV8_NEW100_POSTMATCH_TERMINAL_ARCHIVE_V1"
        or archive.get("registered")!=40 or archive.get("completed")!=39
        or archive.get("postponed")!=1
        or archive.get("human_attestation_count")!=0):
        raise ValueError("UNACCEPTED_RESULT_ARCHIVE")
    refs=archive["rows"]
    rows=[_prediction_from_immutable(root,ref) for ref in refs if ref.get("score") is not None]
    if len(rows)!=39:raise ValueError("NOT_39_ARCHIVED_RESULTS")
    results=[]
    for row in rows:
        fixed={f:select_static(row,f,"fixed") for f in FAMILIES}
        dynamic={f:choose(row,history,f)[0] for f in FAMILIES}
        all_m4={f:select_static(row,f,"all_m4") for f in FAMILIES}
        all_c3={f:select_static(row,f,"all_c3") for f in FAMILIES}
        results.append({"row":row,"fixed":fixed,"dynamic":dynamic,
                        "values":{
                          "fixed":score(row,fixed),"dynamic":score(row,dynamic),
                          "all_m4":score(row,all_m4),"all_c3":score(row,all_c3)}})
    scores={k:summary([{"values":z["values"][k]} for z in results])
            for k in ("fixed","dynamic","all_m4","all_c3")}
    switches={f:sum(z["fixed"][f]!=z["dynamic"][f] for z in results) for f in FAMILIES}
    return {"schema":"263_meta_nov8_existing_shas_research_v1",
        "retrospective_history_n":880,"sealed_forecasts_scored":39,"registered_n":40,
        "postponed_unscored":1,"latest_training_day":max(x["date"] for x in history),
        "evaluation_day":"2026-11-08","distinct_evaluation_days":1,
        "source_grades":dict(Counter(r["evidence_grade"] for r in rows)),
        "metrics":scores,"switches":switches,
        "training_future_result_leakage":False,"sha_seals_changed":False,
        "main_model_changed":False,"operational_policy_changed":False,
        "no_xg":True,"no_odds_or_ev":True,
        "limitation":"Only 3 results direct network-verified TFF; other archived web research. Single date, no valid day-block bootstrap CI. Research comparison only."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--predictions",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    report=evaluate_nov(args.predictions)
    path=Path(args.output)
    if path.exists():raise ValueError("NO_OVERWRITE")
    path.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("META_EXISTING_NOVEMBER_SHA_RESULTS="+json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
