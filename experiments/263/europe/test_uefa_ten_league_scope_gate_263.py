"""Focused NEW European ten-league gate tests; no model/pilot/backtest runs."""
import copy
import json
import unittest
from pathlib import Path
from uefa_ten_league_scope_gate_263 import (
    check_europe_scope,preflight_then,ScopeGateError,LEAGUES
)
INDEX=Path("experiments/263/evidence/identity_index_263.json")
class ScopeFirst(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.index=json.loads(INDEX.read_text(encoding="utf-8"))
    def test_ten_exact_leagues_are_unchanged(self):
        self.assertEqual(set(self.index["season_memberships"]["2026-2027"]),set(LEAGUES))
        self.assertEqual(len(LEAGUES),10)
    def test_galatasaray_vs_barcelona_passes_scope_only(self):
        x=check_europe_scope("Galatasaray","Barcelona",self.index)
        self.assertTrue(x["allow_further_research"])
        self.assertEqual(x["home"]["current_ten_league_membership"],["TUR1"])
        self.assertEqual(x["away"]["current_ten_league_membership"],["ESP1"])
        self.assertFalse(x["official_match_verified"])
        self.assertFalse(x["model_forecast_authorized"])
    def test_aston_villa_vs_fenerbahce_passes_scope_only(self):
        x=check_europe_scope("Aston Villa","Fenerbahçe",self.index)
        self.assertTrue(x["allow_further_research"])
        self.assertEqual(x["home"]["current_ten_league_membership"],["ENG1"])
        self.assertEqual(x["away"]["current_ten_league_membership"],["TUR1"])
    def test_celtic_not_in_index_causes_stop_before_any_research(self):
        calls=[]
        decision,payload=preflight_then("Galatasaray","Celtic",self.index,
                                         lambda x:calls.append(x))
        self.assertEqual(decision["status"],"ANALYSIS_SKIPPED_TEAM_SCOPE_UNVERIFIED")
        self.assertFalse(decision["allow_further_research"])
        self.assertEqual(calls,[])
        self.assertIsNone(payload)
    def test_known_team_no_longer_current_is_outside_scope(self):
        # Leicester is present in identity cache historically but NOT in the
        # current 2026/27 ten-league membership. Never use past season instead.
        x=check_europe_scope("Galatasaray","Leicester",self.index)
        self.assertEqual(x["status"],"ANALYSIS_SKIPPED_OUTSIDE_TEN_LEAGUES")
        self.assertEqual(x["away"]["state"],"NOT_IN_CURRENT_TEN_LEAGUES")
        self.assertIn("kapsam dışı",x["message"])
    def test_wrong_uefa_spelling_is_not_guessed_or_fuzzily_approved(self):
        x=check_europe_scope("FC Barcelona (ESP)","Galatasaray",self.index)
        self.assertFalse(x["allow_further_research"])
        self.assertEqual(x["status"],"ANALYSIS_SKIPPED_TEAM_SCOPE_UNVERIFIED")
    def test_when_both_eligible_only_then_do_downstream_once(self):
        calls=[]
        decision,result=preflight_then("Galatasaray","Aston Villa",self.index,
                                       lambda scope:(calls.append(scope["version"]) or "READY"))
        self.assertEqual(len(calls),1)
        self.assertEqual(result,"READY")
        self.assertTrue(decision["allow_further_research"])
    def test_index_validation_refuses_missing_domestic_league(self):
        bad=copy.deepcopy(self.index)
        del bad["season_memberships"]["2026-2027"]["ENG2"]
        with self.assertRaisesRegex(ScopeGateError,"UNIVERSE_CHANGED"):
            check_europe_scope("Galatasaray","Barcelona",bad)
    def test_same_team_rejected(self):
        with self.assertRaisesRegex(ScopeGateError,"SAME_TEAM"):
            check_europe_scope("Galatasaray","Galatasaray",self.index)
    def test_no_side_effect_or_mutation_of_identity_index(self):
        data=copy.deepcopy(self.index)
        check_europe_scope("Aston Villa","Galatasaray",self.index)
        self.assertEqual(data,self.index)
if __name__=="__main__":unittest.main()
