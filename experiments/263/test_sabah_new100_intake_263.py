"""No-op workflow readiness probe and user-named intake: zero network."""
import json,os,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from sabah_new100_request_intake_263 import inspect,IntakeBlocked
NOW=datetime(2026,11,7,9,0,tzinfo=timezone.utc)
class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=os.getcwd()
        os.chdir(self.tmp.name)
        Path("experiments/263/sabah_readiness_probes").mkdir(parents=True)
        Path("experiments/263/sabah_requests").mkdir(parents=True)
    def tearDown(self):os.chdir(self.old);self.tmp.cleanup()
    def probe(self,data=None):
        p=Path("experiments/263/sabah_readiness_probes/probe.json")
        value=data or {"schema":"NEW100_READINESS_PROBE_V1",
                       "day_turkey":"2026-11-07",
                       "mode":"NO_MODELS_NO_ODDS_NO_PILOT","cohort":"new100"}
        p.write_text(json.dumps(value),encoding="utf-8")
        return inspect(str(p),now=NOW)
    def request(self,matches=None):
        p=Path("experiments/263/sabah_requests/user_choice.json")
        data={"schema":"SABAH_TOPLU_V1","day_turkey":"2026-11-07",
              "matches":matches or [{"league":"ENG1","home":"A","away":"B"}]}
        p.write_text(json.dumps(data),encoding="utf-8")
        return inspect(str(p),now=NOW)
    def test_noop_probe_cannot_start_pilot(self):
        a=self.probe()
        self.assertEqual(a["kind"],"readiness_only")
        self.assertEqual(a["new_pilot_records"],0)
        self.assertEqual(a["bookmaker_api_calls"],0)
        self.assertFalse(a["manual_dispatch_confirmed"])
    def test_probe_with_match_is_rejected(self):
        data={"schema":"NEW100_READINESS_PROBE_V1",
              "day_turkey":"2026-11-07","mode":"NO_MODELS_NO_ODDS_NO_PILOT",
              "cohort":"new100","matches":[{"league":"TUR1","home":"A","away":"B"}]}
        with self.assertRaises(IntakeBlocked):self.probe(data)
    def test_real_named_user_request_routes_without_automatic_selector(self):
        r=self.request()
        self.assertEqual(r["kind"],"real_named_request")
        self.assertTrue(r["not_an_automatic_match_selector"])
        self.assertEqual(r["fixture_count"],1)
    def test_date_only_future_day_never_forges_real_request(self):
        p=Path("experiments/263/sabah_requests/user_choice.json")
        p.write_text(json.dumps({"schema":"SABAH_TOPLU_V1",
            "day_turkey":"2026-11-08",
            "matches":[{"league":"TUR1","home":"A","away":"B"}]}))
        with self.assertRaises(IntakeBlocked):inspect(str(p),now=NOW)
    def test_old_copies_cannot_enter_request_channel(self):
        p=Path("experiments/263/sabah_readiness_probes/probe.json")
        p.write_text("{}",encoding="utf-8")
        with self.assertRaises(IntakeBlocked):
            inspect("experiments/263/local_leagues/candidates.json",now=NOW)
    def test_past_morning_window_does_not_register(self):
        self.probe()
        with self.assertRaises(IntakeBlocked):
            inspect("experiments/263/sabah_readiness_probes/probe.json",
                    now=datetime(2026,11,7,12,0,tzinfo=timezone.utc))
    def test_duplicate_named_match_denied(self):
        dup=[{"league":"ENG1","home":"A","away":"B"}]*2
        with self.assertRaises(ValueError):self.request(dup)
if __name__=="__main__":unittest.main()
