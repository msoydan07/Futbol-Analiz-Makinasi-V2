"""Test unsafe DEV per-event q is never called a coherent MS vector."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from second_engineer_decision_263 import analyse
from sabah_mobile_screens_263 import single

ROOT=Path(__file__).resolve().parents[2]
class DevDecisionAuditTests(unittest.TestCase):
    def test_40_real_decisions_examined(self):
        r=analyse(ROOT)
        self.assertEqual(r["counts"]["decisions"],40)
        self.assertGreater(r["counts"]["joint_sum_not_one"],0)
        self.assertFalse(r["original_40_decisions_changed"])
    def test_phone_distinguishes_dev_market_from_valid_1x2(self):
        f={"fixture":{"league":"TUR1","kickoff_utc":"2026-11-14T15:00:00+00:00",
                      "official_source":"https://test.invalid"},
           "model_predictions":{k:{"status":"UNAVAILABLE","reason":"test"}
                                for k in ("B","C2","C3","M4")},
           "payload_sha256":"a"*64,"created_at_utc":"2026-11-14T10:00:00+00:00"}
        row={"home":"Synthetic H","away":"Synthetic A","rotation":{}}
        d={"all_market_diagnostics":[
            {"market":"MS1","calibrated_probability":.55},
            {"market":"MSX","calibrated_probability":.24},
            {"market":"MS2","calibrated_probability":.17}],
           "main_candidate":None,"alternative_candidate":None,
           "payload_sha256":"b"*64}
        text=single(row,f,d)
        self.assertIn("DEV tek-market",text)
        self.assertIn("1X2 dağılımı değil",text)
        self.assertNotIn("Kalibre MS yönü",text)
if __name__=="__main__":unittest.main()
