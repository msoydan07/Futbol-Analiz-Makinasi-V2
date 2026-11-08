import unittest
from paired_audit import score,probability,unique_index,block_interval

class PairedAuditTests(unittest.TestCase):
 def test_score(self):
  ll,b=score((.6,.25,.15),"H")
  self.assertGreater(ll,0)
  self.assertAlmostEqual(b,.4*.4+.25*.25+.15*.15)
 def test_probability_rejects_bad_sum(self):
  with self.assertRaises(ValueError):
   probability({"p_home":".7","p_draw":".3","p_away":".3"})
 def test_duplicate_fixture_blocked(self):
  row={"league":"ENG1","date":"2025-09-01","home":"A","away":"B"}
  with self.assertRaises(ValueError):
   unique_index([row,row])
 def test_date_block_pair_interval(self):
  rows=[{"date":"2025-01-01","a":.2,"b":.1},
        {"date":"2025-01-01","a":.4,"b":.3},
        {"date":"2025-01-02","a":.5,"b":.4}]
  lo,hi=block_interval(rows,"a","b",iterations=200)
  self.assertAlmostEqual(lo,.1)
  self.assertAlmostEqual(hi,.1)
if __name__=="__main__":
 unittest.main()
