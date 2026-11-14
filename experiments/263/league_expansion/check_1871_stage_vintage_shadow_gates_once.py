#!/usr/bin/env python3
"""One NEW audit dimension on the already classified 1871 CC0-source rows:
competition stage, freshness, same-day club conflicts, and feature time vintage.

Strictly read-only. No match score re-validation of old 178/22/472/420/50
checks, no license re-probe, no source CSV exports, no training, no M4 edits.
"""
from __future__ import annotations
import argparse, json, re
from collections import Counter, defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
from prepare_2396_provenance_rights_quality_gate_20261114 import EXPECTED,HOLD,read_csv,match_key

ROOT=Path("experiments/263/league_expansion")
CUTOFF=date(2026,11,13) # previous frozen research cut, not a fresh fixture snapshot
CC0="PUBLISHER_CC0_CLAIM"
STAGES={"regular","championship","relegation","conference_playoff","other","undeclared"}

def recognize_stage(row):
    value=(row.get("round_stage") or "").casefold().strip()
    if not value:return "undeclared"
    if value.startswith("regular season"):return "regular"
    if value.startswith("championship round"):return "championship"
    if value.startswith("relegation round"):return "relegation"
    if "play-off" in value or "playoff" in value:return "conference_playoff"
    return "other"

def day_of(row):
    val=row["date"]
    if not re.fullmatch(r"20\d\d-\d\d-\d\d",val):raise ValueError("BAD_DATE_FORMAT")
    d=date.fromisoformat(val)
    s=row["season"]
    start,end=((date(2025,7,1),date(2026,6,30)) if s=="2025-26"
               else (date(2026,7,1),CUTOFF) if s=="2026-27" else (None,None))
    if start is None or not start<=d<=end:
        raise ValueError("SEASON_WINDOW_OR_FUTURE_DATE")
    return d

