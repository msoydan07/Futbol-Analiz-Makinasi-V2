"""Mathematical invariants for coherent goal-market research candidates."""
import math,unittest
try:
 from goal_market_distribution_challenge import matrix,probs,candidates,actual
except ModuleNotFoundError:
 matrix=None

@unittest.skipIf(matrix is None,"scientific dependencies available in dedicated workflow")
class CoherentMarkets(unittest.TestCase):
 def test_every_candidate_valid_and_consistent(self):
  for family,opts in candidates().items():
   for c in opts:
    with self.subTest(candidate=c):
     p=matrix(1.4,1.2,**c)
     self.assertAlmostEqual(float(p.sum()),1.,places=8)
     self.assertTrue((p>=0).all())
     m=probs(p)
     self.assertAlmostEqual(sum(m[x] for x in ("MS_H","MS_D","MS_A")),1.)
     self.assertTrue(m["OVER_1.5"]>=m["OVER_2.5"]>=m["OVER_3.5"])
     self.assertTrue(all(0<=v<=1 for v in m.values()))
 def test_identity_candidates_match_exact_independent(self):
  base=matrix(1.5,1.7,kind="independent")
  from numpy.testing import assert_allclose
  assert_allclose(base,matrix(1.5,1.7,kind="dc",rho=0.),atol=1e-12)
  assert_allclose(base,matrix(1.5,1.7,kind="bivar",cov=0.),atol=1e-12)
  assert_allclose(base,matrix(1.5,1.7,kind="scaled",scale=1.),atol=1e-12)
 def test_dc_changes_low_scores_but_preserves_marginals(self):
  p=matrix(1.5,1.3,kind="dc",rho=-.1)
  base=matrix(1.5,1.3,kind="independent")
  self.assertGreater(p[0,0],base[0,0])
  from numpy.testing import assert_allclose
  assert_allclose(p.sum(axis=0),base.sum(axis=0),atol=1e-10)
  assert_allclose(p.sum(axis=1),base.sum(axis=1),atol=1e-10)
 def test_bivariate_preserves_marginal_means(self):
  import numpy as np
  p=matrix(1.5,1.7,kind="bivar",cov=.2)
  idx=np.arange(p.shape[0])
  self.assertAlmostEqual(float(idx@p.sum(axis=1)),1.5,places=5)
  self.assertAlmostEqual(float(idx@p.sum(axis=0)),1.7,places=5)
 def test_0_0_groundtruth(self):
  y=actual(0,0)
  self.assertEqual(y["BTTS_YES"],0)
  self.assertEqual(y["OVER_2.5"],0)
  self.assertEqual(y["MS_D"],1)
if __name__=="__main__":unittest.main()
