"""Offline-only tests of pre-kickoff inference with synthetic football data.
An external fixture provider is deliberately NOT mocked as independently
authenticated; these tests prove schema and time guards, not source truth.
"""
from __future__ import annotations
import csv,json,tempfile,unittest
from datetime import date,datetime,timezone,timedelta
from pathlib import Path
try:
 import numpy as np
 from xgb_challenger import make_features
 from xgb_live_inference import feature_at,load_history,inference,MAX_FEATURES
except ModuleNotFoundError:
 np = None

UTC=timezone.utc
NOW=datetime(2026,11,9,10,0,tzinfo=UTC)
def synthetic_rows(n=1200):
    start=date(2023,8,1)
    rows=[]
    for i in range(n):
        d=start+timedelta(days=i)
        rows.append({"league":"ENG1" if i%2==0 else "GER1",
          "date":d.isoformat(),"home":"Club A" if i%4<2 else "Club B",
          "away":"Club C" if i%4<2 else "Club D",
          "home_goals":str(i%4),"away_goals":str((i+2)%3)})
    return rows

def manifest(now=NOW):
    return {"schema":"MC_VERIFIED_FIXTURE_INPUT_V1",
      "fixture_id":"synthetic-123","league":"ENG1",
      "home_name":"Club A","away_name":"Club C",
      "home_id":"official-home-123","away_id":"official-away-456",
      "kickoff_utc":(now+timedelta(days=2,hours=2)).isoformat(),
      "official_fixture_url":"https://example.org/fictional-only",
      "source_verified_at_utc":(now-timedelta(minutes=3)).isoformat(),
      "history_asof_utc":(now-timedelta(hours=23)).isoformat(),
      "fixture_verified_by":"EXTERNAL_OFFICIAL_GATE"}

@unittest.skipIf(np is None, "ML deps only in dedicated inference QA")
class PreKickoffTests(unittest.TestCase):
 def write_rows(self,path,rows):
  with open(path,"w",encoding="utf8",newline="") as f:
   w=csv.DictWriter(f,fieldnames=rows[0])
   w.writeheader();w.writerows(rows)

 def test_feature_parity_against_historical_training_path(self):
  rows=synthetic_rows(105)
  historical=make_features(rows)
  # A historical match's features should be identical to inference built
  # from only strictly earlier dates, with the same league encoder universe.
  for item in historical[85:100]:
   r,legacy,_,_=item
   before=[z for z in rows if z["date"]<r["date"]]
   a,_=feature_at(before,r["league"],r["home"],r["away"],
                  date.fromisoformat(r["date"]))
   np.testing.assert_allclose(a,np.array(legacy,dtype=np.float32),
                              rtol=0,atol=0)
   self.assertEqual(len(a),MAX_FEATURES)

 def test_predict_with_no_fixture_result_and_preserved_source_ids(self):
  with tempfile.TemporaryDirectory() as t:
   h=Path(t,"history.csv");f=Path(t,"manifest.json")
   rows=[r for r in synthetic_rows() if r["date"]<
          (NOW-timedelta(days=1)).date().isoformat()]
   self.write_rows(h,rows)
   f.write_text(json.dumps(manifest()),encoding="utf8")
   candidate,details=inference(h,f,now=NOW)
   self.assertEqual(candidate["fixture"]["home_id"],"official-home-123")
   self.assertEqual(candidate["models"]["XGBoost"]["status"],"AVAILABLE")
   self.assertEqual(candidate["models"]["Elo"]["status"],"PAS")
   self.assertAlmostEqual(sum(candidate["models"]["XGBoost"]["probabilities"].values()),1)
   self.assertGreater(details["training_matches"],1000)
   from prospective_seal import seal,Rejected
   sealed,sha=seal(candidate,t,now=NOW)
   self.assertTrue(sealed.exists())
   self.assertEqual(json.loads(sealed.read_text())["payload_sha256"],sha)
   with self.assertRaises(Rejected):
    seal(candidate,t,now=NOW)

 def test_false_claim_without_external_gate_fails(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t,"manifest.json");m=manifest()
   m["fixture_verified_by"]="SELF_ASSERTED"
   f.write_text(json.dumps(m),encoding="utf8")
   with self.assertRaisesRegex(ValueError,"unverified fixture"):
    inference("/does/not/exist",f,now=NOW)

 def test_reject_same_day_or_future_score(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t,"history.csv")
   rows=synthetic_rows(6)
   rows.append({**rows[0],"date":"2026-11-11"})
   self.write_rows(p,rows)
   with self.assertRaisesRegex(ValueError,"fixture date or later"):
    load_history(p,date(2026,11,11))

 def test_missing_identity_fails(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t,"manifest.json");m=manifest()
   m["home_id"]=""
   f.write_text(json.dumps(m),encoding="utf8")
   with self.assertRaisesRegex(ValueError,"identities"):
    inference("/does/not/exist",f,now=NOW)

 def test_fixture_after_start_fails(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t,"manifest.json");m=manifest()
   m["kickoff_utc"]=(NOW-timedelta(minutes=1)).isoformat()
   f.write_text(json.dumps(m),encoding="utf8")
   with self.assertRaises(ValueError):
    inference("/does/not/exist",f,now=NOW)

if __name__=="__main__":
 unittest.main()
