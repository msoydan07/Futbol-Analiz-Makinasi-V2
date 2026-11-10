"""Synthetic edge cases plus one bounded real 4617 score-only file audit."""
from __future__ import annotations
import copy
import sys
import unittest
from datetime import date,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from team_coverage_audit_263 import (
    AuditBlocked,audit,effective_n,matchup_check,team_profile,load_verified_prematch)
sys.path.insert(0,str(ROOT/"experiments/263"))
from m4_integrated import predict_m4
import numpy as np

DAY="2026-11-11"
def row(i,home="A",away="B",when="2026-11-10",season="2026-2027"):
    return {"fixture_id":f"fixture_{i}","league":"ENG1","match_date":when,"season":season,
            "home_id":home,"away_id":away,"home_goals":"1","away_goals":"0","result":"H"}

class TeamCoverageResearchTests(unittest.TestCase):
    def test_zero_existing_history_team_must_be_flagged(self):
        profile=team_profile([row(1)],"ENG1","NEW_TEAM","home",DAY)
        self.assertEqual(profile["coverage_grade"],"UNSEEN")
        self.assertIn("UNSEEN_TEAM_M4_LEAGUE_BASELINE_FALLBACK",profile["flags"])
        self.assertFalse(profile["high_confidence_certified"])
    def test_m4_zero_vector_fallback_for_missing_team_is_real_and_surfaced(self):
        beta=np.zeros(2+6*2,dtype=float)
        fit=(beta,{"A":0,"B":1},2,80)
        # Actual frozen M4 returns probabilities for an unknown team.
        result=predict_m4(fit,"NOT_IN_DATA","B")
        self.assertIsNotNone(result)
        self.assertEqual(result,(1.0,1.0))
        diag=team_profile([row(1)],"ENG1","NOT_IN_DATA","home",DAY)
        self.assertEqual(diag["coverage_grade"],"UNSEEN")
    def test_current_season_context_less_than_four_detected(self):
        past=[row(i,"HOME",f"V{i}",when="2026-10-2"+str(i)) for i in range(4)]
        profile=team_profile(past,"ENG1","HOME","home",DAY)
        self.assertEqual(profile["current_season_role_matches"],4)
        self.assertNotIn("CURRENT_SEASON_ROLE_LT4",profile["flags"])
        # One fewer game is diagnostically thin.
        reduced=team_profile(past[:3],"ENG1","HOME","home",DAY)
        self.assertIn("CURRENT_SEASON_ROLE_LT4",reduced["flags"])
    def test_all_history_venue_but_no_current_season_is_marked(self):
        past=[row(i,home="HOME",away=f"V{i}",when="2026-04-02",season="2025-2026")
              for i in range(10)]
        profile=team_profile(past,"ENG1","HOME","home",DAY)
        self.assertIn("NO_CURRENT_SEASON_MATCH",profile["flags"])
        self.assertIn("LAST_MATCH_MORE_THAN_60_DAYS_OLD",profile["flags"])
        self.assertEqual(profile["historical_role_matches"],10)
        self.assertNotIn("HISTORICAL_ROLE_LT8",profile["flags"])
    def test_role_not_confused_with_general_team_history(self):
        past=[row(i,"A","B",when="2026-10-10") for i in range(12)]
        away=team_profile(past,"ENG1","A","away",DAY)
        self.assertEqual(away["historical_all_matches"],12)
        self.assertEqual(away["historical_role_matches"],0)
        self.assertIn("HISTORICAL_ROLE_LT8",away["flags"])
        self.assertIn("CURRENT_SEASON_ROLE_LT4",away["flags"])
    def test_data_from_future_date_forbidden(self):
        with self.assertRaisesRegex(AuditBlocked,"HISTORY_NOT_SCOPED"):
            team_profile([row(1,when="2026-11-12")],"ENG1","A","home",DAY)
        with self.assertRaisesRegex(AuditBlocked,"HISTORY_NOT_SCOPED"):
            team_profile([row(1,when=DAY)],"ENG1","A","home",DAY)
    def test_decayed_effective_n_is_bounded_not_fake_team_probability(self):
        self.assertEqual(effective_n([]),0)
        self.assertAlmostEqual(effective_n([10]*8),8)
        self.assertLess(effective_n([2,10,40,100,200]),5)
    def test_matchup_diagnostic_uses_both_roles_and_no_live_fixture_claim(self):
        past=[row(i,home=f"H{i%4}",away=f"A{i%5}",when="2026-10-10")
              for i in range(65)]
        o=matchup_check(past,"ENG1","UNKNOWN","A1",DAY)
        self.assertTrue(o["has_unseen_team"])
        self.assertFalse(o["not_a_verified_live_fixture"] is False)
        self.assertTrue(o["use_original_M4_probabilities_unchanged"])
        self.assertEqual(o["home"]["coverage_grade"],"UNSEEN")
        self.assertNotEqual(o["away"]["coverage_grade"],"UNSEEN")
    def test_all_ten_league_real_scores_and_one_shortened_match_excluded(self):
        x=audit(DAY)
        self.assertEqual(x["leagues"],10)
        self.assertEqual(x["eligible_90min_history_rows"],4616)
        self.assertEqual(x["excluded_awarded_early_finish"],1)
        self.assertTrue(x["model_or_seals_modified"] is False)
        self.assertEqual(set(z["league"] for z in x["findings"]),
            {"ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1"})
        self.assertTrue(all(z["active_current_season_teams"]>0 for z in x["findings"]))
        for z in x["findings"]:
            for side in ("home","away"):
                c=z["coverage_by_role"][side]
                self.assertLessEqual(c["current_season_role_lt4"],c["active_team_count"])
                self.assertEqual(c["active_team_count"],z["active_current_season_teams"])

if __name__=="__main__":
    unittest.main()
