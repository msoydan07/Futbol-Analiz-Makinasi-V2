"""Synthetic adversarial tests plus real sealed 40/39 read-only source check."""
import unittest,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from m4_sealed_goal_error_matchup_263 import explain,summarize,score,AuditStop
ROOT=Path(__file__).resolve().parents[2]
class Tests(unittest.TestCase):
    def test_baseline_comparison_and_direction(self):
        rows=[{"home_goal_error":1,"away_goal_error":-0.2,"total_goal_error":.8,
               "probabilities":{"BTTS_YES":.7,"OVER_1.5":.8,"OVER_2.5":.7,"OVER_3.5":.1},
               "events":{"BTTS_YES":1,"OVER_1.5":1,"OVER_2.5":0,"OVER_3.5":0},
               "league_baseline":{"BTTS_YES":.5,"OVER_1.5":.6,"OVER_2.5":.5,"OVER_3.5":.2}}]
        s=summarize(rows)
        self.assertEqual(s["average_total_error_goals_actual_minus_expected"],.8)
        self.assertGreater(s["goals_by_market"]["OVER_2.5"]["m4_minus_climatology_brier_lower_is_better"],0)
        self.assertLess(s["goals_by_market"]["BTTS_YES"]["m4_minus_climatology_brier_lower_is_better"],0)
    def test_no_sample_not_zero(self):
        r=summarize([])
        self.assertEqual(r["n"],0)
        self.assertNotIn("goals_by_market",r)
    def test_invalid_probability_is_blocked(self):
        for p in (float("nan"),float("inf"),-0.01,1.01,True):
            with self.assertRaises(AuditStop):score(p,1)
    def test_real_nov8_seals_not_asof_retrofit(self):
        x=explain(ROOT)
        self.assertEqual(x["forecast_sha_locked"],40)
        self.assertEqual(x["postponed_excluded"],1)
        self.assertEqual(x["scored_m4"],39)
        self.assertEqual(x["source_class_counts"].get("PRIMARY_LEAGUE_OR_CLUB"),35)
        self.assertFalse(x["model_changed"])
        self.assertTrue(all(v["latest_date"]<"2026-11-08" for v in x["league_current_season_baselines"].values()))
if __name__=="__main__":unittest.main()
