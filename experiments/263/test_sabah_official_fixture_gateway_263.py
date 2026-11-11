import unittest
from datetime import datetime,timezone,timedelta
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway

NOW=datetime(2026,11,7,7,0,tzinfo=timezone.utc)
START="2026-11-07T16:00:00+01:00"
NEXT="2026-11-10T20:00:00+01:00"
def ld(home="A",away="B",start=START):
    import json
    return '<script type="application/ld+json">'+json.dumps({
        "@type":"SportsEvent","homeTeam":{"name":home},
        "awayTeam":{"name":away},"startDate":start})+"</script>"
def gate_runner(league,h,a,lookup_override=None):
    if lookup_override is None:return {"status":"NOT_VERIFIED","reason":"NOT_ON_OLD_SOURCE"}
    observed=lookup_override(h,a)
    if observed.get("source_origin")!="FETCHED_OFFICIAL_PAGE_BATCH_CACHE":
        return {"status":"NOT_VERIFIED","reason":"NOT_FROM_LIVE_BATCH"}
    return {"status":"VERIFIED","league":league,"home_id":h,"away_id":a,
            "source_url":observed["source_url"],
            "kickoff_utc":observed["kickoff_utc"],
            "retrieved_at_utc":NOW.isoformat()}
def make_fetch(result,called):
    def f(url,league):
        called.append((url,league))
        return (url,result)
    return f

class GatewayTests(unittest.TestCase):
 def init(self,html,called,**kwargs):
    return OfficialFixtureGateway(
      fetcher=make_fetch(html,called),
      resolve_id=lambda league,name: name,
      gate_runner=kwargs.get("gate_runner",gate_runner),
      clock=lambda:NOW)
 def test_one_page_fetch_many_matches(self):
    called=[];g=self.init(ld("A","B")+ld("C","D"),called)
    self.assertEqual(g.lookup("ESP1","A","B")["status"],"VERIFIED")
    self.assertEqual(g.lookup("ESP1","C","D")["status"],"VERIFIED")
    self.assertEqual(len(called),1)
    self.assertEqual(g.coverage()["ESP1"]["parsed_events"],2)
    self.assertEqual(g.match_checks[0]["selected_lookup"],
                     "CACHED_OFFICIAL_PAGE_AND_CANONICAL_GATE")
 def test_refuses_unverified_page_date(self):
    called=[];g=self.init("<h2>Saturday 7 November</h2><p>Arsenal v Hull City</p>",called)
    out=g.lookup("ENG1","Arsenal","Hull City")
    self.assertNotEqual(out["status"],"VERIFIED")
    self.assertEqual(g.match_checks[-1]["page_observation_status"],
                     "VERIFIED_OFFICIAL_FIXTURE_DATE_ONLY")
 def test_rejects_redirect_to_spoof(self):
    seen=[]
    def bad(url,league):seen.append(url);return "https://www.laliga.com.evil.test/matches",ld()
    g=OfficialFixtureGateway(fetcher=bad,resolve_id=lambda league,n:n,
                             gate_runner=gate_runner,clock=lambda:NOW)
    self.assertEqual(g.lookup("ESP1","A","B")["status"],"NOT_VERIFIED")
    self.assertEqual(len(seen),1)
    self.assertEqual(g.coverage()["ESP1"]["status"],"NOT_VERIFIED")
 def test_no_identity_guess(self):
    called=[]
    resolver=lambda league,name:{"A":"A","B":"B"}.get(name,
                               (_ for _ in ()).throw(ValueError("UNKNOWN")))
    g=OfficialFixtureGateway(fetcher=make_fetch(ld("A","B"),called),
        resolve_id=resolver,gate_runner=gate_runner,clock=lambda:NOW)
    self.assertNotEqual(g.lookup("ESP1","A","Unknown")["status"],"VERIFIED")
 def test_fallback_old_gate_still_operates(self):
    called=[]
    def old(league,h,a,lookup_override=None):
        if lookup_override is None:
            return {"status":"VERIFIED","league":league,"home_id":h,
                    "away_id":a,"source_url":"https://www.laliga.com",
                    "kickoff_utc":START,"retrieved_at_utc":NOW.isoformat()}
        return {"status":"NOT_VERIFIED"}
    g=self.init("<p>no fixtures</p>",called,gate_runner=old)
    self.assertEqual(g.lookup("ESP1","A","B")["status"],"VERIFIED")
    self.assertEqual(g.match_checks[-1]["selected_lookup"],
                     "EXISTING_LIVE_NAMED_MATCH_GATE")
 def test_adjacent_verified_league_only(self):
    called=[]
    g=self.init(ld("A","B")+ld("A","C",NEXT),called)
    f=g.lookup("ESP1","A","B")
    events=g.adjacent_for(f)
    self.assertEqual(len(events),1)
    self.assertEqual(events[0]["team_id"],"A")
    self.assertEqual(events[0]["opponent"],"C")
    self.assertEqual(events[0]["competition"],"LIG")
    self.assertEqual(events[0]["verification"],"VERIFIED_OFFICIAL_ADAPTER")
    self.assertFalse(g.coverage()["ESP1"]["all_competitions_covered"])
 def test_adjacent_requested_at_7_day_boundary_and_no_extra_source_calls(self):
    called=[]
    inside=(NOW+timedelta(days=7)).isoformat()
    outside=(NOW+timedelta(days=7,seconds=1)).isoformat()
    g=self.init(ld("A","B")+ld("A","C",inside)+ld("A","D",outside),called)
    f=g.lookup("ESP1","A","B")
    items=g.adjacent_for(f,requested_at=NOW)
    self.assertEqual(len(items),1)
    self.assertEqual(items[0]["opponent"],"C")
    self.assertEqual(len(called),1)
    self.assertFalse(g.coverage()["ESP1"]["all_competitions_covered"])
 def test_adjacent_conflicting_times_fail_closed(self):
    called=[]
    g=self.init(ld("A","B")+ld("A","C",NEXT)+ld("A","C","2026-11-11T20:00:00+01:00"),called)
    f=g.lookup("ESP1","A","B")
    self.assertEqual(g.adjacent_for(f),[])
 def test_source_fetch_failure_does_not_fake(self):
    def bad(url,league):raise OSError("network unavailable")
    g=OfficialFixtureGateway(fetcher=bad,resolve_id=lambda league,n:n,
                             gate_runner=gate_runner,clock=lambda:NOW)
    self.assertEqual(g.lookup("ESP1","A","B")["status"],"NOT_VERIFIED")
    self.assertIsNone(g.coverage()["ESP1"]["page_sha256"])
 def test_wrong_order_is_blocked(self):
    called=[];g=self.init(ld("A","B"),called)
    self.assertNotEqual(g.lookup("ESP1","B","A")["status"],"VERIFIED")
 def test_fresh_10minute_cache(self):
    called=[];current=[NOW]
    g=OfficialFixtureGateway(fetcher=make_fetch(ld(),called),
        resolve_id=lambda league,n:n,gate_runner=gate_runner,clock=lambda:current[0])
    g.lookup("ESP1","A","B")
    current[0]=datetime(2026,11,7,7,11,tzinfo=timezone.utc)
    g.lookup("ESP1","A","B")
    self.assertEqual(len(called),2)
if __name__=="__main__":unittest.main()
