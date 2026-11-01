"""One batch of targeted tests, no previous Poisson/model backtest reruns."""
import json
import sys
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from official_page_lookup_263 import (parse_official_events,official_page_lookup,
    is_approved_url,coverage_inventory,SOURCES)

NOW=datetime(2026,11,1,12,tzinfo=timezone.utc)
DFL='''<table><tr><th>Matchday</th><th>Day</th><th>Date</th><th>Kick-off CET</th><th>Kick-off UTC</th><th>Home</th><th>Away</th><th>Type</th></tr>
<tr><td>9</td><td>Sat</td><td>07-Nov-2026</td><td>15:30</td><td>14:30</td><td>Borussia Dortmund</td><td>SV Elversberg</td><td>Silver</td></tr></table>'''
KNVB='''<div>zaterdag 7 november 2026</div><div>Fortuna Sittard</div><div>16:30</div><div>Telstar</div>'''
EPL='''<h2>Saturday 7 November</h2><p>12:30 Leeds United v Tottenham Hotspur (TNT Sports)</p>
<p>Arsenal v Hull City</p>'''
JSONLD='''<script type="application/ld+json">{"@context":"https://schema.org","@type":"SportsEvent",
"homeTeam":{"@type":"SportsTeam","name":"Club Home"},
"awayTeam":{"@type":"SportsTeam","name":"Club Away"},
"startDate":"2026-11-07T20:00:00+01:00"}</script>'''

def equiv(o,r):return o==r

class OfficialSourceCoverageTests(unittest.TestCase):
    def test_ten_leagues_only_source_configuration(self):
        self.assertEqual(len(coverage_inventory()),10)
        self.assertTrue(all(not r['all_fixtures_covered'] for r in coverage_inventory().values()))
    def test_url_rejects_spoof_subdomain(self):
        self.assertFalse(is_approved_url('https://www.knvb.nl.evil.test/a','NED1'))
    def test_url_rejects_username(self):
        self.assertFalse(is_approved_url('https://bad@knvb.nl/a','NED1'))
    def test_bad_domain_rejected_before_fetch(self):
        calls=[]
        r=official_page_lookup('GER1','Borussia Dortmund','SV Elversberg',now=NOW,
                               source_url='https://evil.test',fetcher=lambda url:calls.append(url),same_team=equiv)
        self.assertEqual(r['status'],'REJECTED');self.assertEqual(calls,[])
    def test_dfl_correct_columns_real_fixture_shape(self):
        rows=parse_official_events('GER1',DFL)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['home'],'Borussia Dortmund')
        self.assertEqual(rows[0]['away'],'SV Elversberg')
        self.assertEqual(rows[0]['kickoff_utc'],'2026-11-07T14:30:00+00:00')
    def test_dfl_verified_with_actual_fetched_page_callback(self):
        calls=[]
        def fetch(url):calls.append(url);return url,DFL
        r=official_page_lookup('GER1','Borussia Dortmund','SV Elversberg',now=NOW,fetcher=fetch,same_team=equiv)
        self.assertEqual(r['status'],'VERIFIED_OFFICIAL_FIXTURE')
        self.assertEqual(r['source_origin'],'FETCHED_OFFICIAL_PAGE')
        self.assertEqual(len(calls),1)
    def test_netherlands_home_time_away(self):
        rows=parse_official_events('NED1',KNVB)
        self.assertEqual([(r['home'],r['away']) for r in rows],[('Fortuna Sittard','Telstar')])
        r=official_page_lookup('NED1','Fortuna Sittard','Telstar',now=NOW,html=KNVB,same_team=equiv)
        self.assertEqual(r['kickoff_utc'],'2026-11-07T15:30:00+00:00')
    def test_premier_date_only_not_guessed_time(self):
        r=official_page_lookup('ENG1','Arsenal','Hull City',now=NOW,html=EPL,same_team=equiv)
        self.assertEqual(r['status'],'VERIFIED_OFFICIAL_FIXTURE_DATE_ONLY')
        self.assertIsNone(r['kickoff_utc'])
    def test_premier_explicit_time_timezone(self):
        r=official_page_lookup('ENG1','Leeds United','Tottenham Hotspur',now=NOW,html=EPL,same_team=equiv)
        self.assertEqual(r['status'],'VERIFIED_OFFICIAL_FIXTURE_DATE_ONLY')
        self.assertIsNone(r['kickoff_utc'])
        self.assertTrue(r['listed_time_unreconfirmed'])
    def test_cancelled_structured_event_is_not_accepted(self):
        event=JSONLD.replace('\"startDate\"','\"eventStatus\":\"https://schema.org/EventCancelled\",\"startDate\"')
        self.assertEqual(parse_official_events('ESP1',event, 'jsonld'),[])
    def test_structured_jsonld_eligible_for_all_but_not_guaranteed(self):
        for lg in SOURCES:
            with self.subTest(league=lg):
                res=parse_official_events(lg,JSONLD,'jsonld')
                self.assertEqual(len(res),1)
                self.assertEqual(res[0]['away'],'Club Away')
    def test_redirect_different_domain_rejected(self):
        r=official_page_lookup('GER1','Borussia Dortmund','SV Elversberg',now=NOW,
           fetcher=lambda url:('https://fake.example/fixtures',DFL),same_team=equiv)
        self.assertEqual(r['status'],'NOT_VERIFIED')
    def test_ambiguous_duplicate_dates_rejected(self):
        dfl=DFL.replace('</table>','<tr><td>9</td><td>Sun</td><td>08-Nov-2026</td><td>15:30</td><td>14:30</td><td>Borussia Dortmund</td><td>SV Elversberg</td><td>Silver</td></tr></table>')
        r=official_page_lookup('GER1','Borussia Dortmund','SV Elversberg',html=dfl,now=NOW,same_team=equiv)
        self.assertEqual(r['status'],'REVIEW_REQUIRED')
    def test_absent_on_site_not_absent_in_reality(self):
        r=official_page_lookup('GER1','Arsenal','Hull City',html=DFL,now=NOW,same_team=equiv)
        self.assertTrue(r['does_not_prove_no_fixture'])
    def test_no_auto_match_discovery(self):
        r=official_page_lookup('GER1','','',html=DFL,now=NOW,same_team=equiv)
        self.assertNotEqual(r.get('status'),'VERIFIED_OFFICIAL_FIXTURE')
    def test_past_fixture_rejected(self):
        r=official_page_lookup('GER1','Borussia Dortmund','SV Elversberg',html=DFL,now=NOW+timedelta(days=10),same_team=equiv)
        self.assertEqual(r['reason'],'kickoff_outside_7_days')
    def test_missing_parser_data_not_verified(self):
        r=official_page_lookup('POR1','Sporting CP','SL Benfica',now=NOW,html='<p>Under construction</p>',same_team=equiv)
        self.assertEqual(r['status'],'NOT_VERIFIED')
    def test_malformed_html_fails_closed(self):
        r=official_page_lookup('GER1','A','B',html=' '*2_000_001,now=NOW,same_team=equiv)
        self.assertEqual(r['status'],'NOT_VERIFIED')

if __name__=='__main__':unittest.main()
