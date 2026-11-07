import unittest
from datetime import datetime,timezone
from official_page_lookup_263 import parse_official_events,official_page_lookup,SOURCES
NOW=datetime(2026,11,7,7,0,tzinfo=timezone.utc)
NEWS='''<h1>Fixture amendments for Premier League matches in November</h1>
<p>21 Sep 2026</p><p>The November 2026 broadcast selections have been released.</p>
<p>All fixtures are GMT and are 15:00 kick-offs unless otherwise stated.</p>
<h2>Saturday 7 November</h2>
<p>12:30 Leeds v Spurs (TNT Sports)</p>
<p>Arsenal v Hull City</p>
<p>Fulham v Newcastle</p>
<p>17:30 Nott'm Forest v Man City (Sky Sports)</p>'''

class PremierCurrentSource(unittest.TestCase):
 def test_source_specific_updated_url(self):
  self.assertIn('/4725574/',SOURCES['ENG1'][0])
 def test_all_four_grounded_gmt_times(self):
  rows=parse_official_events('ENG1',NEWS)
  self.assertEqual(len(rows),4)
  self.assertEqual(rows[0]['home'],'Leeds United')
  self.assertEqual(rows[0]['away'],'Tottenham Hotspur')
  self.assertEqual([r['kickoff_utc'] for r in rows],
       ['2026-11-07T12:30:00+00:00',
        '2026-11-07T15:00:00+00:00','2026-11-07T15:00:00+00:00',
        '2026-11-07T17:30:00+00:00'])
  self.assertEqual(rows[3]['home'],'Nottingham Forest')
  self.assertEqual(rows[3]['away'],'Manchester City')
 def test_unconfirmed_default_time_never_promoted(self):
  old=NEWS.replace('All fixtures are GMT and are 15:00 kick-offs unless otherwise stated.','No default kickoff time was published')
  rows=parse_official_events('ENG1',old)
  self.assertTrue(all(r['format']=='epl' for r in rows))
  x=official_page_lookup('ENG1','Arsenal','Hull City',now=NOW,html=old,same_team=lambda a,b:a==b)
  self.assertEqual(x['status'],'VERIFIED_OFFICIAL_FIXTURE_DATE_ONLY')
 def test_explicit_current_official_article_can_verify(self):
  x=official_page_lookup('ENG1','Arsenal','Hull City',now=NOW,html=NEWS,same_team=lambda a,b:a==b)
  self.assertEqual(x['status'],'VERIFIED_OFFICIAL_FIXTURE')
  self.assertEqual(x['kickoff_utc'],'2026-11-07T15:00:00+00:00')
 def test_wrong_home_away_is_blocked(self):
  x=official_page_lookup('ENG1','Tottenham Hotspur','Leeds United',now=NOW,html=NEWS,same_team=lambda a,b:a==b)
  self.assertNotEqual(x['status'],'VERIFIED_OFFICIAL_FIXTURE')
 def test_wrong_season_does_not_promote(self):
  old=NEWS.replace('November 2026','November 2025')
  rows=parse_official_events('ENG1',old)
  self.assertTrue(all(r['format']=='epl' for r in rows))
if __name__=='__main__':unittest.main()
