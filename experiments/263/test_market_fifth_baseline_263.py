"""All prices and fixtures below are synthetic; NEVER a live bookmaker quote."""
import hashlib
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from classification_odds_263 import poisson_market
from forward_c3 import canonical_bytes
from forward_quad import SCHEMA
from market_fifth_baseline_263 import (
    OBSERVATION_SCHEMA, evaluate_pair, sealed_payload, summarize, _score, _result_side
)

KO = datetime(2026, 11, 6, 17, 0, tzinfo=timezone.utc)
CREATED = KO - timedelta(hours=1)
ANALYSIS = KO - timedelta(minutes=55)
EVALUATED = KO + timedelta(hours=3)
KEY = "TUR1:HOME:AWAY:2026-11-06"


def seal(x):
    out = deepcopy(x)
    out["payload_sha256"] = hashlib.sha256(canonical_bytes(out)).hexdigest()
    return out


def inputs():
    m = poisson_market(1.6, 0.6)
    pred = {name: {"status": "AVAILABLE", "goals": {"markets": deepcopy(m)}}
            for name in ("B", "C2", "C3", "M4")}
    forecast = seal({
        "schema": SCHEMA, "created_at_utc": CREATED.isoformat(),
        "fixture": {"league":"TUR1", "home_id":"HOME", "away_id":"AWAY",
                    "kickoff_utc":KO.isoformat(), "match_local_date":"2026-11-06",
                    "fixture_verification":"VERIFIED_BY_LIVE_OFFICIAL_GATE",
                    "source_checked_at_utc":(CREATED-timedelta(minutes=2)).isoformat()},
        "model_predictions": pred,
    })
    quote = {
        "fixture_key":KEY, "market_group":"MS",
        "verification":"INDEPENDENTLY_CHECKED", "stage":"PREMATCH",
        "source":"example.org", "source_url":"https://example.org/mock",
        "checked_at_utc":(ANALYSIS-timedelta(minutes=1)).isoformat(),
        "decimal_odds":{"MS1":1.6, "MSX":4.0, "MS2":6.0},
    }
    obs = seal({
        "schema":OBSERVATION_SCHEMA, "fixture_key":KEY,
        "forecast_payload_sha256":forecast["payload_sha256"],
        "analysis_at_utc":ANALYSIS.isoformat(),
        "source_domain":"example.org",
        "source_review":{"method":"MANUAL_PUBLIC_PAGE", "reviewer":"synthetic-tester",
                         "reviewed_at_utc":ANALYSIS.isoformat()},
        "quotes":{"MS":quote},
    })
    final={"home_goals":2,"away_goals":1,
           "source_url":"https://example.org/mock-final",
           "finalized_at_utc":(KO+timedelta(hours=2)).isoformat()}
    return forecast,obs,final


def calc(f=None,o=None,r=None):
    a,b,c=inputs()
    return evaluate_pair(forecast=f if f is not None else a,
                         observation=o if o is not None else b,
                         final=r if r is not None else c,
                         asof=EVALUATED.isoformat())


