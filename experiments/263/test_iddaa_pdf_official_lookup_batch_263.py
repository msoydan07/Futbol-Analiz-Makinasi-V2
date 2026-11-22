"""The live first-PDF path must use current cached league sources, not a
hard-coded obsolete league-week adapter. No external internet in unit tests."""
import unittest
from datetime import datetime,timezone
from unittest.mock import patch
from iddaa_pdf_official_lookup_batch_263 import OriginalPdfOfficialGateway
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway
from iddaa_pdf_session_263 import run_session
from iddaa_pdf_bulletin_263 import SCHEMA as INPUT_SCHEMA

NOW=datetime(2026,11,22,11,0,tzinfo=timezone.utc)
NOV22='''<main>
<h1>Fixture amendments for Premier League matches in November</h1>
<p>The November 2026 broadcast selections and displaced matches have been released</p>
<p>All fixtures are GMT and are 15:00 kick-offs unless otherwise stated.</p>
<h2>Sunday 22 November</h2>
<p>14:00 Hull City v Brighton (Sky Sports)</p>
<p>16:30 Liverpool v Man Utd (Sky Sports)</p>
</main>'''
URL="https://www.premierleague.com/en/news/4725574/fixture-amendments-for-november"


def gateway():
    calls=[]
    def fetcher(url,league):
        calls.append((url,league))
        return url,NOV22
    canon={"Brighton":"Brighton & Hove Albion",
           "Man Utd":"Manchester United"}
    def same(lg,name):return canon.get(name,name)
    def gate_runner(league,h,a,lookup_override=None):
        if lookup_override is None:
            return {"status":"NOT_VERIFIED","reason":"OLD_ADAPTER_NO_MATCH"}
        data=lookup_override(h,a)
        if data.get("source_origin")!="FETCHED_OFFICIAL_PAGE_BATCH_CACHE":
            return {"status":"NOT_VERIFIED","reason":"NOT_OFFICIAL_PAGE"}
        return {"status":"VERIFIED","league":league,
                "source_url":data["source_url"],
                "retrieved_at_utc":data["retrieved_at_utc"],
                "kickoff_utc":data["kickoff_utc"],
                "home_id":same(league,data["home"]),
                "away_id":same(league,data["away"])}
    g=OfficialFixtureGateway(fetcher=fetcher,
              clock=lambda:NOW,resolve_id=same,
              gate_runner=gate_runner)
    return OriginalPdfOfficialGateway(gateway=g),calls


class TestPdfCurrentOfficialGateway(unittest.TestCase):
    def test_nov22_both_premier_league_matches_from_single_real_current_article(self):
        bridge,calls=gateway()
        a=bridge.lookup("ENG1","Hull City","Brighton & Hove Albion")
        b=bridge.lookup("ENG1","Liverpool","Manchester United")
        self.assertEqual(a["status"],"VERIFIED_OFFICIAL_FIXTURE")
        self.assertEqual(a["kickoff_utc"],"2026-11-22T14:00:00+00:00")
        self.assertEqual(b["status"],"VERIFIED_OFFICIAL_FIXTURE")
        self.assertEqual(b["kickoff_utc"],"2026-11-22T16:30:00+00:00")
        self.assertEqual(len(calls),1)
        self.assertEqual(bridge.lookup("ENG1","Manchester United","Liverpool")["status"],"NOT_VERIFIED")
    def test_gateway_never_accepts_wrong_or_forged_host_as_verified(self):
        class Wrong:
            def lookup(self,league,h,a):
                return {"status":"VERIFIED","league":league,
                        "source_url":"https://premierleague.com.evil.test/matches",
                        "retrieved_at_utc":NOW.isoformat(),
                        "kickoff_utc":"2026-11-22T14:00:00+00:00"}
        self.assertEqual(OriginalPdfOfficialGateway(gateway=Wrong()).lookup(
            "ENG1","Hull City","Brighton & Hove Albion")["status"],"NOT_VERIFIED")
    def test_default_session_uses_new_gateway_not_static_adapter(self):
        import iddaa_pdf_official_lookup_batch_263 as module
        bridge,calls=gateway()
        original=module.OriginalPdfOfficialGateway
        def factory(*args,**kwargs):return bridge
        data={"schema":INPUT_SCHEMA,"source_domain":"iddaa.com",
              "pdf_sha256":"e"*64,"pdf_capture_utc":"2026-11-22T10:30:00+00:00",
              "rows":[{"page":1,"league":"ENG1","home_label":"Hull City",
                       "away_label":"Brighton","match_date_tr":"2026-11-22",
                       "kickoff_time_tr":"17:00",
                       "status":"PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK",
                       "odds":{"MS1":5.77,"MSX":4.14,"MS2":1.34,
                               "O25_UNDER":1.87,"O25_OVER":1.60,
                               "BTTS_YES":1.76,"BTTS_NO":1.69}}]}
        with patch.object(module,"OriginalPdfOfficialGateway",side_effect=factory):
            result=run_session(data,now=NOW,max_workers=1)
        self.assertEqual(result["n_official"],1)
        self.assertEqual(result["rows"][0]["status"],"ONE_OFFICIAL_SOURCE_CONFIRMED")
        self.assertEqual(len(calls),1)
if __name__=="__main__":unittest.main()
