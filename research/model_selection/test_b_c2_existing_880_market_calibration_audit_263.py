"""Math/integrity regression, no repeat of 880 models or old 96 SHA pilots."""
from __future__ import annotations
import math,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from b_c2_existing_880_market_calibration_audit_263 import (
 AuditBlocked,MAPPINGS,metrics,per_event,score_market,pair_metric,
 binary_shadow_calibration,day_ci,MODELS,FIELDS
)
sys.path.insert(0,str(ROOT/"experiments/263"))
from chrono_goal_stage2_263 import calibration

def row(date="2026-10-02",models=("B","C3","M4")):
    probs={"MS1":.5,"MSX":.25,"MS2":.25,
           "BTTS_YES":.6,"BTTS_NO":.4,
           "OVER_2.5":.3,"UNDER_2.5":.7}
    base={"MS1":.4,"MSX":.3,"MS2":.3,
          "BTTS_YES":.5,"BTTS_NO":.5,
          "OVER_2.5":.5,"UNDER_2.5":.5}
    y={"MS1":0,"MSX":1,"MS2":0,
       "BTTS_YES":1,"BTTS_NO":0,
       "OVER_2.5":0,"UNDER_2.5":1}
    return {"date":date,"league":"TUR1","obs":y,"base":base,
            "p":{m:dict(probs) for m in models}}
class AuditTests(unittest.TestCase):
    def test_ms_three_way_categorical_brier_logloss_and_top1(self):
        r=row()
        got=per_event(r,"B","MS")["model"]
        self.assertAlmostEqual(got["brier"],.5**2+(.25-1)**2+.25**2)
        self.assertAlmostEqual(got["logloss"],-math.log(.25))
        self.assertEqual(got["top1"],0)

    def test_no_independent_binary_rename_of_multiclass_ms(self):
        p={"MS1":.7,"MSX":.6,"MS2":.2}
        y={"MS1":1,"MSX":0,"MS2":0}
        with self.assertRaisesRegex(AuditBlocked,"INVALID_3WAY_PROBABILITY"):
            metrics(p,y,"MS")
        with self.assertRaisesRegex(AuditBlocked,"MS_NOT_INDEPENDENT_BINARY"):
            binary_shadow_calibration([row()],"B",
                {"MS1":{"available":True}}, "MS")

    def test_binary_market_and_asof_baseline_are_scored_as_same_event(self):
        r=row()
        score=per_event(r,"B","KG")
        self.assertAlmostEqual(score["model"]["brier"],(.6-1)**2)
        self.assertAlmostEqual(score["base"]["brier"],(.5-1)**2)
        n=score_market([r],"B","OVER25")
        self.assertAlmostEqual(n["brier"],.3**2)
        self.assertAlmostEqual(n["baseline_brier"],.5**2)

    def test_no_c2_dev_context_does_not_fabricate_skill_weight(self):
        c=calibration([],"C2")
        self.assertTrue(all(c[m]["available"] is False and
                            c[m]["weight"] is None and
                            c[m]["development_brier_skill"] is None
                            for m in c))

    def test_pair_compares_identical_matches_only(self):
        a=row(models=("B","M4"))
        b=row(date="2026-10-03",models=("M4",))
        s=pair_metric([a,b],"B","M4","KG")
        self.assertEqual(s["n"],1)
        self.assertEqual(s["days"],1)
        self.assertAlmostEqual(s["candidate_minus_reference_negative_Brier_improves"]["brier"],0)
        self.assertIsNone(s["calendar_day_resampling_interval"])

    def test_dev_only_weights_not_recomputed_from_october_results(self):
        cal={"BTTS_YES":{"available":True,"weight":.3,"development_brier_skill":.01}}
        result=binary_shadow_calibration([row()],"B",cal,"KG")
        self.assertEqual(result["n"],1)
        self.assertAlmostEqual(result["frozen_dev_weight"],.3)
        self.assertAlmostEqual(result["shrunk_Brier"],(.5+.3*(.6-.5)-1)**2)
        self.assertFalse(result["lock_applied_to_actual_live_picks"])

    def test_paired_date_bootstrap_fails_closed_on_few_dates(self):
        x=[{"date":"2026-10-02","brier":.02} for i in range(150)]
        self.assertIsNone(day_ci(x,"brier"))
        y=[{"date":f"2026-10-{i%12+1:02d}","brier":.01*(i%3-1)}
           for i in range(120)]
        got=day_ci(y,"brier",draws=100)
        self.assertIsNotNone(got)
        self.assertEqual(got["n_days"],12)

if __name__=="__main__":unittest.main()
