"""Research-only same-fixture historical M4/XGBoost predictions, 2026/27.

Uses existing frozen M4 implementation and locked M4 settings, without
editing production code. Each M4 fit includes ONLY earlier date results;
XGBoost training excludes all 2026/27 results, but date-shifted features
can update with earlier completed 2026/27 matches. This is a retrospective
research reconstruction, NEVER a SHA-sealed 2026 pre-match forecast.

The 2026/27 outcomes have already been viewed in other challenge reports;
this is a development/diagnostic pairing set, not an untouched holdout.
"""
from __future__ import annotations
import argparse,csv,json,sys,math
from collections import defaultdict
from pathlib import Path
import numpy as np

from ingest_openfootball import FIELDS
from next_season_test import load_archive,load_next,PARAMS,NEW_START
from xgb_challenger import make_features,fit,probabilities,LABEL

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments"/"263"))
from m4_integrated import Settings,fit_m4,predict_m4,score_markets,use_lock

def mk(r):
    return (r["league"],r["date"],r["home"],r["away"])

def run(input_path,lock_path,out_path):
    old=load_archive(input_path)
    new,qa=load_next()
    if not new:raise ValueError("no verified subsequent scores")
    combined=sorted(old+new,key=lambda r:(r["date"],r["league"],r["home"],r["away"]))
    keys=set()
    for r in combined:
        k=mk(r)
        if k in keys:raise ValueError("duplicate fixture "+str(k))
        keys.add(k)
    # Fitting M4 uses the exact original 2.6.3 routine; only data adapter is research.
    history=[{"league":r["league"],"season":r["season"].replace("-","-"),
       "match_date":r["date"],"fixture_id":"|".join(mk(r)),
       "home_id":r["home"],"away_id":r["away"],
       "home_goals":int(r["home_goals"]),"away_goals":int(r["away_goals"]),
       "result": "H" if int(r["home_goals"])>int(r["away_goals"]) else (
           "D" if r["home_goals"]==r["away_goals"] else "A")}
       for r in combined]
    lock=json.loads(Path(lock_path).read_text(encoding="utf8"))
    settings=use_lock(lock)
    historical_features=[r for r in make_features(combined) if r[3]>=40
                         and r[0]["date"]<NEW_START]
    future_features=[r for r in make_features(combined) if r[3]>=40
                     and r[0]["date"]>=NEW_START]
    xmodel=fit(historical_features,PARAMS)
    xprob=dict(zip((mk(r[0]) for r in future_features),
                   probabilities(xmodel,future_features)))
    pending=defaultdict(list)
    for row in new:pending[(row["league"],row["date"])].append(row)
    results=[];failures=[]
    for league,day in sorted(pending):
        # Fit on strictly earlier dated scored games; never today's results.
        model=fit_m4(history,league,day,settings)
        if model is None:
            failures.extend({"league":league,"date":day,"reason":"M4_NO_FIT",
                             "key":list(mk(r))} for r in pending[league,day])
            continue
        for row in pending[league,day]:
            k=mk(row); xp=xprob.get(k); lams=predict_m4(model,row["home"],row["away"])
            if xp is None or lams is None:
                failures.append({"league":league,"date":day,
                                 "reason":"NO_XGB_OR_M4_PRED","key":list(k)})
                continue
            p=score_markets(*lams)["markets"]["1X2"]
            actual="H" if int(row["home_goals"])>int(row["away_goals"]) else (
                "D" if int(row["home_goals"])==int(row["away_goals"]) else "A")
            x={name:float(xp[LABEL[name]]) for name in ("H","D","A")}
            item={"league":league,"date":day,"home_id":row["home"],
                  "away_id":row["away"],"result":actual,
                  "m4":p,"xgboost":x,
                  "train_history_m4_excludes_current_date":True,
                  "train_history_xgb_excludes_2026_27":True,
                  "mode":"RETROSPECTIVE_RECONSTRUCTION_NOT_SEALED"}
            results.append(item)
    if len(results)<100:
        raise ValueError("too few pairs, fail closed")
    result={"schema":"MC_M4_XGB_RETRO_PAIR_V1",
            "matched_count":len(results),"missing_count":len(failures),
            "period":"2026-07-01 to 2026-09-22",
            "m4_code":"original_unmodified_m4_integrated",
            "m4_settings":lock["settings"],
            "status":"RESEARCH_RECONSTRUCTION_NOT_PROSPECTIVE",
            "original_263_predictions_replayed":False,
            "cross_validation_ready":False,
            "pairs":results,"failures":failures,"source_qa":qa}
    dest=Path(out_path);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                    encoding="utf8")
    print(json.dumps({"matched_count":result["matched_count"],
                      "missing_count":result["missing_count"],
                      "m4_settings":result["m4_settings"],
                      "status":result["status"]},indent=2))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True);p.add_argument("--lock",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args();run(a.input,a.lock,a.out)
