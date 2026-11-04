"""One bounded test batch; synthetic odds NEVER described as live."""
import copy,json,unittest
from datetime import datetime,timezone
from pathlib import Path
from forward_calibration_bridge_263 import _digest
from forward_baseline_provenance_263 import SCHEMA as BASE_SCHEMA
from test_forward_baseline_provenance_263 import forecast as sample_forecast
from market_fifth_baseline_263 import OBSERVATION_SCHEMA,fixture_key
from four_model_value_policy_263 import decide,render
NOW=datetime(2026,11,6,16,3,tzinfo=timezone.utc)
def seal(d):
    d["payload_sha256"]=_digest({k:v for k,v in d.items() if k!="payload_sha256"});return d
def fixture():
    f=sample_forecast()
    f["fixture"].update(home_id="HOME",away_id="AWAY",source_checked_at_utc="2026-11-06T15:58:00+00:00")
    mk={"1X2":{"H":.72,"D":.17,"A":.11},
        "BTTS_YES":.58,"BTTS_NO":.42,
        "OVER_1.5":.82,"UNDER_1.5":.18,"OVER_2.5":.53,"UNDER_2.5":.47,
        "OVER_3.5":.16,"UNDER_3.5":.84}
    f["model_predictions"]={m:{"status":"AVAILABLE","goals":{"markets":copy.deepcopy(mk),"top_scores":{"1-0":.15}}}
       for m in ("B","C2","C3","M4")}
    seal(f)
    rates={"MS1":.43,"MSX":.28,"MS2":.29,"BTTS_YES":.50,"BTTS_NO":.50,
       "OVER_1.5":.70,"UNDER_1.5":.30,"OVER_2.5":.49,"UNDER_2.5":.51,
       "OVER_3.5":.23,"UNDER_3.5":.77}
    b={"schema":BASE_SCHEMA,"forecast_sha256":f["payload_sha256"],"league":"TUR1",
        "method":"PAST_RESULTS_LEAGUE_MARKET_RATE",
        "source_snapshot_sha256":f["data"]["snapshot_sha256"],
        "historical_match_count":150,"last_result_date":"2026-11-05",
        "forecast_created_at_utc":f["created_at_utc"],
        "created_at_utc":"2026-11-06T16:00:30+00:00","markets":rates}
    seal(b)
    lock=json.loads((Path(__file__).with_name("forward_dev_calibration_lock_263.json")).read_text())
    return f,b,lock
def odds(f,groups=None,observed="2026-11-06T16:02:00+00:00"):
    groups=groups if groups is not None else {
       "MS":{"MS1":1.99,"MSX":3.1,"MS2":5.4},
       "GOALS_3.5":{"UNDER_3.5":1.65,"OVER_3.5":2.45},
       "GOALS_1.5":{"OVER_1.5":1.1,"UNDER_1.5":6.5}}
    key=fixture_key(f["fixture"])
    q={"schema":OBSERVATION_SCHEMA,"fixture_key":key,"forecast_payload_sha256":f["payload_sha256"],
       "source_domain":"nesine.com","analysis_at_utc":observed,
       "evidence_scope":"HUMAN_ATTESTED_NOT_EXTERNALLY_REVERIFIED",
       "source_review":{"method":"MANUAL_PUBLIC_PAGE","reviewer":"SYNTHETIC_TEST",
         "reviewed_at_utc":"2026-11-06T16:01:00+00:00",
         "visible_source_note":"SYNTHETIC DEMONSTRATION PRICES NOT LIVE"},
       "quotes":{g:{"fixture_key":key,"market_group":g,"verification":"INDEPENDENTLY_CHECKED",
          "stage":"PREMATCH","source":"nesine.com","source_url":"https://nesine.com/synthetic-only",
          "checked_at_utc":observed,"decimal_odds":v} for g,v in groups.items()}}
    return seal(q)
