import unittest
from datetime import datetime,timezone
from official_page_lookup_263 import parse_official_events,official_page_lookup,SOURCES
NOW=datetime(2026,11,7,7,0,tzinfo=timezone.utc)

ITA='''<h1>Le designazioni arbitrali dell'11ª</h1><p>04/11/2026</p>
<p>Le gare del 6 all’8 novembre per la Serie A</p>
<p>CAGLIARI – FROSINONE Sabato 7/11 h. 15.00</p>
<p>TORINO – LECCE Sabato 7/11 h.15.00</p>
<p>PARMA – BOLOGNA Sabato 7/11 h. 18.00</p>
<p>ROMA – SASSUOLO Sabato 7/11 h. 20.45</p>'''

TFF='''<h2>Trendyol Süper Lig Adnan Süvari Sezonu - 11.Hafta</h2>
<div>07.11.2026</div><div>Cumartesi</div><div>13:30</div>
<div>EYÜPSPOR</div><div>-</div><div>Detaylar</div>
<div>ESENYURT NECMİ KADIOĞLU STADI</div><div>KOCAELİSPOR</div>
<div>(H) MELEK DAKAN</div>
<div>07.11.2026</div><div>Cumartesi</div><div>16:00</div>
<div>SAMSUNSPOR A.Ş.</div><div>-</div><div>Detaylar</div>
<div>SAMSUN YENİ 19 MAYIS</div><div>TÜMOSAN KONYASPOR</div>
<div>(H) AYŞE HAKEM</div>
<h2>Trendyol 1. Lig - 14.Hafta</h2>
<div>07.11.2026</div><div>19:00</div><div>ALT LİG TAKIMI</div>
<div>-</div><div>Detaylar</div><div>ALT LİG STADI</div>
<div>RAKİP</div><div>(H) HAKEM</div>'''
def same(x,y):return x==y

class StrictOfficialWeekTests(unittest.TestCase):
 def test_both_source_urls_are_not_generic(self):
    self.assertIn('le-designazioni-arbitrali-della-11a',SOURCES['ITA1'][0])
    self.assertIn('ftxtID=2966',SOURCES['TUR1'][0])
 def test_italy_complete_all_four_and_utc(self):
    e=parse_official_events('ITA1',ITA)
    self.assertEqual(len(e),4)
    self.assertEqual(e[0]['home'],'CAGLIARI')
    self.assertEqual(e[0]['kickoff_utc'],'2026-11-07T14:00:00+00:00')
    self.assertEqual(e[-1]['kickoff_utc'],'2026-11-07T19:45:00+00:00')
 def test_italy_wrong_weekday_cannot_verify(self):
    self.assertEqual(parse_official_events('ITA1',ITA.replace('Sabato 7/11','Domenica 7/11')),[])
 def test_italy_missing_anchor_or_year_is_rejected(self):
    self.assertEqual(parse_official_events('ITA1',ITA.replace('04/11/2026','04/11/2025')),[])
    self.assertEqual(parse_official_events('ITA1',ITA.replace('designazioni arbitrali','unrelated article')),[])
 def test_italy_must_not_flip_home_away(self):
    self.assertEqual(official_page_lookup('ITA1','FROSINONE','CAGLIARI',now=NOW,html=ITA,same_team=same)['status'],'NOT_VERIFIED')
    self.assertEqual(official_page_lookup('ITA1','CAGLIARI','FROSINONE',now=NOW,html=ITA,same_team=same)['status'],'VERIFIED_OFFICIAL_FIXTURE')
 def test_tff_only_top_division_and_local_time(self):
    e=parse_official_events('TUR1',TFF)
    self.assertEqual(len(e),2)
    self.assertEqual(e[0]['home'],'EYÜPSPOR')
    self.assertEqual(e[0]['away'],'KOCAELİSPOR')
    self.assertEqual(e[0]['kickoff_utc'],'2026-11-07T10:30:00+00:00')
    self.assertEqual(e[-1]['kickoff_utc'],'2026-11-07T13:00:00+00:00')
 def test_tff_no_referee_no_team_borrowing(self):
    bad=TFF.replace('<div>(H) MELEK DAKAN</div>','')
    e=parse_official_events('TUR1',bad)
    self.assertEqual(len(e),1)
    self.assertEqual(e[0]['home'],'SAMSUNSPOR A.Ş.')
 def test_tff_missing_week_heading_no_fabrication(self):
    self.assertEqual(parse_official_events('TUR1',TFF.replace('11.Hafta','12.Hafta')),[])
 def test_tff_heading_split_cannot_leak_championship(self):
    split=TFF.replace('<h2>Trendyol 1. Lig - 14.Hafta</h2>',
                      '<h2>Trendyol 1. Lig</h2><h3>14.Hafta</h3>')
    self.assertEqual(len(parse_official_events('TUR1',split)),2)
 def test_tff_missing_lower_division_boundary_fail_closed(self):
    bad=TFF.replace('Trendyol 1. Lig - 14.Hafta','Other competition')
    self.assertEqual(parse_official_events('TUR1',bad),[])
 def test_tff_no_identity_when_away_unknown(self):
    r=official_page_lookup('TUR1','EYÜPSPOR','UNKNOWN',now=NOW,html=TFF,same_team=same)
    self.assertNotEqual(r['status'],'VERIFIED_OFFICIAL_FIXTURE')
if __name__=='__main__':unittest.main()
