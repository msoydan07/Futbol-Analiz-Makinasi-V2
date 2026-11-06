"""One bounded synthetic test batch; never requests live odds without user key."""
import copy
import json
import unittest
from datetime import datetime,timezone,date,timedelta
from free_bulk_odds_263 import SPORTS,SCHEMA,MAX_RUN_CREDITS,QuoteUnavailable,collect,normalize_event,canonical,utc
NOW=datetime(2026,11,6,6,0,tzinfo=timezone.utc)
DAY=date(2026,11,6)
def sample(sport="soccer_turkey_super_league",ko="2026-11-06T17:00:00Z"):
    return {"id":"provider-fixture-1","sport_key":sport,"commence_time":ko,
      "home_team":"Gaziantep FK","away_team":"Kasımpaşa",
      "bookmakers":[{"key":"book_eu_one","last_update":"2026-11-06T05:59:00Z",
        "markets":[
          {"key":"h2h","last_update":"2026-11-06T05:59:00Z",
           "outcomes":[{"name":"Gaziantep FK","price":2.40},
                       {"name":"Draw","price":3.20},
                       {"name":"Kasımpaşa","price":2.90}]},
          {"key":"totals","last_update":"2026-11-06T05:59:00Z",
           "outcomes":[{"name":"Over","point":2.5,"price":1.83},
                       {"name":"Under","point":2.5,"price":1.94}]}]}]}
class FreeBulkOdds(unittest.TestCase):
    def test_ten_leagues_and_single_batch_budget(self):
        self.assertEqual(len(SPORTS),10)
        self.assertEqual(len(set(SPORTS.values())),10)
        self.assertEqual(MAX_RUN_CREDITS,20)
        calls=[]
        def getter(sport,params,key):
            calls.append((sport,params["markets"],params["regions"]))
            return [sample(sport)],478
        result=collect(DAY,NOW,"SYNTHETIC_KEY_NOT_REAL",getter)
        self.assertEqual(len(calls),10)
        self.assertTrue(all(x[1:] == ("h2h,totals","eu") for x in calls))
        self.assertEqual(len(result["leagues"]),10)
        self.assertEqual(result["blocked"],{})
        self.assertEqual(result["schema"],SCHEMA)
        self.assertFalse(result["S1_S2_official_approved"])
        self.assertTrue(result["bookmaker_odds_not_iddaa"])
        self.assertNotIn("SYNTHETIC_KEY_NOT_REAL",json.dumps(result))
        self.assertEqual(result["leagues"]["TUR1"][0]["bookmakers"][0]["markets"][0]["prices"],
                         {"H":2.4,"D":3.2,"A":2.9})
    def test_full_same_book_or_none_never_mix(self):
        item=sample()
        valid=normalize_event(item,SPORTS["TUR1"],DAY,NOW)
        self.assertEqual(len(valid["bookmakers"][0]["markets"]),2)
        broken=copy.deepcopy(item)
        broken["bookmakers"][0]["markets"][0]["outcomes"].pop()
        out=normalize_event(broken,SPORTS["TUR1"],DAY,NOW)
        self.assertEqual([x["market"] for x in out["bookmakers"][0]["markets"]],["totals"])
        broken["bookmakers"][0]["markets"][1]["outcomes"].pop()
        self.assertIsNone(normalize_event(broken,SPORTS["TUR1"],DAY,NOW))
    def test_unknown_and_stale_are_not_odds(self):
        wrong=sample(sport="soccer_epl")
        self.assertIsNone(normalize_event(wrong,SPORTS["TUR1"],DAY,NOW))
        stale=sample()
        stale["bookmakers"][0]["last_update"]="2026-11-05T05:00:00Z"
        for m in stale["bookmakers"][0]["markets"]:m["last_update"]="2026-11-05T05:00:00Z"
        self.assertIsNone(normalize_event(stale,SPORTS["TUR1"],DAY,NOW))
        started=sample(ko="2026-11-06T05:00:00Z")
        self.assertIsNone(normalize_event(started,SPORTS["TUR1"],DAY,NOW))
    def test_no_key_or_past_date(self):
        with self.assertRaisesRegex(QuoteUnavailable,"NO_FREE"):
            collect(DAY,NOW,None)
        with self.assertRaisesRegex(QuoteUnavailable,"NO_HISTORICAL"):
            collect(date(2026,11,5),NOW,"TEST",lambda *a:([],None))
    def test_quota_guard_stops_later_leagues(self):
        calls=[]
        def getter(sport,params,key):
            calls.append(sport)
            return [sample(sport)],1
        out=collect(DAY,NOW,"TEST",getter)
        self.assertEqual(len(calls),1)
        self.assertEqual(len(out["blocked"]),9)
        self.assertEqual(len(out["leagues"]),1)
    def test_malformed_market_never_accepted(self):
        case=sample()
        case["bookmakers"][0]["markets"][0]["outcomes"][0]["price"]=True
        result=normalize_event(case,SPORTS["TUR1"],DAY,NOW)
        self.assertEqual(len(result["bookmakers"][0]["markets"]),1)
    def test_no_bookmaker_no_odd_record(self):
        case=sample()
        case["bookmakers"]=[]
        self.assertIsNone(normalize_event(case,SPORTS["TUR1"],DAY,NOW))
    def test_timezones_and_source_sha(self):
        self.assertEqual(utc("2026-11-06T17:00:00Z").isoformat(),"2026-11-06T17:00:00+00:00")
        def getter(sport,params,key):return [],None
        out=collect(DAY,NOW,"TEST",getter)
        import hashlib
        digest=out.pop("payload_sha256")
        self.assertEqual(hashlib.sha256(canonical(out)).hexdigest(),digest)
if __name__=="__main__":unittest.main()
