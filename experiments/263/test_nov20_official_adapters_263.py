"""Nov 20 official league HTML adapters: exact verified match/date/clock."""
import unittest
from datetime import datetime,timezone
from official_page_lookup_263 import SOURCES,parse_official_events,official_page_lookup

LFP="""<html><h1>Programmations TV : J10 et J11</h1>
<h3>11e JOURNÉE DE LIGUE 1 McDONALD’S</h3>
<p>Vendredi 20 novembre 2026 à 20h45 sur Ligue 1+</p>
<p>ESTAC Troyes – Havre AC</p></html>"""
LALIGA="""<html><h1>Horarios de la decimotercera jornada de LALIGA EA SPORTS 2026/27</h1>
<p>LALIGA ha confirmado los horarios de los diez partidos
que arrancará el viernes 20 de noviembre con el encuentro entre
Athletic Club y RCD Espanyol a las 21:00h, y terminará el lunes</p></html>"""

class OfficialNov20(unittest.TestCase):
 def test_ligue1_current_source_and_exact_nov20_time(self):
  self.assertIn("l1_article_5839",SOURCES["FRA1"][0])
  f=parse_official_events("FRA1",LFP)
  self.assertEqual(len(f),1)
  self.assertEqual(f[0]["home"],"ESTAC Troyes")
  self.assertEqual(f[0]["away"],"Havre AC")
  self.assertEqual(f[0]["kickoff_utc"],"2026-11-20T19:45:00+00:00")
 def test_laliga_current_source_and_exact_nov20_time(self):
  self.assertIn("decimotercera",SOURCES["ESP1"][0])
  f=parse_official_events("ESP1",LALIGA)
  self.assertEqual(len(f),1)
  self.assertEqual(f[0]["home"],"Athletic Club")
  self.assertEqual(f[0]["away"],"RCD Espanyol de Barcelona")
  self.assertEqual(f[0]["kickoff_utc"],"2026-11-20T20:00:00+00:00")
 def test_old_round_blocked(self):
  self.assertEqual(parse_official_events("FRA1",LFP.replace("20 novembre","6 novembre")),[])
  self.assertEqual(parse_official_events("ESP1",LALIGA.replace("21:00h","19:00h")),[])
 def test_outside_window_fails_closed(self):
  x=official_page_lookup("ESP1","Athletic Club","RCD Espanyol",
       now=datetime(2026,11,21,0,0,tzinfo=timezone.utc),
       html=LALIGA,same_team=lambda a,b:a in ("RCD Espanyol de Barcelona","RCD Espanyol") and b in ("RCD Espanyol de Barcelona","RCD Espanyol") or a==b)
  self.assertEqual(x["status"],"OUTSIDE_WINDOW")
if __name__=="__main__":unittest.main()
