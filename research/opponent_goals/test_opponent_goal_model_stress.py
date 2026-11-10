"""Adversarial math checks before slower real cohort is processed."""
import sys,unittest,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from opponent_goal_model_stress import dc_fixed,bivar_fixed,markets_from_matrix,scalar_scores,score_markets_record,elo_by_week
import numpy as np

class JointProbabilityTests(unittest.TestCase):
    def test_dc_high_goal_market_unaffected_by_low_score_only(self):
        from m4_integrated import score_markets
        for lh,la in ((1.1,1.0),(2.5,.8),(.9,2.0)):
            raw=score_markets(lh,la)["markets"];candidate=dc_fixed(lh,la)
            for key in ("OVER_2.5","OVER_3.5"):
                self.assertAlmostEqual(raw[key],candidate[key],places=8)
            self.assertGreater(abs(raw["BTTS_YES"]-candidate["BTTS_YES"]),1e-4)
    def test_bivariate_changes_over25_without_changing_team_marginal_lambdas(self):
        from m4_integrated import score_markets
        lh,la=1.9,1.4
        raw=score_markets(lh,la)["markets"];candidate=bivar_fixed(lh,la)
        self.assertGreater(abs(raw["OVER_2.5"]-candidate["OVER_2.5"]),1e-4)
        self.assertGreater(abs(raw["BTTS_YES"]-candidate["BTTS_YES"]),1e-4)
        self.assertEqual(candidate["common_shock_rate"],.12)
        self.assertAlmostEqual(sum(candidate["1X2"].values()),1,places=10)
    def test_coherence_over_multiple_matchups(self):
        for lh,la in ((.05,.05),(.4,2.7),(3,3),(5.,1.2)):
            for f in (dc_fixed,bivar_fixed):
                p=f(lh,la)
                self.assertAlmostEqual(sum(p["1X2"].values()),1,places=8)
                self.assertGreaterEqual(p["OVER_1.5"]+1e-10,p["OVER_2.5"])
                self.assertGreaterEqual(p["OVER_2.5"]+1e-10,p["OVER_3.5"])
                self.assertLessEqual(p["BTTS_YES"],p["OVER_1.5"]+1e-10)
    def test_weekly_elo_no_result_leak(self):
        def r(i,d,h,a,y):
            return {"fixture_id":str(i),"league":"TUR1","match_date":d,
                "home_id":h,"away_id":a,"result":y}
        es=elo_by_week([r(1,"2025-08-05","A","B","H"),r(2,"2025-08-07","A","C","A"),
                        r(3,"2025-08-12","A","C","D")])
        self.assertEqual(es["1"]["gap"],0)
        self.assertEqual(es["2"]["gap"],0)
        self.assertNotEqual(es["3"]["gap"],0)
    def test_probability_failure(self):
        with self.assertRaises(ValueError):scalar_scores(-.5,1)
if __name__=="__main__":unittest.main()
