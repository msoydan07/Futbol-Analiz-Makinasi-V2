"""Isolated synthetic manual quote intake: no actual bookmaker data used."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

from forward_c3 import canonical_bytes
from forward_quad import SCHEMA
from classification_odds_263 import poisson_market
from market_quote_intake_263 import ingest_one, ingest_batch, REQUEST_SCHEMA
from market_fifth_baseline_263 import sealed_payload, evaluate_pair, OBSERVATION_SCHEMA


KO = datetime(2026, 11, 6, 18, 0, tzinfo=timezone.utc)
NOW = KO - timedelta(minutes=50)
CREATED = KO - timedelta(minutes=65)
STEM = "0123456789abcdef01234567"
FORECAST = "forward_quad_263/2026-11-06/" + STEM + ".json"
REQUEST = "experiments/263/market_quote_requests/SYNTHETIC01.json"


def sha_payload(d):
    a=deepcopy(d)
    a["payload_sha256"]=hashlib.sha256(canonical_bytes(a)).hexdigest()
    return a


class ManualOddsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.out=self.root/"locked"
        self.request_path=self.root/REQUEST
        self.request_path.parent.mkdir(parents=True,exist_ok=True)
        self.forecast_path=self.root/FORECAST
        self.forecast_path.parent.mkdir(parents=True,exist_ok=True)
        m=poisson_market(1.7,.6)
        model={name: {"status":"AVAILABLE", "goals":{"markets":m}}
               for name in ("B","C2","C3","M4")}
        forecast=sha_payload({
            "schema":SCHEMA, "created_at_utc":CREATED.isoformat(),
            "fixture":{
                "league":"TUR1","home_id":"AAA","away_id":"BBB",
                "match_local_date":"2026-11-06", "kickoff_utc":KO.isoformat(),
                "fixture_verification":"VERIFIED_BY_LIVE_OFFICIAL_GATE",
                "source_checked_at_utc":(CREATED-timedelta(minutes=2)).isoformat()
            },
            "model_predictions":model,
        })
        self.forecast_path.write_text(json.dumps(forecast),encoding="utf-8")
        self.req={
            "schema":REQUEST_SCHEMA,
            "forecast_path":FORECAST,
            "source_url":"https://www.nesine.com/iddaa/futbol?match=synthetic",
            "source_domain":"nesine.com",
            "reviewer":"Synthetic Human Reviewer",
            "reviewed_at_utc":(NOW-timedelta(minutes=2)).isoformat(),
            "observed_at_utc":(NOW-timedelta(minutes=1)).isoformat(),
            "visible_source_note":"SYNTHETIC match: MS1 1.60 / MSX 4.20 / MS2 6.30; not live data",
            "market_prices":{"MS":{"MS1":1.6,"MSX":4.2,"MS2":6.3}},
        }
        self.save()
    def tearDown(self):
        self.tmp.cleanup()
    def save(self):
        self.request_path.write_text(json.dumps(self.req),encoding="utf-8")
    def ingest(self,now=NOW):
        return ingest_one(REQUEST,root=self.root,output_dir=self.out,now=now)
    def test_success_valid_synced_complete_and_shadownotproven(self):
        r=self.ingest()
        snap=json.loads((self.root/r["path"]).read_text(encoding="utf-8")
                        ) if not Path(r["path"]).is_absolute() else json.loads(Path(r["path"]).read_text())
        self.assertEqual(sealed_payload(snap,OBSERVATION_SCHEMA),r["payload_sha256"])
        self.assertFalse(snap["betting_authorized"])
        self.assertEqual(set(snap["quotes"]),{"MS"})
        self.assertEqual(snap["evidence_scope"],"HUMAN_ATTESTED_NOT_EXTERNALLY_REVERIFIED")
        f=json.loads(self.forecast_path.read_text())
        out=evaluate_pair(forecast=f,observation=snap,
                          final={"home_goals":2,"away_goals":0,"source_url":"https://example.org/final",
                                 "finalized_at_utc":(KO+timedelta(hours=2)).isoformat()},
                          asof=(KO+timedelta(hours=3)).isoformat())
        self.assertEqual(out["groups"]["MS"]["status"],"DESCRIPTIVE_MATCHED_PAIR_NOT_LIVE_VERIFIED")
        self.assertEqual(out["groups"]["KG"]["status"],"NO_SNAPSHOT_FOR_THIS_MARKET")
    def test_refuses_incomplete_group(self):
        self.req["market_prices"]["MS"].pop("MSX");self.save()
        with self.assertRaisesRegex(ValueError,"INCOMPLETE"):self.ingest()
    def test_refuses_stale_quote(self):
        self.req["observed_at_utc"]=(NOW-timedelta(minutes=11)).isoformat()
        self.req["reviewed_at_utc"]=(NOW-timedelta(minutes=12)).isoformat()
        self.save()
        with self.assertRaisesRegex(ValueError,"STALE"):self.ingest()
    def test_refuses_post_kickoff(self):
        with self.assertRaisesRegex(ValueError,"PREGAME"):self.ingest(now=KO+timedelta(minutes=1))
    def test_refuses_changed_forecast(self):
        d=json.loads(self.forecast_path.read_text());d["fixture"]["home_id"]="BAD"
        self.forecast_path.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,"TAMPERED"):self.ingest()
    def test_refuses_wrong_domain(self):
        self.req["source_domain"]="iddaa.com";self.save()
        with self.assertRaisesRegex(ValueError,"DIFFER"):self.ingest()
    def test_refuses_non_accepted_source(self):
        self.req["source_url"]="https://example.org/anything"
        self.req["source_domain"]="example.org";self.save()
        with self.assertRaisesRegex(ValueError,"UNACCEPTED"):self.ingest()
    def test_refuses_wrong_match_forecast_path(self):
        self.req["forecast_path"]="experiments/263/notourforecast.json";self.save()
        with self.assertRaisesRegex(ValueError,"NOT_A_WEEKEND"):self.ingest()
    def test_no_silent_quote_overwrite(self):
        self.ingest()
        with self.assertRaises(FileExistsError):self.ingest()
    def test_blocks_unreviewed_human_source(self):
        self.req["reviewer"]="";self.save()
        with self.assertRaisesRegex(ValueError,"HUMAN_REVIEWER"):self.ingest()
    def test_blocks_wrong_price_bool(self):
        self.req["market_prices"]["MS"]["MSX"]=True;self.save()
        with self.assertRaisesRegex(ValueError,"INVALID_DECIMAL_ODDS"):self.ingest()
    def test_blocks_bad_bookmaker_margin(self):
        self.req["market_prices"]["MS"]={"MS1":1.1,"MSX":1.1,"MS2":1.1};self.save()
        with self.assertRaisesRegex(ValueError,"PRICE_GROUP"):self.ingest()
    def test_batch_keeps_valid_and_blocked_separately(self):
        invalid="experiments/263/market_quote_requests/invalid.json"
        (self.root/invalid).write_text("{}",encoding="utf-8")
        result=ingest_batch([REQUEST,invalid],root=self.root,output_dir=self.out,
                            report_path=self.root/"report.json",now=NOW)
        self.assertEqual(result["accepted"],1)
        self.assertEqual(result["blocked"],1)
        self.assertTrue((self.root/"report.json").is_file())
    def test_future_observation_rejected(self):
        self.req["observed_at_utc"]=(NOW+timedelta(minutes=1)).isoformat();self.save()
        with self.assertRaisesRegex(ValueError,"FUTURE"):self.ingest()
    def test_all_markets_are_symmetric_when_provided(self):
        self.req["market_prices"].update({
            "KG":{"BTTS_YES":1.85,"BTTS_NO":1.86},
            "GOALS_2.5":{"OVER_2.5":1.88,"UNDER_2.5":1.82}})
        self.save()
        r=self.ingest()
        self.assertEqual(set(r["market_groups"]),{"MS","KG","GOALS_2.5"})


if __name__=="__main__":unittest.main()
