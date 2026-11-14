#!/usr/bin/env python3
"""Second source FT facts for ONLY 106 newly archived 2025/26 second-phase
matches (playoffs, second-stage groups, Scottish top/bottom split).

No old 1,268, 1,775, 461 score matches are rechecked. Uses existing
one-read-per-target-league comparison helpers, but replaces their target
scope with these 106 *new* fixture IDs. The source publisher's CSV is
never redistributed; only one SHA hash per second source is retained.
No model training or pre-match vintage claims.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from verify_1269_NEW_only_scored_FT_second_source_once import compare,get,SECONDARY
from verify_4391_research_source_integrity_once import blob_sha
ROOT=Path("experiments/263/league_expansion")
FOLDER=ROOT/"ccby_footballcharts_2025_26_106_separate_secondary_phase"
FINAL=FOLDER/"new106_only_playoffs_and_second_phase_FT_second_witness_20261114.json"
FILES={
 "ENG3":("9ae856cbabee7d11d97e870bf77ac68600ed13cb",5),
 "ENG4":("28a29e5f0782b2c72584a322a86bba78aad4afcd",4),
 "ENG5":("065c51d70960942fa8f328853d0f377a2aa2bded",2),
 "ITA2":("1ced7c836d57f8cc2db3d85b51cf4415cfed4a37",10),
 "FRA2":("474815153537d43f660717a1a1c152baa52d7e55",1),
 "GRE1":("7bd67debffc2c317b7fcce1bc06293f8d2b17c6c",54),
 "SCO1":("90db060fb3e4ebf9dba087d88555c4e74a4244da",30)
}
def new_only(lg):
 p=FOLDER/(lg.lower()+"_2025_26_SECOND_PHASE_ONLY_LICENSED_SOURCE_QA_PENDING.csv")
 raw=p.read_bytes()
 sha,n=FILES[lg]
 if blob_sha(raw)!=sha:raise ValueError("NEW_PHASE_RESEARCH_SOURCE_BLOB_CHANGED_"+lg)
 items=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
 if len(items)!=n or {x["league"] for x in items}!={lg} or {x["season"] for x in items}!={"2025-26"}:
  raise ValueError("SOURCE_MATCH_COUNT_OR_SEASON_DRIFT")
 if any(not x["stage"] for x in items):raise ValueError("MISSING_SEGREGATED_STAGE_TAG")
 return items,sha
def audit():
 groups={};tot=Counter()
 for lg,division in SECONDARY.items():
  source,original_blob=new_only(lg)
  url=f"https://www.football-data.co.uk/mmz4281/2526/{division}.csv"
  try:
   data=get(url)
   verdict=compare(lg,data,source)
   verdict.update({
    "status":"SOURCE_FACT_CHECK_FINISHED_FOR_ONLY_NEW_PHASE_KEYS",
    "pinned_original_Git_Blob":original_blob,
    "second_result_source_url":url,
    "second_source_SHA256":hashlib.sha256(data).hexdigest(),
    "second_source_raw_tables_archived":False,
    "previously_certified_normal_source_match_ids_retested":0
   })
  except Exception as e:
   verdict={
    "status":"SECOND_SOURCE_UNAVAILABLE_OR_ALIAS_REQUIRES_EXPLICIT_HOLD",
    "pinned_original_Git_Blob":original_blob,
    "new_targeted_keys":len(source),
    "score_verified":0,
    "not_exactly_corrobated":len(source),
    "error_class":type(e).__name__,
    "reason":str(e)[:170] if isinstance(e,ValueError) else "HTTP or provider unavailable",
    "previously_certified_normal_source_match_ids_retested":0
   }
  if verdict["score_verified"]+verdict["not_exactly_corrobated"]!=len(source):
   raise ValueError("FINAL_SOURCE_WITNESS_COUNT_DRIFT_"+lg)
  tot["checked"]+=len(source)
  tot["exact"]+=verdict["score_verified"]
  tot["hold"]+=verdict["not_exactly_corrobated"]
  groups[lg]=verdict
 if tot["checked"]!=106 or tot["exact"]+tot["hold"]!=106:
  raise ValueError("TARGETED_106_ONLY_COUNTS_DRIFT")
 return {
  "status":"TARGET_ONLY_106_SEPARATE_SECOND_PHASE_FT_FACT_QA_FINISHED_PER_LEAGUE",
  "checked_at_utc":datetime.now(timezone.utc).isoformat(),
  "original_license":"CC BY 4.0 Football Charts (original 2025/26 season snapshot)",
  "original_reference":"https://doi.org/10.5281/zenodo.22295583",
  "new_only_second_phase_fixture_keys_checked":tot["checked"],
  "new_only_second_source_exact_same_date_home_away_FT":tot["exact"],
  "new_only_second_source_missing_different_or_unavailable_HOLD":tot["hold"],
  "by_league":groups,
  "earlier_4391_plus_new_106_separate_phase_research_identifiers":4497,
  "previous_result_fact_verifications_rerun":0,
  "old_FRA2_Bastia_abandoned_and_ENG5_technical_award_unaffected":True,
  "eight_cross_tier_transition_matches_still_HOLD":True,
  "full_external_source_match_table_republished":False,
  "historic_feature_asof_and_upstream_rights_certified":False,
  "model_training_rows_approved":0,
  "M4_10leagues_predictive_output_or_xG_excel_edited":False,
  "next_distinct_task":"Resolve ONLY phase fixtures that have missing second-source confirmation; keep all exact source-witness successes frozen. Original five 2026/27 rights-clean missing groups remain on source-rights HOLD."
 }
def test():
 assert sum(v for sha,v in FILES.values())==106
 for lg in FILES:
  assert lg in SECONDARY
  new_only(lg)
 print("PASS only 106 new stage source IDs; no old 4391 result source comparisons")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true")
 a=p.parse_args()
 if a.self_test:test()
 if a.run:
  try:d=audit()
  except Exception as e:d={"status":"FAIL_CLOSED_106_SECOND_SOURCE_FACT_QA",
   "error":str(e)[:250],"model_training_rows_approved":0}
  print("NEW_PHASE_106_QA_START")
  print(json.dumps(d,ensure_ascii=False,indent=2))
  print("NEW_PHASE_106_QA_END")
