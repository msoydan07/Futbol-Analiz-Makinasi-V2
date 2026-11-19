"""PDF-to-forecast xG sidecar routing; synthetic official fixture and private file."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from iddaa_pdf_session_263 import run_session
from test_iddaa_pdf_session_263 import row, source, NOW, real_official


class PDFPrivateXGBridgeTests(unittest.TestCase):
    def test_good_private_xg_path_after_a_verified_pdf_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            private=Path(d)/"private.csv"
            private.write_text("test-private-xg",encoding="utf-8")
            private_sha=hashlib.sha256(private.read_bytes()).hexdigest()
            output_dir=Path(d)/"private_sidecars"
            forecast_dir=Path(d)/"model_forecasts"
            def mock_forecaster(g, history, out_dir, lock, now=None, base=None,
                                source_audit=None):
                target=Path(out_dir)/"2026-11-11"/("a"*24+".json")
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_text('{"sealed":"untouched"}',encoding="utf-8")
                forecast={"fixture":{"match_local_date":"2026-11-11"},
                          "model_predictions":{},"payload_sha256":"a"*64}
                return target, forecast
            def mock_sidecar(f, history, private_xg, result):
                self.assertEqual(private_xg,private.resolve())
                self.assertFalse(result.is_relative_to(Path.cwd().resolve()))
                self.assertIn("private_sidecars",str(result))
                self.assertEqual(f.read_text(), '{"sealed":"untouched"}')
                result.parent.mkdir(parents=True,exist_ok=True)
                result.write_text('{"private_only":true}',encoding="utf-8")
                return {"xg":{"status":"XG_INCLUDED_IN_M4_RESEARCH_LAMBDA"}}
            options={"history":"not_used_for_test.csv","lock":"not_used_for_test.json",
                     "out_dir":str(forecast_dir),
                     "empirical_baseline_out_dir":str(Path(d)/"baselines"),
                     "xg_snapshot":str(private),"xg_expected_sha256":private_sha,
                     "xg_private_dir":str(output_dir)}
            with patch("forward_quad.predict_quad_from_verified_gate",side_effect=mock_forecaster):
                with patch("forward_empirical_baseline_263.produce",
                           return_value={"payload_sha256":"b"*64}):
                    with patch("m4_xg_support_263.sidecar",side_effect=mock_sidecar) as bridge:
                        result=run_session(source([row()]),now=NOW,official_lookup=real_official,
                                           forecast_options=options,max_workers=1)
            r=result["rows"][0]
            self.assertEqual(r["status"],"FOUR_MODELS_FORECAST_SHA_CREATED")
            self.assertEqual(r["m4_xg_status"],"XG_INCLUDED_IN_M4_RESEARCH_LAMBDA")
            self.assertTrue(r["m4_xg_seal_preserved"])
            self.assertEqual(bridge.call_count,1)
            self.assertNotIn("test-private-xg",json.dumps(result))
            self.assertNotIn("private_sidecars",json.dumps(result))
            self.assertEqual(len(list(output_dir.rglob("*.json"))),1)
    def test_wrong_xg_sha_does_not_block_original_pdf_m4(self):
        with tempfile.TemporaryDirectory() as d:
            private=Path(d)/"xg.csv";private.write_text("private",encoding="utf-8")
            def fake_predict(g,h,out_dir,lock,now=None,base=None,source_audit=None):
                target=Path(d)/"forecast.json"
                target.write_text("sealed",encoding="utf-8")
                return target,{"fixture":{"match_local_date":"2026-11-11"},
                               "model_predictions":{},"payload_sha256":"a"*64}
            options={"history":"history.csv","lock":"lock.json","out_dir":d,
                     "empirical_baseline_out_dir":str(Path(d)/"baseline"),
                     "xg_snapshot":str(private),"xg_expected_sha256":"0"*64,
                     "xg_private_dir":str(Path(d)/"private_out")}
            with patch("forward_quad.predict_quad_from_verified_gate",side_effect=fake_predict):
                with patch("forward_empirical_baseline_263.produce",
                           return_value={"payload_sha256":"b"*64}):
                    with patch("m4_xg_support_263.sidecar") as sidecar:
                        result=run_session(source([row()]),now=NOW,
                                           official_lookup=real_official,
                                           forecast_options=options,max_workers=1)
            r=result["rows"][0]
            self.assertEqual(r["status"],"FOUR_MODELS_FORECAST_SHA_CREATED")
            self.assertEqual(r["m4_xg_status"],"PRIVATE_XG_REJECTED_M4_UNCHANGED")
            self.assertEqual(sidecar.call_count,0)


if __name__=="__main__":unittest.main()
