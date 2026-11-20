"""Numerical adapter regressions: preserve frozen B/C3; do not touch seals.

The Bayern figures are the reproduced original 20-Nov pre-match goal lambdas.
Barcelona/City-like strengths below are SYNTHETIC STRESS INPUTS, not fixtures.
"""
import json
import math
import unittest

from exp_263_batch import scores as frozen_scores
from forward_quad import _legacy_joint,_safe_legacy_poisson_joint
from m4_integrated import score_markets

class TailExtension(unittest.TestCase):
    def check_normalized(self,sc):
        m=sc["markets"]
        self.assertAlmostEqual(sum(m["1X2"].values()),1,places=11)
        for a,b in (("BTTS_YES","BTTS_NO"),
                    ("OVER_1.5","UNDER_1.5"),
                    ("OVER_2.5","UNDER_2.5"),
                    ("OVER_3.5","UNDER_3.5")):
            self.assertAlmostEqual(m[a]+m[b],1,places=11)
        self.assertLess(sc["tail_mass"],1e-9)
        self.assertEqual(len(sc["top_scores"]),5)
    def test_old_normal_matches_are_identical_no_recalibration(self):
        for home,away in ((1.1,1.0),(2.0,1.2),(3.0,.7),(.8,.8),(2.5,2.5)):
            with self.subTest(lh=home,la=away):
                original=frozen_scores(home,away)
                self.assertIsNotNone(original)
                expected=_legacy_joint(home,away,original[0])
                new,extended=_safe_legacy_poisson_joint(home,away,original[0])
                self.assertFalse(extended)
                self.assertEqual(json.dumps(new,sort_keys=True),
                                 json.dumps(expected,sort_keys=True))
                self.check_normalized(new)
    def test_bayern_b_c3_recovered_without_model_formula_modification(self):
        for model,lh,la in (
            ("B",3.96547779365698,0.9473698585317792),
            ("C3",4.188326334899042,0.845469110968623)):
            with self.subTest(model=model):
                self.assertIsNone(frozen_scores(lh,la))
                new,extended=_safe_legacy_poisson_joint(lh,la)
                self.assertTrue(extended)
                self.assertGreater(new["legacy_0_10_tail_mass"],.001)
                self.assertLess(new["tail_mass"],1e-9)
                self.assertTrue(new["lambda_formula_unchanged"])
                self.assertAlmostEqual(new["lambda_home"],lh,places=14)
                self.assertAlmostEqual(new["lambda_away"],la,places=14)
                self.assertEqual(new["scoring_adapter"],
                                 "FROZEN_B_C3_NUMERICAL_TAIL_EXTENSION_V1")
                self.check_normalized(new)
                fairkg=(1-math.exp(-lh))*(1-math.exp(-la))
                self.assertAlmostEqual(new["markets"]["BTTS_YES"],fairkg,places=10)
                mu=lh+la
                fair_over=1-math.exp(-mu)*(1+mu+mu*mu/2)
                self.assertAlmostEqual(new["markets"]["OVER_2.5"],fair_over,places=10)
                reference=score_markets(lh,la)
                self.assertEqual(new["markets"],reference["markets"])
    def test_synthetic_big_favorites_same_exact_rule_all_leagues(self):
        # Not real games, no ex-post predictions: stress test goals near 5.
        for league,lh,la in (("ENG1",4.75,.3),
                             ("ESP1",4.6,1.1),("GER1",5.,.05),
                             ("ITA1",.05,5.),("TUR1",4.8,.1)):
            with self.subTest(league=league):
                x,extended=_safe_legacy_poisson_joint(lh,la)
                self.assertTrue(extended)
                self.check_normalized(x)
                self.assertAlmostEqual(x["markets"]["BTTS_YES"],
                    (1-math.exp(-lh))*(1-math.exp(-la)),places=10)
    def test_invalid_original_lambdas_not_allowed_and_not_masked(self):
        for lh,la in ((5.01,.3),(0,.5),(float("nan"),1.),
                      (1.,float("inf")),(-1.,1.)):
            with self.subTest(home=lh,away=la):
                with self.assertRaisesRegex(ValueError,"original_valid_range"):
                    _safe_legacy_poisson_joint(lh,la)
    def test_b_c3_original_frozen_legacy_function_unchanged(self):
        # The old scorer MUST still reject the high-tail example; the new
        # forward numerical adapter recovers it without editing frozen code.
        self.assertIsNone(frozen_scores(4.188326334899042,.845469110968623))
        x,e=_safe_legacy_poisson_joint(4.188326334899042,.845469110968623)
        self.assertTrue(e)
        self.assertIn("extended_from_legacy",x["distribution"])

if __name__=="__main__":unittest.main()
