"""Synthetic-only safety checks; no provider call and no model test."""
import copy
import json
import unittest
from build_xg_public_summary_safe import sanitize

LEAGUES = ("ENG1", "ESP1", "FRA1", "GER1", "ITA1")
SEASONS = ("2025-2026", "2026-2027")

def sample():
    coverage = [{"league": l, "season": s, "matched": 4,
                 "historical": 5, "secret_match_url": "DO_NOT_EXPORT"}
                for l in LEAGUES for s in SEASONS]
    audit = {"source_rows": 43, "matched_unique": 40,
             "historical_eligible": 50, "coverage_by_league_season": coverage,
             "status_counts": [{"status": "MATCHED", "count": 40},
                               {"status": "UNMATCHED", "count": 3}],
             "private_values": [3.4, 1.2]}
    history = {"verified_xg_rows": 40, "source_rows": 43, "audit_rows": 43,
               "historical_rows": 100, "prediction_engine_modified": False,
               "private_rows": [{"fixture_id": "SECRET"}]}
    return audit, history

class SafeExportTests(unittest.TestCase):
    def test_no_raw_fields(self):
        a, b = sample()
        result = sanitize(a, b)
        body = json.dumps(result)
        self.assertNotIn("DO_NOT_EXPORT", body)
        self.assertNotIn("SECRET", body)
        self.assertNotIn("private_values", body)
        self.assertEqual(result["counts"]["verified_matches"], 40)
        self.assertFalse(result["asof_provider_vintage_proven"])

    def test_bad_row_total_fails(self):
        a, b = sample()
        b["verified_xg_rows"] = 41
        with self.assertRaisesRegex(ValueError, "disagree"):
            sanitize(a, b)

    def test_duplicate_league_fails(self):
        a, b = sample()
        a["coverage_by_league_season"][1] = copy.deepcopy(a["coverage_by_league_season"][0])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            sanitize(a, b)

    def test_unapproved_league_fails(self):
        a, b = sample()
        a["coverage_by_league_season"][0]["league"] = "TUR1"
        with self.assertRaisesRegex(ValueError, "unexpected"):
            sanitize(a, b)

    def test_noninteger_count_fails(self):
        a, b = sample()
        a["matched_unique"] = True
        with self.assertRaisesRegex(ValueError, "count"):
            sanitize(a, b)

    def test_model_mutation_fails(self):
        a, b = sample()
        b["prediction_engine_modified"] = True
        with self.assertRaisesRegex(ValueError, "model state"):
            sanitize(a, b)

    def test_status_total_mismatch_fails(self):
        a, b = sample()
        a["status_counts"][1]["count"] = 1
        with self.assertRaisesRegex(ValueError, "status count"):
            sanitize(a, b)

if __name__ == "__main__":
    unittest.main()
