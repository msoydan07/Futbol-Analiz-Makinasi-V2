"""Broader independent *weekly-cutoff* historical M4/XGBoost paired check.

Every 2026/27 scored fixture (not a sampled weekday) eligible. To ensure
EXACTLY the same information cutoff for both experts, predictions are made
from the prior Monday 00:00 (date only, no weekly match outcome leakage).
The frozen M4 model is fitted separately at each league-week Monday.
XGBoost's feature state is constructed at the same league-week Monday.
XGBoost model was fitted ONLY using 2025/26 results; its parameters
are fixed. No prior 2026/27 outcome is used until a later week.

This is a retrospective, already-inspected, research-only check.
No assertions about actual pre-match as-of timestamps or profit.
"""
from __future__ import annotations
import argparse,csv,json,math,random,sys
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import numpy as np

from xgb_challenger import make_features,fit,LABEL
from next_season_test import PARAMS
from xgb_live_inference import feature_at

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments"/"263"))
from m4_integrated import fit_m4,predict_m4,score_markets,use_lock
from ten_league_263_paired_eval import losses,LABELS,CUTOFF

def monday(iso):
    d=date.fromisoformat(iso)
    return (d-timedelta(days=d.weekday())).isoformat()

def summarize(rows):
    return {m:{metric:sum(r[m+"_"+metric] for r in rows)/len(rows)
               for metric in ("logloss","brier","accuracy")}
            for m in ("M4","XGBoost","Fixed50")}

def audit(source,lock_path,out_path):
    rows=list(csv.DictReader(open(source,encoding="utf8",newline="")))
    if len(rows)!=4518:raise ValueError("expected owner accepted 4518 snapshot")
    rows.sort(key=lambda r:(r["date"],r["league"],r["home"],r["away"]))
    if len({(r["league"],r["date"],r["home"],r["away"]) for r in rows})!=len(rows):
        raise ValueError("duplicate history fixture")
    train=[r for r in make_features(rows) if r[0]["date"]<CUTOFF and r[3]>=40]
    if len(train)<1500:raise ValueError("insufficient XGB preceding-season examples")
    xgb=fit(train,PARAMS)
    history=[{"league":r["league"],"season":r["season"],"match_date":r["date"],
         "fixture_id":"|".join((r["league"],r["date"],r["home"],r["away"])),
         "home_id":r["home"],"away_id":r["away"],
         "home_goals":int(r["home_goals"]),"away_goals":int(r["away_goals"]),
         "result":"H" if int(r["home_goals"])>int(r["away_goals"]) else
             "A" if int(r["home_goals"])<int(r["away_goals"]) else "D"}
             for r in rows]
    lock=json.loads(Path(lock_path).read_text(encoding="utf8"))
    setting=use_lock(lock)
    batches=defaultdict(list)
    for r in rows:
        if r["date"]>=CUTOFF:
            batches[(r["league"],monday(r["date"]))].append(r)
    evaluated=[];failed=[];leagues=defaultdict(list)
    for (league,week),fixtures in sorted(batches.items()):
        # Both experts share MONDAY cutoff; no outcomes from this week.
        history_before=[r for r in rows if r["date"]<week]
        m4fit=fit_m4(history,league,week,setting)
        for r in fixtures:
            if not m4fit:
                failed.append({"league":league,"week":week,"why":"M4_NO_FIT"})
                continue
            lambdas=predict_m4(m4fit,r["home"],r["away"])
            if lambdas is None:
                failed.append({"league":league,"week":week,"why":"M4_NO_LAMBDA"})
                continue
            try:
                x,detail=feature_at(history_before,league,r["home"],r["away"],date.fromisoformat(week))
            except ValueError as err:
                failed.append({"league":league,"week":week,"why":str(err)})
                continue
            if x.shape!=(25,):
                raise ValueError("feature contract mismatch")
            prediction=xgb.predict_proba(x.reshape(1,-1))[0]
            mp=score_markets(*lambdas)["markets"]["1X2"]
            xp={k:float(prediction[LABEL[k]]) for k in LABELS}
            hp={k:(mp[k]+xp[k])/2 for k in LABELS}
            h,a=int(r["home_goals"]),int(r["away_goals"])
            y="H" if h>a else "A" if a>h else "D"
            rec={"league":league,"date":r["date"],"week":week,
                 "result":y}
            for name,p in (("M4",mp),("XGBoost",xp),("Fixed50",hp)):
                ll,br,acc=losses(p,y)
                rec[name+"_logloss"]=ll
                rec[name+"_brier"]=br
                rec[name+"_accuracy"]=acc
            evaluated.append(rec)
            leagues[league].append(rec)
    if len(evaluated)<450:
        raise ValueError("too few weekly all-fixture paired results")
    byweek=defaultdict(list)
    for r in evaluated:byweek[r["week"]].append(r)
    clusters=sorted(byweek);rng=random.Random(263);bootstrap=[]
    for _ in range(1500):
        drawn=[byweek[clusters[rng.randrange(len(clusters))]] for _ in clusters]
        vals=[r for batch in drawn for r in batch]
        bootstrap.append(sum(r["XGBoost_logloss"]-r["M4_logloss"] for r in vals)/len(vals))
    bootstrap.sort()
    report={"schema":"MC_263_TENLEAGUE_WEEKLY_FREEZE_ALL_V1",
       "status":"EXPLORATORY_PRIOR_RESULT_WINDOW_ALREADY_VIEWED",
       "cutoff":"MONDAY_00_00_DATE_ONLY_FOR_BOTH_MODELS",
       "training_before":CUTOFF,"trained_xgboost_n":len(train),
       "total_season_fixtures":sum(len(v) for v in batches.values()),
       "matched":len(evaluated),"unmatched":len(failed),
       "failure_reasons":dict(__import__("collections").Counter(x["why"] for x in failed)),
       "frozen_m4_settings":lock["settings"],"xgb_parameters":PARAMS,
       "overall":summarize(evaluated),
       "per_league":{name:{"n":len(v),"models":summarize(v)}
                     for name,v in sorted(leagues.items())},
       "xgb_minus_m4_logloss_weekcluster_95pct":
            [bootstrap[37],bootstrap[1461]],
       "independently_reevaluated_original_263_predictions":False,
       "results_not_independently_score_verified":True,
       "no_market_odds":True,"research_only":True,"betting_authorized":False,
       "source_accuracy_not_licensed_for_claims":True,
       "production_promotion":False}
    dest=Path(out_path);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:report[k] for k in ("total_season_fixtures","matched",
        "unmatched","failure_reasons","overall",
        "xgb_minus_m4_logloss_weekcluster_95pct")},indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for arg in ("source","lock","out"):p.add_argument("--"+arg,required=True)
    a=p.parse_args();audit(a.source,a.lock,a.out)
