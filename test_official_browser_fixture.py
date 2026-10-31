"""Deterministic browser fixture parser regression tests. No network or browser needed."""
import unittest
from datetime import datetime,timezone
from official_browser_fixture import extract
NOW=datetime(2026,10,31,12,tzinfo=timezone.utc)
class TestOfficialBrowserParser(unittest.TestCase):
 def test_portugal_known_match(self):
  lines=["sáb. 31 out","J10","FCP","20h30","EPF"]
  self.assertEqual([x.isoformat() for x in extract("POR1",lines,"FC Porto","Estoril Praia",NOW)],["2026-10-31T20:30:00+00:00"])
 def test_portugal_other_date(self):
  lines=["dom. 1 nov","J11","FCP","21h15","EPF"]
  self.assertEqual([x.isoformat() for x in extract("POR1",lines,"FC Porto","Estoril Praia",NOW)],["2026-11-01T21:15:00+00:00"])
 def test_portugal_other_teams_full_names(self):
  lines=["sáb. 31 out","J10","Benfica","18h00","Braga"]
  self.assertEqual([x.isoformat() for x in extract("POR1",lines,"Benfica","Braga",NOW)],["2026-10-31T18:00:00+00:00"])
 def test_portugal_different_date_not_mixed(self):
  lines=["sáb. 31 out","FCP","dom. 1 nov","20h30","EPF"]
  self.assertEqual(extract("POR1",lines,"FC Porto","Estoril Praia",NOW),[])
 def test_portugal_unknown_abbreviation_not_guessed(self):
  lines=["sáb. 31 out","SLB","18h00","SCB"]
  self.assertEqual(extract("POR1",lines,"Benfica","Braga",NOW),[])
 def test_portugal_other_club_abbreviations(self):
  lines=["dom. 1 nov","J10","SLB","20h15","SCB"]
  self.assertEqual([x.isoformat() for x in extract("POR1",lines,"SL Benfica","SC Braga",NOW)],["2026-11-01T20:15:00+00:00"])
 def test_portugal_wrong_order(self):
  lines=["sáb. 31 out","J10","EPF","20h30","FCP"]
  self.assertEqual(extract("POR1",lines,"FC Porto","Estoril Praia",NOW),[])
 def test_portugal_missing_time(self):
  self.assertEqual(extract("POR1",["sáb. 31 out","FCP","EPF"],"FC Porto","Estoril Praia",NOW),[])
 def test_belgium(self):
  lines=["KV Mechelen","15:00","sam. 31 oct.","KRC Genk"]
  self.assertEqual([x.isoformat() for x in extract("BEL1",lines,"KV Mechelen","KRC Genk",NOW)],["2026-10-31T15:00:00+00:00"])
 def test_belgium_club_calendar_row(self):
  lines=["za 31 okt - 16:00 KV Mechelen KRC Genk"]
  self.assertEqual([x.isoformat() for x in extract("BEL1",lines,"KV Mechelen","KRC Genk",NOW)],["2026-10-31T15:00:00+00:00"])
 def test_belgium_wrong_away(self):
  self.assertEqual(extract("BEL1",["KV Mechelen","15:00","sam. 31 oct.","Anderlecht"],"KV Mechelen","KRC Genk",NOW),[])
 def test_championship(self):
  lines=["Tuesday 3 November","Sky Bet Championship","Blackburn Rovers v Stoke City (19:45)"]
  self.assertEqual([x.isoformat() for x in extract("ENG2",lines,"Blackburn Rovers","Stoke City",NOW)],["2026-11-03T19:45:00+00:00"])
 def test_championship_match_centre_other_teams(self):
  lines=["Tuesday 3rd November","Sky Bet Championship","Preston North End","19:45","Sheffield United"]
  self.assertEqual([x.isoformat() for x in extract("ENG2",lines,"Preston North End","Sheffield United",NOW)],["2026-11-03T19:45:00+00:00"])
 def test_championship_match_centre_wrong_opponent(self):
  lines=["Tuesday 3rd November","Sky Bet Championship","Preston North End","19:45","Sheffield United"]
  self.assertEqual(extract("ENG2",lines,"Preston North End","Stoke City",NOW),[])
 def test_championship_separate_lines_wrong_division(self):
  lines=["Tuesday 3rd November","Sky Bet League One","Preston North End","19:45","Sheffield United"]
  self.assertEqual(extract("ENG2",lines,"Preston North End","Sheffield United",NOW),[])
 def test_championship_wrong_division(self):
  lines=["Tuesday 3 November","Sky Bet League One","Blackburn Rovers v Stoke City (19:45)"]
  self.assertEqual(extract("ENG2",lines,"Blackburn Rovers","Stoke City",NOW),[])
if __name__=="__main__":unittest.main()
