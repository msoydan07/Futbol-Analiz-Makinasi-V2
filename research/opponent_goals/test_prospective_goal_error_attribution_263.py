"""Safety regressions: prospective diagnosis is NOT historical pilot replay.

All newly created dates, score observations and fake official gates in these
tests are TEMPORARY UNIT TEST DATA. No actual fixture or outcome is asserted.
"""
from __future__ import annotations

import copy
import json
import math
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from prospective_goal_error_attribution_263 import (
    ROOT, Blocked, _day_ci, attribution_report, independent_m4_probabilities)
sys.path.insert(0,str(ROOT/"experiments/263"))
from sabah_batch_263 import sha
from m4_integrated import score_markets
from sabah_postmatch_new100_263 import SCHEMA as POSTMATCH_SCHEMA, ScoreBlocked

KO=datetime(2026,11,20,18,0,tzinfo=timezone.utc)
NOW=datetime(2026,12,15,12,0,tzinfo=timezone.utc)

def iso(x):return x.isoformat()

class ProspectiveGoalAttributionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)

    def put(self,day=KO,seq=0,score=(1,1),lh=1.2,la=.8,
            with_result=True,m4_available=True):
        # A synthetic deterministic forecast with valid old seal schema.
        made=day-timedelta(hours=7)
        checked=made+timedelta(seconds=9)
        names={"home_id":"SYNT_H_%d"%seq,"away_id":"SYNT_A_%d"%seq}
        markets=score_markets(lh,la)
        model_predictions={m:{"status":"AVAILABLE","goals":copy.deepcopy(markets)}
                           for m in ("B","C2","C3","M4")}
        if not m4_available:
            model_predictions["M4"]={"status":"UNAVAILABLE_FIT_OR_RANGE"}
        fixture={
            "league":"ENG1",**names,
            "match_local_date":day.date().isoformat(),
            "kickoff_utc":iso(day),
            "source_checked_at_utc":iso(checked),
            "fixture_verification":"VERIFIED_BY_LIVE_OFFICIAL_GATE",
            "official_source":"https://www.premierleague.com/en/fixtures"
        }
        forecast={
            "schema":"quad_forward_263_v1",
            "created_at_utc":iso(made),"fixture":fixture,
            "model_predictions":model_predictions
        }
        forecast["payload_sha256"]=sha(forecast)
        p=(self.root/"forward_morning_263"/fixture["match_local_date"]/
           ("%024x"%seq+".json"))
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(forecast),encoding="utf-8")
        result=None;rp=None
        if with_result:
            result={
              "schema":POSTMATCH_SCHEMA,"cohort":"new100",
              "forecast_sha256":forecast["payload_sha256"],
              "league":"ENG1",**names,"kickoff_utc":iso(day),
              "home_goals":score[0],"away_goals":score[1],
              "final_status":"FULL_TIME_HUMAN_REVIEWED",
              "source_url":"https://www.premierleague.com/en/fixtures",
              "source_checked_at_utc":iso(day+timedelta(hours=2,minutes=10)),
              "reviewed_at_utc":iso(day+timedelta(hours=2,minutes=15)),
              "reviewer":"Unit test only",
              "verification_scope":"HUMAN_ATTESTED_OFFICIAL_PAGE_NOT_NETWORK_REVERIFIED"
            }
            rp=(self.root/"experiments/263/sabah_postmatch_inputs"/
                fixture["match_local_date"]/(f"obs_{seq:04d}.json"))
            rp.parent.mkdir(parents=True,exist_ok=True)
            rp.write_text(json.dumps(result),encoding="utf-8")
        return forecast,p,result,rp

    def test_current_repository_never_replays_old_46_and_adapts_to_new_scores(self):
        # Real repo can grow after 11 Nov. Do NOT pin "zero fixtures" forever.
        r=attribution_report(ROOT,now=datetime.now(timezone.utc))
        self.assertTrue(r["no_nov6_7_8_reevaluation"])
        self.assertGreaterEqual(r["registered_new_day_sealed_forecasts"],0)
        self.assertLessEqual(r["eligible_finished_reviewed_results"],
                             r["registered_new_day_sealed_forecasts"])
        self.assertTrue(all(d>="2026-11-09" for d in r["observed_match_dates"]))
        self.assertFalse(r["automatic_model_promotion"])
        self.assertFalse(r["betting_authorized"])
        if r["eligible_finished_reviewed_results"]==0:
            self.assertIsNone(r["diagnostics"]["btts_residual"]["mean"])

    def test_older_invalid_prediction_not_opened_or_re_evaluated(self):
        old=self.root/"forward_morning_263/2026-11-08/a.json"
        old.parent.mkdir(parents=True)
        old.write_text("tampered old pilot, deliberately unreadable")
        r=attribution_report(self.root,now=NOW)
        self.assertEqual(r["registered_new_day_sealed_forecasts"],0)
        self.assertTrue(r["no_nov6_7_8_reevaluation"])

    def test_scored_new_day_exact_lambdas_and_goal_market_errors(self):
        self.put(score=(2,1),lh=1.2,la=.8)
        r=attribution_report(self.root,now=NOW)
        self.assertEqual(r["eligible_finished_reviewed_results"],1)
        self.assertEqual(r["distinct_new_match_dates"],1)
        line=r["per_match"][0]
        p=independent_m4_probabilities(1.2,.8)
        self.assertAlmostEqual(line["m4_btts_probability"],p["BTTS_YES"])
        self.assertAlmostEqual(line["m4_over25_probability"],p["OVER_2.5"])
        self.assertAlmostEqual(r["diagnostics"]["total_goal_residual"]["mean"],1.)
        self.assertAlmostEqual(r["diagnostics"]["btts_residual"]["mean"],1-p["BTTS_YES"])
        self.assertAlmostEqual(line["m4_over25_brier"],(1-p["OVER_2.5"])**2)
        self.assertEqual(r["mean_market_brier_and_paired_models"]["B_minus_M4_BTTS_brier"]["n_same_matches"],1)
        self.assertEqual(r["triage_hypothesis_not_model_decision"],
                         "NEW_INDEPENDENT_DATES_INSUFFICIENT_FOR_DIAGNOSTIC_CI")

    def test_dev_only_lambda_105_shadow_has_exact_paired_losses_and_never_edits_seal(self):
        forecast,p,_,_=self.put(score=(2,1),lh=1.2,la=.8)
        sealed_before=p.read_bytes()
        report=attribution_report(self.root,now=NOW)
        s=report["fixed_lambda_105_dev_candidate_shadow"]
        self.assertEqual(s["same_match_new_day_n"],1)
        self.assertTrue(s["no_pre_match_probability_changes"])
        self.assertTrue(s["no_model_promotion"])
        self.assertTrue(s["no_new_pilot"])
        candidate=score_markets(1.2*1.05,.8*1.05)["markets"]
        baseline=score_markets(1.2,.8)["markets"]
        expected_kg=(candidate["BTTS_YES"]-1)**2-(baseline["BTTS_YES"]-1)**2
        expected_o25=(candidate["OVER_2.5"]-1)**2-(baseline["OVER_2.5"]-1)**2
        means=s["candidate_minus_original_lower_brier_is_better"]
        self.assertAlmostEqual(means["candidate_minus_original_KG_Brier"]["mean"],expected_kg)
        self.assertAlmostEqual(means["candidate_minus_original_O25_Brier"]["mean"],expected_o25)
        self.assertIsNone(means["candidate_minus_original_KG_Brier"]["date_block_95pct_interval"])
        self.assertEqual(p.read_bytes(),sealed_before)
        self.assertEqual(report["per_match"][0]["forecast_sha256"],forecast["payload_sha256"])

    def test_105_candidate_never_fills_out_of_range_expected_goals(self):
        self.put(score=(1,0),lh=4.9,la=.8)
        r=attribution_report(self.root,now=NOW)
        self.assertEqual(r["eligible_finished_reviewed_results"],1)
        self.assertIsNone(r["per_match"][0]["fixed_lambda_105_dev_candidate"])
        s=r["fixed_lambda_105_dev_candidate_shadow"]
        self.assertEqual(s["same_match_new_day_n"],0)
        self.assertEqual(s["excluded_out_of_safe_lambda_range"],1)
        self.assertIsNone(s["candidate_minus_original_lower_brier_is_better"]
                          ["candidate_minus_original_MS_Brier"]["mean"])

    def test_pending_prediction_is_not_imputed_as_zero_score(self):
        self.put(with_result=False)
        r=attribution_report(self.root,now=NOW)
        self.assertEqual(r["registered_new_day_sealed_forecasts"],1)
        self.assertEqual(r["pending_results"],1)
        self.assertEqual(r["eligible_finished_reviewed_results"],0)

    def test_future_or_prekickoff_source_result_is_rejected(self):
        _,_,raw,p=self.put()
        raw["source_checked_at_utc"]=iso(KO+timedelta(minutes=8))
        p.write_text(json.dumps(raw))
        with self.assertRaises(ScoreBlocked):
            attribution_report(self.root,now=NOW)

    def test_results_from_other_forecasts_are_not_admitted(self):
        _,_,raw,p=self.put()
        raw["forecast_sha256"]="f"*64
        p.write_text(json.dumps(raw))
        with self.assertRaisesRegex(Blocked,"RESULT_NOT_FOR_NEW_DAY"):
            attribution_report(self.root,now=NOW)

    def test_duplicate_result_never_changes_n(self):
        _,_,raw,p=self.put()
        second=p.with_name("other.json")
        second.write_text(json.dumps(raw))
        with self.assertRaisesRegex(Blocked,"DUPLICATE_RESULT_ATTESTATION"):
            attribution_report(self.root,now=NOW)

    def test_tampered_forecast_prediction_is_rejected(self):
        forecast,p,_,_=self.put()
        forecast["model_predictions"]["M4"]["goals"]["markets"]["BTTS_YES"]=0.97
        p.write_text(json.dumps(forecast))
        with self.assertRaisesRegex(ValueError,"SHA"):
            attribution_report(self.root,now=NOW)

    def test_forged_rehashed_but_math_inconsistent_m4_is_rejected(self):
        forecast,p,raw,rp=self.put()
        forecast["model_predictions"]["M4"]["goals"]["markets"]["BTTS_YES"]=.99
        forecast["payload_sha256"]=sha({k:v for k,v in forecast.items()
                                          if k!="payload_sha256"})
        p.write_text(json.dumps(forecast))
        raw["forecast_sha256"]=forecast["payload_sha256"]
        rp.write_text(json.dumps(raw))
        with self.assertRaisesRegex(Blocked,"MARKET_NOT_DERIVED"):
            attribution_report(self.root,now=NOW)

    def test_too_little_data_has_no_date_bootstrap_ci(self):
        for i in range(20):
            self.put(KO+timedelta(days=i//2),seq=i)
        r=attribution_report(self.root,now=NOW)
        self.assertEqual(r["distinct_new_match_dates"],10)
        self.assertEqual(r["eligible_finished_reviewed_results"],20)
        self.assertIsNone(r["diagnostics"]["goal_cross_residual"]["date_block_95pct_interval"])
        self.assertIsNone(r["mean_market_brier_and_paired_models"]["B_minus_M4_BTTS_brier"]
                          ["date_block_95pct_interval"])

    def test_80_matches_ten_days_enters_exploratory_bootstrap_not_model_promotion(self):
        for i in range(80):
            self.put(KO+timedelta(days=i//8),seq=i,
                     score=(i%3, (i//3)%3),lh=1.1+(i%4)*.1,
                     la=.8+(i%3)*.1)
        r=attribution_report(self.root,now=NOW)
        self.assertEqual(r["eligible_finished_reviewed_results"],80)
        self.assertEqual(r["distinct_new_match_dates"],10)
        ci=r["diagnostics"]["home_goal_residual"]["date_block_95pct_interval"]
        self.assertIsNotNone(ci)
        self.assertEqual(ci["method"],"day_block_bootstrap")
        self.assertEqual(ci["distinct_days"],10)
        self.assertFalse(r["causal_lambda_vs_dependence_identification_proven"])
        self.assertFalse(r["automatic_model_promotion"])
        self.assertFalse(r["betting_authorized"])

    def test_bad_lambda_and_unknown_unavailable_m4_are_not_substituted(self):
        with self.assertRaises(Blocked):
            independent_m4_probabilities(float("nan"),1.0)
        self.put(m4_available=False)
        r=attribution_report(self.root,now=NOW)
        self.assertEqual(r["finished_missing_M4"],1)
        self.assertEqual(r["eligible_finished_reviewed_results"],0)

    def test_reviewed_result_with_wrong_team_id_is_refused(self):
        _,_,raw,p=self.put()
        raw["away_id"]="WRONG_CLUB"
        p.write_text(json.dumps(raw))
        with self.assertRaises(ScoreBlocked):
            attribution_report(self.root,now=NOW)

if __name__=="__main__":
    unittest.main()
