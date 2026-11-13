#!/usr/bin/env python3
"""Swiss 2025-26 228-result independent acceptance gate (research-only).

Requires 216 exact RSSSF date/team/score witnesses plus 12 independently
source-cited official match event exceptions. Does NOT confer data rights.
Never archives either provider's full score records or trains any model.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from urllib.request import Request, urlopen

from verify_che1_2526_rsssf_fullseason_once import (
    audit, primary_results, csv_rows, PRIMARY, INDEPENDENT,
    EXPECTED_SHA, WITNESSES
)

EXCEPTIONS = Path("experiments/263/league_expansion/che1_2526_12_official_exception_score_witnesses_20261114.json")

def fetch(url, accept):
    req=Request(url, headers={"User-Agent":"Research-ReadOnly-Swiss-2025-26-QA/1.0 (one-shot)","Accept":accept})
    with urlopen(req,timeout=20) as res:
        data=res.read(3000001)
        if len(data)>3000000: raise ValueError("SOURCE_BYTES_OVER_LIMIT")
    return data

def verify(raw_csv, raw_rsssf, old_witnesses, exceptions):
    if hashlib.sha256(raw_csv).hexdigest() != EXPECTED_SHA:
        raise ValueError("SOURCE_HASH_CHANGED__STOP")
    base=audit(raw_csv,raw_rsssf,old_witnesses)
    if base.get("matched_date_club_score")!=216:
        raise ValueError("RSSSF_MATCH_COUNT_DRIFT")
    if (base.get("score_disagreements"),base.get("unmatched_csv_fixtures"),base.get("unmatched_rsssf_fixtures"))!=(1,11,11):
        raise ValueError("RSSSF_EXCEPTION_SET_CHANGED")
    if base["rsssf_parser"]["abandoned_incomplete_match_scores_ignored"]!=1:
        raise ValueError("ABANDONED_SOURCE_MATCH_NOT_EXCLUDED")
    if base["rsssf_parser"]["duplicate_keys"]!=0:
        raise ValueError("RSSSF_REPLAY_NOT_HANDLED")
    primary,duplicates=primary_results(csv_rows(raw_csv.decode("utf-8-sig")))
    if len(primary)!=228 or duplicates:
        raise ValueError("PRIMARY_SCORE_COVERAGE_FAILED")
    expected_unmatched={(r["date"],r["home"],r["away"]) for r in base["csv_missing_examples"]}
    expected_conflicts={(r["date"],r["home"],r["away"]) for r in base["different_examples"]}
    if len(expected_unmatched)!=11 or len(expected_conflicts)!=1:
        raise ValueError("EXCEPTION_SUMMARY_TRUNCATED")
    exceptional_keys=expected_unmatched|expected_conflicts
    cases=exceptions["exception_facts"]
    if len(cases)!=12:
        raise ValueError("WRONG_OFFICIAL_EXCEPTION_COUNT")
    checked,seen,differences=[],set(),[]
    for item in cases:
        key=(item["date"],item["home"],item["away"])
        if key in seen: raise ValueError("DUPLICATE_EXCEPTION_KEY")
        seen.add(key)
        if key not in exceptional_keys: raise ValueError("SCORE_EXCEPTION_NOT_IN_INDEPENDENT_DIFF_SET")
        score=primary.get(key)
        expected=(item["ft_home"],item["ft_away"])
        if score != expected:
            differences.append({"date":key[0],"home":key[1],"away":key[2],
                                "csv_goals":score,"official_goals":expected,
                                "witness_url":item["source_url"]})
        else:
            checked.append(key)
    if seen!=exceptional_keys:
        raise ValueError("OFFICIAL_EXCEPTION_KEY_COVERAGE_INCOMPLETE")
    complete=(not differences and len(checked)==12 and base["matched_date_club_score"]==216 and
              len(seen)==12 and set(primary)==(
                (set(primary)-expected_unmatched-expected_conflicts) | seen))
    return {
        "status":"FULL_INDEPENDENT_228_FACT_CHECK_PASS" if complete else "FAIL_CLOSED",
        "scope":"CHE1_2025_26_FT_DATE_CLUB_SCORE",
        "main_M4_modified":False, "old_SHA_seals_modified":False,
        "source_primary":"MatchDaySync public 2025/26 228 match CSV",
        "source_csv_sha256":hashlib.sha256(raw_csv).hexdigest(),
        "source_secondary":"RSSSF Switzerland 2025/26 text (contains known typographical/abandoned-match mistakes)",
        "source_secondary_html_sha256":hashlib.sha256(raw_rsssf).hexdigest(),
        "independent_exact_RSSSF_date_team_score":base["matched_date_club_score"],
        "independent_official_exception_date_team_score":len(checked),
        "independent_checked_unique_games":base["matched_date_club_score"]+len(checked),
        "expected_total_league_games":228,
        "official_exception_score_disagreements":len(differences),
        "official_exception_differences":differences[:12],
        "rsssf_discrepancies_handled":{
            "nine_one_day_early_RSSSF":9,
            "one_source_reversed_home_away":1,
            "one_source_one_day_late":1,
            "one_wrong_RSSSF_score":1,
            "abandoned_1_0_ignored_replayed_1_3":1,
        },
        "existing_36_plus_new_evidence": {
            "previous_36_in_rsssf_exact_set":36,
            "new_180_exact_RSSSF":180,
            "new_12_official_exception_matches":len(checked),
            "new_independently_checked_since_previous_36":180+len(checked)
        },
        "raw_match_sources_stored":False, "training_rows_added":0, "public_quarantine_rows_added":0,
        "license_to_rehost_or_train":"NOT_ESTABLISHED",
        "model_integration_status":"NOT_AUTHORIZED",
        "note":"Fixture-score fidelity check only, not the license/admission gate. Keep original provider CSV out of repository."
    }

def selftest():
    # Cheap no-network structural test for immutable exception ledger and expected count.
    x=json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
    entries=x["exception_facts"]
    assert len(entries)==12
    assert len({(e["date"],e["home"],e["away"]) for e in entries})==12
    assert len([e for e in entries if e["cause"]=="DAY_IN_RSSSF_ONE_EARLIER"])==9
    assert len([e for e in entries if e["cause"]=="RSSSF_WRONG_FT_SCORE_2_2"])==1
    assert all(e["source_url"].startswith("https://") for e in entries)
    print("PASS: 12 distinct date/home/away/official-score witness facts pinned")

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--live",action="store_true")
    a=p.parse_args()
    if a.self_test: selftest()
    if a.live:
        from datetime import datetime, timezone
        record={"checked_on_utc":datetime.now(timezone.utc).isoformat(),
                "status":"NOT_VERIFIED","new_training_rows":0,"old_models_modified":False}
        try:
            import json
            old=json.loads(Path(WITNESSES).read_text(encoding="utf-8"))["checks"]
            case=json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
            source=fetch(PRIMARY,"text/csv")
            other=fetch(INDEPENDENT,"text/html")
            record.update(verify(source,other,old,case))
        except Exception as exc:
            record["status"]="FAIL_CLOSED_EXCEPTION"
            record["failure_class"]=type(exc).__name__
        print("COMBINED_SWISS_228_START")
        print(json.dumps(record,ensure_ascii=False,indent=2))
        print("COMBINED_SWISS_228_END")
