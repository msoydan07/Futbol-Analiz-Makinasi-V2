"""EFL 2026/27 official TV-selection: partial Championship fallback tests."""
import unittest
from datetime import datetime,timezone
from sabah_eng2_official_tv_263 import parse_efl_tv,PARSER,SOURCE_URL
from official_page_lookup_263 import official_page_lookup,parse_official_events,SOURCES
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway

NOW=datetime(2026,11,7,12,0,tzinfo=timezone.utc)
LINES=[
 ("Championship","07-Nov-26","Saturday","12:30","Wrexham","V","Wolverhampton Wanderers","Sky Sports Football"),
 ("Championship","07-Nov-26","Saturday","12:30","Portsmouth","V","Stoke City","Sky Sports+"),
 ("Championship","07-Nov-26","Saturday","12:30","Bristol City","V","Norwich City","Sky Sports+"),
]
def html(rows=LINES):
    return "<html><table>"+"".join("<tr>"+"".join("<td>"+item+"</td>" for item in row)+"</tr>" for row in rows)+"</table></html>"

class OfficialEFLTVSelection(unittest.TestCase):
    def test_three_known_tv_times_are_official_but_partial(self):
        out=parse_efl_tv(html())
        self.assertEqual(len(out),3)
        self.assertEqual(out[0]["kickoff_utc"],"2026-11-07T12:30:00+00:00")
        self.assertEqual(out[1]["home"],"Portsmouth")
        self.assertTrue(all(x["format"]==PARSER for x in out))
        # Only the published TV list, never the whole 11-game league matchday.
        self.assertNotEqual(len(out),11)
    def test_lower_leagues_do_not_leak(self):
        r=LINES[0]
        q=("League One",)+r[1:]
        self.assertEqual(parse_efl_tv(html([q])),[])
    def test_untrusted_or_date_only_does_not_promote(self):
        q=list(LINES[0]);q[3]="TBC"
        self.assertEqual(parse_efl_tv(html([tuple(q)])),[])
        q=list(LINES[0]);q[1]="TBC"
        self.assertEqual(parse_efl_tv(html([tuple(q)])),[])
    def test_conflicting_duplicate_fails_closed(self):
        q=list(LINES[0]);q[3]="17:30"
        self.assertEqual(parse_efl_tv(html([LINES[0],tuple(q)])),[])
    def test_official_dispatch_and_canonical_match_gate(self):
        self.assertEqual(parse_official_events("ENG2",html(),parser=PARSER),parse_efl_tv(html()))
        calls=[]
        def get(url,league):
            calls.append(url)
            if url==SOURCES["ENG2"][0]:return url,"<html>Loading...</html>"
            if url==SOURCE_URL:return url,html()
            raise AssertionError("UNEXPECTED_EXTERNAL_OFFICIAL_CALL")
        def gate(league,home,away,lookup_override=None):
            assert lookup_override
            x=lookup_override(home,away)
            assert x["status"]=="VERIFIED_OFFICIAL_FIXTURE"
            assert x["source_parser"]==PARSER
            return {"status":"VERIFIED","league":league,
                    "home_id":"CANON:"+home,"away_id":"CANON:"+away,
                    "kickoff_utc":x["kickoff_utc"]}
        gw=OfficialFixtureGateway(fetcher=get,gate_runner=gate,
                  resolve_id=lambda league,club:"CANON:"+club,clock=lambda:NOW)
        out=gw.lookup("ENG2","Wrexham","Wolverhampton Wanderers")
        self.assertEqual(out["status"],"VERIFIED")
        self.assertEqual(len(gw._get("ENG2")["events"]),3)
        self.assertEqual(gw._get("ENG2").get("efl_source_coverage"),"PARTIAL_TV_SELECTION_ONLY")
        self.assertEqual(calls,[SOURCES["ENG2"][0],SOURCE_URL])
    def test_competition_jsonld_fallback_after_empty_tv_requires_explicit_timed_event(self):
        import json
        second="https://www.efl.com/competitions/efl-championship/"
        future=datetime(2026,11,8,8,0,tzinfo=timezone.utc)
        payload={"@type":"SportsEvent","homeTeam":{"name":"Wrexham"},
                 "awayTeam":{"name":"Wolverhampton Wanderers"},
                 "startDate":"2026-11-08T15:00:00+00:00"}
        fixture='<html><script type="application/ld+json">'+json.dumps(payload)+'</script></html>'
        calls=[]
        def fetch(url,league):
            calls.append(url)
            if url==SOURCES["ENG2"][0]:return url,"<html>Loading...</html>"
            if url==SOURCE_URL:return url,"<html>Sky Sports Championship</html>"
            if url==second:return url,fixture
            raise AssertionError("UNEXPECTED_OFFICIAL_REQUEST")
        def gate(league,home,away,lookup_override=None):
            result=lookup_override(home,away)
            self.assertEqual(result["status"],"VERIFIED_OFFICIAL_FIXTURE")
            return {"status":"VERIFIED","home_id":"H","away_id":"A",
                    "kickoff_utc":result["kickoff_utc"]}
        gw=OfficialFixtureGateway(fetcher=fetch,gate_runner=gate,
                 resolve_id=lambda league,club:club,clock=lambda:future)
        out=gw.lookup("ENG2","Wrexham","Wolverhampton Wanderers")
        self.assertEqual(out["status"],"VERIFIED")
        source=gw._get("ENG2")
        self.assertEqual(source["parser"],"jsonld")
        self.assertEqual(source["efl_source_coverage"],
                         "OFFICIAL_COMPETITION_JSONLD_PARTIAL_UNVERIFIED_COVERAGE")
        self.assertEqual(calls,[SOURCES["ENG2"][0],SOURCE_URL,second])
    def test_competition_page_date_only_never_promoted(self):
        import json
        second="https://www.efl.com/competitions/efl-championship/"
        event={"@type":"SportsEvent","homeTeam":{"name":"Wrexham"},
               "awayTeam":{"name":"Wolverhampton Wanderers"},
               "startDate":"2026-11-08"}
        def fetch(url,league):
            if url==SOURCES["ENG2"][0]:return url,"<html>Loading...</html>"
            if url==SOURCE_URL:return url,"<html>Sky Sports Championship</html>"
            if url==second:
                return url,'<html><script type="application/ld+json">'+json.dumps(event)+'</script></html>'
            raise AssertionError("UNEXPECTED")
        gw=OfficialFixtureGateway(fetcher=fetch,
                 resolve_id=lambda league,club:club,clock=lambda:datetime(2026,11,8,8,tzinfo=timezone.utc))
        self.assertEqual(gw._get("ENG2")["events"],[])
        self.assertEqual(gw._get("ENG2")["efl_competition_fallback_status"],
                         "NO_EXPLICIT_TIMED_SPORTSEVENT_JSONLD")
    def test_no_magic_fallback_and_untrusted_domain_denied(self):
        r=official_page_lookup("ENG2","Wrexham","Wolverhampton Wanderers",
              now=NOW,source_url="https://efl.com.evil.test/fake",
              html=html(),same_team=lambda a,b:a==b,parser=PARSER)
        self.assertEqual(r["status"],"REJECTED")
        self.assertEqual(parse_efl_tv("<html>match time 12:30 Wrexham Portsmouth</html>"),[])
if __name__=="__main__":unittest.main()
