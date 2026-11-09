"""Pre-registered joint-score calibration experiment on 4518 canonical games.

Baseline: original, unchanged M4 independent-Poisson distribution.
Candidate: (1-w)*M4_joint_score + w*as-of empirical league score matrix.
The empirical reference is a smoothed probability distribution from games
STRICTLY BEFORE each model's week-Monday cutoff. Convex joint blending
ensures BTTS / totals / 1X2 remain mutually mathematically consistent.

DEV window: 2026-08-01 through 2026-09-30, select weight once.
Evaluation: 2026-10-01 through 2026-11-03, no retuning.
The 2026/27 evaluation results were previously inspected; exploratory only.
Never trains on prospective November 6/8 match results.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,sys
from collections import defaultdict,Counter
from datetime import date,timedelta
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments"/"263"))
from m4_integrated import fit_m4,predict_m4,use_lock
from goal_market_distribution_challenge import (
    N,matrix,probs,actual,metrics,diagnostic, BINARY
)

SCHEMA="MC_263_JOINT_SCORE_ASOF_CALIBRATION_V1"
WEIGHTS=(0.,.10,.20,.35,.50)
DEV_END="2026-10-01"
START="2026-08-01"
PRIORS=35.
# Scoreline probability can safely have a residual >10; 40 is the common
# fixed research score grid for both original and alternate models.
def monday(s):
    d=date.fromisoformat(s)
    return (d-timedelta(days=d.weekday())).isoformat()

def asof_empirical(history,league,cutoff):
    """League matrix with hierarchical strictly earlier global prior."""
    cutoff_date=date.fromisoformat(cutoff)
    league_counts=np.zeros((N+1,N+1))
    global_counts=np.zeros((N+1,N+1))
    for r in history:
        if r["date"]>=cutoff:continue
        h,a=int(r["home_goals"]),int(r["away_goals"])
        if max(h,a)>N:raise ValueError("score exceeds pinned grid")
        global_counts[h,a]+=1
        if r["league"]==league:league_counts[h,a]+=1
    if global_counts.sum()<100:
        raise ValueError("too little global asof history")
    # Priors use only scores before the week; no full-hindsight average.
    prior=(global_counts+.01)/(global_counts.sum()+.01*global_counts.size)
    out=(league_counts+PRIORS*prior)/(league_counts.sum()+PRIORS)
    if not np.isfinite(out).all() or abs(out.sum()-1)>1e-9:
        raise ValueError("empirical distribution normalization")
    return out

def sample(rows,settings):
    hist=[{"league":r["league"],"season":r["season"],
       "match_date":r["date"],"fixture_id":"|".join(
           (r["league"],r["date"],r["home"],r["away"])),
       "home_id":r["home"],"away_id":r["away"],
       "home_goals":int(r["home_goals"]),"away_goals":int(r["away_goals"]),
       "result":"H" if int(r["home_goals"])>int(r["away_goals"]) else
           "A" if int(r["home_goals"])<int(r["away_goals"]) else "D"} for r in rows]
    batches=defaultdict(list)
    for r in rows:
        if START<=r["date"]<"2026-11-09":
            batches[r["league"],monday(r["date"])].append(r)
    out=[];failed=[]
    for (league,week),batch in sorted(batches.items()):
        model=fit_m4(hist,league,week,settings)
        reference=asof_empirical(rows,league,week)
        for r in batch:
            lam=predict_m4(model,r["home"],r["away"]) if model else None
            if lam is None:
                failed.append({"league":league,"date":r["date"],"reason":"M4_NO_LAMBDA"})
                continue
            incumbent=matrix(*lam,kind="independent")
            h,a=int(r["home_goals"]),int(r["away_goals"])
            out.append({"league":league,"date":r["date"],"week":week,
                "h":h,"a":a,"lh":float(lam[0]),"la":float(lam[1]),
                "m4":incumbent,"ref":reference})
    return out,failed

def get_predictions(rows,weight):
    return [probs((1-weight)*r["m4"]+weight*r["ref"]) for r in rows]

def score(rows,weight):
    return metrics(get_predictions(rows,weight),
                   [actual(x["h"],x["a"]) for x in rows])

def bs_diff(rows,weight,market):
    if not rows:return None
    m4=get_predictions(rows,0)
    challenger=get_predictions(rows,weight)
    ground=[actual(x["h"],x["a"]) for x in rows]
    return [(q[market]-y[market])**2-(p[market]-y[market])**2
            for p,q,y in zip(m4,challenger,ground)]

def run(archive,lock_path,out_path):
    content=Path(archive).read_bytes()
    rows=list(csv.DictReader(content.decode("utf8").splitlines()))
    if len(rows)!=4518:
        raise ValueError("expected owner accepted 4518 history only")
    if any(r["date"]>="2026-11-09" for r in rows):
        raise ValueError("newer-than-evaluation history")
    if len({(r["league"],r["date"],r["home"],r["away"]) for r in rows})!=len(rows):
        raise ValueError("duplicate fixture")
    lock=json.loads(Path(lock_path).read_text(encoding="utf8"))
    settings=use_lock(lock)
    records,fail=sample(rows,settings)
    dev=[r for r in records if r["date"]<DEV_END]
    test=[r for r in records if r["date"]>=DEV_END]
    if min(len(dev),len(test))<200:
        raise ValueError("insufficient chronological development/evaluation")
    baseline=score(dev,0)
    trials=[]
    for w in WEIGHTS:
        met=score(dev,w)
        # Guardrails: neither requested market may meaningfully deteriorate
        # on the DEV period and MS multiclass Brier must remain stable.
        guard=(met["BTTS_YES"]["brier"]-baseline["BTTS_YES"]["brier"]<=.002
          and met["OVER_2.5"]["brier"]-baseline["OVER_2.5"]["brier"]<=.002
          and met["MS"]["brier"]-baseline["MS"]["brier"]<=.003)
        trials.append({"weight":w,"eligible":bool(guard),
          "dev_mean_brier":met["mean_goal_market_brier"],
          "dev_btts_brier":met["BTTS_YES"]["brier"],
          "dev_over25_brier":met["OVER_2.5"]["brier"],
          "dev_ms_brier":met["MS"]["brier"]})
    good=[r for r in trials if r["eligible"]]
    if not good:raise ValueError("no candidate passed DEV guards, baseline failure")
    picked=min(good,key=lambda r:(r["dev_mean_brier"],r["weight"]))
    chosen=picked["weight"]
    baseline_test=score(test,0)
    candidate_test=score(test,chosen)
    byweek=defaultdict(list)
    for k,r in enumerate(test):byweek[r["week"]].append(k)
    diffs={market:bs_diff(test,chosen,market) for market in BINARY}
    diffs["MS"]=[
        sum((q[m]-y[m])**2-(p[m]-y[m])**2 for m in ("MS_H","MS_D","MS_A"))
        for p,q,y in zip(get_predictions(test,0),get_predictions(test,chosen),
                         [actual(x["h"],x["a"]) for x in test])]
    rng=random.Random(263);weeks=sorted(byweek)
    intervals={}
    for market,per_match in diffs.items():
        observed=float(np.mean(per_match))
        estimates=[]
        for _ in range(1000):
            ix=[index for _ in weeks for index in byweek[weeks[rng.randrange(len(weeks))]]]
            estimates.append(float(np.mean([per_match[k] for k in ix])))
        estimates.sort()
        intervals[market]={"candidate_minus_m4_brier":observed,
           "week_cluster_bootstrap_95pct":[estimates[24],estimates[974]]}
    # All analysis is on one fixed holdout; no new optimization afterward.
    report={"schema":SCHEMA,
       "status":"RETROSPECTIVE_EXPLORATORY_PREVIOUSLY_VIEWED_2026_27",
       "source_sha256":hashlib.sha256(content).hexdigest(),
       "original_history_owner_accepted_only":True,
       "same_week_scores_excluded_from_every_asof_fit":True,
       "future_2026_11_06_08_scores_used_for_training":False,
       "development_n":len(dev),"evaluation_n":len(test),"unpaired_n":len(fail),
       "failed_reasons":dict(Counter(f["reason"] for f in fail)),
       "week_start_cutoff":"Monday YYYY-MM-DD exclusive",
       "development_weight_grid":list(WEIGHTS),
       "development_trials":trials,
       "selected_dev_weight":chosen,
       "metrics_original_m4":baseline_test,
       "metrics_candidate_joint_calibration":candidate_test,
       "paired_brier_differences":intervals,
       "original_m4_diagnostic":diagnostic([{"lambda_h":x["lh"],
              "lambda_a":x["la"],"h":x["h"],"a":x["a"]} for x in test]),
       "method":"joint convex mixture with league asof empirical scoreline reference",
       "joint_distribution_coherence_guaranteed":True,
       "MS_unchanged_only_if_weight_zero":chosen==0,
       "new100_live_evaluation_is_separate":True,
       "independent_new_match_success_proven":False,
       "promotion_to_263":False,"betting_authorized":False}
    out=Path(out_path);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"dev":len(dev),"eval":len(test),"unpaired":len(fail),
       "weight":chosen,
       "markets":{m:{"original":baseline_test[m]["brier"],
          "candidate":candidate_test[m]["brier"],
          "delta":intervals[m]} for m in (*BINARY,"MS")}},indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for field in ("archive","lock","out"):p.add_argument("--"+field,required=True)
    a=p.parse_args()
    run(a.archive,a.lock,a.out)
