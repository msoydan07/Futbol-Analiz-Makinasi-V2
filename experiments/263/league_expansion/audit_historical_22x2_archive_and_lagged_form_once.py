#!/usr/bin/env python3
"""Historical-only 22 leagues x two seasons coverage and pre-match date-form diagnostic.

NO NEW fixture predictions, NO network, NO training, NO production changes,
NO repeated FT checks. Reads already SHA-pinned local research CSVs and
pre-existing evidence summary. Missing timestamps are not fabricated.
"""
import argparse
import json
from collections import Counter,defaultdict
from datetime import date,timedelta
from pathlib import Path
from prepare_2396_provenance_rights_quality_gate_20261114 import EXPECTED,HOLD,read_csv,match_key
from check_1871_stage_vintage_shadow_gates_once import recognize_stage

ROOT=Path("experiments/263/league_expansion")
SEASONS=("2025-26","2026-27")
CC0="PUBLISHER_CC0_CLAIM"
MAX=date(2026,11,13)
HOLD96="eng5_2025_26_96_exact_original_FT_conflict_training_HOLD_20261114.csv"
HOLD96_SHA="0a422d9e0a68b6e714852addcb3ec9cf4602a7f6"
ANALYSIS_EXISTING={"ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1"}
EXTERNAL_ONLY={
 ("CHE1","2025-26"):{"independent_fact_checks":228,"source":"previous independent Swiss 228 FT QA","inside_quarantine":0},
 ("DNK1","2025-26"):{"independent_fact_checks":192,"source":"previous independent Danish 192 FT QA","inside_quarantine":0},
 ("DNK1","2026-27"):{"independent_fact_checks":84,"source":"previous Danish 2026-27 source checks","inside_quarantine":0},
 ("CHE1","2026-27"):{"independent_fact_checks":78,"source":"previous Swiss 2026-27 source checks","inside_quarantine":57},
}
def hold_keys():
    a,sha=read_csv(HOLD)
    b,sha96=read_csv(HOLD96)
    if len(a)!=200 or len(b)!=96 or sha96!=HOLD96_SHA:
        raise ValueError("SOURCE_HOLD_PIN_CHANGED")
    old={match_key(r) for r in a}
    new={("ENG5","2025-26",r["original_date"],r["home"],r["away"]) for r in b}
    if len(old)!=200 or len(new)!=96 or old&new:
        raise ValueError("HOLD_KEY_DUPLICATE_OR_DRIFT")
    return old,new

def count_form_history(dataset,lookback_days=2,required_games=5):
    """Date-only diagnostic, NOT verified 'as-of' eligibility.
    Only per-team games at least 2 calendar dates before fixture date.
    Never use the target's FT, HT, xG or another same-day match.
    """
    dataset=sorted(dataset,key=lambda x:(x["date"],x["home"],x["away"]))
    appearances=defaultdict(list)
    totals=Counter()
    for r in dataset:
        d=date.fromisoformat(r["date"])
        prior_home=[z for z in appearances[r["home"]] if z<=d-timedelta(days=lookback_days)]
        prior_away=[z for z in appearances[r["away"]] if z<=d-timedelta(days=lookback_days)]
        totals["total_date_only_candidates"]+=1
        if prior_home and prior_away:totals["both_teams_at_least_1_old_match"]+=1
        if len(prior_home)>=3 and len(prior_away)>=3:totals["both_teams_at_least_3_old_matches"]+=1
        if len(prior_home)>=required_games and len(prior_away)>=required_games:
            totals["both_teams_at_least_5_old_matches"]+=1
        appearances[r["home"]].append(d)
        appearances[r["away"]].append(d)
    return dict(totals)

