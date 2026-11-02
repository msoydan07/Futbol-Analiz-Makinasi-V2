"""Targeted NEW queue tests; no prior M4 or frozen model tests rerun."""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

from run_quad_requested_batch import read_request, record_batch, prior_keys

NOW = datetime(2026, 11, 2, 7, 0, tzinfo=timezone.utc)


class QuadRequestIntake(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.filename = "experiments/263/quad_requests/fixture_001.json"
        dest = self.root / self.filename
        dest.parent.mkdir(parents=True)
        self.match = {"league": "TUR1", "home": "Besiktas", "away": "Genclerbirligi"}
        dest.write_text(json.dumps({"schema": "quad_named_match_batch_request_v1",
                                    "matches": [self.match]}), encoding="utf-8")

    def test_read_valid_named_fixture_without_user_supplied_date_or_verification(self):
        matches, digest = read_request(self.filename, self.root)
        self.assertEqual(matches, [self.match])
        self.assertEqual(len(digest), 64)

    def test_bad_request_and_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside_quad_request_queue"):
            read_request("../outside.json", self.root)
        file = self.root / self.filename
        file.write_text(json.dumps({"schema": "quad_named_match_batch_request_v1",
                                    "matches": [self.match, self.match]}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate_or_same_team"):
            read_request(self.filename, self.root)

    def test_missing_accepted_source_blocks_before_live_lookup_and_leaves_audit(self):
        lookup = Mock(side_effect=AssertionError("should not make network request"))
        audit_path = self.root / "audit" / "blocked.json"
        report = record_batch([self.filename], root=self.root,
                              history=self.root / "missing.csv",
                              baseline=self.root / "frozen.csv",
                              acceptance=self.root / "acceptance.json",
                              lock=self.root / "m4_lock.json",
                              records_dir=self.root / "records", report_path=audit_path,
                              lookup=lookup, now=NOW)
        self.assertEqual(report["statuses"]["REGISTERED_FOUR_MODELS_EXPERIMENTAL"], 0)
        self.assertEqual(report["outcomes"][0]["reason"], "UPDATED_SOURCE_NOT_HUMAN_ACCEPTED_YET")
        lookup.assert_not_called()
        self.assertEqual(json.loads(audit_path.read_text())["schema"],
                         "quad_named_match_batch_report_v1")

    def test_corrupted_prior_record_rejected(self):
        folder = self.root / "records" / "2026-11-08"
        folder.mkdir(parents=True)
        (folder / "corrupt.json").write_text('{"schema":"quad_forward_263_v1"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "tampered_existing_pilot_record"):
            prior_keys(self.root / "records")


if __name__ == "__main__":
    unittest.main()
