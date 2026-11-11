"""Read-only, *real SHA-sealed* B/C2/C3/M4 vs archived completed results.

Close legacy96 bookkeeping without conflating: Nov6 4 actual quad seals,
Nov7 3 separate acceptance seals, Nov8 40 NEW100 morning seals. The '96'
legacy name was the target, not proof of 96 matched sealed fixture results.
Join completed 99 mixed-source archived full-time results ONLY by exact
league/date/home_ID/away_ID. No new matches, no backfilled forecast seals,
no refitting, no outcome-driven model-market selection or betting decisions.

Statistically insufficient 3 distinct sealed dates => NO model promotion,
NO cherry-picked 'winner', NO day-block CIs, NO market EV without odds.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re, sys
from collections import Counter,defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments/263"))
from forward_c3 import read_aware,canonical_bytes
from m4_integrated import score_markets
from full_match_eligibility_263 import full_match_rows
from exp_263_batch import clean_rows

ARCHIVE=ROOT/"data/quad_accepted_263/completed_99_results_only_20261110.json"
HISTORY=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
FROZEN=ROOT/"data/quad_accepted_263/extended_history.csv"
PIN={
 "archive_blob":"b9332f9a99eb51aff808de9034b3498a89b10f03",
 "historical4518":"1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9",
 "historical4617":"637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89"}
COHORT_PATHS={
 "nov6_quad":("forward_quad_263",4,"2026-11-06"),
 "nov7_acceptance_separate":("forward_acceptance_263",3,"2026-11-07"),
 "nov8_new100":("forward_morning_263",40,"2026-11-08")}
COHORT_TOTAL=47
MODELS=("B","C2","C3","M4")
MARKETS=("KG","OVER25","MS")
SCHEMA="263_LEGACY96_ACTUAL_SEALS_PAIRED_4MODEL_KG_O25_MS_RESEARCH_V1"
GRADES={
 "OFFICIAL_PAGE_AND_PROVIDER_RESEARCH_CONCORDANT":28,
 "DIRECT_LEAGUE_OR_CLUB_SCORE_PAGE":28,
 "PUBLIC_SECONDARY_SCORE_WITH_PARTIAL_OFFICIAL_FIXTURE":43}

class AuditError(ValueError):pass
def must(ok,reason):
    if not ok:raise AuditError(reason)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def blobsha(p):
    data=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def key(league,day,home,away):return (league,day,home,away)
def avg(x):return sum(x)/len(x) if x else None
def checked_prob(v):
    must(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1,
         "UNSAFE_MODEL_PROBABILITY")
    return float(v)

def verified_archive(root=ROOT):
    a=root/"data/quad_accepted_263/completed_99_results_only_20261110.json"
    h=root/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
    b=root/"data/quad_accepted_263/extended_history.csv"
    must(blobsha(a)==PIN["archive_blob"] and sha(h)==PIN["historical4617"]
         and sha(b)==PIN["historical4518"],"HISTORY_OR_SCORE_ARCHIVE_MUTATED")
    record=json.loads(a.read_text(encoding="utf-8"))
    rows=record["records"]
    must(len(rows)==99 and record.get("new_completed_result_count")==99 and
         dict(Counter(x["source_class"] for x in rows))==GRADES,
         "NOT_ORIGINAL_99_MIXED_SOURCE_RESULTS")
    idmap={}
    for row in rows:
        k=key(row["league"],row["match_date"],row["home_id"],row["away_id"])
        must(k not in idmap,"DUPLICATE_99_MATCH")
        must(row["season"]=="2026-2027" and
             all(type(row[t]) is int and row[t]>=0 for t in ("home_goals","away_goals"))
             and row["result"]==("H" if row["home_goals"]>row["away_goals"] else
                 "A" if row["away_goals"]>row["home_goals"] else "D"),
             "BAD_99_FULLTIME_RESULT")
        idmap[k]=row
    old=clean_rows(b);new=clean_rows(h)
    must(len(old)==4518 and len(new)==4617 and
         all(x in new for x in old),"HISTORICAL_SOURCE_NOT_APPEND_ONLY")
    eligible,excluded,_=full_match_rows(new)
    must(len(eligible)==4616 and len(excluded)==1,"NINETY_MINUTE_EXCEPTION_CHANGED")
    joined=defaultdict(list)
    for row in eligible:
        joined[key(row["league"],row["match_date"],row["home_id"],row["away_id"])].append(row)
    must(all(len(joined[k])==1 and
             int(joined[k][0]["home_goals"])==r["home_goals"] and
             int(joined[k][0]["away_goals"])==r["away_goals"]
             for k,r in idmap.items()),"MIXED_ARCHIVED_RESULT_IDENTITY_NOT_MATCHED")
    return idmap

def sealed_records(root=ROOT):
    allrows=[];seenSHA=set();seenMatch=set()
    for cohort,(folder,required,day) in COHORT_PATHS.items():
        paths=sorted((root/folder/day).glob("*.json"))
        must(len(paths)==required,"ACTUAL_SHA_COHORT_CARDINALITY_CHANGED_"+cohort)
        for path in paths:
            must(re.fullmatch(r"[0-9a-f]{24}\.json",path.name) is not None,
                 "INVALID_SEALED_FILENAME")
            doc=json.loads(path.read_text(encoding="utf-8"))
            must(doc.get("schema")=="quad_forward_263_v1" and
                 doc.get("status")=="EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING",
                 "NOT_REAL_FOUR_MODEL_SEAL")
            digest=doc.get("payload_sha256")
            payload=dict(doc);payload.pop("payload_sha256",None)
            must(isinstance(digest,str) and len(digest)==64 and
                 hashlib.sha256(canonical_bytes(payload)).hexdigest()==digest,
                 "FORECAST_SHA_INVALID")
            must(digest not in seenSHA,"DUPLICATE_FORECAST_SHA")
            seenSHA.add(digest)
            fx=doc["fixture"]
            must(fx["match_local_date"]==day and
                 fx["fixture_verification"]=="VERIFIED_BY_LIVE_OFFICIAL_GATE",
                 "PREMATCH_FIXTURE_NOT_OFFICIAL_GATE")
            made=read_aware(doc["created_at_utc"])
            checked=read_aware(fx["source_checked_at_utc"])
            ko=read_aware(fx["kickoff_utc"])
            must(checked<=ko and checked<=made+timedelta(seconds=60) and
                 made<ko,"SEALED_RECORD_AFTER_KICKOFF_OR_BAD_SOURCE_TIME")
            k=key(fx["league"],day,fx["home_id"],fx["away_id"])
            must(k not in seenMatch,"SAME_FIXTURE_DOUBLE_COUNTED_ACROSS_COHORTS")
            seenMatch.add(k)
            must(set(doc.get("model_predictions",{}))==set(MODELS),
                 "MISSING_ONE_OF_FOUR_MODEL_SLOTS")
            allrows.append({"cohort":cohort,"path":path.relative_to(root).as_posix(),
                "forecast_sha256":digest,"fixture_key":k,
                "predictions":doc["model_predictions"]})
    must(len(allrows)==COHORT_TOTAL,"UNEXPECTED_REGISTERED_ACTUAL_SEALS")
    return allrows

def outcome(h,a):
    return {"MS":"H" if h>a else "A" if a>h else "D",
            "KG":int(h>0 and a>0),"OVER25":int(h+a>=3)}

def probs(pred):
    markets=pred["goals"]["markets"]
    ms=markets["1X2"]
    must(set(ms)=={"H","D","A"},"MS_PROBABILITY_SHAPE")
    m={k:checked_prob(ms[k]) for k in ("H","D","A")}
    must(abs(sum(m.values())-1)<1e-7,"INVALID_MS_NORMALIZATION")
    return {"MS":m,
            "KG":checked_prob(markets["BTTS_YES"]),
            "OVER25":checked_prob(markets["OVER_2.5"])}

def mark(prob,actual,market):
    if market=="MS":
        must(set(prob)=={"H","D","A"},"NOT_THREE_WAY_MS")
        return {"brier":sum((prob[x]-int(x==actual))**2 for x in ("H","D","A")),
                "logloss":-math.log(max(.001,prob[actual])),
                "top1_correct":int(max(prob,key=prob.get)==actual)}
    yes=checked_prob(prob)
    return {"brier":(yes-actual)**2,
            "logloss":-math.log(max(.001,yes if actual else 1-yes)),
            "top1_correct":int((yes>=.5)==bool(actual))}

def audited(root=ROOT):
    reference=verified_archive(root)
    seals=sealed_records(root)
    counts=Counter();metrics=[];missing=[]
    for record in seals:
        result=reference.get(record["fixture_key"])
        if result is None:
            counts["NO_EXACT_ARCHIVED_MATCH_SCORE"]+=1
            missing.append({"cohort":record["cohort"],"path":record["path"],
                            "forecast_sha256":record["forecast_sha256"],
                            "match_key":record["fixture_key"],
                            "status":"UNMATCHED_NO_RESULT_GUESSED"})
            continue
        target=outcome(result["home_goals"],result["away_goals"])
        m={}
        for model,pred in record["predictions"].items():
            if pred.get("status")!="AVAILABLE":continue
            p=probs(pred)
            m[model]={market:mark(p[market],target[market],market)
                      for market in MARKETS}
        counts["EXACT_SHA_MATCHED"]+=1
        if set(m)==set(MODELS):counts["ALL_FOUR_MODELS_AVAILABLE"]+=1
        metrics.append({
          "cohort":record["cohort"],"league":result["league"],
          "date":result["match_date"],
          "forecast_sha256":record["forecast_sha256"],"path":record["path"],
          "source_class":result["source_class"],
          "score":[result["home_goals"],result["away_goals"]],
          "goal_markets":m,
          "model_unavailable":[name for name in MODELS if name not in m],
          "result_status":"MIXED_GRADE_PUBLIC_SCORE_ARCHIVE_NOT_NEW_OFFICIAL_ATTESTATION"
        })
    def summary(samples):
        if not samples:return {"n":0,"models":None,"pair_n":None}
        scores={};pairs={}
        for model in MODELS:
            sub=[r["goal_markets"][model] for r in samples
                 if model in r["goal_markets"]]
            scores[model]={
                market:{"n":len(sub),
                        "brier":avg([r[market]["brier"] for r in sub]),
                        "logloss":avg([r[market]["logloss"] for r in sub]),
                        "top1_correct_count":sum(r[market]["top1_correct"] for r in sub)}
                for market in MARKETS}
        # Compare only same exact matches where all FOUR models were available.
        complete=[r for r in samples if len(r["goal_markets"])==len(MODELS)]
        common={}
        for model in MODELS:
            common[model]={market:{
               "brier":avg([r["goal_markets"][model][market]["brier"] for r in complete]),
               "logloss":avg([r["goal_markets"][model][market]["logloss"] for r in complete]),
               "top1_correct_count":sum(r["goal_markets"][model][market]["top1_correct"]
                                         for r in complete)
               } for market in MARKETS}
        for model in ("B","C2","C3"):
            pairs[model+"_minus_M4"]={
                market:{"n_same_four_model_matches":len(complete),
                        "brier_delta_positive_favors_M4":avg([
                            r["goal_markets"][model][market]["brier"]-
                            r["goal_markets"]["M4"][market]["brier"]
                            for r in complete]),
                        "logloss_delta_positive_favors_M4":avg([
                            r["goal_markets"][model][market]["logloss"]-
                            r["goal_markets"]["M4"][market]["logloss"]
                            for r in complete])}
                for market in MARKETS}
        return {"n":len(samples),"n_all_four":len(complete),
                "models":scores,"same_four_model_scores":common,
                "paired_model_minus_M4":pairs}
    dates=sorted({r["date"] for r in metrics})
    return {
      "schema":SCHEMA,"status":"SEALED_PREGAME_FORECAST_POSTMATCH_DESCRIPTIVE_NO_PROMOTION",
      "legacy96_is_nominal_cohort_goal_not_96_proven_actual_seals":True,
      "actual_seal_counts":{k:v[1] for k,v in COHORT_PATHS.items()},
      "actual_legacy_weekend_registered_seals":len(seals),
      "actual_exact_archived_score_pairs":len(metrics),
      "unmatched_seal_count":len(missing),"unmatched_seals":missing,
      "result_source_grade_mix_on_matched":dict(Counter(r["source_class"] for r in metrics)),
      "all_four_models_match_count":counts["ALL_FOUR_MODELS_AVAILABLE"],
      "matched_date_count":len(dates),"matched_dates":dates,
      "overall":summary(metrics),
      "by_cohort":{label:summary([r for r in metrics if r["cohort"]==label])
                   for label in COHORT_PATHS},
      "by_league":{league:summary([r for r in metrics if r["league"]==league])
                   for league in sorted({r["league"] for r in metrics})},
      "matched_actual_forecast_hashes":[r["forecast_sha256"] for r in metrics],
      "market_strategy_audit":{
        "main_reference":"FROZEN_M4_NOT_AUTOMATICALLY_A_NEW_WINNER",
        "B_C2_C3":"ONLY_INDEPENDENT_COMPARATORS_NO_MODEL_ROUTING_PROMOTED",
        "market_picks_included":"KG Var/Yok and 2.5 Alt/Üst and MS 1/X/2",
        "one_top_market_for_betting":"NOT_AUTHORIZED_WITHOUT_VERIFIED_SAME_DAY_ODDS_OR_CALIBRATION",
        "odds_available_for_this_readonly_comparison":False,
        "no_vig_value_edge_calculated":False,
        "recommended_action":"RESEARCH_PAS_NO_PRICE_NO_JUSTIFIED_VALUE",
        "model_market_selection_based_on_result_of_same_test":False,
        "new_selector_or_meta_learner_promoted":False
      },
      "calendar_day_block_interval":None,
      "reason_no_calendar_day_confidence_interval":
          "Weekend has fewer than 10 distinct sealed match dates: cannot credibly rank model by significance.",
      "prediction_percentages_or_immutable_forecasts_changed":False,
      "model_coefficients_changed":False,
      "old_99_result_archive_changed":False,
      "new_pilot_started":False,
      "source_99_provenance_only_mixed_grade":True,
      "all_results_independently_reverified_today":False,
      "betting_authorized":False,
      "per_match_provenance_and_scores":metrics,
      "limitations":[
        "Legacy96 is 96 planned candidates, not 96 unique proven SHA seals with outcomes.",
        "Nov7 acceptance seals are a distinct operational cohort: not silently counted as Nov8 NEW100.",
        "Completed99 outcomes mix 28 stronger concordant, 28 direct scores and 43 secondary research observations; no independent provider IDs.",
        "Matching checks exact league, match day and internal IDs, not merely fuzzy team names.",
        "Market comparisons use same-four-model matches and Brier/logloss; MS 3-way Brier scale cannot compare directly with binary markets.",
        "Weekend dates cannot establish model superiority across future weeks, despite exact historic seals.",
        "No independently verified pregame odds => never certify EV/value, one real betting pick or PAS-to-bet transition.",
        "Do not tune a routing/meta-learner on these already evaluated outcomes and call their in-sample performance prospective."
      ]
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    a=p.parse_args()
    report=audited()
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")
    o=report["overall"]
    brief={"registered":report["actual_legacy_weekend_registered_seals"],
           "matched":report["actual_exact_archived_score_pairs"],
           "unmatched":report["unmatched_seal_count"],
           "four_way_common":report["all_four_models_match_count"],
           "dates":report["matched_dates"],
           "full_model_market_metrics":o["same_four_model_scores"],
           "paired_vs_M4":o["paired_model_minus_M4"],
           "status":report["status"],
           "new_model_promotion":False,"user_market_picks":False}
    print(json.dumps(brief,ensure_ascii=False))
if __name__=="__main__":main()
