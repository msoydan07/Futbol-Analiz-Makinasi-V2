"""Verify TWO genuine official-source snippet formats and prohibit missing matches."""
import unittest
from datetime import datetime,timezone
from serie_a_fixture_lookup import lookup as italy
from ligue1_fixture_lookup import lookup as france

NOW=datetime(2026,11,6,19,10,tzinfo=timezone.utc)
ITALY="""<main><p>VENEZIA – UDINESE    Venerdì 6/11 h. 20.45</p>
<p>SACCHI J.L. (IMPERIALE – MONDIN)</p></main>"""
FRANCE="""<article><p>Vendredi 6 novembre 2026 à 20h45 sur Ligue 1+</p>
<p>Toulouse FC – RC Strasbourg Alsace</p></article>"""

class TonightOfficialSources(unittest.TestCase):
    def test_italy_official_11th_round_date_home_away_and_utc(self):
        x=italy("Venezia","Udinese",now=NOW,html=ITALY)
        self.assertEqual(x["status"],"VERIFIED_OFFICIAL_FIXTURE")
        self.assertEqual(x["kickoff_utc"],"2026-11-06T19:45:00+00:00")
        self.assertTrue(x["source_url"].startswith("https://www.legaseriea.it/"))
        self.assertEqual(italy("Udinese","Venezia",now=NOW,html=ITALY)["status"],"NOT_VERIFIED")
    def test_france_official_10th_round_utc_and_alias(self):
        x=france("Toulouse FC","RC Strasbourg Alsace",now=NOW,html=FRANCE)
        self.assertEqual(x["status"],"VERIFIED_OFFICIAL_FIXTURE")
        self.assertEqual(x["kickoff_utc"],"2026-11-06T19:45:00+00:00")
        self.assertEqual(france("RC Strasbourg Alsace","Toulouse FC",now=NOW,html=FRANCE)["status"],"NOT_VERIFIED")
    def test_no_random_invented_fixture(self):
        self.assertEqual(italy("Roma","Udinese",now=NOW,html=ITALY)["status"],"NOT_VERIFIED")
        self.assertEqual(france("PSG","RC Strasbourg Alsace",now=NOW,html=FRANCE)["status"],"NOT_VERIFIED")
if __name__=="__main__":unittest.main()
