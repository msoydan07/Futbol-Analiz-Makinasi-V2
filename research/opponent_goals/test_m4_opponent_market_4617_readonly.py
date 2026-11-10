"""Read-only research: opponent-lambda and KG/over2.5 mathematical invariants."""
import math
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from m4_opponent_market_4617_readonly import explain_strength,closed_forms,verify_market,run,DiagnosticInvalid

class OpponentAndGoalMarketChecks(unittest.TestCase):
    def test_manual_away_defence_coefficients_exactly_change_home_goals(self):
        # m=3, 2 shared intercepts, 6*m coefficients; no empirical fitting.
        m=3;beta=np.zeros(2+6*m)
        beta[0]=math.log(1.4);beta[1]=math.log(1.1)
        ix={"home":0,"strong":1,"weak":2}
        beta[2+m+ix["strong"]]=-0.4
        beta[2+5*m+ix["strong"]]=-0.1
        beta[2+m+ix["weak"]]=0.5
        beta[2+5*m+ix["weak"]]=0.2
        beta[2+ix["strong"]]=0.1
        beta[2+3*m+ix["weak"]]=-0.2
        fit=(beta,ix,m,100)
        strong=explain_strength(fit,"home","strong")
        weak=explain_strength(fit,"home","weak")
        self.assertAlmostEqual(strong["home_lambda"],1.4*math.exp(-.5),places=10)
        self.assertAlmostEqual(weak["home_lambda"],1.4*math.exp(.7),places=10)
        self.assertAlmostEqual(math.log(weak["home_lambda"]/strong["home_lambda"]),1.2,places=10)
        self.assertNotEqual(strong["away_lambda"],weak["away_lambda"])

    def test_kg_and_o25_are_exact_analytic_poisson_not_fitted_separately(self):
        for home,away in ((.05,.05),(.4,1.6),(1.5,1.1),(2.3,2.8),(5.,5.)):
            with self.subTest(home=home,away=away):
                a=verify_market(home,away)
                self.assertAlmostEqual(a["BTTS_YES"],
                   (1-math.exp(-home))*(1-math.exp(-away)),places=10)
                self.assertAlmostEqual(a["OVER_2.5"],
                   1-math.exp(-home-away)*(1+home+away+(.5*(home+away)**2)),places=10)

    def test_bad_lambda_is_fully_rejected(self):
        for h,a in ((0,1.5),(-1,2.),(10.,1.),(float("nan"),1.0)):
            with self.subTest(h=h,a=a):
                with self.assertRaises(DiagnosticInvalid):closed_forms(h,a)
    def test_identity_unknown_club_is_rejected(self):
        fit=(np.zeros(2+6*2),{"home":0,"away":1},2,70)
        with self.assertRaisesRegex(DiagnosticInvalid,"INSUFFICIENT_IDENTIFIED_TEAMS"):
            explain_strength(fit,"home","unseen")
    def test_4617_real_10_league_opponent_effect_and_market_invariants(self):
        report=run()
        self.assertEqual(report["leagues_diagnosed"],10)
        self.assertEqual(report["new_99_score_rows_present"],99)
        self.assertTrue(report["market_analytic_identity_verified"])
        self.assertTrue(report["proof_not_new_predictive_accuracy"])
        self.assertTrue(report["no_model_promotion_or_historical_forecast_rewrite"])
        self.assertEqual(len(report["details"]),10)
        for x in report["details"]:
            self.assertGreater(x["opponent_only_home_lambda_log_delta"],0)
            self.assertEqual(len(x["counterfactuals"]),2)
            self.assertGreaterEqual(x["full_match_train_rows"],60)
            for e in x["counterfactuals"]:
                self.assertLess(abs(e["market_probabilities"]["BTTS_YES"]-
                    e["independent_closed_form_reference"]["BTTS_YES"]),2e-10)
                self.assertLess(abs(e["market_probabilities"]["OVER_2.5"]-
                    e["independent_closed_form_reference"]["OVER_2.5"]),2e-10)

if __name__=="__main__":
    unittest.main()
