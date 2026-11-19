"""C3 calibration SHADOW can never change the market decision or PAS."""
import copy
import json
import unittest
from pathlib import Path
from c3_calibration_shadow_263 import make_shadow, SCHEMA
from model_first_decision_263 import select,verified,digest
from test_model_first_decision_263 import scenario,LOCK,NOW,seal
from test_model_first_iddaa_bridge_263 import TestModelFirstIddaa

ROOT=Path(__file__).resolve().parents[2]
DEV=json.loads((ROOT/"experiments/263/forward_dev_calibration_lock_263.json").read_text())

class ShadowSafety(unittest.TestCase):
    def test_signed_raw_and_shrunk_complements(self):
        f,b=scenario()
        d=select(f,b,LOCK,now=NOW)
        before=d["payload_sha256"]
        sh=make_shadow(f,b,d,DEV)
        self.assertEqual(verified(sh,SCHEMA),sh)
        self.assertEqual(sh["model_decision_sha256"],before)
        self.assertEqual(d["payload_sha256"],before)
        self.assertFalse(sh["selection_changed"])
        self.assertFalse(sh["pas_changed"])
        for fam in ("KG","O25"):
            z=sh["families"][fam]
            self.assertEqual(z["model"],"C3")
            self.assertAlmostEqual(z["raw_positive"]+z["raw_negative"],1)
            self.assertAlmostEqual(z["frozen_shrunken_positive"]+
                                   z["frozen_shrunken_negative"],1)
            self.assertAlmostEqual(z["frozen_shrunken_positive"],
                z["asof_league_positive"]+
                z["source_dev_weight"]*(z["raw_positive"]-z["asof_league_positive"]))
        self.assertEqual(d["main_candidate"]["market"],"MS1")

    def test_source_brier_future_results_are_not_inputs(self):
        f,b=scenario();d=select(f,b,LOCK,now=NOW)
        sh=make_shadow(f,b,d,DEV)
        self.assertNotIn("actual",json.dumps(sh))
        self.assertNotIn("result",json.dumps(sh))
        self.assertTrue(sh["do_not_use_to_pick"])

    def test_frozen_lock_tamper_rejected(self):
        f,b=scenario();d=select(f,b,LOCK,now=NOW)
        fake=copy.deepcopy(DEV)
        fake["calibration"]["C3"]["OVER_2.5"]["weight"]=.9
        with self.assertRaisesRegex(ValueError,"C3_SHADOW_DEV_LOCK_UNTRUSTED"):
            make_shadow(f,b,d,fake)

    def test_forecast_reference_cannot_switch_matches(self):
        f,b=scenario();d=select(f,b,LOCK,now=NOW)
        bad=copy.deepcopy(b)
        bad["forecast_sha256"]="0"*64
        seal(bad)
        with self.assertRaisesRegex(ValueError,"C3_SHADOW_CROSS_RECORD_SHA_MISMATCH"):
            make_shadow(f,bad,d,DEV)

    def test_shadow_source_unavailable_is_not_a_model_block_or_pas(self):
        f,b=scenario()
        f["model_predictions"]["C3"]["status"]="UNAVAILABLE"
        seal(f)
        b["forecast_sha256"]=f["payload_sha256"]
        seal(b)
        d=select(f,b,LOCK,now=NOW)
        sh=make_shadow(f,b,d,DEV)
        self.assertEqual(sh["status"],"C3_UNAVAILABLE_SHADOW_SKIPPED")
        self.assertEqual(sh["families"],{})
        self.assertEqual(sh["model_decision_sha256"],d["payload_sha256"])

if __name__=="__main__":
    unittest.main()
