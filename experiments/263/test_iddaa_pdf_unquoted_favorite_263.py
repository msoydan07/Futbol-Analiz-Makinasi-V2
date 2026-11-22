"""Regression: bookmaker '-' is a known unquoted cell, not a bad PDF parse."""
import unittest
from test_model_first_decision_263 import scenario, seal
from iddaa_pdf_session_263 import pdf_prices, market_no_vig, SCHEMA as S
from iddaa_pdf_bulletin_263 import SCHEMA as B
from iddaa_pdf_first_quote_263 import build_snapshot

class TestUnquotedFavorite(unittest.TestCase):
    def test_trabzon_style_first_pdf_dash_keeps_full_and_partial_quotes(self):
        forecast,_ = scenario()
        forecast["fixture"]["official_source"] = "https://www.tff.org/default.aspx?ftxtID=2966&pageID=600"
        seal(forecast)
        r = {
            "status": "PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK",
            "league": "TUR1", "home_label": "Trabzonspor",
            "away_label": "Eyüpspor", "match_date_tr": "2026-11-21",
            "kickoff_time_tr": "20:00", "page": 1,
            "odds": {"MS1": None, "MSX": 8.21, "MS2": 16.50,
                     "O25_UNDER": 2.79, "O25_OVER": 1.25,
                     "BTTS_YES": 2.01, "BTTS_NO": 1.51},
        }
        row = {
            "index": 0, "status": "FOUR_MODELS_FORECAST_SHA_CREATED",
            "model_forecast_created": True,
            "league": "TUR1", "pdf_home": "Trabzonspor", "pdf_away": "Eyüpspor",
            "match_date_tr": "2026-11-21", "kickoff_time_tr": "20:00",
            "pdf_page": 1, "prices": pdf_prices(r),
            "market_no_vig": market_no_vig(r),
            "price_capture_utc": "2026-11-21T09:00:00+00:00",
            "model_forecast_sha256": forecast["payload_sha256"],
            "home_id": forecast["fixture"]["home_id"],
            "away_id": forecast["fixture"]["away_id"],
            "official": {
                "source_url": forecast["fixture"]["official_source"],
                "kickoff_utc": forecast["fixture"]["kickoff_utc"],
            },
        }
        bulletin = {
            "schema": B, "source_domain": "iddaa.com",
            "pdf_sha256": "c"*64, "pdf_capture_utc": row["price_capture_utc"],
            "rows": [r],
        }
        session = {
            "schema": S, "source_bookmaker": "iddaa.com",
            "pdf_sha256": "c"*64, "pdf_capture_utc": row["price_capture_utc"],
            "bookmaker_reverification_calls": 0,
            "rows": [row],
        }
        snap = build_snapshot(bulletin, session, row, forecast, verified_pdf_sha="c"*64)
        self.assertEqual(snap["not_offered_pdf_market_keys"], ["MS1"])
        self.assertEqual(snap["partial_quoted_prices_no_no_vig"]["MS"],
                         {"MSX":8.21,"MS2":16.5})
        self.assertEqual(set(snap["groups"]), {"GOALS_2.5", "KG"})
        self.assertIn("MS", snap["missing_or_invalid_groups"])
        self.assertNotIn("MS1", snap["groups"])
        self.assertTrue(snap["payload_sha256"])
        self.assertFalse(snap["is_current_live_quote"])

    def test_all_seven_unquoted_choices_are_generic_not_ms1_specific(self):
        # Exercise the actual original-first-PDF quote bridge for MS1/X/2,
        # 2.5 UNDER/OVER, KG YES/NO. A published '-' is NEVER estimated.
        from iddaa_pdf_session_263 import PDF_TO_MARKET, MARKET_GROUPS
        reverse={v:k for k,v in PDF_TO_MARKET.items()}
        base_odds={
            "MS1":2.33, "MSX":3.02, "MS2":2.52,
            "O25_UNDER":1.72, "O25_OVER":1.74,
            "BTTS_YES":1.70, "BTTS_NO":1.80,
        }
        for absent_market in PDF_TO_MARKET.values():
            with self.subTest(unquoted=absent_market):
                forecast,_=scenario()
                forecast["fixture"]["official_source"] = "https://www.tff.org/default.aspx?ftxtID=2966&pageID=600"
                seal(forecast)
                odds=base_odds.copy()
                odds[reverse[absent_market]]=None
                r={"status":"PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK",
                   "league":"TUR1", "home_label":"Ev sahibi", "away_label":"Deplasman",
                   "match_date_tr":"2026-11-21", "kickoff_time_tr":"20:00",
                   "page":1, "odds":odds}
                row={"index":0,"status":"FOUR_MODELS_FORECAST_SHA_CREATED",
                     "model_forecast_created":True,
                     "league":"TUR1", "pdf_home":"Ev sahibi", "pdf_away":"Deplasman",
                     "match_date_tr":"2026-11-21", "kickoff_time_tr":"20:00",
                     "pdf_page":1,"prices":pdf_prices(r),
                     "market_no_vig":market_no_vig(r),
                     "price_capture_utc":"2026-11-21T09:00:00+00:00",
                     "model_forecast_sha256":forecast["payload_sha256"],
                     "home_id":forecast["fixture"]["home_id"],
                     "away_id":forecast["fixture"]["away_id"],
                     "official":{"source_url":forecast["fixture"]["official_source"],
                                 "kickoff_utc":forecast["fixture"]["kickoff_utc"]}}
                bulletin={"schema":B,"source_domain":"iddaa.com",
                          "pdf_sha256":"c"*64,
                          "pdf_capture_utc":row["price_capture_utc"],"rows":[r]}
                session={"schema":S,"source_bookmaker":"iddaa.com","pdf_sha256":"c"*64,
                         "pdf_capture_utc":row["price_capture_utc"],
                         "bookmaker_reverification_calls":0,"rows":[row]}
                actual=build_snapshot(bulletin,session,row,forecast,verified_pdf_sha="c"*64)
                expected_group=next(g for g,keys in MARKET_GROUPS.items()
                                    if absent_market in keys)
                self.assertEqual(actual["not_offered_pdf_market_keys"],[absent_market])
                self.assertEqual(set(actual["groups"]),set(MARKET_GROUPS)-{expected_group})
                remaining={k:pdf_prices(r)[k] for k in MARKET_GROUPS[expected_group]
                           if k!=absent_market}
                self.assertEqual(actual["partial_quoted_prices_no_no_vig"][expected_group],remaining)
                self.assertIn(expected_group,actual["missing_or_invalid_groups"])
                self.assertFalse(actual["is_current_live_quote"])
                self.assertEqual(actual["forecast_sha256"],forecast["payload_sha256"])


if __name__ == "__main__":
    unittest.main()
