"""Synthetic tests: no live credit consumption."""
import unittest
from datetime import date,datetime,timezone
from pinnacle_real_access_probe_263 import probe,QuoteUnavailable
from free_bulk_odds_263 import SPORTS
NOW=datetime(2026,11,6,18,40,tzinfo=timezone.utc)
DAY=date(2026,11,7)
def sample(sport):
    return {"id":"SYNTHETIC_ONLY","sport_key":sport,
            "commence_time":"2026-11-07T15:00:00Z",
            "home_team":"A","away_team":"B","bookmakers":[
                {"key":"pinnacle","last_update":"2026-11-06T18:39:00Z",
                 "markets":[{"key":"h2h","last_update":"2026-11-06T18:39:00Z",
                  "outcomes":[{"name":"A","price":2.3},{"name":"Draw","price":3.2},
                              {"name":"B","price":3.4}]}]}]}
class Probe(unittest.TestCase):
    def test_one_success_stops_without_spending_three_calls(self):
        calls=[]
        def fake(sport,params,key):
            calls.append((sport,params))
            return [sample(sport)],499
        x=probe(DAY,NOW,"SYNTHETIC_KEY_DO_NOT_USE",fake)
        self.assertEqual(x["requests_made"],1)
        self.assertEqual(x["result"],"LIVE_PINNACLE_ACCESS_VERIFIED_FOR_AT_LEAST_ONE_MATCH")
        self.assertEqual(calls[0][1]["bookmakers"],"pinnacle")
        self.assertEqual(calls[0][1]["markets"],"h2h")
        self.assertFalse(x["betting_authorized"])
        self.assertNotIn("SYNTHETIC_KEY_DO_NOT_USE",str(x))
    def test_no_price_tries_three_and_remains_unverified(self):
        x=probe(DAY,NOW,"FAKE",lambda sport,params,key:([],499))
        self.assertEqual(x["requests_made"],3)
        self.assertEqual(x["result"],"NO_VERIFIED_PINNACLE_PRICE_YET")
    def test_403_stops_after_one(self):
        def fake(s,p,k):raise QuoteUnavailable("ODDS_API_HTTP_403")
        x=probe(DAY,NOW,"FAKE",fake)
        self.assertEqual(x["requests_made"],1)
        self.assertEqual(x["blocked"]["ENG1"],"ODDS_API_HTTP_403")
    def test_missing_key_or_bad_day_fails_before_calls(self):
        with self.assertRaisesRegex(QuoteUnavailable,"NO_FREE"):
            probe(DAY,NOW,None)
        with self.assertRaisesRegex(QuoteUnavailable,"ONLY_TODAY"):
            probe(date(2026,11,9),NOW,"FAKE")
    def test_foreign_book_not_pinnacle(self):
        def fake(s,p,k):
            d=sample(s);d["bookmakers"][0]["key"]="not_pinnacle"
            return [d],498
        x=probe(DAY,NOW,"FAKE",fake)
        self.assertEqual(x["result"],"NO_VERIFIED_PINNACLE_PRICE_YET")
if __name__=="__main__":unittest.main()
