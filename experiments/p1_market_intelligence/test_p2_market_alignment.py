"""P2 agreement auditor synthetic safety tests. No outcome tuning, no betting."""
import copy
import unittest

from p1_market import _sha_json, no_vig
from p2_market_alignment import (
    AlignmentError, PDF_SCHEMA, DECISION_SCHEMA, _p0_from_prices,
    align_first_pdf_snapshot, _align, run_signed_session,
)

ODDS = {
    "MS": {"MS1": 1.65, "MSX": 3.9, "MS2": 4.5},
    "OU25": {"UNDER_2.5": 1.8, "OVER_2.5": 1.9},
    "KG": {"BTTS_YES": 1.8, "BTTS_NO": 1.85},
}
P = {
    "MS1": .60, "MSX": .18, "MS2": .22,
    "OVER_2.5": .55, "UNDER_2.5": .45,
    "BTTS_YES": .58, "BTTS_NO": .42,
}


def _sign(o, field):
    o[field] = _sha_json(o)
    return o


def decision(p=.60):
    d = {
        "schema": DECISION_SCHEMA,
        "forecast_sha256": "f" * 64,
        "fixture": {
            "league": "TUR1", "home_id": "h1", "away_id": "a1",
            "match_local_date": "2026-11-22",
            "kickoff_utc": "2026-11-22T20:00:00+00:00",
            "fixture_verification": "VERIFIED_BY_LIVE_OFFICIAL_GATE",
        },
        "main_candidate": {
            "family": "MS", "market": "MS1",
            "calibrated_probability": p,
        },
        "model_market_diagnostics": [
            {"market": k, "calibrated_probability": p if k == "MS1" else v}
            for k, v in P.items()
        ],
        "price_used_in_decision": False,
        "odds_affected_selection": False,
        "market_prices_not_required_for_model_decision": True,
        "production_modified": False,
        "betting_authorized": False,
        "forecast_unchanged": True,
    }
    return _sign(d, "payload_sha256")


def snapshot(prices=ODDS):
    group_map = {"MS": "MS", "OU25": "GOALS_2.5", "KG": "KG"}
    s = {
        "schema": PDF_SCHEMA,
        "source_domain": "iddaa.com",
        "human_source_type": "ORIGINAL_USER_CHROME_PRINT_TO_PDF",
        "price_age_class": "ARCHIVED_PDF_PRE_FORECAST",
        "is_current_live_quote": False,
        "network_bookmaker_reverified": False,
        "bookmaker_api_calls": 0,
        "forecast_sha256": "f" * 64,
        "fixture_key": "TUR1:h1:a1:2026-11-22",
        "kickoff_utc": "2026-11-22T20:00:00+00:00",
        "observed_at_utc": "2026-11-22T07:00:00+00:00",
        "created_after_pdf_forecast_utc": "2026-11-22T07:10:00+00:00",
        "source_pdf_sha256": "a" * 64,
        "groups": {
            group_map[k]: {
                "prices": v,
                "no_vig": no_vig(v)["probabilities"],
            }
            for k, v in prices.items()
        },
    }
    return _sign(s, "payload_sha256")


