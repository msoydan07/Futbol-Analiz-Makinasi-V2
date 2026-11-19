"""Private xG data audit and final M4 production decision; no xG data in repository."""
from __future__ import annotations
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from m4_xg_operational_gate_263 import private_data_preflight,promotion_gate,EXPECTED_SHA,TEN

class Gate(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.root=Path(self.d.name)
        self.public=self.root/"public";self.public.mkdir()
        self.private=self.root/"private";self.private.mkdir()
        self.xg=self.private/"xg.csv"
        rows=[]
        for i,l in enumerate(sorted(TEN)):
            rows.append(dict(fixture_id=f"ID{i}",league=l,date="2026-10-01",home_id="a",
                             away_id="b",home_goals="1",away_goals="0",
                             home_xg="1.3",away_xg="0.8",xg_source="xgEdge",
                             source_status="VERIFIED"))
        with self.xg.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        self.sha=hashlib.sha256(self.xg.read_bytes()).hexdigest()
        self.cal={"schema":"263_xg_1083_calibration_audit_v1","n":1083,
                  "source_sha256":EXPECTED_SHA,"details":{
                     "M4":{"brier":0.24773368147294106},
                     "M4_PLUS_XG":{"brier":0.24464868704059028,
                                   "ece_10":0.069028,"mean_p":0.54245,
                                   "actual_rate":0.600185}}}
    def tearDown(self):self.d.cleanup()
    def test_private_file_passes_and_no_raw_values_emitted(self):
        got=private_data_preflight(self.xg,self.public,self.sha,10)
        self.assertEqual(got["status"],"PRIVATE_XG_READABLE_IN_CHATGPT_ENVIRONMENT")
        self.assertEqual(got["record_count"],10)
        self.assertFalse(got["github_actions_ready"])
        self.assertNotIn("home_xg",json.dumps(got))
        self.assertNotIn("1.3",json.dumps(got))
    def test_wrong_hash_falls_back(self):
        got=private_data_preflight(self.xg,self.public,"0"*64,10)
        self.assertEqual(got["status"],"PRIVATE_XG_SHA_MISMATCH")
    def test_missing_file_falls_back(self):
        got=private_data_preflight(self.root/"missing.csv",self.public)
        self.assertEqual(got["status"],"PRIVATE_XG_NOT_AVAILABLE")
    def test_refuse_public_repo_source(self):
        p=self.public/"xg.csv";p.write_bytes(self.xg.read_bytes())
        with self.assertRaisesRegex(ValueError,"PUBLIC_CHECKOUT"):
            private_data_preflight(p,self.public,self.sha,10)
    def test_calibration_and_source_gates_explicit_hold(self):
        got=promotion_gate(self.cal)
        self.assertEqual(got["status"],"HOLD_KEEP_M4_OFFICIAL_UNCHANGED")
        self.assertIn("GOAL_2_5_MEAN_CALIBRATION_BIAS_TOO_LARGE",got["reasons"])
        self.assertIn("GOAL_2_5_BUCKET_RELIABILITY_NOT_YET_STRONG",got["reasons"])
        self.assertIn("NOT_VERIFIED_PROVIDER_PRE_MATCH_VINTAGE",got["reasons"])
        self.assertFalse(got["official_m4_modified"])
    def test_even_perfect_calibration_without_source_rights_holds(self):
        c=json.loads(json.dumps(self.cal))
        c["details"]["M4_PLUS_XG"]["mean_p"]=.60
        c["details"]["M4_PLUS_XG"]["ece_10"]=.01
        got=promotion_gate(c)
        self.assertEqual(got["status"],"HOLD_KEEP_M4_OFFICIAL_UNCHANGED")
        self.assertIn("NOT_VERIFIED_PROVIDER_USAGE_RIGHTS",got["reasons"])
    def test_audited_prerequisites_only_allow_review_not_auto_promotion(self):
        c=json.loads(json.dumps(self.cal))
        c["details"]["M4_PLUS_XG"]["mean_p"]=.60
        c["details"]["M4_PLUS_XG"]["ece_10"]=.01
        got=promotion_gate(c,historical_score_source_independently_verified=True,
          provider_vintage_asof_verified=True,rights_verified=True,
          new_unseen_prematch_evaluation=True)
        self.assertEqual(got["status"],"ALL_GATES_PASSED_REVIEW_REQUIRED")
        self.assertFalse(got["official_m4_modified"] or got["betting_authorized"])

if __name__=="__main__":unittest.main()
