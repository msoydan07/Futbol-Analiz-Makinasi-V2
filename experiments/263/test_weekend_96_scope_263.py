"""Synthetic checks for the fixed 96-candidate Nov 2026 cohort."""
import unittest
from unittest.mock import patch
from forward_quad import PILOT_GOAL
from evaluate_quad import MODELS, report


class WeekendScopeTests(unittest.TestCase):
    def _eval(self, n):
        rows = []
        for i in range(n):
            rows.append({
                "date": ["2026-11-06","2026-11-07","2026-11-08"][i % 3],
                "league": "TUR1", "sha": f"synthetic{i}",
                "scores": {m: {"logloss": .9, "brier": .5, "is_correct": 1} for m in MODELS},
                "markets": {m: {
                    "BTTS": {"logloss": .7, "brier": .25, "p": .5, "y": 1},
                    "OVER_2.5": {"logloss": .7, "brier": .25, "p": .5, "y": 0},
                } for m in MODELS},
            })
        meta = {"registered": n, "finished_matched": n,
                "coverage": {m:n for m in MODELS}, "unresolved_fixtures": 0}
        with patch("evaluate_quad.collect", return_value=(rows,meta)):
            return report("synthetic", "synthetic")

    def test_limit_is_96(self):
        self.assertEqual(PILOT_GOAL,96)

    def test_96_reports_weekend_not_promotion(self):
        x = self._eval(96)
        self.assertEqual(x["milestone"],"WEEKEND_96_DESCRIPTIVE_REPORT")
        self.assertEqual(x["four_way_common"]["n"],96)
        for key in ("B_versus_M4","C2_versus_M4","C3_versus_M4"):
            self.assertIsNone(x["paired"][key]["date_block_bootstrap_95"])

    def test_25_is_operational(self):
        self.assertEqual(self._eval(25)["milestone"],"OPERATIONAL_ONLY_AT_25")

    def test_incomplete_coverage_not_marked_as_complete(self):
        self.assertNotEqual(self._eval(80)["milestone"],"WEEKEND_96_DESCRIPTIVE_REPORT")

if __name__=="__main__":unittest.main()
