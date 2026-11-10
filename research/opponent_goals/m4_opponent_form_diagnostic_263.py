"""Read-only M4 opponent-quality × recent-form error diagnostic, 10 leagues.

Frozen M4 parameters + three ORIGINAL 2025/26 development folds. No 2026/27
outcomes are fitted, scored, used as adjustments or used to select candidates.
The last-five match form signal is opponent-adjusted using the same frozen
M4 fold fit's expected-goals for the older matches. Because those previous
matches partly occur inside the FIT sample, the signal is EXPLORATORY and
cannot be considered independent residual evidence.

Two fixed FORM coefficients, 0.10 and 0.20, compared on identical eligible
games to M4 0.00. Never write/seal/promote predictions or alter user markets.
This is NOT the old 984 DC/bivariate experiment or any sealed pilot rerun.
"""
from __future__ import annotations
import argparse, hashlib, json, math, random, sys
from collections import defaultdict, Counter
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments/263"))
from exp_263_batch import clean_rows
from full_match_eligibility_263 import full_match_rows
from m4_integrated import fit_m4,predict_m4,score_markets,use_lock

SOURCE=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
BASE=ROOT/"data/quad_accepted_263/extended_history.csv"
ENGINE=ROOT/"experiments/263/m4_integrated.py"
LOCK=ROOT/"experiments/263/m4_lock.json"
PIN={
    "source":"637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89",
    "base":"1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9",
    "engine":"eac755e54086738f40d7f30a514b2c9bb789b2c428ffef4ee70bb2fd2b49bc45"}
LEAGUES=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
FOLDS=(("2025-11-15","2025-12-06"),("2026-01-15","2026-02-05"),("2026-03-15","2026-04-05"))
FORM_LENGTH=5
FORM_STALE_MAX_DAYS=90
FORM_COEFFICIENTS=(0.0,0.10,0.20)
FORM_CLIP=1.0
STRONG_DEFENSE_LOG_THRESHOLD=-0.08
WEAK_DEFENSE_LOG_THRESHOLD=0.08
FORM_THRESHOLD=0.25
MEASURES=("KG_Brier","Over25_Brier","MS_Brier","KG_logloss","Over25_logloss","MS_logloss")
SCHEMA="263_M4_OPPONENT_RECENT5_FORM_RESIDUAL_DEV_ONLY_V1"

class Reject(ValueError):pass
def require(x,reason):
    if not x:raise Reject(reason)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def mean(vals):return sum(vals)/len(vals) if vals else None

def load():
    require(sha(SOURCE)==PIN["source"] and sha(BASE)==PIN["base"] and
            sha(ENGINE)==PIN["engine"],"IMMUTABLE_SOURCE_OR_M4_ENGINE_CHANGED")
    lock=json.loads(LOCK.read_text(encoding="utf-8"))
    require(lock.get("m4_engine_sha256")==PIN["engine"] and
            lock.get("evaluation_season_excluded")=="2026-2027",
            "DEVELOPMENT_LOCK_OR_HOLDOUT_VIOLATED")
    settings=use_lock(lock)
    allrows=clean_rows(SOURCE);old=clean_rows(BASE)
    require(len(allrows)==4617 and len(old)==4518,"RESULT_ARCHIVE_COUNT_CHANGED")
    oldmap={r["fixture_id"]:r for r in old}
    allmap={r["fixture_id"]:r for r in allrows}
    require(all(allmap.get(i)==r for i,r in oldmap.items()) and
            len(set(allmap)-set(oldmap))==99,"ORIGINAL_4518_OR_NEW_99_CHANGED")
    eligible,excluded,_=full_match_rows(allrows)
    require(len(eligible)==4616 and len(excluded)==1,"INCOMPLETE_RESULT_POLICY_CHANGED")
    dev=[r for r in eligible if r["season"]=="2025-2026" and
         r["match_date"]<"2026-07-01"]
    require(len(dev)>1000 and all(r["match_date"]<"2026-07-01" for r in dev),
            "NO_SAFE_DEVELOPMENT_HISTORY")
    return dev,settings

