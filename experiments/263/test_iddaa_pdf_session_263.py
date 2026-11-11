"""One-pass official matching, as-of PDF price, no repeated odds access."""
from datetime import datetime,timezone
import unittest
from iddaa_pdf_bulletin_263 import SCHEMA as BULLETIN
from iddaa_pdf_session_263 import (
 run_session,market_no_vig,pdf_prices,SCHEMA
)

def row(**kw):
    d={"page":1,"league":"TUR1","league_label":"TÜRKİYE SÜPER LİG",
       "match_date_tr":"2026-11-11","kickoff_time_tr":"20:00",
       "home_label":"Besiktas JK","away_label":"Genclerbirligi SK",
       "status":"PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK",
       "odds":{"MS1":3.62,"MSX":3.73,"MS2":1.65,
               "O25_UNDER":2.38,"O25_OVER":1.37,
               "BTTS_YES":1.38,"BTTS_NO":2.35}}
    d.update(kw);return d

def source(rows):
    return {"schema":BULLETIN,"source_domain":"iddaa.com",
            "pdf_sha256":"a"*64,"pdf_capture_utc":"2026-11-11T14:46:22+00:00",
            "rows":rows}

NOW=datetime(2026,11,11,15,0,tzinfo=timezone.utc)

def real_official(h,a):
    return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":h,"away":a,
            "source_url":"https://www.tff.org/fikstur",
            "kickoff_utc":"2026-11-11T17:00:00+00:00",
            "retrieved_at_utc":"2026-11-11T14:59:00+00:00"}

class SessionTests(unittest.TestCase):
    def test_complete_prices_no_vig_and_only_requested_markets(self):
        r=row()
        fair=market_no_vig(r)
        self.assertEqual(set(fair),{"MS","GOALS_2.5","KG"})
        for market in fair.values():
            self.assertEqual(market["status"],"FULL_MARKET_QUOTE_AVAILABLE")
            self.assertAlmostEqual(sum(market["no_vig"].values()),1,places=9)
        self.assertEqual(set(pdf_prices(r)),
                         {"MS1","MSX","MS2","OVER_2.5",
                          "UNDER_2.5","BTTS_YES","BTTS_NO"})
        self.assertNotIn("OVER_1.5",str(fair))
        self.assertNotIn("UNDER_3.5",str(fair))

    def test_only_missing_market_is_skipped_and_others_proceed(self):
        r=row();r["odds"]["O25_OVER"]=None
        fair=market_no_vig(r)
        self.assertEqual(fair["GOALS_2.5"]["status"],"PRICE_MISSING_ONE_OR_MORE_SIDES")
        self.assertEqual(fair["KG"]["status"],"FULL_MARKET_QUOTE_AVAILABLE")
        self.assertEqual(fair["MS"]["status"],"FULL_MARKET_QUOTE_AVAILABLE")

    def test_one_official_lookup_per_match_no_secondary_bookmaker(self):
        calls=[]
        def fake(h,a):
            calls.append((h,a))
            return real_official(h,a)
        outcome=run_session(source([row()]),now=NOW,official_lookup=fake,max_workers=1)
        self.assertEqual(outcome["schema"],SCHEMA)
        self.assertEqual(outcome["n_rows"],1)
        self.assertEqual(outcome["n_official"],1)
        self.assertEqual(outcome["n_forecast"],0)
        self.assertEqual(len(calls),1)
        self.assertEqual(outcome["bookmaker_reverification_calls"],0)
        self.assertEqual(outcome["rows"][0]["status"],"ONE_OFFICIAL_SOURCE_CONFIRMED")
        self.assertEqual(outcome["rows"][0]["official_lookup_attempts"],1)

    def test_one_bad_name_does_not_block_valid_row(self):
        calls=[]
        def official(h,a):
            calls.append((h,a));return real_official(h,a)
        bad=row(home_label="Besiktas…")
        s=run_session(source([row(),bad]),now=NOW,
                      official_lookup=official,max_workers=2)
        self.assertEqual(s["n_rows"],2)
        self.assertEqual(s["n_official"],1)
        self.assertEqual(s["rows"][1]["status"],"ONE_ROW_NAME_REVIEW")
        self.assertEqual(len(calls),1)

    def test_reversed_official_team_order_refused_without_retry(self):
        calls=[]
        def reversed_source(h,a):
            calls.append(1);p=real_official(h,a)
            p["home"],p["away"]=a,h
            return p
        result=run_session(source([row()]),now=NOW,
            official_lookup=reversed_source,max_workers=1)
        self.assertEqual(result["n_official"],0)
        self.assertEqual(len(calls),1)
        self.assertEqual(result["rows"][0]["status"],
                         "ONE_ROW_OFFICIAL_TEAM_ORDER_OR_ALIAS_MISMATCH")

    def test_mismatched_official_kickoff_refused_without_research_loop(self):
        def shifted(h,a):
            data=real_official(h,a)
            data["kickoff_utc"]="2026-11-11T18:00:00+00:00"
            return data
        result=run_session(source([row()]),now=NOW,
            official_lookup=shifted,max_workers=1)
        self.assertEqual(result["n_official"],0)
        self.assertEqual(result["rows"][0]["status"],
                         "ONE_ROW_OFFICIAL_PDF_TIME_OR_DATE_DIFFER")

    def test_kickoff_passed_never_calls_official_or_model(self):
        calls=[]
        def no_touch(h,a):
            calls.append(1);return real_official(h,a)
        result=run_session(source([row(kickoff_time_tr="17:00")]),now=NOW,
            official_lookup=no_touch,max_workers=1)
        self.assertEqual(len(calls),0)
        self.assertEqual(result["rows"][0]["status"],
                         "KICKOFF_PASSED_OR_PDF_NOT_PREMATCH")

    def test_outside_ten_league_does_not_call_official(self):
        calls=[]
        s=run_session(source([row(league=None)]),now=NOW,
            official_lookup=lambda h,a:calls.append(1),max_workers=1)
        self.assertEqual(s["n_official"],0)
        self.assertEqual(s["rows"][0]["status"],"SKIPPED_OUT_OF_10_LEAGUES")
        self.assertFalse(calls)

    def test_pdf_after_match_does_not_backdate_price(self):
        observed_after=source([row()])
        observed_after["pdf_capture_utc"]="2026-11-11T18:05:00+00:00"
        s=run_session(observed_after,now=datetime(2026,11,11,18,10,tzinfo=timezone.utc),
                      official_lookup=lambda h,a:real_official(h,a),max_workers=1)
        self.assertEqual(s["rows"][0]["status"],"KICKOFF_PASSED_OR_PDF_NOT_PREMATCH")
        self.assertEqual(s["n_official"],0)

if __name__=="__main__":unittest.main()
