"""Frozen M4-MS and C3-KG/GOALS selector must stay internally coherent.
All examples synthetic; never bets, no price downloads or model modifications.
"""
import copy
import unittest
from datetime import datetime,timezone
from test_four_model_value_policy_263 import fixture,seal,NOW
from four_model_value_policy_263 import decide, _fixed_family_experts, _validate_family

class FixedSpecialistTests(unittest.TestCase):
    def setUp(self):
        self.f,self.base,self.lock=fixture()

    def test_officially_not_approved_even_when_expert_present(self):
        d=decide(self.f,self.base,self.lock,now=NOW)
        self.assertFalse(d["betting_authorized"])
        self.assertFalse(d["S1_S2_official_approved"])
        self.assertEqual(d["status"],"RESEARCH_PAS")
        self.assertIsNone(d["main_candidate"])
        self.assertIsNone(d["alternative_candidate"])

    def test_inconsistent_old_marketwise_weights_cannot_break_ms_total(self):
        d=decide(self.f,self.base,self.lock,now=NOW)
        for name in ("MS1","MSX","MS2"):
            x=next(x for x in d["all_market_diagnostics"] if x["market"]==name)
            self.assertEqual(x["fixed_specialist_model"],"M4")
            self.assertEqual(x["anchor_model"],"M4")
            self.assertIsNotNone(x["calibrated_probability"])
        qs={x["market"]:x["calibrated_probability"] for x in d["all_market_diagnostics"]
            if x["market"] in ("MS1","MSX","MS2")}
        self.assertAlmostEqual(sum(qs.values()),1,places=12)

    def test_ms_is_whole_model_when_c3_has_opposite_opinion(self):
        f=copy.deepcopy(self.f)
        f["model_predictions"]["C3"]["goals"]["markets"]["1X2"]={"H":.1,"D":.8,"A":.1}
        seal(f)
        b=copy.deepcopy(self.base)
        b["forecast_sha256"]=f["payload_sha256"]
        seal(b)
        result=decide(f,b,self.lock,now=NOW)
        e=result["fixed_market_specialists_research_only"]
        self.assertEqual(e["MS"]["model"],"M4")
        self.assertEqual(e["KG"]["model"],"C3")
        self.assertEqual(e["GOALS"]["model"],"C3")
        self.assertAlmostEqual(sum(e["MS"]["dev_shrunken_probability_vector"].values()),1,places=12)
        for fam in ("MS","KG","GOALS"):
            _validate_family(e[fam]["dev_shrunken_probability_vector"],fam)

    def test_goal_bad_skill_remains_pas_and_raw_c3_is_visible(self):
        d=decide(self.f,self.base,self.lock,now=NOW)
        r=next(x for x in d["all_market_diagnostics"] if x["market"]=="OVER_2.5")
        self.assertEqual(r["fixed_specialist_model"],"C3")
        self.assertIsNone(r["calibrated_probability"])
        self.assertIsNone(r["EV"])
        self.assertIn("NO_POSITIVE_DEV_BRIER_SKILL",r["qualification_reasons"])
        self.assertAlmostEqual(r["fixed_specialist_raw_probability"],.53)

    def test_invalid_original_expert_vector_fails_closed(self):
        f=copy.deepcopy(self.f)
        f["model_predictions"]["M4"]["goals"]["markets"]["1X2"]={"H":.7,"D":.2,"A":.2}
        seal(f)
        b=copy.deepcopy(self.base)
        b["forecast_sha256"]=f["payload_sha256"]
        seal(b)
        with self.assertRaisesRegex(ValueError,"1X2_NOT_NORMALIZED|EXPERT_MS_NOT_NORMALIZED"):
            decide(f,b,self.lock,now=NOW)

if __name__=="__main__":unittest.main()