def prior_five(team,history,asof):
    """Order strictly by date, not row after same-day result."""
    require(date.fromisoformat(asof).year in (2025,2026),"DATE_RANGE_INVALID")
    eligible=[r for r in history if (r["home_id"]==team or r["away_id"]==team)
              and r["match_date"]<asof and
              0<(date.fromisoformat(asof)-date.fromisoformat(r["match_date"])).days<=FORM_STALE_MAX_DAYS]
    eligible.sort(key=lambda r:(r["match_date"],r["fixture_id"]))
    return eligible[-FORM_LENGTH:]

def m4_quality(fit,team,position):
    """ONLY pre-fold-fitted coefficients, no league table / postmatch rank."""
    beta,ix,m,n=fit
    require(team in ix,"TEAM_NOT_IN_PAST_FIT")
    j=ix[team]
    if position=="away_defense":
        return float(beta[2+m+j]+beta[2+5*m+j])
    if position=="away_attack":
        return float(beta[2+j]+beta[2+3*m+j])
    raise Reject("UNKNOWN_OPPONENT_QUALITY_ROLE")

def form_record(team,history,asof,fit):
    prior=prior_five(team,history,asof)
    if len(prior)<FORM_LENGTH:return None
    require(all(r["match_date"]<asof for r in prior),"PREVIOUS_FORM_LOOKAHEAD")
    attack=[];conceded=[]
    for r in prior:
        # Never fill missing unseen team predictions with a fabricated zero:
        beta,ix,m,n=fit
        if r["home_id"] not in ix or r["away_id"] not in ix:
            return None
        lam=predict_m4(fit,r["home_id"],r["away_id"])
        if lam is None:return None
        lh,la=lam
        if r["home_id"]==team:
            attack.append(int(r["home_goals"])-lh)
            conceded.append(int(r["away_goals"])-la)
        else:
            attack.append(int(r["away_goals"])-la)
            conceded.append(int(r["home_goals"])-lh)
    return {"n":FORM_LENGTH,
            "most_recent_date":prior[-1]["match_date"],
            "most_recent_fixture_ids":[r["fixture_id"] for r in prior],
            "goal_attack_surprise":mean(attack),
            "goal_concede_surprise":mean(conceded),
            "source_all_pre_target":True,
            "source_at_most_90_days_old":True}

def signal(home_form,away_form):
    """Positive home adjustment from recent home attack and away defence leaks.

    Opponent strength enters via past-game M4 expectation (pre-fold fit),
    NOT extra opponent-factor multiplication. Signals are independently clipped.
    """
    require(home_form is not None and away_form is not None,"FORM_MISSING_NO_IMPUTATION")
    h=(home_form["goal_attack_surprise"]+away_form["goal_concede_surprise"])/2
    a=(away_form["goal_attack_surprise"]+home_form["goal_concede_surprise"])/2
    return max(-FORM_CLIP,min(FORM_CLIP,h)),max(-FORM_CLIP,min(FORM_CLIP,a))

def candidate_lambda(lh,la,s_home,s_away,coefficient):
    require(coefficient in FORM_COEFFICIENTS,"UNPREDECLARED_FORM_COEFFICIENT")
    require(all(isinstance(x,(int,float)) and math.isfinite(x) and .05<=x<=5
                for x in (lh,la)),"BASELINE_LAMBDA_INVALID")
    require(all(-FORM_CLIP<=s<=FORM_CLIP and math.isfinite(s)
                for s in (s_home,s_away)),"FORM_SIGNAL_UNSAFE")
    lhome=lh*math.exp(coefficient*s_home)
    laway=la*math.exp(coefficient*s_away)
    return (lhome,laway) if .05<=lhome<=5 and .05<=laway<=5 else None

def scores(markets,h,a):
    ykg=int(h>0 and a>0);yo=int(h+a>=3)
    ym="H" if h>a else "A" if a>h else "D"
    btts=float(markets["BTTS_YES"]);o=float(markets["OVER_2.5"])
    ms=markets["1X2"]
    require(abs(sum(ms.values())-1)<1e-10 and 0<=btts<=1 and 0<=o<=1,
            "MARKETS_NOT_COHERENT")
    return {
       "KG_Brier":(btts-ykg)**2,
       "Over25_Brier":(o-yo)**2,
       "MS_Brier":sum((ms[k]-int(k==ym))**2 for k in ("H","D","A")),
       "KG_logloss":-math.log(max(1e-12,btts if ykg else 1-btts)),
       "Over25_logloss":-math.log(max(1e-12,o if yo else 1-o)),
       "MS_logloss":-math.log(max(1e-12,ms[ym]))}

