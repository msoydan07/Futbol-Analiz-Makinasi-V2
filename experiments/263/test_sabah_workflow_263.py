"""Synthetic offline acceptance: no football-model fitting and NO API credits."""
import json,os,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
from sabah_batch_263 import named,run,precommit,sha,save_new,Blocked
from sabah_mobile_screens_263 import build,ScreenError
from sabah_pinnacle_capture_263 import eligible,capture
from sabah_pinnacle_credit_guard_263 import reserve,AlreadyReserved
NOW=datetime(2026,11,7,6,0,tzinfo=timezone.utc)
KO=datetime(2026,11,7,14,0,tzinfo=timezone.utc)
def gate(league,home,away):
 return {"status":"VERIFIED","league":league,"home_id":"HomeID","away_id":"AwayID",
         "kickoff_utc":KO.isoformat(),"retrieved_at_utc":NOW.isoformat(),
         "source_url":"https://www.tff.org/synthetic"}

def fake_predict(g,history,out_dir,lock,now=None,base=None,source_audit=None):
 p=Path(out_dir)/"2026-11-07"/("a"*24+".json")
 x={"schema":"quad_forward_263_v1","status":"EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING",
    "created_at_utc":now.isoformat(),"fixture":{
    "league":g["league"],"home_id":g["home_id"],"away_id":g["away_id"],
    "match_local_date":"2026-11-07","kickoff_utc":g["kickoff_utc"],
    "official_source":g["source_url"],
    "fixture_verification":"VERIFIED_BY_LIVE_OFFICIAL_GATE"},
    "model_predictions":{}}
 for m in ("B","C2","C3","M4"):
  raw={"1X2":{"H":.5,"D":.3,"A":.2},
       "BTTS_YES":.58,"BTTS_NO":.42,
       "OVER_1.5":.8,"UNDER_1.5":.2,
       "OVER_2.5":.55,"UNDER_2.5":.45,
       "OVER_3.5":.31,"UNDER_3.5":.69}
  x["model_predictions"][m]={"status":"AVAILABLE","goals":{"markets":raw}}
 x["payload_sha256"]=sha(x)
 save_new(p,x)
 return p,x

def fake_baseline(f,history,now=None):
 x={"schema":"test_baseline","forecast_sha256":f["payload_sha256"]}
 x["payload_sha256"]=sha(x);return x

def fake_decision(f,b,l,observation=None,now=None):
 x={"schema":"263_four_model_value_decision_research_v1",
    "forecast_sha256":f["payload_sha256"],"betting_authorized":False,
    "status":"RESEARCH_PAS","quote_sha256":None,
    "main_candidate":None,"alternative_candidate":None,
    "all_market_diagnostics":[
      {"market":"MS1","calibrated_probability":.51},
      {"market":"MSX","calibrated_probability":.29},
      {"market":"MS2","calibrated_probability":.20}],
    "high_probability_alerts_not_bets":[]}
 x["payload_sha256"]=sha(x);return x

class Acceptance(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.old=os.getcwd();os.chdir(self.temp.name)
  Path("experiments/263/sabah_requests").mkdir(parents=True)
  self.manifest=Path("experiments/263/sabah_requests/new100_demo.json")
  self.manifest.write_text(json.dumps({
   "schema":"SABAH_TOPLU_V1","day_turkey":"2026-11-07",
   "matches":[{"league":"TUR1","home":"A","away":"B"}]}),encoding="utf-8")
  for p in ("history.csv","base.csv","acceptance.json","lock.json"):
   Path(p).write_text("{}")
 def tearDown(self):
  os.chdir(self.old);self.temp.cleanup()
 def create(self,now=NOW):
  return run("new100","2026-11-07",self.manifest,
     "history.csv","base.csv","acceptance.json","lock.json",
     now=now,lookup=gate,predictor=fake_predict,
     baseline_fn=fake_baseline,decision_fn=fake_decision,dev_lock_path='lock.json')
 def test_new100_is_separate_from_96_and_SHA(self):
  r=self.create()
  self.assertEqual(r["new_forecasts"],1)
  self.assertTrue(r["outcomes"][0]["forecast_path"].startswith("forward_morning_263/"))
  self.assertTrue(precommit(r,now=NOW))
  self.assertFalse(Path("forward_quad_263").exists())
 def test_mobile_same_locked_SHA(self):
  r=self.create();summary,details=build(".",r)
  self.assertIn("MS 1: 51,0%",summary)
  self.assertIn(r["outcomes"][0]["forecast_sha256"],next(iter(details.values())))
  self.assertIn("B / C2 / C3 / M4",next(iter(details.values())))
 def test_duplicate_does_not_write_again(self):
  r=self.create()
  next_result=self.create()
  self.assertEqual(next_result["already_sealed"],1)
  self.assertEqual(next_result["new_forecasts"],0)
 def test_reject_future_and_past_day(self):
  with self.assertRaises(Blocked):self.create(NOW-timedelta(days=1))
 def test_ko_precommit_fails(self):
  r=self.create()
  with self.assertRaises(Blocked):precommit(r,now=KO)
 def test_reject_tampered_input(self):
  obj=json.loads(self.manifest.read_text());obj["matches"][0]["away"]="A"
  self.manifest.write_text(json.dumps(obj))
  with self.assertRaises(Blocked):named("new100","2026-11-07",self.manifest)
 def test_no_odds_credit_without_fresh_forecast(self):
  r=self.create()
  self.assertEqual(eligible(r,".",NOW),["TUR1"])
  self.assertEqual(eligible(r,".",NOW+timedelta(minutes=12)),[])
 def test_daily_reservation_survives_failure(self):
  p,_=reserve("ledger","TUR1",NOW)
  with patch("sabah_pinnacle_capture_263.collect",side_effect=ValueError("synthetic_http_error")) as f:
   outcome=capture("ledger","TUR1","2026-11-07","cache/snapshot.json","dummy-key",NOW)
  self.assertEqual(f.call_count,1)
  self.assertEqual(outcome["status"],"UNAVAILABLE_NO_RETRY")
  with self.assertRaises(AlreadyReserved):reserve("ledger","TUR1",NOW)
  with self.assertRaises(ValueError):capture("ledger","TUR1","2026-11-07","cache/snapshot.json","dummy-key",NOW)
 def test_sealed_receipt_and_empty_source(self):
  reserve("ledger","TUR1",NOW)
  body={"schema":"263_free_bulk_external_odds_research_v1",
       "day_turkey":"2026-11-07","blocked":{},"leagues":{"TUR1":[]},"reported_remaining_credits":123}
  with patch("sabah_pinnacle_capture_263.collect",return_value=body) as fake:
   out=capture("ledger","TUR1","2026-11-07","cache/receipt.json","key",NOW)
  self.assertEqual(fake.call_count,1)
  self.assertEqual(out["remaining_credits_as_returned"],123)
  self.assertEqual(out["source_bulk"]["leagues"]["TUR1"],[])
if __name__=="__main__":unittest.main()
