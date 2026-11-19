"""Private xG operational smoke: a sealed morning M4 forecast gets an external sidecar.

Tests only synthetic fixture evidence, no real odds, no retrospective SHA write.
"""
import csv
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from m4_integrated import score_markets
from m4_xg_support_263 import _sha
from sabah_batch_263 import run,sha
from test_sabah_workflow_263 import Acceptance,fake_predict,gate,fake_baseline,fake_decision


class PrivateXGTests(Acceptance):
    # Inherit the existing synthetic batch scaffold, plus real private xG I/O.
    def setUp(self):
        super().setUp()
        self.private=tempfile.TemporaryDirectory()
        self.private_file=Path(self.private.name)/"private.csv"
        self.private_report=Path(self.private.name)/"results"
        scores=[]
        xg=[]
        for i in range(80):
            day=f"2026-01-{1+i//28:02d}"
            home,away=("HomeID","AwayID") if i%2==0 else ("AwayID","HomeID")
            row={"fixture_id":f"id{i}","league":"TUR1","season":"2025-2026",
                 "match_date":day,"home_id":home,"away_id":away,
                 "home_goals":"1","away_goals":"0","result":"H"}
            scores.append(row)
            xg.append({"fixture_id":row["fixture_id"],"league":"TUR1","date":day,
                       "home_id":home,"away_id":away,
                       "home_goals":"1","away_goals":"0",
                       "home_xg":"1.7","away_xg":"0.6",
                       "xg_source":"xgEdge","source_status":"ONCEKI_VERIFIED"})
        def csv_save(p,rows):
            with p.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]))
                w.writeheader();w.writerows(rows)
        csv_save(Path("history.csv"),scores)
        csv_save(self.private_file,xg)
    def tearDown(self):
        self.private.cleanup()
        super().tearDown()
    def predictor(self,g,history,out_dir,lock,now=None,base=None,source_audit=None):
        path,forecast=fake_predict(g,history,out_dir,lock,now=now,base=base,
                                   source_audit=source_audit)
        forecast["data"]={"snapshot_sha256":_sha(history)}
        forecast["model_predictions"]["M4"]["goals"]=score_markets(1.1,1.0)
        payload={k:v for k,v in forecast.items() if k!="payload_sha256"}
        forecast["payload_sha256"]=sha(payload)
        path.write_text(json.dumps(forecast,sort_keys=True),encoding="utf-8")
        return path,forecast
    def run_once(self, xg_path,sha_value):
        from test_sabah_workflow_263 import NOW
        return run("new100","2026-11-07",self.manifest,
                   "history.csv","base.csv","acceptance.json","lock.json",
                   now=NOW,lookup=gate,predictor=self.predictor,
                   baseline_fn=fake_baseline,decision_fn=fake_decision,
                   dev_lock_path="lock.json",xg_snapshot=xg_path,
                   xg_expected_sha=sha_value,xg_private_dir=self.private_report)
    def test_private_sidecar_uses_xg_without_editing_seal(self):
        r=self.run_once(self.private_file,_sha(self.private_file))
        self.assertEqual(r["new_forecasts"],1)
        item=r["outcomes"][0]
        self.assertEqual(item["xg_status"],"XG_INCLUDED_IN_M4_RESEARCH_LAMBDA")
        self.assertEqual(r["xg_private_results"],1)
        evidence_files=list(self.private_report.rglob("*.json"))
        self.assertEqual(len(evidence_files),1)
        evidence=json.loads(evidence_files[0].read_text())
        sealed=json.loads(Path(item["forecast_path"]).read_text())
        self.assertEqual(evidence["forecast_sha256"],sealed["payload_sha256"])
        self.assertEqual(evidence["xg"]["markets"]["M4_original"],
                         sealed["model_predictions"]["M4"]["goals"]["markets"])
        self.assertNotEqual(evidence["xg"]["markets"]["M4_with_xg"]["OVER_2.5"],
                            evidence["xg"]["markets"]["M4_original"]["OVER_2.5"])
        self.assertNotIn("adjusted_lambdas",json.dumps(r))
        self.assertNotIn("home_xg",json.dumps(r))
        self.assertNotIn("away_xg",json.dumps(r))
        self.assertFalse(any(Path("experiments").rglob("m4_xg_evidence.json")))
    def test_invalid_sha_rejects_xg_preserves_sealed_forecast(self):
        r=self.run_once(self.private_file,"0"*64)
        self.assertEqual(r["new_forecasts"],1)
        self.assertEqual(r["xg_private_results"],0)
        self.assertEqual(r["outcomes"][0]["xg_status"],
                         "PRIVATE_XG_SOURCE_REJECTED_M4_UNCHANGED")
        self.assertFalse(self.private_report.exists())
    def test_public_repo_file_path_is_rejected(self):
        path=Path("sensitive-do-not-publish.csv")
        path.write_bytes(self.private_file.read_bytes())
        r=self.run_once(path,_sha(path))
        self.assertEqual(r["new_forecasts"],1)
        self.assertEqual(r["xg_private_results"],0)
        self.assertEqual(r["outcomes"][0]["xg_status"],
                         "PRIVATE_XG_SOURCE_REJECTED_M4_UNCHANGED")


if __name__=="__main__":
    unittest.main()
