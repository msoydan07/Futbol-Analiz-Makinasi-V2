"""Unit tests ONLY: full 10-league comparison runs once in CI executable."""
import math,sys,unittest
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from m4_opponent_defence_shrinkage_263 import (
    archive_and_lock,defence_effects,candidate_lambdas,band,losses,
    paired_date_ci,AuditError,VARIANTS,PINS
)
sys.path.insert(0,str(ROOT/"experiments/263"))
from m4_integrated import predict_m4,score_markets

class DefenceDampingSafetyTests(unittest.TestCase):
    def setUp(self):
        m=3;ix={"HOME":0,"AWAY":1,"OTHER":2}
        beta=np.zeros(2+6*m)
        beta[0]=math.log(1.6);beta[1]=math.log(1.1)
        beta[2+m+ix["AWAY"]]=-.2
        beta[2+5*m+ix["AWAY"]]=-.3
        beta[2+m+ix["HOME"]]=.1
        beta[2+4*m+ix["HOME"]]=.2
        self.fit=(beta,ix,m,100)

    def test_frozen_model_exact_when_weight_one(self):
        original=predict_m4(self.fit,"HOME","AWAY")
        ref=candidate_lambdas(self.fit,"HOME","AWAY","original",1.)
        self.assertEqual(ref,original)
        self.assertAlmostEqual(original[0],1.6*math.exp(-.5),places=11)
        self.assertAlmostEqual(original[1],1.1*math.exp(.3),places=11)

    def test_selected_away_defence_reduction_changes_only_home_lambda(self):
        lh,la=predict_m4(self.fit,"HOME","AWAY")
        d1,d2=defence_effects(self.fit,"HOME","AWAY")
        self.assertAlmostEqual(d1,-.5,places=11)
        self.assertAlmostEqual(d2,.3,places=11)
        for weight in (.9,.8):
            a,b=candidate_lambdas(self.fit,"HOME","AWAY","away_only",weight)
            self.assertAlmostEqual(a,lh*math.exp((weight-1)*(-.5)),places=11)
            self.assertEqual(b,la)
            self.assertGreater(a,lh)

    def test_symmetric_defences_modify_both_scoring_lambdas(self):
        lh,la=predict_m4(self.fit,"HOME","AWAY")
        x,y=candidate_lambdas(self.fit,"HOME","AWAY","symmetric",.8)
        self.assertAlmostEqual(x,lh*math.exp(.1),places=11)
        self.assertAlmostEqual(y,la*math.exp(-.06),places=11)
        self.assertLess(y,la)

    def test_missing_teams_are_not_silently_average_for_experiment(self):
        with self.assertRaisesRegex(AuditError,"UNSEEN"):
            candidate_lambdas(self.fit,"UNSEEN","AWAY","away_only",.9)
        with self.assertRaisesRegex(AuditError,"UNSEEN"):
            defence_effects(self.fit,"HOME","UNKNOWN")

    def test_no_unregistered_weight_or_mode_and_expected_goal_safety(self):
        for mode,weight in (("away_only",.77),("symmetric",.5),("other",.9)):
            with self.assertRaisesRegex(AuditError,"UNPREDECLARED"):
                candidate_lambdas(self.fit,"HOME","AWAY",mode,weight)

    def test_scoring_definitions_are_exact_for_all_markets(self):
        m=score_markets(1.2,.8)["markets"]
        x=losses(m,2,1)
        self.assertAlmostEqual(x["KG_Brier"],(1-m["BTTS_YES"])**2)
        self.assertAlmostEqual(x["Over25_Brier"],(1-m["OVER_2.5"])**2)
        self.assertAlmostEqual(x["MS_Brier"],
             (1-m["1X2"]["H"])**2+m["1X2"]["D"]**2+m["1X2"]["A"]**2)

    def test_day_block_confidence_not_calculated_with_one_day(self):
        self.assertIsNone(paired_date_ci([
            {"date":"2025-11-20","deltas":{"KG_Brier":.01}}
            for _ in range(140)],"KG_Brier"))
        many=[{"date":f"2025-11-{i%12+1:02d}","deltas":{"KG_Brier":(i%3-1)*.01}}
              for i in range(120)]
        ci=paired_date_ci(many,"KG_Brier",reps=100)
        self.assertIsNotNone(ci)
        self.assertEqual(ci["dates"],12)

    def test_pin_archive_validation_does_not_evaluate_holdout(self):
        dev,settings,full,excluded=archive_and_lock()
        self.assertEqual(full,4616)
        self.assertEqual(excluded,1)
        self.assertTrue(all(x["season"]=="2025-2026" and
                            x["match_date"]<"2026-07-01" for x in dev))
        self.assertGreater(len(dev),1000)
        self.assertEqual(len(VARIANTS),5)

if __name__=="__main__":
    unittest.main()
