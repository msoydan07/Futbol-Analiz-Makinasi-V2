#!/usr/bin/env python3
"""New one-time independent audit: rights + EXACT 296 HOLD + pre-kickoff feature vintage.
Reads only pinned local research CSVs. DOES NOT rerun any match-score sources.
Production code, 871+904 confirmed fact witnesses and 1855 manual xG are untouched.
"""
from __future__ import annotations
import argparse,json,hashlib
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
from prepare_2396_provenance_rights_quality_gate_20261114 import EXPECTED,HOLD,read_csv,match_key,assert_origin
from check_1871_stage_vintage_shadow_gates_once import recognize_stage
EXTRA="eng5_2025_26_96_exact_original_FT_conflict_training_HOLD_20261114.csv"
EXTRA_KEY_SHA="0fc4455beea8089ce8fca68d575af424f5bc3a3be3efe2a06e41fe8403191f90"
EXTRA_BLOB_SHA="0a422d9e0a68b6e714852addcb3ec9cf4602a7f6"
CUTOFF=date(2026,11,13)
CC0="PUBLISHER_CC0_CLAIM"
RIGHTS_UNKNOWN={"CCBY_COMPILATION_UPSTREAM_UNCLEAR","THIRD_PARTY_REHOST_UNCLEARED"}
FEATURE_BANNED={"ft_home","ft_away","ht_home","ht_away","xg_home","xg_away","score","result","ft"}
FEATURE_ALLOWED={"home_prior_games","away_prior_games","home_prior_goals_for","home_prior_goals_against","away_prior_goals_for","away_prior_goals_against"}
def holds():
    old,old_sha=read_csv(HOLD)
    if len(old)!=200:raise ValueError("OLD_200_HOLD_DRIFT")
    old_keys={match_key(r) for r in old}
    if len(old_keys)!=200:raise ValueError("OLD_HOLD_DUPLICATE")
    extra,sha=read_csv(EXTRA)
    if sha!=EXTRA_BLOB_SHA or len(extra)!=96:raise ValueError("96_HOLD_SOURCE_DRIFT")
    expected_keys=[(r["original_date"],r["home"],r["away"]) for r in extra]
    digest=hashlib.sha256("\n".join("|".join(k) for k in expected_keys).encode()).hexdigest()
    if digest!=EXTRA_KEY_SHA or len(set(expected_keys))!=96:
        raise ValueError("96_EXACT_KEYS_DRIFT")
    new_keys=set()
    orig_scores={}
    for x in extra:
        if x["league"]!="ENG5" or x["season"]!="2025-26":raise ValueError("NOT_NATIONAL_LEAGUE_HOLD")
        key=(x["league"],x["season"],x["original_date"],x["home"],x["away"])
        if key in old_keys:raise ValueError("OVERLAPPING_OLD_NEW_HOLD")
        new_keys.add(key)
        orig_scores[key]=(x["original_home_goals"],x["original_away_goals"])
    return old_keys,new_keys,orig_scores

def historical_form_from_certified_past(target, observations):
    """Synthetic contract only. Require actual available_at and kickoff for every observation.
    Never allow target result or future/same-day info into model features.
    """
    permitted=[]
    kickoff=datetime.fromisoformat(target["kickoff_at_utc"].replace("Z","+00:00"))
    if kickoff.tzinfo is None:raise ValueError("NO_TARGET_TIMEZONE")
    for row in observations:
        if row["league"]!=target["league"] or row["season"]!=target["season"]:
            continue
        if row["date"]>=target["date"]: continue
        if "available_at_utc" not in row or not row["available_at_utc"]:
            raise ValueError("HISTORIC_OBSERVATION_VINTAGE_MISSING")
        available=datetime.fromisoformat(row["available_at_utc"].replace("Z","+00:00"))
        if available.tzinfo is None or available>=kickoff:continue
        permitted.append(row)
    teams={"home":target["home"],"away":target["away"]}
    result={}
    for role,team in teams.items():
        relevant=[r for r in permitted if team in (r["home"],r["away"])]
        result[role+"_prior_games"]=len(relevant)
        result[role+"_prior_goals_for"]=sum(int(r["ft_home"] if team==r["home"] else r["ft_away"]) for r in relevant)
        result[role+"_prior_goals_against"]=sum(int(r["ft_away"] if team==r["home"] else r["ft_home"]) for r in relevant)
    if set(result)!=FEATURE_ALLOWED or (set(result)&FEATURE_BANNED):
        raise ValueError("TARGET_OR_POSTMATCH_OUTCOME_USED_AS_FEATURE")
    return result

