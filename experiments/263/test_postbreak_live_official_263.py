"""Offline safety regression only: mocked official HTML, no bookmaker calls."""
import unittest
from datetime import datetime,timezone
from iddaa_pdf_live_official_263 import lookup,CURRENT_PAGES
from postbreak_freshness_gate_263 import freshness_gate,EXCEPTIONS
from iddaa_pdf_team_alias_preflight_263 import index_registry

T=datetime(2026,11,21,10,0,tzinfo=timezone.utc)
PL_HTML="""<html><body>
<h1>Fixture amendments for Premier League matches in November</h1>
<p>November 2026 schedule</p>
<p>All fixtures are GMT and are 15:00 kick-offs unless otherwise stated</p>
<p>Saturday 21 November</p><p>12:30 Man City v Fulham (TNT Sports)</p>
<p>Aston Villa v Sunderland</p>
</body></html>"""
EFL_HTML="""<html><body><h1>Sky Sports Championship selections</h1>
<table><tr><td>Championship</td><td>21-Nov-26</td><td>Saturday</td>
<td>12:30</td><td>Millwall</td><td>V</td><td>Queens Park Rangers</td><td>Sky Sports</td></tr></table></body></html>"""

class RealSourceAndBreakGate(unittest.TestCase):
    def test_current_official_sources_exclude_stale_week11_articles(self):
        self.assertIn("/4725574",CURRENT_PAGES["ENG1"][0])
        for lg in ("ESP1","ITA1","FRA1"):
            self.assertNotIn("j11",CURRENT_PAGES[lg][0].lower())
            self.assertNotIn("arbitrali",CURRENT_PAGES[lg][0].lower())

    def test_november_official_premier_kickoff_and_no_wrong_team_guess(self):
        url=CURRENT_PAGES["ENG1"][0]
        calls=[]
        def fetch(page):
            calls.append(page)
            return page,PL_HTML
        found=lookup("ENG1","Manchester City","Fulham",now=T,fetcher=fetch)
        self.assertEqual(found["status"],"VERIFIED_OFFICIAL_FIXTURE",found)
        self.assertEqual(found["kickoff_utc"],"2026-11-21T12:30:00+00:00")
        self.assertEqual(calls,[url])
        reversed_=lookup("ENG1","Fulham","Manchester City",now=T,fetcher=fetch)
        self.assertEqual(reversed_["status"],"NOT_VERIFIED")

    def test_efl_tv_partial_coverage_and_wrong_club_block(self):
        found=lookup("ENG2","Millwall","Queens Park Rangers",now=T,
                     fetcher=lambda url:(url,EFL_HTML))
        self.assertEqual(found["status"],"VERIFIED_OFFICIAL_FIXTURE",found)
        self.assertEqual(found["coverage"],"OFFICIAL_PARTIAL_TELEVISED_ONLY")
        wrong=lookup("ENG2","Millwall","Preston North End",now=T,
                     fetcher=lambda url:(url,EFL_HTML))
        self.assertEqual(wrong["status"],"NOT_VERIFIED")

    def test_javascript_no_timed_events_never_confirms_a_fixture(self):
        for lg,home,away in (("ITA1","Inter","Milan"),
                             ("ESP1","Real Madrid","Barcelona"),
                             ("FRA1","PSG","Marseille")):
            result=lookup(lg,home,away,now=T,fetcher=lambda u:(u,"<html>Loading...</html>"))
            self.assertNotEqual(result.get("status"),"VERIFIED_OFFICIAL_FIXTURE")

    def test_break_only_two_scoped_leagues_and_sources(self):
        for lg in ("ENG1","ENG2"):
            src=EXCEPTIONS[lg]["source"]
            kickoff="2026-11-21T12:30:00+00:00"
            gate={"status":"VERIFIED","source_url":src,
                  "retrieved_at_utc":T.isoformat(),"kickoff_utc":kickoff}
            result=freshness_gate(league=lg,latest="2026-11-08",
                       match_date="2026-11-21",gate=gate,now=T)
            self.assertEqual(result["status"],"REVIEWED_FIRST_POST_BREAK_SCHEDULE_ONLY",result)
            for bad in ("https://unofficial.com","https://www.tff.org/"):
                with self.subTest(lg=lg,bad=bad):
                    changed={**gate,"source_url":bad}
                    self.assertTrue(freshness_gate(league=lg,latest="2026-11-08",
                        match_date="2026-11-21",gate=changed,now=T)["status"].startswith("BLOCKED"))
        assert "TUR1" not in EXCEPTIONS
        self.assertTrue(freshness_gate(league="TUR1",latest="2026-11-08",
                match_date="2026-11-21",gate={},now=T)["status"].startswith("BLOCKED"))

    def test_break_never_extends_to_later_round_or_missing_recent_scores(self):
        gate={"status":"VERIFIED","source_url":EXCEPTIONS["ENG1"]["source"],
              "retrieved_at_utc":T.isoformat(),"kickoff_utc":"2026-11-21T12:30:00+00:00"}
        for latest,day in (("2026-11-05","2026-11-21"),
                           ("2026-11-08","2026-11-29"),
                           ("2026-11-08","2026-12-01")):
            self.assertTrue(freshness_gate(league="ENG1",latest=latest,
                match_date=day,gate=gate,now=T)["status"].startswith("BLOCKED"))
        self.assertEqual(freshness_gate(league="TUR1",latest="2026-11-14",
            match_date="2026-11-21",gate={},now=T)["status"],"NORMAL_TEN_DAY_LIMIT")

if __name__=="__main__":unittest.main()