class FifthMarketBaselineChecks(unittest.TestCase):
    def test_fifth_reference_compares_on_same_match(self):
        p=calc()
        self.assertEqual(p["groups"]["MS"]["status"],"DESCRIPTIVE_MATCHED_PAIR_NOT_LIVE_VERIFIED")
        self.assertEqual(set(p["groups"]["MS"]["scores"]),{"MARKET","B","C2","C3","M4"})
        self.assertAlmostEqual(sum(p["groups"]["MS"]["no_vig"].values()),1)
        self.assertFalse(p["S1_S2_approved"])

    def test_missing_markets_are_not_fabricated(self):
        p=calc()
        self.assertEqual(p["groups"]["KG"]["status"],"NO_SNAPSHOT_FOR_THIS_MARKET")
        self.assertEqual(p["groups"]["GOALS_1.5"]["status"],"NO_SNAPSHOT_FOR_THIS_MARKET")
        self.assertEqual(p["groups"]["GOALS_2.5"]["status"],"NO_SNAPSHOT_FOR_THIS_MARKET")
        self.assertEqual(p["groups"]["GOALS_3.5"]["status"],"NO_SNAPSHOT_FOR_THIS_MARKET")
        self.assertEqual(summarize([p])["markets"]["KG"]["quotes_complete_n"],0)

    def test_same_match_paired_scores_and_unavailable_model(self):
        f,o,r=inputs()
        f.pop("payload_sha256")
        f["model_predictions"]["C2"]={"status":"UNAVAILABLE","reason":"sample"}
        f=seal(f)
        o.pop("payload_sha256")
        o["forecast_payload_sha256"]=f["payload_sha256"]
        o=seal(o)
        out=summarize([calc(f,o,r)])
        self.assertEqual(out["markets"]["MS"]["scores"]["C2"]["n"],0)
        self.assertEqual(out["markets"]["MS"]["same_match_comparison"]["M4"]["matched_n"],1)

    def test_modified_forecast_refused(self):
        f,o,r=inputs()
        f["fixture"]["home_id"]="WRONG"
        with self.assertRaisesRegex(ValueError,"TAMPERED"): calc(f,o,r)

    def test_observation_linked_to_wrong_forecast_refused(self):
        f,o,r=inputs()
        o.pop("payload_sha256")
        o["forecast_payload_sha256"]="a"*64
        with self.assertRaisesRegex(ValueError,"SEALED_SHA_MISSING|WRONG_FORECAST"):
            calc(f,seal(o),r)

    def test_changed_quote_detected(self):
        f,o,r=inputs()
        o["quotes"]["MS"]["decimal_odds"]["MS1"]=3.0
        with self.assertRaisesRegex(ValueError,"TAMPERED"):calc(f,o,r)

    def test_stale_quote_never_scored(self):
        f,o,r=inputs()
        o.pop("payload_sha256")
        o["quotes"]["MS"]["checked_at_utc"]=(ANALYSIS-timedelta(minutes=11)).isoformat()
        p=calc(f,seal(o),r)
        self.assertEqual(p["groups"]["MS"]["status"],"NO_COMPLETE_FRESH_QUOTE")

    def test_incomplete_market_never_scored(self):
        f,o,r=inputs()
        o.pop("payload_sha256")
        o["quotes"]["MS"]["decimal_odds"]={"MS1":1.6}
        p=calc(f,seal(o),r)
        self.assertEqual(p["groups"]["MS"]["status"],"NO_COMPLETE_FRESH_QUOTE")

    def test_cross_site_url_refused(self):
        f,o,r=inputs()
        o.pop("payload_sha256")
        o["quotes"]["MS"]["source_url"]="https://evil.test/mock"
        with self.assertRaisesRegex(ValueError,"URL_SOURCE"): calc(f,seal(o),r)

    def test_quote_after_kickoff_refused(self):
        f,o,r=inputs()
        o.pop("payload_sha256")
        o["analysis_at_utc"]=(KO+timedelta(minutes=1)).isoformat()
        with self.assertRaisesRegex(ValueError,"OUTSIDE_PREMATCH"):calc(f,seal(o),r)

    def test_wrong_fixture_refused(self):
        f,o,r=inputs()
        o.pop("payload_sha256")
        o["fixture_key"]="WRONG"
        with self.assertRaisesRegex(ValueError,"IDENTITY_MISMATCH"):calc(f,seal(o),r)

    def test_result_must_be_after_kickoff(self):
        f,o,r=inputs()
        r["finalized_at_utc"]=(KO-timedelta(minutes=1)).isoformat()
        with self.assertRaisesRegex(ValueError,"RESULT_NOT_POSTMATCH"):calc(f,o,r)

    def test_no_fake_source_attestation(self):
        f,o,r=inputs()
        o.pop("payload_sha256")
        o["source_review"]["method"]="GENERATED_BY_MODEL"
        with self.assertRaisesRegex(ValueError,"HUMAN_SOURCE"):calc(f,seal(o),r)

    def test_binary_brier_matches_existing_method(self):
        self.assertAlmostEqual(_score({"BTTS_YES":.7,"BTTS_NO":.3},"KG","BTTS_YES")["brier"],.09)

    def test_postmatch_all_three_goal_lines_scored_with_opposites(self):
        f,o,r=inputs()
        o.pop("payload_sha256")
        for group,prices in {
            "GOALS_1.5":{"OVER_1.5":1.25,"UNDER_1.5":4.0},
            "GOALS_2.5":{"OVER_2.5":1.85,"UNDER_2.5":2.0},
            "GOALS_3.5":{"OVER_3.5":3.20,"UNDER_3.5":1.42},
        }.items():
            q=deepcopy(o["quotes"]["MS"])
            q["market_group"]=group
            q["decimal_odds"]=prices
            o["quotes"][group]=q
        o=seal(o)
        pair=calc(f,o,r)
        expected={"GOALS_1.5":"OVER_1.5",
                  "GOALS_2.5":"OVER_2.5",
                  "GOALS_3.5":"UNDER_3.5"}
        for group,selection in expected.items():
            got=pair["groups"][group]
            self.assertEqual(got["status"],"DESCRIPTIVE_MATCHED_PAIR_NOT_LIVE_VERIFIED")
            self.assertEqual(got["actual_selection"],selection)
            self.assertEqual(set(got["scores"]),{"MARKET","B","C2","C3","M4"})
            self.assertAlmostEqual(sum(got["no_vig"].values()),1)
            self.assertGreaterEqual(got["scores"]["MARKET"]["brier"],0)
            self.assertLessEqual(got["scores"]["MARKET"]["brier"],1)
        overview=summarize([pair])
        self.assertEqual(set(overview["markets"]),{"MS","KG","GOALS_1.5","GOALS_2.5","GOALS_3.5"})
        for group in expected:
            self.assertEqual(overview["markets"][group]["quotes_complete_n"],1)

    def test_goals_threshold_boundaries_not_conflated(self):
        scored={"home_goals":2,"away_goals":0}
        self.assertEqual(_result_side(scored,"GOALS_1.5"),"OVER_1.5")
        self.assertEqual(_result_side(scored,"GOALS_2.5"),"UNDER_2.5")
        self.assertEqual(_result_side(scored,"GOALS_3.5"),"UNDER_3.5")
        scored={"home_goals":3,"away_goals":1}
        self.assertEqual(_result_side(scored,"GOALS_1.5"),"OVER_1.5")
        self.assertEqual(_result_side(scored,"GOALS_2.5"),"OVER_2.5")
        self.assertEqual(_result_side(scored,"GOALS_3.5"),"OVER_3.5")
        scored={"home_goals":0,"away_goals":1}
        self.assertEqual(_result_side(scored,"GOALS_1.5"),"UNDER_1.5")

    def test_stale_new_goal_quote_does_not_enter_postmatch_scores(self):
        f,o,r=inputs()
        o.pop("payload_sha256")
        q=deepcopy(o["quotes"]["MS"])
        q["market_group"]="GOALS_3.5"
        q["decimal_odds"]={"OVER_3.5":3.20,"UNDER_3.5":1.42}
        q["checked_at_utc"]=(ANALYSIS-timedelta(minutes=11)).isoformat()
        o["quotes"]["GOALS_3.5"]=q
        pair=calc(f,seal(o),r)
        self.assertEqual(pair["groups"]["GOALS_3.5"]["status"],"NO_COMPLETE_FRESH_QUOTE")
        self.assertEqual(summarize([pair])["markets"]["GOALS_3.5"]["quotes_complete_n"],0)

    def test_no_model_modified_by_paired_scoring(self):
        f,o,r=inputs()
        prior=deepcopy(f)
        calc(f,o,r)
        self.assertEqual(f,prior)

if __name__=="__main__":
    unittest.main()
