"""2026 Nov 4/6/7/8 completed 99 scores: retrospective as-of replay, NOT a seal.

One LOCKED predeclared challenger (both defences at 80%) vs original M4.
Historical 2025/26 DEV already selected this option; do NOT tune on the 99.
All M4 fits explicitly exclude each match's date and all subsequent results.
Never update M4, previous SHA-sealed forecasts, betting picks, archives or UI.

This is an out-of-development-period retrospective check, NOT a real
pre-kickoff sealed prospective forecast or a newly verified source.
The 99 scores have mixed public-source verification grades; report all.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,math,sys
from pathlib import Path
from datetime import date

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments/263"))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from exp_263_batch import clean_rows
from full_match_eligibility_263 import full_match_rows
from m4_integrated import fit_m4,predict_m4,score_markets,use_lock
from m4_opponent_defence_shrinkage_263 import (
   candidate_lambdas,losses,LEAGUES,PINS,FILES,LOCK)
# External score ledger: Git blob SHA explicitly pin. The ordinary historical
# CSVs and frozen M4 mathematical source are also SHA256 pinned by PINS.
NOV99=ROOT/"data/quad_accepted_263/completed_99_results_only_20261110.json"
NOV99_GIT_BLOB_SHA="b9332f9a99eb51aff808de9034b3498a89b10f03"
DATES={"2026-11-04":4,"2026-11-06":10,"2026-11-07":43,"2026-11-08":42}
SOURCE_GRADES={
 "OFFICIAL_PAGE_AND_PROVIDER_RESEARCH_CONCORDANT":28,
 "DIRECT_LEAGUE_OR_CLUB_SCORE_PAGE":28,
 "PUBLIC_SECONDARY_SCORE_WITH_PARTIAL_OFFICIAL_FIXTURE":43
}
METRICS=("KG_Brier","Over25_Brier","MS_Brier",
         "KG_logloss","Over25_logloss","MS_logloss")
LABELS={"KG_Brier":"KG Var","Over25_Brier":"2.5 Üst","MS_Brier":"MS"}
TARGET_CANDIDATE="both_defences_080"
SCHEMA="263_NOV99_RECONSTRUCTED_PREMATCH_ASOF_OPPONENT_DEFENCE_080_ONLY_V1"

class StopResearch(ValueError):pass
def need(ok,message):
    if not ok:raise StopResearch(message)
def sha256(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def gitblob(path):
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()
def mean(vals):return sum(vals)/len(vals) if vals else None
def key(x):return x["league"],x["match_date"],x["home_id"],x["away_id"]

def read_history():
    for k,path in FILES.items():
        need(sha256(path)==PINS[k],"FROZEN_SOURCE_CHANGED_"+k)
    need(gitblob(NOV99)==NOV99_GIT_BLOB_SHA,"NOV99_RESULTS_BLOB_CHANGED")
    record=json.loads(NOV99.read_text(encoding="utf-8"))
    need(record.get("schema")=="263_RESULTS_ONLY_APPEND_ARCHIVE_V1",
         "NOV99_ARCHIVE_SCHEMA_CHANGED")
    need(record.get("base_accepted_history_count")==4518 and
         record.get("new_completed_result_count")==99,"NOV99_COHORT_CHANGED")
    reported=record["records"]
    need(len(reported)==99,"NOV99_NOT_99")
    need(dict(collections.Counter(x["match_date"] for x in reported))==DATES,
         "NOV99_DATE_COUNTS_CHANGED")
    need(dict(collections.Counter(x["source_class"] for x in reported))==SOURCE_GRADES,
         "NOV99_SOURCE_GRADE_COUNTS_CHANGED")
    need(set(x["league"] for x in reported)==set(LEAGUES),
         "NOV99_NOT_ALL_10_LEAGUES")
    need(len({key(x) for x in reported})==99,
         "NOV99_DUPLICATE_REAL_TEAM_DATE_IDENTITY")
    need(all(x["season"]=="2026-2027" and
             x["status"]=="COMPLETED_PUBLIC_SCORE_RESEARCH_CONCORDANT" and
             isinstance(x.get("score_source_url"),str) and
             x["score_source_url"].startswith("https://") and
             all(isinstance(x.get(g),int) and x[g]>=0
                 for g in ("home_goals","away_goals")) and
             x["result"]==("H" if x["home_goals"]>x["away_goals"] else
                          "A" if x["away_goals"]>x["home_goals"] else "D")
             for x in reported),"NOV99_INVALID_RESULT_OR_SOURCE_SCOPE")
    base=clean_rows(FILES["original"])
    scores=clean_rows(FILES["scores"])
    need(len(base)==4518 and len(scores)==4617,
         "HISTORICAL_CSV_COUNTS_CHANGED")
    old={r["fixture_id"]:r for r in base}
    combined={r["fixture_id"]:r for r in scores}
    need(len(old)==4518 and len(combined)==4617 and
         all(combined.get(k)==r for k,r in old.items()) and
         len(set(combined)-set(old))==99,
         "4518_OR_99_RESULT_APPEND_INTEGRITY_FAILED")
    full,excluded,_=full_match_rows(scores)
    need(len(full)==4616 and len(excluded)==1,
         "NORMAL_DURATION_TRAINING_POLICY_CHANGED")
    by_identity=collections.defaultdict(list)
    for r in full:by_identity[key(r)].append(r)
    for r in reported:
        match=by_identity.get(key(r),[])
        need(len(match)==1,"NOV99_NOT_UNIQUELY_JOINED_TO_CSV")
        matched=match[0]
        need(matched["season"]==r["season"] and
             int(matched["home_goals"])==r["home_goals"] and
             int(matched["away_goals"])==r["away_goals"] and
             matched["result"]==r["result"],"NOV99_CSV_GOAL_OR_RESULT_CONFLICT")
        need(matched["fixture_id"] not in old,
             "NOV99_ALREADY_IN_ORIGINAL_4518")
    frozen=json.loads(LOCK.read_text(encoding="utf-8"))
    need(frozen.get("m4_engine_sha256")==PINS["engine"] and
         frozen.get("evaluation_season_excluded")=="2026-2027",
         "M4_LOCK_HOLDOUT_NOT_FROZEN")
    settings=use_lock(frozen)
    return reported,full,settings

def top1_accuracy(markets,h,a):
    yes=int(h>0 and a>0)
    over=int(h+a>=3)
    actual="H" if h>a else "A" if a>h else "D"
    return {
      "KG":int((markets["BTTS_YES"]>=.5)==bool(yes)),
      "Over25":int((markets["OVER_2.5"]>=.5)==bool(over)),
      "MS":int(max(markets["1X2"],key=markets["1X2"].get)==actual)}
def pct(values):
    return 100*mean(values) if values else None

def run():
    records,eligible,settings=read_history()
    # Unique leagues/day can share one fit. Every fit includes only prior
    # calendar-day results: no same-day/after match outcome is ever trained.
    fit_cache={}
    attempted=[]
    issues=collections.Counter()
    for r in sorted(records,key=lambda x:(x["match_date"],x["league"],x["home_id"])):
        league,day=r["league"],r["match_date"]
        k=(league,day)
        if k not in fit_cache:
            prev=[x for x in eligible if x["league"]==league
                  and x["match_date"]<day]
            need(all(x["match_date"]<day for x in prev),"PREMATCH_LEAKAGE")
            fit=fit_m4(eligible,league,day,settings)
            need(fit is not None and fit[3]==len(prev),
                 "M4_FIT_CANNOT_BE_VERIFIED_PRE_DATE_"+league+"_"+day)
            fit_cache[k]={"fit":fit,"history_count":len(prev)}
        fit=fit_cache[k]["fit"]
        info={
            "league":league,"date":day,
            "home_name":r["home_name"],"away_name":r["away_name"],
            "home_goals":r["home_goals"],"away_goals":r["away_goals"],
            "source_class":r["source_class"],
            "training_matches_strictly_before_day":fit_cache[k]["history_count"],
            "asof_model_prediction_ever_sha_sealed":False
        }
        if r["home_id"] not in fit[1] or r["away_id"] not in fit[1]:
            info["status"]="UNSEEN_TEAM_SAFETY_EXCLUDED"
            issues[info["status"]]+=1
            attempted.append(info)
            continue
        original=predict_m4(fit,r["home_id"],r["away_id"])
        challenger=candidate_lambdas(fit,r["home_id"],r["away_id"],
                                     "symmetric",0.80)
        if original is None or challenger is None:
            info["status"]="ORIGINAL_OR_CHALLENGER_LAMBDA_UNSAFE"
            issues[info["status"]]+=1
            attempted.append(info)
            continue
        pm4=score_markets(*original)["markets"]
        pnew=score_markets(*challenger)["markets"]
        y1=losses(pm4,r["home_goals"],r["away_goals"])
        y2=losses(pnew,r["home_goals"],r["away_goals"])
        info.update({
          "status":"PAIRED_RECONSTRUCTED_ASOF_ONLY",
          "original_M4_lambda_home":original[0],
          "original_M4_lambda_away":original[1],
          "shadow_080_lambda_home":challenger[0],
          "shadow_080_lambda_away":challenger[1],
          "original_probabilities":{
             "KG":pm4["BTTS_YES"],"Over25":pm4["OVER_2.5"],
             "MS":pm4["1X2"]},
          "shadow_080_probabilities":{
             "KG":pnew["BTTS_YES"],"Over25":pnew["OVER_2.5"],
             "MS":pnew["1X2"]},
          "brier_logloss_frozen":y1,
          "brier_logloss_shadow_080":y2,
          "brier_logloss_delta_shadow_minus_M4":{
              x:y2[x]-y1[x] for x in METRICS},
          "top1_correct_frozen":top1_accuracy(pm4,r["home_goals"],r["away_goals"]),
          "top1_correct_shadow_080":top1_accuracy(pnew,r["home_goals"],r["away_goals"])
        })
        attempted.append(info)
    valid=[r for r in attempted if r["status"]=="PAIRED_RECONSTRUCTED_ASOF_ONLY"]
    need(len(attempted)==99 and len(valid)>=50,
         "TOO_FEW_PAIRED_RETROSPECTIVE_MATCHES")
    need(len({(r["league"],r["date"],r["home_name"],r["away_name"])
              for r in attempted})==99,"DUPLICATE_ATTEMPT")
    def summary(subset):
        if not subset:return None
        return {
         "n":len(subset),
         "frozen_brier":{metric:mean([r["brier_logloss_frozen"][metric]
                                      for r in subset]) for metric in METRICS},
         "shadow_080_brier":{metric:mean([r["brier_logloss_shadow_080"][metric]
                                          for r in subset]) for metric in METRICS},
         "delta_shadow_minus_M4_negative_better":{
             metric:mean([r["brier_logloss_delta_shadow_minus_M4"][metric]
                          for r in subset]) for metric in METRICS},
         "top1_correct_counts":{
             grp:{
               "original":sum(r["top1_correct_frozen"][grp] for r in subset),
               "shadow_080":sum(r["top1_correct_shadow_080"][grp] for r in subset),
             } for grp in ("KG","Over25","MS")}
        }
    by_league={league:summary([r for r in valid if r["league"]==league])
               for league in LEAGUES}
    by_day={day:summary([r for r in valid if r["date"]==day])
            for day in sorted(DATES)}
    out={
      "schema":SCHEMA,
      "decision":"RETROSPECTIVE_STRESS_TEST_NO_PRODUCTION_PROMOTION",
      "sample":"archived_99_completed_results_from_Nov_04_06_07_08_2026",
      "selection_lock":"ONE_PRESELECTED_SYMMETRIC_DEFENCE_WEIGHT_0_80_VS_ORIGINAL_M4",
      "not_original_prematch_SHA_forecasts":True,
      "not_a_prospective_or_live_forecast":True,
      "training_asof_target_date_exclusive":True,
      "reused_winner_settings_from_2025_26_only":True,
      "new99_outcomes_used_to_fit_or_adjust_parameters":False,
      "historical_m4_predictions_generated_after_results_known":True,
      "test_sample_no_longer_untouched_after_this_evaluation":True,
      "comparison_is_not_in_sample_2025_26_dev_but_is_retrospective":True,
      "original_source_SHA256":PINS["original"],
      "history_with99_SHA256":PINS["scores"],
      "goal_model_code_SHA256":PINS["engine"],
      "new99_json_git_blob_sha":NOV99_GIT_BLOB_SHA,
      "source_quality_mix":SOURCE_GRADES,
      "official_unique_match_ids_not_independently_verified":True,
      "unknown_score_source_uncertainty":True,
      "attempted_99":len(attempted),"paired_usable":len(valid),
      "not_scored_reasons":dict(issues),
      "number_of_asof_model_fits":len(fit_cache),
      "no_form_data_imputed":True,
      "no_probabilities_rewritten_in_Git":True,
      "betting_authorized":False,
      "main_m4_or_SHA_seals_changed":False,
      "overall":summary(valid),
      "by_league":by_league,
      "by_match_day":by_day,
      "independent_date_block_CI":None,
      "date_cluster_CI_reason":"Only 4 distinct match days; cannot claim a reliable date-block interval.",
      "per_match_retrospective_comparison":attempted,
      "limitations":[
       "Archived 99 mixed-grade score sources: 43 secondary partly corroborated, no unique official provider IDs independently checked.",
       "No actual pre-match SHA forecasts created for these 99; all M4 fits reconstructed AFTER outcomes were known.",
       "The new99 score rows do not contribute to any fit for their own date or earlier dates; 2025/26 M4 settings remain frozen.",
       "Four calendar dates give too few independent day clusters for a defensible bootstrap confidence interval.",
       "Any result is a once-only out-of-dev retrospective stress test; cannot be reused to tune 80% or claim prospective predictive edge.",
       "A wrong old or newly archived match outcome would alter reported performance; archive source evidence remains research-grade.",
       "No new pilot, no odds, no stake or financial return proof; original model probabilities and all historical seals untouched."
      ]
    }
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    a=p.parse_args()
    report=run()
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as o:
        json.dump(report,o,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)
        o.write("\n")
    print(json.dumps({
       "status":report["decision"],
       "attempted":report["attempted_99"],
       "paired":report["paired_usable"],
       "blocked":report["not_scored_reasons"],
       "fit_count":report["number_of_asof_model_fits"],
       "overall":report["overall"],
       "by_day":{k:None if v is None else {
         "n":v["n"],"delta":v["delta_shadow_minus_M4_negative_better"]
         } for k,v in report["by_match_day"].items()},
       "league_delta":{k:None if v is None else {
         "n":v["n"],"delta":v["delta_shadow_minus_M4_negative_better"]
         } for k,v in report["by_league"].items()},
       "production_modified":False
    },ensure_ascii=False))
if __name__=="__main__":
    main()
