"""Focused NEW stage7 tests; previous Stage6 14 checks are not rerun."""
from __future__ import annotations
import copy
import json
import math
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from uefa_nov3_5_stage7_independent_qa_263 import (
    independent_model,poisson_independent,index_key,checked,
    check_profile,QualityError,audit,points,side)
from uefa_nov3_5_stage6_shadow_math_preflight_263 import compute_volatile

PROTO={
    "k_smoothing":5.0,
    "UEFA_train_home_goal_mean":135/76,
    "UEFA_train_away_goal_mean":101/76,
}
def team(elo, h_scored=7,h_conceded=3,a_scored=4,a_conceded=5):
    return {"elo":elo,"profile":{
        "domestic_home_goals_scored":h_scored,
        "domestic_home_goals_conceded":h_conceded,
        "domestic_away_goals_scored":a_scored,
        "domestic_away_goals_conceded":a_conceded,
        "past_domestic_home_games":4,"past_domestic_away_games":4,
        "domestic_league_home_goals_per_game_before_target":1.6,
        "domestic_league_away_goals_per_game_before_target":1.1,
        "team_id":str(elo),
    }}
class IndependentQATests(unittest.TestCase):
    def setUp(self):
        self.pair={"home":team(1850),"away":team(1810)}
    def test_01_math_wide_grid_has_unit_1x2_mass(self):
        for h in (.15,.55,1.0,1.75,3.5,4.9,5.0):
            for a in (.15,.8,1.2,2.7,5.0):
                p,over,btts,loss=poisson_independent(h,a)
                self.assertAlmostEqual(sum(p),1,places=12)
                self.assertLess(loss,1e-12)
                self.assertTrue(0<=over<=1 and 0<=btts<=1)
    def test_02_independent_over25_equals_closed_form(self):
        for h,a in ((.2,1.0),(1.8,2.1),(5.0,5.0)):
            _,over,_,_=poisson_independent(h,a)
            m=h+a
            self.assertAlmostEqual(over,1-math.exp(-m)*(1+m+m*m/2),places=12)
    def test_03_btts_independent_closed_form(self):
        for h,a in ((.15,.15),(2,1),(4.7,1.5)):
            _,_,btts,_=poisson_independent(h,a)
            self.assertAlmostEqual(btts,
                (1-math.exp(-h))*(1-math.exp(-a)),places=12)
    def test_04_swapped_lambda_swaps_win_probability(self):
        p,_,_,_=poisson_independent(2.5,1)
        q,_,_,_=poisson_independent(1,2.5)
        self.assertAlmostEqual(p[0],q[2],places=12)
        self.assertAlmostEqual(p[1],q[1],places=12)
    def test_05_equal_lambda_gives_equal_home_away_win_probability(self):
        p,_,_,_=poisson_independent(2.2,2.2)
        self.assertAlmostEqual(p[0],p[2],places=12)
    def test_06_elo_zero_diff_reduces_to_M0(self):
        pair=copy.deepcopy(self.pair)
        pair["away"]["elo"]=pair["home"]["elo"]
        self.assertEqual(independent_model(pair,PROTO,0),
                         independent_model(pair,PROTO,.5254760017675575))
    def test_07_positive_elo_diff_increases_home_and_reduces_away_lambda(self):
        base=independent_model(self.pair,PROTO,0)
        plus=independent_model(self.pair,PROTO,.5254760017675575)
        self.assertGreater(plus[0],base[0])
        self.assertLess(plus[1],base[1])
    def test_08_elo_only_secondary_modifier_no_change_to_M0(self):
        base=independent_model(self.pair,PROTO,0)
        pair=copy.deepcopy(self.pair)
        pair["away"]["elo"]=2700
        self.assertEqual(base,independent_model(pair,PROTO,0))
    def test_09_independent_vs_unchanged_retro_on_synthetic_input(self):
        from uefa_nov3_5_stage6_shadow_math_preflight_263 import compute_volatile
        for beta in (0,.5254760017675575):
            expected=independent_model(self.pair,PROTO,beta)
            out=compute_volatile(self.pair,PROTO["UEFA_train_home_goal_mean"],
                                 PROTO["UEFA_train_away_goal_mean"],.5254760017675575)
            actual=out["M0" if beta==0 else "M0Elo"][:2]
            self.assertLess(max(abs(a-b) for a,b in zip(expected,actual)),1e-12)
    def test_10_hash_modified_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"stage4.json"
            path.write_text('{"x":1}',encoding="utf8")
            with self.assertRaisesRegex(QualityError,"FROZEN_EVIDENCE_SHA_CHANGED"):
                checked(path,"0"*64)
    def test_11_normalizer_rejects_false_fuzzy_merge(self):
        self.assertEqual(index_key("FENERBAHÇE A.Ş."),index_key("Fenerbahçe AŞ"))
        self.assertNotEqual(index_key("Union SG"),index_key("Union Berlin"))
        self.assertNotEqual(index_key("Real Sociedad"),index_key("Real Madrid"))
    def test_12_wrong_role_fixture_is_invalid(self):
        match={"h":"a","a":"b","gh":2,"ga":1}
        with self.assertRaisesRegex(QualityError,"CLUB_ABSENT_FROM_RESULT"):
            side(match,"c")
        self.assertEqual(points(3,1),3)
        self.assertEqual(points(1,1),1)
        self.assertEqual(points(0,1),0)
    def test_13_bad_stage6_summary_not_promoted(self):
        invalid={"status":"CLAIMS_ALREADY_APPROVED"}
        with self.assertRaisesRegex(QualityError,"FROZEN_STAGE6_SUMMARY_INCONSISTENT"):
            audit({},{},{},invalid,{}, {}, "/never-read")
    def test_14_never_turn_retro_source_into_model_acceptance(self):
        stage6={"status":"17_OF_17_VOLATILE_SHADOW_MATH_INVARIANTS_PASSED_NO_FORECAST_RECORD",
                "matches_tested":17,"unique_teams_tested":34,
                "any_per_match_lambda_or_probability_saved":False,
                "mathematical_calibration_or_main_approval":False}
        stage4={"fixture_status_counts":{"DESCRIPTIVE_GOAL_PROFILE_SOURCE_READY":17}}
        stage5={"coverage":{"matches":17,"news_el_secondary_provisional_team_reports":10,
                            "confirmed_starting_XIs":0}}
        retro={"Elo_weight_approved_for_model":True,
               "historical_rating_first_seen_verified":False}
        with self.assertRaisesRegex(QualityError,"PREVIOUS_EXPLORATORY_DATA_STATUS_MUST_REMAIN_UNAPPROVED"):
            audit(stage4,stage5,retro,stage6,{}, {},"/never-read")

if __name__=="__main__":unittest.main()