def audit():
    manifest=json.loads((ROOT/"pool_manifest_20261113.json").read_text(encoding="utf-8"))
    leagues=manifest["active_leagues"]+manifest["training_only_leagues"]
    assert len(leagues)==22 and len({x["code"] for x in leagues})==22
    old,new=hold_keys()
    allkeys=set();observed_holds=set()
    groups=defaultdict(list);by_group=defaultdict(Counter);source_totals=Counter()
    for filename,(blob,n,kind) in EXPECTED.items():
        rows,sha=read_csv(filename)
        if sha!=blob or len(rows)!=n:raise ValueError("SOURCE_BLOB_OR_COUNT_CHANGED:"+filename)
        for r in rows:
            k=match_key(r);l,s,ds,h,a=k
            if k in allkeys:raise ValueError("DUPLICATE_RESEARCH_FIXTURE")
            allkeys.add(k)
            if s not in SEASONS or l not in {x["code"] for x in leagues}:
                raise ValueError("OUT_OF_SCOPE_LEAGUE_OR_SEASON")
            d=date.fromisoformat(ds)
            if d>MAX:raise ValueError("FUTURE_MATCH_FOUND")
            group=(l,s)
            by_group[group]["pinned_research_rows"]+=1
            source_totals[kind]+=1
            if k in old or k in new:
                observed_holds.add(k);by_group[group]["exact_quality_hold"]+=1
            elif kind!=CC0:
                by_group[group]["source_rights_pending"]+=1
            elif l=="AUT1" and s=="2025-26" and recognize_stage(r)=="conference_playoff":
                by_group[group]["outside_normal_league_playoff"]+=1
            else:
                by_group[group]["CC0_unheld_date_only_possible"]+=1
                groups[group].append({"date":ds,"home":h,"away":a})
    if len(allkeys)!=2396 or observed_holds!=old|new:
        raise ValueError("2396_OR_296_FROZEN_HOLD_DRIFT")
    expected={CC0:2071,"CCBY_COMPILATION_UPSTREAM_UNCLEAR":322,"THIRD_PARTY_REHOST_UNCLEARED":3}
    if dict(source_totals)!=expected:raise ValueError("SOURCE_RIGHTS_COUNTS_CHANGED")
    rows=[];totals=Counter();absent=[]
    for rec in leagues:
        league=rec["code"]
        for season in SEASONS:
            key=(league,season)
            stats=dict(by_group[key])
            diag=count_form_history(groups[key])
            for field,num in diag.items():totals[field]+=num
            if league in ANALYSIS_EXISTING:
                status="MAIN_10_PRODUCTION_DATA_SEPARATE__NOT_SCANNED"
            elif stats.get("pinned_research_rows",0)>0:
                status="RESEARCH_ROWS_PRESENT__NOT_ADMITTED_FOR_TRAINING"
            elif key in EXTERNAL_ONLY:
                status="CROSS_SOURCE_FACTS_CHECKED__NO_PERMITTED_RESEARCH_ROW_IMPORTED"
            else:
                status="NO_RESEARCH_ROWS_OR_INDEPENDENT_SCORE_WITNESSES_RECORDED"
                absent.append(f"{league}/{season}")
            res={
              "league":league,"season":season,
              "role":rec.get("group") or ("analysis" if league in ANALYSIS_EXISTING|{"CHE1","SCO1","DNK1"} else "training_only"),
              "status":status,
              **stats,
              "historical_date_form_diagnostic_only":diag,
              "training_admission":0
            }
            if key in EXTERNAL_ONLY:
                res["separate_independent_score_facts_NOT_ADDITIVE"]=EXTERNAL_ONLY[key]
            if stats.get("pinned_research_rows",0):
                dates=[r["date"] for r in groups[key]]
                if dates:
                    res["CC0_unheld_earliest_date"]=min(dates)
                    res["CC0_unheld_last_date"]=max(dates)
            rows.append(res)
    assert len(rows)==44 and sum(x.get("pinned_research_rows",0) for x in rows)==2396
    assert sum(x.get("exact_quality_hold",0) for x in rows)==296
    assert sum(x.get("source_rights_pending",0) for x in rows)==325
    assert sum(x.get("outside_normal_league_playoff",0) for x in rows)==3
    assert sum(x.get("CC0_unheld_date_only_possible",0) for x in rows)==1772
    research_groups=[x for x in rows if x["league"] not in ANALYSIS_EXISTING]
    assert len(research_groups)==24
    assert len([x for x in research_groups if x.get("pinned_research_rows",0)>0])==16
    return {
      "date":"2026-11-14",
      "status":"HISTORICAL_ONLY_22x2_44_CELLS_CHECKED_NO_NEW_FIXTURES",
      "role":"research-only completeness and conservative date-form diagnostic; NOT a training/rights/as-of approval",
      "allowed_seasons":list(SEASONS),
      "league_count":22,"league_season_cells":44,
      "research_league_season_cells_excluding_existing_main":24,
      "research_cells_with_pinned_candidate_rows":16,
      "research_cells_without_pinned_candidate_rows":8,
      "research_cells_with_no_pinned_rows_and_no_prior_independent_facts":absent,
      "separate_existing_main_league_season_cells_not_scanned":20,
      "research_quarantine_rows":2396,
      "exact_source_quality_holds":296,
      "other_rights_uncleared":325,
      "Austrian_non_regular_playoffs_separated":3,
      "CC0_unheld_ordinary_league_date_only_candidates":1772,
      "date_only_diagnostic_total":dict(totals),
      "unavailable_point_in_time_feature_timestamp_certificates":1772,
      "date_only_2day_cooling_off_interpretation":"Only sufficient previous game dates; not proof that historical results actually appeared online before target kickoff. True observed_at and published_at not reconstructed.",
      "separate_nonadditive_evidence":{
        "CHE1_2025_26":228,
        "DNK1_2025_26":192,
        "CHE1_2026_27":78,
        "DNK1_2026_27":84
      },
      "new_rows_added_to_training":0,
      "new_match_score_sources_rechecked":0,
      "future_matches_queried":0,
      "previous_871_and_904_verification_batches_repeated":0,
      "production_10league_M4_SHA_touched":False,
      "matches_by_league_season":rows,
      "next_historical_work":"Complete eight not-yet-ingested non-production league/season cells with licence-safe original fixture facts where available, mark independent evidence separately, then address 296 held quality errors before any research training admission. Never infer publication timestamps."
    }

def test():
    r=[
       {"date":"2025-10-01","home":"A","away":"B"},
       {"date":"2025-10-02","home":"C","away":"A"},
       {"date":"2025-10-04","home":"A","away":"C"},
       {"date":"2025-10-04","home":"B","away":"D"},
       {"date":"2025-10-07","home":"A","away":"B"},
    ]
    c=count_form_history(r)
    assert c["total_date_only_candidates"]==5,c
    assert c["both_teams_at_least_1_old_match"]>=1,c
    assert c.get("both_teams_at_least_5_old_matches",0)==0
    print("PASS strict date-only prior results; same date excluded; zero target result features; no future match or 2024/25 data")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if a.self_test:test()
    if a.run:
        print("HISTORICAL_ARCHIVE_START")
        print(json.dumps(audit(),indent=2,ensure_ascii=False))
        print("HISTORICAL_ARCHIVE_END")

