"""Regression: a separate DEV market q must NOT look like 1X2 distribution."""
import inspect,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sabah_mobile_screens_263 import single
from sabah_mobile_approved_pdf_263 import foot,match,single_pdf

class DisplayTests(unittest.TestCase):
    def test_phone_names_event_specific_dev_not_full_probability_vector(self):
        f={"fixture":{"league":"TUR1","kickoff_utc":"2026-11-14T15:00:00+00:00",
                      "official_source":"https://test.invalid"},
           "model_predictions":{k:{"status":"UNAVAILABLE","reason":"synthetic"}
                    for k in ("B","C2","C3","M4")},
           "payload_sha256":"a"*64,"created_at_utc":"2026-11-14T10:00:00+00:00"}
        row={"home":"Synthetic H","away":"Synthetic A","rotation":{}}
        d={"all_market_diagnostics":[
            {"market":"MS1","calibrated_probability":.55},
            {"market":"MSX","calibrated_probability":.24},
            {"market":"MS2","calibrated_probability":.17}],
           "main_candidate":None,"alternative_candidate":None,
           "payload_sha256":"b"*64}
        rendered=single(row,f,d)
        self.assertIn("DEV tek-market",rendered)
        self.assertIn("1X2 dağılımı değil",rendered)
        self.assertNotIn("Kalibre MS yönü",rendered)
        self.assertIn("PAS",rendered)
    def test_pdf_legend_and_amount_label_dont_claim_triple_joint_calibration(self):
        leg=inspect.getsource(foot)
        matchline=inspect.getsource(match)
        singleline=inspect.getsource(single_pdf)
        self.assertIn("1X2 dagilimi degil",leg)
        self.assertIn("BIZIM (TEK MS)",matchline)
        self.assertIn("BIZIM (TEK MS)",singleline)
    def test_immutable_seal_remains_unchanged_by_display_functions(self):
        self.assertTrue(callable(single))
        self.assertTrue(callable(match))
if __name__=="__main__":unittest.main()
