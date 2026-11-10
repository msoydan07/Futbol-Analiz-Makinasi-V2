"""Five mathematical and archive guard regressions, plus real 10-league folds."""
import math
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from goal_distribution_challenger_263 import (
    VARIANTS,derived_markets,marginal,values,run,verify_source,DiagnosticFailed)
sys.path.insert(0,str(ROOT/"experiments/263"))
from m4_integrated import score_markets

class DevGoalDistributionChecks(unittest.TestCase):
    def test_poisson_baseline_is_original_m4_to_machine_precision(self):
        for home,away in ((.07,.08),(.55,1.05),(1.45,1.8),(2.1,3.7),(5.,5.)):
            with self.subTest(home=home,away=away):
                actual=derived_markets(home,away,"poisson",0)
                frozen=score_markets(home,away)["markets"]
                for kind in ("H","D","A"):
                    self.assertAlmostEqual(actual["1X2"][kind],frozen["1X2"][kind],places=10)
                self.assertAlmostEqual(actual["BTTS_YES"],frozen["BTTS_YES"],places=10)
                self.assertAlmostEqual(actual["OVER_2.5"],frozen["OVER_2.5"],places=10)

    def test_negative_binomial_same_expected_goals_but_higher_variance(self):
        for mu in (0.05,.4,1.0,1.8,4.9):
            for alpha in (.1,.25):
                with self.subTest(mu=mu,alpha=alpha):
                    p=marginal(mu,"nb",alpha)
                    expected=sum(k*v for k,v in enumerate(p))
                    variance=sum((k-expected)**2*v for k,v in enumerate(p))
                    self.assertAlmostEqual(float(p.sum()),1.,places=9)
                    self.assertAlmostEqual(float(expected),mu,places=9)
                    self.assertAlmostEqual(float(variance),mu+alpha*mu*mu,places=8)

    def test_candidate_1x2_kg_and_over25_are_valid_and_jointly_coherent(self):
        for lh,la in ((.1,1.9),(1.,1.),(3.2,.6),(4.7,3.8)):
            for _,(kind,scale,alpha) in VARIANTS.items():
                m=derived_markets(lh*scale,la*scale,kind,alpha)
                self.assertAlmostEqual(sum(m["1X2"].values()),1,places=9)
                self.assertTrue(0<=m["BTTS_YES"]<=1)
                self.assertTrue(0<=m["OVER_2.5"]<=1)
                self.assertTrue(all(0<=q<=1 for q in m["1X2"].values()))
                scored=values(m,2,1)
                self.assertGreaterEqual(scored["O25_Brier"],0)
                self.assertGreaterEqual(scored["MS_Brier"],0)

    def test_out_of_range_or_inconsistent_alpha_rejects(self):
        for args in ((0,"poisson",0),(-1,"nb",.2),(7.0,"poisson",0),
                     (1,"nb",-1),(1,"poisson",.1),(1,"nb",0)):
            with self.subTest(args=args):
                with self.assertRaises(DiagnosticFailed):
                    marginal(*args)

    def test_4617_source_only_2025_26_dev_available_and_99_not_backdated(self):
        dev,settings,n=verify_source()
        self.assertEqual(n["full"],4617)
        self.assertGreater(n["excluded_2026_27"],0)
        self.assertTrue(all(row["season"]=="2025-2026" for row in dev))
        self.assertEqual(n["partial_exception"],1)

    def test_actual_ten_league_challenge_reuses_locked_m4_without_holdout(self):
        r=run()
        self.assertGreaterEqual(r["eligible_common_paired_dev_matches"],400)
        self.assertEqual(len(r["league_counts"]),10)
        self.assertEqual(set(r["variant_methods"]),set(VARIANTS))
        self.assertEqual(set(r["paired_development_contrasts"]),
                         set(VARIANTS)-{"m4_original_poisson"})
        self.assertEqual(len(r["trained_folds"]),30)
        self.assertTrue(r["2026_27_holdout_never_touched"])
        self.assertTrue(r["winner_not_promoted"])
        self.assertTrue(r["m4_and_lock_unchanged"])
        self.assertTrue(r["old_seals_unmodified"])

if __name__=="__main__":
    unittest.main()
