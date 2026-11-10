"""Pre-match leak guards, form signal sanity, and a single real 10-league run."""
from __future__ import annotations
import math,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from m4_opponent_form_diagnostic_263 import (
    FORM_COEFFICIENTS,FORM_LENGTH,Reject,prior_five,form_record,signal,
    candidate_lambda,defense_band,form_band,scores,date_bootstrap,load,run,
)
sys.path.insert(0,str(ROOT/"experiments/263"))
from m4_integrated import score_markets
import numpy as np

def fixture(i,d,home="A",away="B",hg=1,ag=1):
    return {"fixture_id":f"ID{i}","league":"ENG1","season":"2025-2026",
            "match_date":d,"home_id":home,"away_id":away,
            "home_goals":str(hg),"away_goals":str(ag),"result":
                "H" if hg>ag else "A" if ag>hg else "D"}

class M4OpponentFormAuditTests(unittest.TestCase):
    def test_last_five_strictly_before_match_never_same_day_or_future(self):
        games=[fixture(1,"2025-11-01"),fixture(2,"2025-11-02"),
               fixture(3,"2025-11-03"),fixture(4,"2025-11-04"),
               fixture(5,"2025-11-05"),fixture(6,"2025-11-06"),
               fixture(7,"2025-11-07"),fixture(8,"2025-11-07")]
        matches=prior_five("A",games,"2025-11-07")
        self.assertEqual(len(matches),5)
        self.assertEqual([r["fixture_id"] for r in matches],
                         ["ID2","ID3","ID4","ID5","ID6"])
        self.assertNotIn("ID7",[r["fixture_id"] for r in matches])
        self.assertNotIn("ID8",[r["fixture_id"] for r in matches])

    def test_no_last_five_does_not_turn_into_zero_form(self):
        fit=(np.zeros(14),{"A":0,"B":1},2,100)
        self.assertIsNone(form_record("A",[fixture(1,"2025-11-04")],
                                      "2025-11-07",fit))
        self.assertEqual(prior_five("A",[fixture(1,"2025-01-01")],
                                    "2025-11-07"),[])

    def test_opponent_adjusted_form_residual_exactly_matches_known_model(self):
        beta=np.zeros(2+6*2)
        fit=(beta,{"A":0,"B":1},2,100)
        records=[fixture(i,f"2025-11-{i+1:02d}",hg=2,ag=0) for i in range(5)]
        form=form_record("A",records,"2025-11-08",fit)
        self.assertEqual(form["n"],5)
        self.assertAlmostEqual(form["goal_attack_surprise"],1.)
        self.assertAlmostEqual(form["goal_concede_surprise"],-1.)
        faway=form_record("B",records,"2025-11-08",fit)
        self.assertAlmostEqual(faway["goal_attack_surprise"],-1.)
        self.assertAlmostEqual(faway["goal_concede_surprise"],1.)
        self.assertEqual(signal(form,faway),(1.,-1.))

    def test_zero_coefficient_is_exact_frozen_m4_and_safe_candidate_caps(self):
        self.assertEqual(candidate_lambda(1.1,0.9,.4,-.7,0.),
                         (1.1,0.9))
        self.assertAlmostEqual(candidate_lambda(1.1,.9,.4,-.7,.1)[0],
                               1.1*math.exp(.04))
        self.assertIsNone(candidate_lambda(4.99,1.5,1.,0.,.20))
        with self.assertRaises(Reject):
            candidate_lambda(1.1,1.1,.1,.1,.5)
        with self.assertRaises(Reject):
            candidate_lambda(1.1,1.1,1.1,.1,.1)

    def test_predefined_opponent_strength_and_form_buckets(self):
        self.assertEqual(defense_band(-.2),"strong_relative_fitted_away_defence")
        self.assertEqual(defense_band(.2),"weak_relative_fitted_away_defence")
        self.assertEqual(defense_band(.0),"central_fitted_away_defence")
        self.assertEqual(form_band(.4),"positive_residual_form")
        self.assertEqual(form_band(-.4),"negative_residual_form")
        self.assertEqual(form_band(.0),"neutral_residual_form")

    def test_kg_over_ms_brier_keep_correct_market_meanings(self):
        p=score_markets(1.2,.8)["markets"]
        vals=scores(p,2,1)
        self.assertAlmostEqual(vals["KG_Brier"],(p["BTTS_YES"]-1)**2)
        self.assertAlmostEqual(vals["Over25_Brier"],(p["OVER_2.5"]-1)**2)
        self.assertAlmostEqual(vals["MS_Brier"],
                               (p["1X2"]["H"]-1)**2+
                               p["1X2"]["D"]**2+p["1X2"]["A"]**2)

    def test_date_bootstrap_refuses_few_dates_even_if_many_games(self):
        self.assertIsNone(date_bootstrap(
            [{"date":"2025-12-01","value":1.0} for _ in range(100)]))
        self.assertIsNotNone(date_bootstrap(
            [{"date":f"2025-12-{i%12+1:02d}","value":i%3-.7}
             for i in range(120)],reps=100))

    def test_real_4617_integrity_and_holdout_exclusion(self):
        dev,settings=load()
        self.assertTrue(all(r["season"]=="2025-2026" and
                            r["match_date"]<"2026-07-01" for r in dev))
        self.assertGreater(len(dev),1000)
    def test_full_ten_leagues_five_match_asof_form_against_frozen_m4(self):
        report=run()
        self.assertEqual(report["num_original_ten_league_development_folds"],30)
        self.assertGreaterEqual(report["all_valid_baseline_matches"],650)
        self.assertGreaterEqual(report["paired_five_match_asof_form_matches"],450)
        self.assertEqual(report["2026_27_outcome_rows_used"],0)
        self.assertTrue(report["2026_27_holdout_excluded"])
        self.assertEqual(report["historical_sealed_forecasts_scored"],0)
        self.assertFalse(report["automatic_model_promotion"])
        self.assertFalse(report["original_m4_settings_changed"])
        self.assertFalse(report["morning_or_mobile_percentages_changed"])
        self.assertEqual(set(report["league_level_descriptives"]),
                         {"ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1"})
        self.assertEqual(set(report["paired_form_challenger_scores"]),{"0.1","0.2"})
        for c in ("0.1","0.2"):
            self.assertEqual(report["paired_form_challenger_scores"][c]["n_paired"],
                             report["paired_five_match_asof_form_matches"])

if __name__=="__main__":
    unittest.main()
