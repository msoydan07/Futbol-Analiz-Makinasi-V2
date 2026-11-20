"""Real 39-result read-only pre-kickoff reference acceptance, no betting APIs."""
import unittest
from collections import Counter
from datetime import datetime,timezone
from normal_historical_reference_263 import load,available_asof,AVAILABLE_FROM
from historical_probability_reliability_263 import rank_candidates,similar

CUTOFF="2026-11-20T11:30:00+00:00"

class NormalCoreHistory(unittest.TestCase):
    def test_archive_not_available_before_12_nov_closeout(self):
        self.assertFalse(available_asof(asof="2026-11-12T22:00:00+00:00"))
        self.assertEqual(load(asof="2026-11-08T07:00:00+00:00"),[])
    def test_real_signed_history_40_39_273(self):
        rows=load(asof=CUTOFF)
        self.assertEqual(len(rows),273)
        self.assertEqual(len({r["forecast_sha256"] for r in rows}),39)
        self.assertEqual(len({(r["forecast_sha256"],r["market"]) for r in rows}),273)
        self.assertTrue(all(r["forecast_origin"]=="SEALED_BEFORE_KICKOFF" for r in rows))
        self.assertTrue(all(r["result_known_at_utc"]==AVAILABLE_FROM for r in rows))
        self.assertTrue(all(r["model_identity"] in ("M4_AUG_JOINT_CALIBRATED",
                              "C3_RAW_UNCALIBRATED",
                              "M4_RAW_FALLBACK_UNCALIBRATED") for r in rows))
    def test_real_reference_is_market_and_model_specific(self):
        rows=load(asof=CUTOFF)
        e=similar(rows,league="ESP1",market="UNDER_2.5",probability=.5813,
              asof=CUTOFF,model_identity="C3_RAW_UNCALIBRATED")
        self.assertLessEqual(e["n"],39)
        self.assertEqual(e["market"],"UNDER_2.5")
        self.assertGreaterEqual(e["wins"],0)
        c=[{"market":"UNDER_2.5","family":"O25",
            "calibrated_probability":.5813,
            "probability_type":"C3_RAW_UNCALIBRATED"},
           {"market":"MS1","family":"MS",
            "calibrated_probability":.4625,
            "probability_type":"M4_AUG_JOINT_CALIBRATED"}]
        ranked=rank_candidates(c,rows,league="ESP1",asof=CUTOFF)
        self.assertEqual(len(ranked),2)
        self.assertTrue(all(0<=r["estimated_realization_probability"]<=1
                            for r in ranked))
        self.assertTrue(all(r["historical_reliability"]["independent_holdout_verified"] is False
                            for r in ranked))
if __name__=="__main__":unittest.main()
