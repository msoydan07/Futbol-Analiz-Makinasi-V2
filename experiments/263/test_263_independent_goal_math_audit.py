"""Independent analytic goals-market acceptance of B/C3, C2 and M4 scorers.

Not a new pilot and not a retuning sweep. The independent formulas used here
do NOT call any engine under test:
    P(KG Var) = (1-exp(-home_lambda))*(1-exp(-away_lambda))
    P(2.5 Alt) = exp(-sum_lambda)*(1+sum_lambda+sum_lambda**2/2)
Both follow from independent Poisson assumptions already declared by v2.6.3.
"""
from __future__ import annotations
import math,unittest
from itertools import product
from exp_263_batch import scores as legacy_scores
from m4_integrated import score_markets as m4_scores
from analysis_math_core import score_market as c2_scores

GRID=(0.05,0.25,0.7,1.2,1.85,2.5,3.5,4.8,5.0)

def analytical(lh,la):
    s=lh+la
    return {"kg_yes":(-math.expm1(-lh))*(-math.expm1(-la)),
            "under25":math.exp(-s)*(1+s+s*s/2),
            "over25":1-math.exp(-s)*(1+s+s*s/2)}

class IndependentPoissonAudit(unittest.TestCase):
    def test_81_lambda_pairs_agree_with_closed_forms(self):
        n=0
        for lh,la in product(GRID,repeat=2):
            with self.subTest(home_lambda=lh,away_lambda=la):
                a=analytical(lh,la)
                m=m4_scores(lh,la)["markets"]
                c=c2_scores(lh,la)["markets"]
                self.assertAlmostEqual(m["BTTS_YES"],a["kg_yes"],delta=1e-10)
                self.assertAlmostEqual(c["BTTS_YES"],a["kg_yes"],delta=1e-10)
                self.assertAlmostEqual(m["UNDER_2.5"],a["under25"],delta=1e-10)
                self.assertAlmostEqual(c["UNDER_2.5"],a["under25"],delta=1e-10)
                self.assertAlmostEqual(m["OVER_2.5"],a["over25"],delta=1e-10)
                self.assertAlmostEqual(c["OVER_2.5"],a["over25"],delta=1e-10)
                for ms_m,ms_c in (("H","MS1"),("D","MSX"),("A","MS2")):
                    self.assertAlmostEqual(m["1X2"][ms_m],c[ms_c],delta=1e-10)
                self.assertAlmostEqual(sum(m["1X2"].values()),1,delta=1e-10)
                self.assertAlmostEqual(sum(c[k] for k in ("MS1","MSX","MS2")),1,delta=1e-10)
                self.assertAlmostEqual(m["BTTS_YES"]+m["BTTS_NO"],1,delta=1e-12)
                self.assertAlmostEqual(c["BTTS_YES"]+c["BTTS_NO"],1,delta=1e-12)
                self.assertAlmostEqual(m["UNDER_2.5"]+m["OVER_2.5"],1,delta=1e-12)
                self.assertAlmostEqual(c["UNDER_2.5"]+c["OVER_2.5"],1,delta=1e-12)
                self.assertGreaterEqual(m["OVER_3.5"],0)
                self.assertLessEqual(m["OVER_3.5"],m["OVER_2.5"])
                self.assertLessEqual(m["OVER_2.5"],m["OVER_1.5"])
                self.assertGreaterEqual(m["UNDER_3.5"],m["UNDER_2.5"])
                self.assertGreaterEqual(m["UNDER_2.5"],m["UNDER_1.5"])
                n+=1
        self.assertEqual(n,81)

    def test_swap_home_away_preserves_goals_and_kg_but_flips_ms(self):
        for lh,la in product((.2,.9,1.4,2.9,4.7),repeat=2):
            a=m4_scores(lh,la)["markets"]
            b=m4_scores(la,lh)["markets"]
            self.assertAlmostEqual(a["1X2"]["H"],b["1X2"]["A"],delta=1e-11)
            self.assertAlmostEqual(a["1X2"]["D"],b["1X2"]["D"],delta=1e-11)
            self.assertAlmostEqual(a["1X2"]["A"],b["1X2"]["H"],delta=1e-11)
            for market in ("OVER_2.5","UNDER_2.5","BTTS_YES","BTTS_NO"):
                self.assertAlmostEqual(a[market],b[market],delta=1e-11)

    def test_legacy_b_c3_truncation_never_claims_full_m4_when_tail_large(self):
        # Old B/C3 0..10 Poisson truncation is a deliberate frozen-model
        # limitation. It must refuse large tails, never fill with M4's scores.
        self.assertIsNone(legacy_scores(5.0,5.0))
        for lh,la in ((.1,.2),(1.0,1.5),(2.0,2.2)):
            old=legacy_scores(lh,la)
            self.assertIsNotNone(old)
            new=m4_scores(lh,la)["markets"]["1X2"]
            for i,key in enumerate(("H","D","A")):
                self.assertAlmostEqual(old[0][i],new[key],delta=0.0005)

    def test_b_c3_extreme_out_of_domain_is_unavailable_not_faked(self):
        for lh,la in ((0.,1.),(.001,1.),(1.,5.1),(math.inf,1.),(1.,math.nan)):
            self.assertIsNone(legacy_scores(lh,la))
        # C2's mathematical count distribution explicitly permits zero,
        # while the empirical M4 prediction domain requires >=0.05.
        self.assertAlmostEqual(c2_scores(0.,1.)["markets"]["BTTS_YES"],0.)
        for scorer,points in (
            (m4_scores,((0.,1.),(.001,1.),(5.01,1.),(1.,math.inf),(1.,math.nan))),
            (c2_scores,((-.001,1.),(5.01,1.),(1.,math.inf),(1.,math.nan))),
        ):
            for lh,la in points:
                with self.subTest(scorer=scorer.__name__,lh=lh,la=la):
                    with self.assertRaises(ValueError):
                        scorer(lh,la)

if __name__=="__main__":unittest.main()
