"""Offline NEW100-to-Pinnacle same-job, credit locks, exact market and PAS.

All odds here are SYNTHETIC and never call The Odds API.
"""
import copy,hashlib,json,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from free_bulk_odds_263 import canonical
from sabah_batch_263 import sha
from sabah_pinnacle_credit_guard_263 import reserve
from pinnacle_market_benchmark_263 import compare
from sabah_pinnacle_new100_bridge_263 import (
    plan,prequery,render,mobile,validate_snapshot,PriceBridgeBlocked,digest)
from sabah_pinnacle_capture_263 import SNAP
from test_pinnacle_market_benchmark_263 import bulk,NOW

ORIGINAL=Path("forward_quad_263/2026-11-06/1d6b6f16fef8bac971c184c4.json")
NAME="1d6b6f16fef8bac971c184c4"
def seal(data):
    data.pop("payload_sha256",None)
    data["payload_sha256"]=sha(data)
    return data

class New100PinnacleBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.f=json.loads(ORIGINAL.read_text(encoding="utf-8"))
        self.rel="forward_morning_263/2026-11-06/"+NAME+".json"
        target=self.root/self.rel;target.parent.mkdir(parents=True)
        target.write_text(json.dumps(self.f),encoding="utf-8")
        self.report=seal({
            "schema":"SABAH_TOPLU_KAYIT_V1","cohort":"new100",
            "day_turkey":"2026-11-06","input_count":1,"new_forecasts":1,
            "outcomes":[{"status":"REGISTERED_FOUR_MODELS_EXPERIMENTAL",
                         "league":"TUR1","home":"Gaziantep","away":"Kasımpaşa",
                         "forecast_path":self.rel,
                         "forecast_sha256":self.f["payload_sha256"],
                         "decision_status":"RESEARCH_PAS"}]})
        self.receipt=seal({
            "schema":"263_NEW100_FORWARD_MOBILE_ACCEPTANCE_V1",
            "cohort":"new100","new_count":1,"bookmaker_api_calls":0,
            "batch_report_sha256":self.report["payload_sha256"],
            "records":[{"forecast_path":self.rel,
                        "forecast_sha256":self.f["payload_sha256"]}]})
        self.ledger=self.root/"experiments/263/pinnacle_daily_reservations"
        self.snapshots=self.root/"experiments/263/pinnacle_daily_snapshots"
        self.decision=seal({"schema":"263_four_model_value_decision_research_v1",
            "status":"RESEARCH_PAS","forecast_sha256":self.f["payload_sha256"],
            "quote_sha256":None,"main_candidate":None,"betting_authorized":False,
            "all_market_diagnostics":[
                {"market":"MS1","calibrated_probability":.53,"anchor_model":"M4",
                 "dev_brier_skill":.02,"support_count":3},
                {"market":"MSX","calibrated_probability":.24,"anchor_model":"C3",
                 "dev_brier_skill":.01,"support_count":3},
                {"market":"MS2","calibrated_probability":None,"anchor_model":None,
                 "dev_brier_skill":None,"support_count":0}]})
        self.report["outcomes"][0]["decision_sha256"]=self.decision["payload_sha256"]
        self.report=seal(self.report)
        self.receipt["batch_report_sha256"]=self.report["payload_sha256"]
        self.receipt=seal(self.receipt)
        folder=self.root/"experiments/263/sabah_research/new100/2026-11-06"/NAME
        folder.mkdir(parents=True)
        (folder/"decision.json").write_text(json.dumps(self.decision),encoding="utf-8")
    def snapshot(self,bulk_value=None):
        val=bulk() if bulk_value is None else bulk_value
        snap={"schema":SNAP,"league":"TUR1","day_turkey":"2026-11-06",
              "bookmaker":"pinnacle","market":"h2h","provider":"The Odds API",
              "retry_automatically":False,"betting_authorized":False,
              "source_bulk":val,"status":"OBSERVED_OR_EMPTY"}
        snap["payload_sha256"]=digest(snap)
        path=self.snapshots/"2026-11-06/TUR1.json"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(snap),encoding="utf-8")
        return path
    def test_one_league_not_per_match_and_T_minus_60(self):
        x=plan(self.report,self.receipt,self.root,self.ledger,NOW)
        self.assertEqual(x["leagues"],["TUR1"])
        self.assertEqual(x["max_external_calls"],1)
        self.assertEqual(x["eligible_forecasts_by_league"]["TUR1"],[self.rel])
        self.assertFalse(x["betting_authorized"])
    def test_outside_20_to_90_minute_window_does_not_spend(self):
        x=plan(self.report,self.receipt,self.root,self.ledger,datetime(2026,11,6,16,48,tzinfo=timezone.utc))
        self.assertEqual(x["leagues"],[])
        self.assertEqual(x["max_external_calls"],0)
    def test_same_time_forecast_older_than_10min_denied(self):
        later=NOW+timedelta(minutes=11)
        x=plan(self.report,self.receipt,self.root,self.ledger,later)
        self.assertEqual(x["leagues"],[])
        with self.assertRaises(PriceBridgeBlocked):
            prequery(self.report,self.receipt,self.root,"TUR1",later)
    def test_persistent_one_credit_reservation_excludes_requery(self):
        reserve(self.ledger,"TUR1",NOW)
        x=plan(self.report,self.receipt,self.root,self.ledger,NOW)
        self.assertEqual(x["leagues"],[])
        self.assertEqual(x["skipped"][0]["reason"],"DAILY_LEAGUE_PINNACLE_CREDIT_ALREADY_RESERVED")
        # prequery is deliberately separate and must only be called after
        # a brand new reservation has been pushed by the CI job.
        self.assertEqual(prequery(self.report,self.receipt,self.root,"TUR1",NOW)["league"],"TUR1")
    def test_missing_unchanged_secret_yields_explicit_PAS(self):
        before=(self.root/self.rel).read_bytes()
        x=render(self.report,self.receipt,self.root,self.snapshots)
        self.assertEqual(x["matches_compared"],0)
        self.assertEqual(x["items"][0]["reason"],"NO_DAILY_PINNACLE_SNAPSHOT")
        self.assertEqual(before,(self.root/self.rel).read_bytes())
        self.assertIn("MS piyasa kıyası",mobile(x))
    def test_valid_synthetic_pinnacle_compares_calibrated_and_4_models(self):
        self.snapshot()
        original=(self.root/self.rel).read_bytes()
        report=render(self.report,self.receipt,self.root,self.snapshots)
        self.assertEqual(report["matches_compared"],1)
        row=report["items"][0]
        self.assertEqual(row["status"],"READ_ONLY_SAME_TIME_PINNACLE_AND_CALIBRATED")
        self.assertEqual(set(row["comparison"]["models"]),{"B","C2","C3","M4"})
        self.assertAlmostEqual(sum(row["comparison"]["pinnacle_no_vig_probabilities"].values()),1)
        self.assertAlmostEqual(row["calibrated_MS_research"]["MS1"]["calibrated_probability"],.53)
        self.assertIsNone(row["calibrated_MS_research"]["MS2"]["calibrated_probability"])
        self.assertFalse(row["betting_authorized"])
        self.assertEqual(before if False else original,(self.root/self.rel).read_bytes())
        self.assertEqual(self.decision["payload_sha256"],row["original_PAS_decision_sha256"])
    def test_tampered_snapshot_is_fail_closed(self):
        p=self.snapshot()
        bad=json.loads(p.read_text())
        bad["source_bulk"]={"tampered":"not a real market"}
        p.write_text(json.dumps(bad))
        with self.assertRaises(PriceBridgeBlocked):render(self.report,self.receipt,self.root,self.snapshots)
    def test_wrong_receipt_sha_never_requests_api(self):
        receipt=dict(self.receipt)
        receipt["batch_report_sha256"]="0"*64
        with self.assertRaises(PriceBridgeBlocked):plan(self.report,receipt,self.root,self.ledger,NOW)
    def test_quote_replay_stale_is_not_synchronized(self):
        fake=bulk(now=NOW+timedelta(minutes=15))
        # Existing quote is outside forecast's 10 min anchor, hence never usable.
        self.snapshot(fake)
        x=render(self.report,self.receipt,self.root,self.snapshots)
        self.assertEqual(x["matches_compared"],0)
        self.assertEqual(x["items"][0]["reason"],"FORECAST_AND_PRICE_MORE_THAN_10_MIN_APART")
    def test_three_of_four_missing_B_not_imputed(self):
        f=copy.deepcopy(self.f)
        f["model_predictions"]["B"]={"status":"UNAVAILABLE_INSUFFICIENT_CONTEXT"}
        seal(f)
        observation=bulk()
        out=compare(f,observation)
        self.assertEqual(out["status"],"READ_ONLY_SAME_TIME_BENCHMARK")
        self.assertEqual(out["available_model_count"],3)
        self.assertEqual(out["model_missing_not_imputed"]["B"]["status"],"UNAVAILABLE_INSUFFICIENT_CONTEXT")
        self.assertNotIn("B",out["models"])
    def test_M4_missing_ever_stays_unavailable(self):
        f=copy.deepcopy(self.f)
        f["model_predictions"]["M4"]={"status":"UNAVAILABLE"}
        seal(f)
        o=compare(f,bulk())
        self.assertEqual(o["reason"],"C3_M4_AND_THREE_AVAILABLE_MODELS_REQUIRED")
    def test_no_old_pilot_or_other_date_can_be_priced(self):
        other=copy.deepcopy(self.report);other["cohort"]="legacy96";seal(other)
        with self.assertRaises(PriceBridgeBlocked):plan(other,self.receipt,self.root,self.ledger,NOW)
        with self.assertRaises(PriceBridgeBlocked):
            plan(self.report,self.receipt,self.root,self.ledger,datetime(2026,11,7,16,20,tzinfo=timezone.utc))
if __name__=="__main__":unittest.main()