def defense_band(x):
    return ("strong_relative_fitted_away_defence" if x<=STRONG_DEFENSE_LOG_THRESHOLD
            else "weak_relative_fitted_away_defence" if x>=WEAK_DEFENSE_LOG_THRESHOLD
            else "central_fitted_away_defence")

def form_band(x):
    return "positive_residual_form" if x>=FORM_THRESHOLD else (
           "negative_residual_form" if x<=-FORM_THRESHOLD else "neutral_residual_form")

def date_bootstrap(values,*,seed=20261111,reps=600):
    """By-date paired mean interval. Exploratory NOT independent model acceptance."""
    groups=defaultdict(list)
    for v in values:
        groups[v["date"]].append(v["value"])
    if len(values)<80 or len(groups)<10:return None
    ordered=sorted(groups)
    rng=random.Random(seed)
    draws=[]
    for _ in range(reps):
        x=[]
        for i in ordered:x.extend(groups[ordered[rng.randrange(len(ordered))]])
        draws.append(mean(x))
    draws.sort()
    return {"low":draws[int(.025*reps)],"high":draws[int(.975*reps)-1],
            "distinct_days":len(groups),"method":"calendar_day_block_bootstrap_EXPLORATORY"}

def run():
    dev,settings=load()
    evaluated=[]; paired=[];folds=[];skips=Counter()
    for league in LEAGUES:
        league_history=sorted((r for r in dev if r["league"]==league),
                              key=lambda r:(r["match_date"],r["fixture_id"]))
        for start,end in FOLDS:
            future=[r for r in league_history if start<=r["match_date"]<end]
            require(future,"MISSING_PREDECLARED_DEV_FOLD_"+league)
            fit=fit_m4(dev,league,start,settings)
            require(fit is not None,"FROZEN_M4_FIT_FAILED_"+league)
            # Same fixed fit for all matches in fold; forms from prior results
            # (including preceding dates in fold), never the current/future date.
            folds.append({"league":league,"start":start,"end":end,
                          "train_rows":fit[3],"candidate_games":len(future)})
            for r in future:
                lam=predict_m4(fit,r["home_id"],r["away_id"])
                if lam is None:
                    skips["NO_BASELINE_M4_LAMBDA"]+=1;continue
                h,a=int(r["home_goals"]),int(r["away_goals"])
                lh,la=lam
                beta,ix,m,n=fit
                if r["away_id"] not in ix:
                    skips["OPPONENT_UNSEEN_IN_FIXED_FIT"]+=1;continue
                opponent_def=m4_quality(fit,r["away_id"],"away_defense")
                baseline=score_markets(lh,la)["markets"]
                f_h=form_record(r["home_id"],league_history,r["match_date"],fit)
                f_a=form_record(r["away_id"],league_history,r["match_date"],fit)
                base_entry={"league":league,"fixture_id":r["fixture_id"],
                            "date":r["match_date"],"goal_home_error":h-lh,
                            "goal_away_error":a-la,"goal_total_error":h+a-lh-la,
                            "opponent_away_defense_log":opponent_def,
                            "opponent_defense_band":defense_band(opponent_def),
                            "base_kg_probability":baseline["BTTS_YES"],
                            "base_o25_probability":baseline["OVER_2.5"],
                            "actual_kg":int(h>0 and a>0),"actual_o25":int(h+a>=3),
                            "score":(h,a),
                            "form_available":f_h is not None and f_a is not None}
                evaluated.append(base_entry)
                if f_h is None or f_a is None:
                    skips["FORM5_NOT_AVAILABLE_ASOF"]+=1;continue
                sh,sa=signal(f_h,f_a)
                signals={}
                for c in FORM_COEFFICIENTS:
                    alt=candidate_lambda(lh,la,sh,sa,c)
                    if alt is None:break
                    signals[str(c)]=scores(score_markets(*alt)["markets"],h,a)
                if len(signals)!=len(FORM_COEFFICIENTS):
                    skips["FORM_CANDIDATE_LAMBDA_UNSAFE"]+=1;continue
                require(signals["0.0"]==scores(baseline,h,a),
                        "ORIGINAL_M4_BASELINE_NOT_REPRODUCED")
                paired.append({
                   **base_entry,"home_form_attack_residual":f_h["goal_attack_surprise"],
                   "home_form_defense_residual":f_h["goal_concede_surprise"],
                   "away_form_attack_residual":f_a["goal_attack_surprise"],
                   "away_form_defense_residual":f_a["goal_concede_surprise"],
                   "home_signal":sh,"away_signal":sa,
                   "joint_form_band":form_band((sh+sa)/2),
                   "last_home_form_date":f_h["most_recent_date"],
                   "last_away_form_date":f_a["most_recent_date"],
                   "last_home_form_fixture_ids":f_h["most_recent_fixture_ids"],
                   "last_away_form_fixture_ids":f_a["most_recent_fixture_ids"],
                   "candidate_scores":signals
                })
    require(len(folds)==len(LEAGUES)*len(FOLDS),"WRONG_NUMBER_OF_ORIGINAL_DEV_FOLDS")
    require(len(evaluated)>=650 and len(paired)>=450,
            "TOO_FEW_COMPLETE_MATCHES_FOR_OPPONENT_FORM_ANALYSIS")
    require(len(set(x["fixture_id"] for x in evaluated))==len(evaluated),
            "DUPLICATE_MATCH_IN_EVAL_FOLDS")
    require(all(x["date"]<"2026-07-01" for x in evaluated),
            "2026_27_RESULTS_LEAKED_TO_TEST")
    require(all(x["last_home_form_date"]<x["date"] and
                x["last_away_form_date"]<x["date"] for x in paired),
            "PREMATCH_FORM_CONTAINS_SAME_DAY_OR_LATER")
    groups={}
    for grouper,identities in [
        ("opponent_strength",["strong_relative_fitted_away_defence",
                              "central_fitted_away_defence",
                              "weak_relative_fitted_away_defence"]),
        ("opponent_adjusted_form",["negative_residual_form",
                                  "neutral_residual_form","positive_residual_form"])]:
        source=evaluated if grouper=="opponent_strength" else paired
        key="opponent_defense_band" if grouper=="opponent_strength" else "joint_form_band"
        breakdown={}
        for group in identities:
            arr=[x for x in source if x[key]==group]
            breakdown[group]={
                "n":len(arr),"distinct_days":len({x["date"] for x in arr}),
                "mean_home_goal_error":mean([x["goal_home_error"] for x in arr]),
                "mean_away_goal_error":mean([x["goal_away_error"] for x in arr]),
                "mean_total_goal_error":mean([x["goal_total_error"] for x in arr]),
                "mean_kg_observed_minus_expected":mean([
                    x["actual_kg"]-x["base_kg_probability"] for x in arr]),
                "mean_o25_observed_minus_expected":mean([
                    x["actual_o25"]-x["base_o25_probability"] for x in arr]),
                "mean_goal_error_dayblock_exploratory_ci":date_bootstrap([
                     {"date":x["date"],"value":x["goal_total_error"]} for x in arr])
            }
        groups[grouper]=breakdown
    contrasts={}
    for coeff in FORM_COEFFICIENTS[1:]:
        k=str(coeff);v=[]
        for x in paired:
            changes={m:x["candidate_scores"][k][m]-x["candidate_scores"]["0.0"][m]
                     for m in MEASURES}
            v.append({"date":x["date"],"changes":changes})
        contrasts[k]={
            "alpha":coeff,"n_paired":len(v),
            "candidate_minus_frozen_m4_negative_improves":{
               m:mean([x["changes"][m] for x in v]) for m in MEASURES},
            "calendar_day_block_exploratory_ci":{
               m:date_bootstrap([{"date":x["date"],"value":x["changes"][m]}
                                for x in v])
               for m in ("KG_Brier","Over25_Brier","MS_Brier")
            }
        }
    score_corr={}
    for name in LEAGUES:
        subset=[x for x in paired if x["league"]==name]
        score_corr[name]={
           "paired":len(subset),
           "avg_total_goal_error":mean([x["goal_total_error"] for x in subset]),
           "avg_joint_recent5_signal":mean([(x["home_signal"]+x["away_signal"])/2 for x in subset]),
           "alpha_010_KG_Brier_delta":mean([
               x["candidate_scores"]["0.1"]["KG_Brier"]-x["candidate_scores"]["0.0"]["KG_Brier"]
               for x in subset]),
           "alpha_010_O25_Brier_delta":mean([
               x["candidate_scores"]["0.1"]["Over25_Brier"]-x["candidate_scores"]["0.0"]["Over25_Brier"]
               for x in subset]),
        }
    return {
       "schema":SCHEMA,"status":"RESEARCH_ONLY_NO_MODEL_OR_FORECAST_MODIFICATION",
       "source_4617_sha256":PIN["source"],
       "source_4518_unchanged_sha256":PIN["base"],
       "frozen_m4_engine_sha256":PIN["engine"],
       "2026_27_outcome_rows_used":0,
       "2026_27_holdout_excluded":True,
       "original_984_match_experiment_rerun":False,
       "historical_sealed_forecasts_scored":0,
       "real_upcoming_fixtures_predicted":0,
       "num_original_ten_league_development_folds":len(folds),
       "all_valid_baseline_matches":len(evaluated),
       "paired_five_match_asof_form_matches":len(paired),
       "sample_exclusions":dict(skips),
       "fixed_model_fit_folds":folds,
       "fixed_features":{
           "recent_game_count":FORM_LENGTH,"recent_max_age_days":FORM_STALE_MAX_DAYS,
           "home_signal":"mean(home_prior_attack_goal_surprise,away_prior_concede_goal_surprise)",
           "away_signal":"mean(away_prior_attack_goal_surprise,home_prior_concede_goal_surprise)",
           "recent_surprise_reference":"original_M4_fold_fit_pre_kickoff_only_but_in_sample_prior_results",
           "form_signal_clamp":FORM_CLIP,
           "opponent_defense_band_log_thresholds":[STRONG_DEFENSE_LOG_THRESHOLD,
                                                    WEAK_DEFENSE_LOG_THRESHOLD],
           "joint_form_band_abs_threshold":FORM_THRESHOLD,
           "challenger_form_coefficients":FORM_COEFFICIENTS,
       },
       "baseline_error_by_opponent_and_form":groups,
       "paired_form_challenger_scores":contrasts,
       "league_level_descriptives":score_corr,
       "automatic_model_promotion":False,"original_m4_settings_changed":False,
       "morning_or_mobile_percentages_changed":False,
       "betting_authorized":False,
       "limitations":[
         "Same M4-selected 2025/26 development folds reused for a NEW residual question: diagnostic, not independent validation.",
         "Prior form outcome residuals are compared with the fixed pre-fold M4 which was trained on many of those historical games; NOT out-of-sample goal residuals for form.",
         "Form for earlier match dates can include results of prior dates of the same evaluation fold, never same-day or future.",
         "Form's opponent quality is already controlled by M4; the opponent strength bucket is relative fitted away-defence coefficient, not external Elo or league-table rank.",
         "Two fixed form candidate scalars were chosen as sensitivity probes; any apparent improvement needs independent future locked SHA matches before use.",
         "All candidate forecasts computed in detached research script and never written to any forward forecast, markets, mobile output or model setting.",
         "Day-block bootstrap uncertainty does not remove old dev hyperparameter-selection bias.",
         "No new purchase, paid data feed, updated lineups or source fiction. No gambling performance guarantee."]
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    opts=parser.parse_args()
    report=run()
    out=Path(opts.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
       "schema":report["schema"],
       "league_folds":report["num_original_ten_league_development_folds"],
       "baseline_n":report["all_valid_baseline_matches"],
       "form_n":report["paired_five_match_asof_form_matches"],
       "skips":report["sample_exclusions"],
       "strength":report["baseline_error_by_opponent_and_form"]["opponent_strength"],
       "form":report["baseline_error_by_opponent_and_form"]["opponent_adjusted_form"],
       "paired_brier":{k:{m:v for m,v in x["candidate_minus_frozen_m4_negative_improves"].items()
                           if m in ("KG_Brier","Over25_Brier","MS_Brier")}
                       for k,x in report["paired_form_challenger_scores"].items()},
       "no_deployment":True},ensure_ascii=False))
if __name__=="__main__":
    main()
