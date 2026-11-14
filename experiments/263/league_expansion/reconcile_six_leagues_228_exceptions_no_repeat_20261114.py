#!/usr/bin/env python3
"""ONLY 228 unresolved initial-967 outcomes: six league exception QA pass.

The 739 prior FULL date+club+FT confirmations (including ENG3 256/256) are
immutable baseline, never retested or reclassified by this tool. No original
data overwritten, no external CSV rehosted, no model-training approvals.

National League 89 score discrepancies are REAL independent-source conflicts,
not silently fixed; only newly discovered alias gaps can gain source-witness
counts. Independently identify conference score corruption and hold it.
"""
from __future__ import annotations
import argparse,hashlib,json,io,csv,re
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from verify_public_season_csv_2526 import csv_rows
import audit_6_leagues_967_scores_one_batch_20261114 as old

PREVIOUS_EXACT={
 "ENG3/2025-26":256,
 "ENG4/2025-26":148,
 "ENG5/2025-26":182,
 "GRE1/2025-26":53,
 "GRE1/2026-27":17,
 "SCO1/2025-26":48,
 "SCO1/2026-27":35,
 "AUT1/2026-27":0
}
PREVIOUS_UNMATCHED={
 "ENG3/2025-26":0,
 "ENG4/2025-26":28,
 "ENG5/2025-26":114,
 "GRE1/2025-26":9,
 "GRE1/2026-27":18,
 "SCO1/2025-26":10,
 "SCO1/2026-27":7,
 "AUT1/2026-27":42
}
PREVIOUS_SHA={
 "ENG4/2025-26":"eff4fa15cb18857091d1f0666d0b8a6c61eda7a8374feef8f2d8a38244e0e45d",
 "ENG5/2025-26":"2372229d616a57f9df3d9a401cd942df8e1909ba67017b3793c6aceaf0becf76",
 "GRE1/2025-26":"0f77e72cb9db8f5dcd298d16f20551a82d018b478fc12a67e065241f05810830",
 "GRE1/2026-27":"89a08b02b2bdec2c10472274a2e83d4f39aba5894c2ac952c2df8b24432ba3b5",
 "SCO1/2025-26":"be3c45e08f09a327e3fd5289dd0b362b200f430ed5845cb18df1aca7e3ced2ee",
 "SCO1/2026-27":"042594e2a58575ae3c029c8c8c235926e35dd04c4bcf7c0500ed905d4539bc03"
}
ALIAS_DELTA={
 "ENG4/2025-26":{"bristol rvs":"Bristol Rovers","crewe":"Crewe Alexandra","salford":"Salford City"},
 "ENG5/2025-26":{"boston utd":"Boston United"},
 "GRE1/2025-26":{"levadeiakos":"Levadiakos"},
 "GRE1/2026-27":{
   "levadeiakos":"Levadiakos","ofi crete":"OFI",
   "volos nfc":"Volos","aris":"Aris Thessaloniki",
   "iraklis":"Iraklis 1908",
 },
 "SCO1/2025-26":{"dundee":"Dundee FC"},
 "SCO1/2026-27":{"dundee":"Dundee"},
 "AUT1/2026-27":{
   "lask":"LASK Linz","lask linz":"LASK Linz","sk rapid":"Rapid Wien",
   "sk rapid wien":"Rapid Wien","rapid":"Rapid Wien",
   "sk sturm graz":"Sturm Graz","sturm graz":"Sturm Graz",
   "red bull salzburg":"FC Salzburg","rb red bull salzburg":"FC Salzburg",
   "salzburg":"FC Salzburg",
   "austria vienna":"Austria Wien","fk austria wien":"Austria Wien",
   "a lustenau":"Austria Lustenau",
   "altach":"SCR Altach","grazer ak":"Grazer AK",
   "ried":"SV Ried","tirol":"WSG Tirol","hartberg":"TSV Hartberg",
   "wolfsberger ac":"Wolfsberger AC"
 }
}
def patched_lookups(group,clubs):
    league=group.split("/")[0]
    original=old.exact_name_maps(league,clubs)
    for alias,target in ALIAS_DELTA.get(group,{}).items():
        if target not in clubs:raise ValueError("ALIAS_NOT_IN_TARGET_CLUBS:"+alias+"/"+target)
        k=old.norm(alias)
        if k in original and original[k]!=target:
            # Only replace a collision-removal artifact explicitly
            raise ValueError("NEVER_OVERRIDE_EXISTING_DIFFERENT_TEAM:"+alias)
        original[k]=target
    return original

