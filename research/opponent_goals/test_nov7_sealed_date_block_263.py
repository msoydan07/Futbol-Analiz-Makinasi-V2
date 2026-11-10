"""Checks original 7 Nov seal integrity, strict outcome gate and no false certification."""
import copy
import json
import unittest
from pathlib import Path
try:
    from research.opponent_goals.nov7_sealed_date_block_263 import (
        ROOT, EVIDENCE, Blocked, evaluate
    )
except ModuleNotFoundError:
    from nov7_sealed_date_block_263 import ROOT, EVIDENCE, Blocked, evaluate

class TestNov7PrimaryDateBlock(unittest.TestCase):
    def source(self):
        return json.loads((Path(ROOT) / EVIDENCE).read_text(encoding="utf-8"))

    def test_three_original_sha_forecasts_and_prior_day_separate(self):
        report = evaluate()
        self.assertEqual(report["distinct_match_days"], 2)
        self.assertEqual(report["nov7"]["n"], 3)
        self.assertEqual(report["nov8_reference_only"]["n"], 39)
        self.assertFalse(report["nov8_reference_only"]["scored_again"])
        self.assertEqual(report["new100_accepted_results_from_nov7"], 0)
        self.assertEqual(report["decision"], "HOLD_UNTIL_MULTIPLE_NEW_INDEPENDENT_DATES")
        self.assertEqual(report["nov7"]["markets"]["BTTS_YES"]["observed_rate"], 0)
        self.assertAlmostEqual(report["nov7"]["markets"]["BTTS_YES"]["mean_forecast"], .44438, delta=.0002)
        self.assertAlmostEqual(report["nov7"]["markets"]["OVER_2.5"]["mean_forecast"], .45207, delta=.0002)
        self.assertEqual(report["nov7"]["markets"]["OVER_2.5"]["observed_rate"], .333333)
        self.assertFalse(report["candidate_promoted"])
        self.assertFalse(report["production_probability_recalibration"])
        self.assertEqual(len({m["forecast_sha256"] for m in report["nov7"]["matches"]}), 3)

    def test_invalid_score_blocked(self):
        d = self.source()
        d["observations"][0]["home_goals"] = 33
        with self.assertRaisesRegex(Blocked, "UNSAFE_FULL_TIME_SCORE"):
            evaluate(evidence_override=d)

    def test_source_domain_not_verified_blocked(self):
        d = self.source()
        d["observations"][0]["source_url"] = "https://example.com/results"
        with self.assertRaisesRegex(Blocked, "INVALID_OR_NONPRIMARY_RESULT_SOURCE"):
            evaluate(evidence_override=d)

    def test_duplicate_result_never_double_counts(self):
        d = self.source()
        d["observations"][1] = copy.deepcopy(d["observations"][0])
        with self.assertRaisesRegex(Blocked, "DUPLICATE_OR_UNMATCHED_OUTCOME"):
            evaluate(evidence_override=d)

    def test_wrong_identity_cannot_steal_a_seal(self):
        d = self.source()
        d["observations"][0]["away"] = "Another Club"
        with self.assertRaisesRegex(Blocked, "DUPLICATE_OR_UNMATCHED_OUTCOME"):
            evaluate(evidence_override=d)

    def test_acceptance3_must_not_be_mislabeled_new100(self):
        d = self.source()
        d["cohort"] = "new100"
        with self.assertRaisesRegex(Blocked, "EVIDENCE_CONTRACT_NOT_RESEARCH_ONLY"):
            evaluate(evidence_override=d)

    def test_website_check_not_falsely_claimed_by_ci(self):
        d = self.source()
        d["source_checks_in_github_ci"] = True
        with self.assertRaisesRegex(Blocked, "EVIDENCE_CONTRACT_NOT_RESEARCH_ONLY"):
            evaluate(evidence_override=d)

if __name__ == "__main__":
    unittest.main()
