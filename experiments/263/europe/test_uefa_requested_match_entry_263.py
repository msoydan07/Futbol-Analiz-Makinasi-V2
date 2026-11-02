"""New deterministic single UEFA match entry acceptance. All example HTML synthetic."""
import json
import unittest
from datetime import datetime,timezone
from pathlib import Path

from uefa_requested_match_entry_263 import (
    SOURCES,requested_europe_match,extract_one_official_fixture,
    official_url_ok
)
INDEX=json.loads(Path("experiments/263/evidence/identity_index_263.json").read_text(encoding="utf-8"))
NOW=datetime.fromisoformat("2026-11-02T17:00:00+03:00")
DOC_CL="""<html><body><h1>2026/27 Champions League: All the league phase fixtures and results</h1>
<p>League phase fixtures by date</p>
<p>Kick-offs are 21:00 unless stated; all times CET.</p>
<h2>Matchday 4</h2><p>Tuesday 3 November 2026</p>
<p><a>Galatasaray vs Stuttgart</a> (18:45)</p>
<p><a>Barcelona vs Aston Villa</a></p>
<p><a>Manchester United vs Roma</a></p>
<p>Wednesday 4 November 2026</p><p>Fenerbahçe vs Liverpool (18:45)</p>
<h2>Matchday 5</h2><p>Tuesday 24 November 2026</p><p>Galatasaray vs Aston Villa (18:45)</p></body></html>"""
DOC_EL="""<html><body><h1>2026/27 Europa League: All the league phase fixtures and results</h1>
<p>League phase fixtures by date</p>
<p>Kick-offs are 21:00 unless stated; all times CET.</p>
<h2>Matchday 4</h2><p>Thursday 5 November 2026</p>
<p>Celtic vs Beşiktaş</p><p>Crystal Palace vs Hoffenheim (18:45)</p>
<p>AZ Alkmaar vs Juventus</p></body></html>"""
class RealEntrypoint(unittest.TestCase):
    def test_eligible_pair_checks_one_official_article_and_rejects_model(self):
        calls=[]
        def fake(comp):
            calls.append(comp);return DOC_CL,SOURCES[comp]
        got=requested_europe_match("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=NOW,official_provider=fake)
        self.assertEqual(calls,["UEFA_CL"])
        self.assertTrue(got["fixture_verified"])
        self.assertEqual(got["fixture"]["kickoff_utc"],"2026-11-03T20:00:00+00:00")
        self.assertEqual(got["fixture"]["kickoff_time_basis"],"UEFA_ARTICLE_PUBLISHED_21_00_CET_DEFAULT")
        self.assertFalse(got["model_forecast_authorized"])
        self.assertFalse(got["pilot_recorded"])
    def test_explicit_early_kickoff_not_converted_to_21(self):
        got=requested_europe_match("UEFA_CL","Galatasaray","Stuttgart",index=INDEX,now=NOW,
                                   official_provider=lambda c:(DOC_CL,SOURCES[c]))
        self.assertTrue(got["fixture_verified"])
        self.assertEqual(got["fixture"]["kickoff_utc"],"2026-11-03T17:45:00+00:00")
    def test_outside_known_current_membership_calls_no_provider(self):
        calls=[]
        got=requested_europe_match("UEFA_CL","Galatasaray","Leicester",index=INDEX,now=NOW,
                                    official_provider=lambda c:calls.append(c))
        self.assertEqual(calls,[])
        self.assertEqual(got["status"],"ANALYSIS_SKIPPED_OUTSIDE_TEN_LEAGUES")
        self.assertIsNone(got["fixture"])
    def test_unknown_celtic_causes_stop_even_if_official_fixture_exists(self):
        calls=[]
        got=requested_europe_match("UEFA_EL","Celtic","Beşiktaş",index=INDEX,now=NOW,
                                    official_provider=lambda c:calls.append(c))
        self.assertEqual(calls,[])
        self.assertEqual(got["status"],"ANALYSIS_SKIPPED_TEAM_SCOPE_UNVERIFIED")
    def test_europa_eligible_teams_fetch_only_europa(self):
        calls=[]
        got=requested_europe_match("UEFA_EL","Crystal Palace","Hoffenheim",index=INDEX,now=NOW,
                                   official_provider=lambda c:(calls.append(c) or DOC_EL,SOURCES[c]))
        self.assertTrue(got["fixture_verified"])
        self.assertEqual(calls,["UEFA_EL"])
        self.assertEqual(got["fixture"]["kickoff_utc"],"2026-11-05T17:45:00+00:00")
    def test_seven_day_limit_prevents_looking_ahead_for_far_fixture(self):
        got=requested_europe_match("UEFA_CL","Galatasaray","Aston Villa",index=INDEX,now=NOW,
                                   official_provider=lambda c:(DOC_CL,SOURCES[c]))
        self.assertFalse(got["fixture_verified"])
        self.assertEqual(got["status"],"OFFICIAL_UEFA_FIXTURE_NOT_FOUND_OR_AMBIGUOUS")
    def test_official_unavailable_no_fallback_guess_or_model(self):
        got=requested_europe_match("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=NOW,
                                   official_provider=lambda c:(_ for _ in ()).throw(OSError("network")))
        self.assertEqual(got["status"],"OFFICIAL_UEFA_FIXTURE_NOT_VERIFIED")
        self.assertFalse(got["fixture_verified"])
        self.assertIsNone(got["fixture"])
    def test_wrong_competition_url_or_evil_host_rejected(self):
        for url in (SOURCES["UEFA_EL"],SOURCES["UEFA_CL"].replace("www.uefa.com","www.uefa.com.evil.io")):
            with self.subTest(url=url):
                got=requested_europe_match("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=NOW,
                                           official_provider=lambda c:(DOC_CL,url))
                self.assertFalse(got["fixture_verified"])
    def test_article_document_season_mismatch_fail_closed(self):
        bad=DOC_CL.replace("2026/27","2025/26")
        got=requested_europe_match("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=NOW,
                                   official_provider=lambda c:(bad,SOURCES[c]))
        self.assertEqual(got["status"],"OFFICIAL_UEFA_FIXTURE_NOT_VERIFIED")
    def test_fixture_from_result_cannot_be_invented_as_future(self):
        scored=DOC_CL.replace("Barcelona vs Aston Villa","Barcelona 8-0 Aston Villa")
        got=requested_europe_match("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=NOW,
                                   official_provider=lambda c:(scored,SOURCES[c]))
        self.assertFalse(got["fixture_verified"])
    def test_no_source_default_kickoff_text_means_no_clock_guess(self):
        bad=DOC_CL.replace("Kick-offs are 21:00 unless stated; all times CET.","Kickoffs TBD.")
        got=requested_europe_match("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=NOW,
                                   official_provider=lambda c:(bad,SOURCES[c]))
        self.assertEqual(got["status"],"OFFICIAL_UEFA_FIXTURE_NOT_VERIFIED")
    def test_wrong_direction_of_fixture_not_verified(self):
        got=requested_europe_match("UEFA_CL","Aston Villa","Barcelona",index=INDEX,now=NOW,
                                   official_provider=lambda c:(DOC_CL,SOURCES[c]))
        self.assertFalse(got["fixture_verified"])
    def test_script_injection_does_not_count_as_visible_official_fixture(self):
        bad=DOC_CL.replace("<p><a>Barcelona vs Aston Villa</a></p>",
            "<script>Barcelona vs Aston Villa</script>")
        got=requested_europe_match("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=NOW,
                                   official_provider=lambda c:(bad,SOURCES[c]))
        self.assertFalse(got["fixture_verified"])
    def test_after_kickoff_no_future_fixture(self):
        later=datetime.fromisoformat("2026-11-06T12:00:00+03:00")
        got=requested_europe_match("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=later,
                                   official_provider=lambda c:(DOC_CL,SOURCES[c]))
        self.assertFalse(got["fixture_verified"])
    def test_single_source_only_and_no_identity_fuzzy(self):
        got=requested_europe_match("UEFA_CL","FC Barcelona (ESP)","Aston Villa",index=INDEX,now=NOW,
                                   official_provider=lambda c:1/0)
        self.assertFalse(got["fixture_verified"])
        self.assertEqual(got["status"],"ANALYSIS_SKIPPED_TEAM_SCOPE_UNVERIFIED")
if __name__=="__main__":unittest.main()