class TestAgreedResult(unittest.TestCase):
    def setUp(self):self.f,self.b,self.lock=fixture()
    def test_no_odds_means_pas_but_provides_most_likely(self):
        d=decide(self.f,self.b,self.lock,now=NOW)
        self.assertEqual(d["status"],"RESEARCH_PAS");self.assertIsNone(d["main_candidate"])
        self.assertEqual(d["descriptive_most_likely_1x2_by_model_median"],"MS1")
        self.assertTrue(any(x["market"]=="OVER_1.5" for x in d["high_probability_alerts_not_bets"]))
    def test_value_main_and_unrelated_alternative(self):
        d=decide(self.f,self.b,self.lock,odds(self.f),now=NOW)
        self.assertEqual(d["main_candidate"]["market"],"MS1")
        self.assertEqual(d["alternative_candidate"]["market"],"UNDER_3.5")
        self.assertNotEqual(d["main_candidate"]["family"],d["alternative_candidate"]["family"])
        self.assertTrue(d["main_candidate"]["EV"]>=.05)
        self.assertFalse(d["betting_authorized"])
        self.assertIn("Ana tercih",render(d))
    def test_over15_not_banned_if_skill_supported(self):
        for model in ("C3","M4"):
            self.lock["calibration"][model]["OVER_1.5"].update(development_brier_skill=.08,n=587,weight=.8)
        seal(self.lock)
        d=decide(self.f,self.b,self.lock,odds(self.f,groups={
           "GOALS_1.5":{"OVER_1.5":1.42,"UNDER_1.5":3.1}}),now=NOW)
        self.assertEqual(d["main_candidate"]["market"],"OVER_1.5")
        self.assertIsNone(d["alternative_candidate"])
    def test_current_negative_dev_skill_not_disguised(self):
        d=decide(self.f,self.b,self.lock,odds(self.f,groups={
           "GOALS_1.5":{"OVER_1.5":1.42,"UNDER_1.5":3.1}}),now=NOW)
        r=next(x for x in d["all_market_diagnostics"] if x["market"]=="OVER_1.5")
        self.assertIn("NO_POSITIVE_DEV_BRIER_SKILL",r["qualification_reasons"])
        self.assertIsNone(r["EV"])
        self.assertEqual(d["status"],"RESEARCH_PAS")
    def test_same_family_not_second_choice(self):
        for model in ("C3","M4"):
            self.lock["calibration"][model]["OVER_1.5"].update(development_brier_skill=.08,n=587,weight=.8)
        seal(self.lock)
        d=decide(self.f,self.b,self.lock,odds(self.f,groups={
          "GOALS_1.5":{"OVER_1.5":1.42,"UNDER_1.5":3.1},
          "GOALS_3.5":{"UNDER_3.5":1.65,"OVER_3.5":2.45}}),now=NOW)
        self.assertEqual(d["main_candidate"]["family"],"GOALS")
        self.assertIsNone(d["alternative_candidate"])
    def test_stale_or_invalid_quote(self):
        q=odds(self.f,observed="2026-11-06T15:50:00+00:00")
        q["source_review"]["reviewed_at_utc"]="2026-11-06T15:49:00+00:00";seal(q)
        self.assertEqual(decide(self.f,self.b,self.lock,q,now=NOW)["status"],"RESEARCH_PAS")
        q=odds(self.f);q["quotes"]["MS"]["source"]="fake.com";seal(q)
        with self.assertRaisesRegex(ValueError,"ODDS_GROUP_SOURCE_MISMATCH"):
            decide(self.f,self.b,self.lock,q,now=NOW)
    def test_forecast_sha_and_after_kickoff(self):
        f=copy.deepcopy(self.f);f["model_predictions"]["M4"]["goals"]["markets"]["OVER_1.5"]=.99
        with self.assertRaisesRegex(ValueError,"SHA_TAMPERED"):
            decide(f,self.b,self.lock,now=NOW)
        with self.assertRaisesRegex(ValueError,"DECISION_AFTER_KICKOFF"):
            decide(self.f,self.b,self.lock,now=datetime(2026,11,6,17,0,tzinfo=timezone.utc))
    def test_four_model_support(self):
        f=copy.deepcopy(self.f)
        for m in ("B","C2"):f["model_predictions"][m]["goals"]["markets"]["1X2"]={"H":.20,"D":.20,"A":.60}
        seal(f);b=copy.deepcopy(self.b);b["forecast_sha256"]=f["payload_sha256"];seal(b)
        d=decide(f,b,self.lock,odds(f),now=NOW)
        self.assertIn("UNDER_3_MODEL_SUPPORT",next(x for x in d["all_market_diagnostics"] if x["market"]=="MS1")["qualification_reasons"])
if __name__=="__main__":unittest.main()
