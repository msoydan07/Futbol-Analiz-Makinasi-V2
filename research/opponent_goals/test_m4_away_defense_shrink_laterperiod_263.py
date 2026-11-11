"""Disjoint later-period opponent defense hypothesis and deployment safety."""
import math, sys, unittest
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from m4_away_defense_shrink_laterperiod_263 import (
  TRAIN_CUTOFF,EVAL_END,OLD_DEV_END,FACTORS,Rejected,
  candidate_goals,center_defense,defense_contribution,brier_loss,
  date_block_ci,ensure_sources,run
)
sys.path.insert(0,str(ROOT/"experiments/263"))
from m4_integrated import predict_m4,score_markets

class AwayDefenseShrinkLaterPeriodTests(unittest.TestCase):
    def setUp(self):
        # m=3, two intercepts, six team effects each.
        m=3;beta=np.zeros(2+6*m,dtype=float)
        self.ix={"HOME":0,"STRONG_AWAY":1,"WEAK_AWAY":2}
        beta[0]=math.log(1.4)
        beta[1]=math.log(1.1)
        beta[2+m+self.ix["STRONG_AWAY"]]=-.5
        beta[2+5*m+self.ix["STRONG_AWAY"]]=-.2
        beta[2+m+self.ix["WEAK_AWAY"]]=.5
        beta[2+5*m+self.ix["WEAK_AWAY"]]=.2
        self.fit=(beta,self.ix,m,120)
    def test_baseline_factor_one_exactly_reproduces_m4(self):
        for rival in ("STRONG_AWAY","WEAK_AWAY"):
            actual=candidate_goals(self.fit,"HOME",rival,1.0)
            self.assertEqual(actual,predict_m4(self.fit,"HOME",rival))
    def test_smaller_defence_strength_moves_strong_and_weak_toward_same_mean(self):
        strong_before=predict_m4(self.fit,"HOME","STRONG_AWAY")[0]
        weak_before=predict_m4(self.fit,"HOME","WEAK_AWAY")[0]
        strong_half=candidate_goals(self.fit,"HOME","STRONG_AWAY",.5)[0]
        weak_half=candidate_goals(self.fit,"HOME","WEAK_AWAY",.5)[0]
        self.assertLess(strong_before,strong_half)
        self.assertGreater(weak_before,weak_half)
        self.assertLess(weak_half-strong_half,weak_before-strong_before)
        self.assertAlmostEqual(
            math.log(weak_half/strong_half),
            .5*math.log(weak_before/strong_before),
            places=10)
    def test_cannot_edit_away_goal_lambda_by_shrink(self):
        for factor in FACTORS:
            for opponent in ("STRONG_AWAY","WEAK_AWAY"):
                self.assertEqual(
                    candidate_goals(self.fit,"HOME",opponent,factor)[1],
                    predict_m4(self.fit,"HOME",opponent)[1])
    def test_mean_centers_on_training_teams_without_postmatch_information(self):
        self.assertAlmostEqual(center_defense(self.fit),0.)
        self.assertAlmostEqual(defense_contribution(self.fit,"STRONG_AWAY"),-.7)
        self.assertAlmostEqual(defense_contribution(self.fit,"WEAK_AWAY"),.7)
    def test_unknown_team_or_unpredeclared_factor_rejected(self):
        with self.assertRaises(Rejected):
            candidate_goals(self.fit,"HOME","WEAK_AWAY",.9)
        with self.assertRaises(Rejected):
            candidate_goals(self.fit,"UNKNOWN","WEAK_AWAY",.75)
        with self.assertRaises(Rejected):
            candidate_goals(self.fit,"HOME","UNKNOWN",.75)
    def test_changed_goal_expected_rate_produces_valid_KG_over_MS_loss(self):
        candidate=candidate_goals(self.fit,"HOME","WEAK_AWAY",.75)
        l=brier_loss(candidate,2,1)
        ref=score_markets(*candidate)["markets"]
        self.assertAlmostEqual(l["KG_Brier"],(1-ref["BTTS_YES"])**2)
        self.assertAlmostEqual(l["OVER25_Brier"],(1-ref["OVER_2.5"])**2)
        self.assertAlmostEqual(l["MS_Brier"],sum(
            (ref["1X2"][i]-int(i=="H"))**2 for i in ("H","D","A")))
    def test_day_bootstrap_requires_ten_dates_not_ten_similar_games(self):
        self.assertIsNone(date_block_ci(
            [{"date":"2026-04-11","deltas":{"KG_Brier":.03}} for _ in range(80)],
            "KG_Brier"))
        x=[{"date":f"2026-04-{1+i%12:02d}","deltas":{"KG_Brier":(-.01 if i%2 else .01)}}
            for i in range(100)]
        b=date_block_ci(x,"KG_Brier",reps=100)
        self.assertEqual(b["distinct_match_dates"],12)
        self.assertLessEqual(b["low"],b["high"])
    def test_source_2026_27_holdout_and_old_702_nonoverlap(self):
        dev,settings=ensure_sources()
        self.assertTrue(TRAIN_CUTOFF>OLD_DEV_END)
        self.assertTrue(EVAL_END<"2026-07-01")
        self.assertTrue(all(r["season"]=="2025-2026" for r in dev))
        self.assertTrue(any(TRAIN_CUTOFF<=r["match_date"]<EVAL_END for r in dev))
    def test_actual_10_league_time_block_with_every_candidate_on_same_fixture(self):
        r=run()
        self.assertEqual(r["schema"],"263_AWAY_DEFENSE_SHRINK_LATER_DATE_2025_26_FIXED_M4_V1")
        self.assertEqual(len(r["freeze_fit_by_league"]),10)
        self.assertEqual(set(r["n_by_league"]),set((
          "ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")))
        self.assertGreaterEqual(r["n_accepted"],200)
        self.assertTrue(r["new_99_results_used_for_tuning_or_evaluation"] is False)
        self.assertFalse(r["season_2026_27_included"])
        self.assertFalse(r["pre_game_probability_changed"])
        self.assertFalse(r["model_promoted"])
        self.assertEqual(r["factors"],[1.,.75,.5])
        for factor in (".75",".5"):
            self.assertIn(factor,r["same_match_matched_loss"])

if __name__=="__main__":
    unittest.main()
