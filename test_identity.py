import tempfile
import unittest
from pathlib import Path
from identity import Registry, LEAGUES, SEASONS


class IdentityTests(unittest.TestCase):
    def test_league_season_scope(self):
        self.assertEqual(len(LEAGUES), 10)
        self.assertEqual(len(SEASONS), 2)

    def test_persistent_teams_aliases_and_collision(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "registry.json"
            r = Registry(path)
            a = r.register_team("galatasaray-sk", "Galatasaray", ["Galatasaray SK"])
            b = r.register_team("konyaspor", "Konyaspor")
            self.assertNotEqual(a, b)
            self.assertEqual(r.resolve_team("GALATASARAY  SK"), a)
            with self.assertRaises(ValueError):
                r.register_team("other-club", "Galatasaray")
            with self.assertRaises(KeyError):
                r.resolve_team("Unknown FC")
            r.save()
            self.assertEqual(Registry(path).resolve_team("Galatasaray SK"), a)

    def test_fixture_stability_and_conflicts(self):
        with tempfile.TemporaryDirectory() as folder:
            r = Registry(Path(folder) / "registry.json")
            home = r.register_team("galatasaray-sk", "Galatasaray")
            away = r.register_team("konyaspor", "Konyaspor")
            first = r.register_fixture("TUR1", "2026-2027", home, away, "league", "fixture-17", "2026-11-01T20:00+03:00")
            again = r.register_fixture("TUR1", "2026-2027", home, away, "league", "fixture-17", "2026-11-08T20:00+03:00")
            self.assertEqual(first, again)
            self.assertEqual(len(r.data["fixtures"]), 1)
            with self.assertRaises(ValueError):
                r.register_fixture("TUR1", "2026-2027", away, home, "league", "fixture-17")
            with self.assertRaises(ValueError):
                r.register_fixture("TUR1", "2026-2027", home, away, "league", "")
            with self.assertRaises(ValueError):
                r.register_fixture("TUR1", "2024-2025", home, away, "league", "fixture-18")


if __name__ == "__main__":
    unittest.main()
