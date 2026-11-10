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


    def test_efl_official_competition_card_next_matchday(self):
        asof = datetime(2026, 11, 18, tzinfo=timezone.utc)
        lines = ["EFL Championship", "Sync Fixtures", "Fixtures", "All Fixtures",
                 "Sat 21 Nov 2026", "12:30 KO", "Millwall",
                 "Queens Park Rangers", "Sat 21 Nov 2026", "15:00 KO",
                 "Stoke City", "Birmingham City", "League Table"]
        self.assertEqual(discover("ENG2", lines, asof),
                         [("Millwall", "Queens Park Rangers"),
                          ("Stoke City", "Birmingham City")])

    def test_efl_lookalike_not_competition_proven(self):
        asof = datetime(2026, 11, 18, tzinfo=timezone.utc)
        lines = ["EFL League One", "Sync Fixtures", "All Fixtures",
                 "Sat 21 Nov 2026", "12:30 KO", "Millwall", "Queens Park Rangers"]
        self.assertEqual(discover("ENG2", lines, asof), [])

    def test_portugal_long_day_card_was_truncated(self):
        asof = datetime(2026, 11, 24, tzinfo=timezone.utc)
        lines = ["Dom. 29 Nov", "J12"] + ["UI filler"] * 24 + [
            "FCP", "20H30", "SCP", "Seg. 30 Nov", "J12"]
        self.assertEqual(discover("POR1", lines, asof), [("FC Porto", "Sporting CP")])

    def test_portugal_never_borrow_from_next_day(self):
        asof = datetime(2026, 11, 24, tzinfo=timezone.utc)
        lines = ["Dom. 29 Nov", "FCP", "Seg. 30 Nov", "20H30", "SCP"]
        self.assertEqual(discover("POR1", lines, asof), [])

if __name__ == "__main__":
    unittest.main()
