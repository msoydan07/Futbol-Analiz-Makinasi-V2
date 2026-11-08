"""Offline QA tests for the new *research* archive importer.

Run: python -m unittest discover -s research/model_challenge -p 'test_*.py'
"""
import tempfile
import unittest
from datetime import date
from pathlib import Path

from ingest_openfootball import Reject, ingest, normalize_one


class IngestTests(unittest.TestCase):
    def base(self):
        return {"name": "Sample", "matches": [
            {"date": "2025-08-01", "team1": "Team A", "team2": "Team B",
             "score": {"ft": [2, 1]}},
            {"date": "2025-08-02", "team1": "Team C", "team2": "Team D",
             "score": {}},
            {"date": "2026-12-01", "team1": "Team A", "team2": "Team C",
             "score": {"ft": [4, 2]}}]}

    def test_pre_cutoff_only_and_no_unplayed(self):
        rows, missing = normalize_one(self.base(), "ENG1", "2025-26",
                                      "source", "hash", cutoff=date(2026, 11, 9))
        self.assertEqual(len(rows), 1)
        self.assertEqual(missing, 1)
        self.assertEqual(rows[0]["home_goals"], 2)

    def test_duplicates_fail_closed(self):
        data = self.base()
        data["matches"].append(data["matches"][0].copy())
        with self.assertRaises(Reject):
            normalize_one(data, "ENG1", "2025-26", "source", "hash",
                          cutoff=date(2026, 11, 9))

    def test_self_match_fail_closed(self):
        data = self.base()
        data["matches"][0]["team2"] = "Team A"
        with self.assertRaises(Reject):
            normalize_one(data, "ENG1", "2025-26", "source", "hash",
                          cutoff=date(2026, 11, 9))

    def test_bad_score_fail_closed(self):
        data = self.base()
        data["matches"][0]["score"]["ft"] = [2, -1]
        with self.assertRaises(Reject):
            normalize_one(data, "ENG1", "2025-26", "source", "hash",
                          cutoff=date(2026, 11, 9))

    def test_coverage_with_missing_sources(self):
        def fake_fetch(url):
            if url.endswith("/en.1.json"):
                return self.base(), "a" * 64
            return None, None
        with tempfile.TemporaryDirectory() as tmp:
            report = ingest(out=tmp, seasons=("2025-26",),
                            cutoff=date(2026, 11, 9), fetch=fake_fetch)
            self.assertEqual(report["matches"], 1)
            self.assertEqual(report["league_count"], 1)
            self.assertEqual(len(report["coverage"]), 20)
            self.assertTrue(Path(tmp, "coverage.json").exists())
            self.assertTrue(Path(tmp, "normalized_matches.csv").exists())


if __name__ == "__main__":
    unittest.main()
