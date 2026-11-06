"""One bounded offline acceptance run for market-vs-model forward integration."""
import json,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from free_bulk_odds_263 import SPORTS,QuoteUnavailable
from pinnacle_forward_join_263 import join

ROOT=Path(__file__).resolve().parents[2]
ORIGINAL=ROOT/"forward_quad_263/2026-11-06/1d6b6f16fef8bac971c184c4.json"
NOW=datetime(2026,11,6,16,20,tzinfo=timezone.utc)

def market_event():
    return {"id":"SYNTHETIC_TEST_NOT_ACTUAL_PRICE",
        "sport_key":SPORTS["TUR1"],"commence_time":"2026-11-06T17:00:00Z",
        "home_team":"Gaziantep","away_team":"Kasimpasa",
        "bookmakers":[{"key":"pinnacle",
            "last_update":"2026-11-06T16:19:00Z",
            "markets":[{"key":"h2h","last_update":"2026-11-06T16:19:00Z",
                "outcomes":[{"name":"Gaziantep","price":2.4},
                            {"name":"Draw","price":3.2},
                            {"name":"Kasimpasa","price":2.9}]}]}]}

class OneForwardJoin(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.relative="forward_quad_263/2026-11-06/1d6b6f16fef8bac971c184c4.json"
        p=self.root/self.relative;p.parent.mkdir(parents=True)
        p.write_bytes(ORIGINAL.read_bytes())
        self.original=p.read_bytes()
        f=json.loads(p.read_text())
        self.batch="experiments/263/quad_batch_reports/TEST_ONLY.json"
        q=self.root/self.batch;q.parent.mkdir(parents=True)
        q.write_text(json.dumps({"schema":"quad_named_match_batch_report_v1",
            "outcomes":[{"status":"REGISTERED_FOUR_MODELS_EXPERIMENTAL",
                         "path":self.relative,"payload_sha256":f["payload_sha256"]}]}))
    def fake(self,sport,params,key):
        self.assertEqual(sport,SPORTS["TUR1"])
        self.assertEqual(params["bookmakers"],"pinnacle")
        self.assertEqual(params["markets"],"h2h")
        return [market_event()],498
    def test_one_real_like_quote_with_same_time_pure_four_model_comparison(self):
        calls=[]
        def supplier(*args):
            calls.append(args)
            return self.fake(*args)
        result=join(self.batch,root=self.root,key="SYNTHETIC",
                    now=NOW,getter=supplier)
        self.assertEqual(len(calls),1)
        self.assertEqual(result["max_requested_credits"],1)
        self.assertEqual(result["items"][0]["status"],"PINNACLE_READ_ONLY_COMPARISON_STORED")
        comparison=json.loads((self.root/result["items"][0]["comparison_path"]).read_text())
        self.assertEqual(set(comparison["models"]),{"B","C2","C3","M4"})
        self.assertEqual(comparison["bookmaker"],"pinnacle")
        self.assertAlmostEqual(sum(comparison["pinnacle_no_vig_probabilities"].values()),1.0)
        self.assertFalse(comparison["betting_authorized"])
        self.assertFalse(result["original_predictions_modified"])
        self.assertEqual((self.root/self.relative).read_bytes(),self.original)
    def test_no_key_never_queries_provider(self):
        result=join(self.batch,root=self.root,key=None,now=NOW,
                    getter=lambda *args:self.fail("No key should never query"))
        self.assertEqual(result["max_requested_credits"],0)
        self.assertEqual(result["snapshots"],[])
        self.assertEqual(result["items"][0]["reason"],"NO_FREE_THE_ODDS_API_KEY_CONFIGURED")
    def test_outside_t60_or_stale_forecast_blocks_query(self):
        for t in [NOW+timedelta(minutes=15),datetime(2026,11,6,17,2,tzinfo=timezone.utc)]:
            with self.subTest(t=t):
                a=join(self.batch,root=self.root,key="SYNTHETIC",now=t,
                    getter=lambda *args:self.fail("Out of window must not query"))
                self.assertEqual(a["max_requested_credits"],0)
    def test_missing_pinnacle_is_not_silently_swapped(self):
        def supplier(*args):
            e=market_event();e["bookmakers"][0]["key"]="random_else"
            return [e],497
        a=join(self.batch,root=self.root,key="SYNTHETIC",now=NOW,getter=supplier)
        self.assertEqual(a["items"][0]["status"],"NO_PINNACLE_COMPARISON")
        self.assertEqual(a["items"][0]["reason"],"NO_UNIQUE_EXACT_TEAM_AND_KICKOFF_MATCH")
        self.assertEqual(len(a["snapshots"]),1)
    def test_api_block_records_reason_no_ghost_price(self):
        def supplier(*args):raise QuoteUnavailable("ODDS_API_HTTP_403")
        a=join(self.batch,root=self.root,key="SYNTHETIC",now=NOW,getter=supplier)
        self.assertEqual(a["items"][0]["status"],"NO_PINNACLE_COMPARISON")
        self.assertEqual(a["snapshots"][0]["blocked"]["TUR1"],"ODDS_API_HTTP_403")
    def test_tampered_forecast_prohibits_any_price_request(self):
        p=self.root/self.relative
        f=json.loads(p.read_text())
        f["model_predictions"]["M4"]["goals"]["markets"]["OVER_2.5"]=0.001
        p.write_text(json.dumps(f))
        with self.assertRaises(ValueError):
            join(self.batch,root=self.root,key="SYNTHETIC",now=NOW,
                 getter=lambda *args:self.fail("tampered source must not query"))
    def test_selective_one_market_one_league_bulk_quota(self):
        from free_bulk_odds_263 import collect
        counts=[]
        def supplier(sport,params,key):
            counts.append(sport)
            return [market_event()],497
        a=collect(NOW.date(),NOW,"FAKE",getter=supplier,
                  bookmaker_filter="pinnacle",leagues=("TUR1",),markets=("h2h",))
        self.assertEqual(a["max_one_run_credit_cost"],1)
        self.assertEqual(a["leagues_requested"],["TUR1"])
        self.assertEqual(a["markets_requested"],["h2h"])
        self.assertEqual(len(counts),1)
        with self.assertRaisesRegex(QuoteUnavailable,"DUPLICATED"):
            collect(NOW.date(),NOW,"FAKE",getter=supplier,
                    bookmaker_filter="pinnacle",leagues=("TUR1","TUR1"),
                    markets=("h2h",))
if __name__=="__main__":unittest.main()
