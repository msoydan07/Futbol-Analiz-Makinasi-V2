"""Network-free discovery regression: exact real-looking match cards, no invented fixtures."""
import unittest
from datetime import datetime, timezone
from official_browser_fixture import discover

NOW = datetime(2026, 10, 31, 12, tzinfo=timezone.utc)

class TestThreeLeagueDiscovery(unittest.TestCase):
    def test_belgium_visible_card(self):
        lines = ["KV Mechelen", "15:00", "sam. 31 oct.", "KRC Genk"]
        self.assertEqual(discover("BEL1", lines, NOW), [("KV Mechelen", "KRC Genk")])

    def test_portugal_visible_card(self):
        lines = ["sáb. 31 out", "J10", "FCP", "20h30", "EPF"]
        self.assertEqual(discover("POR1", lines, NOW), [("FC Porto", "Estoril Praia")])

    def test_championship_visible_match(self):
        lines = ["Tuesday 3 November", "Sky Bet Championship",
                 "Blackburn Rovers v Stoke City (19:45)"]
        self.assertEqual(discover("ENG2", lines, NOW),
                         [("Blackburn Rovers", "Stoke City")])

    def test_championship_wrong_division_blocked(self):
        lines = ["Tuesday 3 November", "Sky Bet League One",
                 "Blackburn Rovers v Stoke City (19:45)"]
        self.assertEqual(discover("ENG2", lines, NOW), [])

    def test_missing_kickoff_blocked(self):
        self.assertEqual(discover("POR1", ["sáb. 31 out", "FCP", "EPF"], NOW), [])

    def test_outside_seven_day_window_blocked(self):
        lines = ["Tuesday 10 November", "Sky Bet Championship",
                 "Blackburn Rovers v Stoke City (19:45)"]
        self.assertEqual(discover("ENG2", lines, NOW), [])

if __name__ == "__main__":
    unittest.main()
