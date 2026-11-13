#!/usr/bin/env python3
"""Exactly eight 2025/26 Plymouth Argyle alias exceptions from prior 170/178 QA.

Not a replay of the 170 already-checked fixture scores. Pin E2.csv hash,
read it once into memory, match 8 frozen issue keys and stop. No training.
"""
import json,hashlib
from datetime import datetime,timezone
from eng3_eng4_2526_single_batch_external_score_audit import (
 load_ledger,previously_confirmed,key,match_score,csv_source,get,URLS
)
EXPECTED_E2_SHA="4c96eff8a2f20c5e26015af8609c4f90478ff055f58ab6e137cc3445bf4c67ee"

def issues_eight():
    conflicts,old_only=load_ledger()
    target=[r for r in conflicts if r["league"]=="ENG3" and
            "Plymouth Argyle" in (r["home"],r["away"])]
    if len(target)!=8:raise ValueError("EIGHT_PLYMOUTH_SOURCE_DRIFT")
    return target

def alias_key(row):
    home=row["home"].replace("Plymouth Argyle","Plymouth")
    away=row["away"].replace("Plymouth Argyle","Plymouth")
    return key(row["league"],row["date"],home,away)

def verify(raw):
    actual_sha=hashlib.sha256(raw).hexdigest()
    if actual_sha!=EXPECTED_E2_SHA:raise ValueError("E2_SHA_CHANGED_STOP")
    source,diag=csv_source(raw,"ENG3")
    if diag["scored_unique"]!=552 or diag["zero_zero_games"]!=33 or diag["clubs_normalized"]!=24:
        raise ValueError("E2_SOURCE_COVERAGE_DRIFT")
    prior=previously_confirmed()
    matches=[];miss=[];wrong=[];already=0
    for r in issues_eight():
        k=alias_key(r)
        ft=source.get(k)
        expected=match_score(r["sean_score"])
        if ft is None:
            miss.append({"date":r["date"],"home":r["home"],"away":r["away"]})
        elif ft!=expected:
            wrong.append({"date":r["date"],"home":r["home"],"away":r["away"],
                          "third_facts_ft":list(ft),"alternate_ft":list(expected)})
        else:
            matches.append(k)
        original_key=key(r["league"],r["date"],r["home"],r["away"])
        if original_key in prior:
            if prior[original_key]!=expected:raise ValueError("EARLIER_EDITORIAL_WITNESS_CONFLICT")
            already+=1
    if already!=1:raise ValueError("PREVIOUS_25_PLYMOUTH_OVERLAP_DRIFT")
    complete=len(matches)==8 and not miss and not wrong
    return {
     "scope":"ENG3_2025_26_ONLY_8_UNMATCHED_PLYMOUTH_ALIAS_ISSUES",
     "status":"ALL_8_EXTERNAL_SCORE_FACTS_MATCH_ALTERNATE" if complete else "FAIL_CLOSED",
     "source":URLS["ENG3"],"source_sha256":actual_sha,
     "original_external_score_rows_read_once":diag["scored_unique"],
     "frozen_conflicts_targeted":8, "same_90min_ft_score":len(matches),
     "not_found":len(miss),"other_score":len(wrong),
     "previous_editorial_checked_already":already,
     "new_external_matches_beyond_prior_25":len(matches)-already,
     "missing_examples":miss,"disagreement_examples":wrong,
     "previous_successful_170_rows_rechecked":0,
     "full_CSV_rehosted":False,"research_quarantine_added":0,"trainable_rows_added":0,
     "production_main_m4_seals_modified":False
    }

def selftest():
    assert len(issues_eight())==8
    assert len(previously_confirmed())==25
    for r in issues_eight():
        changed=alias_key(r)
        assert "plymouth" in changed[2:] and "plymouthargyle" not in changed[2:]
    print("PASS 8 isolated Plymouth aliases, 25 previous editorial facts untouched")

if __name__=="__main__":
    import argparse
    cli=argparse.ArgumentParser()
    cli.add_argument("--self-test",action="store_true")
    cli.add_argument("--live",action="store_true")
    opts=cli.parse_args()
    if opts.self_test:selftest()
    if opts.live:
        report={"status":"NOT_VERIFIED","trainable_rows_added":0}
        try:
            report.update(verify(get(URLS["ENG3"])))
        except Exception as exc:
            report["status"]="FAIL_CLOSED_SOURCE_OR_COMPARATOR"
            report["failure_class"]=type(exc).__name__
            report["http_status"]=getattr(exc,"code",None)
            report["error_detail"]=str(exc)[:130] if isinstance(exc,ValueError) else "source inaccessible"
        report["checked_at_utc"]=datetime.now(timezone.utc).isoformat()
        print("PLYMOUTH_EIGHT_START")
        print(json.dumps(report,indent=2,ensure_ascii=False))
        print("PLYMOUTH_EIGHT_END")
