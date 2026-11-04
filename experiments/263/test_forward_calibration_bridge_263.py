import importlib.util
from pathlib import Path
import unittest
def load(n):
    spec=importlib.util.spec_from_file_location(n,Path(__file__).with_name(n+".py"))
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
b=load("forward_calibration_bridge_263")
def lock():
    x={"schema":b.CAL_SCHEMA,"source_stage2_sha256":"a"*64,
       "source_predictions_sha256":"b"*64,"development_period":"2026-08-01/2026-09-30",
       "evaluation_period_not_used_for_weights":"2026-10-01/2026-10-29",
       "calibration":{"M4":{k:{"n":587,"available":True,"development_brier_skill":.1,"weight":.7} for k in b.MARKETS},
                      "C3":{k:{"n":580,"available":True,"development_brier_skill":.1,"weight":.7} for k in b.MARKETS}},
       "official_approval":False}
    x["payload_sha256"]=b._digest(x);return x
def forecast():
    mk={"1X2":{"H":.7,"D":.2,"A":.1},"BTTS_YES":.6,"BTTS_NO":.4}
    for line in ("1.5","2.5","3.5"):
        mk["OVER_"+line]=.7;mk["UNDER_"+line]=.3
    x={"schema":b.FORECAST_SCHEMA,"status":"EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING",
       "created_at_utc":"2026-11-06T16:00:00+00:00",
       "fixture":{"kickoff_utc":"2026-11-06T17:00:00+00:00",
                  "fixture_verification":"VERIFIED_BY_LIVE_OFFICIAL_GATE"},
       "data":{"human_source_acceptance":True,"research_shadow_unverified_source":False},
       "model_predictions":{"M4":{"status":"AVAILABLE","goals":{"markets":mk}}}}
    x["payload_sha256"]=b._digest(x);return x
class TestBridge(unittest.TestCase):
    def test_research_only(self):
        out=b.connect(forecast(),lock(),asof_baselines={k:.4 for k in b.MARKETS})
        self.assertFalse(out["betting_authorized"])
        self.assertIsNone(out["official_S1"])
        self.assertEqual(out["pilot_count_increment"],0)
        self.assertEqual(out["baseline_status"],"CALLER_SUPPLIED_ASOF_UNVERIFIED_BY_BRIDGE")
    def test_reject_modified_forecast(self):
        f=forecast();f["created_at_utc"]="2026-11-06T16:30:00+00:00"
        with self.assertRaisesRegex(ValueError,"FORECAST_HASH"):b.connect(f,lock(),asof_baselines={k:.4 for k in b.MARKETS})
    def test_reject_modified_lock(self):
        l=lock();l["calibration"]["M4"]["MS1"]["weight"]=.1
        with self.assertRaisesRegex(ValueError,"CALIBRATION_LOCK_HASH"):b.connect(forecast(),l,asof_baselines={k:.4 for k in b.MARKETS})
    def test_reject_missing_baseline(self):
        with self.assertRaisesRegex(ValueError,"ASOF_BASELINES"):b.connect(forecast(),lock(),asof_baselines={})
    def test_reject_shadow(self):
        f=forecast();f["status"]="EXPERIMENTAL_EARLY_SHADOW_UNVERIFIED_SOURCE_NO_BETTING"
        f["payload_sha256"]=b._digest({k:v for k,v in f.items() if k!="payload_sha256"})
        with self.assertRaisesRegex(ValueError,"NOT_ACCEPTED_FORWARD"):b.connect(f,lock(),asof_baselines={k:.4 for k in b.MARKETS})
    def test_reject_unavailable_model(self):
        f=forecast();f["model_predictions"]["M4"]["status"]="UNAVAILABLE"
        f["payload_sha256"]=b._digest({k:v for k,v in f.items() if k!="payload_sha256"})
        with self.assertRaisesRegex(ValueError,"M4_UNAVAILABLE"):b.connect(f,lock(),asof_baselines={k:.4 for k in b.MARKETS})
if __name__=="__main__":unittest.main()
