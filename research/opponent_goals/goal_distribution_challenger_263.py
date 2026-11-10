"""2025/26 DEV-ONLY, frozen M4 expected-goals and goal-count distribution check.

Two separate hypotheses, NEVER combined:
  - small multiplicative errors in both estimated goal means (0.95/1.05);
  - overdispersion in independent goal marginals (NB alpha=0.10/0.25).

This is not Dixon-Coles, bivariate goal shock, a fifth model, a new live pilot,
a refit of old sealed predictions, or a claim of newly independent evaluation.
2026/27 matches, including the 99 completed results, may be present in the
source SHA but NEVER enter fitting or evaluation. Changes not deployed.
"""
from __future__ import annotations

import argparse,hashlib,json,math,random,sys
from collections import defaultdict,Counter
from datetime import date
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments/263"))
from exp_263_batch import clean_rows
from m4_integrated import fit_m4,predict_m4,score_markets,use_lock
from full_match_eligibility_263 import full_match_rows

SOURCE=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
OLD=ROOT/"data/quad_accepted_263/extended_history.csv"
M4=ROOT/"experiments/263/m4_integrated.py"
LOCK=ROOT/"experiments/263/m4_lock.json"
SHA_SOURCE="637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89"
SHA_OLD="1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9"
SHA_M4="eac755e54086738f40d7f30a514b2c9bb789b2c428ffef4ee70bb2fd2b49bc45"
LEAGUES=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
FOLDS=(("2025-11-15","2025-12-06"),("2026-01-15","2026-02-05"),("2026-03-15","2026-04-05"))
# Frozen before examining comparison results. Goal-mean shift and dispersion
# are *separate* simple challenges to frozen M4 Poisson.
VARIANTS={
    "m4_original_poisson":("poisson",1.00,0.0),
    "lambda_scale_095":("poisson",0.95,0.0),
    "lambda_scale_105":("poisson",1.05,0.0),
    "independent_nb_alpha_010":("nb",1.00,0.10),
    "independent_nb_alpha_025":("nb",1.00,0.25)
}
METRICS=("KG_Brier","O25_Brier","MS_Brier","KG_logloss","O25_logloss","MS_logloss")
class DiagnosticFailed(ValueError):pass
def require(cond,reason):
    if not cond:raise DiagnosticFailed(reason)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def marginal(mu,kind,alpha):
    """Poisson / negative binomial PMF with SAME mean, alpha=extra variance/mean²."""
    require(math.isfinite(mu) and 0.05<=mu<=5,"INVALID_MARGINAL_MEAN")
    require((kind=="poisson" and alpha==0) or
            (kind=="nb" and alpha>0 and alpha<=0.5),"INVALID_DISTRIBUTION")
    if kind=="poisson":
        p0=math.exp(-mu)
        ratio=lambda k:mu/(k+1)
    else:
        r=1/alpha
        p0=(r/(r+mu))**r
        ratio=lambda k:(k+r)/(k+1)*mu/(r+mu)
    p=[p0]
    while 1-sum(p)>1e-13 and len(p)<150:
        p.append(p[-1]*ratio(len(p)-1))
    missing=1-sum(p)
    require(-1e-10<missing<1e-10,"DISTRIBUTION_MASS_NOT_CONTROLLED")
    return np.asarray(p,dtype=float)

def derived_markets(lh,la,kind="poisson",alpha=0):
    ph=marginal(lh,kind,alpha);pa=marginal(la,kind,alpha)
    mat=np.outer(ph,pa)
    require(abs(float(mat.sum())-1)<2e-10,"UNCONTROLLED_JOINT_TAIL")
    h=np.arange(len(ph))[:,None];a=np.arange(len(pa))[None,:]
    ms={"H":float(mat[h>a].sum()),"D":float(mat[h==a].sum()),
        "A":float(mat[h<a].sum())}
    btts=(1-float(ph[0]))*(1-float(pa[0]))
    o25=1-sum(float(ph[i]*pa[j]) for i in range(3) for j in range(3-i))
    require(abs(sum(ms.values())-1)<2e-10 and
            0<=btts<=1 and 0<=o25<=1,"MARKET_PROBABILITY_NOT_COHERENT")
    return {"1X2":ms,"BTTS_YES":btts,"OVER_2.5":o25}

def values(m,h,a):
    btts=int(h>0 and a>0);o25=int(h+a>=3)
    ms="H" if h>a else "A" if a>h else "D"
    pB=float(m["BTTS_YES"]);pO=float(m["OVER_2.5"])
    pMS=m["1X2"]
    eps=1e-12
    return {
      "KG_Brier":(pB-btts)**2,
      "O25_Brier":(pO-o25)**2,
      "MS_Brier":sum((float(pMS[z])-int(z==ms))**2 for z in ("H","D","A")),
      "KG_logloss":-math.log(max(eps,pB if btts else 1-pB)),
      "O25_logloss":-math.log(max(eps,pO if o25 else 1-pO)),
      "MS_logloss":-math.log(max(eps,float(pMS[ms]))),
    }

