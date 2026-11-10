"""Legacy 6 Nov four sealed outcomes: strict identity, date, cohort, and safety."""
import copy
import json
import unittest
from pathlib import Path
from research.opponent_goals.nov6_7_8_separate_date_audit_263 import (
    ROOT, EVIDENCE, Blocked, evaluate
)

class TestNov6AndSeparateDates(unittest.TestCase):
    def data(self):
        return json.loads((Path(ROOT)/EVIDENCE).read_text(encoding="utf-8"))

    def test_all_four_seals_and_all_three_date_blocks(self):
        x=evaluate()
        self.assertEqual(x["nov6"]["n"],4)
        self.assertEqual(x["nov7"]["n"],3)
        self.assertEqual(x["nov8_reference_only"]["n"],39)
        self.assertEqual(x["research_event_count_UNPOOLED"],46)
        self.assertEqual(x["distinct_match_dates"],3)
        self.assertTrue(x["all_cohorts_separate"])
        self.assertEqual(x["nov6"]["markets"]["BTTS_YES"]["observed_rate"],.75)
        self.assertEqual(x["nov6"]["markets"]["OVER_2.5"]["observed_rate"],.5)
        self.assertFalse(x["candidate_promoted"])
        self.assertFalse(x["production_calibration_changed"])
        self.assertEqual(x["official_results_new100_promoted"],0)
        self.assertEqual(len(set(f["forecast_sha256"] for f in x["nov6"]["matches"])),4)

    def test_duplicate_identity_blocked(self):
        d=self.data()
        d["observations"][1]=copy.deepcopy(d["observations"][0])
        with self.assertRaisesRegex(Blocked,"INVALID_OR_DUPLICATE_LEGACY_SEAL"):
            evaluate(evidence_override=d)

    def test_wrong_identity_index_blocked(self):
        d=self.data()
        d["observations"][0]["away"]="besiktas"
        with self.assertRaisesRegex(Blocked,"FORECAST_TEAM_ID_OR_OFFICIAL_FIXTURE_MISMATCH"):
            evaluate(evidence_override=d)

    def test_wrong_original_sha_blocked(self):
        d=self.data()
        d["observations"][0]["seal_sha256"]="0"*64
        with self.assertRaisesRegex(Blocked,"FORECAST_SHA_CHANGED_OR_UNMATCHED"):
            evaluate(evidence_override=d)

    def test_bad_score_and_false_provenance_blocked(self):
        d=self.data();d["observations"][0]["score"]=[-1,2]
        with self.assertRaisesRegex(Blocked,"INVALID_FULL_TIME_SCORE"):
            evaluate(evidence_override=d)
        d=self.data();d["ci_independently_rechecks_sources"]=True
        with self.assertRaisesRegex(Blocked,"INVALID_LEGACY_QUAD4_RESEARCH_CONTRACT"):
            evaluate(evidence_override=d)

    def test_untrusted_source_url_blocked(self):
        d=self.data()
        d["observations"][0]["source_url"]="https://tff.org.evil.example/fixture"
        with self.assertRaisesRegex(Blocked,"OUTCOME_PRIMARY_SOURCE_MISMATCH"):
            evaluate(evidence_override=d)

if __name__=="__main__":
    unittest.main()