class TestP2(unittest.TestCase):
    def test_aligned_same_top_five_pp(self):
        d = decision()
        s = snapshot()
        report = align_first_pdf_snapshot(d, s)
        expected = no_vig(ODDS["MS"])["probabilities"]["MS1"]
        self.assertAlmostEqual(report["p0_same_choice_probability"], expected)
        self.assertEqual(report["status"], "UYUMLU")
        self.assertEqual(report["window_sensitivity"]["3"], "UYUMLU_TAHMIN_BULUNAMADI")
        self.assertEqual(report["window_sensitivity"]["5"], "UYUMLU")
        self.assertTrue(report["p0_main_choice_matches"])
        self.assertTrue(report["no_new_probability"])
        self.assertFalse(report["main_decision_changed"])
        self.assertFalse(report["threshold_validated"])

    def test_not_aligned_if_p0_top_different_even_when_same_event_close(self):
        odds = copy.deepcopy(ODDS)
        odds["KG"] = {"BTTS_YES": 1.3, "BTTS_NO": 3.1}
        report = align_first_pdf_snapshot(decision(), snapshot(odds))
        self.assertEqual(report["p0_highest_choice"], "BTTS_YES")
        self.assertLess(report["absolute_gap_pp"], 5)
        self.assertEqual(report["status"], "UYUMLU_TAHMIN_BULUNAMADI")

    def test_not_aligned_when_large_gap(self):
        report = align_first_pdf_snapshot(decision(.72), snapshot())
        self.assertGreater(report["absolute_gap_pp"], 7)
        self.assertEqual(report["status"], "UYUMLU_TAHMIN_BULUNAMADI")
        self.assertFalse(report["main_decision_changed"])

    def test_missing_selected_market_never_imputed(self):
        partial = {k: v for k, v in ODDS.items() if k != "MS"}
        report = align_first_pdf_snapshot(decision(), snapshot(partial))
        self.assertEqual(report["status"], "P0_SAME_MARKET_UNAVAILABLE")
        self.assertIsNone(report["p0_same_choice_probability"])
        self.assertIsNone(report["absolute_gap_pp"])


    def test_missing_other_group_cannot_claim_seven_event_top(self):
        partial = {k: v for k, v in ODDS.items() if k != "KG"}
        report = align_first_pdf_snapshot(decision(), snapshot(partial))
        self.assertIsNotNone(report["p0_same_choice_probability"])
        self.assertLess(report["absolute_gap_pp"], 5)
        self.assertEqual(report["status"], "P0_SEVEN_MARKETS_INCOMPLETE")
        self.assertFalse(report["p0_highest_is_global"])
        self.assertEqual(report["window_sensitivity"], {})


    def test_pdf_explicit_dash_unquoted_not_parser_error(self):
        # Trabzon-like MS1 '-' while MSX and MS2 are still displayed.
        remaining = {"OU25": ODDS["OU25"], "KG": ODDS["KG"]}
        data = snapshot(remaining)
        data["not_offered_pdf_market_keys"] = ["MS1"]
        data["partial_quoted_prices_no_no_vig"] = {
            "MS": {"MSX": 8.21, "MS2": 16.50}}
        data["payload_sha256"] = _sha_json({
            k: v for k, v in data.items() if k != "payload_sha256"})
        got = align_first_pdf_snapshot(decision(), data)
        self.assertEqual(got["status"], "MODEL_TOP_CHOICE_NOT_OFFERED_IN_PDF")
        self.assertEqual(got["unquoted_pdf_selections"], ["MS1"])
        self.assertIsNone(got["p0_same_choice_probability"])
        self.assertFalse(got["p0_highest_is_global"])
        self.assertEqual(got["partially_quoted_unpriced_families"]["MS"]["MSX"], 8.21)
        self.assertEqual(len(got["other_complete_market_comparisons"]), 4)
        self.assertTrue(got["no_new_probability"])
        self.assertFalse(got["main_decision_changed"])

    def test_dash_in_other_family_does_not_create_fake_full_agreement(self):
        only = {"MS": ODDS["MS"], "OU25": ODDS["OU25"]}
        data = snapshot(only)
        data["not_offered_pdf_market_keys"] = ["BTTS_NO"]
        data["partial_quoted_prices_no_no_vig"] = {"KG": {"BTTS_YES": 1.8}}
        data["payload_sha256"] = _sha_json({
            k: v for k,v in data.items() if k != "payload_sha256"})
        got = align_first_pdf_snapshot(decision(), data)
        self.assertEqual(got["status"], "P0_SEVEN_MARKETS_INCOMPLETE")
        self.assertIsNotNone(got["p0_same_choice_probability"])
        self.assertFalse(got["p0_highest_is_global"])

    def test_unquoted_cannot_coexist_with_full_quoted_price(self):
        data = snapshot()
        data["not_offered_pdf_market_keys"] = ["MS1"]
        data["payload_sha256"] = _sha_json({
            k:v for k,v in data.items() if k != "payload_sha256"})
        with self.assertRaisesRegex(AlignmentError, "UNQUOTED_PDF_KEYS_CONTRADICT"):
            align_first_pdf_snapshot(decision(), data)

    def test_partial_odds_cannot_forge_a_complete_market(self):
        data = snapshot({"OU25": ODDS["OU25"], "KG": ODDS["KG"]})
        data["not_offered_pdf_market_keys"] = ["MS1"]
        data["partial_quoted_prices_no_no_vig"] = {
            "MS": {"MSX": 8.21, "MS2": 16.50, "MS1": 1.01}}
        data["payload_sha256"] = _sha_json({
            k:v for k,v in data.items() if k != "payload_sha256"})
        with self.assertRaisesRegex(AlignmentError, "PARTIAL_QUOTES_INCONSISTENT"):
            align_first_pdf_snapshot(decision(), data)

    def test_decision_and_pdf_hashes_protected(self):
        d, s = decision(), snapshot()
        d["main_candidate"]["calibrated_probability"] += .01
        with self.assertRaisesRegex(AlignmentError, "DECISION_SHA_INVALID"):
            align_first_pdf_snapshot(d, s)
        d, s = decision(), snapshot()
        s["groups"]["MS"]["prices"]["MS1"] = 1.4
        with self.assertRaisesRegex(AlignmentError, "PDF_SNAPSHOT_SHA_INVALID"):
            align_first_pdf_snapshot(d, s)

    def test_forged_identity_or_postforecast_prices_rejected(self):
        d, s = decision(), snapshot()
        s["fixture_key"] = "TUR1:a1:h1:2026-11-22"
        _sign({k: v for k, v in s.items() if k != "payload_sha256"}, "payload_sha256")
        s["payload_sha256"] = _sha_json({k: v for k, v in s.items() if k != "payload_sha256"})
        with self.assertRaisesRegex(AlignmentError, "SOURCE_OR_FIXTURE_JOIN"):
            align_first_pdf_snapshot(d, s)
        d, s = decision(), snapshot()
        s["observed_at_utc"] = "2026-11-22T21:00:00+00:00"
        s["payload_sha256"] = _sha_json({k: v for k, v in s.items() if k != "payload_sha256"})
        with self.assertRaisesRegex(AlignmentError, "PRICE_NOT_BEFORE_MODEL"):
            align_first_pdf_snapshot(d, s)

    def test_second_pdf_never_accepted_as_morning(self):
        d, s = decision(), snapshot()
        s["price_age_class"] = "SECOND_PDF_AFTER_FORECAST"
        s["payload_sha256"] = _sha_json({k: v for k, v in s.items() if k != "payload_sha256"})
        with self.assertRaisesRegex(AlignmentError, "SOURCE_OR_FIXTURE_JOIN"):
            align_first_pdf_snapshot(d, s)

    def test_missing_or_corrupted_market_fair_rejected(self):
        d, s = decision(), snapshot()
        s["groups"]["MS"]["no_vig"]["MS1"] = .95
        s["payload_sha256"] = _sha_json({k: v for k, v in s.items() if k != "payload_sha256"})
        with self.assertRaisesRegex(AlignmentError, "PDF_FAIR_VALUES_DO_NOT_MATCH"):
            align_first_pdf_snapshot(d, s)

    def test_seven_probabilities_not_normalized_together(self):
        p = _p0_from_prices(ODDS)
        self.assertEqual(sum(len(v) for v in p.values()), 7)
        for values in p.values():
            self.assertAlmostEqual(sum(values.values()), 1.0, places=12)
        self.assertAlmostEqual(sum(sum(v.values()) for v in p.values()), 3.0, places=12)

    def test_model_favorite_not_seven_max_rejected(self):
        d = decision()
        d["model_market_diagnostics"][0]["calibrated_probability"] = .50
        d["payload_sha256"] = _sha_json({k: v for k, v in d.items() if k != "payload_sha256"})
        with self.assertRaisesRegex(AlignmentError, "MODEL_TOP_CHOICE_NOT_FROZEN_MAXIMUM"):
            align_first_pdf_snapshot(d, snapshot())

    def test_immutable_first_pdf_session_route(self):
        session = {
            "source_original_pdf_verified_once_locally": True,
            "source_bookmaker": "iddaa.com",
            "new_bookmaker_network_calls": 0,
            "pilot_count_changed": False,
            "rows": [{"index": 0, "model_first_decision": decision(),
                      "pdf_first_price_snapshot": snapshot()}],
        }
        session["signed_research_session_sha256"] = _sha_json(session)
        report = run_signed_session(session)
        self.assertEqual(report["analyzed"], 1)
        self.assertEqual(report["excluded"], [])
        self.assertEqual(report["records"][0]["alignment"]["status"], "UYUMLU")
        self.assertEqual(len(report["records"][0]["alignment"]["p0_probabilities"]), 3)
        self.assertTrue(report["no_new_seals"])
        self.assertTrue(report["no_model_selection_changes"])
        session["rows"][0]["model_first_decision"]["main_candidate"]["market"] = "MS2"
        with self.assertRaisesRegex(AlignmentError, "SESSION_SHA_INVALID"):
            run_signed_session(session)

    def test_session_blocks_unproven_pdf_origin(self):
        session = {
            "source_original_pdf_verified_once_locally": False,
            "source_bookmaker": "iddaa.com",
            "new_bookmaker_network_calls": 0,
            "pilot_count_changed": False,
            "rows": [{"index": 0, "model_first_decision": decision(),
                      "pdf_first_price_snapshot": snapshot()}],
        }
        session["signed_research_session_sha256"] = _sha_json(session)
        with self.assertRaisesRegex(AlignmentError, "NOT_ORIGINAL_SIGNED_IDDAA"):
            run_signed_session(session)


if __name__ == "__main__":
    unittest.main()
