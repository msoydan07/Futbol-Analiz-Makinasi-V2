#!/usr/bin/env python3
"""The 2396-source-rows licensing vs quality ledger: research-only, offline.

NOT a revalidation of the completed 178 / 22 / 472 / 420 / 50
score checks, NOT a training dataset, not an import into M4.
Publisher licenses alone never certify source accuracy or rights of third
parties. For any future experiments both source and score/as-of gates must PASS.
"""
from __future__ import annotations
import csv,hashlib,io,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path("experiments/263/league_expansion")
EXPECTED={
 "training_2025_26_cc0_scored_QUARANTINE.csv":("82593a87cec5aa9deea3802ea31b86dd4ac8573c",1249,"PUBLISHER_CC0_CLAIM"),
 "cc0_new_485_2526_2627_QUARANTINE_20261113.csv":("2582e3ffa6e200b74704702dccc01ca19ad4750e",485,"PUBLISHER_CC0_CLAIM"),
 "cc0_aut1_2026_27_42_QUARANTINE_20261113.csv":("a404b3a395b32c42ac4e6cfef724bdebd3cbecb9",42,"PUBLISHER_CC0_CLAIM"),
 "score_shape_recovery_295_2526_QUARANTINE_20261113.csv":("46071b306d6f73be71d27b0a6c5f4480630b73a0",295,"PUBLISHER_CC0_CLAIM"),
 "eng3_eng4_2026_27_322_CCBY_QUARANTINE_20261113.csv":("22b909a504254bfd3c9013f27fdbf2736ffbf746",322,"CCBY_COMPILATION_UPSTREAM_UNCLEAR"),
 "che1_2026_27_oct10_3_match_score_facts_QUARANTINE_20261114.csv":("7098dd60bde56f8dbcd5b16930308028f332b821",3,"THIRD_PARTY_REHOST_UNCLEARED"),
}
HOLD="eng3_eng4_2025_26_200_exact_legacy_fixture_training_HOLD_20261114.csv"
PUBLISHERS={
 "PUBLISHER_CC0_CLAIM":{"github.com/openfootball/football.json","github.com/openfootball/england","github.com/openfootball/austria"},
 "CCBY_COMPILATION_UPSTREAM_UNCLEAR":{"github.com/seanelvidge/England-football-results"},
 "THIRD_PARTY_REHOST_UNCLEARED":{"uniquescores.com"},
}
DOCS={
 "openfootball_json":"https://github.com/openfootball/football.json/blob/master/README.md",
 "openfootball_england":"https://github.com/openfootball/england/blob/master/LICENSE.md",
 "openfootball_austria":"https://github.com/openfootball/austria/blob/master/LICENSE.md",
 "sean_terms":"https://github.com/seanelvidge/England-football-results/blob/main/LICENCE.md",
}
def blob_sha(content):
    return hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest()
def read_csv(name):
    binary=(ROOT/name).read_bytes()
    decoded=binary.decode("utf-8-sig")
    rows=list(csv.DictReader(io.StringIO(decoded,newline="")))
    return rows,blob_sha(binary)
def match_key(r):
    return tuple(r[k] for k in ("league","season","date","home","away"))
def assert_origin(row,group):
    p=urlparse(row["source_uri"])
    if p.scheme!="https":raise ValueError("UNSAFE_SOURCE_URL")
    allow=PUBLISHERS[group]
    joined=(p.netloc+p.path).lower()
    if not any(joined.startswith(x.lower()+"/") for x in allow):
        raise ValueError("UNEXPECTED_ORIGIN:"+row["source_uri"][:80])
