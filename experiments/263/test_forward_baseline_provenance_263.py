import importlib.util
from pathlib import Path
import unittest
def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
base=load("forward_baseline_provenance_263")
fixtures=load("test_forward_calibration_bridge_263")
def forecast():
    x=fixtures.forecast()
    x["fixture"]["league"]="TUR1"
    x["fixture"]["match_local_date"]="2026-11-06"
    x["data"]["snapshot_sha256"]="f"*64
    x["data"]["snapshot_acceptance"]="APPEND_ONLY_HUMAN_SOURCE_ATTESTED_NOT_INDEPENDENTLY_RECHECKED"
    x["data"]["league_latest_result_date"]="2026-11-05"
    x["payload_sha256"]=base._digest({k:v for k,v in x.items() if k!="payload_sha256"})
    return x
def baseline(f):
    b={"schema":base.SCHEMA,"forecast_sha256":f["payload_sha256"],
       "league":"TUR1","method":"PAST_RESULTS_LEAGUE_MARKET_RATE",
       "source_snapshot_sha256":"f"*64,"historical_match_count":587,
       "last_result_date":"2026-11-05","forecast_created_at_utc":f["created_at_utc"],
       "created_at_utc":"2026-11-06T16:00:00Z",
       "markets":{k:.4 for k in base.MARKETS}}
    b["payload_sha256"]=base._digest(b);return b
def reseal(b):
    b["payload_sha256"]=base._digest({k:v for k,v in b.items() if k!="payload_sha256"})
class TestBaseline(unittest.TestCase):
    def test_sealed_research_only(self):
        f=forecast();out=base.connect_verified_baseline(f,fixtures.lock(),baseline(f))
        self.assertFalse(out["betting_authorized"])
        self.assertEqual(out["pilot_count_increment"],0)
        self.assertIn("SHA_SEALED",out["baseline_status"])
    def test_tampered(self):
        f=forecast();b=baseline(f);b["markets"]["MS1"]=.99
        with self.assertRaisesRegex(ValueError,"HASH"):base.connect_verified_baseline(f,fixtures.lock(),b)
    def test_post_kickoff_is_rejected(self):
        f=forecast();b=baseline(f);b["created_at_utc"]="2026-11-06T17:00:00Z";reseal(b)
        with self.assertRaisesRegex(ValueError,"LOOKAHEAD"):base.connect_verified_baseline(f,fixtures.lock(),b)
    def test_backdated_is_rejected(self):
        f=forecast();b=baseline(f);b["created_at_utc"]="2026-11-06T15:59:00Z";reseal(b)
        with self.assertRaisesRegex(ValueError,"LOOKAHEAD"):base.connect_verified_baseline(f,fixtures.lock(),b)
    def test_delayed_creation_is_rejected(self):
        f=forecast();b=baseline(f);b["created_at_utc"]="2026-11-06T16:11:00Z";reseal(b)
        with self.assertRaisesRegex(ValueError,"LOOKAHEAD"):base.connect_verified_baseline(f,fixtures.lock(),b)
    def test_real_later_pre_kickoff_creation_is_allowed(self):
        f=forecast();b=baseline(f);b["created_at_utc"]="2026-11-06T16:02:00Z";reseal(b)
        self.assertEqual(base.connect_verified_baseline(f,fixtures.lock(),b)["pilot_count_increment"],0)
    def test_wrong_forecast_recorded_time_rejected(self):
        f=forecast();b=baseline(f);b["forecast_created_at_utc"]="2026-11-06T15:59:00Z";reseal(b)
        with self.assertRaisesRegex(ValueError,"FORECAST_TIME_MISMATCH"):base.connect_verified_baseline(f,fixtures.lock(),b)
    def test_future_results_rejected(self):
        f=forecast();b=baseline(f);b["last_result_date"]="2026-11-06";reseal(b)
        with self.assertRaisesRegex(ValueError,"LEAKAGE"):base.connect_verified_baseline(f,fixtures.lock(),b)
    def test_wrong_source_rejected(self):
        f=forecast();b=baseline(f);b["source_snapshot_sha256"]="a"*64;reseal(b)
        with self.assertRaisesRegex(ValueError,"SOURCE"):base.connect_verified_baseline(f,fixtures.lock(),b)
    def test_unsealed_missing(self):
        with self.assertRaisesRegex(ValueError,"PROVENANCE"):base.connect_verified_baseline(forecast(),fixtures.lock(),{})
if __name__=="__main__":unittest.main()
