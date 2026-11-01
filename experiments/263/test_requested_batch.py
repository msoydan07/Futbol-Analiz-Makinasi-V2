"""New batch-queue contract tests only; synthetic gates, NO genuine predictions.

Do not re-run the five old model tests or old historical backtest.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import hashlib
from run_requested_batch import (load_request, record_batch, canonical_bytes,
                                 REQUEST_SCHEMA, FROZEN_MODEL_SHA,
                                 FROZEN_FORWARD_SHA)


class RequestBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        p = self.root / "experiments/263"
        (p / "requests").mkdir(parents=True)
        (p / "exp_263_batch.py").write_text("FROZEN_MODEL_STUB", encoding="utf-8")
        (p / "forward_c3.py").write_text("FROZEN_FORWARD_STUB", encoding="utf-8")
        self.request = "experiments/263/requests/batch_01.json"
        self.records = self.root / "forward_263"
        self.report = self.root / "reports/batch_01.json"
        self.match = {"league":"TUR1","home":"AAA","away":"BBB"}
        self.payload = {"schema":REQUEST_SCHEMA,"matches":[self.match]}
        self.save_request(self.payload)
        self.gate = {"status":"VERIFIED","league":"TUR1","home_id":"ID-AAA","away_id":"ID-BBB",
                     "kickoff_utc":"2026-11-03T17:00:00+00:00"}

    def save_request(self, data):
        (self.root / self.request).write_text(json.dumps(data),encoding="utf-8")

    def fake_predict(self, gate, history, out_dir, now=None):
        from datetime import datetime
        target = Path(out_dir) / "2026-11-03" / "abc123.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        item = {"fixture": {"league":gate["league"],"home_id":gate["home_id"],
                            "away_id":gate["away_id"],"match_local_date":"2026-11-03"},
                "created_at_utc":"2026-11-01T12:00:00+00:00"}
        item["payload_sha256"] = hashlib.sha256(canonical_bytes(item)).hexdigest()
        with target.open("x") as f: json.dump(item,f)
        return target,item

    def execute(self, lookup=None, paths=None, report=None):
        return record_batch(paths or [self.request],self.root,"fake_history.csv",
                            self.records,report or self.report,lookup=lookup or (lambda *args:self.gate))

    def test_requested_names_create_one_record_and_report(self):
        with patch("run_requested_batch.sha256_file", side_effect=[FROZEN_MODEL_SHA,FROZEN_FORWARD_SHA]), \
             patch("run_requested_batch.predict_from_verified_gate", side_effect=self.fake_predict):
            report=self.execute()
        self.assertEqual(report["statuses"]["REGISTERED_EXPERIMENTAL"],1)
        self.assertEqual(report["source_model_sha256"],FROZEN_MODEL_SHA)
        self.assertTrue(self.report.is_file())
        self.assertEqual(len(list(self.records.glob("*/*.json"))),1)

    def test_official_gate_rejects_without_prediction(self):
        with patch("run_requested_batch.sha256_file",side_effect=[FROZEN_MODEL_SHA,FROZEN_FORWARD_SHA]), \
             patch("run_requested_batch.predict_from_verified_gate") as predictor:
            report=self.execute(lookup=lambda *args:{"status":"NOT_VERIFIED","reason":"no_official_fixture"})
        self.assertEqual(report["statuses"]["BLOCKED_NO_FORECAST"],1)
        predictor.assert_not_called()

    def test_existing_record_not_overwritten(self):
        with patch("run_requested_batch.sha256_file",side_effect=[FROZEN_MODEL_SHA,FROZEN_FORWARD_SHA]), \
             patch("run_requested_batch.predict_from_verified_gate",side_effect=self.fake_predict):
            self.execute()
        with patch("run_requested_batch.sha256_file",side_effect=[FROZEN_MODEL_SHA,FROZEN_FORWARD_SHA]), \
             patch("run_requested_batch.predict_from_verified_gate") as predictor:
            report=self.execute(report=self.root/"reports/another.json")
        self.assertEqual(report["statuses"]["ALREADY_REGISTERED_NO_OVERWRITE"],1)
        predictor.assert_not_called()

    def test_tampered_existing_record_blocks_batch(self):
        with patch("run_requested_batch.sha256_file",side_effect=[FROZEN_MODEL_SHA,FROZEN_FORWARD_SHA]), \
             patch("run_requested_batch.predict_from_verified_gate",side_effect=self.fake_predict):
            self.execute()
        p=next(self.records.glob("*/*.json"))
        item=json.loads(p.read_text());item["created_at_utc"]="2019-01-01"
        p.write_text(json.dumps(item))
        with patch("run_requested_batch.sha256_file",side_effect=[FROZEN_MODEL_SHA,FROZEN_FORWARD_SHA]):
            with self.assertRaisesRegex(ValueError,"tampered_existing_forecast"):
                self.execute(report=self.root/"reports/new.json")

    def test_request_cannot_supply_fixture_date_or_gate(self):
        self.save_request({"schema":REQUEST_SCHEMA,"matches":[{**self.match,"kickoff":"tomorrow"}]})
        with self.assertRaisesRegex(ValueError,"bad_match_keys"):
            load_request(self.request,self.root)

    def test_refuse_changes_to_frozen_model(self):
        with patch("run_requested_batch.sha256_file",return_value="WRONG_HASH"):
            with self.assertRaisesRegex(ValueError,"frozen_C3_model_hash_mismatch"):
                self.execute()

    def test_batch_partial_success_visible_and_one_report(self):
        self.save_request({"schema":REQUEST_SCHEMA,"matches":[self.match,{"league":"ENG1","home":"CCC","away":"DDD"}]})
        def checker(league,*other):
            return self.gate if league=="TUR1" else {"status":"NOT_VERIFIED","reason":"missing"}
        with patch("run_requested_batch.sha256_file",side_effect=[FROZEN_MODEL_SHA,FROZEN_FORWARD_SHA]), \
             patch("run_requested_batch.predict_from_verified_gate",side_effect=self.fake_predict):
            r=self.execute(lookup=checker)
        self.assertEqual(r["statuses"]["REGISTERED_EXPERIMENTAL"],1)
        self.assertEqual(r["statuses"]["BLOCKED_NO_FORECAST"],1)
        self.assertEqual(len(r["outcomes"]),2)


if __name__ == "__main__": unittest.main()
