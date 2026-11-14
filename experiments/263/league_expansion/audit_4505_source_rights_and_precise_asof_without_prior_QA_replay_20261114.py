#!/usr/bin/env python3
"""One NEW dimension: 4,505-source rights + point-in-time input eligibility.

Offline; source SHA-pinned. REUSES previous passed score/identity reports
without rerunning second-source FT score checks, fixture schedule checks,
2025/26 cross-source dedup or forecast model. No old files mutated.
Outputs source-level aggregate evidence ONLY, never a training CSV or scores.
M4, 10 league signed results, 1855 manual xG workbook untouched.

Key distinctions:
  historical FINISHED fixture date != pre-kickoff feature observation time;
  kickoff_utc != source feature available_at;
  source_last_updated_at / archive_observed_at on completed result API
      != historical pre-kickoff observation proof;
  CC BY / CC0 / ODbL displayed source license != automatically cleared
      upstream terms, database combination, or betting deployment rights.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,datetime
from pathlib import Path
from collections import Counter,defaultdict
from prepare_2396_provenance_rights_quality_gate_20261114 import EXPECTED
from verify_4391_research_source_integrity_once import FILES
ROOT=Path("experiments/263/league_expansion")
OUT=ROOT/"4505_rights_provenance_and_pre_kickoff_asof_source_gate_20261114.json"
STAGE="ccby_footballcharts_2025_26_106_separate_secondary_phase/"
STAGE_SHA={
 "eng3":("9ae856cbabee7d11d97e870bf77ac68600ed13cb",5),
 "eng4":("28a29e5f0782b2c72584a322a86bba78aad4afcd",4),
 "eng5":("065c51d70960942fa8f328853d0f377a2aa2bded",2),
 "ita2":("1ced7c836d57f8cc2db3d85b51cf4415cfed4a37",10),
 "fra2":("474815153537d43f660717a1a1c152baa52d7e55",1),
 "gre1":("7bd67debffc2c317b7fcce1bc06293f8d2b17c6c",54),
 "sco1":("90db060fb3e4ebf9dba087d88555c4e74a4244da",30)
}
TRANSITION=STAGE+"eight_transition_specific_research_only_FT_witness_20261114.csv"
TRANSITION_SHA=("94b8dcadc96f3f4eb1a72e9c99b8ac2c854e4a23",8)
def gitsha(b):
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def all_inputs():
 source={}
 for name,(sha,n,rights) in EXPECTED.items():
  source[name]=(sha,n,"ORIGINAL_BASE",rights)
 for name,(sha,n) in FILES.items():
  rights=("PUBLISHER_ODBL_RESEARCH_ONLY" if name.startswith("odbl_")
          else "PUBLISHER_CC_BY_ORIGINAL_RESEARCH_ONLY")
  source[name]=(sha,n,"NEW_SOURCE_1995",rights)
 for name,(sha,n) in STAGE_SHA.items():
  p=STAGE+name+"_2025_26_SECOND_PHASE_ONLY_LICENSED_SOURCE_QA_PENDING.csv"
  source[p]=(sha,n,"SEPARATE_PHASE_106","PUBLISHER_CC_BY_ORIGINAL_RESEARCH_ONLY")
 source[TRANSITION]=(*TRANSITION_SHA,"TRANSITION_8","PUBLISHER_CC_BY_ORIGINAL_RESEARCH_ONLY")
 if len(source)!=26:raise ValueError("WRONG_SOURCE_FILE_COUNT")
 return source
def utc(value):
 if not isinstance(value,str) or not value:return None
 try:
  x=datetime.datetime.fromisoformat(value.replace("Z","+00:00"))
  if not x.tzinfo or x.utcoffset() is None:return None
  return x.astimezone(datetime.timezone.utc)
 except (ValueError,TypeError):return None
def eligible_feature_snapshot(record):
 """Explicit feature snapshot proof, never retro-infer from finished result."""
 required=("target_kickoff_utc","snapshot_observed_at_utc",
           "feature_available_at_utc","source_result_completed_at_utc",
           "rights_for_this_feature","feature_scope","feature_field",
           "source_proof_ref")
 if any(not record.get(k) for k in required):return False,"MISSING_EXPLICIT_FEATURE_SNAPSHOT_PROOF"
 if record["rights_for_this_feature"]!="TRAINING_USE_LICENSE_VERIFIED":
  return False,"SOURCE_USE_RIGHTS_UNVERIFIED"
 if record["feature_scope"]!="PRIOR_MATCH_RESULT_ONLY":
  return False,"TARGET_MATCH_OR_POSTMATCH_SCOPE"
 if record["feature_field"] not in ("prior_ft_home","prior_ft_away","prior_home_pts",
                                    "prior_away_pts","prior_team_goals_for","prior_team_goals_against"):
  return False,"UNSAFE_OR_UNKNOWN_INPUT_FIELD"
 if not str(record["source_proof_ref"]).startswith("https://"):
  return False,"SOURCE_PROOF_REFERENCE_MISSING"
 kickoff=utc(record["target_kickoff_utc"])
 seen=utc(record["snapshot_observed_at_utc"])
 available=utc(record["feature_available_at_utc"])
 completed=utc(record["source_result_completed_at_utc"])
 if any(x is None for x in (kickoff,seen,available,completed)):
  return False,"TIMESTAMP_TZ_INVALID"
 if not completed<=available<=seen<kickoff:
  return False,"NOT_OBSERVED_AVAILABLE_BEFORE_TARGET_KICKOFF"
 if completed>kickoff-datetime.timedelta(hours=48):
  return False,"PREVIOUS_MATCH_RESULT_NOT_TWO_DAYS_OLD"
 return True,"PASS_EXPLICIT_ASOF_AND_RIGHTS_GATE_ONLY"
def classify():
 ledger=json.loads((ROOT/"research_historical_4391_distinct_source_accounting_20261114.json").read_text())
 stage=json.loads((ROOT/STAGE/"2025_26_106_second_phase_8_cross_tier_source_gate_20261114.json").read_text())
 bridge=json.loads((ROOT/STAGE/"2025_26_eight_transition_stage_reclassified_and_facts_QA_20261114.json").read_text())
 prev=json.loads((ROOT/"2396_296_hold_rights_and_feature_vintage_final_20261114.json").read_text())
 if ledger["status"]!="PASS_4391_UNIQUE_HISTORIC_RESEARCH_FIXTURES_CROSS_SOURCE_QA" or ledger["research_league_fixture_records"]!=4391:
  raise ValueError("OLDER_FINAL_IDENTITY_REPORT_CHANGED")
 if stage["new_2025_26_additional_stage_research_source_match_identities"]!=106 or bridge["match_fact_8_all_exact_date_teams_scores"]!=8:
  raise ValueError("OLDER_SECOND_STAGE_REPORTS_NOT_PROVEN")
 if prev["pool_scored_quarantine"]!=2396 or prev["disjoint_partitions"]["prior_eng3_eng4_source_quality_holds"]!=200 or prev["disjoint_partitions"]["new_eng5_original_score_date_quality_holds"]!=96:
  raise ValueError("BASELINE_HOLD_REPORT_CHANGED")
 right=Counter();segment=Counter();field_presence=Counter();by_file=[];total=0
 for path,(sha,n,part,rights) in all_inputs().items():
  binary=(ROOT/path).read_bytes()
  if gitsha(binary)!=sha:raise ValueError("IMMUTABLE_SOURCE_BLOB_CHANGED: "+path)
  with (ROOT/path).open(encoding="utf-8-sig",newline="") as f:
   reader=csv.DictReader(f)
   keys=reader.fieldnames or []
   if not {"league","season","date","ft_home","ft_away"}.issubset(keys):
    raise ValueError("SOURCE_SCORE_IDENTITY_COLUMN_CHANGED: "+path)
   rows=list(reader)
  if len(rows)!=n:raise ValueError("IMMUTABLE_SOURCE_COUNT_CHANGED: "+path)
  segment[part]+=n;right[rights]+=n;total+=n
  feature_keys=[k for k in keys if k in ("snapshot_observed_at_utc","feature_available_at_utc",
                                        "target_kickoff_utc","rights_for_this_feature","feature_scope")]
  observed_archive=sum(bool(r.get("archive_observed_at_utc")) for r in rows)
  kickoff=sum(bool(r.get("kickoff_utc")) for r in rows)
  field_presence["original_kickoff_time_metadata_only"]+=kickoff
  field_presence["posthoc_result_archive_receipt_metadata_only"]+=observed_archive
  eligible=0
  if all(k in keys for k in ("snapshot_observed_at_utc","feature_available_at_utc",
                             "target_kickoff_utc","rights_for_this_feature","feature_scope")):
   for r in rows:
    good,_=eligible_feature_snapshot(r)
    eligible+=int(good)
  field_presence["explicit_precise_prematch_input_proof_present"]+=eligible
  by_file.append({"path":path,"source_git_blob_sha":sha,"research_rows":n,
                  "group":part,"rights_status":rights,
                  "schema_pre_kickoff_feature_proof_keys_present":feature_keys,
                  "kickoff_metadata_nonproof_rows":kickoff,
                  "postmatch_archive_receipt_nonproof_rows":observed_archive,
                  "training_admitted":eligible})
 if total!=4505 or segment!=Counter({"ORIGINAL_BASE":2396,"NEW_SOURCE_1995":1995,
                                     "SEPARATE_PHASE_106":106,"TRANSITION_8":8}):
  raise ValueError("TOTAL_4505_RESEARCH_SOURCE_COUNT_DRIFT")
 assert sum(right.values())==4505
 if field_presence["explicit_precise_prematch_input_proof_present"]!=0:
  raise ValueError("NEW_UNREVIEWED_TRAINING_ADMISSION_MUST_NOT_HAPPEN")
 expected_right=Counter({
  "PUBLISHER_CC0_CLAIM":2071,
  "CCBY_COMPILATION_UPSTREAM_UNCLEAR":322,
  "THIRD_PARTY_REHOST_UNCLEARED":3,
  "PUBLISHER_ODBL_RESEARCH_ONLY":467,
  "PUBLISHER_CC_BY_ORIGINAL_RESEARCH_ONLY":1642
 })
 if right!=expected_right:raise ValueError("RIGHTS_CLASSIFICATION_COUNT_DRIFT: "+str(right))
 return {
  "checked_on":"2026-11-14",
  "status":"PASS_4505_LICENSE_AND_ASOF_SOURCE_INVENTORY_ZERO_UNPROVEN_TRAINING_ADMISSIONS",
  "frozen_historical_source_only_fixture_identities":4505,
  "source_files_examined_offline":len(by_file),
  "disjoint_source_groups":dict(segment),
  "source_rights_advertised_not_training_permission":dict(right),
  "source_metadata_nonproof_count":dict(field_presence),
  "newly_promoted_to_training":0,
  "prior_baseline_exact_296_quality_holds_unchanged":True,
  "additional_FRA2_2025_12_05_false_completed_0_0_already_held":True,
  "research_source_labels_not_quality_or_asof_approval":True,
  "new_633_personal_API_2026_27_raw_match_rows_persisted":0,
  "historic_2026_27_5_leagues_personal_API_rights_separate":True,
  "training_decision":"FAIL_CLOSED_ALL_EXISTING_SOURCES_LACK_EXPLICIT_HISTORICAL_PRE_KICKOFF_FEATURE_SNAPSHOTS",
  "old_match_score_FT_QA_workflows_reexecuted":0,
  "old_4391_independent_source_result_facts_rechecked":0,
  "no_existing_training_m4_predictions_xg_files_modified":True,
  "model_fit_or_prediction_runs":0,
  "necessary_future_receipt_fields":[
   "target_kickoff_utc","snapshot_observed_at_utc","feature_available_at_utc",
   "source_result_completed_at_utc","rights_for_this_feature","feature_scope",
   "feature_field","source_proof_ref"
  ],
  "explicit_admission_rule":"Source result must be from a distinct prior fixture completed >48h before target; actual available-at <= independently observed-at < real target kickoff UTC; training license verified; never target outcome, contemporaneous xG, or forecast labels.",
  "rights_safeguard":"CC0/CC BY/ODbL provider claim is a separate dimension from upstream provider rights, rights to train, data reuse conditions and historic availability. No retroactive fake observation timestamps.",
  "source_files":by_file,
  "next_distinct":"Starting with future match-days, capture auditable provider feature snapshots with real UTC receipts and source training permission. Existing 4505 historical result-only research cases can be used for score QA, NOT declared contemporaneously snapshotted training features. No repeat source QA."
 }
def selftest():
 base={
  "target_kickoff_utc":"2026-11-14T20:00:00+03:00",
  "snapshot_observed_at_utc":"2026-11-14T16:00:00+00:00",
  "feature_available_at_utc":"2026-11-14T15:59:00Z",
  "source_result_completed_at_utc":"2026-11-10T22:00:00Z",
  "rights_for_this_feature":"TRAINING_USE_LICENSE_VERIFIED",
  "feature_scope":"PRIOR_MATCH_RESULT_ONLY",
  "feature_field":"prior_team_goals_for",
  "source_proof_ref":"https://example.org/snapshot/123"
 }
 yes,reason=eligible_feature_snapshot(base)
 assert yes,reason
 for change in [
   {"snapshot_observed_at_utc":""},
   {"feature_available_at_utc":"2026-11-14T18:00:00Z"},
   {"source_result_completed_at_utc":"2026-11-14T15:00:00Z"},
   {"source_result_completed_at_utc":"2026-11-14T21:00:00Z"},
   {"feature_scope":"TARGET_MATCH_RESULT"},
   {"feature_field":"ft_home"},
   {"rights_for_this_feature":"ODbL_1_0_SOURCE_ONLY"},
   {"target_kickoff_utc":"2026-11-14T20:00:00"},
   {"snapshot_observed_at_utc":"2026-11-14T17:10:00Z"},
   {"source_proof_ref":""}
 ]:
  obj={**base,**change}
  ok,why=eligible_feature_snapshot(obj)
  assert not ok,(change,why)
 assert len(all_inputs())==26
 print("PASS synthetic valid historical receipt and 10 leak/rights blockers; previous QA not rerun")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--report",action="store_true")
 args=p.parse_args()
 if args.self_test:selftest()
 if args.report:
  data=classify()
  OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
  print("RIGHTS_ASOF_4505_BEGIN")
  print(json.dumps({"status":data["status"],"rows":data["frozen_historical_source_only_fixture_identities"],
       "rights":data["source_rights_advertised_not_training_permission"],
       "training":data["newly_promoted_to_training"]},ensure_ascii=False))
  print("RIGHTS_ASOF_4505_END")
