"""Regression coverage: 99 score-only archive does not alter M4 or prior 4518 rows."""
import copy
import json
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_completed99_results_archive import build, load_archive, ROOT, Rejected

class Completed99Tests(unittest.TestCase):
    def source(self):
        return load_archive(ROOT)
    def test_real_4518_plus99_scores_only_archival_acceptance(self):
        output=build()
        self.assertEqual(output["status"],"99_COMPLETED_SCORES_PERMANENTLY_ARCHIVED_RESULTS_ONLY")
        self.assertEqual(output["new_result_records"],99)
        self.assertEqual(output["logical_total_result_records"],4617)
        self.assertEqual(output["old_ENG2_changed_stage_rows_ignored"],9)
        self.assertEqual(output["new_99_advanced_fields_admitted"],0)
        self.assertFalse(output["base_accepted_csv_modified"])
        self.assertFalse(output["production_M4_modified_or_retrained"])
        self.assertEqual(output["score_source_distribution"]["PUBLIC_SECONDARY_SCORE_WITH_PARTIAL_OFFICIAL_FIXTURE"],43)
    def test_old_archive_hash_mismatch_rejected(self):
        d=self.source()
        d["base_accepted_history_sha256"]="0"*64
        with self.assertRaisesRegex(Rejected,"ARCHIVE_BASE_HASH_CHANGED"):build(archive_override=d)
    def test_duplicate_result_not_counted_twice(self):
        d=self.source()
        d["records"][1]=copy.deepcopy(d["records"][0])
        with self.assertRaisesRegex(Rejected,"DUPLICATE_RESULT_ENTRY"):build(archive_override=d)
    def test_wrong_goal_rejected(self):
        d=self.source();d["records"][0]["home_goals"]=17
        d["records"][0]["result"]="H"
        with self.assertRaisesRegex(Rejected,"CANDIDATE_SCORE_VS_ARCHIVE_CONFLICT"):build(archive_override=d)
    def test_unsourced_result_rejected(self):
        d=self.source();d["records"][0]["score_source_url"]="https://"
        with self.assertRaisesRegex(Rejected,"NO_GROUNDED_PUBLIC_SOURCE"):build(archive_override=d)
    def test_fabricated_official_identity_label_rejected(self):
        d=self.source();d["record_policy"]["official_fixture_id_independently_attested"]=True
        with self.assertRaisesRegex(Rejected,"MISLEADING_OFFICIAL_ID_ATTESTATION"):build(archive_override=d)
    def test_cannot_silently_enable_M4_retraining(self):
        d=self.source();d["record_policy"]["promoted_into_M4_training"]=True
        with self.assertRaisesRegex(Rejected,"MODEL_PROMOTION_NOT_AUTHORIZED"):build(archive_override=d)
if __name__=="__main__":unittest.main()
