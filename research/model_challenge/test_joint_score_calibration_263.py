"""Core invariants for chronology-safe, coherent score calibration."""
import unittest
try:
 import numpy as np
 from joint_score_calibration_263 import get_predictions,WEIGHTS, asof_empirical
 from goal_market_distribution_challenge import matrix,probs
except ModuleNotFoundError:
 np=None

@unittest.skipIf(np is None,"scientific packages installed in dedicated workflow")
class JointCalibrationTests(unittest.TestCase):
 def test_score_mix_coherent(self):
  prior=np.zeros((41,41));prior[0,0]=.35;prior[1,1]=.65
  m4=matrix(1.6,1.25,kind="independent")
  rows=[{"m4":m4,"ref":prior}]
  for w in WEIGHTS:
   p=get_predictions(rows,w)[0]
   self.assertAlmostEqual(sum(p[z] for z in ("MS_H","MS_D","MS_A")),1)
   self.assertTrue(p["OVER_1.5"]>=p["OVER_2.5"]>=p["OVER_3.5"])
   self.assertGreaterEqual(p["BTTS_YES"],0)
   self.assertLessEqual(p["BTTS_YES"],1)
 def test_earlier_only_empirical_distribution(self):
  prior=[{"date":"2025-10-04","league":"ENG1",
    "home_goals":"1","away_goals":"1"} for _ in range(110)]
  future=[{"date":"2026-10-02","league":"ENG1",
    "home_goals":"17","away_goals":"2"}]
  first=asof_empirical(prior,"ENG1","2026-10-01")
  second=asof_empirical(prior+future,"ENG1","2026-10-01")
  np.testing.assert_allclose(first,second)
  self.assertAlmostEqual(first.sum(),1)
if __name__=="__main__":unittest.main()
