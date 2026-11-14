#!/usr/bin/env python3
"""OFFLINE freeze and verify *only* 22 new playoff match-result facts.

Web evidence URLs were researched separately and pinned into an explicit,
small per-match fact ledger. This test does NOT fetch the independent pages,
does NOT re-run the previous 83 source comparisons or the older 1268
regular-season checks, does NOT import a secondary result database, and
NEVER approves model training or historical pre-match data availability.
"""
import csv,hashlib,json
from pathlib import Path
ROOT=Path("experiments/263/league_expansion")
DIR=ROOT/"ccby_footballcharts_2025_26_106_separate_secondary_phase"
WIT=DIR/"new22_playoff_specific_independent_FT_facts_20261114.csv"
QA=DIR/"new106_only_playoffs_and_second_phase_FT_second_witness_20261114.json"
PREV=DIR/"new106_fact_witness_83_exact_one_date_fix_22_uncovered_HOLD_20261114.json"
REPORT=DIR/"new106_second_phase_106_all_results_witnessed_20261114.json"
BLOBS={
"ENG3":("9ae856cbabee7d11d97e870bf77ac68600ed13cb",5),
"ENG4":("28a29e5f0782b2c72584a322a86bba78aad4afcd",4),
"ENG5":("065c51d70960942fa8f328853d0f377a2aa2bded",2),
"ITA2":("1ced7c836d57f8cc2db3d85b51cf4415cfed4a37",10),
"FRA2":("474815153537d43f660717a1a1c152baa52d7e55",1),
}
def gitsha(blob):return hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
def check():
 witness=list(csv.DictReader(WIT.open(encoding="utf-8",newline="")))
 report=json.loads(REPORT.read_text())
 prev=json.loads(PREV.read_text())
 qa=json.loads(QA.read_text())
 if len(witness)!=22 or qa["new_only_second_source_exact_same_date_home_away_FT"]!=83 or qa["new_only_second_source_missing_different_or_unavailable_HOLD"]!=23:
  raise ValueError("PRIOR_ONLY_83_23_SOURCE_FACT_GATE_CHANGED")
 if prev["other_no_secondary_playoff_coverage"]!=22 or prev["total_source_specific_research_match_identities"]!=4497:
  raise ValueError("PREVIOUS_22_HOLD_STATUS_CHANGED")
 if report["new_second_source_22_all_match_date_home_away_FT"]!=22 or report["new_model_training_approved"]!=0:
  raise ValueError("REPORT_CLAIMS_ARE_NOT_SAFE")
 all_keys=set();count=0
 for lg,(sha,n) in BLOBS.items():
  path=DIR/(lg.lower()+"_2025_26_SECOND_PHASE_ONLY_LICENSED_SOURCE_QA_PENDING.csv")
  contents=path.read_bytes()
  if gitsha(contents)!=sha:raise ValueError("SOURCE_ORIGINAL_BLOB_CHANGED_"+lg)
  original=list(csv.DictReader(contents.decode("utf-8-sig").splitlines()))
  evidence=[r for r in witness if r["league"]==lg]
  if len(original)!=n or len(evidence)!=n:raise ValueError("PER_LEAGUE_22_COUNT_CHANGED_"+lg)
  by_key={(r["date"],r["home"],r["away"]):r for r in evidence}
  if len(by_key)!=n:raise ValueError("EVIDENCE_DUPLICATE_KEYS_"+lg)
  for r in original:
   k=(r["date"],r["home"],r["away"])
   w=by_key.get(k)
   if w is None:raise ValueError("TARGET_FIXTURE_MISSING_"+lg+":"+str(k))
   if w["ft_home"]!=r["ft_home"] or w["ft_away"]!=r["ft_away"] or w["stage"]!=r["stage"]:
    raise ValueError("INDEPENDENT_WITNESS_CONFLICTS_WITH_SOURCE_"+lg+":"+str(k))
   if w["pinned_original_git_blob"]!=sha or w["season"]!="2025-26":
    raise ValueError("SOURCE_PROVENANCE_KEY_DRIFT")
   if not w["evidence_source_1_url"].startswith("https://") or not w["evidence_source_2_url"].startswith("https://"):
    raise ValueError("NO_TWO_SOURCE_URLS")
   if w["evidence_status"]!="MATCH_IDENTITY_AND_FINISHED_MATCH_SCORE_INDEPENDENTLY_CORROBORATED_NOT_TRAINING" or w["original_match_score_overridden"]!="NO":
    raise ValueError("UNSAFE_STAGE_FT_LABEL")
   marker=(lg,"2025-26",*k)
   if marker in all_keys:raise ValueError("DUPLICATE_GLOBAL_MATCH_KEY")
   all_keys.add(marker);count+=1
 if count!=22 or len(all_keys)!=22:raise ValueError("TWENTY_TWO_NOT_COMPLETE")
 if sum(report["source_current_rows_verified_by_league"].values())!=22:
  raise ValueError("PER_LEAGUE_TOTAL_UNEXPECTED")
 assert report["prior_8_cross_tier_source_records_HOLD_unchanged"] is True
 assert report["new_model_training_approved"]==0
 print("PASS 22 exact independent match fact witness identities, pinned old 83, original blobs unchanged; ZERO training admission")
if __name__=="__main__":check()
