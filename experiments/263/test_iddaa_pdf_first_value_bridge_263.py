"""Synthetic end-to-end PDF-before-forecast -> existing frozen policy tests.

Test odds/fixtures are FAKE UNIT FIXTURES, never marketed as user PDF prices.
Production boundary separately requires original PDF bytes and signed forecast.
"""
from __future__ import annotations
import copy,json,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch

from iddaa_pdf_session_263 import (pdf_prices,market_no_vig,SCHEMA as SESSION)
from iddaa_pdf_bulletin_263 import SCHEMA as BULLETIN
from iddaa_pdf_first_quote_263 import (build_snapshot,extract,sha256)
from four_model_value_policy_263 import decide,render
from iddaa_pdf_value_bridge_263 import calibrate_session
from iddaa_pdf_team_alias_preflight_263 import index_registry
from test_four_model_value_policy_263 import fixture as policy_fixture,seal
from iddaa_pdf_report_263 import _render_pick,build as build_report

NOW=datetime(2026,11,6,16,3,tzinfo=timezone.utc)
PDF_TIME="2026-11-06T15:30:00+00:00"
PDF_SHA="c"*64

def sample():
    f,b,lock=policy_fixture()
    index,names,_=index_registry()
    h=index["TUR1"]["besiktas"]
    a=index["TUR1"]["genclerbirligi"]
    f["fixture"]["home_id"]=h
    f["fixture"]["away_id"]=a
    f["fixture"]["official_source"]="https://www.tff.org/fikstur"
    seal(f)
    b["forecast_sha256"]=f["payload_sha256"]
    seal(b)
    pdfrow={
        "league":"TUR1","league_label":"TÜRKİYE SÜPER LİG",
        "page":1,"home_label":"Besiktas JK",
        "away_label":"Genclerbirligi SK",
        "match_date_tr":"2026-11-06","kickoff_time_tr":"20:00",
        "status":"PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK",
        "odds":{"MS1":1.99,"MSX":3.10,"MS2":5.40,
                "O25_UNDER":1.87,"O25_OVER":2.00,
                "BTTS_YES":1.81,"BTTS_NO":2.01},
    }
    source={"schema":BULLETIN,"pdf_sha256":PDF_SHA,
            "source_domain":"iddaa.com","pdf_capture_utc":PDF_TIME,
            "rows":[pdfrow]}
    match={"index":0,"league":"TUR1",
           "pdf_home":"Besiktas JK","pdf_away":"Genclerbirligi SK",
           "pdf_page":1,"match_date_tr":"2026-11-06",
           "kickoff_time_tr":"20:00",
           "status":"FOUR_MODELS_FORECAST_SHA_CREATED",
           "model_forecast_created":True,
           "model_forecast_sha256":f["payload_sha256"],
           "model_forecast_path":"forward.json",
           "empirical_baseline_path":"baseline.json",
           "empirical_baseline_sha256":b["payload_sha256"],
           "home_id":h,"away_id":a,
           "price_capture_utc":PDF_TIME,"prices":pdf_prices(pdfrow),
           "market_no_vig":market_no_vig(pdfrow),
           "official":{"source_url":"https://www.tff.org/fikstur",
                       "kickoff_utc":"2026-11-06T17:00:00+00:00"},
           "model_1x2_and_core_markets":{"M4":{
               "MS1":.72,"MSX":.17,"MS2":.11,
               "OVER_2.5":.53,"UNDER_2.5":.47,
               "BTTS_YES":.58,"BTTS_NO":.42}}
    session={"schema":SESSION,"source_bookmaker":"iddaa.com",
             "bookmaker_reverification_calls":0,"pdf_sha256":PDF_SHA,
             "pdf_capture_utc":PDF_TIME,"n_rows":1,
             "rows":[match]}
    return f,b,lock,source,session

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.f,self.b,self.lock,self.source,self.session=sample()
    def build(self):
        return build_snapshot(self.source,self.session,self.session["rows"][0],
                              self.f,verified_pdf_sha=PDF_SHA)
    def test_preforecast_pdf_is_conditional_main_no_unwanted_markets(self):
        q=self.build()
        d=decide(self.f,self.b,self.lock,pdf_first_snapshot=q,now=NOW)
        self.assertEqual(d["main_candidate"]["market"],"MS1")
        self.assertTrue(d["main_value_conditional"])
        self.assertFalse(d["main_price_current"])
        self.assertTrue(d["iddaa_pdf_only_seven_markets"])
        self.assertEqual(d["iddaa_pdf_first_sha256"],q["payload_sha256"])
        self.assertEqual(d["iddaa_original_pdf_sha256"],PDF_SHA)
        self.assertEqual(d["quote_status"],"USER_IDDAA_PDF_PRE_FORECAST_NOT_NETWORK_REVERIFIED")
        self.assertEqual(d["status"],"RESEARCH_CONDITIONAL_IDDAA_PDF_PRICE_NOT_CURRENT")
        self.assertTrue(set(x["market"] for x in d["all_market_diagnostics"]).issubset(
            {"MS1","MSX","MS2","OVER_2.5","UNDER_2.5","BTTS_YES","BTTS_NO"}))
        self.assertFalse(d["betting_authorized"])
        self.assertEqual(d["official_pilot_count_increment"],0)
        self.assertNotIn("1.5 Üst",render(d))

    def test_time_observed_before_forecast_and_no_live_relabel(self):
        q=self.build()
        self.assertEqual(q["observed_at_utc"],PDF_TIME)
        prices,status=extract(q,self.f,NOW)
        self.assertEqual(prices["MS1"]["checked"],PDF_TIME)
        self.assertEqual(prices["MS1"]["age_class"],"ARCHIVED_PDF_PRE_FORECAST")
        self.assertNotEqual(prices["MS1"]["age_class"],"CURRENT_T60")
        self.assertIn("PDF_PRE_FORECAST",status)

    def test_different_quote_sources_must_not_mix_with_pdf(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_MIX"):
            decide(self.f,self.b,self.lock,observation={},
                   pdf_first_snapshot=self.build(),now=NOW)
        with self.assertRaisesRegex(ValueError,"CANNOT_MIX"):
            decide(self.f,self.b,self.lock,morning_snapshot={},
                   pdf_first_snapshot=self.build(),now=NOW)

    def test_no_value_when_price_does_not_pass_ev(self):
        self.source["rows"][0]["odds"]["MS1"]=1.30
        self.session["rows"][0]["prices"]=pdf_prices(self.source["rows"][0])
        self.session["rows"][0]["market_no_vig"]=market_no_vig(self.source["rows"][0])
        self.assertEqual(decide(self.f,self.b,self.lock,pdf_first_snapshot=self.build(),
                   now=NOW)["status"],"RESEARCH_PAS")

    def test_missing_over_under_price_no_leak_into_other_groups(self):
        self.source["rows"][0]["odds"]["O25_OVER"]=None
        self.session["rows"][0]["prices"]=pdf_prices(self.source["rows"][0])
        self.session["rows"][0]["market_no_vig"]=market_no_vig(self.source["rows"][0])
        q=self.build()
        self.assertEqual(q["missing_or_invalid_groups"],["GOALS_2.5"])
        prices,_=extract(q,self.f,NOW)
        self.assertIn("MS1",prices)
        self.assertIn("BTTS_YES",prices)
        self.assertNotIn("OVER_2.5",prices)
        self.assertNotIn("UNDER_2.5",prices)

    def test_forecast_or_pdf_team_wrong_blocks_only_specific_row(self):
        self.session["rows"][0]["home_id"]="not-a-real-team-uuid"
        with self.assertRaisesRegex(ValueError,"FIXTURE_SHA_IDENTITY_MISMATCH"):
            self.build()
        self.session["rows"][0]["home_id"]=self.f["fixture"]["home_id"]
        self.source["rows"][0]["away_label"]="Other team"
        with self.assertRaisesRegex(ValueError,"ROW_IDENTITY_CHANGED"):
            self.build()

    def test_pdf_fingerprint_and_rewritten_price_rejected(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_AND_SESSION_MISMATCH"):
            build_snapshot(self.source,self.session,self.session["rows"][0],
                           self.f,verified_pdf_sha="a"*64)
        self.source["rows"][0]["odds"]["MS2"]=16.7
        with self.assertRaisesRegex(ValueError,"REWRITTEN_PRICES"):
            self.build()

    def test_sha_tamper_stale_and_after_kickoff(self):
        q=self.build()
        q["groups"]["MS"]["prices"]["MS1"]=2.6
        with self.assertRaisesRegex(ValueError,"SNAPSHOT_SHA"):
            extract(q,self.f,NOW)
        q=self.build()
        later=NOW+timedelta(days=2)
        # After KO is not a valid decision time even if PDF itself was earlier.
        with self.assertRaisesRegex(ValueError,"DECISION_AFTER_KICKOFF"):
            decide(self.f,self.b,self.lock,pdf_first_snapshot=q,now=later)

    def test_bridge_reads_real_signed_records_once_and_reports_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name,record in (("forward.json",self.f),("baseline.json",self.b),
                                ("lock.json",self.lock)):
                (root/name).write_text(json.dumps(record),encoding="utf-8")
            with patch("iddaa_pdf_value_bridge_263.verify_original_pdf",return_value=PDF_SHA):
                result=calibrate_session(self.source,self.session,
                         original_pdf="synthetic.pdf",repo_root=root,
                         dev_lock_path="lock.json",now=NOW)
            self.assertEqual(result["n_pdf_first_decisions"],1)
            self.assertEqual(result["n_pdf_first_pas_or_blocked"],0)
            self.assertFalse(result["pilot_count_changed"])
            item=result["rows"][0]
            self.assertEqual(item["value_decision_status"],
                             "RESEARCH_CONDITIONAL_IDDAA_PDF_PRICE_NOT_CURRENT")
            text=_render_pick(item,result)
            self.assertIn("ANA KOŞULLU (PDF): MS 1",text)
            self.assertIn("Canlı fiyat teyidi yok",text)
            import fitz
            report=build_report(result,root/"final.pdf")
            pg=" ".join(page.get_text() for page in fitz.open(report))
            self.assertIn("ANA KOŞULLU",pg)
            self.assertIn("KG Var",pg)
            self.assertNotIn("1.5 Üst",pg)
            self.assertNotIn("3.5 Alt",pg)

    def test_forged_boolean_and_modified_decision_are_not_reported(self):
        q=self.build()
        d=decide(self.f,self.b,self.lock,pdf_first_snapshot=q,now=NOW)
        row=self.session["rows"][0]
        row["pdf_first_price_snapshot"]=q
        row["pdf_linked_policy_decision"]=d
        self.session["policy_dev_lock_sha256"]=self.lock["payload_sha256"]
        self.assertIn("ANA KOŞULLU",_render_pick(row,self.session))
        row["pdf_linked_policy_decision"]=copy.deepcopy(d)
        row["pdf_linked_policy_decision"]["main_candidate"]["market"]="OVER_1.5"
        self.assertIn("PAS",_render_pick(row,self.session))
        del row["pdf_linked_policy_decision"]
        row["frozen_policy_verified"]=True
        self.assertIn("PAS",_render_pick(row,self.session))

    def test_original_real_pdf_required_not_just_links(self):
        with self.assertRaisesRegex(ValueError,"ORIGINAL_USER_PDF_REQUIRED"):
            build_snapshot(self.source,self.session,self.session["rows"][0],self.f)

if __name__=="__main__":unittest.main()
