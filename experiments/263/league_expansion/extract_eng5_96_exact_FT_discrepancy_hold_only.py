#!/usr/bin/env python3
"""Create exact research HOLD keys for ONLY 96 divergent 2025/26 National League
CC0 source records, after 871 successful six-league facts already frozen.

This DOES NOT replay the previous six-league score audit. One EC source fetch
is pinned to its previously checked SHA only to identify all 96 exact original
source row identities requiring hold. No correction or remote score exported;
held entries comprise user's existing CC0-research fields ONLY.
"""
from __future__ import annotations
import argparse,hashlib,json
from datetime import datetime,timezone
import audit_6_leagues_967_scores_one_batch_20261114 as base
from reconcile_six_leagues_228_exceptions_no_repeat_20261114 import reparse_historical
from prepare_2396_provenance_rights_quality_gate_20261114 import EXPECTED,read_csv
GROUP="ENG5/2025-26"
EC_SHA="2372229d616a57f9df3d9a401cd942df8e1909ba67017b3793c6aceaf0becf76"
ORIGINAL_SOURCE="cc0_new_485_2526_2627_QUARANTINE_20261113.csv"
def calculate(raw):
    actual_hash=hashlib.sha256(raw).hexdigest()
    if actual_hash!=EC_SHA:raise ValueError("SECOND_SOURCE_SHA_DRIFT_STOP")
    data,clubs,_=base.pinned_primary()
    initial=data[GROUP]
    if len(initial)!=296:raise ValueError("ENG5_SOURCE_296_CHANGED")
    external,diagnostics=reparse_historical(raw,GROUP,clubs[GROUP])
    selected=[]
    valid=0
    for (home,away),(day,ft) in sorted(initial.items(),key=lambda x:(x[1][0],x[0])):
        other=external.get((home,away))
        if not other:raise ValueError("SECONDARY_PAIR_MISSING_AFTER_ALIAS_RECONCILIATION")
        od,ofs=other
        if day==od and ft==ofs:
            valid+=1
            continue
        # Do not publish the external competing FT; it stays at the upstream URL.
        selected.append({"league":"ENG5","season":"2025-26",
           "original_date":day.isoformat(),"home":home,"away":away,
           "original_home_goals":ft[0],"original_away_goals":ft[1],
           "source_file":ORIGINAL_SOURCE,
           "issue":"SECOND_INDEPENDENT_SCORE_OR_DATE_DISAGREES",
           "train_gate":"HOLD_PENDING_THIRD_SOURCE_VERIFICATION",
           "source_sha256":EC_SHA})
    if len(selected)!=96 or valid!=200:
        raise ValueError("EXPECTED_96_HOLDS_200_PASS_DRIFT")
    keys=set((r["original_date"],r["home"],r["away"]) for r in selected)
    if len(keys)!=96:raise ValueError("DUPLICATE_HOLD_KEY")
    originals,source_git_hash=read_csv(ORIGINAL_SOURCE)
    expected_blob,count,_=EXPECTED[ORIGINAL_SOURCE]
    if source_git_hash!=expected_blob or len(originals)!=count:
        raise ValueError("SOURCE_BLOB_CHANGED_STOP")
    actual={(r["date"],r["home"],r["away"]):(int(r["ft_home"]),int(r["ft_away"]))
            for r in originals if r["league"]=="ENG5" and r["season"]=="2025-26"}
    if len(actual)!=296:raise ValueError("ORIGINAL_CC0_296_DRIFT")
    if any(actual.get((x["original_date"],x["home"],x["away"]))!=
             (x["original_home_goals"],x["original_away_goals"]) for x in selected):
        raise ValueError("HOLD_MUST_EQUAL_SOURCE_MATCH_RECORD")
    checksum=hashlib.sha256("\n".join(
        "|".join((v["original_date"],v["home"],v["away"])) for v in selected
    ).encode()).hexdigest()
    return {"status":"EXACT_96_NATIONAL_LEAGUE_SCORE_OR_DATE_DISCREPANCY_KEYS_ON_HOLD",
      "checked_at_utc":datetime.now(timezone.utc).isoformat(),
      "existing_296_original_CC0_result_candidates":296,
      "prior_200_second_source_FT_date_passes_not_retested":200,
      "hold_count":len(selected),
      "source_research_original_blob_sha":expected_blob,
      "pinned_external_fact_source_SHA256":EC_SHA,
      "hold_fixture_keys_sha256":checksum,
      "held_original_research_match_keys":selected,
      "external_FT_scores_rehosted":False,
      "source_research_file_mutated":False,
      "old_200_ENG3_ENG4_HOLD_modified":False,
      "training_rows_admitted":0,
      "production_main_M4_SHA_changed":False}

def selftest():
    data,clubs,files=base.pinned_primary()
    assert len(data[GROUP])==296
    assert len(clubs[GROUP])==24
    assert EXPECTED[ORIGINAL_SOURCE][1]==485
    print("PASS exact frozen ENG5 296 and safe no-third-party-score HOLD schema")

if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--self-test",action="store_true");a.add_argument("--live",action="store_true")
    args=a.parse_args()
    if args.self_test:selftest()
    if args.live:
        try:out=calculate(base.fetch(base.URLS[GROUP]))
        except Exception as e:
            out={"status":"FAIL_CLOSED_HOLD_KEYS_NOT_WRITTEN",
                 "error_class":type(e).__name__,
                 "error_details":str(e)[:220] if isinstance(e,ValueError) else "source access blocked",
                 "training_rows_admitted":0}
        print("ENG5_HOLD_96_START")
        print(json.dumps(out,ensure_ascii=False,indent=2))
        print("ENG5_HOLD_96_END")
