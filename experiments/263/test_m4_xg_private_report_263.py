"""Private M4 xG reporting: secure as-of gates and unchanged SHA forecast."""
import csv
import datetime as dt
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from forward_c3 import canonical_bytes
from m4_integrated import score_markets
from m4_xg_support_263 import _sha
from m4_xg_private_report_263 import produce

NOW=dt.datetime(2026,11,19,18,0,tzinfo=dt.timezone.utc)

class PrivateReportSmoke(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        p=Path(self.tmp.name)
        self.repo=p/"public_repo"
        self.repo.mkdir()
        self.private=p/"private"
        self.private.mkdir()
        self.history=self.repo/"history.csv"
        self.xg=self.private/"data.csv"
        self.forecast=self.repo/"forward.json"
        self.output=self.private/"sidecar.json"
        rows=[];provider=[]
        for i in range(80):
            date=f"2026-01-{i//28+1:02d}"
            h,a=("H","A") if i%2==0 else ("A","H")
            row={"fixture_id":f"f{i}","league":"ENG1","season":"2025-2026","match_date":date,
                 "home_id":h,"away_id":a,"home_goals":"1","away_goals":"0","result":"H"}
            rows.append(row)
            provider.append({"fixture_id":row["fixture_id"],"league":"ENG1","date":date,
                             "home_id":h,"away_id":a,"home_goals":"1","away_goals":"0",
                             "home_xg":"1.8","away_xg":"0.8",
                             "xg_source":"Understat","source_status":"LEGACY_VERIFIED_2026_11_03"})
        for path,records in ((self.history,rows),(self.xg,provider)):
            with path.open("w",encoding="utf-8",newline="") as f:
                w=csv.DictWriter(f,fieldnames=list(records[0]))
                w.writeheader();w.writerows(records)
        baseline=score_markets(1.2,1.1)
        f={"schema":"quad_forward_263_v1",
           "created_at_utc":"2026-11-19T16:00:00+00:00",
           "fixture":{"fixture_verification":"VERIFIED_BY_LIVE_OFFICIAL_GATE",
                      "league":"ENG1","home_id":"H","away_id":"A",
                      "match_local_date":"2026-11-20",
                      "kickoff_utc":"2026-11-20T17:00:00+00:00"},
           "data":{"snapshot_sha256":_sha(self.history)},
           "model_predictions":{"M4":{"status":"AVAILABLE","goals":baseline}}}
        f["payload_sha256"]=hashlib.sha256(canonical_bytes(f)).hexdigest()
        self.forecast.write_text(json.dumps(f,sort_keys=True),encoding="utf-8")
        self.before=self.forecast.read_bytes()
    def tearDown(self):
        self.tmp.cleanup()
    def kwargs(self):
        return dict(forecast_path=self.forecast,history_path=self.history,
                    private_xg_path=self.xg,evidence_path=self.output,
                    expected_xg_sha=_sha(self.xg),now=NOW,public_repo_dir=self.repo)
    def test_real_scoring_math_and_seal_stays_unchanged(self):
        s=produce(**self.kwargs())
        self.assertIn("2.5 Üst",s)
        self.assertIn("KG Var",s)
        self.assertIn("M4 + geçmiş xG",s)
        self.assertEqual(self.forecast.read_bytes(),self.before)
        self.assertTrue(self.output.is_file())
        self.assertNotIn("1.8",s)
        self.assertEqual(json.loads(self.output.read_text())["xg"]["status"],
                         "XG_INCLUDED_IN_M4_RESEARCH_LAMBDA")
    def test_private_file_inside_public_repo_denied(self):
        kw=self.kwargs()
        kw["private_xg_path"]=self.history
        with self.assertRaisesRegex(ValueError,"INSIDE_PUBLIC_REPO"):
            produce(**kw)
        self.assertFalse(self.output.exists())
    def test_after_kickoff_denied(self):
        kw=self.kwargs();kw["now"]=dt.datetime(2026,11,20,18,tzinfo=dt.timezone.utc)
        with self.assertRaisesRegex(ValueError,"NOT_PREKICKOFF"):
            produce(**kw)
        self.assertFalse(self.output.exists())
    def test_hash_mismatch_denied(self):
        kw=self.kwargs();kw["expected_xg_sha"]="0"*64
        with self.assertRaisesRegex(ValueError,"SHA_MISMATCH"):
            produce(**kw)
        self.assertFalse(self.output.exists())
    def test_bad_fixture_gate_denied(self):
        f=json.loads(self.forecast.read_text())
        f["fixture"]["fixture_verification"]="NO_EVIDENCE"
        f["payload_sha256"]=hashlib.sha256(canonical_bytes({k:v for k,v in f.items() if k!="payload_sha256"})).hexdigest()
        self.forecast.write_text(json.dumps(f))
        with self.assertRaisesRegex(ValueError,"OFFICIAL_FIXTURE_GATE"):
            produce(**self.kwargs())
        self.assertFalse(self.output.exists())
    def test_wrong_history_denied(self):
        self.history.write_text(self.history.read_text()+"\n")
        with self.assertRaisesRegex(ValueError,"SCORE_HISTORY_SHA"):
            produce(**self.kwargs())
        self.assertFalse(self.output.exists())

if __name__=="__main__":
    unittest.main()
