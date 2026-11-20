"""v4 acceptance: original v3 seals, prices, time gates and C3-family scoring.

All forecasts below are synthetic; no re-recording of historic SHA results.
"""
import copy
import json
import math
import unittest
from pathlib import Path

from model_first_decision_263 import select,digest,verified,SCHEMA,EvidenceError,joint_poisson
from model_first_frozen_c3_calibration_263 import (
    SUPPORTED,verify_policy,calibrated_binary_pair,TRAIN_N
)
from test_model_first_decision_263 import scenario,NOW,LOCK as LEGACY_V3,seal

ROOT=Path(__file__).resolve().parent
V4=json.loads((ROOT/"model_first_selection_lock_20261121_v4.json").read_text(encoding="utf-8"))

class FrozenC3V4Acceptance(unittest.TestCase):
    def test_new_lock_signed_and_training_frozen(self):
        self.assertEqual(V4["payload_sha256"],digest({k:v for k,v in V4.items() if k!="payload_sha256"}))
        self.assertEqual(V4["calibration_v4"]["train_n"],2898)
        self.assertEqual(V4["calibration_v4"]["train_season"],"2025-2026")
        verify_policy(V4["calibration_v4"])
        self.assertFalse(V4["officially_approved"])
        self.assertFalse(V4["retrospective_evaluation_reused_not_independent"] is False)

    def test_no_leakage_and_market_complements(self):
        f,b=scenario()
        c3=f["model_predictions"]["C3"]["goals"]["markets"]
        c3.update({"BTTS_YES":.91,"BTTS_NO":.09,"OVER_2.5":.82,"UNDER_2.5":.18})
        seal(f);b["forecast_sha256"]=f["payload_sha256"];seal(b)
        d=select(f,b,V4,now=NOW)
        self.assertEqual(d["selection_policy_version"],"20261121_C3_2025_FROZEN_V4")
        self.assertFalse(d["nov8_raw_sha_history_used_to_rank"])
        self.assertFalse(d["price_used_in_decision"])
        self.assertEqual(d["historical_reference_source"],"NONE_FOR_NEW_CALIBRATION_VERSION")
        self.assertEqual(d["historical_completed_matches"],0)
        self.assertFalse(d["independent_forward_superiority_established"])
        diag={x["market"]:x for x in d["model_market_diagnostics"]}
        for positive,negative,family in (
            ("BTTS_YES","BTTS_NO","KG"),("OVER_2.5","UNDER_2.5","O25")):
            exp_yes,_=calibrated_binary_pair(c3[positive],b["markets"][positive],
                                             positive,V4["calibration_v4"])
            self.assertAlmostEqual(diag[positive]["calibrated_probability"],exp_yes,places=8)
            self.assertAlmostEqual(diag[positive]["calibrated_probability"]+
                                   diag[negative]["calibrated_probability"],1,places=8)
            self.assertEqual(diag[positive]["probability_type"],"C3_2025_FROZEN_BINARY_LOGIT")
        self.assertAlmostEqual(sum(diag[k]["calibrated_probability"] for k in ("MS1","MSX","MS2")),1,places=8)
        self.assertEqual(d["main_candidate"]["market"],
                         max(diag,key=lambda k:diag[k]["calibrated_probability"]))
        if d["alternative_candidate"]:
            self.assertNotEqual(d["main_candidate"]["family"],d["alternative_candidate"]["family"])
        self.assertEqual(verified(d,SCHEMA),d)

    def test_preexisting_v3_lock_retains_original_calculation_and_sha(self):
        f,b=scenario()
        legacy=select(f,b,LEGACY_V3,now=NOW)
        fresh=select(f,b,V4,now=NOW)
        self.assertNotIn("selection_policy_version",legacy)
        self.assertEqual(legacy["model_policy_sha256"],LEGACY_V3["payload_sha256"])
        self.assertEqual(verified(legacy,SCHEMA),legacy)
        self.assertEqual(fresh["model_policy_sha256"],V4["payload_sha256"])
        self.assertNotEqual(fresh["payload_sha256"],legacy["payload_sha256"])
        self.assertEqual(fresh["forecast_sha256"],legacy["forecast_sha256"])
        self.assertTrue(fresh["forecast_unchanged"])

    def test_forged_coefficients_fail_even_after_resigning(self):
        f,b=scenario()
        fake=copy.deepcopy(V4)
        fake["calibration_v4"]["coefficients"]["BTTS_YES"]["intercept"]=.999
        seal(fake)
        with self.assertRaisesRegex(EvidenceError,"FROZEN_C3_POLICY_INVALID"):
            select(f,b,fake,now=NOW)

    def test_tampered_v4_sha_fails(self):
        f,b=scenario()
        fake=copy.deepcopy(V4)
        fake["calibration_v4"]["train_n"]=2899
        with self.assertRaisesRegex(EvidenceError,"MODEL_LOCK_SHA_MISMATCH"):
            select(f,b,fake,now=NOW)

    def test_missing_c3_marked_uncalibrated_m4_fallback(self):
        f,b=scenario()
        f["model_predictions"]["C3"]={"status":"UNAVAILABLE","reason":"NO_PRIOR"}
        seal(f);b["forecast_sha256"]=f["payload_sha256"];seal(b)
        d=select(f,b,V4,now=NOW)
        self.assertEqual(set(d["used_fallback_families"]),{"KG","O25"})
        diag={x["market"]:x for x in d["model_market_diagnostics"]}
        self.assertEqual(diag["BTTS_YES"]["probability_type"],"M4_RAW_FALLBACK_UNCALIBRATED")
        self.assertEqual(d["selection_policy_version"],"20261121_C3_2025_FROZEN_V4")

    def test_missing_and_nonfinite_calibration_rejected(self):
        for p in (float("nan"),-0.1,1.1,None,True):
            with self.assertRaises(ValueError):
                calibrated_binary_pair(p,.5,"BTTS_YES",V4["calibration_v4"])

    def test_no_post_kickoff_and_same_day_data(self):
        f,b=scenario()
        with self.assertRaisesRegex(EvidenceError,"NOT_PREKICKOFF"):
            select(f,b,V4,now="2026-11-21T18:00:00+00:00")
        b["last_result_date"]="2026-11-21";seal(b)
        with self.assertRaisesRegex(EvidenceError,"HISTORICAL_LEAKAGE"):
            select(f,b,V4,now=NOW)

if __name__=="__main__":
    unittest.main(verbosity=2)
