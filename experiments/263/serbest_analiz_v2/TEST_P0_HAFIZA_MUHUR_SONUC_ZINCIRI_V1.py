#!/usr/bin/env python3
# coding: utf-8
import unittest,datetime as dt
from unittest.mock import patch
from P0_HAFIZA_MUHUR_SONUC_ZINCIRI_V1 import (
    hash_obj,check_receipt,make_records,event_truth,evaluate_once,OddsForwardError,
    RECEIPT_SCHEMA,RECEIPT_STATUS,SCORE_SCHEMA)

UTC=dt.timezone.utc
NOW=dt.datetime(2026,11,24,9,0,tzinfo=UTC)
KICKOFF="2026-11-24T15:00:00+00:00"
SEVEN={"MS1":"0.6","MSX":"0.2","MS2":"0.2","OVER_2.5":"0.55","UNDER_2.5":"0.45",
       "BTTS_YES":"0.54","BTTS_NO":"0.46"}

def receipt():
    a={"schema":RECEIPT_SCHEMA,"status":RECEIPT_STATUS,
       "kickoff_utc":KICKOFF,"observed_at_utc":NOW.isoformat(),
       "official_verification":"OFFICIAL_FIXTURE_GATEWAY_LOOKUP",
       "official_source_url":"https://example.org/official","fixture_key":"fixture_1",
       "source_pdf_sha256":"a"*64,"match":"A - B",
       "expert_probabilities":{"P0":SEVEN,"HAFIZA":SEVEN}}
    a["payload_sha256"]=hash_obj(a)
    return a

def stage():
    odds={"MS1":"1.5","MSX":"4","MS2":"4","OVER_2.5":"1.6","UNDER_2.5":"2",
          "BTTS_YES":"1.6","BTTS_NO":"2"}
    return {"records":[{
        "source_row":1,"match_name_pdf":"A - B","kickoff_local_time_user_label":"18:00",
        "seven_raw_odds":odds,"p0_seven_proportional":SEVEN,
        "hafiza_seven_realized":SEVEN,"hafiza_similar_n":100
        }],
        "source_pdf_sha256":"b"*64,"staging_payload_sha256":"c"*64,
        "archive_total_matches":35938}
class ForwardTests(unittest.TestCase):
    def test_receipt_sha(self):
        a=receipt();self.assertIs(check_receipt(a,NOW),a)
        a["expert_probabilities"]["P0"]["MS1"]="0.7"
        with self.assertRaises(OddsForwardError):check_receipt(a)
    def test_preko_block_after_kickoff(self):
        with self.assertRaises(OddsForwardError):
            check_receipt(receipt(),dt.datetime(2026,11,24,16,tzinfo=UTC))
    def test_gate_fixture_name_time_checked(self):
        a=stage();official={"status":"VERIFIED","league":"GER1",
           "home_id":"h","away_id":"a","kickoff_utc":KICKOFF,
           "retrieved_at_utc":NOW.isoformat(),"source_url":"https://example.org/official"}
        b=[{"source_row":1,"league":"GER1","home":"A","away":"B","date_local_tr":"2026-11-24"}]
        with patch("P0_HAFIZA_MUHUR_SONUC_ZINCIRI_V1.verify_mobile",return_value={}),\
             patch("P0_HAFIZA_MUHUR_SONUC_ZINCIRI_V1.pdf_rows",return_value=([a["records"][0]["seven_raw_odds"]],[])),\
             patch("P0_HAFIZA_MUHUR_SONUC_ZINCIRI_V1.independent_pdf_fixture_rows",return_value=([{"kickoff_time":"18:00","match_label":"A - B"}])):
             records=make_records(a,b"original_pdf_bytes",b,lambda *args:official,now=NOW)
             self.assertEqual(len(records),1)
             self.assertEqual(check_receipt(records[0])["expert_probabilities"]["P0"],SEVEN)
             b[0]["date_local_tr"]="2026-11-25"
             with self.assertRaises(OddsForwardError):
                 make_records(a,b"original_pdf_bytes",b,lambda *args:official,now=NOW)
    def test_unverified_league_rejected(self):
        a=stage();b=[{"source_row":1,"league":"XYZ","home":"A","away":"B",
                      "date_local_tr":"2026-11-24"}]
        with patch("P0_HAFIZA_MUHUR_SONUC_ZINCIRI_V1.verify_mobile",return_value={}),\
             patch("P0_HAFIZA_MUHUR_SONUС_ZINCIRI_V1.pdf_rows",return_value=([a["records"][0]["seven_raw_odds"]],[])):
            pass
    def test_provisional_score_correctness(self):
        r=receipt()
        d={"schema":SCORE_SCHEMA,"scores":[
           {"fixture_key":"fixture_1","match_status":"FINAL",
            "home_goals":2,"away_goals":1,"observed_after_utc":"2026-11-24T17:00:00Z"}]}
        out=evaluate_once([r],d,now=dt.datetime(2026,11,25,tzinfo=UTC))
        self.assertEqual(out["hit_count"]["P0"],1)
        self.assertEqual(out["provisional_scored"],1)
        self.assertIn("PROVISIONAL",out["status"])
    def test_pending_when_not_kicked_off(self):
        out=evaluate_once([receipt()],{"schema":SCORE_SCHEMA,"scores":[]},now=NOW)
        self.assertEqual(out["pending"],1)
    def test_no_result_leak_before_ko(self):
        d={"schema":SCORE_SCHEMA,"scores":[
           {"fixture_key":"fixture_1","match_status":"FINAL","home_goals":2,"away_goals":1,
            "observed_after_utc":"2026-11-24T14:00:00Z"}]}
        with self.assertRaises(OddsForwardError):
            evaluate_once([receipt()],d,now=dt.datetime(2026,11,25,tzinfo=UTC))
    def test_truth_three_markets(self):
        y=event_truth(2,1)
        self.assertEqual(y["MS1"],1)
        self.assertEqual(y["OVER_2.5"],1)
        self.assertEqual(y["BTTS_YES"],1)
if __name__=="__main__":unittest.main()
