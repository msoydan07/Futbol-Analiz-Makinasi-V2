"""Experimental display must never promote candidates to official picks."""
import importlib.util
from pathlib import Path
import unittest
def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
adapter=load("forward_decision_candidate_263")
view=load("forward_decision_view_263")
def fixture():
    return {"record_type":"FORWARD_PREMATCH_LOCKED","immutable_record_id":"example-lock",
        "asof_utc":"2026-11-06T16:00:00Z","kickoff_utc":"2026-11-06T17:00:00Z",
        "fixture_verified":True,"source_fresh":True,"model":"M4",
        "markets":{k:{"raw_probability":.8,"asof_baseline":.5,
            "development_calibration":{"n":587,"available":True,"development_brier_skill":.1,"weight":.7}}
            for k in adapter.MARKETS}}
class TestView(unittest.TestCase):
    def test_candidate_stays_unapproved(self):
        out=view.render(adapter.decide(fixture()))
        self.assertIn("RESMÎ TERCİH YOK",out)
        self.assertIn("Ana aday (onaysız)",out)
        self.assertIn("Alternatif aday (onaysız)",out)
        self.assertIn("Oran/EV",out)
    def test_pas_reason_visible(self):
        f=fixture();f["source_fresh"]=False
        self.assertIn("SOURCE_STALE",view.render(adapter.decide(f)))
    def test_reject_forged_approval(self):
        x=adapter.decide(fixture());x["official_S1"]="MS1"
        with self.assertRaises(ValueError):view.render(x)
    def test_reject_same_family_alternative(self):
        x=adapter.decide(fixture());x["alternative_candidate"]=dict(x["main_candidate"])
        with self.assertRaises(ValueError):view.render(x)
if __name__=="__main__":unittest.main()
