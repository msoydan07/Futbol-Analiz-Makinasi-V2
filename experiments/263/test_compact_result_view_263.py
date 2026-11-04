"""One small presentation-only acceptance; uses REAL existing SHA-locked data."""
import copy
import json
import unittest
from pathlib import Path

from compact_result_view_263 import build,render

SHADOW="forward_quad_shadow_263/2026-11-06/1d6b6f16fef8bac971c184c4.json"
PRICE="data/staged_263/2026_11_04_gaziantep_kasimpasa_secondary_betano_odds.json"


class CompactResultViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=json.loads(Path(SHADOW).read_text(encoding="utf-8"))
        cls.q=json.loads(Path(PRICE).read_text(encoding="utf-8"))
    def test_main_screen_has_single_clear_decision(self):
        s=render(build(self.f,self.q))
        self.assertIn("ONAYLI TERCİH YOK",s)
        self.assertIn("S1 · En olası tercih:",s)
        self.assertIn("S2 · Matematiksel değer:",s)
        self.assertLess(s.index("## 1. KARAR"),s.index("## 2. PİYASA"))
        self.assertLess(s.index("## 2. PİYASA"),s.index("## 3. DÖRT MODEL"))
    def test_secondary_odds_never_authorize_betting(self):
        b=build(self.f,self.q)
        self.assertFalse(b["betting_authorized"])
        self.assertEqual(b["pilot_count_increment"],0)
        self.assertEqual(b["s2"]["status"],"HESAPLANAMAZ")
        self.assertIn("Piyasaya yakınlık",render(b))
    def test_wrong_forecast_sha_rejected(self):
        f=copy.deepcopy(self.f);f["payload_sha256"]="0"*64
        with self.assertRaises(ValueError):build(f,self.q)
    def test_changed_existing_probability_rejected(self):
        f=copy.deepcopy(self.f);f["model_predictions"]["M4"]["goals"]["markets"]["OVER_2.5"]=0.99
        with self.assertRaisesRegex(ValueError,"ALTERED"):build(f,self.q)
    def test_false_direct_bookmaker_attestation_rejected(self):
        q=copy.deepcopy(self.q);q["direct_bookmaker_confirmation"]=True
        with self.assertRaisesRegex(ValueError,"SECONDARY_PRICE"):build(self.f,q)
    def test_incomplete_counterprice_rejected(self):
        q=copy.deepcopy(self.q);q["price_markets"]["MS"].pop("MSX")
        with self.assertRaisesRegex(ValueError,"MISSING_COUNTER"):build(self.f,q)
    def test_without_price_still_shows_clear_decision(self):
        s=render(build(self.f))
        self.assertIn("DOĞRULANAMADI",s)
        self.assertIn("ONAYLI TERCİH YOK",s)
    def test_no_model_selection_from_market_proximity(self):
        b=build(self.f,self.q)
        self.assertEqual(b["market_role"],"REFERENCE_RESEARCH_ONLY_NOT_MODEL_SELECTION")
        self.assertNotIn("selected_model",b)
    def test_postmatch_not_added_to_prematch_record(self):
        b=build(self.f,self.q)
        self.assertNotIn("actual_result",b)
        self.assertNotIn("postmatch_score",b)

if __name__=="__main__":unittest.main()
