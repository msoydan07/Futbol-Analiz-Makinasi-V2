#!/usr/bin/env python3
"""OFFLINE eight special-stage licensed match-fact witness ledger gate.

Only the 8 previously held results, not old 4,497 original fixture records.
Previous original HOLD is retained; classification and match factual evidence
are corrected, but training and pre-match availability remain forbidden.
"""
import csv,hashlib,json
from pathlib import Path
D=Path("experiments/263/league_expansion/ccby_footballcharts_2025_26_106_separate_secondary_phase")
OLD=D/"eight_interdivision_playoff_2025_26_HOLD_source_only.csv"
NEW=D/"eight_transition_specific_research_only_FT_witness_20261114.csv"
REPORT=D/"2025_26_eight_transition_stage_reclassified_and_facts_QA_20261114.json"
EXPECTED_SHA="a1c5b6c75c3dbf43a960d17d7bdbe10252846099"
EXPECT={
"FRA_NATIONAL_LIGUE2_PROMOTION_RELEGATION_BRIDGE":2,
"SCO_CHAMPIONSHIP_INTRA_TIER_PREMIERSHIP_PLAYOFF_QUALIFIER":4,
"SCO_CHAMPIONSHIP_PREMIERSHIP_CROSS_TIER_FINAL":2}
def sha(s):
 return hashlib.sha1(b"blob "+str(len(s)).encode()+b"\0"+s).hexdigest()
def main():
 raw=OLD.read_bytes()
 if sha(raw)!=EXPECTED_SHA:raise ValueError("ORIGINAL_HOLD_BLOB_DRIFT")
 old=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
 new=list(csv.DictReader(NEW.open(encoding="utf-8",newline="")))
 report=json.loads(REPORT.read_text())
 if len(old)!=8 or len(new)!=8 or report["match_fact_8_all_exact_date_teams_scores"]!=8:
  raise ValueError("EIGHT_ONLY_SCOPE_CHANGED")
 exact={(v["league"],v["season"],v["date"],v["source_home"],v["source_away"],v["ft_home"],v["ft_away"]) for v in old}
 if len(exact)!=8:raise ValueError("DUPLICATE_PRIOR_HOLD_IDENTITY")
 seen=set();stage={}
 for v in new:
  key=(v["league"],v["season"],v["date"],v["source_home"],v["source_away"],v["ft_home"],v["ft_away"])
  if key not in exact or key in seen:raise ValueError("CHANGED_OR_DUPLICATE_MATCH_SOURCE_KEY")
  seen.add(key)
  stage[v["competition_stage_id"]]=stage.get(v["competition_stage_id"],0)+1
  if v["model_training_approval"]!="NO" or v["historic_pre_kickoff_available_at_proven"]!="NO":
   raise ValueError("UNSAFE_TRAINING_OR_TIME_CLAIM")
  if not all(v[k].startswith("https://") for k in ("score_fact_source_official_url","score_fact_source_independent_url")):
   raise ValueError("NO_INDEPENDENT_URL_EVIDENCE")
  if v["original_quality_hold_source_blob"]!=EXPECTED_SHA:raise ValueError("OLD_SOURCE_NOT_PINNED")
 if stage!=EXPECT or report["stage_buckets"]!=EXPECT:raise ValueError("WRONG_POSTSEASON_COMPETITION_CLASSIFICATION")
 if report["new_source_specific_match_identities_all_2025_26"]!=4505 or report["newly_training_approved"]!=0:
  raise ValueError("INCORRECT_TOTAL_OR_TRAINING_APPROVAL")
 print("PASS eight exact source-held football outcomes identified + reclassified, six Scottish and two French, original untouched, no model training")
if __name__=="__main__":main()