def inspect():
    hold,hold_sha=read_csv(HOLD)
    if len(hold)!=200:raise ValueError("HOLD_SIZE_CHANGED")
    by_source={}; all_keys=set(); hold_map={}
    for r in hold:
        k=match_key(r)
        if k in hold_map:raise ValueError("DUPLICATE_HOLD")
        hold_map[k]=r
    license_counts=Counter(); qa_counts=Counter(); divisions={}
    total=0;excluded=0
    for filename,(expected_sha,expected_count,tag) in EXPECTED.items():
        rows,sha=read_csv(filename)
        if sha!=expected_sha or len(rows)!=expected_count:
            raise ValueError("SOURCE_PIN_MISMATCH:"+filename)
        held=0;by_season=Counter(); by_reason=Counter()
        for r in rows:
            assert_origin(r,tag)
            k=match_key(r)
            if k in all_keys:raise ValueError("DUPLICATE_FIXTURE_KEY")
            all_keys.add(k)
            if r["season"] not in ("2025-26","2026-27"):raise ValueError("UNEXPECTED_SEASON")
            by_season[r["league"]+"/"+r["season"]]+=1
            if k in hold_map:
                record=hold_map[k]
                if record["existing_research_source_file"]!=filename:
                    raise ValueError("TRAINING_HOLD_SOURCE_NOT_EXACT")
                if record["existing_source_blob_sha"]!=sha:
                    raise ValueError("TRAINING_HOLD_BLOB_DRIFT")
                held+=1;excluded+=1
                by_reason[record["quality_hold_reason"]]+=1
            total+=1
        license_counts[tag]+=len(rows)
        qa_counts["EXPLICIT_LEGACY_FT_OR_IDENTITY_HOLD"]+=held
        qa_counts["NOT_CLEARED_BUT_NOT_IN_EXPLICIT_HOLD"]+=len(rows)-held
        by_source[filename]={"published_license_provenance":tag,
            "total_scored_candidate_rows":len(rows),
            "frozen_sha":sha,
            "hard_hold_rows":held,
            "other_rows_still_need_quality_and_rights_gates":len(rows)-held,
            "hold_types":dict(by_reason),
            "by_league_season":dict(sorted(by_season.items())),
            "training_admitted":0}
    if len(all_keys)!=2396 or total!=2396 or excluded!=200:
        raise ValueError("ROOT_TOTAL_OR_HOLD_DRIFT")
    if not set(hold_map)<=all_keys:
        raise ValueError("HOLD_ITEM_NOT_IN_SCOPED_RESEARCH_SOURCE")
    if license_counts != Counter({"PUBLISHER_CC0_CLAIM":2071,
        "CCBY_COMPILATION_UPSTREAM_UNCLEAR":322,
        "THIRD_PARTY_REHOST_UNCLEARED":3}):
        raise ValueError("LICENCE_PROVENANCE_GROUP_COUNTS_CHANGED")
    if by_source[EXPECTED.keys().__iter__().__next__()]["hard_hold_rows"]!=186:
        raise ValueError("FIRST_SOURCE_HOLD_COUNT_CHANGED")
    if by_source["score_shape_recovery_295_2526_QUARANTINE_20261113.csv"]["hard_hold_rows"]!=14:
        raise ValueError("SCORE_SHAPE_HOLD_COUNT_CHANGED")
    return {"checked_at_utc":datetime.now(timezone.utc).isoformat(),
        "scope":"RESEARCH_ONLY_2396_MATCH_SOURCE_RIGHTS_AND_QUALITY",
        "source_pins_and_quality":by_source,
        "published_license_provenance_counts":dict(license_counts),
        "quality":dict(qa_counts),
        "CC0_declared_without_hard_hold":2071-200,
        "IMPORTANT":"Publisher CC0 claim is NOT clearance of third-party rights or score validation. 1871 are not trainable yet.",
        "training_approved_rows":0,
        "training_exported_rows":0,"live_M4_or_predictions_changed":False,
        "source_rights_references":DOCS,
        "conditions_before_a_future_shadow_training_run":[
          "Verify source rights for intended model-training use including upstream rights and provenance.",
          "Independent fixture and full-time score QA for the individual row (not aggregate-only season totals).",
          "Reject all 200 exact hold keys until independently corrected and a lawful source is identified.",
          "Require immutable point-in-time feature provenance; only past fixture facts, never target-match postgame xG.",
          "Use time-ordered train/calibration/test splits and report BTTS/O2.5/1X2 calibration and losses.",
          "Do not alter main branch, production M4, old SHA seals or signed predictions."
        ]}
def synthetic():
    assert blob_sha(b"test")==hashlib.sha1(b"blob 4\0test").hexdigest()
    x={"league":"ENG3","season":"2025-26","date":"2025-08-01","home":"A","away":"B"}
    assert match_key(x)==("ENG3","2025-26","2025-08-01","A","B")
    assert_origin({"source_uri":"https://github.com/openfootball/football.json/blob/master/2025-26/en.3.json"},"PUBLISHER_CC0_CLAIM")
    try:
        assert_origin({"source_uri":"https://github.com/other/unrelated/blob/x"},"PUBLISHER_CC0_CLAIM")
        raise AssertionError("unknown provider unexpectedly passed")
    except ValueError:pass
    print("SYNTHETIC_PASS licence whitelist, strict match key and Git blob pin")
if __name__=="__main__":
    import argparse
    arg=argparse.ArgumentParser()
    arg.add_argument("--self-test",action="store_true")
    arg.add_argument("--run",action="store_true")
    a=arg.parse_args()
    if a.self_test:synthetic()
    if a.run:
        print("PROVENANCE_QA_START")
        print(json.dumps(inspect(),ensure_ascii=False,indent=2))
        print("PROVENANCE_QA_END")
