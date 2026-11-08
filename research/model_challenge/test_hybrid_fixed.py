import unittest
from hybrid_fixed import WEIGHTS, pool

class HybridTests(unittest.TestCase):
 def test_constant_weights(self):
  self.assertEqual(set(WEIGHTS),{"Elo","Poisson","XGBoost"})
  self.assertAlmostEqual(sum(WEIGHTS.values()),1)
 def test_probability_pool(self):
  p=pool({"Elo":(.6,.25,.15),"Poisson":(.4,.3,.3),
          "XGBoost":(.5,.2,.3)})
  self.assertAlmostEqual(sum(p),1)
  self.assertAlmostEqual(p[0],.5)
 def test_missing_model_fails(self):
  with self.assertRaises(ValueError):
   pool({"Elo":(.6,.2,.2),"Poisson":(.5,.2,.3)})
 def test_bad_probability_fails(self):
  with self.assertRaises(ValueError):
   pool({"Elo":(2.,0.,0.),"Poisson":(.5,.2,.3),
         "XGBoost":(.5,.2,.3)})
if __name__=="__main__":
 unittest.main()
