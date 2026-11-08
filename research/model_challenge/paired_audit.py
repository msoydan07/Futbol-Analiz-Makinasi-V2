"""Read-only paired diagnostic audit of independent 1X2 challengers.

This uses the already-viewed historical evaluation window. It is NOT a new
blind test, cannot promote a model and does not imply profitable wagers.
No training, feature fitting or hyperparameter selection occurs here.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path

MODELS=("Elo","Poisson","XGBoost")
LABELS=("H","D","A")

def load_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))

def match_key(x):
    return tuple(x[k] for k in ("league","date","home","away"))

def probability(x):
    p=tuple(float(x[k]) for k in ("p_home","p_draw","p_away"))
    if any(not math.isfinite(v) or v<=0 or v>=1 for v in p) or abs(sum(p)-1)>1e-5:
        raise ValueError("invalid three-way probabilities")
    return p

def score(p,y):
    if y not in LABELS:
        raise ValueError("invalid result")
    return (-math.log(p[LABELS.index(y)]),
            sum((p[i]-int(LABELS[i]==y))**2 for i in range(3)))

def unique_index(rows):
    out={}
    for row in rows:
        k=match_key(row)
        if k in out:
            raise ValueError(f"duplicate fixture {k}")
        out[k]=row
    return out

def lower_mean(xs):
    return sum(xs)/len(xs) if xs else None

def block_interval(rows,metric_left,metric_right,iterations=1200,seed=263):
    grouped=defaultdict(list)
    for row in rows:
        grouped[row["date"]].append(row[metric_left]-row[metric_right])
    dates=sorted(grouped)
    if len(dates)<2:
        return [None,None]
    rng=random.Random(seed)
    means=[]
    for _ in range(iterations):
        total=n=0
        for _ in range(len(dates)):
            vals=grouped[dates[rng.randrange(len(dates))]]
            total+=sum(vals);n+=len(vals)
        means.append(total/n)
    means.sort()
    return [means[int(.025*(iterations-1))],means[int(.975*(iterations-1))]]

def audit(elo_file,poisson_file,xgb_file):
    sources={
      "Elo":unique_index(load_csv(elo_file)),
      "Poisson":unique_index(load_csv(poisson_file)),
      "XGBoost":unique_index(load_csv(xgb_file)),
    }
    keys=set(sources["XGBoost"])
    # The XGBoost file is explicitly only from 2025-07-01 onward.
    if any(k[1]<"2025-07-01" or k[1]>"2026-11-09" for k in keys):
        raise ValueError("non-evaluation XGBoost row")
    if not keys.issubset(sources["Elo"]) or not keys.issubset(sources["Poisson"]):
        raise ValueError("not all XGBoost fixtures exist in baselines")
    auditrows=[]
    for key in sorted(keys):
        e,p,x=(sources[m][key] for m in MODELS)
        if any(r.get("valid_warmup","true").lower()!="true" for r in (e,p)):
            raise ValueError("warmup mismatch")
        labels=(e["result"],p["result"],x["actual"])
        if len(set(labels))!=1:
            raise ValueError(f"label mismatch {key}")
        row={"league":key[0],"date":key[1],"home":key[2],"away":key[3],"result":labels[0]}
        for model,data in (("Elo",e),("Poisson",p),("XGBoost",x)):
            prob=probability(data)
            ll,brier=score(prob,labels[0])
            row[model+"_logloss"]=ll
            row[model+"_brier"]=brier
            row[model+"_top1"]=int(LABELS[prob.index(max(prob))]==labels[0])
            row[model+"_p_draw"]=prob[1]
            row[model+"_y_draw"]=int(labels[0]=="D")
        auditrows.append(row)
    if len(auditrows)<1000:
        raise ValueError("insufficient comparable matches")
    def group_metrics(rows):
        return {model:{
          "logloss":lower_mean([r[model+"_logloss"] for r in rows]),
          "brier":lower_mean([r[model+"_brier"] for r in rows]),
          "top1_accuracy":lower_mean([r[model+"_top1"] for r in rows]),
          "predicted_draw_rate":lower_mean([r[model+"_p_draw"] for r in rows]),
          "actual_draw_rate":lower_mean([r[model+"_y_draw"] for r in rows])}
          for model in MODELS}
    by_league=defaultdict(list);by_season=defaultdict(list)
    for r in auditrows:
        by_league[r["league"]].append(r)
        # Season start July 1 for diagnostics; calendar-year leagues would need different convention.
        season=int(r["date"][:4]) if r["date"][5:] >="07-01" else int(r["date"][:4])-1
        by_season[str(season)].append(r)
    paired={}
    for challenger in ("Poisson","XGBoost"):
        paired[challenger+"_minus_Elo"]={}
        for metric in ("logloss","brier"):
            a=challenger+"_"+metric;b="Elo_"+metric
            paired[challenger+"_minus_Elo"][metric]={
                "difference":lower_mean([r[a]-r[b] for r in auditrows]),
                "date_block_bootstrap_95pct":block_interval(auditrows,a,b)}
    for metric in ("logloss","brier"):
        a="XGBoost_"+metric;b="Poisson_"+metric
        paired.setdefault("XGBoost_minus_Poisson",{})[metric]={
            "difference":lower_mean([r[a]-r[b] for r in auditrows]),
            "date_block_bootstrap_95pct":block_interval(auditrows,a,b)}
    return {
       "schema":"MC_THREE_MODEL_PAIRED_AUDIT_V1",
       "status":"EXPLORATORY_ALREADY_VIEWED_EVALUATION",
       "fixture_count":len(auditrows),
       "league_count":len(by_league),
       "overall":group_metrics(auditrows),
       "league_results":{league:{"n":len(rows),"models":group_metrics(rows)}
                         for league,rows in sorted(by_league.items())},
       "season_results":{season:{"n":len(rows),"models":group_metrics(rows)}
                         for season,rows in sorted(by_season.items())},
       "paired":paired,
       "incumbent_263_comparison":{
           "status":"NOT_COMPARABLE",
           "reason":"Frozen 2.6.3 predictions use a distinct, source-gated cohort and history. Their as-of inputs and exact match keys cannot be reconstructed from aggregate historical JSON scores; do not combine or compare unmatched metrics."},
       "market_benchmark":"NOT_AVAILABLE_TIMESTAMPED_ODDS",
       "hybrid_selection":"NOT_PERMITTED_FROM_ALREADY_VIEWED_HOLDOUT",
       "betting_authorized":False,
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--elo",required=True)
    parser.add_argument("--poisson",required=True)
    parser.add_argument("--xgb",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    output=audit(args.elo,args.poisson,args.xgb)
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":output["status"],"n":output["fixture_count"],
                      "leagues":output["league_count"],"overall":output["overall"],
                      "paired":output["paired"],
                      "incumbent_263":output["incumbent_263_comparison"]["status"]},indent=2))

if __name__=="__main__":
    main()
