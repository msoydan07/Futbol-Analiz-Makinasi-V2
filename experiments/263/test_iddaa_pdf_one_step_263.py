"""One command black-white PDF; mock fixture history explicitly synthetic."""
import hashlib,copy,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
from iddaa_pdf_one_step_263 import one_step
from test_iddaa_pdf_first_value_bridge_263 import sample,NOW

class OneStepTests(unittest.TestCase):
    def test_one_pdf_one_report_no_new_odds_api_or_extra_user_input(self):
        _,_,_,bulletin,_=sample()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            src=root/"iddaa_original.pdf"
            src.write_bytes(b"test-only fake-pdf bytes; parser mocked")
            digest=hashlib.sha256(src.read_bytes()).hexdigest()
            bulletin["pdf_sha256"]=digest
            bulletin["total_visible_fixtures"]=1
            bulletin["potential_ten_league_rows"]=1
            history=root/"history.csv"
            history.write_text("fixture_id,league,match_date\n",encoding="utf-8")
            def official(home,away):
                return {"status":"VERIFIED_OFFICIAL_FIXTURE",
                        "home":home,"away":away,
                        "kickoff_utc":"2026-11-06T17:00:00+00:00",
                        "retrieved_at_utc":"2026-11-06T16:02:00+00:00",
                        "source_url":"https://www.tff.org/fikstur"}
            with patch("iddaa_pdf_one_step_263.parse_pdf",return_value=bulletin):
                with patch("iddaa_pdf_value_bridge_263.verify_original_pdf",
                           return_value=digest):
                    output=one_step(src,history=history,
                       output_root=root/"results",official_lookup=official,
                       now=NOW,repo_root=".")
            self.assertTrue(Path(output["pdf_report_path"]).is_file())
            self.assertTrue((Path(output["processing_folder"])/
                              "iddaa_original_user.pdf").is_file())
            self.assertEqual(output["pdf_sha256"],digest)
            self.assertEqual(output["source_rows"],1)
            self.assertEqual(output["official_confirmed_rows"],1)
            self.assertEqual(output["signed_four_model_forecasts"],0)
            self.assertEqual(output["calibrated_price_decisions"],0)
            self.assertTrue(output["no_bookmaker_api_calls"])
            self.assertTrue(output["no_old_pilot_changes"])
            import fitz
            with fitz.open(output["pdf_report_path"]) as pdf:
                content=" ".join(pg.get_text() for pg in pdf)
            self.assertIn("Besiktas JK",content)
            self.assertIn("MS 1",content)
            self.assertIn("KG Var",content)
            self.assertIn("PAS",content)
            self.assertNotIn("1.5 Üst",content)
            # Reusing the same PDF is append-only blocked, not silently
            # replacing stored odds/forecast at another timestamp.
            with patch("iddaa_pdf_one_step_263.parse_pdf",return_value=bulletin):
                with self.assertRaises(FileExistsError):
                    one_step(src,history=history,output_root=root/"results",
                             now=NOW,official_lookup=official)

    def test_absolute_private_session_real_frozen_decision_and_pdf(self):
        """Regression: before fix, /tmp session records failed repo-root check."""
        import json,fitz
        from iddaa_pdf_value_bridge_263 import _load
        f,b,lock,bulletin,session=sample()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            original=root/"fake-iddaa.pdf"
            original.write_bytes(b"fake user pdf solely for offline test")
            digest=hashlib.sha256(original.read_bytes()).hexdigest()
            bulletin["pdf_sha256"]=digest
            bulletin["total_visible_fixtures"]=1
            bulletin["potential_ten_league_rows"]=1
            session["pdf_sha256"]=digest
            history=root/"history.csv"
            history.write_text("fixture_id,league,match_date\n",encoding="utf-8")
            def batch(data,*,forecast_options=None,**kwargs):
                result=copy.deepcopy(session)
                forecast_dir=Path(forecast_options["out_dir"])/"2026-11-06"
                baseline_dir=Path(forecast_options["empirical_baseline_out_dir"])/"2026-11-06"
                forecast_dir.mkdir(parents=True,exist_ok=True)
                baseline_dir.mkdir(parents=True,exist_ok=True)
                forecast_path=forecast_dir/"one.json"
                baseline_path=baseline_dir/"one.json"
                forecast_path.write_text(json.dumps(f),encoding="utf-8")
                baseline_path.write_text(json.dumps(b),encoding="utf-8")
                result["rows"][0]["model_forecast_path"]=str(forecast_path)
                result["rows"][0]["empirical_baseline_path"]=str(baseline_path)
                result["n_official"]=1
                result["n_forecast"]=1
                return result
            with patch("iddaa_pdf_one_step_263.parse_pdf",return_value=bulletin):
                with patch("iddaa_pdf_one_step_263.run_session",side_effect=batch):
                    with patch("iddaa_pdf_value_bridge_263.verify_original_pdf",
                               return_value=digest):
                        done=one_step(original,history=history,
                            output_root=root/"safe-absolute-results",now=NOW,
                            repo_root=".")
            self.assertEqual(done["signed_four_model_forecasts"],1)
            self.assertEqual(done["calibrated_price_decisions"],1)
            self.assertEqual(done["official_confirmed_rows"],1)
            with fitz.open(done["pdf_report_path"]) as generated:
                text=" ".join(page.get_text() for page in generated)
            self.assertIn("ANA KOŞULLU (PDF)",text)
            self.assertNotIn("1.5 Üst",text)
            self.assertNotIn("3.5 Alt",text)
            # Traversal/symlink access via untrusted row JSON is prohibited.
            with self.assertRaisesRegex(ValueError,"ESCAPES_PRIVATE_SESSION"):
                _load(".",str(history),session_dir=done["processing_folder"],
                      record_kind="forecasts")
            with self.assertRaisesRegex(ValueError,"UNSUPPORTED_RECORD_KIND"):
                _load(".",str(history),session_dir=done["processing_folder"],
                      record_kind="user_uploads")

if __name__=="__main__":unittest.main()
