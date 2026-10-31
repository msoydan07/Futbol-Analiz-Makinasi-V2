import unittest
from datetime import datetime,timezone
from tff_fixture_lookup import lookup
NOW=datetime(2026,10,31,12,tzinfo=timezone.utc)
LINES=["Trendyol Süper Lig Adnan Süvari Sezonu - 10.Hafta","Tarih","01.11.2026","Pazar","19:00","KASIMPAŞA A.Ş.","-","Detaylar","RECEP TAYYİP ERDOĞAN STADYUMU","BEŞİKTAŞ A.Ş.","02.11.2026","Pazartesi","20:00","GENÇLERBİRLİĞİ","CORENDON ALANYASPOR","Trendyol 1. Lig - 13.Hafta"]
class LookupTest(unittest.TestCase):
 def test_requested_fixture(self):
  result=lookup("Kasımpaşa","Beşiktaş",now=NOW,lines=LINES)
  self.assertEqual(result["status"],"VERIFIED_OFFICIAL_FIXTURE",result)
  self.assertEqual(result["kickoff_turkey"],"2026-11-01T19:00:00+03:00")
 def test_not_present(self):
  self.assertEqual(lookup("Fenerbahçe","Beşiktaş",now=NOW,lines=LINES)["status"],"NOT_VERIFIED")
 def test_reversed_teams(self):
  self.assertEqual(lookup("Beşiktaş","Kasımpaşa",now=NOW,lines=LINES)["status"],"NOT_VERIFIED")
 def test_old_fixture(self):
  self.assertEqual(lookup("Kasımpaşa","Beşiktaş",now=datetime(2026,11,10,tzinfo=timezone.utc),lines=LINES)["status"],"OUTSIDE_WINDOW")
if __name__=="__main__":unittest.main()
