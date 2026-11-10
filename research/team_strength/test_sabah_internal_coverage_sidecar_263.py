"""A separate sidecar must NEVER modify probability, UI or source SHA seals."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sabah_internal_coverage_sidecar_263 import (
  report_and_receipt,SidecarBlocked)
from team_coverage_audit_263 import ROOT,EXPECTED
sys.path.insert(0,str(ROOT/"experiments/263"))
from sabah_batch_263 import sha
from sabah_new100_commit_guard_263 import RECEIPT

class SilentSidecarTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.day="2026-11-11"
        self.rel=f"forward_morning_263/{self.day}/"+("a"*24)+".json"
        self.fpath=self.root/self.rel
        self.fpath.parent.mkdir(parents=True,exist_ok=True)
        self.forecast={
            "schema":"quad_forward_263_v1",
            "created_at_utc":"2026-11-11T10:00:00+00:00",
            "fixture":{
                "league":"ENG1","home_id":"UNKNOWN_TEAM_INTERNAL_ID",
                "away_id":"EXISTING_OTHER_INTERNAL_ID",
                "kickoff_utc":"2026-11-11T19:00:00+00:00",
                "match_local_date":self.day,
                "fixture_verification":"VERIFIED_BY_LIVE_OFFICIAL_GATE",
            },
            "data":{"snapshot_sha256":EXPECTED["source_4617"]},
            "model_predictions":{"M4":{"status":"AVAILABLE","goals":{"lambda_home":1.25,"lambda_away":.85}}}
        }
        self.forecast["payload_sha256"]=sha(self.forecast)
        self.fpath.write_text(json.dumps(self.forecast),encoding="utf-8")
        self.report={
            "schema":"SABAH_TOPLU_KAYIT_V1","cohort":"new100",
            "day_turkey":self.day,"betting_authorized":False
        }
        self.report["payload_sha256"]=sha(self.report)
        self.receipt={
            "schema":RECEIPT,"cohort":"new100",
            "betting_authorized":False,"batch_report_sha256":self.report["payload_sha256"],
            "new_count":1,
            "records":[{
               "forecast_path":self.rel,
               "forecast_sha256":self.forecast["payload_sha256"],
               "league":"ENG1","kickoff_utc":"2026-11-11T19:00:00+00:00",
            }]
        }
        self.receipt["payload_sha256"]=sha(self.receipt)
        self.rpath=self.root/"report.json"
        self.cpath=self.root/"receipt.json"
        self.write()
    def write(self):
        self.rpath.write_text(json.dumps(self.report),encoding="utf-8")
        self.cpath.write_text(json.dumps(self.receipt),encoding="utf-8")
    def calc(self):
        return report_and_receipt(self.root,self.rpath,self.cpath,ROOT)
    def test_readonly_internal_flag_does_not_change_forecast_or_receipt(self):
        before={x:x.read_bytes() for x in (self.rpath,self.cpath,self.fpath)}
        r=self.calc()
        self.assertEqual(r["status"],"BACKGROUND_READ_ONLY_RESEARCH_NOT_USER_VIEW")
        self.assertEqual(r["new_forecast_count"],1)
        self.assertEqual(r["outcome_count_with_unseen_team"],1)
        self.assertTrue(r["engineering_heuristic_not_empirical_trust_grade"])
        self.assertFalse(r["forecast_percentages_modified"])
        self.assertFalse(r["model_coefficients_modified"])
        self.assertFalse(r["forecast_receipts_modified"])
        self.assertFalse(r["mobile_report_modified"])
        self.assertEqual(r["odds_query_count"],0)
        self.assertEqual(before,{x:x.read_bytes() for x in before})
    def test_unsealed_receipt_fails_without_best_effort_false_report(self):
        self.receipt["new_count"]=2
        self.write()
        with self.assertRaisesRegex(SidecarBlocked,"TAMPERED_RECEIPT_SHA"):
            self.calc()
    def test_receipt_wrong_forecast_sha_is_rejected(self):
        self.receipt["records"][0]["forecast_sha256"]="e"*64
        self.receipt["payload_sha256"]=sha({k:v for k,v in self.receipt.items() if k!="payload_sha256"})
        self.write()
        with self.assertRaisesRegex(SidecarBlocked,"FORECAST_SHA_WRONG"):
            self.calc()
    def test_forecast_probabilities_changed_after_seal_are_rejected(self):
        self.forecast["model_predictions"]["M4"]["goals"]["lambda_home"]=4.2
        self.fpath.write_text(json.dumps(self.forecast),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"SHA"):
            self.calc()
    def test_wrong_model_data_sha_denied(self):
        self.forecast["data"]["snapshot_sha256"]="0"*64
        self.forecast["payload_sha256"]=sha({k:v for k,v in self.forecast.items() if k!="payload_sha256"})
        self.fpath.write_text(json.dumps(self.forecast),encoding="utf-8")
        self.receipt["records"][0]["forecast_sha256"]=self.forecast["payload_sha256"]
        self.receipt["payload_sha256"]=sha({k:v for k,v in self.receipt.items() if k!="payload_sha256"})
        self.write()
        with self.assertRaisesRegex(SidecarBlocked,"NOT_4617_TRAINING_INPUT"):
            self.calc()
    def test_path_traversal_is_rejected(self):
        self.receipt["records"][0]["forecast_path"]="../../secret"
        self.receipt["payload_sha256"]=sha({k:v for k,v in self.receipt.items() if k!="payload_sha256"})
        self.write()
        with self.assertRaisesRegex(SidecarBlocked,"UNSAFE_FORECAST_PATH"):
            self.calc()

if __name__=="__main__":
    unittest.main()
