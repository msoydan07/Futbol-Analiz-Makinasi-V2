"""Synthetic regression: MARKET can never steer the four-model choice."""
import copy
import json
import unittest
from pathlib import Path

from model_first_decision_263 import (
    select, market_reference, digest, verified, EvidenceError, SCHEMA, REF_SCHEMA, joint_poisson
)

HERE = Path(__file__).resolve().parent
LOCK = json.loads((HERE / "model_first_selection_lock_20261120.json").read_text(encoding="utf-8"))
NOW = "2026-11-21T10:05:00+00:00"

def seal(obj):
    obj["payload_sha256"] = digest({k:v for k,v in obj.items() if k != "payload_sha256"})
    return obj

def scenario():
    p=joint_poisson(2.8,.6)
    marks={"1X2":{"H":p["MS1"],"D":p["MSX"],"A":p["MS2"]},
           "BTTS_YES":p["BTTS_YES"],"BTTS_NO":p["BTTS_NO"],
           "OVER_2.5":p["OVER_2.5"],"UNDER_2.5":p["UNDER_2.5"]}
    models={m:{"status":"AVAILABLE","goals":{"lambda_home":2.8,"lambda_away":.6,
             "markets":copy.deepcopy(marks)}} for m in ("B","C3","M4")}
    models["C2"]={"status":"UNAVAILABLE","reason":"INSUFFICIENT_CURRENT_CONTEXT"}
    forecast=seal({"schema":"quad_forward_263_v1",
        "status":"EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING",
        "created_at_utc":"2026-11-21T10:00:00+00:00",
        "fixture":{"league":"TUR1","home_id":"synthetic-home","away_id":"synthetic-away",
                   "match_local_date":"2026-11-21","kickoff_utc":"2026-11-21T17:00:00+00:00",
                   "fixture_verification":"VERIFIED_BY_LIVE_OFFICIAL_GATE"},
        "data":{"snapshot_sha256":"a"*64},"model_predictions":models})
    base=seal({"schema":"263_asof_market_baseline_v2",
       "forecast_sha256":forecast["payload_sha256"],"league":"TUR1",
       "source_snapshot_sha256":"a"*64,"method":"PAST_RESULTS_LEAGUE_MARKET_RATE",
       "last_result_date":"2026-11-08","created_at_utc":"2026-11-21T10:01:00+00:00",
       "markets":{"MS1":.42,"MSX":.26,"MS2":.32,"BTTS_YES":.51,"BTTS_NO":.49,
                  "OVER_2.5":.5,"UNDER_2.5":.5}})
    return forecast,base

