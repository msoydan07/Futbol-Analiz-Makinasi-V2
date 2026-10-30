"""Regression tests for repeated Belgian league pairings and true duplicates."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import import_real_fixtures
from identity import Registry

class FixtureImportTests(unittest.TestCase):
    def test_repeated_pair_distinct_dates_and_reschedule_flag(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = Registry(root / "team_registry.json")
            home = registry.register_team("belgian-home", "Dender")
            away = registry.register_team("belgian-away", "Cercle Brugge")
            registry.save()
            rows = [
                {"season": "2025-2026", "league": "BEL1", "source_row": str(i + 2),
                 "date": date, "home": "Dender", "away": "Cercle Brugge",
                 "candidate_key": "observed", "status": "CANDIDATE_ONLY"}
                for i, date in enumerate(["10/08/2025", "15/03/2026"])
            ]
            with (root / "fixture_candidates.csv").open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
            with (root / "fixture_source_audit.csv").open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["season", "league", "status"])
                writer.writeheader()
                writer.writerows({"season": "2025-2026", "league": f"L{i}", "status": "OK"} for i in range(20))
            with patch.object(import_real_fixtures, "ROOT", root):
                import_real_fixtures.main()
            result = Registry(root / "match_registry.json")
            self.assertEqual(len(result.data["fixtures"]), 2)
            self.assertEqual({f["match_date"] for f in result.data["fixtures"].values()},
                             {"2025-08-10", "2026-03-15"})
            self.assertTrue(all(f["reschedule_requires_reconciliation"]
                                for f in result.data["fixtures"].values()))
            self.assertEqual(json.loads((root / "fixture_import_report.json").read_text())["error_count"], 0)

    def test_duplicate_same_date_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = Registry(root / "team_registry.json")
            registry.register_team("belgian-home", "Dender")
            registry.register_team("belgian-away", "Cercle Brugge")
            registry.save()
            rows = [{"season": "2025-2026", "league": "BEL1", "source_row": str(i),
                     "date": "10/08/2025", "home": "Dender", "away": "Cercle Brugge",
                     "candidate_key": "observed", "status": "CANDIDATE_ONLY"}
                    for i in (2, 3)]
            with (root / "fixture_candidates.csv").open("w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
            with (root / "fixture_source_audit.csv").open("w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["season", "league", "status"])
                writer.writeheader()
                writer.writerows({"season": "2025-2026", "league": f"L{i}", "status": "OK"} for i in range(20))
            with patch.object(import_real_fixtures, "ROOT", root):
                with self.assertRaises(SystemExit):
                    import_real_fixtures.main()
            report = json.loads((root / "fixture_import_report.json").read_text())
            self.assertEqual(report["error_types"]["AMBIGUOUS_SAME_DATE"], 2)
            self.assertFalse((root / "match_registry.json").exists())

if __name__ == "__main__":
    unittest.main()
