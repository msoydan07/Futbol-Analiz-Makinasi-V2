"""Stage 6 only: 14 finite/identity/temporal/no-record regressions.

Pre-existing retrospective performance experiments are never rerun.
"""
from __future__ import annotations

import copy
import json
import math
import unittest
from datetime import datetime
from pathlib import Path

from uefa_nov3_5_stage6_shadow_math_preflight_263 import (
    SOURCES, checked_json, audit, upstream_inputs, to_retro_profile,
    make_pair, compute_volatile, PreflightError)
from uefa_elo_m0_paired_retrospective_263 import (
    lambdas, predict, base_features)

ROOT=Path("data/europe_staged_263/stage6_inputs")
PATHS={
    "stage4":ROOT/"goals/stage4_goal_data_readiness.json",
    "stage5":ROOT/"elo_news/17_match_elo_news_readiness.json",
    "retro":ROOT/"historical/retrospective_elo_vs_m0_report.json",
    "scope":Path("experiments/263/evidence/uefa_2026_11_03_05_fixture_scope_review.json"),
}
START=datetime.fromisoformat("2026-11-03T07:00:00+00:00")

class Stage6Math(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s4=checked_json(PATHS["stage4"],SOURCES["stage4"])
        cls.s5=checked_json(PATHS["stage5"],SOURCES["stage5"])
        cls.retro=checked_json(PATHS["retro"],SOURCES["retro"])
        cls.scope=json.loads(PATHS["scope"].read_text(encoding="utf8"))
        cls.beta=cls.retro["fixed_protocol"]["beta_retrospective_fitted"]
        cls.home_mean=cls.retro["fixed_protocol"]["UEFA_train_home_goal_mean"]
        cls.away_mean=cls.retro["fixed_protocol"]["UEFA_train_away_goal_mean"]
        cls.pairs=[
          make_pair(x,next(y for y in cls.s5["matches"] if y["uefa_match_id"]==x["uefa_match_id"]),
                    next(y for y in cls.scope["verified_fixtures"] if y["uefa_match_id"]==x["uefa_match_id"]))
          for x in cls.s4["fixtures"]]
    def call(self,*,stage4=None,stage5=None,retro=None,scope=None,now=START):
        return audit(stage4 if stage4 is not None else self.s4,
                     stage5 if stage5 is not None else self.s5,
                     retro if retro is not None else self.retro,
                     scope if scope is not None else self.scope,
                     now=now)
    def test_01_all_17_complete_no_prediction_ledger(self):
        r=self.call()
        self.assertEqual(r["matches_tested"],17)
        self.assertEqual(r["unique_teams_tested"],34)
        self.assertEqual(r["day_count"],{"2026-11-03":6,"2026-11-04":6,"2026-11-05":5})
        self.assertTrue(r["historical_math_reused_unchanged"])
        self.assertFalse(r["any_per_match_lambda_or_probability_saved"])
        self.assertFalse(r["any_real_match_prediction_recorded"])
        self.assertFalse(r["pilot_recorded"])
        self.assertFalse(r["mathematical_calibration_or_main_approval"])
        self.assertFalse(any(k in r for k in ("predictions","picks","lambdas","per_match")))
    def test_02_every_match_two_variants_finite_mass_one(self):
        for pair in self.pairs:
            out=compute_volatile(pair,self.home_mean,self.away_mean,self.beta)
            self.assertEqual(set(out),{"M0","M0Elo"})
            for vals in out.values():
                self.assertAlmostEqual(sum(vals[2]),1,places=12)
                self.assertTrue(all(0.15<=x<=5 for x in vals[:2]))
                self.assertTrue(all(0<=x<=1 for x in (*vals[2],vals[3],vals[4])))
    def test_03_same_historical_lambda_function_no_new_formula(self):
        for pair in self.pairs:
            out=compute_volatile(pair,self.home_mean,self.away_mean,self.beta)
            self.assertEqual(out["M0"][:2],lambdas(pair,self.home_mean,self.away_mean,0.0))
            self.assertEqual(out["M0Elo"][:2],lambdas(pair,self.home_mean,self.away_mean,self.beta))
    def test_04_same_rating_must_remove_elo_effect(self):
        test=copy.deepcopy(self.pairs[0])
        test["away"]["elo"]=test["home"]["elo"]
        out=compute_volatile(test,self.home_mean,self.away_mean,self.beta)
        self.assertEqual(out["M0"][:2],out["M0Elo"][:2])
        self.assertEqual(out["M0"][2],out["M0Elo"][2])
    def test_05_elo_is_only_secondary_experimental_modifier(self):
        for pair in self.pairs:
            f=base_features(pair)
            self.assertEqual(len(f),2)
            self.assertTrue(all(0<z<100 for z in f))
            out=compute_volatile(pair,self.home_mean,self.away_mean,self.beta)
            h0,a0=out["M0"][:2]
            self.assertGreater(h0,0)
            self.assertGreater(a0,0)
    def test_06_source_archive_corruption_rejected(self):
        raw=bytearray(PATHS["stage4"].read_bytes())
        raw[22]=ord("X") if raw[22]!=ord("X") else ord("Y")
        damaged=ROOT/"temporary_malicious_stage4.json"
        try:
            damaged.write_bytes(raw)
            with self.assertRaisesRegex(PreflightError,"FROZEN_INPUT_HASH_CHANGED"):
                checked_json(damaged,SOURCES["stage4"])
        finally:
            damaged.unlink(missing_ok=True)
    def test_07_later_than_first_kickoff_rejected(self):
        with self.assertRaisesRegex(PreflightError,"SHADOW_MATH_PREFLIGHT_TOO_LATE_FOR_ALL_17"):
            self.call(now=datetime.fromisoformat("2026-11-03T17:46:00+00:00"))
    def test_08_stage4_source_after_kickoff_rejected(self):
        damaged=copy.deepcopy(self.s4)
        damaged["analysis_time_utc"]="2026-11-03T18:01:00+00:00"
        with self.assertRaisesRegex(PreflightError,"ARCHIVED_PREMATCH_SNAPSHOTS_NOT_BEFORE_FIRST_KICKOFF"):
            self.call(stage4=damaged)
    def test_09_stage5_upgraded_elo_alpha_rejected(self):
        retro=copy.deepcopy(self.retro)
        retro["Elo_weight_approved_for_model"]=True
        with self.assertRaisesRegex(PreflightError,"EXPERIMENTAL_BETA_SOURCE_POLICY_CHANGED"):
            self.call(retro=retro)
    def test_10_stage3_wrong_canonical_club_rejected(self):
        scope=copy.deepcopy(self.scope)
        scope["verified_fixtures"][0]["home_identity"]["canonical_team_id"]="FICTITIOUS_ID"
        with self.assertRaisesRegex(PreflightError,"PREMATCH_CANONICAL_CLUB_ID_MISMATCH"):
            self.call(scope=scope)
    def test_11_stage5_source_elo_identity_swap_rejected(self):
        stage5=copy.deepcopy(self.s5)
        stage5["matches"][0]["home_team"]["canonical_team_id"]="ANOTHER_ID"
        with self.assertRaisesRegex(PreflightError,"PREMATCH_CANONICAL_CLUB_ID_MISMATCH"):
            self.call(stage5=stage5)
    def test_12_future_same_day_results_rejected(self):
        stage4=copy.deepcopy(self.s4)
        stage4["fixtures"][0]["domestic_home"]["recent_5"][-1]["date"]="2026-11-03"
        with self.assertRaisesRegex(PreflightError,"RECENT_MATCH_DATE_LEAK_OR_OPPONENT_UNKNOWN"):
            self.call(stage4=stage4)
    def test_13_news_is_never_a_numeric_modifier(self):
        stage5=copy.deepcopy(self.s5)
        for m in stage5["matches"]:
            for side in ("home_team","away_team"):
                stage5_row=m[side]["news"]
                stage5_row["reported_out"]=["UNVERIFIED_PLAYER_NEVER_USE"]
                stage5_row["reported_doubtful"]=["ANOTHER_UNVERIFIED_PLAYER"]
        # Algebra must be *identical*; news is not consulted to construct pair.
        original=make_pair(self.s4["fixtures"][0],self.s5["matches"][0],self.scope["verified_fixtures"][0])
        changed=make_pair(self.s4["fixtures"][0],stage5["matches"][0],self.scope["verified_fixtures"][0])
        self.assertEqual(
            compute_volatile(original,self.home_mean,self.away_mean,self.beta),
            compute_volatile(changed,self.home_mean,self.away_mean,self.beta))
    def test_14_retro_beta_or_train_goal_base_cannot_be_silently_refitted(self):
        retro=copy.deepcopy(self.retro)
        retro["fixed_protocol"]["beta_retrospective_fitted"]*=1.01
        with self.assertRaisesRegex(PreflightError,"UNEXPECTED_HISTORIC_BASE_OR_EXPLORATORY_BETA"):
            self.call(retro=retro)

if __name__=="__main__":unittest.main()
