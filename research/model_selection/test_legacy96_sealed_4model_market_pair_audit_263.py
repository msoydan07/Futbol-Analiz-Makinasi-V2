"""Deterministic tests, not another full pilot rerun."""
import math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from legacy96_sealed_4model_market_pair_audit_263 import (
    verified_archive,sealed_records,mark,probs,outcome,key,
    COHORT_PATHS,AuditError,COHORT_TOTAL
)

class LockedPilotMarketAuditTests(unittest.TestCase):
    def test_exact_99_archive_join_scope_not_fabricated_outcomes(self):
        x=verified_archive()
        self.assertEqual(len(x),99)
        self.assertEqual(sum(k[1]=="2026-11-08" for k in x),42)

    def test_seals_are_actually_SHA_and_pre_kickoff_verified_by_existing_gate(self):
        x=sealed_records()
        self.assertEqual(len(x),COHORT_TOTAL)
        self.assertEqual({k:sum(r["cohort"]==k for r in x)
                          for k in COHORT_PATHS},
                         {k:v[1] for k,v in COHORT_PATHS.items()})
        self.assertTrue(all(r["forecast_sha256"] and r["path"] for r in x))

    def test_three_way_ms_brier_is_not_binary_brier(self):
        p={"H":.55,"D":.25,"A":.20}
        scored=mark(p,"D","MS")
        self.assertAlmostEqual(scored["brier"],.55**2+(.25-1)**2+.2**2)
        self.assertEqual(scored["top1_correct"],0)
        self.assertAlmostEqual(scored["logloss"],-math.log(.25))

    def test_binary_market_brier_and_labels(self):
        self.assertAlmostEqual(mark(.6,1,"KG")["brier"],.16)
        self.assertAlmostEqual(mark(.6,0,"OVER25")["brier"],.36)
        self.assertEqual(mark(.6,1,"KG")["top1_correct"],1)
        self.assertEqual(mark(.6,0,"KG")["top1_correct"],0)

    def test_correct_actual_market_outcomes_for_h_a_draw(self):
        self.assertEqual(outcome(2,1),{"MS":"H","KG":1,"OVER25":1})
        self.assertEqual(outcome(1,2),{"MS":"A","KG":1,"OVER25":1})
        self.assertEqual(outcome(0,0),{"MS":"D","KG":0,"OVER25":0})

    def test_broken_probability_is_never_silently_normalized(self):
        sample={"status":"AVAILABLE","goals":{"markets":{
            "1X2":{"H":.6,"D":.3,"A":.3},"BTTS_YES":.7,"OVER_2.5":.6}}}
        with self.assertRaisesRegex(AuditError,"INVALID_MS_NORMALIZATION"):
            probs(sample)
        sample["goals"]["markets"]["1X2"]={"H":.4,"D":.3,"A":.3}
        sample["goals"]["markets"]["BTTS_YES"]=-.02
        with self.assertRaisesRegex(AuditError,"UNSAFE_MODEL_PROBABILITY"):
            probs(sample)

    def test_match_join_requires_same_league_day_both_internal_ids(self):
        self.assertNotEqual(key("TUR1","2026-11-08","H","A"),
                            key("TUR1","2026-11-07","H","A"))
        self.assertNotEqual(key("TUR1","2026-11-08","H","A"),
                            key("TUR1","2026-11-08","A","H"))
        self.assertNotEqual(key("TUR1","2026-11-08","H","A"),
                            key("ENG1","2026-11-08","H","A"))

if __name__=="__main__":unittest.main()
