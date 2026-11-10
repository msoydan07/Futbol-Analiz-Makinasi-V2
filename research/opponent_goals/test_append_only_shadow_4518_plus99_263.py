"""Fail-close source and fixture evidence gating; no new downloads."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from staged_candidate_99_joint_audit import evidence_99
from append_only_shadow_4518_plus99_263 import make
ROOT=Path(__file__).resolve().parents[2]
class Tests(unittest.TestCase):
    def test_research_has_99_unique_match_keys(self):
        m=evidence_99(ROOT)
        self.assertEqual(len(m),99)
    def test_source_locked_script_is_callable(self):
        self.assertTrue(callable(make))
if __name__=="__main__":unittest.main()
