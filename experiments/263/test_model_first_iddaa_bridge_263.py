"""Research-only PDF-first integration and non-price-decision tests.

All fixtures, odds and PDF bytes are synthetic. This is NOT live acceptance.
"""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from test_model_first_decision_263 import scenario
from model_first_iddaa_bridge_263 import calibrate_session
from iddaa_pdf_report_263 import _render_pick
from iddaa_pdf_one_step_263 import one_step

NOW=datetime(2026,11,21,10,5,tzinfo=timezone.utc)
ROOT=Path(__file__).resolve().parents[2]

def pair(price=1.8):
    f,b=scenario()
    row={"index":0,"status":"FOUR_MODELS_FORECAST_SHA_CREATED",
         "model_forecast_sha256":f["payload_sha256"],
         "empirical_baseline_sha256":b["payload_sha256"],
         "model_forecast_path":"test-forecast.json",
         "empirical_baseline_path":"test-baseline.json",
         "market_no_vig":{"MS":{"status":"FULL_MARKET_QUOTE_AVAILABLE",
                                 "prices":{"MS1":price,"MSX":4.0,"MS2":5.0},
                                 "no_vig":{"MS1":.55,"MSX":.25,"MS2":.20}}},
         "league":"TUR1"}
    pdf={"schema":"synthetic-not-real","pdf_sha256":"c"*64}
    session={"schema":"263_iddaa_pdf_first_official_gate_session_v1",
             "pdf_sha256":"c"*64,"source_bookmaker":"iddaa.com",
             "rows":[row],"pdf_capture_utc":"2026-11-21T09:00:00+00:00"}
    return f,b,pdf,session

class TestModelFirstIddaa(unittest.TestCase):
    def build(self,price=1.8):
        f,b,pdf,session=pair(price)
        with patch("model_first_iddaa_bridge_263.verify_original_pdf",return_value="c"*64):
            with patch("model_first_iddaa_bridge_263._load",side_effect=[f,b]), patch("model_first_iddaa_bridge_263.build_snapshot",return_value={"groups":{"MS":{"prices":{"MS1":price,"MSX":4.0,"MS2":5.0},"no_vig":{"MS1":.55,"MSX":.25,"MS2":.20}}}}):
                return calibrate_session(pdf,session,original_pdf="synthetic.pdf",
                    repo_root=str(ROOT),now=NOW)
    def test_no_price_dependent_decision(self):
        a=self.build(1.8);b=self.build(2.5)
        d1=a["rows"][0]["model_first_decision"]
        d2=b["rows"][0]["model_first_decision"]
        self.assertEqual(d1["payload_sha256"],d2["payload_sha256"])
        self.assertEqual(d1["main_candidate"]["market"],"MS1")
        self.assertEqual(d1["main_candidate"]["market"],d2["main_candidate"]["market"])
        self.assertNotEqual(a["rows"][0]["market_fifth_reference"]["payload_sha256"],
                            b["rows"][0]["market_fifth_reference"]["payload_sha256"])
    def test_new_report_displays_model_only(self):
        a=self.build()
        msg=_render_pick(a["rows"][0],a)
        self.assertIn("ANA (ORANDAN BAGIMSIZ)",msg)
        self.assertIn("IDDAA SADECE 5. REFERANS",msg)
    def test_block_not_silent_pas(self):
        f,b,pdf,session=pair()
        f["model_predictions"]["M4"]["status"]="UNAVAILABLE"
        from model_first_decision_263 import digest
        f["payload_sha256"]=digest({k:v for k,v in f.items() if k!="payload_sha256"})
        b["forecast_sha256"]=f["payload_sha256"]
        b["payload_sha256"]=digest({k:v for k,v in b.items() if k!="payload_sha256"})
        session["rows"][0]["model_forecast_sha256"]=f["payload_sha256"]
        session["rows"][0]["empirical_baseline_sha256"]=b["payload_sha256"]
        with patch("model_first_iddaa_bridge_263.verify_original_pdf",return_value="c"*64):
            with patch("model_first_iddaa_bridge_263._load",side_effect=[f,b]), patch("model_first_iddaa_bridge_263.build_snapshot",return_value={"groups":{"MS":{"prices":{"MS1":1.8,"MSX":4.0,"MS2":5.0},"no_vig":{"MS1":.55,"MSX":.25,"MS2":.20}}}}):
                result=calibrate_session(pdf,session,original_pdf="synthetic.pdf",
                     repo_root=str(ROOT),now=NOW)
        self.assertEqual(result["n_technical_blocked_not_pas"],1)
        self.assertIn("TEKNIK ENGEL",_render_pick(result["rows"][0],result))
    def test_fake_pdf_sha_prevents_bridge(self):
        f,b,pdf,session=pair()
        with patch("model_first_iddaa_bridge_263.verify_original_pdf",return_value="d"*64):
            with self.assertRaisesRegex(ValueError,"NOT_ORIGINAL_IDDAA"):
                calibrate_session(pdf,session,original_pdf="synthetic.pdf",
                     repo_root=str(ROOT),now=NOW)
    def test_cloned_entrypoint_does_not_call_legacy_decider(self):
        import inspect
        from iddaa_pdf_one_step_263 import one_step
        source=inspect.getsource(inspect.getmodule(one_step))
        self.assertIn("from model_first_iddaa_bridge_263 import calibrate_session",source)
        self.assertNotIn("from iddaa_pdf_value_bridge_263 import calibrate_session",source)

if __name__=="__main__":
    unittest.main(verbosity=2)
