"""New protocol-only guards. No source re-fetch or previous test replay."""
import copy,json,unittest
from pathlib import Path
from uefa_xg_free_model_comparison_prereg_263 import validate_plan,evaluate_protocol,ProtocolError
PLAN=json.loads(Path("experiments/263/evidence/uefa_xg_free_m0_m1_m2_prereg_2026_11_02.json").read_text())
def fake():
    official={"schema":"263_UEFA_2025_26_CL_EL_132_OFFICIAL_MATCH_ID_SOURCE_REVIEW_V1",
              "status":"REVIEW_ONLY_NO_MODEL","model_training_permitted":False,"matches":[]}
    goals={"schema":"263_UEFA_GOL_ONLY_ASOF_FEATURE_READINESS_V1",
           "status":"REVIEW_ONLY_NO_MODEL","training_permitted":False,"matches":[]}
    for i in range(132):
        if i<60:cup="UEFA_CL";day="2025-10-01"
        elif i<84:cup="UEFA_EL";day="2025-10-02"
        elif i<96:cup="UEFA_CL";day="2025-12-10"
        elif i<100:cup="UEFA_EL";day="2025-12-11"
        elif i<123:cup="UEFA_CL";day="2026-01-21"
        else:cup="UEFA_EL";day="2026-01-22"
        official["matches"].append({"uefa_official_match_id":i+1,"competition":cup,"date":day,
                                   "home_id_candidate":"H","away_id_candidate":"A",
                                   "model_eligible":False})
        goals["matches"].append({"uefa_official_match_id":i+1,"competition":cup,
                                 "target_date":day,"team_goals_inputs":{
                                   "home":{"canonical_team_id":"H"},
                                   "away":{"canonical_team_id":"A"}},
                                 "training_or_pilot_allowed":False,
                                 "asof_source_publication_time_proven":False,
                                 "global_league_strength_scale_validated":False,
                                 "both_4_plus_domestic_results":i<124,
                                 "both_have_2_each_home_away":i<124,
                                 "both_leagues_have_30_plus_past_games":i<124})
    return official,goals
class ProtocolGuardTests(unittest.TestCase):
    def test_exact_frozen_specification(self):
        self.assertEqual(len(validate_plan(PLAN)),3)
    def test_synthetic_84_16_32_only_no_model(self):
        o,g=fake();r,_=evaluate_protocol(PLAN,o,g)
        self.assertEqual([r["splits"][k]["source_candidates"] for k in ("train","validation","holdout")],[84,16,32])
        self.assertFalse(r["1X2_or_goal_probabilities_generated"])
        self.assertFalse(r["historical_prematch_provenance_verified"])
    def test_refuse_date_change_outcome_leak(self):
        o,g=fake();o["matches"][0]["date"]="2026-01-22"
        with self.assertRaisesRegex(ProtocolError,"MATCH_ID_DATE"):
            evaluate_protocol(PLAN,o,g)
    def test_refuse_unequal_team_orientation(self):
        o,g=fake();o["matches"][0]["home_id_candidate"]="A"
        with self.assertRaisesRegex(ProtocolError,"TEAM_ID"):
            evaluate_protocol(PLAN,o,g)
    def test_refuse_pairwise_missing_fixture(self):
        o,g=fake();g["matches"].pop()
        with self.assertRaisesRegex(ProtocolError,"REVIEW_INPUTS_NOT_132"):
            evaluate_protocol(PLAN,o,g)
    def test_no_xg_and_h2h_policy_bypass(self):
        p=copy.deepcopy(PLAN);p["candidate_policy"]["xg_xga_xg_proxies_banned_for_both_sides"]=False
        with self.assertRaisesRegex(ProtocolError,"XG_POLICY"):
            validate_plan(p)
        p=copy.deepcopy(PLAN);p["candidate_policy"]["h2h_banned"]=False
        with self.assertRaisesRegex(ProtocolError,"H2H_POLICY"):
            validate_plan(p)
    def test_no_auto_promotion(self):
        p=copy.deepcopy(PLAN);p["decision_rules"]["auto_promote_to_main"]=True
        with self.assertRaisesRegex(ProtocolError,"NO_AUTOMATIC_PROMOTION"):
            validate_plan(p)
    def test_no_new_season_false_claim(self):
        p=copy.deepcopy(PLAN);p["split"]["new_untouched_season_test_available"]=True
        with self.assertRaisesRegex(ProtocolError,"UNTOUCHED_TEST"):
            validate_plan(p)
    def test_no_outcome_is_consumed_by_protocol(self):
        o,g=fake();s,_=evaluate_protocol(PLAN,o,g)
        for m in o["matches"]:m["home_goals"]=20;m["away_goals"]=0
        t,_=evaluate_protocol(PLAN,o,g)
        self.assertEqual(s,t)
if __name__=="__main__":unittest.main()
