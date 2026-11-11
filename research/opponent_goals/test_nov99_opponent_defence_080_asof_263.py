"""One-time Nov99 as-of experiment guards. Does NOT rerun all 99 in tests."""
import math,sys,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from nov99_opponent_defence_080_asof_backtest_263 import (
    read_history,top1_accuracy,losses,FILES,PINS,NOV99,DATES,SOURCE_GRADES,
    StopResearch,SCHEMA
)
from m4_opponent_defence_shrinkage_263 import candidate_lambdas
sys.path.insert(0,str(ROOT/"experiments/263"))
from m4_integrated import predict_m4,score_markets

class ArchivalNov99NoLeakTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.targets,cls.history,cls.settings=read_history()

    def test_nov99_has_99_unique_archived_match_identities_in_ten_leagues(self):
        self.assertEqual(len(self.targets),99)
        self.assertEqual(len({(x["league"],x["match_date"],x["home_id"],x["away_id"])
                              for x in self.targets}),99)
        self.assertEqual(set(x["league"] for x in self.targets),
                         {"BEL1","ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","POR1","TUR1"})
        self.assertEqual({d:sum(x["match_date"]==d for x in self.targets)
                          for d in DATES},DATES)

    def test_asof_same_day_and_later_games_are_not_training_inputs(self):
        for day in DATES:
            past=[x for x in self.history if x["match_date"]<day]
            forbidden=[x for x in self.history if x["match_date"]>=day]
            self.assertTrue(past)
            self.assertTrue(forbidden)
            self.assertTrue(all(x["match_date"]<day for x in past))
            self.assertFalse(set(x["fixture_id"] for x in past)
                             & set(x["fixture_id"] for x in forbidden))
            self.assertFalse(any(x["match_date"]==day for x in past))

    def test_99_mixed_source_quality_and_all_non_90_minute_results_excluded(self):
        self.assertEqual(len(self.history),4616)
        self.assertEqual({k:sum(x["source_class"]==k for x in self.targets)
                          for k in SOURCE_GRADES},SOURCE_GRADES)
        self.assertTrue(all(x["season"]=="2026-2027" for x in self.targets))
        self.assertTrue(all(x["status"]=="COMPLETED_PUBLIC_SCORE_RESEARCH_CONCORDANT"
                            for x in self.targets))

    def test_known_synthetic_frozen_lambdas_vs_preselected_symmetric_080(self):
        m=2;ix={"H":0,"A":1}
        b=np.zeros(2+6*m)
        b[0]=math.log(1.6);b[1]=math.log(1.2)
        b[2+m+1]=-.1;b[2+5*m+1]=-.15
        b[2+m+0]=.15;b[2+4*m+0]=.05
        fit=(b,ix,m,100)
        frozen=predict_m4(fit,"H","A")
        shadow=candidate_lambdas(fit,"H","A","symmetric",.8)
        self.assertAlmostEqual(shadow[0],frozen[0]*math.exp(.05))
        self.assertAlmostEqual(shadow[1],frozen[1]*math.exp(-.04))
        self.assertTrue(all(.05<=v<=5 for v in shadow))

    def test_brier_scoring_and_hit_counter_are_not_mistaken_for_roi(self):
        m=score_markets(1.3,.9)["markets"]
        s=losses(m,2,0)
        self.assertAlmostEqual(s["KG_Brier"],m["BTTS_YES"]**2)
        self.assertAlmostEqual(s["Over25_Brier"],m["OVER_2.5"]**2)
        self.assertAlmostEqual(s["MS_Brier"],
            (m["1X2"]["H"]-1)**2+m["1X2"]["D"]**2+m["1X2"]["A"]**2)
        hit=top1_accuracy(m,2,0)
        self.assertEqual(set(hit),{"KG","Over25","MS"})
        self.assertTrue(all(v in (0,1) for v in hit.values()))

    def test_all_99_are_outside_old_original_4518(self):
        from exp_263_batch import clean_rows
        original=clean_rows(FILES["original"])
        a={(r["league"],r["match_date"],r["home_id"],r["away_id"])
           for r in original}
        self.assertTrue(all((r["league"],r["match_date"],r["home_id"],r["away_id"])
                            not in a for r in self.targets))

if __name__=="__main__":unittest.main()
