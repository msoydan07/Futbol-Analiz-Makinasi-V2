import json,tempfile,unittest
from pathlib import Path
from model_b_reliability_note import assess

class Reliability(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.path=Path(self.tmp.name)/"audit.json"
  self.model={"markets":{"1x2":{"home":0.55,"draw":0.25,"away":0.20}}}
 def tearDown(self):self.tmp.cleanup()
 def test_missing_report_nonblocking(self):
  self.assertEqual(assess(self.model,self.path)["status"],"UNAVAILABLE")
 def test_overconfidence_warning(self):
  bins=[{"range":[i/10,(i+1)/10],"n":0,"predicted":None,"observed":None} for i in range(10)]
  bins[5]={"range":[0.5,0.6],"n":300,"predicted":0.55,"observed":0.49}
  self.path.write_text(json.dumps({"top_choice":bins}),encoding="utf-8")
  result=assess(self.model,self.path)
  self.assertEqual(result["level"],"OVERCONFIDENCE_WARNING")
  self.assertFalse(result["probabilities_changed"])
 def test_sparse_sample_caution(self):
  bins=[{"range":[i/10,(i+1)/10],"n":1,"predicted":0.5,"observed":0.5} for i in range(10)]
  self.path.write_text(json.dumps({"top_choice":bins}),encoding="utf-8")
  self.assertEqual(assess(self.model,self.path)["level"],"LIMITED_EVIDENCE")
if __name__=="__main__":unittest.main()
