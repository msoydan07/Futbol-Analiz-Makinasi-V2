"""Deterministic tests for the experimental Poisson engine; no network."""
import unittest
from experimental_poisson_baseline import estimate,poisson

def match(i,day,home="A",away="B",hg=2,ag=1,league="ENG1"):
 return {"fixture_id":str(i),"league":league,"match_date":day,"home_id":home,"away_id":away,"home_goals":str(hg),"away_goals":str(ag),"result":"H" if hg>ag else "D" if hg==ag else "A"}

class PoissonBaselineTests(unittest.TestCase):
 def setUp(self):
  self.rows=[]
  for i in range(1,41):
   self.rows.append(match(i,f"2026-01-{i:02d}" if i<=28 else f"2026-02-{i-28:02d}",hg=2 if i%2 else 1,ag=i%2))
 def test_poisson_mass(self):
  self.assertAlmostEqual(sum(poisson(1.8,k) for k in range(30)),1.,places=10)
 def test_no_future_or_same_day_leakage(self):
  p=estimate(self.rows,"ENG1","A","B","2026-03-01")
  self.assertIsNotNone(p)
  altered=self.rows+[match(500,"2026-03-01",hg=20,ag=0),match(501,"2026-03-02",hg=0,ag=20)]
  self.assertEqual(p,estimate(altered,"ENG1","A","B","2026-03-01"))
 def test_other_league_excluded(self):
  p=estimate(self.rows,"ENG1","A","B","2026-03-01")
  extra=[match(i+1000,"2026-01-10",hg=10,ag=10,league="ITA1") for i in range(30)]
  self.assertEqual(p,estimate(self.rows+extra,"ENG1","A","B","2026-03-01"))
 def test_probability_and_matrix(self):
  p=estimate(self.rows,"ENG1","A","B","2026-03-01")
  self.assertAlmostEqual(p["p_home"]+p["p_draw"]+p["p_away"],p["matrix_mass"],places=10)
  self.assertLess(p["tail_mass"],0.01)
  self.assertTrue(all(0<=p[k]<=1 for k in ("p_home","p_draw","p_away","p_over25","p_btts")))
 def test_insufficient_data(self):
  self.assertIsNone(estimate(self.rows[:4],"ENG1","A","B","2026-03-01"))

if __name__=="__main__":unittest.main()
