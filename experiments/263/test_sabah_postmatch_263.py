import hashlib,unittest
from sabah_postmatch_263 import canonical,scores,evaluate
def seal(x):
 x.pop('payload_sha256',None);x['payload_sha256']=hashlib.sha256(canonical(x)).hexdigest();return x
def fixture():
 f=seal({'schema':'quad_forward_263_v1','model_predictions':{m:{'status':'AVAILABLE','goals':{'markets':{'1X2':{'H':.5,'D':.3,'A':.2}}}} for m in ('B','C2','C3','M4')}})
 p=seal({'schema':'263_pinnacle_readonly_benchmark_v1','status':'READ_ONLY_SAME_TIME_BENCHMARK','forecast_sha256':f['payload_sha256'],'bookmaker':'pinnacle','pinnacle_no_vig_probabilities':{'H':.4,'D':.3,'A':.3}})
 return f,p
class Tests(unittest.TestCase):
 def test_score(self):self.assertAlmostEqual(scores({'H':.5,'D':.3,'A':.2},'H')['brier'],.38)
 def test_common(self):
  f,p=fixture();self.assertEqual(evaluate([{'forecast':f,'pinnacle':p,'official_result':'H','result_verified':True}])['common_five_source_n'],1)
 def test_unverified(self):
  f,p=fixture();self.assertEqual(evaluate([{'forecast':f,'official_result':'H','result_verified':False}])['verified_results'],0)
 def test_tamper(self):
  f,p=fixture();f['model_predictions']['B']['status']='UNAVAILABLE'
  with self.assertRaises(ValueError):evaluate([{'forecast':f,'official_result':'H','result_verified':True}])
 def test_wrong_market_link(self):
  f,p=fixture();p['forecast_sha256']='wrong';seal(p)
  self.assertEqual(evaluate([{'forecast':f,'pinnacle':p,'official_result':'H','result_verified':True}])['common_five_source_n'],0)
 def test_duplicate(self):
  f,p=fixture();row={'forecast':f,'official_result':'H','result_verified':True}
  with self.assertRaises(ValueError):evaluate([row,row])
if __name__=='__main__':unittest.main()
