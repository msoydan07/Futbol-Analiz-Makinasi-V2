"""Only the newly added no-vig isolated algebra. Never retests old model fits."""
import unittest

from secondary_price_vs_quad_263 import no_vig

class SecondaryMarketMathTests(unittest.TestCase):
 def test_ms_three_outcomes_have_normalized_fair_probabilities(self):
  fair,margin=no_vig({"MS1":2.50,"MSX":3.30,"MS2":2.72})
  self.assertAlmostEqual(sum(fair.values()),1.0,places=12)
  self.assertAlmostEqual(fair["MS2"],0.3433780071589,places=8)
  self.assertAlmostEqual(margin,0.0706724,places=5)
 def test_ou_complete_pair_math(self):
  fair,_=no_vig({"UNDER_2.5":1.95,"OVER_2.5":1.91})
  self.assertAlmostEqual(fair["UNDER_2.5"]+fair["OVER_2.5"],1.0)
 def test_impossible_price(self):
  with self.assertRaisesRegex(ValueError,"invalid_secondary_odds"):
   no_vig({"MS1":2.0,"MSX":0.0,"MS2":3.0})
 def test_below_one_margin(self):
  with self.assertRaisesRegex(ValueError,"invalid_or_implausible"):
   no_vig({"MS1":7.0,"MSX":7.0,"MS2":7.0})

if __name__=="__main__":unittest.main()
