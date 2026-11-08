import hashlib,json,unittest
from datetime import timedelta
from test_prospective_seal import NOW,candidate
from prospective_seal import digest,SCHEMA
from paired_future_gate import join,NotComparable

def data():
 c=candidate()
 f=c["fixture"]
 o={"schema":"quad_forward_263_v1","created_at_utc":c["created_at_utc"],
    "fixture":{"league":f["league"],"home_id":f["home_id"],
               "away_id":f["away_id"],"kickoff_utc":f["kickoff_utc"]},
    "model_predictions":{"M4":{"status":"AVAILABLE","goals":{
      "markets":{"1X2":{"H":.50,"D":.24,"A":.26}}}}}}
 raw=json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
 o["payload_sha256"]=hashlib.sha256(raw).hexdigest()
 r={"schema":SCHEMA,"candidate":c,"research_only":True,
    "betting_authorized":False,"validated_at_utc":NOW.isoformat()}
 r["payload_sha256"]=digest(r)
 return o,r

class GateTests(unittest.TestCase):
 def test_valid_identity_pair(self):
  o,r=data()
  j=join(o,r)
  self.assertEqual(j["status"],"PAIRED_IDENTITY_AND_TIMING_ONLY")
  self.assertEqual(j["m4"]["H"],.50)
  self.assertFalse(j["betting_authorized"])
 def test_modified_original_sha_fails(self):
  o,r=data();o["model_predictions"]["M4"]["goals"]["markets"]["1X2"]["H"]=.7
  with self.assertRaises(NotComparable):join(o,r)
 def test_bad_research_sha_fails(self):
  o,r=data();r["candidate"]["fixture"]["home_id"]="alien-club"
  with self.assertRaises(NotComparable):join(o,r)
 def test_different_kickoff_fails(self):
  o,r=data();r["candidate"]["fixture"]["kickoff_utc"]=(NOW+timedelta(hours=4)).isoformat()
  r["payload_sha256"]=digest({k:v for k,v in r.items() if k!="payload_sha256"})
  with self.assertRaises(NotComparable):join(o,r)
 def test_cutoff_mismatch_fails(self):
  o,r=data();o["created_at_utc"]=(NOW-timedelta(hours=2)).isoformat()
  o["payload_sha256"]=hashlib.sha256(json.dumps(
      {k:v for k,v in o.items() if k!="payload_sha256"},
      sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
  with self.assertRaises(NotComparable):join(o,r)
if __name__=="__main__":unittest.main()
