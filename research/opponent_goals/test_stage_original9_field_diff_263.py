"""Source hash guard, stable 99 identity and staged old row mapping."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from staged_candidate_99_joint_audit import evidence_99
from stage_original9_field_diff_263 import CRITICAL
class Tests(unittest.TestCase):
    def test_original_identity_and_score_are_critical(self):
        self.assertTrue({"home_goals","away_goals","match_date","source_row","home_id"}<=CRITICAL)
    def test_score_99_keys_remain_unique(self):
        d=evidence_99(Path(__file__).resolve().parents[2])
        self.assertEqual(len(d),99)
        self.assertEqual(len(set(d)),99)
if __name__=="__main__":unittest.main()
