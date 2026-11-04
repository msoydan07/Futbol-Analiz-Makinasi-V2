"""Only new machine-stage research mode tests, no re-training/re-fit."""
import copy
import json
import tempfile
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from weekend_shadow_source_263 import verify_shadow_evidence,SHA,CODES

NOW=datetime(2026,11,4,10,tzinfo=timezone.utc)
class ShadowEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/"preflight_report.json"
  self.report={
   "schema":"263_weekend_source_live_fetch_preflight_v1",
   "status":"STAGED_UNVERIFIED_HUMAN_ACCEPTANCE_REQUIRED",
   "source_status":"STAGED_UNVERIFIED_SOURCE_FILES",
   "snapshot_sha256":SHA,
   "human_source_acceptance_completed":False,
   "independent_official_result_verification_completed":False,
   "model_pilot_unlocked":False,
   "source_files_cross_checked_against_receipts":True,
   "newly_added_versus_old_4501":8,
   "created_at_utc":"2026-11-04T09:00:00+00:00",
   "append_only_proof":{
    "prior_4501_sha":"279cb00096da270f6987ae9e518fbe7248c17c993c34508499a971cae76ca4e8",
    "prior_4501_unchanged":4501,
    "new_snapshot_sha":SHA,"new_snapshot_rows":4509},
   "10_source_receipts":{lg:{"league":lg,"url":"https://www.football-data.co.uk/mmz4281/2627/"+code+".csv",
                             "http_status":200,
                             "independently_checked_against_official_federation":False,
                             "bytes":1500,"sha256":"a"*64} for lg,code in CODES.items()},
  }
  self.save()
 def save(self):
  self.path.write_text(json.dumps(self.report),encoding="utf-8")
 def go(self,sha=SHA,n=4509,now=NOW):
  return verify_shadow_evidence(sha,n,self.path,now)
 def test_valid_machine_stage_not_human(self):
  self.assertIn("NOT_HUMAN",self.go())
 def test_bad_sha(self):
  with self.assertRaisesRegex(ValueError,"exact_nov4"):self.go(sha="0"*64)
 def test_bad_rows(self):
  with self.assertRaisesRegex(ValueError,"exact_nov4"):self.go(n=4508)
 def test_false_human_attestation(self):
  self.report["human_source_acceptance_completed"]=True;self.save()
  with self.assertRaisesRegex(ValueError,"not_machine_preflight"):self.go()
 def test_must_have_ten_source_receipts(self):
  self.report["10_source_receipts"].pop("TUR1");self.save()
  with self.assertRaisesRegex(ValueError,"ten_provider"):self.go()
 def test_wrong_provider_host(self):
  self.report["10_source_receipts"]["TUR1"]["url"]="https://fakedata.invalid/T1.csv";self.save()
  with self.assertRaisesRegex(ValueError,"bad_provider_receipt"):self.go()
 def test_expired_source_receipt(self):
  with self.assertRaisesRegex(ValueError,"expired"):self.go(now=NOW+timedelta(days=8))
 def test_future_source_receipt(self):
  with self.assertRaisesRegex(ValueError,"expired"):self.go(now=NOW-timedelta(days=1))
 def test_immutable_old_rows_required(self):
  self.report["append_only_proof"]["prior_4501_unchanged"]=4500;self.save()
  with self.assertRaisesRegex(ValueError,"append_only"):self.go()

if __name__=="__main__":unittest.main()
