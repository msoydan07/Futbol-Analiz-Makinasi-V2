"""Frozen four-way retrospective stress audit; never re-fit on viewed holdout.

Report predeclared model comparisons by league, month, calendar quarter,
minimum coverage, leave-one-league-out, date-block bootstrap and draw
calibration. The goal is a defensible RESEARCH model decision and
identification of weak slices, not pretending the old 2.6.3 was backtested.
"""
from __future__ import annotations
import argparse,csv,json,math,random
from collections import defaultdict
from pathlib import Path

LABELS=("H","D","A")
MODELS=("Elo","Poisson","XGBoost","EqualWeightHybrid")
def key(r):
    return (r["league"],r["date"],r["home"],r["away"])
def load(p):
    with open(p,encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    index={}
    for r in rows:
        k=key(r)
        if k in index:raise ValueError("duplicate "+str(k))
        index[k]=r
    return index
def probability(r):
    p=[float(r[x]) for x in ("p_home","p_draw","p_away")]
    if not all(math.isfinite(v) and v>0 for v in p) or abs(sum(p)-1)>1e-5:
        raise ValueError("invalid forecast")
    return [v/sum(p) for v in p]
def scoring(p,label):
    y=[int(label==x) for x in LABELS]
    return -math.log(p[LABELS.index(label)]),sum((p[i]-y[i])**2 for i in range(3))
def gather(paths):
    indexed={name:load(path) for name,path in paths.items()}
    keys=set(indexed["XGBoost"])
    if len(keys)<1000 or any(keys!=set(indexed[m])&keys for m in ("Elo","Poisson","EqualWeightHybrid")):
        raise ValueError("missing XGBoost fixtures")
    out=[]
    for k in sorted(keys):
        actual=[indexed["Elo"][k]["result"],indexed["Poisson"][k]["result"],
                indexed["XGBoost"][k]["actual"],indexed["EqualWeightHybrid"][k]["result"]]
        if len(set(actual))!=1:raise ValueError("result mismatch")
        if any(indexed[m][k]["valid_warmup"].lower()!="true" for m in ("Elo","Poisson")):
            raise ValueError("warmup mismatch")
        d={"league":k[0],"date":k[1],"result":actual[0]}
        for m in MODELS:
            p=probability(indexed[m][k])
            ll,b=scoring(p,actual[0])
            d[m+"_logloss"]=ll
            d[m+"_brier"]=b
            d[m+"_draw"]=p[1]
            d[m+"_correct"]=float(LABELS[p.index(max(p))]==actual[0])
        out.append(d)
    if len(out)!=4331:
        raise ValueError("unexpected cohort size")
    return out

def mean(rows,field):
    return sum(r[field] for r in rows)/len(rows) if rows else None
def metrics(rows):
    return {"n":len(rows),"models":{m:{
        "logloss":mean(rows,m+"_logloss"),
        "brier":mean(rows,m+"_brier"),
        "top1_accuracy":mean(rows,m+"_correct"),
        "mean_predicted_draw":mean(rows,m+"_draw")}
        for m in MODELS},"actual_draw":mean(
            [{"is_draw":int(r["result"]=="D")} for r in rows],"is_draw")}
def grouped(rows,fn):
    b=defaultdict(list)
    for r in rows:b[fn(r)].append(r)
    return {k:metrics(v) for k,v in sorted(b.items())}
def boot(rows,a,b,iterations=1500,seed=263):
    by_date=defaultdict(list)
    for r in rows:by_date[r["date"]].append(r[a]-r[b])
    dates=sorted(by_date)
    if len(dates)<2:return [None,None]
    rng=random.Random(seed)
    output=[]
    for _ in range(iterations):
        total=n=0
        for _ in dates:
            vals=by_date[dates[rng.randrange(len(dates))]]
            total+=sum(vals);n+=len(vals)
        output.append(total/n)
    output.sort()
    return [output[int(.025*(iterations-1))],output[int(.975*(iterations-1))]]
def audit(paths):
    rows=gather(paths)
    by_league=grouped(rows,lambda r:r["league"])
    # Compare within all 20 leagues, not just on aggregated weighted totals.
    xgb_better_by_league=sum(
        1 for x in by_league.values()
        if x["models"]["XGBoost"]["logloss"] < x["models"]["Elo"]["logloss"])
    hybrid_better_by_league=sum(
        1 for x in by_league.values()
        if x["models"]["EqualWeightHybrid"]["logloss"] < x["models"]["XGBoost"]["logloss"])
    loo={}
    for league in sorted(by_league):
        sub=[x for x in rows if x["league"]!=league]
        loo[league]={"n":len(sub),
            "xgb_minus_elo_logloss":mean(sub,"XGBoost_logloss")-mean(sub,"Elo_logloss"),
            "hybrid_minus_xgb_logloss":mean(sub,"EqualWeightHybrid_logloss")-mean(sub,"XGBoost_logloss")}
    quarters=grouped(rows,lambda r:r["date"][:4]+"Q"+str((int(r["date"][5:7])-1)//3+1))
    r={
        "schema":"MC_FROZEN_4MODEL_STRESS_AUDIT_V1",
        "status":"EXPLORATORY_PRIOR_WINDOW_ALREADY_VIEWED",
        "fixture_count":len(rows),
        "overall":metrics(rows),
        "leagues":by_league,
        "quarters":quarters,
        "per_league_checks":{
            "xgb_lower_logloss_than_elo_count":xgb_better_by_league,
            "hybrid_lower_logloss_than_xgb_count":hybrid_better_by_league,
            "league_count":len(by_league)},
        "leave_one_league_out":loo,
        "paired_uncertainty":{
            "xgb_minus_elo_logloss_95pct":boot(rows,"XGBoost_logloss","Elo_logloss"),
            "hybrid_minus_xgb_logloss_95pct":boot(rows,"EqualWeightHybrid_logloss","XGBoost_logloss"),
            "hybrid_minus_elo_logloss_95pct":boot(rows,"EqualWeightHybrid_logloss","Elo_logloss")},
        "cannot_promote_to_263":True,
        "cannot_claim_future_betting_edge":True,
        "notes":["No hyperparameter tuning, no new test period.",
                 "Intervals ignore model-selection multiplicity and may overstate certainty.",
                 "Quarter/league slices are diagnostics, not separate independent blind trials.",
                 "The original frozen 2.6.3 has a distinct cohort and remains unranked."]
    }
    return r

def main():
    p=argparse.ArgumentParser()
    for x in ("elo","poisson","xgb","hybrid","out"):p.add_argument("--"+x,required=True)
    a=p.parse_args()
    result=audit({"Elo":a.elo,"Poisson":a.poisson,"XGBoost":a.xgb,
                  "EqualWeightHybrid":a.hybrid})
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({k:result[k] for k in ("fixture_count","overall",
          "per_league_checks","paired_uncertainty")},indent=2))
if __name__=="__main__":main()