def day_block_ci(rows,metric,*,draws=600,seed=20261111):
    """Comparison is paired on match; uncertainty resamples whole match dates."""
    days=defaultdict(list)
    for row in rows:days[row["day"]].append(row["deltas"][metric])
    if len(days)<10 or len(rows)<120:return None
    ordered=sorted(days)
    rnd=random.Random(seed)
    samples=[]
    for _ in range(draws):
        vals=[]
        for __ in ordered:
            vals.extend(days[ordered[rnd.randrange(len(ordered))]])
        samples.append(sum(vals)/len(vals))
    samples.sort()
    return {"lower":samples[int(.025*draws)],
            "upper":samples[int(.975*draws)-1],
            "distinct_dates":len(days),"repetitions":draws,
            "interpretation":"exploratory_blocked_on_date_not_independent_holdout"}

def verify_source():
    require(sha(SOURCE)==SHA_SOURCE and sha(OLD)==SHA_OLD and sha(M4)==SHA_M4,
            "PINNED_ARCHIVE_OR_M4_CHANGED")
    lock=json.loads(LOCK.read_text(encoding="utf-8"))
    settings=use_lock(lock)
    require(lock.get("m4_engine_sha256")==SHA_M4 and
            lock.get("training_season")=="2025-2026" and
            lock.get("evaluation_season_excluded")=="2026-2027",
            "FROZEN_DEVELOPMENT_LOCK_INVALID")
    allrows=clean_rows(SOURCE);old=clean_rows(OLD)
    require(len(allrows)==4617 and len(old)==4518,"INTEGRITY_4617_MISSING")
    oldids={r["fixture_id"]:r for r in old}
    require(all(row in allrows for row in old),"4518_ROWS_CHANGED")
    require(len({r["fixture_id"] for r in allrows}-set(oldids))==99,
            "NEW_99_COUNT_CHANGED")
    eligible,excluded,policy_sha=full_match_rows(allrows)
    require(len(eligible)==4616 and len(excluded)==1,"PARTIAL_MATCH_SAFETY_FAILED")
    # All new 2026/27 score rows remain entirely excluded from dev work.
    dev=[r for r in eligible if r["season"]=="2025-2026" and r["match_date"]<"2026-07-01"]
    require(len(dev)>500,"NO_2025_26_DEVELOPMENT_HISTORY")
    return dev,settings,{"full":len(allrows),"dev":len(dev),
                         "excluded_2026_27":len(eligible)-len(dev),
                         "partial_exception":len(excluded)}

