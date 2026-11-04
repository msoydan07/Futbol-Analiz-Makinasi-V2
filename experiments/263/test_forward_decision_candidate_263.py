"""Contract tests: frozen research adapter must never approve a bet."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location("adapter",Path(__file__).with_name("forward_decision_candidate_263.py"))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixture():
    markets={}
    for k in m.MARKETS:
        markets[k]={"raw_probability":.8,"asof_baseline":.5,
            "development_calibration":{"n":587,"available":True,"development_brier_skill":.1,"weight":.7}}
    return {"record_type":"FORWARD_PREMATCH_LOCKED","immutable_record_id":"test-locked",
        "asof_utc":"2026-11-06T16:00:00Z","kickoff_utc":"2026-11-06T17:00:00Z",
        "fixture_verified":True,"source_fresh":True,"model":"M4","markets":markets}
class TestAdapter(unittest.TestCase):
    def test_never_approves(self):
        x=m.decide(fixture())
        self.assertEqual(x["status"],"RESEARCH_CANDIDATE_NOT_APPROVED")
        self.assertIsNone(x["official_S1"]);self.assertIsNone(x["official_S2"])
        self.assertFalse(x["betting_authorized"]);self.assertEqual(x["pilot_count_increment"],0)
        self.assertNotEqual(x["main_candidate"]["family"],x["alternative_candidate"]["family"])
    def test_no_fixture(self):
        f=fixture();f["fixture_verified"]=False
        self.assertEqual(m.decide(f)["pas_reasons"],["FIXTURE_UNVERIFIED"])
    def test_no_development_skill(self):
        f=fixture()
        for x in f["markets"].values():x["development_calibration"]["development_brier_skill"]=-.1
        self.assertEqual(m.decide(f)["pas_reasons"],["NO_RELIABLE_CANDIDATE"])
    def test_no_c2_fallback(self):
        f=fixture();f["model"]="C2"
        self.assertEqual(m.decide(f)["pas_reasons"],["NO_MODEL_COVERAGE"])
    def test_reject_unsealed_and_postko(self):
        f=fixture();f["record_type"]="RETROSPECTIVE_ASOF_NOT_SEALED"
        with self.assertRaises(ValueError):m.decide(f)
        f=fixture();f["asof_utc"]=f["kickoff_utc"]
        with self.assertRaises(ValueError):m.decide(f)
    def test_invalid_probability(self):
        f=fixture();f["markets"]["MS1"]["raw_probability"]=float("nan")
        with self.assertRaises(ValueError):m.decide(f)
if __name__=="__main__":unittest.main()
