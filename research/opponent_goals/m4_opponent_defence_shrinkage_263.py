"""Frozen-M4 opponent-defence sharpness experiment, DEV ONLY / READ ONLY.

Hypothesis from prior descriptive residual audit: learned opponent defensive
effect may be over-sharp. Predeclare 2 modest dampings (90%,80%) and two
application scopes (away opponent only, both defences) BEFORE computing scores.
No fitting of these scalars, no betting use, no 2026/27 outcomes, no historical
pilot replay and no changing signed model code/locks/market probabilities.

The 2025/26 windows were used for the original M4 tuning, so this is a
hypothesis/diagnostic, NOT independent validation or automatic promotion.
"""
from __future__ import annotations
import argparse,hashlib,json,math,random,sys
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments/263"))
from exp_263_batch import clean_rows
from full_match_eligibility_263 import full_match_rows
from m4_integrated import fit_m4,predict_m4,score_markets,use_lock

PINS={
    "original":"1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9",
    "scores":"637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89",
    "engine":"eac755e54086738f40d7f30a514b2c9bb789b2c428ffef4ee70bb2fd2b49bc45"
}
FILES={
    "original":ROOT/"data/quad_accepted_263/extended_history.csv",
    "scores":ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv",
    "engine":ROOT/"experiments/263/m4_integrated.py"
}
LOCK=ROOT/"experiments/263/m4_lock.json"
LEAGUES=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
FOLDS=(("2025-11-15","2025-12-06"),("2026-01-15","2026-02-05"),
       ("2026-03-15","2026-04-05"))
# Fixed without inspecting THIS comparison. "away_only" changes home goals
# only; "symmetric" dampens the defence against both scoring teams.
VARIANTS={
    "m4_original":("original",1.00),
    "away_defence_090":("away_only",0.90),
    "away_defence_080":("away_only",0.80),
    "both_defences_090":("symmetric",0.90),
    "both_defences_080":("symmetric",0.80),
}
METRICS=("KG_Brier","Over25_Brier","MS_Brier","KG_logloss",
         "Over25_logloss","MS_logloss")
BUCKETS=("strong_fitted_away_defence","middle_fitted_away_defence",
         "weak_fitted_away_defence")
SCHEMA="263_M4_DEFENCE_DAMPENING_10_LEAGUE_DEV_ONLY_V1"

class AuditError(ValueError):pass
def must(valid,reason):
    if not valid:raise AuditError(reason)
def file_sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def avg(v):return sum(v)/len(v) if v else None

def archive_and_lock():
    for k,p in FILES.items():
        must(p.is_file() and file_sha(p)==PINS[k],"FROZEN_INPUT_SHA_MISMATCH_"+k)
    lock=json.loads(LOCK.read_text(encoding="utf-8"))
    must(lock.get("m4_engine_sha256")==PINS["engine"] and
         lock.get("training_season")=="2025-2026" and
         lock.get("evaluation_season_excluded")=="2026-2027",
         "M4_FROZEN_LOCK_POLICY_MISMATCH")
    settings=use_lock(lock)
    base=clean_rows(FILES["original"])
    allrows=clean_rows(FILES["scores"])
    must(len(base)==4518 and len(allrows)==4617,"ARCHIVE_ROW_COUNTS_CHANGED")
    base_ids={r["fixture_id"]:r for r in base}
    completed_ids={r["fixture_id"]:r for r in allrows}
    must(len(base_ids)==4518 and len(completed_ids)==4617 and
         all(completed_ids.get(k)==r for k,r in base_ids.items()) and
         len(set(completed_ids)-set(base_ids))==99,
         "OLD_4518_OR_EXTRA_99_MATCH_IDENTITY_CHANGED")
    full,excluded,policy_sha=full_match_rows(allrows)
    must(len(full)==4616 and len(excluded)==1,
         "90_MINUTE_MATCH_EXCLUSION_POLICY_CHANGED")
    dev=[r for r in full if r["season"]=="2025-2026" and
         r["match_date"]<"2026-07-01"]
    must(len(dev)>1000 and
         all(r["season"]=="2025-2026" and r["match_date"]<"2026-07-01" for r in dev),
         "DEVELOPMENT_SEASON_LEAKAGE_OR_TOO_FEW")
    return dev,settings,len(full),len(excluded)

