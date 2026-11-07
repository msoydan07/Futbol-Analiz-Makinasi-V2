"""Synthetic Belgian official Next.js match-card parser acceptance. No API calls."""
import copy,json,unittest
from datetime import datetime,timezone
from sabah_belgium_official_nextjs_263 import parse_proleague,PARSER,OFFICIAL_URL
from official_page_lookup_263 import parse_official_events,official_page_lookup,SOURCES
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway

NOW=datetime(2026,11,7,12,0,tzinfo=timezone.utc)

def card(i,home="KVC Westerlo",away="Sporting Charleroi",when="2026-11-07T15:00:00Z"):
    return {
      "id":"game-"+str(i),"season":{"name":"Seizoen 2026/2027"},
      "competition":{"name":"Jupiler Pro League"},
      "period":{"type":"PreMatch"},"date":"2026-11-07",
      "time":when,"homeTeam":{"name":home},"awayTeam":{"name":away}}

def page(rows=None):
    rows=rows if rows is not None else [
        card(1),
        card(2,"OH Leuven","KV Mechelen","2026-11-07T17:15:00Z")]
    module={"data":{"matches":rows}}
    page={"grids":[{"areas":[{"modules":[module]}]}]}
    body={"props":{"pageProps":{"data":{"page":page}}}}
    return '<html><script id="__NEXT_DATA__" type="application/json">'+json.dumps(body)+'</script></html>'

class BelgianNextTests(unittest.TestCase):
    def test_two_official_clubs_utc_and_order(self):
        out=parse_proleague(page())
        self.assertEqual(len(out),2)
        self.assertEqual(out[0]["home"],"KVC Westerlo")
        self.assertEqual(out[0]["away"],"Sporting Charleroi")
        self.assertEqual(out[0]["kickoff_utc"],"2026-11-07T15:00:00+00:00")
        self.assertTrue(all(v["format"]==PARSER for v in out))
    def test_official_dispatch(self):
        self.assertEqual(SOURCES["BEL1"][0],OFFICIAL_URL)
        self.assertEqual(parse_official_events("BEL1",page()),
                         parse_proleague(page()))
    def test_same_match_conflicting_id_is_blocked(self):
        b=card(1,"OH Leuven","KV Mechelen","2026-11-07T17:15:00Z")
        self.assertEqual(parse_proleague(page([card(1),b])),[])
    def test_wrong_competition_is_not_imported(self):
        m=card(1)
        m["competition"]["name"]="Challenger Pro League"
        self.assertEqual(parse_proleague(page([m])),[])
    def test_naive_time_and_wrong_local_date_blocked(self):
        m=card(1);m["time"]="2026-11-07T15:00:00"
        self.assertEqual(parse_proleague(page([m])),[])
        m["time"]="2026-11-08T01:30:00Z"
        self.assertEqual(parse_proleague(page([m])),[])
    def test_skips_cancelled_game(self):
        m=card(1);m["period"]["type"]="EventCancelled"
        self.assertEqual(parse_proleague(page([m])),[])
    def test_not_pretend_generic_belgian_prose_is_fixture(self):
        self.assertEqual(parse_proleague("<p>KVC Westerlo — Sporting Charleroi 16:00</p>"),[])
        self.assertEqual(parse_proleague("<script id='__NEXT_DATA__'>{malformed</script>"),[])
    def test_source_url_spoof_rejected(self):
        x=official_page_lookup("BEL1","KVC Westerlo","Sporting Charleroi",
            now=NOW,source_url="https://www.proleague.be.evil.test/fixture",
            html=page(),same_team=lambda a,b:a==b)
        self.assertEqual(x["status"],"REJECTED")
    def test_cached_official_named_match_gate(self):
        calls=[]
        def get(url,league):
            calls.append((url,league))
            return url,page()
        def gated(league,h,a,lookup_override=None):
            if not lookup_override:return {"status":"NOT_VERIFIED"}
            observed=lookup_override(h,a)
            self.assertEqual(observed["status"],"VERIFIED_OFFICIAL_FIXTURE")
            self.assertEqual(observed["source_parser"],PARSER)
            return {"status":"VERIFIED","league":league,
                "home_id":h,"away_id":a,"kickoff_utc":observed["kickoff_utc"]}
        g=OfficialFixtureGateway(fetcher=get,
            resolve_id=lambda l,n:n,gate_runner=gated,clock=lambda:NOW)
        first=g.lookup("BEL1","KVC Westerlo","Sporting Charleroi")
        second=g.lookup("BEL1","OH Leuven","KV Mechelen")
        self.assertEqual(first["status"],"VERIFIED")
        self.assertEqual(second["status"],"VERIFIED")
        self.assertEqual(g.coverage()["BEL1"]["parsed_events"],2)
        self.assertEqual(calls,[(OFFICIAL_URL,"BEL1")])
    def test_missing_team_not_verified(self):
        x=official_page_lookup("BEL1","Fake Club","Sporting Charleroi",
            now=NOW,html=page(),same_team=lambda a,b:a==b)
        self.assertNotEqual(x["status"],"VERIFIED_OFFICIAL_FIXTURE")
if __name__=="__main__":unittest.main()
