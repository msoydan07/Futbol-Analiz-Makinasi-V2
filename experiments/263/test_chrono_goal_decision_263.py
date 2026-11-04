import unittest
from chrono_goal_decision_263 import outcome,base,shrink_weights,select
class SingleBatchContract(unittest.TestCase):
 def test_nested_events(self):
  a={"home_goals":"2","away_goals":"0"}
  self.assertEqual(outcome(a,"OVER_1.5"),1)
  self.assertEqual(outcome(a,"OVER_2.5"),0)
 def test_baseline_only_past_passed_in(self):
  a=[{"home_goals":"2","away_goals":"0"} for _ in range(70)]
  self.assertEqual(base(a)["OVER_2.5"],0.)
 def test_no_development_blocks_t2_calibration(self):
  self.assertFalse(shrink_weights([])["OVER_1.5"]["available"])
 def test_c2_absence_never_promotes_experimental(self):
  self.assertEqual(select({"p":{"M4":{}},"base":None},"T0_original_75_70",{})[2],"C2_CONTEXT_MISSING")
 def test_s2_never_included(self):
  self.assertNotIn("S2",tuple(select({"p":{},"base":None},"T1_relaxed_70_65",{})))
if __name__=="__main__":unittest.main()
