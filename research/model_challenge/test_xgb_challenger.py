import unittest
try:
    from xgb_challenger import make_features
except ModuleNotFoundError:
    make_features = None

@unittest.skipIf(make_features is None, 'ML dependencies installed in the dedicated XGBoost workflow')
class FeatureTests(unittest.TestCase):
 def row(self,day,h,a,hg,ag):
  return dict(date=day,league="ENG1",home=h,away=a,
              home_goals=str(hg),away_goals=str(ag))
 def test_no_same_day_score_leakage(self):
  rows=[self.row("2024-01-01","A","B",7,0),
        self.row("2024-01-01","A","C",1,1),
        self.row("2024-01-02","A","D",0,1)]
  a=make_features(rows)
  rows[0]["home_goals"],rows[0]["away_goals"]="0","7"
  b=make_features(rows)
  self.assertEqual(a[0][1],b[0][1])
  self.assertEqual(a[1][1],b[1][1])
  self.assertNotEqual(a[2][1],b[2][1])
 def test_feature_vector_is_numeric_finite(self):
  import math
  rows=[self.row("2024-01-01","A","B",1,0)]
  feats=make_features(rows)[0][1]
  self.assertTrue(feats)
  self.assertTrue(all(isinstance(x,(float,int)) and math.isfinite(x) for x in feats))
 def test_order_is_date_sorted(self):
  rows=[self.row("2024-01-02","A","B",1,0),
        self.row("2024-01-01","C","D",1,0)]
  self.assertEqual(make_features(rows)[0][0]["date"],"2024-01-01")
if __name__=="__main__": unittest.main()
