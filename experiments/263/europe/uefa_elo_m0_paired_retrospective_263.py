"""One preregistered, retrospective-only M0 vs M0+Elo diagnostic on 124 paired UEFA matches.

The source artifacts explicitly remain REVIEW_ONLY / training_permitted=False.
This is a quarantined sensitivity analysis, NOT approved historical training
or proof of live pregame performance. Never write into B/C2/C3/M4/main/pilot.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import random
import statistics
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

OFFICIAL_SHA="6111cb58a7cf25bf81a05dabc73c74f9699fb30aa2fbebb8e1820ce5e9f481ac"
GOALS_SHA="902a56410dc6b6b877ad768e593db87ab1f742f7657dc87aa4e88d5f5739decd"
ELO_SHA="38470d1d17ba4394e85bdf30827ce7fac476dd4f34cdda9c3b198512934adec3"
HIST_LAG_MAX=30
K_SMOOTH=5.0
RIDGE=20.0
CLIP_LO=0.15
CLIP_HI=5.0
BOOTSTRAP=2000
SEED=263
VERSION="263_EUROPE_ELO_M0_PAIRED_RETROSPECTIVE_DISCOVERY_V1"
class AuditError(ValueError):pass

def read_checked(path,sha):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sha:
        raise AuditError("FROZEN_SOURCE_SHA_CHANGED:"+Path(path).name)
    return raw

def clip(x,lo=CLIP_LO,hi=CLIP_HI):
    return min(hi,max(lo,x))

def month_fold(day):
    if "2025-09-01"<=day<"2025-12-01":return "train"
    if "2025-12-01"<=day<"2026-01-01":return "validation"
    if "2026-01-01"<=day<"2026-02-01":return "holdout"
    raise AuditError("UEFA_TARGET_DATE_OUTSIDE_FROZEN_SPLITS")

def load_cohort(official_path,goals_path,elo_path,crosswalk_path):
    official=json.loads(read_checked(official_path,OFFICIAL_SHA))
    goals=json.loads(read_checked(goals_path,GOALS_SHA))
    elo_raw=read_checked(elo_path,ELO_SHA)
    cross_raw=Path(crosswalk_path).read_bytes()
    cross=json.loads(cross_raw)
    if not (official.get("schema")=="263_UEFA_2025_26_CL_EL_132_OFFICIAL_MATCH_ID_SOURCE_REVIEW_V1"
            and official.get("status")=="REVIEW_ONLY_NO_MODEL"
            and official.get("model_training_permitted") is False
            and goals.get("schema")=="263_UEFA_GOL_ONLY_ASOF_FEATURE_READINESS_V1"
            and goals.get("status")=="REVIEW_ONLY_NO_MODEL"
            and goals.get("training_permitted") is False):
        raise AuditError("REVIEW_ONLY_HISTORICAL_SOURCE_CONTRACT_VIOLATED")
    if (cross.get("schema")!="EUROPE_263_167_CLUB_SOURCE_NAME_CROSSWALK_ACCEPTANCE"
            or cross.get("reconciled_name_candidate_count")!=167
            or cross.get("prediction_probs_computed") is not False
            or cross.get("model_weight_approved") is not False):
        raise AuditError("EXPERIMENTAL_ELO_CROSSWALK_INVALID")
    clubs=cross.get("clubs",[])
    byid={row["canonical_id"]:row for row in clubs}
    if len(clubs)!=167 or len(byid)!=167 or len({r["provider_slug"] for r in clubs})!=167:
        raise AuditError("EXPERIMENTAL_IDENTITY_BRIDGE_NOT_UNIQUE")
    # A dated Elo CSV records post-match points; never use target date itself.
    reader=csv.DictReader(io.StringIO(elo_raw.decode("utf-8-sig")))
    if not {"date","club","elo","rd"}.issubset(reader.fieldnames or []):
        raise AuditError("HISTORICAL_ELO_COLUMNS_MISSING")
    histories=defaultdict(list)
    seen={}
    for r in reader:
        slug=(r.get("club") or "").strip();day=(r.get("date") or "").strip()
        if not slug: continue # known nonempty unidentified data: quarantine, never infer ID
        try:
            date.fromisoformat(day)
            elo=float(r["elo"]);rd=float(r["rd"])
        except (ValueError,KeyError,TypeError) as exc:
            raise AuditError("DATED_ELO_ROW_INVALID") from exc
        if not math.isfinite(elo) or not 0<=elo<=4000 or not math.isfinite(rd) or not 0<=rd<=500:
            raise AuditError("ELO_NUMERICAL_RANGE_INVALID")
        key=(slug,day)
        if key in seen:
            if seen[key]!=(elo,rd):raise AuditError("CONFLICTING_SAME_DAY_ELO")
            continue
        seen[key]=(elo,rd)
        histories[slug].append((day,elo,rd))
    for slug in histories:histories[slug].sort()
    matches=official.get("matches",[])
    gs=goals.get("matches",[])
    if len(matches)!=132 or len(gs)!=132:
        raise AuditError("FROZEN_132_MATCH_COUNT_CHANGED")
    target={m["uefa_official_match_id"]:m for m in gs}
    if len(target)!=132:raise AuditError("DUPLICATE_GOAL_PROFILE_ID")
    if len({m["uefa_official_match_id"] for m in matches})!=132:
        raise AuditError("DUPLICATE_UEFA_MATCH_ID")
    examples=[]
    count=Counter();unique_ids=set();missing=[]
    for m in matches:
        match_id=m["uefa_official_match_id"]
        g=target.get(match_id)
        if g is None or m["date"]!=g.get("target_date") or m["competition"]!=g.get("competition"):
            raise AuditError("MATCH_GOAL_SOURCE_NOT_PAIRED")
        if m.get("model_eligible") is not False or g.get("training_or_pilot_allowed") is not False:
            raise AuditError("REVIEW_ONLY_PROVENANCE_PROMOTED")
        eligible=(g["both_4_plus_domestic_results"] is True and
                  g["both_have_2_each_home_away"] is True and
                  g["both_leagues_have_30_plus_past_games"] is True)
        if not eligible:continue
        fold=month_fold(m["date"]);count[fold]+=1
        profiles=g["team_goals_inputs"]
        sides=[]
        for side in ("home","away"):
            team_id=m[side+"_id_candidate"]
            p=profiles[side]
            if team_id!=p["canonical_team_id"]:
                raise AuditError("OFFICIAL_VS_GOAL_CANONICAL_ID_MISMATCH")
            if p["source_data_retrievable_at_original_kickoff_verified"] is not False:
                raise AuditError("UNSUPPORTED_PREMATCH_PUBLICATION_CLAIM")
            if p["past_domestic_home_games"]<2 or p["past_domestic_away_games"]<2:
                raise AuditError("INSUFFICIENT_TEAM_ROLE_GAMES")
            if p["domestic_league_games_before_target"]<30:
                raise AuditError("INSUFFICIENT_LEAGUE_GAMES")
            identity=byid.get(team_id)
            if identity is None:
                missing.append({"id":match_id,"side":side,"reason":"TEAM_NOT_IN_167"})
                continue
            if identity["league"]!=p["domestic_league"]:
                raise AuditError("CURRENT_VS_HISTORICAL_LEAGUE_MISMATCH")
            slug=identity["provider_slug"]
            history=histories.get(slug,[])
            ix=bisect_left([row[0] for row in history],m["date"])-1
            if ix<0:
                missing.append({"id":match_id,"side":side,"slug":slug,"reason":"NO_PRIOR_ELO"})
                continue
            observation=history[ix]
            lag=(date.fromisoformat(m["date"])-date.fromisoformat(observation[0])).days
            if not 1<=lag<=HIST_LAG_MAX:
                missing.append({"id":match_id,"side":side,"slug":slug,
                                "reason":"HISTORICAL_ELO_STALE_OR_FUTURE","lag":lag})
                continue
            sides.append({"id":team_id,"slug":slug,"profile":p,"elo":observation[1],
                          "rd":observation[2],"elo_asof":observation[0],"lag":lag})
            unique_ids.add(team_id)
        if len(sides)!=2:
            missing.append({"id":match_id,"reason":"INCOMPLETE_ELO_PAIR"})
            continue
        if not (type(m.get("home_goals"))==type(m.get("away_goals"))==int
                and 0<=m["home_goals"]<=30 and 0<=m["away_goals"]<=30):
            raise AuditError("UEFA_SCORE_INVALID")
        examples.append({"id":match_id,"date":m["date"],"fold":fold,
                         "competition":m["competition"],"home":sides[0],"away":sides[1],
                         "home_goals":m["home_goals"],"away_goals":m["away_goals"]})
    if count!=Counter({"train":76,"validation":16,"holdout":32}) or missing or len(examples)!=124 or len(unique_ids)!=47:
        raise AuditError("PRE_REGISTERED_PAIRED_COHORT_BLOCKED:"+json.dumps({
            "folds":dict(count),"complete_pairs":len(examples),
            "unique_clubs":len(unique_ids),"issues":missing[:8]},ensure_ascii=False))
    return examples,{"paired_total":124,"unique_clubs":len(unique_ids),
                     "folds":dict(count),
                     "elo_max_lag_days":max(x[side]["lag"] for x in examples for side in ("home","away")),
                     "elo_csv_sha256":ELO_SHA,
                     "crosswalk_sha256":hashlib.sha256(cross_raw).hexdigest(),
                     "history_has_first_seen_publication_proof":False,
                     "uefa_results_independently_fetched_in_original_ci":False}

def relative_rate(goals,n,league_average):
    if not 0<league_average<10 or not isinstance(n,int) or n<0:
        raise AuditError("LEAGUE_RATE_OR_N_INVALID")
    return ((goals+K_SMOOTH*league_average)/(n+K_SMOOTH))/league_average

def base_features(match):
    h=match["home"]["profile"];a=match["away"]["profile"]
    # Domestic home goals are scored by the HOME domestic club,
    # and conceded in the domestic AWAY team's role.
    h_att=relative_rate(h["domestic_home_goals_scored"],
        h["past_domestic_home_games"],h["domestic_league_home_goals_per_game_before_target"])
    a_def=relative_rate(a["domestic_away_goals_conceded"],
        a["past_domestic_away_games"],a["domestic_league_home_goals_per_game_before_target"])
    a_att=relative_rate(a["domestic_away_goals_scored"],
        a["past_domestic_away_games"],a["domestic_league_away_goals_per_game_before_target"])
    h_def=relative_rate(h["domestic_home_goals_conceded"],
        h["past_domestic_home_games"],h["domestic_league_away_goals_per_game_before_target"])
    return h_att*a_def,a_att*h_def

def lambdas(m,train_home_mean,train_away_mean,beta):
    hfactor,afactor=base_features(m)
    d=clip((m["home"]["elo"]-m["away"]["elo"])/400.0,-2.0,2.0)
    base_h=clip(train_home_mean*hfactor);base_a=clip(train_away_mean*afactor)
    lh=clip(base_h*math.exp(beta*d));la=clip(base_a*math.exp(-beta*d))
    return lh,la

def poisson_logpmf(n,mu):
    return n*math.log(mu)-mu-math.lgamma(n+1)

def fit_fixed_beta(train,home_mean,away_mean):
    # This is an exploratory one-coefficient sensitivity fit; NOT approved
    # model fitting from these REVIEW_ONLY sources.
    def objective(beta):
        total=RIDGE*beta*beta/2.0
        for m in train:
            lh,la=lambdas(m,home_mean,away_mean,beta)
            total-=poisson_logpmf(m["home_goals"],lh)+poisson_logpmf(m["away_goals"],la)
        return total
    left,right=-1.0,1.0
    phi=(5**0.5-1)/2
    for _ in range(100):
        c=right-phi*(right-left);d=left+phi*(right-left)
        if objective(c)<objective(d):right=d
        else:left=c
    beta=(left+right)/2
    return beta,objective(beta)

def predict(lh,la):
    ph=[math.exp(poisson_logpmf(k,lh)) for k in range(26)]
    pa=[math.exp(poisson_logpmf(k,la)) for k in range(26)]
    # 0..25 includes effectively all Poisson mass for lambda <=5
    p_h=sum(ph[h]*pa[a] for h in range(26) for a in range(h))
    p_d=sum(ph[k]*pa[k] for k in range(26))
    p_a=sum(pa[a]*ph[h] for a in range(26) for h in range(a))
    total=p_h+p_d+p_a
    probs=[p_h/total,p_d/total,p_a/total]
    mu=lh+la
    p_over=1-math.exp(-mu)*(1+mu+0.5*mu**2)
    p_btts=(1-math.exp(-lh))*(1-math.exp(-la))
    return probs,p_over,p_btts

def score(m,home_mean,away_mean,beta):
    lh,la=lambdas(m,home_mean,away_mean,beta)
    probs,p_over,p_btts=predict(lh,la)
    h,a=m["home_goals"],m["away_goals"]
    true_index=0 if h>a else 1 if h==a else 2
    brier=sum((p-(1 if i==true_index else 0))**2 for i,p in enumerate(probs))
    over=int(h+a>2);btts=int(h>0 and a>0)
    return {"1x2_logloss":-math.log(max(probs[true_index],1e-14)),
            "1x2_brier":brier,"over25_brier":(p_over-over)**2,
            "btts_brier":(p_btts-btts)**2,
            "goal_pair_poisson_logloss":-poisson_logpmf(h,lh)-poisson_logpmf(a,la),
            "prob_home":probs[0],"prob_draw":probs[1],"prob_away":probs[2],
            "prob_over25":p_over,"observed_over25":over}

METRICS=("1x2_logloss","1x2_brier","over25_brier","btts_brier","goal_pair_poisson_logloss")
def avg(rows,key):
    return sum(r[key] for r in rows)/len(rows)

def fold_results(rows):
    a=[x["m0"] for x in rows];b=[x["m0_elo"] for x in rows]
    result={"n":len(rows),"distinct_dates":len({x["date"] for x in rows}),
            "by_competition":dict(Counter(x["cup"] for x in rows)),
            "metrics":{metric:{"M0":avg(a,metric),"M0_plus_Elo":avg(b,metric),
                               "delta_Elo_minus_M0":avg(b,metric)-avg(a,metric)}
                       for metric in METRICS},
            "1x2_mean_probs_M0":{key:avg(a,key) for key in ("prob_home","prob_draw","prob_away")},
            "1x2_mean_probs_Elo":{key:avg(b,key) for key in ("prob_home","prob_draw","prob_away")},
            "observed_1x2_counts":dict(Counter(x["result"] for x in rows))}
    return result

def bootstrap_days(rows):
    buckets=defaultdict(list)
    for x in rows:buckets[x["date"]].append(x)
    days=sorted(buckets)
    rng=random.Random(SEED)
    vals=[]
    for _ in range(BOOTSTRAP):
        sample=[x for day in (rng.choice(days) for _ in days) for x in buckets[day]]
        d=sum(x["m0_elo"]["1x2_logloss"]-x["m0"]["1x2_logloss"] for x in sample)/len(sample)
        vals.append(d)
    vals.sort()
    return {"resamples":BOOTSTRAP,"seed":SEED,"days":len(days),
            "delta_Elo_minus_M0_ci_2p5_97p5":[vals[int(0.025*(BOOTSTRAP-1))],
                                              vals[int(0.975*(BOOTSTRAP-1))]],
            "fraction_improving":sum(v<0 for v in vals)/len(vals),
            "warning":"Few calendar clusters; exploratory interval, not independent season proof"}

def run(official,goals,history,crosswalk,out):
    examples,coverage=load_cohort(official,goals,history,crosswalk)
    train=[x for x in examples if x["fold"]=="train"]
    home_mean=sum(m["home_goals"] for m in train)/len(train)
    away_mean=sum(m["away_goals"] for m in train)/len(train)
    if not (0.1<home_mean<5 and 0.1<away_mean<5):
        raise AuditError("UEFA_TRAIN_GOAL_BASELINE_UNSAFE")
    beta,objective=fit_fixed_beta(train,home_mean,away_mean)
    predictions=[]
    for m in examples:
        s0=score(m,home_mean,away_mean,0.0)
        s1=score(m,home_mean,away_mean,beta)
        predictions.append({"match_id":m["id"],"date":m["date"],"fold":m["fold"],
                            "cup":m["competition"],"result":"H" if m["home_goals"]>m["away_goals"]
                            else "A" if m["home_goals"]<m["away_goals"] else "D",
                            "m0":s0,"m0_elo":s1})
    folds={}
    for f in ("train","validation","holdout"):
        rows=[x for x in predictions if x["fold"]==f]
        folds[f]=fold_results(rows)
        if f!="train":folds[f]["date_block_bootstrap"]=bootstrap_days(rows)
    for cup in ("UEFA_CL","UEFA_EL"):
        selected=[x for x in predictions if x["fold"]=="holdout" and x["cup"]==cup]
        folds["holdout"][cup]=fold_results(selected)
    val_d=folds["validation"]["metrics"]["1x2_logloss"]["delta_Elo_minus_M0"]
    test_d=folds["holdout"]["metrics"]["1x2_logloss"]["delta_Elo_minus_M0"]
    decision=("RETROSPECTIVE_IMPROVEMENT_BOTH_PERIODS_NOT_PRODUCTION_PROOF"
              if val_d<0 and test_d<0 else
              "NO_CONSISTENT_RETROSPECTIVE_ELO_IMPROVEMENT")
    report={"schema":VERSION,"status":"RETROSPEKTIF_KESIF_NO_LIVE_PREGAME_PROOF",
            "decision":decision,
            "source_read_only_training_permitted":False,
            "exploratory_retro_coefficient_only":True,
            "uefa_match_id_review_only":True,
            "historical_rating_first_seen_verified":False,
            "reliable_live_prematch_forecast_claim":False,
            "new_independent_season_holdout":False,
            "stats_based_on_pre_calendar_date_only":True,
            "provider":"beyondELO https://beyondelo.com CC BY 4.0",
            "all_matches_paired":True,"xg_or_h2h_used":False,
            "additional_league_coefficient_used":False,
            "goal_lambda_approved":False,"Elo_weight_approved_for_model":False,
            "main_modified":False,"pilot_recorded":False,
            "original_models_B_C2_C3_M4_untouched":True,
            "source_coverage":coverage,
            "fixed_protocol":{"training_n":76,"validation_n":16,"holdout_n":32,
                              "k_smoothing":K_SMOOTH,"ridge":RIDGE,
                              "goal_lambda_bounds":[CLIP_LO,CLIP_HI],
                              "Elo_normalization":400,
                              "Elo_delta_bounds":[-2,2],
                              "beta_bounds":[-1,1],
                              "UEFA_train_home_goal_mean":home_mean,
                              "UEFA_train_away_goal_mean":away_mean,
                              "beta_retrospective_fitted":beta,
                              "train_penalized_poisson_objective":objective,
                              "bootstrap_seed":SEED,
                              "bootstrap_runs":BOOTSTRAP},
            "folds":folds,
            "cautions":["132 UEFA match ID links and local goal summaries are review-only",
                        "Elo dated values may reflect corrections after the original historic match",
                        "A dated row is not proof of publication/first_seen before kickoff",
                        "Only 32 final January games, 5 distinct play dates",
                        "If Elo seems good, it still cannot go into production without prospectively locked evidence"]}
    path=Path(out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n",
                    encoding="utf-8")
    summary={"status":report["status"],"decision":decision,"cohort":coverage,
             "beta_retro":beta,"val_delta":val_d,"holdout_delta":test_d,
             "val_1x2":folds["validation"]["metrics"]["1x2_logloss"],
             "holdout_1x2":folds["holdout"]["metrics"]["1x2_logloss"],
             "main_unchanged":True,"model_not_approved":True}
    print("ELO_M0_PAIRED_ONE_SHOT="+json.dumps(summary,ensure_ascii=False,sort_keys=True))
    return report

def main():
    parser=argparse.ArgumentParser()
    for name in ("official","goals","history","crosswalk","out"):
        parser.add_argument("--"+name,required=True)
    a=parser.parse_args()
    try:run(a.official,a.goals,a.history,a.crosswalk,a.out)
    except Exception as exc:
        # Failure is explicitly recorded, no silent selective match filtering.
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps({"schema":VERSION,"status":"PAIRED_ELO_EXPERIMENT_BLOCKED",
            "error_type":type(exc).__name__,"reason":str(exc)[:600],
            "main_modified":False,"pilot_recorded":False,
            "model_weight_approved":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("ELO_RETROSPECTIVE_TEST_BLOCKED "+type(exc).__name__+" "+str(exc))
        raise
if __name__=="__main__":main()
