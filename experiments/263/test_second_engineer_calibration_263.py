"""Second engineer probability checks: deliberately adversarial synthetic QA."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from second_engineer_calibration_263 import coherent,band,wilson,summary,audit,EvidenceBlocked
ROOT=Path(__file__).resolve().parents[2]
def markets():
    return {"1X2":{"H":.7,"D":.2,"A":.1},
      "BTTS_YES":.6,"BTTS_NO":.4,
      "OVER_1.5":.85,"UNDER_1.5":.15,
      "OVER_2.5":.6,"UNDER_2.5":.4,
      "OVER_3.5":.3,"UNDER_3.5":.7}

class SkepticTests(unittest.TestCase):
    def test_valid_joint_events(self):
        self.assertAlmostEqual(coherent(markets())["H"],.7)
    def test_bad_one_x_two_bets_refused(self):
        a=markets();a["1X2"]["H"]=.8
        with self.assertRaisesRegex(EvidenceBlocked,"SUM"):coherent(a)
    def test_bad_goal_tail_refused(self):
        a=markets();a["OVER_2.5"]=.91;a["UNDER_2.5"]=.09
        with self.assertRaisesRegex(EvidenceBlocked,"MONOTONICITY"):coherent(a)
    def test_btts_above_two_goals_impossible(self):
        a=markets();a["BTTS_YES"]=.9;a["BTTS_NO"]=.1
        with self.assertRaisesRegex(EvidenceBlocked,"BOTH_SCORE"):coherent(a)
    def test_bad_complement_refused(self):
        a=markets();a["UNDER_1.5"]=.55
        with self.assertRaisesRegex(EvidenceBlocked,"COMPLEMENT"):coherent(a)
    def test_nonfinite_and_bool_refused(self):
        for v in (float("nan"),float("inf"),True,-.1,1.1):
            a=markets();a["1X2"]["H"]=v
            with self.assertRaises(EvidenceBlocked):coherent(a)
    def test_70_percent_7_of_10_not_certification(self):
        rows=[{"p":.7,"y":int(i<7),"match_day":"2026-11-08"} for i in range(10)]
        b=band(rows)
        self.assertEqual(b["sample_n"],10)
        self.assertEqual(b["observed_rate"],.7)
        self.assertEqual(b["distinct_utc_match_days"],1)
        self.assertEqual(b["evidence_status"],"DESCRIPTIVE_ONLY_TOO_FEW_OR_SAME_DAY")
        self.assertLess(b["95pct_wilson_independent_binomial_reference_only"][0],.5)
    def test_no_samples_means_null_not_zero(self):
        self.assertIsNone(band([])["observed_rate"])
        self.assertIsNone(summary([])["brier"])
    def test_boundary_and_minimum_different_days(self):
        rows=[{"p":.7,"y":int(i<70),"match_day":f"2026-11-{8+i%5:02d}"} for i in range(100)]
        self.assertEqual(band(rows)["evidence_status"],
           "SAMPLE_ELIGIBLE_FOR_INDEPENDENT_CONFIRMATION_NOT_PROOF")
        self.assertEqual(band([{"p":.75,"y":1,"match_day":"2026-11-08"}])["sample_n"],0)
    def test_impossible_wilson(self):
        with self.assertRaises(EvidenceBlocked):wilson(9,8)
    def test_existing_seal_40_vs_39_vs_postponed_no_promotion(self):
        report=audit(ROOT)
        self.assertEqual((report["cohort"]["seals"],report["cohort"]["results_web_reviewed"],
                    report["cohort"]["postponed_excluded"]),(40,39,1))
        self.assertEqual(report["by_evidence_class"]["PRIMARY_ONLY"]["M4"]["MS_n"],35)
        self.assertFalse(report["independent_70_percent_acceptance"])
        self.assertEqual(report["by_evidence_class"]["ALL_WEB_REVIEW"]["M4"]["MS_n"],39)

if __name__=="__main__":unittest.main()
