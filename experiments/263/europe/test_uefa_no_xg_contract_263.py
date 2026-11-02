"""Only NEW Europe no-xG scope and input-contract checks; no old model tests."""
import json,unittest
from datetime import datetime
from pathlib import Path
from uefa_no_xg_contract_263 import (
    RESEARCH_FIELDS,key_forbidden,validate_research_facts,
    user_requested_europe_without_xg,XGPolicyViolation,POLICY,
)
IDX=json.loads(Path("experiments/263/evidence/identity_index_263.json").read_text(encoding="utf8"))
NOW=datetime.fromisoformat("2026-11-02T18:00:00+03:00")
class NoXGEuropeTests(unittest.TestCase):
    def call(self,away="Barcelona",collector=None,home="Galatasaray"):
        return user_requested_europe_without_xg("UEFA_CL",home,away,
            "2026-11-03","21:00",index=IDX,now=NOW,collector=collector)
    def test_all_active_research_features_are_xg_free(self):
        self.assertTrue(all(not key_forbidden(x) for x in RESEARCH_FIELDS))
        self.assertFalse(any("xg" in x for x in RESEARCH_FIELDS))
    def test_reject_any_xg_both_clubs_even_if_available(self):
        for name in ("home_xg","away_xg","xGA","non_penalty_npxg",
                     "PSxG","expected_goals","expectedGoals"):
            with self.subTest(name=name):
                self.assertTrue(key_forbidden(name))
    def test_xg_missing_not_failure(self):
        gate,_=self.call()
        policy=gate["europe_research_policy"]
        self.assertTrue(gate["data_research_allowed"])
        self.assertEqual(policy["version"],POLICY)
        self.assertFalse(policy["missing_xg_is_data_defect"])
        self.assertFalse(policy["xg_and_xga_research_allowed"])
    def test_collector_is_only_asked_for_allowed_keys(self):
        calls=[]
        def source(request,*,fields):
            calls.append(tuple(fields))
            return {"completed_goals_for_against":{"home":{"goals":9},
                "away":{"goals":7},"source_name":"fake test only"}}
        gate,facts=self.call(collector=source)
        self.assertEqual(calls,[RESEARCH_FIELDS])
        self.assertTrue(gate["data_research_allowed"])
        self.assertIn("completed_goals_for_against",facts)
    def test_nested_xg_cannot_sneak_through(self):
        def fake(_,*,fields):
            return {"completed_goals_for_against":{"home":{"xG":1.6},"away":{"goals":1}}}
        with self.assertRaisesRegex(XGPolicyViolation,"XG_FIELD"):
            self.call(collector=fake)
    def test_unreviewed_arbitrary_feature_blocked(self):
        with self.assertRaisesRegex(XGPolicyViolation,"UNREVIEWED_EXTERNAL_FIELD"):
            validate_research_facts({"unreviewed_opponent_strength_scaler":1.5})
    def test_scope_outside_ten_stops_before_collector(self):
        called=[]
        g,f=self.call(away="Celtic",collector=lambda *a,**k:called.append(1))
        self.assertFalse(g["data_research_allowed"])
        self.assertEqual(called,[])
        self.assertIsNone(f)
    def test_lambda_prediction_is_not_observed_xg(self):
        self.assertFalse(key_forbidden("lambda_home"))
        self.assertFalse(key_forbidden("lambda_away"))
        self.assertFalse(key_forbidden("poisson_goal_rate"))
        self.assertTrue(key_forbidden("model_based_xg_from_odds"))
    def test_no_direct_model_predictions_or_pilot_registration(self):
        gate,_=self.call()
        self.assertFalse(gate["model_predictions_approved"])
        self.assertFalse(gate["pilot_registration_allowed"])
    def test_xg_free_fields_never_require_xg_availability(self):
        v=validate_research_facts({"domestic_home_away_goal_results":
             {"home":[1,0,2],"away":[0,1,1],"verified":True}})
        self.assertTrue(v)
    def test_non_callable_collector_fails_closed(self):
        with self.assertRaisesRegex(XGPolicyViolation,"TRUSTED_COLLECTOR"):
            self.call(collector={})
    def test_no_xg_in_meta_keys(self):
        with self.assertRaisesRegex(XGPolicyViolation,"XG_FIELD"):
            validate_research_facts({"status":"ok","notes":{"away_xga":"missing"}})
if __name__=="__main__":unittest.main()
