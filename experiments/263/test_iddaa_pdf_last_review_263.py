"""Offline contract tests: 5-match same-time Bundesliga batch; NO model or PDF input."""
from __future__ import annotations
import copy,unittest
from datetime import datetime,timezone,timedelta
from iddaa_pdf_first_quote_263 import sha256
from iddaa_pdf_bulletin_263 import SCHEMA as BULLETIN
from iddaa_pdf_session_263 import SCHEMA as MORNING,market_no_vig
from iddaa_pdf_last_review_263 import build,summary_md

MOM="2026-11-21T09:10:00+00:00"
OPEN="2026-11-21T08:55:00+00:00"
CLOSE="2026-11-21T13:40:00+00:00"
NOW="2026-11-21T13:50:00+00:00"
KO="2026-11-21T14:30:00+00:00"
SEVEN={"MS1":1.70,"MSX":3.75,"MS2":4.80,"O25_OVER":1.88,"O25_UNDER":1.90,
       "BTTS_YES":1.80,"BTTS_NO":1.95}
LAST={"MS1":1.91,"MSX":3.45,"MS2":4.10,"O25_OVER":1.75,"O25_UNDER":2.05,
       "BTTS_YES":1.72,"BTTS_NO":2.10}
def make():
 first={"schema":BULLETIN,"source_domain":"iddaa.com",
        "pdf_sha256":"a"*64,"pdf_capture_utc":OPEN,"rows":[]}
 second={"schema":BULLETIN,"source_domain":"iddaa.com",
        "pdf_sha256":"b"*64,"pdf_capture_utc":CLOSE,"rows":[]}
 session={"schema":MORNING,"pdf_sha256":first["pdf_sha256"],
  "source_bookmaker":"iddaa.com","bookmaker_reverification_calls":0,
  "session_created_utc":MOM,"rows":[]}
 for n in range(5):
  home=f"Ev Takimi {n}";away=f"Dep Takimi {n}"
  first["rows"].append({"league":"GER1","home_label":home,"away_label":away,
     "match_date_tr":"2026-11-21","kickoff_time_tr":"17:30",
     "status":"PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK","odds":SEVEN})
  second["rows"].append({"league":"GER1","home_label":home,"away_label":away,
     "match_date_tr":"2026-11-21","kickoff_time_tr":"17:30",
     "status":"PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK","odds":LAST})
  session["rows"].append({
     "index":n,"league":"GER1","pdf_home":home,"pdf_away":away,
     "home_id":f"H{n}","away_id":f"A{n}",
     "match_date_tr":"2026-11-21","kickoff_time_tr":"17:30",
     "status":"FOUR_MODELS_FORECAST_SHA_CREATED","model_forecast_created":True,
     "model_forecast_sha256":f"{n+1:064x}",
     "price_capture_utc":OPEN,
     "prices":{"MS1":SEVEN["MS1"]},
     "market_no_vig":market_no_vig(first["rows"][-1]),
     "model_1x2_and_core_markets":{"M4":{"MS1":0.55,"MSX":0.25,"MS2":0.20,
         "OVER_2.5":0.54,"UNDER_2.5":0.46,
         "BTTS_YES":0.53,"BTTS_NO":0.47}},
     "official":{"kickoff_utc":KO}})
 session["signed_research_session_sha256"]=sha256(session)
 mapping={f"Ev Takimi {n}":f"H{n}" for n in range(5)}
 mapping.update({f"Dep Takimi {n}":f"A{n}" for n in range(5)})
 return session,first,second,lambda l,n:mapping.get(n)
def xi(session,with_change=False):
 m=session["rows"][0]
 x={"league":m["league"],"home_id":m["home_id"],"away_id":m["away_id"],
    "match_date_tr":m["match_date_tr"],"lineup_status":"CONFIRMED",
    "source_url":"https://example.org/match/1",
    "observed_at_utc":"2026-11-21T13:32:00+00:00",
    "home_starting_xi":[f"Ev {i}" for i in range(11)],
    "away_starting_xi":[f"Dep {i}" for i in range(11)],
    "observations":[]}
 if with_change:
  x["observations"]=[{"side":"HOME","category":"ATTACK",
   "fact":"As forvet ilk on birde bulunmuyor",
   "football_reason":"Takimin ileri uc tercihi degisti ve belirsizlik artti",
   "impact":"POSSIBLE_ATTACK_RISK",
   "source_url":"https://example.org/match/1"}]
 return x
