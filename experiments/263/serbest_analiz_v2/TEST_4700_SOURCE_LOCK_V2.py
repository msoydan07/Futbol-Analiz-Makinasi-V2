"""Read-only integration tests of original source + separately accepted 4700."""
from pathlib import Path
import tempfile, unittest
from GUNLUK_SERBEST_ANALIZ_KAPISI_V2 import (
    GateError,validate_source_locks,latest_result_age)
ROOT=Path(__file__).resolve().parents[3]
LEGACY=ROOT/'data/results_only_263/2026-11-10_completed_4617_scores_only.csv'
FRESH=ROOT/'data/research_263/2026-11-23_4700_two_source_research.csv'

class LockResearchTests(unittest.TestCase):
    def test_old_frozen_4617_still_works(self):
        v=validate_source_locks(ROOT,LEGACY)
        self.assertEqual(v['research_rows'],4617)
    def test_two_source_4700_sha_provenance_and_83_ledger(self):
        v=validate_source_locks(ROOT,FRESH)
        self.assertEqual(v['research_rows'],4700)
        self.assertEqual(v['score_evidence'],'83_TWO_PUBLIC_SECONDARY_SOURCES_NOT_FEDERATIONS')
        age,latest=latest_result_age(FRESH,'GER1','2026-11-27')
        self.assertEqual((age,latest),(5,'2026-11-22'))
    def test_same_bytes_outside_locked_source_path_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            cp=Path(d)/'spoof.csv'
            cp.write_bytes(FRESH.read_bytes())
            with self.assertRaisesRegex(GateError,'WHITELIST'):
                validate_source_locks(ROOT,cp)

if __name__=='__main__':unittest.main(verbosity=2)
