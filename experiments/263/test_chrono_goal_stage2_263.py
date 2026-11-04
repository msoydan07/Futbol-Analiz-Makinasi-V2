import unittest
from chrono_goal_stage2_263 import group,calibration,choose
class ReusedPredictionTests(unittest.TestCase):
 def test_nested_goal_family(self):
  self.assertEqual(group("OVER_1.5"),group("OVER_2.5"))
  self.assertNotEqual(group("BTTS_YES"),group("OVER_2.5"))
 def test_no_dev_does_not_fabricate_model_weights(self):
  c=calibration([],"M4")
  self.assertFalse(c["OVER_1.5"]["available"])
 def test_undeveloped_calibrator_returns_pas(self):
  r={"p":{"M4":{}},"base":{},"obs":{}}
  weights={m:{"available":False} for m in ["MS1","MSX","MS2","OVER_1.5","UNDER_1.5","OVER_2.5","UNDER_2.5","OVER_3.5","UNDER_3.5","BTTS_YES","BTTS_NO"]}
  self.assertIsNone(choose(r,"M4",weights,True)[0])
 def test_unavailable_model_cannot_self_promote(self):
  self.assertEqual(choose({"p":{}},"C3",{},True)[2],"MODEL_MISSING")
if __name__=="__main__":unittest.main()