def audit():
    old,new,original_scores=holds()
    total=Counter();legal=Counter();stages=Counter();vintage=Counter()
    by_group=defaultdict(Counter); held_seen=set(); distinct=set()
    source_pins={}
    for filename,(blob,n,kind) in EXPECTED.items():
        rows,sha=read_csv(filename)
        if sha!=blob or len(rows)!=n:raise ValueError("QUARANTINE_SOURCE_PIN_DRIFT:"+filename)
        source_pins[filename]={"git_blob_sha":sha,"row_count":n,"source_kind":kind}
        for r in rows:
            assert_origin(r,kind)
            key=match_key(r)
            if key in distinct:raise ValueError("DUPLICATE_RESEARCH_FIXTURE")
            distinct.add(key)
            if r["season"] not in ("2025-26","2026-27"):raise ValueError("UNEXPECTED_SEASON")
            if date.fromisoformat(r["date"])>CUTOFF:raise ValueError("FUTURE_RESULT_IN_QUARANTINE")
            group=r["league"]+"/"+r["season"]
            total["research_rows"]+=1;legal[kind]+=1
            by_group[group]["research_rows"]+=1
            if key in old:
                total["old_hold_200"]+=1;by_group[group]["old_hold"]+=1;held_seen.add(key)
            if key in new:
                if filename!="cc0_new_485_2526_2627_QUARANTINE_20261113.csv" or kind!=CC0:
                    raise ValueError("HOLD96_SOURCE_MISMATCH")
                if (r["ft_home"],r["ft_away"])!=original_scores[key]:
                    raise ValueError("HOLD96_SCORE_CHANGED")
                total["new_hold_96"]+=1;by_group[group]["new_hold"]+=1;held_seen.add(key)
            if key in old or key in new:continue
            if kind!=CC0:
                total["rights_unclear_not_released"]+=1;by_group[group]["rights_unclear"]+=1
                continue
            total["publisher_CC0_unheld"]+=1
            by_group[group]["publisher_CC0_unheld"]+=1
            stage=recognize_stage(r);stages[stage]+=1
            if r["league"]=="AUT1" and r["season"]=="2025-26" and stage=="conference_playoff":
                total["aut_nonregular_conference_playoff_excluded"]+=1
                by_group[group]["explicit_playoff_excluded"]+=1
                continue
            total["cc0_unheld_normal_stage_research_only"]+=1
            # The existing scored source files contain outcome labels, but lack
            # published_at (when prior score became available), exact kickoff timestamps,
            # and an immutable per-event feature snapshot.
            required=("kickoff_at_utc","available_at_utc","source_observed_at_utc")
            missing=[x for x in required if not r.get(x)]
            if missing:
                total["asof_provenance_missing"]+=1
                by_group[group]["asof_provenance_missing"]+=1
                for field in missing:vintage[field]+=1
            else:
                # This path is explicitly NOT a promotion: still needs independent
                # licence/lineage, identity and temporal split evidence.
                total["asof_fields_present_but_uncertified"]+=1
    if len(distinct)!=2396 or len(held_seen)!=296 or len(old)!=200 or len(new)!=96:
        raise ValueError("EXPECTED_2396_296_HOLDS_COUNT_DRIFT")
    if legal != Counter({CC0:2071,"CCBY_COMPILATION_UPSTREAM_UNCLEAR":322,"THIRD_PARTY_REHOST_UNCLEARED":3}):
        raise ValueError("RIGHTS_SOURCE_DISTRIBUTION_CHANGED")
    if total["publisher_CC0_unheld"]!=1775 or total["aut_nonregular_conference_playoff_excluded"]!=3:
        raise ValueError("NO_REGULAR_LEAGUE_RELEASE_WITHOUT_NEW_AUDIT")
    if total["asof_provenance_missing"]!=1772 or total["rights_unclear_not_released"]!=325:
        raise ValueError("EXPECTED_FULL_ASOF_RIGHTS_QUARANTINE")
    return {
      "status":"NEW_2396_FINAL_296_HOLD_RIGHTS_VINTAGE_GATE_RESEARCH_ONLY_COMPLETE",
      "date_local":"2026-11-14",
      "scope":"Only source rights, exact OLD200+NEW96 holds, playoff stages and point-in-time feature timestamps; no completed match-score crosschecks rerun.",
      "raw_research_rows":2396,
      "source_provenance":dict(legal),
      "exact_holds":{ "prior_ENG3_ENG4":200,"new_ENG5":96,"total":296},
      "publisher_CC0_unheld_source_score_witnessed":1775,
      "ordinary_league_aut_conference_playoff_excluded":3,
      "remaining_CC0_normal_stage_asof_unapproved":1772,
      "asof_timestamp_missing_in_this_subset":total["asof_provenance_missing"],
      "per_required_timestamp_missing":dict(vintage),
      "other_rights_unclear_rows":325,
      "by_league_season":{k:dict(v) for k,v in sorted(by_group.items())},
      "source_blob_unchanged_pins":source_pins,
      "pre_match_feature_contract":{
        "allow":"Only strictly earlier match-day score facts with a certified available_at timestamp before target kickoff, same league and season, for aggregate home/away prior-form features",
        "ban_target_match_ft_ht_xg_as_features":sorted(FEATURE_BANNED),
        "same_day_observations":"EXCLUDE_BY_DEFAULT_WITHOUT_EXACT_TIMES",
        "history_revision_and_publish_time":"MUST_BE_EVIDENCED; today-visible historical scores do not certify historical availability",
        "synthetic_contract_test":"PASS_REQUIRED_BEFORE_ANY_SHADOW_PIPELINE"
      },
      "license_interpretation":{
        "openfootball":"Publisher CC0 dedication confirmed for published dataset; upstream third-party rights and quality not automatically warranted.",
        "football_data":"Comparison witness only; no bulk training import or automated repeats on restricted free site.",
        "ccby322":"Attribution/source lineage and upstream rights not cleared.",
        "swiss3":"Third-party rights not cleared."
      },
      "training_rows_newly_approved":0,
      "new_model_fit_or_predictions_run":0,
      "original_holds_or_2396_rows_changed":False,
      "prior_871_and_904_score_QA_retested":0,
      "main_10_league_M4_SHA_changed":False,
      "next_distinct_step":"Develop pre-kickoff immutable snapshot collector for new fixtures on permitted sources; then prove matched observations available before kickoff and time-ordered shadow validation. No current score-source rechecks."
    }
