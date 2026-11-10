"""Fail-close uncertainty and sample-size diagnostics, no external source requests."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from opponent_group_uncertainty_263 import wilson,interval_for,build,EvidenceError
ROOT=Path(__file__).resolve().parents[2]

class TestUncertainty(unittest.TestCase):
    def test_eight_of_ten_does_not_mean_true_80_percent(self):
        lower,upper=wilson(8,10)
        self.assertLess(lower,.51)
        self.assertGreater(upper,.94)
    def test_seven_of_eleven_wide(self):
        lower,upper=wilson(7,11)
        self.assertLess(lower,.37)
        self.assertGreater(upper,.83)
    def test_empty_does_not_become_zero_probability(self):
        a=interval_for({"n":0,"btts_frequency":None},"btts_frequency")
        self.assertIsNone(a["empirical_rate"])
        self.assertIsNone(a["95pct_Wilson_independent_reference_only"])
    def test_inconsistent_frequency_refused(self):
        with self.assertRaisesRegex(EvidenceError,"INTEGER_COMPATIBLE"):
            interval_for({"n":10,"btts_frequency":.777},"btts_frequency")
    def test_real_archive_stays_research_only(self):
        x=build(ROOT)
        self.assertEqual(x["cell_coverage"]["n_under_5"],609)
        self.assertEqual(x["cell_coverage"]["n_total"],1280)
        self.assertTrue(x["besiktas_home_only_reference"]["intervals_overlap"])
        self.assertEqual(x["besiktas_home_only_reference"]["team_50_to_150_ahead_2_5_Over_k"],8)
        self.assertEqual(x["decision"],"DO_NOT_PROMOTE_OPPONENT_STRENGTH_STYLE_COEFFICIENT")

if __name__=="__main__":unittest.main()
