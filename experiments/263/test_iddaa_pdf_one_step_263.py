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
if __name__=="__main__":unittest.main()
