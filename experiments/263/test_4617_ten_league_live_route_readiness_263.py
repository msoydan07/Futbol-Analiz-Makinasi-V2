"""All 10 league 4617 result-only route acceptance, without real fixtures or bets.

A controlled temporary fake gate tests computation only; this does NOT certify
live official provider availability, rights, or all original source scores.
"""
import collections
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from exp_263_batch import clean_rows
from forward_quad import predict_quad_from_verified_gate
from forward_empirical_baseline_263 import produce
from four_model_value_policy_263 import decide
from full_match_eligibility_263 import full_match_rows
from market_fifth_baseline_263 import sealed_payload

ROOT=Path(__file__).resolve().parents[2]
NEW=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
OLD=ROOT/"data/quad_accepted_263/extended_history.csv"
MANIFEST=ROOT/"data/results_only_263/4617_research_input_provenance.json"
BASE=ROOT/"m4_quad_base/historical_results.csv"
LOCK=ROOT/"experiments/263/m4_lock.json"
DEVLOCK=ROOT/"experiments/263/forward_dev_calibration_lock_263.json"
LEAGUES={"ENG1":10,"ENG2":15,"GER1":9,"ESP1":10,"ITA1":10,"FRA1":9,"NED1":9,"TUR1":9,"POR1":8,"BEL1":10}
ASOF=datetime(2026,11,11,9,0,tzinfo=timezone.utc)
GOAL_MARKETS=("BTTS_YES","BTTS_NO","OVER_1.5","UNDER_1.5",
              "OVER_2.5","UNDER_2.5","OVER_3.5","UNDER_3.5")

class TenLeagueRealHistoryNoRealFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BASE.is_file():raise RuntimeError("REQUIRED_ORIGINAL_4413_BASELINE_UNAVAILABLE")
        cls.old=clean_rows(OLD)
        cls.new=clean_rows(NEW)
        cls.old_ids={r["fixture_id"] for r in cls.old}
        cls.new_only=[r for r in cls.new if r["fixture_id"] not in cls.old_ids]

    def test_all_10_new_score_counts_and_zero_advanced_stats(self):
        self.assertEqual(len(self.old),4518)
        self.assertEqual(len(self.new),4617)
        self.assertEqual(len(self.new_only),99)
        self.assertEqual(dict(collections.Counter(r["league"] for r in self.new_only)),LEAGUES)
        self.assertTrue(all(r["match_date"]<"2026-11-11" for r in self.new_only))
        raw={r["fixture_id"]:r for r in self.new}
        for r in self.old:
            self.assertEqual(raw[r["fixture_id"]],r)
        for r in self.new_only:
            self.assertTrue(all(not r[col] for col in (
                "half_time_home_goals","half_time_away_goals",
                "home_shots","away_shots","home_corners","away_corners")))
            self.assertTrue(r["home_goals"].isdigit() and r["away_goals"].isdigit())
        p=json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(p["official_unique_match_id_verified"])
        self.assertFalse(p["human_official_review_of_all_99"])
        self.assertFalse(p["betting_authorized"])

    def test_all_10_league_m4_and_three_other_models_use_correct_new_data(self):
        import os
        old_history=collections.Counter(r["league"] for r in self.old if r["match_date"]<"2026-11-11")
        new_history=collections.Counter(r["league"] for r in self.new if r["match_date"]<"2026-11-11")
        for league,added in LEAGUES.items():
            with self.subTest(league=league):
                self.assertEqual(new_history[league]-old_history[league],added)
                fixture_candidates=[r for r in self.new if r["league"]==league and r["match_date"]<"2026-11-11"]
                test_fixture=fixture_candidates[-1]
                gate={"status":"VERIFIED","league":league,
                      "home_id":test_fixture["home_id"],
                      "away_id":test_fixture["away_id"],
                      "kickoff_utc":"2026-11-11T17:00:00+00:00",
                      "retrieved_at_utc":ASOF.isoformat(),
                      "source_url":"https://example.com/TEST_ONLY_NEVER_OFFICIAL"}
                with tempfile.TemporaryDirectory() as tmp:
                    forecast_path,forecast=predict_quad_from_verified_gate(
                        gate,NEW,Path(tmp),LOCK,now=ASOF,base=BASE,source_audit=MANIFEST)
                    self.assertTrue(forecast_path.is_file())
                    sealed_payload(forecast,"quad_forward_263_v1")
                    self.assertEqual(forecast["data"]["snapshot_acceptance"],
                                     "APPEND_ONLY_4617_PUBLIC_RESULTS_ONLY_RESEARCH_NOT_OFFICIAL_ID_VERIFIED")
                    self.assertFalse(forecast["data"]["human_source_acceptance"])
                    self.assertFalse(forecast["data"]["research_shadow_unverified_source"])
                    self.assertEqual(forecast["data"]["snapshot_sha256"],
                                     "637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89")
                    self.assertEqual(set(forecast["model_predictions"]),{"B","C2","C3","M4"})
                    self.assertEqual(forecast["model_predictions"]["M4"]["status"],"AVAILABLE")
                    eligible,excluded,sha=full_match_rows(fixture_candidates)
                    self.assertEqual(forecast["model_predictions"]["M4"]["train_rows"],len(eligible))
                    self.assertEqual(forecast["data"]["training_excluded_partial_match_ids"],excluded)
                    for name in ("B","C2","C3","M4"):
                        prediction=forecast["model_predictions"][name]
                        if prediction["status"]!="AVAILABLE":
                            # Missing context is reported, never filled from another model.
                            self.assertIn(prediction["status"],(
                                "UNAVAILABLE","UNAVAILABLE_INSUFFICIENT_CONTEXT",
                                "UNAVAILABLE_FIT_OR_TAIL"))
                            continue
                        m=prediction["goals"]["markets"]
                        self.assertAlmostEqual(sum(m["1X2"].values()),1.0,places=7)
                        for left,right in (("BTTS_YES","BTTS_NO"),
                                           ("OVER_1.5","UNDER_1.5"),
                                           ("OVER_2.5","UNDER_2.5"),
                                           ("OVER_3.5","UNDER_3.5")):
                            self.assertAlmostEqual(m[left]+m[right],1.0,places=7)
                        self.assertTrue(all(0<=m[market]<=1 for market in GOAL_MARKETS))
                    b=produce(forecast,NEW,now=ASOF)
                    self.assertEqual(b["historical_match_count"],len(eligible))
                    self.assertEqual(b["source_snapshot_sha256"],
                                     forecast["data"]["snapshot_sha256"])
                    self.assertEqual(b["last_result_date"],forecast["data"]["league_latest_result_date"])
                    decision=decide(forecast,b,json.loads(DEVLOCK.read_text(encoding="utf-8")),
                                    observation=None,now=ASOF)
                    self.assertEqual(decision["status"],"RESEARCH_PAS")
                    self.assertIsNone(decision["main_candidate"])
                    self.assertFalse(decision["betting_authorized"])
                    self.assertEqual(decision["forecast_sha256"],forecast["payload_sha256"])

if __name__=="__main__":
    unittest.main()