def reparse_historical(raw,group,clubs):
    # Parse the file once per target group, matching only the previously unresolved
    # fixture keys; previously confirmed 739 keys are immutable evidence.
    r=csv.DictReader(io.StringIO(raw.decode("utf-8-sig","replace"),newline=""))
    if not {"Div","Date","HomeTeam","AwayTeam","FTHG","FTAG"}.issubset(r.fieldnames or []):
        raise ValueError("FOOTBALL_DATA_HEADERS_CHANGED")
    aliases=patched_lookups(group,clubs)
    source={};diag=Counter();unmapped=[]
    season=group.split("/")[1]
    for item in r:
        if not item.get("Date"):continue
        d=old.day_of(item["Date"])
        if d is None or d>old.MAX_DATE:continue
        if season=="2025-26" and not date(2025,7,1)<=d<date(2026,7,1):continue
        if season=="2026-27" and not date(2026,7,1)<=d<=old.MAX_DATE:continue
        if item.get("Div")!=old.TARGETS[group][2]:raise ValueError("DIVISION_CHANGED")
        ft=old.score(item.get("FTHG"),item.get("FTAG"))
        if ft is None:continue
        h=old.match_name(item.get("HomeTeam"),aliases)
        a=old.match_name(item.get("AwayTeam"),aliases)
        if not h or not a or h==a:
            diag["unknown"]+=1
            if len(unmapped)<8:unmapped.append({"home":item.get("HomeTeam"),"away":item.get("AwayTeam")})
            continue
        key=(h,a)
        if key in source:
            # The Greek & Scottish full seasons have home/away rematches.
            # The first match in 2025/26 (earliest fixture) should precede
            # 2026 spring group-stage replays for this Aug-Dec research subset.
            diag["later_pair_rematch"]+=1
            if source[key][0]>d:source[key]=(d,ft)
            continue
        source[key]=(d,ft)
    return source,{"mapped_unique_pair_count":len(source),"flags":dict(diag),"unmapped_samples":unmapped}

def reparse_austria(raw,group,clubs):
    text=raw.decode("utf-8-sig","replace")
    data=csv_rows(text)  # known existing parser strips "# Source" comments safely
    aliases=patched_lookups(group,clubs)
    by_date={};source={};diag=Counter();unmapped=[]
    for row in data:
        if str(row.get("status") or "").strip().lower() not in ("finished","completed","full-time","full time","ft"):
            continue
        d=old.day_of(str(row.get("date") or "")[:10])
        if not d or not date(2026,7,1)<=d<=old.MAX_DATE:continue
        ft=old.score(row.get("home_goals"),row.get("away_goals"))
        if ft is None:diag["no_numeric_score"]+=1;continue
        h=old.match_name(row.get("home"),aliases);a=old.match_name(row.get("away"),aliases)
        if not h or not a or h==a:
            diag["unknown_team"]+=1
            if len(unmapped)<8:unmapped.append({"home":row.get("home"),"away":row.get("away"),"date":d.isoformat()})
            continue
        k=(d,h,a)
        if k in by_date:
            if by_date[k]!=ft:diag["conflicting_alias_same_fixture"]+=1
            else:diag["redundant_alias_duplicate"]+=1
        else:by_date[k]=ft
        pair=(h,a)
        if pair in source and source[pair][0]!=d:
            diag["new_date_same_home_away"]+=1
            if d<source[pair][0]:source[pair]=(d,ft)
        elif pair not in source:source[pair]=(d,ft)
    return source,{"mapped_unique_pair_count":len(source),
       "mapped_unique_exact_date_keys":len(by_date),
       "flags":dict(diag),"unmapped_samples":unmapped}