class TestNoOddsDecision(unittest.TestCase):
    def test_valid_candidate_and_seal(self):
        f,b=scenario();d=select(f,b,LOCK,now=NOW)
        self.assertEqual(d["main_candidate"]["market"],"MS1")
        self.assertEqual(d["main_candidate"]["anchor_model"],"M4")
        self.assertFalse(d["price_used_in_decision"])
        self.assertFalse(d["betting_authorized"])
        self.assertEqual(verified(d,SCHEMA),d)

    def test_market_odds_can_change_but_forecast_sha_cannot(self):
        f,b=scenario();d=select(f,b,LOCK,now=NOW)
        a={"MS":{"status":"FULL_MARKET_QUOTE_AVAILABLE",
                 "prices":{"MS1":1.5,"MSX":4.3,"MS2":5.5},
                 "no_vig":{"MS1":.61,"MSX":.22,"MS2":.17}}}
        r1=market_reference(d,a,source_pdf_sha256="c"*64)
        a["MS"]["prices"]["MS1"]=2.4;a["MS"]["no_vig"]["MS1"]=.38
        r2=market_reference(d,a,source_pdf_sha256="c"*64)
        self.assertEqual(r1["decision_sha256"],r2["decision_sha256"])
        self.assertNotEqual(r1["payload_sha256"],r2["payload_sha256"])
        self.assertEqual(d["main_candidate"]["market"],"MS1")

    def test_no_price_not_a_model_pas(self):
        f,b=scenario();d=select(f,b,LOCK,now=NOW)
        r=market_reference(d,{},source_pdf_sha256="c"*64)
        self.assertEqual(d["status"],"RESEARCH_CANDIDATE_NOT_APPROVED")
        self.assertTrue(all(z["status"]=="NO_COMPLETE_GROUP" for z in r["rows"]))

    def test_c2_unavailable_still_returns_decision(self):
        f,b=scenario()
        self.assertEqual(select(f,b,LOCK,now=NOW)["main_candidate"]["market"],"MS1")

    def test_m4_missing_is_technical_failure(self):
        f,b=scenario();f["model_predictions"]["M4"]["status"]="UNAVAILABLE";seal(f)
        b["forecast_sha256"]=f["payload_sha256"];seal(b)
        with self.assertRaisesRegex(EvidenceError,"ANCHOR_M4_UNAVAILABLE"):
            select(f,b,LOCK,now=NOW)

    def test_mutated_forecast_rejected(self):
        f,b=scenario();f["fixture"]["home_id"]="OTHER"
        with self.assertRaisesRegex(EvidenceError,"SHA_TAMPERED"):
            select(f,b,LOCK,now=NOW)

    def test_cross_fixture_baseline_rejected(self):
        f,b=scenario();b["forecast_sha256"]="e"*64;seal(b)
        with self.assertRaisesRegex(EvidenceError,"BASELINE_FORECAST_SHA_MISMATCH"):
            select(f,b,LOCK,now=NOW)

    def test_post_kickoff_rejected(self):
        f,b=scenario()
        with self.assertRaisesRegex(EvidenceError,"NOT_PREKICKOFF"):
            select(f,b,LOCK,now="2026-11-21T18:00:00+00:00")

    def test_same_day_history_leakage(self):
        f,b=scenario();b["last_result_date"]="2026-11-21";seal(b)
        with self.assertRaisesRegex(EvidenceError,"HISTORICAL_LEAKAGE"):
            select(f,b,LOCK,now=NOW)

    def test_old_lock_modified(self):
        f,b=scenario();lock=copy.deepcopy(LOCK);lock["min_probability"]=0
        with self.assertRaisesRegex(EvidenceError,"MODEL_LOCK_SHA_MISMATCH"):
            select(f,b,lock,now=NOW)

    def test_invalid_model_probability(self):
        f,b=scenario();f["model_predictions"]["B"]["goals"]["markets"]["1X2"]["H"]=2.0;seal(f)
        b["forecast_sha256"]=f["payload_sha256"];seal(b)
        with self.assertRaisesRegex(EvidenceError,"BAD_PROBABILITY"):
            select(f,b,LOCK,now=NOW)

    def test_low_confidence_is_actual_model_pas(self):
        f,b=scenario();p=joint_poisson(1.3,1.3)
        for name in ("M4","C3","B"):
            g=f["model_predictions"][name]["goals"]
            g["lambda_home"]=1.3;g["lambda_away"]=1.3
            g["markets"]["1X2"]={"H":p["MS1"],"D":p["MSX"],"A":p["MS2"]}
            for k in ("BTTS_YES","BTTS_NO","OVER_2.5","UNDER_2.5"):
                g["markets"][k]=p[k]
        seal(f);b["forecast_sha256"]=f["payload_sha256"];seal(b)
        self.assertEqual(select(f,b,LOCK,now=NOW)["status"],"RESEARCH_PAS_MODEL_ONLY")

    def test_forged_pdf_sha_rejected(self):
        f,b=scenario();d=select(f,b,LOCK,now=NOW)
        with self.assertRaisesRegex(EvidenceError,"PDF_SHA_INVALID"):
            market_reference(d,{},source_pdf_sha256="not-a-hash")

    def test_reference_record_immutable(self):
        f,b=scenario();d=select(f,b,LOCK,now=NOW)
        ref=market_reference(d,{},source_pdf_sha256="c"*64)
        verified(ref,REF_SCHEMA)
        ref["rows"][0]["status"]="FORGED"
        with self.assertRaisesRegex(EvidenceError,"SHA_TAMPERED"):
            verified(ref,REF_SCHEMA)

    def test_joint_calibration_market_sum_consistent(self):
        f,b=scenario();d=select(f,b,LOCK,now=NOW)
        p={x["market"]:x["calibrated_probability"] for x in d["model_market_diagnostics"]}
        for names in (("MS1","MSX","MS2"),("BTTS_YES","BTTS_NO"),
                      ("OVER_2.5","UNDER_2.5")):
            self.assertAlmostEqual(sum(p[k] for k in names),1,places=8)

    def test_nov20_specialists_MS_m4_KG_and_O25_c3_with_distinct_vectors(self):
        f,b=scenario()
        # Distinct, normalized C3 BTTS/O25; keep MS unchanged.
        c3=f["model_predictions"]["C3"]["goals"]["markets"]
        c3.update({"BTTS_YES":.91,"BTTS_NO":.09,
                   "OVER_2.5":.82,"UNDER_2.5":.18})
        seal(f);b["forecast_sha256"]=f["payload_sha256"];seal(b)
        result=select(f,b,LOCK,now=NOW)
        diag={r["market"]:r for r in result["model_market_diagnostics"]}
        self.assertEqual(result["fixed_family_experts"],{"MS":"M4","KG":"C3","O25":"C3"})
        self.assertEqual(diag["MS1"]["anchor_model"],"M4")
        self.assertEqual(diag["BTTS_YES"]["anchor_model"],"C3")
        self.assertEqual(diag["OVER_2.5"]["anchor_model"],"C3")
        self.assertEqual(diag["BTTS_YES"]["probability_type"],"C3_RAW_UNCALIBRATED")
        self.assertAlmostEqual(diag["BTTS_YES"]["calibrated_probability"],.91)
        self.assertAlmostEqual(diag["OVER_2.5"]["calibrated_probability"],.82)
        self.assertAlmostEqual(sum(diag[k]["calibrated_probability"] for k in ("MS1","MSX","MS2")),1,places=8)

    def test_market_reference_only_cannot_create_model_pas(self):
        f,b=scenario()
        d=select(f,b,LOCK,now=NOW)
        original=d["payload_sha256"]
        for prices in ({"MS":{"status":"PRICE_MISSING_ONE_OR_MORE_SIDES"}},
                       {"KG":{"status":"INVALID_PRICE"}},{}):
            ref=market_reference(d,prices,source_pdf_sha256="d"*64)
            self.assertEqual(ref["decision_sha256"],original)
            self.assertEqual(d["payload_sha256"],original)

    def test_alternative_distinct_family(self):
        f,b=scenario();d=select(f,b,LOCK,now=NOW)
        if d["alternative_candidate"]:
            self.assertNotEqual(d["main_candidate"]["family"],d["alternative_candidate"]["family"])

if __name__=="__main__":
    unittest.main(verbosity=2)
