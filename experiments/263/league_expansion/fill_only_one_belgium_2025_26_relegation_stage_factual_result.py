#!/usr/bin/env python3
"""ONE exact missing BEL1 match only: Dender - La Louviere May 3 2026 2-1.

Source authoritative club own website + opponent official page + BBC.
Original core 311 already confirmed to be 240 normal + 71 playoff fixtures,
one missing in 4-team relegation double-round-robin. Identify UUID prefixes
through existing complete group graph, confirm absent by date & directed pair,
and add research-only single historical result fact. Never write into the
original 4617 match score file or main 10-league M4.
"""
from pathlib import Path
import csv,hashlib,json
from collections import Counter
ROOT=Path("experiments/263/league_expansion")
DIR=ROOT/"bel1_2025_26_one_official_missing"
PREV=ROOT/"bel1_2025_26_311_core_stage_graph_missing_fixtures_20261114.json"
CORE=Path("data/results_only_263/2026-11-10_completed_4617_scores_only.csv")
PROV=Path("data/results_only_263/4617_research_input_provenance.json")
OUT=DIR/"bel1_2025_05_03_dender_raal_single_novel_research_only.csv"
REPORT=DIR/"bel1_2025_26_312_source_stage_identity_completion_20261114.json"
FIRST="https://fcvdendereh.be/nl/nieuws/nieuws/2026/fc-dender-la-louviere-2-1-tanken-vertrouwen/"
OPPONENT="https://www.raal.be/event/playoffs-md05-dender-raal/"
NEUTRAL="https://www.bbc.co.uk/sport/football/live/cp9prp4n5rdt"
DATE="2026-05-03"
def run():
 a=json.loads(PREV.read_text())
 if a["old_BEL1_2025_26_scored_source_rows"]!=311 or a["normal_stage_until_2026_03_22"]!=240 or a["separately_grouped_2026_04_01_thru_2026_05_26"]!=71:
  raise ValueError("PREVIOUS_BELGIUM_STAGE_COUNT_CHANGED")
 comps=[x for x in a["components"] if x["group_size"]==4]
 if len(comps)!=1 or comps[0]["missing_directed_fixture_count"]!=1:raise ValueError("MISSING_DIRECTED_NOT_ONE")
 bad=comps[0]["missing_internal_team_uuid_hashes_not_real_names"][0]
 if bad["home_uuid_prefix"]!="3978e856-d49" or bad["away_uuid_prefix"]!="77e47d4e-eed":
  raise ValueError("MISSING_TEAM_UUID_NOT_DENDER_LA_LOUVIERE")
 prov=json.loads(PROV.read_text())
 if hashlib.sha256(CORE.read_bytes()).hexdigest()!=prov["source_snapshot_sha256"]:
  raise ValueError("ORIGINAL_MAIN_CORE_SOURCE_DRIFT")
 rows=[x for x in csv.DictReader(CORE.open(encoding="utf-8-sig",newline="")) if x["league"]=="BEL1" and x["season"]=="2025-2026"]
 if len(rows)!=311:raise ValueError("ORIGINAL_311_CHANGED")
 homes={r["home_id"] for r in rows if r["home_id"].startswith("3978e856-d49")}
 aways={r["away_id"] for r in rows if r["away_id"].startswith("77e47d4e-eed")}
 if len(homes)!=1 or len(aways)!=1:raise ValueError("CANNOT_RECOVER_ORIGINAL_REGISTRY_TEAM_IDS")
 home=next(iter(homes));away=next(iter(aways))
 if any(r["match_date"]==DATE and r["home_id"]==home and r["away_id"]==away for r in rows):
  raise ValueError("NOT_NOVEL_PRESENT_IN_ORIGINAL")
 # Old source team ID's independently identifiable in 2025/26 first round:
 # 3978... HOME Dender FCV -> 2025-07-26 0-0 Cercle; 77e... HOME
 # RAAL La Louviere -> 2025-07-26 0-2 Standard (club name taken from
 # original 2025/26 source report and source league official).
 if not any(r["match_date"]=="2025-07-26" and r["home_id"]==home and (r["home_goals"],r["away_goals"])==("0","0") for r in rows):
  raise ValueError("DENDER_REGISTRY_NAME_FIRST_ROUND_QA_FAILED")
 if not any(r["match_date"]=="2025-07-26" and r["home_id"]==away and (r["home_goals"],r["away_goals"])==("0","2") for r in rows):
  raise ValueError("RAAL_REGISTRY_NAME_FIRST_ROUND_QA_FAILED")
 DIR.mkdir(parents=True,exist_ok=True)
 fields=["league","season","date","home_id","away_id","home","away","ft_home","ft_away","stage","source_official_home_url","source_official_away_url","source_neutral_url","source_rights","research_status","training_gate"]
 row={
  "league":"BEL1","season":"2025-26","date":DATE,
  "home_id":home,"away_id":away,"home":"FCV Dender EH","away":"RAAL La Louvière",
  "ft_home":"2","ft_away":"1","stage":"RELEGATION_PLAYOFFS_MD5",
  "source_official_home_url":FIRST,"source_official_away_url":OPPONENT,
  "source_neutral_url":NEUTRAL,"source_rights":"SINGLE_PUBLIC_MATCH_FACT_CITED_ONLY_NOT_BULK_SOURCE_REHOST",
  "research_status":"ONE_NEW_OFFICIAL_SCORE_TWO_CLUB_SOURCES_AGREE_RESEARCH_ONLY",
  "training_gate":"NOT_APPROVED_ASOF_SOURCE_RIGHTS_AND_INDEPENDENT_FEATURE_TIMING"
 }
 with OUT.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
  w.writeheader();w.writerow(row)
 report={
  "status":"PASS_BEL1_2025_26_REGULAR_240_PLUS_GROUP_PLAYOFF_72_SOURCE_IDS_COMPLETED",
  "source_first_group_regular":240,"source_original_group_playoffs":71,
  "one_official_missing_group_result_added":1,
  "total_standard_BEL1_season_2025_26_known":312,
  "original_main_core_4617_untouched":True,
  "additional_research_source_fixture_ids":1,
  "preexisting_research_source_identities_prior_Spain337":4842,
  "research_source_identites_new":4843,
  "combined_4617_plus_4843":9460,
  "original_source_BEL1_311_scores_not_rechecked":True,
  "match":row,
  "first_club_official_witness":FIRST,
  "second_club_official_witness":OPPONENT,
  "third_public_FT_witness":NEUTRAL,
  "out_csv":str(OUT),
  "special_Gent_Genk_2026_05_31_cross_group_penalty_winner_not_standard_league_312":True,
  "separate_top_tier_v_second_tier_Lommel_Dender_two_fixtures_not_added":True,
  "training_approved":0
 }
 REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 return report
if __name__=="__main__":
 print(json.dumps(run(),ensure_ascii=False,indent=2))
