"""Regression tests for provisional manual fixture intake."""
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from manual_match_intake import intake

class ManualIntakeTests(unittest.TestCase):
    def future(self):
        return (datetime.now(ZoneInfo("Europe/Istanbul"))+timedelta(days=2)).strftime("%Y-%m-%d %H:%M").split()
    def test_manual_is_not_verified(self):
        d,t=self.future()
        r=intake("TUR1","Galatasaray","Konyaspor",d,t)
        self.assertEqual(r["status"],"MANUAL_INPUT_ACCEPTED")
        self.assertFalse(r["fixture_verified"])
        self.assertFalse(r["pilot_eligible"])
        self.assertEqual(r["analysis_gate"],"PROVISIONAL_DATA_AUDIT_ONLY")
    def test_unknown_league_rejected(self):
        d,t=self.future()
        self.assertEqual(intake("FAKE","A","B",d,t)["status"],"REJECTED")
    def test_same_teams_rejected(self):
        d,t=self.future()
        self.assertEqual(intake("TUR1","A","a",d,t)["status"],"REJECTED")
    def test_past_rejected(self):
        self.assertEqual(intake("TUR1","A","B","2020-01-01","12:00")["status"],"REJECTED")
    def test_invalid_time_rejected(self):
        self.assertEqual(intake("TUR1","A","B","2026-11-01","25:00")["status"],"REJECTED")

if __name__=="__main__":
    unittest.main()
