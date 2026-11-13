#!/usr/bin/env python3
"""Exactly 472 2025/26 ENG3 ENG4 previously absent home/away pairs — offline QA.

This deliberately does NOT fetch E2/E3 or another third-party fixture feed:
their free CSV download policy is limited to personal/academic use and does
not grant unrestricted AI model training or heavy automated retrieval.

The 178 already-proven wrong legacy scores and 22 misdated legacy identities
are NOT revalidated here. Training/rehosting remain prohibited by default.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import csv
from hashlib import sha1, sha256
import json
from pathlib import Path
import re
import unicodedata
from datetime import date,datetime,timezone

ROOT=Path("experiments/263/league_expansion")
PINS={
 "eng3_eng4_2025_26_1104_ALTERNATIVE_NONADDITIVE_20261113.csv":"320c28af572afd4f2557698d54a375011ca869ff",
 "training_2025_26_cc0_scored_QUARANTINE.csv":"82593a87cec5aa9deea3802ea31b86dd4ac8573c",
 "score_shape_recovery_295_2526_QUARANTINE_20261113.csv":"46071b306d6f73be71d27b0a6c5f4480630b73a0",
}
EXPECTED_TOTAL={"ENG3":(552,1452,33,196,13,536),"ENG4":(552,1423,36,276,20,699)}
EXPECTED_ALT_SOURCE_BLOB="a27f04e87e1b82718f6c487964f7de2def5a2043"
EXPECTED_RIGHTS_NOTICE="CC_BY4_SEAN_ORIGINAL_ONLY_UPSTREAM_RIGHTS_PENDING"
EXPECTED_STATUS="ALTERNATE_CANDIDATE_NOT_ADDITIVE_NOT_TRAINING"

def blob_sha(payload:bytes)->str:
    return sha1(b"blob "+str(len(payload)).encode()+b"\0"+payload).hexdigest()

def rows(filename):
    p=ROOT/filename
    raw=p.read_bytes()
    if blob_sha(raw)!=PINS[filename]:
        raise ValueError("FILE_BLOB_CHANGED_STOP:"+filename)
    with p.open(encoding="utf-8",newline="") as handle:
        data=list(csv.DictReader(handle))
    return data,sha256(raw).hexdigest()

def canonical(name):
    x=unicodedata.normalize("NFKD",str(name).casefold())
    x="".join(c for c in x if not unicodedata.combining(c))
    x=re.sub(r"\b(?:fc|afc)\b"," ",x)
    x=re.sub(r"\s+(?:city|town|united|rovers|wanderers|county|athletic|stanley|alexandra|albion)$","",x.strip())
    return re.sub(r"[^a-z0-9]","",x)

def fixture(r):
    return (r["league"],canonical(r["home"]),canonical(r["away"]))

def strictdate(value):
    if not re.fullmatch(r"20\d\d-\d\d-\d\d",value or ""):
        raise ValueError("NOT_ISO_DATE")
    d=date.fromisoformat(value)
    if not(date(2025,7,1)<=d<=date(2026,6,30)):
        raise ValueError("OUT_OF_SEASON")
    return d

def goals(h,a):
    if not re.fullmatch(r"\d{1,2}",str(h)) or not re.fullmatch(r"\d{1,2}",str(a)):
        raise ValueError("MISSING_FT")
    h,a=int(h),int(a)
    if h>30 or a>30:raise ValueError("INVALID_FT_GOALS")
    return h,a

def run():
    alt,h_alt=rows("eng3_eng4_2025_26_1104_ALTERNATIVE_NONADDITIVE_20261113.csv")
    original1,h_leg1=rows("training_2025_26_cc0_scored_QUARANTINE.csv")
    original2,h_leg2=rows("score_shape_recovery_295_2526_QUARANTINE_20261113.csv")
    existing=[r for r in original1+original2
              if r.get("league") in ("ENG3","ENG4") and r.get("season")=="2025-26"]
    if len(alt)!=1104 or len(existing)!=632:
        raise ValueError("INPUT_RECORD_COUNT_DRIFT")
    legacy={}
    for r in existing:
        strictdate(r["date"]);goals(r["ft_home"],r["ft_away"])
        k=fixture(r)
        if k in legacy:raise ValueError("DUPLICATE_LEGACY_PAIR")
        legacy[k]=r
    current={}
    for r in alt:
        if r["league"] not in ("ENG3","ENG4") or r["season"]!="2025-26":
            raise ValueError("UNEXPECTED_SEASON_OR_LEAGUE")
        strictdate(r["date"]);goals(r["sean_home_goals"],r["sean_away_goals"])
        if canonical(r["home"])==canonical(r["away"]):raise ValueError("SAME_TEAM")
        if r["source_sha"]!=EXPECTED_ALT_SOURCE_BLOB:
            raise ValueError("SEAN_ORIGINAL_PROVENANCE_CHANGED")
        if r["license_notice"]!=EXPECTED_RIGHTS_NOTICE or r["research_status"]!=EXPECTED_STATUS:
            raise ValueError("RIGHTS_OR_QUARANTINE_LABEL_CHANGED")
        k=fixture(r)
        if k in current:raise ValueError("DUPLICATE_ALTERNATE_PAIR")
        current[k]=r
    if set(legacy)-set(current):
        raise ValueError("PRIOR_PAIR_MISSING_FROM_FULL_SEASON")
    additional=[r for k,r in current.items() if k not in legacy]
    reused=[r for k,r in current.items() if k in legacy]
    shifted=sum(current[k]["date"]!=legacy[k]["date"] for k in legacy)
    if len(additional)!=472 or len(reused)!=632 or shifted!=22:
        raise ValueError("NO_REPEAT_NOVEL_PAIR_COUNT_DRIFT")
    if any(r["identity_join_status"]!="SEAN_ONLY_NO_OLD_ID" for r in additional):
        raise ValueError("NOVEL_ROW_NOT_MARKED_SEAN_ONLY")

    leagues={};all_novel_keys=set()
    for league in ("ENG3","ENG4"):
        season=[r for r in alt if r["league"]==league]
        novel=[r for r in additional if r["league"]==league]
        home=Counter();away=Counter();identities=set();months=Counter()
        for r in season:
            h,a=goals(r["sean_home_goals"],r["sean_away_goals"])
            home[canonical(r["home"])]+=1
            away[canonical(r["away"])]+=1
            identities.add(canonical(r["home"]));identities.add(canonical(r["away"]))
        if len(identities)!=24 or len(home)!=24 or len(away)!=24:
            raise ValueError("CLUB_CANONICALIZATION_COLLISION_OR_MISSING")
        if any(home[k]!=23 or away[k]!=23 for k in identities):
            raise ValueError("NOT_23_HOME_AND_AWAY_FOR_EACH_CLUB")
        ft_total=sum(sum(goals(r["sean_home_goals"],r["sean_away_goals"])) for r in season)
        zeros=sum(goals(r["sean_home_goals"],r["sean_away_goals"])==(0,0) for r in season)
        nzeros=sum(goals(r["sean_home_goals"],r["sean_away_goals"])==(0,0) for r in novel)
        ng=sum(sum(goals(r["sean_home_goals"],r["sean_away_goals"])) for r in novel)
        for r in novel:
            months[r["date"][:7]]+=1
            all_novel_keys.add(fixture(r))
        expected=EXPECTED_TOTAL[league]
        got=(len(season),ft_total,zeros,len(novel),nzeros,ng)
        if got!=expected:raise ValueError("FULL_SEASON_TEAM_OR_NOVEL_SCORE_CHECKSUM_FAILED:"+str((league,got,expected)))
        leagues[league]={
            "full_alternate_season":{"fixtures":len(season),"clubs":24,"each_club_home":23,
                                     "each_club_away":23,"total_goals":ft_total,"zero_zero":zeros},
            "new_distinct_pairs":{"count":len(novel),"goals":ng,"zero_zero":nzeros,
                                  "month_distribution":dict(sorted(months.items()))},
            "external_independent_match_by_match_FT_confirmation_for_new_pairs":0,
            "trainable_rows":0
        }
    if len(all_novel_keys)!=472:raise ValueError("DUPLICATED_NOVEL_PAIRS")
    record={
        "checked_at_utc":datetime.now(timezone.utc).isoformat(),
        "scope":"ENG3_ENG4_2025_26_472_NEW_HOME_AWAY_PAIRS_ONLY",
        "gate":"OFFLINE_SOURCE_SHAPE_COMPLETE__INDEPENDENT_FT_AND_RIGHTS_BLOCKED",
        "pinned_input_git_blob_sha":PINS,
        "pinned_input_file_sha256":{
            "sean_full_nonadditive":h_alt,
            "legacy_1249":h_leg1,"legacy_recovered_295":h_leg2
        },
        "old_178_independent_score_conflicts_rechecked":0,
        "old_22_misdated_fixtures_rechecked":0,
        "old_pairs_reconciled_count_from_frozen_sources":632,
        "new_unique_home_away_pair_facts":len(additional),
        "source_rows_copied_to_public_repo":0,
        "new_training_rows":0,
        "third_party_rights":"SEAN_ORIGINAL_CONTRIBUTIONS_CC_BY4; UPSTREAM_SOURCE_RIGHTS_RESERVED",
        "football_data_free_csv_policy":"PERSONAL_ACADEMIC; NO_UNRESTRICTED_AI_MODEL_TRAINING_PERMISSION",
        "independent_factual_score_source_for_472":"NOT_BATCH_VERIFIED",
        "right_to_use_472_in_model_training":"NOT_CLEARED",
        "full_season_integrity":leagues,
        "existing_research_quarantine_count_unchanged":2396,
        "production_m4_and_10_leagues_unchanged":True,
        "next":"No additional score search on 178/22. 472 already nonadditive; obtain legitimate independently usable score source or grant for model training, then compare its FT facts and temporal leakage properties in one controlled holdout before any data promotion."
    }
    return record

def selftest():
    assert canonical("Peterborough United")=="peterborough"
    assert canonical("FC Peterborough United")=="peterborough"
    assert canonical("Bristol Rovers")=="bristol"
    assert canonical("AFC Wimbledon")=="wimbledon"
    assert canonical("Milton Keynes Dons")=="miltonkeynesdons"
    assert canonical("Plymouth Argyle")=="plymouthargyle"
    assert goals("0","0")==(0,0)
    assert strictdate("2025-11-15")==date(2025,11,15)
    try:
        strictdate("2024-11-15")
        raise AssertionError("out-of-season date accepted")
    except ValueError:
        pass
    print("SELFTEST_PASS offline 472 canonical/season-score-zero/rights and uniqueness primitives")

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--audit",action="store_true")
    args=parser.parse_args()
    if args.self_test:selftest()
    if args.audit:
        print("ENG472_AUDIT_START")
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        print("ENG472_AUDIT_END")
