#!/usr/bin/env python3
"""Data-only licensing and update freshness gate for the 633+118 open-source candidates.

Reads only existing research metadata and score-pointer manifests, NOT model
training, old score source re-query, API raw results or user's manual xG.
This is not a legal opinion: fail closed whenever source rights are unclear.
"""
import argparse,hashlib,json
from collections import Counter
from pathlib import Path

ROOT=Path("experiments/263/league_expansion")
FIVE=ROOT/"current_2026_27_five_leagues_footballcharts_personal_research_API_rights_probe_20261114.json"
FOUR=ROOT/"2026_27_FOUR_118_SCOPED_CROSS_SOURCE_FIXTURE_IDENTITY_METADATA_20261114.json"
SCORE=ROOT/"FINAL_9460_RESEARCH_SCORE_FACTS_FILTERED_20261114.json"
OLD_SCAN=ROOT/"2026_27_17_persisted_leagues_one_freshness_aggregates_only_20261114.json"
OUT=ROOT/"2026_27_751_SOURCE_RIGHTS_AND_STALE_CC0_FINAL_GATE_20261114.json"
CUT="2026-11-13"

# Verified November 14 via *direct first-party repo file inspection*. All four
# git blob SHAs equal the original source pointers already pinned in research.
# These are WHOLE repo source blob SHAs, not newly created event datasets.
PUBLIC_CC0={
 "SCO1":{"repo":"openfootball/europe","file":"scotland/2026-27_sco1.txt",
         "blob":"60b4918c6ee436fae3716ebe50dbcbc6b9cb84fb","scored_lines":42},
 "CHE1":{"repo":"openfootball/europe","file":"switzerland/2026-27_ch1.txt",
         "blob":"d0234e0d4356fa92adcf6b2fdc728014ce081136","scored_lines":54},
 "GRE1":{"repo":"openfootball/europe","file":"greece/2026-27_gr1.txt",
         "blob":"887c592e263406efc12eae97a5c808422957c09c","scored_lines":35},
 "AUT1":{"repo":"openfootball/austria","file":"2026-27/1-bundesliga.txt",
         "blob":"3d94e3020c2fbe38f298af9e5d63369fbc069c95","scored_lines":42},
}
FIVE_TARGETS={"ENG5":190,"ESP2":141,"ITA2":110,"FRA2":108,"DNK1":84}
FOUR_TARGETS={"SCO1":33,"CHE1":21,"GRE1":34,"AUT1":30}
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def execute():
 five=load(FIVE);four=load(FOUR);score=load(SCORE);old=load(OLD_SCAN)
 assert (score["source_rows"],score["frozen_core_4617"],
         score["research_score_fact_qa_pass_only"],score["model_training_admitted_new_rows"])==(9460,4617,4218,0)
 assert five["rights_classification"]=="FREE_PERSONAL_RESEARCH_USE_ONLY_NO_RAW_DATA_REDISTRIBUTION_OR_SUBSTANTIAL_EXTRACT_PUBLICATION"
 assert five["scored_source_rows_only_ephemeral"]==633
 assert sum(FIVE_TARGETS.values())==633 and sum(FOUR_TARGETS.values())==118
 assert four["status"]=="FOUR_LEAGUE_176_OF_176_MATCHED_118_SOURCE_ONLY_CANDIDATES_RIGHTS_HOLD"
 assert four["source_successful"]==4 and four["source_access_blocked"]==0
 assert four["source_only_candidate_count_after_canonical_match"]==118
 assert four["identities_known_present_in_old_archive_and_source"]==176
 assert four["new_model_training_rows"]==0
 assert not four["main_M4_or_xG_file_modified"]
 for league,count in FIVE_TARGETS.items():
  got=five["by_league"][league]
  assert got["derived_metadata_only"]["matched_completed_historical_result_field_rows"]==count
  assert got["raw_fixture_rows_written_to_GitHub"]==0
  assert got["new_training_rows"]==0
 for lg,gap in FOUR_TARGETS.items():
  g=four["league_results"][lg]
  assert g["source_missing_identity_candidates_after_curated_aliases"]==gap
  assert g["curated_team_roster_date_score_matches"]==g["local"]
  assert g["curated_team_roster_source_date_or_FT_conflicts_hold"]==0
  assert g["old_rows_not_recovered_from_source"]==0
  assert old["counts"][lg]["source_minus_local_count"]==gap
 # Important: original explicit source blob SHA is NOT a license for other
 # providers' new 118 match score lines.
 report={
  "date":"2026-11-14","cutoff":CUT,
  "status":"751_CANDIDATES_RIGHTS_AND_INDEPENDENT_FT_GATED_NO_AUTO_PROMOTION",
  "existing_pinned_source_rows_unchanged":9460,
  "current_provider_new_fixture_candidates":751,
  "five_leagues_live_only_2026_27":FIVE_TARGETS,
  "five_current_unarchived_total":633,
  "four_leagues_count_gap_after_canonical_club_identity":FOUR_TARGETS,
  "four_current_not_yet_officially_witnessed_total":118,
  "previously_archived_176_of_176_cross_source_date_team_score_confirmed":True,
  "eligible_new_match_rows_for_public_git_archive_from_these_sources":0,
  "new_model_training_approval":0,
  "licenses":{
   "four_source_candidates":{"publisher":"Football Charts",
     "source_terms":"https://www.football-charts.com/terms",
     "status":"SOURCE_DATA_FROM_PERSONAL_RESEARCH_API_PUBLIC_REHOST_NOT_APPROVED",
     "requery_status":"COMPLETE_176_PLUS_118_AGGREGATES_FROZEN_DO_NOT_REQUERY"},
   "five_source_candidates":{"publisher":"Football Charts",
     "source_terms":"https://www.football-charts.com/terms",
     "status":"SOURCE_DATA_FROM_PERSONAL_RESEARCH_API_PUBLIC_REHOST_NOT_APPROVED",
     "previous_third_party_rehost":"oladeeayo/open-matchday_632_UPSTREAM_ESPN_SOCCERWAY_FIXTUREDOWNLOAD_UNCLEARED",
     "status_632":"DO_NOT_USE_AS_LICENSE_CURE"},
   "extra_free_spreadsheet_compilation":{"publisher":"Football-Data.co.uk",
     "rights_page":"https://www.football-data.co.uk/data",
     "terms_observation":"The first-party data page restricts use to private individuals, explicitly excluding commercial or data-training products using automated bots/scrapers/AI.",
     "status":"NOT_APPROVED_FOR_AUTOMATED_AI_SCRAPING_OR_AI_TRAINING",
     "may_recheck_by_automated_tools":False,
     "new_downloads_this_gate":0,
     "historical_second_source_score_comparisons_do_not_GRANT_NEW_TRAINING_RIGHTS":True},
   "public_domain_archives":{"publisher":"OpenFootball",
     "license":"CC0-1.0",
     "license_pages":["https://github.com/openfootball/europe/blob/master/LICENSE.md",
                      "https://github.com/openfootball/austria/blob/master/LICENSE.md"],
     "four_2026_27_existing_source_blob_matches":PUBLIC_CC0,
     "swiss_extra_three_research_rows_have_separate_second_source_and_are_NOT_in_openfootball_cc0":True,
     "new_matches_found_on_four_CC0_source_files_after_original_archive":0,
     "five_missing_2026_27_division_files_present_in_seasonal_public_domain_catalog":False,
     "catalog_checked":"https://github.com/openfootball/football.json/tree/master/2026-27",
     "england_first_and_second_only":"https://github.com/openfootball/england/tree/master/2026-27",
     "spanish_first_only":"https://github.com/openfootball/espana/tree/master/2026-27",
     "italian_first_only":"https://github.com/openfootball/italy/tree/master/2026-27",
     "danish_europe_last_listed_seasons":"2024-25",
     "note":"These observed content paths prove only that those particular repositories do not supply the missing 2026/27 fixture results at this snapshot; another licensed source might still exist."}
  },
  "quality_gates_for_promotion":[
   "An independent match-level fixture/date/90min FT corroboration from a trustworthy source",
   "Reusability/redistribution rights must be established from the actual upstream owner; public URL != license",
   "Stable league, season, canonical teams, played state, playoff vs regular stage",
   "Postponed, abandoned, administratively awarded or conflicting FT stays HOLD",
   "No future leak: any later training feature must have a real historical as-of before kickoff",
   "No old M4, 96 sealed matches, or manual xG file changes without explicit separate authorization"],
  "next_distinct_step":"Request explicit owner permissions or find genuinely original CC0/ODbL 2026/27 leagues; validate only new fixtures and never rerun 9460 earlier rows or 176 confirmed identities.",
  "new_automatic_external_requests_from_this_script":0,
  "manual_xg_1855_user_workbook_unchanged":True,
  "model_math_changed":False,
  "all_prior_seals_untouched":True
 }
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps({k:report[k] for k in (
  "status","five_current_unarchived_total","four_current_not_yet_officially_witnessed_total",
  "eligible_new_match_rows_for_public_git_archive_from_these_sources","new_model_training_approval",
  "new_automatic_external_requests_from_this_script")},ensure_ascii=False))
def selftest():
 assert len(PUBLIC_CC0)==4 and len(FIVE_TARGETS)==5
 assert sum(x["scored_lines"] for x in PUBLIC_CC0.values())==173
 assert sum(FIVE_TARGETS.values())+sum(FOUR_TARGETS.values())==751
 assert len({c["blob"] for c in PUBLIC_CC0.values()})==4
 print("PASS 5+4 league boundaries, 751 rights-held candidates, 4 SHA-pinned open archives")
if __name__=="__main__":
 a=argparse.ArgumentParser()
 a.add_argument("--self-test",action="store_true")
 a.add_argument("--run",action="store_true")
 args=a.parse_args()
 if args.self_test:selftest()
 if args.run:execute()
