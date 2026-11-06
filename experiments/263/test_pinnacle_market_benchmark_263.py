"""Single synthetic Pinnacle benchmark acceptance; prices NOT live."""
import copy,hashlib,json,unittest
from datetime import date,datetime,timezone
from pathlib import Path
from free_bulk_odds_263 import collect,canonical,SPORTS,normalize_event,fetch,QuoteUnavailable
from pinnacle_market_benchmark_263 import compare,BenchmarkBlocked
ROOT=Path(__file__).resolve().parents[2]
ORIGINAL=ROOT/"forward_quad_263/2026-11-06/1d6b6f16fef8bac971c184c4.json"
NOW=datetime(2026,11,6,16,20,0,tzinfo=timezone.utc)
DAY=date(2026,11,6)
def sample(sport="soccer_turkey_super_league",key="pinnacle",
           home="Gaziantep",away="Kasımpaşa",last="2026-11-06T16:19:00Z",
           kickoff="2026-11-06T17:00:00Z"):
    return {"id":"SYNTHETIC_EVENT_NOT_LIVE","sport_key":sport,"commence_time":kickoff,
       "home_team":home,"away_team":away,"bookmakers":[
          {"key":key,"last_update":last,"markets":[
          {"key":"h2h","last_update":last,"outcomes":[
               {"name":home,"price":2.40},{"name":"Draw","price":3.20},
               {"name":away,"price":2.90}]},
          {"key":"totals","last_update":last,"outcomes":[
               {"name":"Over","point":2.5,"price":1.83},
               {"name":"Under","point":2.5,"price":1.94}]}]}]}
def forecast():
    return json.loads(ORIGINAL.read_text(encoding="utf-8"))
def bulk(events=None,now=NOW):
    events=[sample()] if events is None else events
    def getter(sport,params,key):
        if sport==SPORTS["TUR1"]:return events,480
        return [],480
    return collect(DAY,now,"SYNTHETIC_KEY_NOT_REAL",getter,bookmaker_filter="pinnacle")
def reseal(data):
    data.pop("payload_sha256",None)
    data["payload_sha256"]=hashlib.sha256(canonical(data)).hexdigest()
    return data
class OnePinnacleAcceptance(unittest.TestCase):
    def test_pinnacle_only_source_and_10_league_api_filter(self):
        calls=[]
        def getter(sport,params,key):
            calls.append(params.copy())
            return [sample(sport)],480
        b=collect(DAY,NOW,"SYNTHETIC_KEY",getter,bookmaker_filter="pinnacle")
        self.assertEqual(len(calls),10)
        self.assertTrue(all(x["bookmakers"]=="pinnacle" and "regions" not in x
                            for x in calls))
        self.assertTrue(all(x["bookmaker_key"]=="pinnacle" for row in b["leagues"].values()
            for event in row for x in event["bookmakers"]))
    def test_valid_synthetic_comparison_fair_no_vig(self):
        f=forecast();immutable=json.dumps(f,sort_keys=True)
        o=bulk();r=compare(f,o)
        self.assertEqual(r["status"],"READ_ONLY_SAME_TIME_BENCHMARK")
        self.assertEqual(r["bookmaker"],"pinnacle")
        self.assertTrue(r["overround_pp"]>0)
        self.assertAlmostEqual(sum(r["pinnacle_no_vig_probabilities"].values()),1.0)
        self.assertEqual(set(r["models"]),{"B","C2","C3","M4"})
        self.assertFalse(r["betting_authorized"])
        self.assertFalse(r["changes_forecast_or_decision"])
        self.assertEqual(r["forecast_sha256"],f["payload_sha256"])
        self.assertEqual(json.dumps(f,sort_keys=True),immutable)
    def test_other_book_is_not_substituted_for_pinnacle(self):
        o=bulk([sample(key="other_eu_book")])
        self.assertEqual(o["leagues"]["TUR1"],[])
        self.assertEqual(compare(forecast(),o)["status"],"NO_VALID_SAME_TIME_PINNACLE_REFERENCE")
    def test_ambiguous_and_wrong_team_not_promoted(self):
        f=forecast();a=sample()
        o=bulk([a,a])
        self.assertEqual(compare(f,o)["reason"],"NO_UNIQUE_EXACT_TEAM_AND_KICKOFF_MATCH")
        o=bulk([sample(home="Gaziantep FK")])
        self.assertEqual(compare(f,o)["reason"],"NO_UNIQUE_EXACT_TEAM_AND_KICKOFF_MATCH")
    def test_stale_odds_and_forecast_window_block(self):
        f=forecast()
        o=bulk([sample(last="2026-11-06T16:00:00Z")])
        self.assertEqual(compare(f,o)["status"],"NO_VALID_SAME_TIME_PINNACLE_REFERENCE")
        o=bulk(now=datetime(2026,11,6,16,32,tzinfo=timezone.utc))
        self.assertEqual(compare(f,o)["reason"],"FORECAST_AND_PRICE_MORE_THAN_10_MIN_APART")
    def test_hash_tamper_blocked_without_recomputation(self):
        o=bulk()
        o["leagues"]["TUR1"][0]["bookmakers"][0]["markets"][0]["prices"]["H"]=999
        with self.assertRaisesRegex(BenchmarkBlocked,"BULK_SHA_CHANGED"):
            compare(forecast(),o)
    def test_after_kickoff_not_a_premarket_comparison(self):
        o=bulk()
        o["checked_at_utc"]="2026-11-06T17:01:00+00:00"
        reseal(o)
        self.assertEqual(compare(forecast(),o)["reason"],"NOT_SAME_PREMATCH_WINDOW")
    def test_access_and_quota_fail_fast(self):
        calls=[]
        def getter(sport,params,key):
            calls.append(sport)
            raise QuoteUnavailable("ODDS_API_HTTP_403")
        o=collect(DAY,NOW,"SYNTHETIC",getter,bookmaker_filter="pinnacle")
        self.assertEqual(len(calls),1)
        self.assertEqual(len(o["blocked"]),10)
        self.assertEqual(o["leagues"],{})
        with self.assertRaisesRegex(QuoteUnavailable,"NO_FREE"):
            collect(DAY,NOW,None,bookmaker_filter="pinnacle")
    def test_unfiltered_eu_bundle_not_misrepresented(self):
        def getter(sport,params,key):return [sample(sport)],480
        o=collect(DAY,NOW,"SYNTHETIC",getter)
        with self.assertRaisesRegex(BenchmarkBlocked,"UNFILTERED"):
            compare(forecast(),o)
if __name__=="__main__":unittest.main()