def selftest():
    old,new,raw=holds()
    assert len(old)==200 and len(new)==96 and not(old&new)
    target={"league":"ENG5","season":"2025-26","date":"2025-11-08","home":"A","away":"B","kickoff_at_utc":"2025-11-08T15:00:00Z"}
    observed=[
       {"league":"ENG5","season":"2025-26","date":"2025-11-05","home":"A","away":"C","ft_home":"2","ft_away":"0","available_at_utc":"2025-11-05T20:00:00Z"},
       {"league":"ENG5","season":"2025-26","date":"2025-11-07","home":"B","away":"D","ft_home":"1","ft_away":"1","available_at_utc":"2025-11-08T16:00:00Z"},
       {"league":"ENG5","season":"2025-26","date":"2025-11-08","home":"A","away":"B","ft_home":"5","ft_away":"0","available_at_utc":"2025-11-08T17:00:00Z"},
       {"league":"ENG5","season":"2025-26","date":"2025-11-10","home":"B","away":"C","ft_home":"3","ft_away":"1","available_at_utc":"2025-11-10T18:00:00Z"}
    ]
    p=historical_form_from_certified_past(target,observed)
    assert p=={"home_prior_games":1,"home_prior_goals_for":2,"home_prior_goals_against":0,"away_prior_games":0,"away_prior_goals_for":0,"away_prior_goals_against":0},p
    try:historical_form_from_certified_past(target,[dict(observed[0],available_at_utc=None)])
    except ValueError:pass
    else:raise AssertionError("missing historical vintage did not fail closed")
    try:historical_form_from_certified_past(target,[dict(observed[0],available_at_utc="2025-11-07T00:00:00")])
    except ValueError:pass
    else:raise AssertionError("naive timestamp did not fail closed")
    print("PASS 296 nonoverlapping held keys, frozen source score PINs, temporal feature contract: target/same-day/future/unpublished blocked")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if a.self_test:selftest()
    if a.run:
        print("FINAL_GATE_START")
        print(json.dumps(audit(),indent=2,ensure_ascii=False))
        print("FINAL_GATE_END")
