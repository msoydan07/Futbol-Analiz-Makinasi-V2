"""Frozen M4 rival-away-defence coefficient shrink: later TIME-BLOCK check.

Question fixed by the preceding 702-development-match investigation:
Does softening the effect of the OPPONENT'S AWAY DEFENCE on HOME xG make
proper-probability KG Var / 2.5 Over / MS Brier better on a chronologically
later nonoverlapping block?

- Train ONE fixed M4 per league on 2025-26 results strictly before 2026-04-06.
- Evaluate 2026-04-06..2026-05-31 (not the previous Nov/Jan/Mar folds).
- Two PREDECLARED factors 0.75 and 0.50 vs locked 1.0.
- Center defender effect at the training-set mean; avoid spurious global
  lambda shifts masquerading as opponent calibration improvement.
- No 2026-27 outcomes, no new pilots or existing SHA-sealed forecasts.
- Not a guarantee of out-of-sample generalization; the hypothesis itself
  originated from exploring prior development results.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
import math
from pathlib import Path
from random import Random
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments/263"))
from exp_263_batch import clean_rows
from full_match_eligibility_263 import full_match_rows
from m4_integrated import fit_m4,predict_m4,score_markets,use_lock

HISTORY=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
OLD=ROOT/"data/quad_accepted_263/extended_history.csv"
M4=ROOT/"experiments/263/m4_integrated.py"
LOCK=ROOT/"experiments/263/m4_lock.json"
EXPECTED_HASHES={
 "history":"637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89",
 "original":"1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9",
 "engine":"eac755e54086738f40d7f30a514b2c9bb789b2c428ffef4ee70bb2fd2b49bc45"}
TRAIN_CUTOFF="2026-04-06"
EVAL_END="2026-06-01"
OLD_DEV_END="2026-04-05"
LEAGUES=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
FACTORS=(1.0,0.75,0.50)
METRICS=("KG_Brier","OVER25_Brier","MS_Brier",
         "KG_logloss","OVER25_logloss","MS_logloss",
         "home_goal_absolute_error","home_goal_squared_error")
SCHEMA="263_AWAY_DEFENSE_SHRINK_LATER_DATE_2025_26_FIXED_M4_V1"
class Rejected(ValueError):pass
def require(ok,msg):
    if not ok:raise Rejected(msg)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def avg(a):return sum(a)/len(a) if a else None

def ensure_sources():
    require(sha(HISTORY)==EXPECTED_HASHES["history"] and
            sha(OLD)==EXPECTED_HASHES["original"] and
            sha(M4)==EXPECTED_HASHES["engine"],"HISTORICAL_INPUT_OR_M4_SHA_CHANGED")
    lock=json.loads(LOCK.read_text(encoding="utf-8"))
    require(lock["m4_engine_sha256"]==EXPECTED_HASHES["engine"] and
            lock["evaluation_season_excluded"]=="2026-2027" and
            lock["training_season"]=="2025-2026","LOCK_NOT_FROZEN_OR_UNEXPECTED")
    settings=use_lock(lock)
    rows=clean_rows(HISTORY)
    old=clean_rows(OLD)
    require(len(rows)==4617 and len(old)==4518,"SOURCE_COUNTS_TAMPERED")
    index={r["fixture_id"]:r for r in rows}
    require(len(index)==4617 and all(index.get(r["fixture_id"])==r for r in old),
            "ORIGINAL_4518_NOT_PRESERVED")
    require(len({r["fixture_id"] for r in rows}-{r["fixture_id"] for r in old})==99,
            "RESULTS_ONLY_ADDITIONAL_99_MISSING")
    eligible,excluded,_=full_match_rows(rows)
    require(len(eligible)==4616 and len(excluded)==1,
            "PARTIAL_ABANDONED_EXCLUSION_CHANGED")
    dev=[r for r in eligible if r["season"]=="2025-2026" and
         r["match_date"]<"2026-07-01"]
    require(len(dev)>1000 and not any(r["season"]=="2026-2027" for r in dev),
            "HOLDOUT_2026_27_LEAKED")
    require(TRAIN_CUTOFF>OLD_DEV_END and EVAL_END<"2026-07-01",
            "TIME_SPLIT_OVERLAPS_PREVIOUS_DEVELOPMENT")
    return dev,settings

def defense_contribution(fit,away):
    beta,ix,m,n=fit
    require(away in ix,"AWAY_TEAM_NOT_IN_PRE_DATE_FIT")
    j=ix[away]
    return float(beta[2+m+j]+beta[2+5*m+j])

def center_defense(fit):
    beta,ix,m,n=fit
    require(len(ix)==m and m>=2,"BAD_FIT_INDEX")
    # Center across unique *training* teams only (zero-sum in mean).
    return sum(defense_contribution(fit,t) for t in ix)/m

def candidate_goals(fit,home,away,factor):
    require(factor in FACTORS,"NOT_PREDECLARED_DEFENSE_FACTOR")
    baseline=predict_m4(fit,home,away)
    if baseline is None:return None
    beta,ix,m,n=fit
    require(home in ix and away in ix and home!=away,
            "NO_UNSEEN_TEAM_FALLBACK_IN_COMPARISON")
    home_lambda,away_lambda=baseline
    centered=defense_contribution(fit,away)-center_defense(fit)
    candidate_home=home_lambda*math.exp((factor-1.0)*centered)
    if not (math.isfinite(candidate_home) and .05<=candidate_home<=5):
        return None
    # Opponent defense affects ONLY home goal rate; away xG is untouched.
    require(abs(away_lambda-baseline[1])<1e-12,
            "CHALLENGER_IMPROPER_AWAY_GOAL_EDIT")
    return candidate_home,away_lambda

def brier_loss(goals,h,a):
    lam_h,lam_a=goals
    market=score_markets(lam_h,lam_a)["markets"]
    kg=int(h>0 and a>0)
    over=int(h+a>=3)
    win="H" if h>a else "A" if a>h else "D"
    pkg=market["BTTS_YES"];po=market["OVER_2.5"];pw=market["1X2"]
    require(all(0<=p<=1 for p in (pkg,po,*pw.values())) and
            abs(sum(pw.values())-1)<1e-10,"MARKET_PROBABILITY_NOT_NORMALIZED")
    return {
      "KG_Brier":(pkg-kg)**2,
      "OVER25_Brier":(po-over)**2,
      "MS_Brier":sum((pw[k]-int(k==win))**2 for k in ("H","D","A")),
      "KG_logloss":-math.log(max(1e-12,pkg if kg else 1-pkg)),
      "OVER25_logloss":-math.log(max(1e-12,po if over else 1-po)),
      "MS_logloss":-math.log(max(1e-12,pw[win])),
      "home_goal_absolute_error":abs(h-lam_h),
      "home_goal_squared_error":(h-lam_h)**2
    }

def date_block_ci(rows,key,*,reps=900,seed=20261111):
    blocks=defaultdict(list)
    for r in rows:
        blocks[r["date"]].append(r["deltas"][key])
    if len(rows)<80 or len(blocks)<10:return None
    dates=sorted(blocks)
    rng=Random(seed)
    sample=[]
    for _ in range(reps):
        v=[]
        for __ in dates:v.extend(blocks[dates[rng.randrange(len(dates))]])
        sample.append(avg(v))
    sample.sort()
    return {"low":sample[int(.025*reps)],
            "high":sample[int(.975*reps)-1],
            "distinct_match_dates":len(dates),
            "method":"entire_calendar_date_cluster_bootstrap_exploratory"}

def run():
    dev,settings=ensure_sources()
    evaluated=[];excluded=Counter();fits=[]
    for league in LEAGUES:
        league_rows=[r for r in dev if r["league"]==league]
        training=[r for r in league_rows if r["match_date"]<TRAIN_CUTOFF]
        evaluation=[r for r in league_rows
                    if TRAIN_CUTOFF<=r["match_date"]<EVAL_END]
        require(len(training)>=60,"NOT_ENOUGH_PRE_SPLIT_MATCHES_"+league)
        require(len(evaluation)>=10,"NOT_ENOUGH_POST_SPLIT_MATCHES_"+league)
        fit=fit_m4(dev,league,TRAIN_CUTOFF,settings)
        require(fit is not None and fit[3]==len(training),"FIT_NOT_STRICTLY_PRE_SPLIT_"+league)
        center=center_defense(fit)
        fits.append({"league":league,"fit_asof_exclusive":TRAIN_CUTOFF,
                     "training_results":len(training),
                     "evaluation_results":len(evaluation),
                     "away_defense_mean_center":center})
        for r in evaluation:
            # Score outcomes are used here only *after* predictions from an
            # immutable pre-block fit, never during fit or tuning.
            home=r["home_id"];away=r["away_id"]
            if home not in fit[1] or away not in fit[1]:
                excluded["UNSEEN_IN_FIT"]+=1;continue
            predictions={str(f):candidate_goals(fit,home,away,f) for f in FACTORS}
            if any(g is None for g in predictions.values()):
                excluded["NOT_COMMON_SAFE_LAMBDA_RANGE"]+=1;continue
            frozen=predict_m4(fit,home,away)
            require(predictions["1.0"]==frozen,"BASELINE_NOT_UNCHANGED_FROZEN_M4")
            h=int(r["home_goals"]);a=int(r["away_goals"])
            raw={key:brier_loss(g,h,a) for key,g in predictions.items()}
            defense=defense_contribution(fit,away)-center
            evaluated.append({
              "fixture_id":r["fixture_id"],"date":r["match_date"],"league":league,
              "away_defense_centered_log":defense,
              "home_scored_minus_frozen_lambda":h-frozen[0],
              "scored":(h,a),"losses":raw
            })
    require(len(evaluated)>=200 and len({r["fixture_id"] for r in evaluated})==len(evaluated),
            "LATER_NONOVERLAP_SAMPLE_TOO_SMALL_OR_DUPLICATED")
    require(len(fits)==10 and all(TRAIN_CUTOFF<=r["date"]<EVAL_END for r in evaluated),
            "DEVELOPMENT_BLOCK_LEAKAGE")
    contrast={}
    for factor in FACTORS:
        key=str(factor)
        absolute={measure:avg([row["losses"][key][measure] for row in evaluated])
                  for measure in METRICS}
        if factor==1.0:
            contrast[key]={"alpha":factor,"absolute_scores":absolute,
                           "candidate_minus_frozen_m4":None}
        else:
            pair=[{"date":r["date"],"league":r["league"],
                   "deltas":{m:r["losses"][key][m]-r["losses"]["1.0"][m]
                             for m in METRICS}} for r in evaluated]
            contrast[key]={
              "alpha":factor,"absolute_scores":absolute,
              "candidate_minus_frozen_m4":{
                m:{"mean":avg([row["deltas"][m] for row in pair]),
                   "date_block_95pct_interval":date_block_ci(pair,m)}
                for m in METRICS}
            }
            league_breakdown={}
            for league in LEAGUES:
                subset=[r for r in pair if r["league"]==league]
                league_breakdown[league]={
                    "n":len(subset),
                    "kg_delta_brier":avg([r["deltas"]["KG_Brier"] for r in subset]),
                    "over25_delta_brier":avg([r["deltas"]["OVER25_Brier"] for r in subset]),
                    "ms_delta_brier":avg([r["deltas"]["MS_Brier"] for r in subset])
                }
            contrast[key]["per_league"]=league_breakdown
    # Independently inspect SAME directional hypothesis from earlier 702
    # on this chronologically later, disjoint period. No band tuning.
    strong=[r for r in evaluated if r["away_defense_centered_log"]<=-0.08]
    weak=[r for r in evaluated if r["away_defense_centered_log"]>=0.08]
    strength={
       "threshold_frozen_before_this_result":0.08,
       "strong_count":len(strong),"weak_count":len(weak),
       "strong_home_goal_residual":avg([r["home_scored_minus_frozen_lambda"] for r in strong]),
       "weak_home_goal_residual":avg([r["home_scored_minus_frozen_lambda"] for r in weak]),
    }
    strength["strong_minus_weak_home_goal_residual"]=(
        strength["strong_home_goal_residual"]-strength["weak_home_goal_residual"]
        if strong and weak else None)
    return {
       "schema":SCHEMA,
       "status":"CHRONOLOGICALLY_LATER_2025_26_RESEARCH_NO_PROMOTION",
       "hypothesis_from_old_702_not_reused":True,
       "train_asof_exclusive":TRAIN_CUTOFF,"last_evaluation_exclusive":EVAL_END,
       "previous_702_evaluation_ends_exclusive":OLD_DEV_END,
       "locked_m4_settings":settings.__dict__,
       "old_4518_hash":EXPECTED_HASHES["original"],
       "new_4617_hash":EXPECTED_HASHES["history"],
       "m4_engine_hash":EXPECTED_HASHES["engine"],
       "new_99_results_used_for_tuning_or_evaluation":False,
       "season_2026_27_included":False,
       "existing_pre_game_96_pilot_reprocessed":False,
       "new_pilot_registered":False,
       "pre_game_probability_changed":False,
       "model_promoted":False,
       "n_accepted":len(evaluated),
       "n_unique_match_days":len({r["date"] for r in evaluated}),
       "n_by_league":dict(Counter(r["league"] for r in evaluated)),
       "excluded":dict(excluded),
       "freeze_fit_by_league":fits,
       "factors":list(FACTORS),
       "baseline_strength_residual_nonoverlap":strength,
       "same_match_matched_loss":contrast,
       "notes":[
         "No result from 2026/27 or the already sealed Nov 6-8 pilot was evaluated.",
         "Opponent's learned away-defense coefficient+venue is softened TOWARD the pre-fit league team mean in log goal space; no extra term or away-goal change.",
         "Loss contrasts are strictly paired on SAME evaluation fixtures, with both models fitted only up to April 6.",
         "The hypothesis was chosen after viewing the prior 702 development games; later-period check is not a prospective sealed match test.",
         "The same 2025/26 season may previously have been consulted in other research. Never claim untouched globally.",
         "Day-block intervals are exploratory and small per-league results must not justify production model promotion.",
         "No M4 coefficients or main/research history source files were rewritten; nothing bet or displayed on mobile."
       ]
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    doc=run()
    p=Path(args.out)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(doc,ensure_ascii=False,indent=2,allow_nan=False)+"\n",
                 encoding="utf-8")
    print(json.dumps({
       "period":[doc["train_asof_exclusive"],doc["last_evaluation_exclusive"]],
       "n":doc["n_accepted"],"n_days":doc["n_unique_match_days"],
       "leagues":doc["n_by_league"],
       "defense_residual":doc["baseline_strength_residual_nonoverlap"],
       "paired":{k:{m:{ "delta":v["mean"],"CI":v["date_block_95pct_interval"]}
                        for m,v in x["candidate_minus_frozen_m4"].items()
                        if m in ("KG_Brier","OVER25_Brier","MS_Brier")}
                 for k,x in doc["same_match_matched_loss"].items()
                 if k!="1.0"},
       "model_changed":False},ensure_ascii=False))
