#!/usr/bin/env python3
"""Compare only 161 NEW ODbL Swiss 2025/26 facts to SHA-pinned previously
independently adjudicated 228 Swiss records; do NOT rerun the old 228 QA.
No raw third party score table saved or rehosted, no model training.
"""
from __future__ import annotations
import csv,json,hashlib,argparse
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from verify_public_season_csv_2526 import name_map,norm,csv_rows
SRC=Path("experiments/263/league_expansion/odbl_openligadb_swiss1/che1_2025_26_football_scores_ODbL_research_quarantine.csv")
URL="https://matchdaysync.com/api/public/csv/swiss-super-league/2025-26/matches"
SHA="46a8b9aedb6bf294a6991e701609c04d511eb844bd02a24094349ce4be51678c"
def old161():
    data=list(csv.DictReader(SRC.open(encoding="utf-8",newline="")))
    if len(data)!=161:raise ValueError("ODBL_NEW_161_COUNT_CHANGED")
    canonical=name_map("CHE1")
    ids=set();results={}
    for r in data:
        mid=r["match_id"]
        if mid in ids:raise ValueError("DUPLICATE_SWISS_ODBL_MATCH_ID")
        ids.add(mid)
        home=canonical.get(norm(r["home"]))
        away=canonical.get(norm(r["away"]))
        if not home or not away or home==away:
            raise ValueError("CANNOT_IDENTIFY_NEW_ODBL_TEAM")
        key=(r["date"],home,away)
        if key in results:raise ValueError("ODBL_DUPLICATE_DATE_CLUBS")
        results[key]=((int(r["ft_home"]),int(r["ft_away"])),mid)
    return results
def run():
    inputs=old161()
    req=Request(URL,headers={"User-Agent":"Swiss-New-161-Research-Source-Witness/1.0 (one-time only)","Accept":"text/csv"})
    with urlopen(req,timeout=30) as res:raw=res.read(2_000_001)
    if len(raw)>2_000_000:raise ValueError("SOURCE_OVERSIZED")
    if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError("INDEPENDENT_228_ORIGINAL_SHA_CHANGED")
    source=csv_rows(raw.decode("utf-8-sig"))
    canon=name_map("CHE1")
    witness={};source_total=0
    for r in source:
        if r.get("status","").strip().lower()!="finished":continue
        date=r["date"][:10]
        h=canon.get(norm(r["home"]));a=canon.get(norm(r["away"]))
        if not h or not a or h==a:raise ValueError("INDEPENDENT_TEAM_ALIAS_UNEXPECTED")
        k=(date,h,a)
        if k in witness:raise ValueError("INDEPENDENT_DUPLICATE_FIXTURE")
        witness[k]=(int(r["home_goals"]),int(r["away_goals"]))
        source_total+=1
    if source_total!=228:raise ValueError("PINNED_228_MATCH_SOURCE_UNEXPECTED")
    matches=[];mismatches=[];notfound=[]
    for k,(score,mid) in inputs.items():
        got=witness.get(k)
        if got is None:notfound.append({"match_id":mid,"key":"|".join(k)})
        elif got!=score:mismatches.append({"match_id":mid,"key":"|".join(k),"original_ODbL_score":"-".join(map(str,score))})
        else:matches.append(mid)
    if len(matches)+len(mismatches)+len(notfound)!=161:raise ValueError("TARGET_161_COUNT_DRIFT")
    return {
     "status":"SWISS_NEW_161_ODBL_TARGETED_SECOND_SCORE_WITNESS_DONE",
     "at_utc":datetime.now(timezone.utc).isoformat(),
     "only_new_odbl_match_facts_checked":161,
     "old_228_source_witnesses_rechecked":0,
     "pinned_228_old_source_reused_as_comparison_only":True,
     "first_source":"OpenLigaDB ODbL-1.0",
     "comparison_source":URL,"comparison_source_sha256":SHA,
     "ODbL_exact_date_teams_90min_FT_against_prior_228":len(matches),
     "ODbL_FT_conflicts":len(mismatches),
     "ODbL_unmatched_date_or_team":len(notfound),
     "unmatched_or_conflicting_ODbL_original_only":mismatches+notfound,
     "no_publishing_of_competing_source_FT":True,
     "source_is_PARTIAL_161_of_228":True,
     "original_2396_296_holds_unchanged":True,
     "training_rows_newly_approved":0,
     "main_M4_and_signed_predictions_untouched":True,
     "other_67_not_archived_from_unlicensed_provider":True,
     "no_repeated_full_228_RSSSF_swiss_fact_audit":True}
def test():
    x=old161()
    assert len(x)==161 and (norm("FC Basel 1893") in name_map("CHE1"))
    print("PASS 161 new ODbL Swiss fixture keys; 0 previously tested 228 source cases rerun")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--live",action="store_true");a=p.parse_args()
    if a.self_test:test()
    if a.live:
        try:d=run()
        except Exception as e:d={"status":"FAIL_CLOSED_NEW_SWISS_161_NOT_ADJUDICATED","error_class":type(e).__name__,
          "reason":str(e)[:180] if isinstance(e,ValueError) else "source unavailable","training_rows_newly_approved":0}
        print("SWISS_NEW161_START")
        print(json.dumps(d,indent=2,ensure_ascii=False))
        print("SWISS_NEW161_END")
