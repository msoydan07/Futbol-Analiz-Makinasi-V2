"""Offline fixtures and score evidence guardrail tests; no provider download."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from staged_candidate_99_joint_audit import evidence_99,validate_source_identity,AuditStop
ROOT=Path(__file__).resolve().parents[2]
class Tests(unittest.TestCase):
    def test_existing_published_99_cover_exactly_three_tiers(self):
        x=evidence_99(ROOT)
        self.assertEqual(len(x),99)
        from collections import Counter
        c=Counter(k[0] for k in x)
        self.assertEqual(dict(c),{"BEL1":10,"ENG1":10,"ENG2":15,"ESP1":10,
        "FRA1":9,"GER1":9,"ITA1":10,"NED1":9,"POR1":8,"TUR1":9})
    def test_wrong_source_url_halted(self):
        r=dict(league="ENG1",season="2026-2027",
          source_url="https://random-provider.invalid/E0.csv",source_row="22",
          home_goals="1",away_goals="0",result="H")
        with self.assertRaisesRegex(AuditStop,"SOURCE_URL"):
            validate_source_identity(r)
    def test_incorrect_score_result_halted(self):
        r=dict(league="ENG1",season="2026-2027",
          source_url="https://www.football-data.co.uk/mmz4281/2627/E0.csv",
          source_row="22",home_goals="1",away_goals="0",result="A")
        with self.assertRaisesRegex(AuditStop,"SCORE"):
            validate_source_identity(r)
if __name__=="__main__":unittest.main()