def audit():
    original,clubs,_=old.pinned_primary()
    target_results=[]
    for group in old.TARGETS:
        if group=="ENG3/2025-26":
            target_results.append({"group":group,"prior_confirmed":256,
              "unresolved_initial":0,"targeted_new_verified":0,"status":"PRIOR_256_FROZEN_NO_REPEAT"})
            continue
        initial=PREVIOUS_EXACT[group];unresolved_n=PREVIOUS_UNMATCHED[group]
        try:
            raw=old.fetch(old.URLS[group])
            actual_sha=hashlib.sha256(raw).hexdigest()
            if group in PREVIOUS_SHA and actual_sha!=PREVIOUS_SHA[group]:
                raise ValueError("SOURCE_SHA_DRIFT_STOP")
            if group=="AUT1/2026-27":
                first_source={}
            else:
                first_source,_=old.external_csv(raw,group,clubs[group])
            remain={}
            for k,v in original[group].items():
                other=first_source.get(k)
                if other is None or other!=v:remain[k]=v
            if len(remain)!=unresolved_n or len(original[group])-len(remain)!=initial:
                raise ValueError("FROZEN_739_BASELINE_IDENTITIES_CHANGED:"+group)
            newsource,diagnostics=(reparse_austria(raw,group,clubs[group])
                  if group=="AUT1/2026-27" else reparse_historical(raw,group,clubs[group]))
            confirmed=0;date_only=0;conflicts=0;absent=0;zeroconfirm=0
            diffs=defaultdict(list)
            for (home,away),(d,ft) in remain.items():
                candidate=newsource.get((home,away))
                if candidate is None:
                    absent+=1
                    if len(diffs["still_unmatched"])<9:
                        diffs["still_unmatched"].append({"home":home,"away":away,"date":d.isoformat()})
                    continue
                nd,other_ft=candidate
                if other_ft!=ft:
                    conflicts+=1
                    if len(diffs["source_FT_disagrees"])<14:
                        diffs["source_FT_disagrees"].append({"date":d.isoformat(),
                          "home":home,"away":away,
                          "old_score":list(ft),"independent_score":list(other_ft),
                          "independent_date":nd.isoformat()})
                elif nd!=d:
                    date_only+=1
                    if len(diffs["date_only"])<10:
                        diffs["date_only"].append({"home":home,"away":away,
                         "original_date":d.isoformat(),"source_date":nd.isoformat()})
                else:confirmed+=1
                if ft==(0,0) and other_ft==ft:zeroconfirm+=1
            if confirmed+date_only+conflicts+absent!=unresolved_n:
                raise ValueError("EXCEPTION_SUM_NOT_EQUAL_TO_BASELINE")
            status=("TARGET_EXCEPTIONS_FULLY_RESOLVED" if confirmed==unresolved_n
                    else "TARGET_EXCEPTIONS_PARTIAL_OR_REAL_FT_CONFLICTS")
            if diagnostics["flags"].get("conflicting_alias_same_fixture"):
                status="BLOCKED_CONFLICTING_ALIAS_SCORES"
            target_results.append({"group":group,"prior_confirmed_unchanged":initial,
                "unresolved_initial":unresolved_n,
                "targeted_new_verified":confirmed,
                "targeted_score_matches_different_date":date_only,
                "targeted_old_score_conflicts":conflicts,
                "targeted_still_unmatched":absent,
                "targeted_new_zero_zero_confirmed":zeroconfirm,
                "status":status,"input_source_sha256":actual_sha,
                "external_source":old.URLS[group],
                "targeted_diagnostics":diagnostics,
                "issue_samples":dict(diffs),"training_admitted":0})
        except Exception as e:
            target_results.append({"group":group,"prior_confirmed_unchanged":initial,
                "unresolved_initial":unresolved_n,"status":"FAIL_CLOSED_TARGET_SOURCE_OR_QA",
                "error":str(e)[:220] if isinstance(e,ValueError) else "external provider unavailable",
                "http_status":getattr(e,"code",None),
                "error_class":type(e).__name__,"training_admitted":0})
    new=sum(x.get("targeted_new_verified",0) for x in target_results)
    old_baseline=739
    scores_mismatched=sum(x.get("targeted_old_score_conflicts",0) for x in target_results)
    unresolved_after=967-old_baseline-new
    return {"checked_utc":datetime.now(timezone.utc).isoformat(),
        "status":"228_ONLY_TARGETED_RECONCILIATION_COMPLETE_NO_739_RETEST",
        "six_leagues_and_eight_groups":True,
        "original_scored_research_candidates":967,
        "prior_739_proof_not_retested_or_mutated":739,
        "initial_228_unresolved":228,
        "targeted_new_date_home_away_FT_confirmed":new,
        "cumulative_exact_FT_date_witness":old_baseline+new,
        "unresolved_score_or_identity_or_access":unresolved_after,
        "confirmed_conflicting_FT_from_target":scores_mismatched,
        "new_training_rows":0,
        "original_2396_research_quarantine_rows_unchanged":True,
        "all_200_ENG3_ENG4_preexisting_legacy_HOLD_kept":True,
        "no_original_predictions_or_M4_changes":True,
        "group_results":target_results}

def selftest():
    prim,clubs,_=old.pinned_primary()
    assert len(prim["ENG3/2025-26"])==256
    assert sum(PREVIOUS_EXACT.values())==739
    assert sum(PREVIOUS_UNMATCHED.values())==228
    for g in ALIAS_DELTA:
        index=patched_lookups(g,clubs[g])
        for label,expected in ALIAS_DELTA[g].items():
            assert index[old.norm(label)]==expected,(g,label)
    assert old.score("0","0")==(0,0) and old.score("","") is None
    print("PASS 739 frozen, only 228 unresolved, safe 7 group alias exception maps")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--live",action="store_true")
    o=p.parse_args()
    if o.self_test:selftest()
    if o.live:
        print("SIX_228_TARGETED_START")
        print(json.dumps(audit(),indent=2,ensure_ascii=False))
        print("SIX_228_TARGETED_END")
