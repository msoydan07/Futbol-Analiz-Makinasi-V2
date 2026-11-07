import unittest
from datetime import datetime,timezone
from official_page_lookup_263 import parse_official_events,official_page_lookup,SOURCES
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway

NOW=datetime(2026,11,7,8,0,tzinfo=timezone.utc)
HTML='''<h1>MPP : Les infos de la J10</h1><p>Publié le 05/11/2026 à 11:00</p>
<h3>Samedi 7 novembre</h3>
<p>AJ Auxerre (13e) - Paris FC (4e), samedi (19h00), sur Ligue 1+</p>
<p>Paris Saint-Germain (1er) - ESTAC Troyes (16e), samedi (21h05), sur Ligue 1+</p>
<h3>Dimanche 8 novembre</h3><p>Stade Rennais FC - LOSC (2e), dimanche (15h00), sur Ligue 1+</p>'''

class FrenchCurrentSourceTests(unittest.TestCase):
 def test_recent_publication_and_new_times(self):
  events=parse_official_events("FRA1",HTML)
  self.assertEqual(len(events),3)
  self.assertEqual(events[0]["kickoff_utc"],"2026-11-07T18:00:00+00:00")
  self.assertEqual(events[1]["kickoff_utc"],"2026-11-07T20:05:00+00:00")
  self.assertEqual(events[2]["kickoff_utc"],"2026-11-08T14:00:00+00:00")
 def test_date_missing_is_not_promoted(self):
  self.assertEqual(parse_official_events("FRA1",HTML.replace("05/11/2026","04/09/2026")),[])
 def test_title_or_weekday_missing_is_not_promoted(self):
  self.assertEqual(parse_official_events("FRA1",HTML.replace("MPP : Les infos de la J10","Old draft")),[])
  self.assertEqual(parse_official_events("FRA1",HTML.replace("samedi (19h00)","dimanche (19h00)"))[0]["home"],"Paris Saint-Germain")
 def test_official_live_page_can_confirm_single_match_only(self):
  x=official_page_lookup("FRA1","AJ Auxerre","Paris FC",now=NOW,html=HTML,same_team=lambda a,b:a==b)
  self.assertEqual(x["status"],"VERIFIED_OFFICIAL_FIXTURE")
  self.assertEqual(x["kickoff_utc"],"2026-11-07T18:00:00+00:00")
  self.assertNotEqual(official_page_lookup("FRA1","Paris FC","AJ Auxerre",now=NOW,html=HTML,
                                            same_team=lambda a,b:a==b)["status"],"VERIFIED_OFFICIAL_FIXTURE")
 def test_old_fallback_blocked_in_france(self):
  calls=[]
  def old(l,h,a,lookup_override=None):
   calls.append(lookup_override is None)
   return {"status":"NOT_VERIFIED","reason":"OLD_DATA"}
  gate=OfficialFixtureGateway(fetcher=lambda u,l:(u,"<p>no fixtures</p>"),
      resolve_id=lambda l,n:n,gate_runner=old,clock=lambda:NOW)
  x=gate.lookup("FRA1","AJ Auxerre","Paris FC")
  self.assertEqual(x["reason"],"NEWER_FRA1_OFFICIAL_MATCHWEEK_PAGE_REQUIRED")
  self.assertEqual(calls,[])
 def test_french_source_is_authoritative_domain(self):
  self.assertIn("ligue1.com",SOURCES["FRA1"][0])
if __name__=="__main__":unittest.main()
