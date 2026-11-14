#!/usr/bin/env python3
"""Targeted research-only 48 Serie B 2025/26 date-only exceptions, NOT the
261 prior exact date+FT matches. External full 380 source is SHA pinned and
used once in memory solely to locate 48 previously unmatched date keys.
No changes to CC0 input fixtures; date overlay requires independent proof.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from verify_ita2_2526_309_second_source_standings_once import (
    primary,secondary,get,URL,standings)
PINNED_SHA="47c7834f1ce997ed406975ee290cb0eda4d88a343cbacb3f4c3f1f2c86515934"
PUBLISHER_DATE_WITNESSES=[
 "https://www.legab.it/news/il-programma-gare-dalla-30a-alla-32a-giornata",
 "https://fbref.com/en/comps/18/2025-2026/schedule/2025-2026-Serie-B-Scores-and-Fixtures"
]
def run(raw):
    if hashlib.sha256(raw).hexdigest()!=PINNED_SHA:
        raise ValueError("SECOND_SOURCE_HASH_CHANGED_STOP_NO_RETEST")
    old,origin=primary()
    external,diag=secondary(raw)
    if diag["rows"]!=380 or diag["scored_unique"]!=380 or diag["exclusions"]:
        raise ValueError("SECONDARY_380_SOURCE_DRIFT")
    residual={k:v for k,v in old.items() if k not in external}
    if len(residual)!=48:raise ValueError("OLD_UNMATCHED_48_CARDINALITY_CHANGED")
    by_pair=defaultdict(list)
    for (day,h,a),ft in external.items():
        by_pair[(h,a)].append((day,ft))
    comparable=0;score_same=0;score_differ=0;unmatched=0
    shifts=Counter();score_conflicts=[];long_shift=[];notfound=[]
    zeros=0;zero_agree=0
    for (day,h,a),original_ft in sorted(residual.items()):
        hits=by_pair.get((h,a),[])
        if len(hits)!=1:
            unmatched+=1
            notfound.append({"original_day":day,"home":h,"away":a,"same_home_away_in_external":len(hits)})
            continue
        comparable+=1
        actual_day,actual_ft=hits[0]
        delta=(date.fromisoformat(actual_day)-date.fromisoformat(day)).days
        shifts[str(delta)]+=1
        zeros+=int(original_ft==(0,0))
        zero_agree+=int(original_ft==(0,0) and original_ft==actual_ft)
        if original_ft==actual_ft:score_same+=1
        else:
            score_differ+=1
            score_conflicts.append({"original_date":day,"independent_date":actual_day,
                                    "home":h,"away":a,"original_ft":list(original_ft),
                                    "independent_ft":list(actual_ft)})
        if abs(delta)>3:
            long_shift.append({"original_date":day,"independent_date":actual_day,
                               "home":h,"away":a,"date_delta_days":delta,
                               "same_fulltime_score":original_ft==actual_ft})
    final={"checked_utc":datetime.now(timezone.utc).isoformat(),
      "scope":"ONLY_48_2025_26_ITA2_ORIGINAL_DATE_UNMATCHED_FROM_PRIOR_309",
      "status":"48_OF_48_HOME_AWAY_FT_FACTS_EQUAL_DATES_DIFFER"
                if comparable==48 and score_same==48 and not score_conflicts
                else "FAIL_CLOSED_REMAINING_SCORE_OR_IDENTITY_ERROR",
      "original_309_rows":309,
      "prior_successful_exact_date_and_score_matches_NOT_RECHECKED":261,
      "targeted_date_exception_count":48,
      "same_home_away_FT_score_equal_after_pinned_date_reconcile":score_same,
      "same_home_away_FT_score_conflict":score_differ,
      "external_matching_home_away_fixture_not_found_or_nonunique":unmatched,
      "day_shift_distribution":dict(sorted(shifts.items(),key=lambda x:int(x[0]))),
      "date_shift_within_3_days":sum(int(n) for shift,n in shifts.items() if abs(int(shift))<=3),
      "date_shift_longer_than_3_days":len(long_shift),
      "long_shift_facts":long_shift,
      "score_conflict_examples":score_conflicts[:10],
      "unmatched_pair_examples":notfound[:10],
      "historical_0_0_in_residual":zeros,
      "historical_0_0_same_as_independent_score":zero_agree,
      "external_csv_SHA256":PINNED_SHA,
      "observed_source_date_vs_original_is_separate_quality_gate":True,
      "date_adjudication_with_official_kickoff_schedule":"STILL_REQUIRES_PROOF_FOR_ALL_48",
      "date_witness_candidates":PUBLISHER_DATE_WITNESSES,
      "external_CSV_not_rehosted":True,
      "new_accepted_training_rows":0,"main_M4_production_SHA_modified":False}
    return final

def selftest():
    old,_=primary()
    assert len(old)==309
    assert len(set((h,a) for day,h,a in old))==309
    assert (date(2026,2,15)-date(2026,2,14)).days==1
    assert (date(2026,3,18)-date(2026,3,17)).days==1
    print("PASS 309 immutable source keys, focused date shifts, no rewrite of prior 261")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true")
    opt=p.parse_args()
    if opt.self_test:selftest()
    if opt.run:
        try:result=run(get())
        except Exception as exc:
            result={"status":"FAIL_CLOSED_SOURCE_OR_VALIDATION",
                    "error_class":type(exc).__name__,
                    "error_reason":str(exc)[:200] if isinstance(exc,ValueError) else "provider blocked",
                    "new_accepted_training_rows":0}
        print("ITA48_DATE_START")
        print(json.dumps(result,indent=2,ensure_ascii=False))
        print("ITA48_DATE_END")