def run():
    dev,settings,stats=verify_source()
    all_obs=[];trained=[];dropped=Counter()
    for league in LEAGUES:
        for start,end in FOLDS:
            fold_rows=[r for r in dev if r["league"]==league and start<=r["match_date"]<end]
            if not fold_rows:continue
            fit=fit_m4(dev,league,start,settings)
            require(fit is not None,"FROZEN_M4_FIT_MISSING_"+league+"_"+start)
            require(all(r["match_date"]<start for r in
                        [r for r in dev if r["league"]==league and r["match_date"]<start]),
                    "CUTOFF_NOT_HONORED")
            trained.append({"league":league,"start":start,"end":end,
                            "training_rows":fit[3],"validation_matches":len(fold_rows)})
            for r in fold_rows:
                lam=predict_m4(fit,r["home_id"],r["away_id"])
                if lam is None:
                    dropped["M4_UNAVAILABLE"]+=1;continue
                lh,la=lam
                # Paired sample: all 5 variants must safely exist and use
                # the SAME fixture, as-of model and only pre-fold input.
                if min(lh,la)*.95<.05 or max(lh,la)*1.05>5:
                    dropped["OUTSIDE_COMMON_SAFE_LAMBDA_RANGE"]+=1;continue
                predicted={}
                for name,(kind,scale,alpha) in VARIANTS.items():
                    candidate=derived_markets(lh*scale,la*scale,kind,alpha)
                    if name=="m4_original_poisson":
                        orig=score_markets(lh,la)["markets"]
                        require(all(abs(candidate["1X2"][z]-orig["1X2"][z])<2e-10
                                    for z in ("H","D","A")) and
                                abs(candidate["BTTS_YES"]-orig["BTTS_YES"])<2e-10 and
                                abs(candidate["OVER_2.5"]-orig["OVER_2.5"])<2e-10,
                                "PAIRED_BASELINE_NOT_EXACT_FROZEN_M4")
                    predicted[name]=values(candidate,int(r["home_goals"]),int(r["away_goals"]))
                original=predicted["m4_original_poisson"]
                all_obs.append({
                  "day":r["match_date"],"league":league,"fixture_id":r["fixture_id"],
                  "goal_residual":int(r["home_goals"])+int(r["away_goals"])-(lh+la),
                  "variance_residual":(int(r["home_goals"])+int(r["away_goals"])-(lh+la))**2-(lh+la),
                  "btts_observed":int(int(r["home_goals"])>0 and int(r["away_goals"])>0),
                  "btts_predicted":derived_markets(lh,la)["BTTS_YES"],
                  "o25_observed":int(int(r["home_goals"])+int(r["away_goals"])>=3),
                  "o25_predicted":derived_markets(lh,la)["OVER_2.5"],
                  "per_variant":predicted
                })
    require(len(all_obs)>=400,"FEWER_THAN_400_HISTORICAL_DEV_OBSERVATIONS")
    require(len({x["fixture_id"] for x in all_obs})==len(all_obs),"DUPLICATE_DEV_FIXTURE")
    require(all("2025-"<=x["day"]<"2026-07-01" for x in all_obs),
            "HOLDOUT_2026_27_LEAKED_INTO_DEVELOPMENT")
    counts=Counter(x["league"] for x in all_obs)
    require(set(counts)==set(LEAGUES),"TEN_LEAGUES_NOT_ALL_EVALUATED")
    averages={}
    for name in VARIANTS:
        av={metric:sum(r["per_variant"][name][metric] for r in all_obs)/len(all_obs)
            for metric in METRICS}
        averages[name]=av
    contrasts={}
    for name in VARIANTS:
        if name=="m4_original_poisson":continue
        rows=[{"day":r["day"],
               "deltas":{metric:r["per_variant"][name][metric]-
                                r["per_variant"]["m4_original_poisson"][metric]
                         for metric in METRICS}} for r in all_obs]
        contrasts[name]={
            "candidate_minus_original_negative_means_better":{
                metric:sum(x["deltas"][metric] for x in rows)/len(rows)
                for metric in METRICS},
            "day_block_95pct_uncertainty":{
                metric:day_block_ci(rows,metric)
                for metric in ("KG_Brier","O25_Brier","MS_Brier")}
        }
    def mean(field):return sum(r[field] for r in all_obs)/len(all_obs)
    return {
       "schema":"263_M4_LAMBDA_VS_NB_GOAL_MARGIN_DEV_SENSITIVITY_V1",
       "status":"2025_26_DEV_ONLY_RESEARCH_NO_NEW_MODEL_PROMOTION",
       "asof_folds":FOLDS,
       "new99_results_loaded_but_never_used_in_model_fitting_or_evaluation":True,
       "rows":stats,
       "eligible_common_paired_dev_matches":len(all_obs),
       "league_counts":dict(sorted(counts.items())),
       "trained_folds":trained,
       "dropped":dict(dropped),
       "baseline_goal_residual_mean":mean("goal_residual"),
       "baseline_goal_variance_residual_mean":mean("variance_residual"),
       "baseline_btts_observed":mean("btts_observed"),
       "baseline_btts_predicted":mean("btts_predicted"),
       "baseline_o25_observed":mean("o25_observed"),
       "baseline_o25_predicted":mean("o25_predicted"),
       "variant_methods":{
           k:{"distribution":v[0],"goal_lambda_scale":v[1],"alpha":v[2]}
           for k,v in VARIANTS.items()},
       "raw_development_metrics":averages,
       "paired_development_contrasts":contrasts,
       "winner_not_promoted":True,"old_seals_unmodified":True,
       "m4_and_lock_unchanged":True,"2026_27_holdout_never_touched":True,
       "source_sha256":SHA_SOURCE,"engine_sha256":SHA_M4,
       "limitations":[
         "Same 2025/26 development folds that helped lock M4: exploratory, NOT independent new validation.",
         "Negative-binomial marginal dispersion is new hypothesis and not a retest of earlier Dixon-Coles/bivariate 984 games.",
         "No candidate is chosen for production from these results regardless of small descriptive differences.",
         "No 2026/27 outcomes (including newly archived 99) enter this dev comparison; they remain prospective/holdout.",
         "No pre-match sealed forecasts, historic result rows, M4 coefficients, market selection, or user interface changed.",
         "Paired common sample excludes cases beyond strict baseline and 0.95/1.05 lambda safety bounds.",
         "Bootstrap CIs group matches by calendar day, but do not remove model-dev tuning selection bias.",
         "Lambda shift and goal distribution dispersion variants tested SEPARATELY, never blended."],
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    opt=parser.parse_args()
    report=run()
    p=Path(opt.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    summary={k:report[k] for k in (
        "status","eligible_common_paired_dev_matches","league_counts",
        "baseline_goal_residual_mean","baseline_goal_variance_residual_mean",
        "baseline_btts_observed","baseline_btts_predicted",
        "baseline_o25_observed","baseline_o25_predicted")}
    summary["paired_development_contrasts"]={
       k:v["candidate_minus_original_negative_means_better"]
       for k,v in report["paired_development_contrasts"].items()}
    print(json.dumps(summary,ensure_ascii=False))
if __name__=="__main__":
    main()