def defence_effects(fit,home,away):
    beta,ix,m,n=fit
    must(home in ix and away in ix and home!=away,"UNSEEN_OR_IDENTICAL_TEAM")
    h=ix[home];a=ix[away]
    # Exact two opponent-defence terms used by frozen M4.
    away_against_home=float(beta[2+m+a]+beta[2+5*m+a])
    home_against_away=float(beta[2+m+h]+beta[2+4*m+h])
    return away_against_home,home_against_away

def candidate_lambdas(fit,home,away,scope,weight):
    must((scope,weight) in VARIANTS.values(),"UNPREDECLARED_CHALLENGER")
    baseline=predict_m4(fit,home,away)
    if baseline is None:return None
    # Never silently treat unseen opponent as average in this experiment.
    d_away,d_home=defence_effects(fit,home,away)
    lh,la=baseline
    if scope in ("away_only","symmetric"):
        lh*=math.exp((weight-1)*d_away)
    if scope=="symmetric":
        la*=math.exp((weight-1)*d_home)
    must(math.isfinite(lh) and math.isfinite(la),"NONFINITE_DEFENCE_DAMPING")
    if not (.05<=lh<=5 and .05<=la<=5):return None
    return lh,la

def band(d):
    return (BUCKETS[0] if d<=-0.08 else
            BUCKETS[2] if d>=0.08 else BUCKETS[1])

def losses(markets,home_goals,away_goals):
    yes=int(home_goals>0 and away_goals>0)
    over=int(home_goals+away_goals>=3)
    ms="H" if home_goals>away_goals else (
       "A" if away_goals>home_goals else "D")
    kg=float(markets["BTTS_YES"])
    o=float(markets["OVER_2.5"])
    pm=markets["1X2"]
    must(abs(sum(pm.values())-1)<1e-9 and 0<=kg<=1 and 0<=o<=1,
         "INVALID_MARKET_PROBABILITY")
    return {
      "KG_Brier":(kg-yes)**2,
      "Over25_Brier":(o-over)**2,
      "MS_Brier":sum((pm[k]-int(k==ms))**2 for k in ("H","D","A")),
      "KG_logloss":-math.log(max(1e-12,kg if yes else 1-kg)),
      "Over25_logloss":-math.log(max(1e-12,o if over else 1-o)),
      "MS_logloss":-math.log(max(1e-12,pm[ms]))
    }

def paired_date_ci(records,metric,*,seed=20261111,reps=600):
    # Each element {date, delta}; resample WHOLE dates, not individual games.
    groups=defaultdict(list)
    for r in records:groups[r["date"]].append(r["deltas"][metric])
    if len(groups)<10 or len(records)<120:return None
    dates=sorted(groups)
    rng=random.Random(seed)
    draws=[]
    for _ in range(reps):
        sampled=[v for _ in dates for v in groups[dates[rng.randrange(len(dates))]]]
        draws.append(avg(sampled))
    draws.sort()
    return {"low":draws[int(.025*reps)],
            "high":draws[int(.975*reps)-1],
            "dates":len(dates),"resamples":reps,
            "meaning":"EXPLORATORY_DATE_CLUSTERED_NOT_UNTOUCHED_HOLDOUT"}