class TestReview(unittest.TestCase):
 def test_all_five_no_guess_and_frozen(self):
  s,f,l,resolve=make()
  r=build(s,f,l,[],NOW,resolver=resolve)
  self.assertEqual(r["matches_reviewed"],5)
  self.assertTrue(all(x["status"]=="GUNCEL_ORAN_KAYDI_VE_KADRO_DURUMU_HAZIR" for x in r["rows"]))
  self.assertTrue(all(x["lineups"]["comments"]==[] for x in r["rows"]))
  self.assertFalse(r["math_refitted"])
  self.assertFalse(r["second_model_seal_created"])
  self.assertFalse(r["betting_authorized"])
  self.assertTrue(all(x["morning_model_sha256"]==f"{i+1:064x}" for i,x in enumerate(r["rows"])))
  self.assertIn("MS",r["rows"][0]["market_no_vig_change_pp"])
  self.assertIn("Yorum uydurulmadı",summary_md(r))
 def test_one_factual_claim_not_faked_new(self):
  s,f,l,resolve=make()
  a=build(s,f,l,[xi(s,True)],NOW,resolver=resolve)
  self.assertEqual(len(a["rows"][0]["lineups"]["comments"]),1)
  self.assertIn("SABAH_KIYASI_YOK",a["rows"][0]["lineups"]["comments"][0]["freshness"])
  self.assertFalse(a["rows"][0]["lineups"]["independently_verified_by_script"])
  self.assertTrue(all(not y["lineups"]["comments"] for y in a["rows"][1:]))
 def test_stale_wrong_team_wrong_timestamp_missing_lineup(self):
  s,f,l,resolve=make()
  d=xi(s,True);d["home_id"]="WRONG"
  a=build(s,f,l,[d],NOW,resolver=resolve)
  self.assertFalse(a["rows"][0]["lineups"]["comments"])
  d=xi(s,True);d["observed_at_utc"]="2026-11-21T10:00:00Z"
  a=build(s,f,l,[d],NOW,resolver=resolve)
  self.assertFalse(a["rows"][0]["lineups"]["comments"])
  d=xi(s,True);d["home_starting_xi"]=["A"]*11
  a=build(s,f,l,[d],NOW,resolver=resolve)
  self.assertFalse(a["rows"][0]["lineups"]["comments"])
 def test_date_and_identity_guards(self):
  s,f,l,resolve=make()
  l["rows"][0]["home_label"]="Wrong"
  a=build(s,f,l,[],NOW,resolver=resolve)
  self.assertEqual(a["rows"][0]["status"],"GUNCEL_PDF_MAC_ESLESMEDI")
  l["rows"].append(copy.deepcopy(l["rows"][1]))
  a=build(s,f,l,[],NOW,resolver=resolve)
  self.assertEqual(a["rows"][1]["status"],"GUNCEL_PDF_CIFT_KAYIT")
  l["pdf_capture_utc"]="2026-11-21T14:35:00Z"
  with self.assertRaises(ValueError):build(s,f,l,[],"2026-11-21T14:40:00Z",resolver=resolve)
 def test_morning_tamper_and_second_too_old(self):
  s,f,l,resolve=make()
  s["rows"][0]["prices"]["MS1"]=100
  with self.assertRaises(ValueError):build(s,f,l,[],NOW,resolver=resolve)
  s,f,l,resolve=make()
  with self.assertRaises(ValueError):build(s,f,l,[],"2026-11-21T14:20:00Z",resolver=resolve)
 def test_after_kickoff_never_final_review(self):
  s,f,l,resolve=make()
  l["pdf_capture_utc"]="2026-11-21T14:31:00Z"
  r=build(s,f,l,[],"2026-11-21T14:32:00Z",resolver=resolve)
  self.assertTrue(all(x["status"]=="MAC_BASLADI_VEYA_GUNCEL_PDF_GEC_KALDI" for x in r["rows"]))
 def test_never_forge_new_morning_status(self):
  s,f,l,resolve=make()
  d=xi(s,True)
  d["observations"][0]["morning_comparison"]={"source_url":"https://example.org/old",
     "fact":"already known","observed_at_utc":"2026-11-21T11:00:00Z"}
  a=build(s,f,l,[d],NOW,resolver=resolve)
  self.assertFalse(a["rows"][0]["lineups"]["comments"])
 def test_all_matches_can_be_no_opinion(self):
  s,f,l,resolve=make()
  result=build(s,f,l,[xi(s,False)],NOW,resolver=resolve)
  self.assertEqual(result["rows"][0]["lineups"]["comments"],[])
  self.assertEqual(result["rows"][0]["lineups"]["status"],"XI_KAYNAK_IDDIASI_KAYDEDILDI")

if __name__=="__main__":unittest.main()
