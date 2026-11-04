import unittest
from overline_fairness_263 import compare,baseline,report
class NestedLinesTests(unittest.TestCase):
 def test_25_not_disfavored_just_for_lower_raw_p(self):
  r=compare(.83,.68,.78,.52)
  self.assertEqual(r["raw_p_winner"],"OVER_1.5")
  self.assertEqual(r["baseline_research_winner"],"OVER_2.5")
  self.assertFalse(r["S1_approved"])
 def test_15_may_win_when_evidently_above_own_baseline(self):
  r=compare(.94,.60,.77,.54)
  self.assertEqual(r["baseline_research_winner"],"OVER_1.5")
 def test_no_positive_lift(self):
  self.assertIsNone(compare(.71,.46,.77,.54)["baseline_research_winner"])
 def test_alt_correlated_with_main(self):
  self.assertTrue(compare(.9,.7,.77,.54)["nested_goals_not_independent_alternatives"])
 def test_nested_wrong(self):
  with self.assertRaisesRegex(ValueError,"nested_goal"):compare(.65,.70,.77,.54)
 def test_asof_excludes_target_result(self):
  rows=[{"league":"TUR1","match_date":"2026-10-01","home_goals":"2","away_goals":"0"} for _ in range(100)]
  rows.extend({"league":"TUR1","match_date":"2026-11-06","home_goals":"0","away_goals":"0"} for _ in range(250))
  b=baseline(rows,"TUR1","2026-11-06")
  self.assertEqual(b["n"],100);self.assertEqual(b["p15"],1.0)
 def test_insufficient_data(self):
  with self.assertRaisesRegex(ValueError,"insufficient"):baseline([],"TUR1","2026-11-06")
 def test_invalid_p(self):
  with self.assertRaisesRegex(ValueError,"bad_probability"):compare(-.1,.4,.77,.54)
 def test_not_original_sha(self):
  with self.assertRaisesRegex(ValueError,"wrong_forecast"):report({"payload_sha256":"fake"},[],"fake")
 def test_tie_more_specific_line_not_automatically_15(self):
  self.assertEqual(compare(.80,.57,.75,.52)["baseline_research_winner"],"OVER_2.5")
if __name__=="__main__":unittest.main()