def classify():
    holds,hsha=read_csv(HOLD)
    held={match_key(r) for r in holds}
    if len(holds)!=200 or len(held)!=200:raise ValueError("FROZEN_HOLD_COUNT_CHANGED")
    groups=defaultdict(list)
    stages=defaultdict(Counter)
    source_undec=defaultdict(Counter)
    same_day=defaultdict(list)
    source_pin_counts=Counter()
    source_held=Counter()
    candidate_n=0
    che_witness=0
    original_aut=0
    restored_aut=0
    aut_playoffs=[]
    key_seen=set()
    for filename,(sha,expected,kind) in EXPECTED.items():
        rows,current_sha=read_csv(filename)
        if len(rows)!=expected or current_sha!=sha:
            raise ValueError("FROZEN_SOURCE_SHA_CHANGED")
        for row in rows:
            k=match_key(row)
            if k in key_seen:raise ValueError("DUPLICATE_IN_RESEARCH_QUARANTINE")
            key_seen.add(k)
            d=day_of(row)
            if k in held:
                source_held[filename]+=1
                continue
            if kind!=CC0:continue
            stage=recognize_stage(row)
            g=row["league"]+"/"+row["season"]
            groups[g].append((d,row,filename,stage))
            stages[g][stage]+=1
            source_undec[filename][stage]+=1
            source_pin_counts[filename]+=1
            candidate_n+=1
            if row["league"]=="CHE1" and row["season"]=="2026-27":
                if filename!="cc0_new_485_2526_2627_QUARANTINE_20261113.csv":
                    raise ValueError("CHE1_SCORE_WITNESS_SOURCE_DRIFT")
                che_witness+=1
            if row["league"]=="AUT1" and row["season"]=="2025-26":
                if filename=="training_2025_26_cc0_scored_QUARANTINE.csv":
                    original_aut+=1
                    # No explicit round field: a provenance inference, not
                    # a fully independent regular-season stage verification.
                    if d>=date(2026,3,9):
                        raise ValueError("UNLABELED_AUT_FT_AFTER_REGULAR_SEASON")
                elif filename=="score_shape_recovery_295_2526_QUARANTINE_20261113.csv":
                    restored_aut+=1
                else:raise ValueError("AUT1_SOURCE_DRIFT")
                if stage=="conference_playoff":
                    aut_playoffs.append({"date":row["date"],"home":row["home"],
                        "away":row["away"],"stage":row["round_stage"]})
            for name in (row["home"],row["away"]):
                same_day[(row["league"],row["season"],d.isoformat(),name.casefold())].append(
                    {"source":filename,"stage":stage,"date":row["date"]})
    if len(key_seen)!=2396 or candidate_n!=1871 or sum(source_held.values())!=200:
        raise ValueError("2396_TO_1871_SPLIT_DRIFT")
    if che_witness!=54:raise ValueError("CHE1_PRIOR_WITNESS_COUNT_CHANGED")
    if original_aut!=67 or restored_aut!=128:
        raise ValueError("AUT1_STAGE_PROVENANCE_COUNT_CHANGED")
    a=stages["AUT1/2025-26"]
    expected_a={"undeclared":67,"regular":65,"championship":30,
                "relegation":30,"conference_playoff":3}
    if dict(a)!=expected_a:
        raise ValueError("AUT1_STAGE_DISTRIBUTION_CHANGED:"+repr(dict(a)))
    # Recovered proper season-stage labels plus 67 unlabeled first-half rows:
    # 67+65=132 regular-season *candidates*, not independently stage-approved.
    # Group/championship 30+30=60. Three extra playoff games must NOT be
    # mixed into ordinary league-model training.
    clashes=[{"league":k[0],"season":k[1],"date":k[2],"club":k[3],
        "records":len(v)} for k,v in same_day.items() if len(v)>1]
    leagues={}
    current_lag={}
    for label,matches in sorted(groups.items()):
        dates=sorted(x[0] for x in matches)
        league,season=label.split("/")
        counts=stages[label]
        leagues[label]={
            "candidate_rows":len(matches),
            "stage_declared_rows":len(matches)-counts["undeclared"],
            "stage_undeclared_rows":counts["undeclared"],
            "stages":dict(counts),
            "earliest_scored_date":dates[0].isoformat(),
            "latest_scored_date":dates[-1].isoformat(),
            "score_witness_from_previous_different_source":
                 54 if label=="CHE1/2026-27" else 0,
            "row_level_full_time_QA_for_others":"PENDING_NOT_REPEAT_OLD_CLOSED_CASES",
            "training_admitted":0
        }
        if season=="2026-27":
            age=(CUTOFF-dates[-1]).days
            current_lag[label]={"last_recorded_result":dates[-1].isoformat(),
                "calendar_lag_days_to_research_snapshot":age,
                "freshness": "SOURCE_COVERAGE_REVIEW_REQUIRED" if age>21
                    else "RECENCY_ALONE_DOES_NOT_PROVE_COMPLETENESS"}
    input_counts=dict(source_pin_counts)
    if input_counts != {
         "training_2025_26_cc0_scored_QUARANTINE.csv":1063,
         "cc0_new_485_2526_2627_QUARANTINE_20261113.csv":485,
         "cc0_aut1_2026_27_42_QUARANTINE_20261113.csv":42,
         "score_shape_recovery_295_2526_QUARANTINE_20261113.csv":281,
        }:
        raise ValueError("EXPLICIT_CC0_SOURCE_SUBSET_COUNT_CHANGED:"+repr(input_counts))
    summary={
        "checked_utc":datetime.now(timezone.utc).isoformat(),
        "original_frozen_cutoff":"2026-11-13",
        "analysis_scope":"1871_unheld_CC0_publication_claim_only_no_training",
        "all_2396_scored_research_keys_unchanged":2396,
        "old_200_held_source_identities_unchanged":200,
        "CC0_not_explicitly_held":1871,
        "prior_already_double_source_corrobated_FT_CHE1_2026_27":che_witness,
        "other_records_without_prior_reusable_individual_FT_witness":1817,
        "competition_stage_separation":{
          "AUT1_2025_26":{
             "raw_scored_total":195,"67_unlabeled_early_results":67,
             "65_labeled_regular_results":65,"regular_candidate_sum_not_independent_stage_proof":132,
             "championship_group":30,"relegation_group":30,
             "extra_conference_league_playoffs_not_normal_league":len(aut_playoffs),
             "playoff_event_facts":aut_playoffs,
             "default_shadow_train_exclusion":"ALL_3_CONFERENCE_LEAGUE_PLAYOFFS",
             "additional_conditional_gate":"67 early regular-stage candidates have no explicit stored stage label; infer only after schedule stage verification"
          }},
        "same_club_two_scored_games_on_same_day":{
            "potential_anomaly_count":len(clashes),
            "sample_anomalies":clashes[:15],
            "automatic_training_exclusions_pending_review":len(clashes)
        },
        "source_file_candidate_counts":input_counts,
        "league_season_candidate_coverage":leagues,
        "current_season_recency_gates":current_lag,
        "rights_review":"PUBLISHER_CC0_CLAIM_NOT_FULL_UPSTREAM_RIGHTS_OR_INDIVIDUAL_SCORE_PROOF",
        "pre_kickoff_feature_vintage_status":"NOT_RECORDED_PER_MATCH",
        "training_admitted":0,
        "new_model_tests_run":0,
        "M4_main_SHA_modified":False,
        "source_match_files_modified":False,
        "repeated_prior_scored_QA_tests":0,
        "new_GitHub_source_downloads":0,
        "next":"Resolve any same-day fixture anomalies and AUT1 stage labels separately; seek independently licensed FT witnesses for rows other than the prechecked CHE1 54. Source publication, feature vintage and time-ordered splits must pass before any shadow training."
    }
    return summary

def test():
    assert recognize_stage({"round_stage":"Championship Round - 3"})=="championship"
    assert recognize_stage({"round_stage":"Conference League Play-offs - Final"})=="conference_playoff"
    assert recognize_stage({"round_stage":"Regular Season - 4"})=="regular"
    assert recognize_stage({"round_stage":""})=="undeclared"
    assert day_of({"date":"2025-11-04","season":"2025-26"})==date(2025,11,4)
    for r in ({"date":"2026-11-14","season":"2026-27"},
              {"date":"2025-06-30","season":"2025-26"},
              {"date":"2026-06-30","season":"2026-27"}):
        try:day_of(r)
        except ValueError:pass
        else:raise AssertionError("future/out-of-season allowed")
    print("PASS synthetic stage whitelist, playoff segregation, no future/as-of date")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--run",action="store_true")
    opt=p.parse_args()
    if opt.self_test:test()
    if opt.run:
        print("NEW_STAGE_QA_START")
        print(json.dumps(classify(),ensure_ascii=False,indent=2))
        print("NEW_STAGE_QA_END")