def run():
    dev,settings,eligible_n,excluded_n=archive_and_lock()
    complete=[];dropped=Counter();fit_manifest=[]
    for league in LEAGUES:
        for start,end in FOLDS:
            fold=[r for r in dev if r["league"]==league and
                  start<=r["match_date"]<end]
            must(len(fold)>0,"MISSING_ORIGINAL_DEV_FOLD_"+league)
            fit=fit_m4(dev,league,start,settings)
            must(fit is not None,"M4_CANNOT_FIT_"+league+"_"+start)
            train_n=sum(r["league"]==league and r["match_date"]<start for r in dev)
            must(fit[3]==train_n,"M4_TRAINING_DATE_LEAKAGE")
            fit_manifest.append({"league":league,"train_cutoff_exclusive":start,
                                 "evaluation_end_exclusive":end,
                                 "train_n":fit[3],"eval_n":len(fold)})
            for r in fold:
                home,away=r["home_id"],r["away_id"]
                if home not in fit[1] or away not in fit[1]:
                    dropped["TEAM_NOT_SEEN_BEFORE_FOLD"]+=1
                    continue
                pred={}
                for key,(mode,weight) in VARIANTS.items():
                    lam=candidate_lambdas(fit,home,away,mode,weight)
                    if lam is None:break
                    pred[key]={"lambdas":lam,
                               "markets":score_markets(*lam)["markets"]}
                if len(pred)!=len(VARIANTS):
                    dropped["AT_LEAST_ONE_CHALLENGER_OUTSIDE_M4_LAMBDA_RANGE"]+=1
                    continue
                base_lam=predict_m4(fit,home,away)
                must(pred["m4_original"]["lambdas"]==base_lam,
                     "ORIGINAL_M4_LAMBDA_CHANGED")
                d_away,d_home=defence_effects(fit,home,away)
                hg,ag=int(r["home_goals"]),int(r["away_goals"])
                scored={key:losses(v["markets"],hg,ag) for key,v in pred.items()}
                complete.append({
                   "date":r["match_date"],"league":league,
                   "fixture_id":r["fixture_id"],
                   "opponent_defence_bucket":band(d_away),
                   "opponent_away_defence_log":d_away,
                   "original_home_goal_error":hg-base_lam[0],
                   "original_total_goal_error":hg+ag-sum(base_lam),
                   "candidate_home_goal_errors":{
                      key:hg-v["lambdas"][0] for key,v in pred.items()},
                   "losses":scored
                })
    must(len(fit_manifest)==30 and len(complete)>=650,
         "INSUFFICIENT_TEN_LEAGUE_DEVELOPMENT_EXPOSURE")
    must(len({r["fixture_id"] for r in complete})==len(complete),
         "REUSED_HISTORICAL_FIXTURE")
    must(set(r["league"] for r in complete)==set(LEAGUES),
         "SOME_LEAGUES_MISSING")
    must(all(r["date"]<"2026-07-01" for r in complete),
         "2026_27_HOLDOUT_LEAKED_TO_RESEARCH")
    results={}
    for key in VARIANTS:
        averages={m:avg([r["losses"][key][m] for r in complete])
                  for m in METRICS}
        deltas=[{"date":r["date"],
                 "deltas":{m:r["losses"][key][m]-
                               r["losses"]["m4_original"][m]
                           for m in METRICS}} for r in complete]
        strength={}
        for bucket in BUCKETS:
            selected=[r for r in complete if r["opponent_defence_bucket"]==bucket]
            strength[bucket]={
                "n":len(selected),
                "mean_home_goal_error":avg([
                    r["candidate_home_goal_errors"][key] for r in selected]),
                "mean_original_home_goal_error":avg([
                    r["original_home_goal_error"] for r in selected])
            }
        results[key]={
            "scope":VARIANTS[key][0],"defence_weight":VARIANTS[key][1],
            "markets":averages,
            "candidate_minus_original_negative_improves":{
                m:avg([z["deltas"][m] for z in deltas]) for m in METRICS},
            "candidate_minus_original_day_block_95pct":{
                m:paired_date_ci(deltas,m) for m in ("KG_Brier","Over25_Brier","MS_Brier")},
            "home_goal_error_by_opponent_away_defence":strength
        }
        strong=strength[BUCKETS[0]]["mean_home_goal_error"]
        weak=strength[BUCKETS[2]]["mean_home_goal_error"]
        results[key]["strong_minus_weak_goal_bias"]=strong-weak
    consistency={}
    for league in LEAGUES:
        rows=[r for r in complete if r["league"]==league]
        consistency[league]={
            "n":len(rows),
            "opponent_band_counts":dict(Counter(r["opponent_defence_bucket"] for r in rows)),
            "comparison":{k:{
                "delta_KG_Brier":avg([
                    r["losses"][k]["KG_Brier"]-r["losses"]["m4_original"]["KG_Brier"]
                    for r in rows]),
                "delta_Over25_Brier":avg([
                    r["losses"][k]["Over25_Brier"]-r["losses"]["m4_original"]["Over25_Brier"]
                    for r in rows]),
                "delta_MS_Brier":avg([
                    r["losses"][k]["MS_Brier"]-r["losses"]["m4_original"]["MS_Brier"]
                    for r in rows])
            } for k in VARIANTS if k!="m4_original"}
        }
    return {
        "schema":SCHEMA,"status":"DEV_ONLY_EXPLORATORY_NOT_INDEPENDENT_NO_PROMOTION",
        "source_4617_sha256":PINS["scores"],
        "old_4518_sha256":PINS["original"],
        "frozen_m4_engine_sha256":PINS["engine"],
        "rows_90min_eligible_in_archive":eligible_n,
        "excluded_early_finished_result_rows":excluded_n,
        "old_99_result_archive_untouched":True,
        "tested_period":"2025-2026_OLD_PREDECLARED_DEV_FOLDS_ONLY",
        "folds":fit_manifest,
        "same_fixture_comparisons":len(complete),
        "skipped":dict(dropped),
        "variants":results,
        "league_level":consistency,
        "2026_27_match_outcomes_used":0,
        "any_old_sealed_pilot_re_evaluated":False,
        "no_model_fitted_to_current_target_scores":True,
        "production_math_unchanged":True,
        "morning_user_percentages_unchanged":True,
        "automatic_model_promotion":False,
        "limitations":[
          "Defensive weights 0.90/0.80 are separate fixed diagnostic candidates, not selected or optimized from scores.",
          "Both-defence variants dampen against BOTH opponents, while away-only variants change home goals only.",
          "All goal predictions reuse the exact frozen fold fits; 2026/27 outcome data including newly archived 99 are NOT evaluated.",
          "Current comparison uses old M4 development-season folds; any apparent gain is exploratory and needs genuinely untouched future observations.",
          "Changing an already-fitted defence coefficient may alter global goal mean and cannot by itself prove a causal model flaw.",
          "Bootstrap intervals resample match dates but do not correct earlier model or hypothesis selection on similar development games.",
          "Actual new signed prematch SHA forecasts and future match result scoring are separate. No league or bookmaker result is fabricated.",
          "No odds, betting advice, main branch changes, original M4 coefficients, old seals or telephone screen alterations."
        ]
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    report=run()
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,indent=2,allow_nan=False)
        f.write("\n")
    print(json.dumps({
      "status":report["status"],
      "same_match_n":report["same_fixture_comparisons"],
      "league_n":len(report["league_level"]),
      "skipped":report["skipped"],
      "candidate_comparison":{
        k:{"delta_Brier":{m:v for m,v in item["candidate_minus_original_negative_improves"].items()
                         if m in ("KG_Brier","Over25_Brier","MS_Brier")},
           "day_CI":item["candidate_minus_original_day_block_95pct"],
           "strong_weak_goal_bias":item["strong_minus_weak_goal_bias"]}
        for k,item in report["variants"].items()
      },
      "no_promotion":True
    },ensure_ascii=False))
if __name__=="__main__":
    main()
