"""New pure model/market-report contracts; no persisted pilot and no backtest."""
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
from classification_odds_263 import poisson_market
from readonly_quad_market_report_263 import make_reference,render_four_report
from readonly_quad_models_263 import read_only_quad,ReadonlyQuadError

NOW=datetime(2026,11,2,10,tzinfo=timezone.utc)
FIX={"league":"TUR1","home_id":"H","away_id":"A","local_date":"2026-11-08",
     "kickoff_utc":"2026-11-08T18:00:00+00:00"}
KEY="TUR1:H:A:2026-11-08"
def model(p):
    m=poisson_market(2.,.5)
    m["MS1"]=p;m["MSX"]=(1-p)*.65;m["MS2"]=(1-p)*.35
    m.update({"1X":m["MS1"]+m["MSX"],"X2":m["MSX"]+m["MS2"],
              "12":m["MS1"]+m["MS2"]})
    return {"status":"AVAILABLE","goals":{"markets":m}}
def four():return {"B":model(.64),"C2":model(.79),"C3":model(.65),"M4":model(.66)}
def quote():
    return {"fixture_key":KEY,"market_group":"MS","verification":"INDEPENDENTLY_CHECKED",
            "stage":"PREMATCH","source":"SYNTHETIC","source_url":"https://example.org/test",
            "checked_at_utc":NOW.isoformat(),
            "decimal_odds":{"MS1":1.5,"MSX":4.5,"MS2":7.0}}

class ReadonlyReport(unittest.TestCase):
    def test_no_odds_still_four_separate_models_and_no_records(self):
        models=four();before=deepcopy(models)
        r=make_reference(models,{},FIX,NOW)
        self.assertEqual(r["models"],before)
        self.assertEqual(r["benchmarks"],{})
        self.assertIn("DOĞRULANAMADI",render_four_report(r))
        self.assertFalse(r["pilot_recorded"])
        self.assertFalse(r["production_modified"])
    def test_one_complete_quote_group_used_and_no_grade_or_selection(self):
        r=make_reference(four(),{"MS1":quote()},FIX,NOW)
        ms=r["benchmarks"]["MS"]
        self.assertEqual(ms["closest_per_selection"]["MS1"],["C3"])
        self.assertFalse(ms["model_selected"])
        self.assertFalse(r["pilot_recorded"])
        self.assertIn("C2",render_four_report(r))
    def test_conflicting_quote_snapshots_same_group_rejected(self):
        other=quote();other["decimal_odds"]=dict(other["decimal_odds"],MS1=1.4)
        with self.assertRaisesRegex(ValueError,"MIXED_ODDS"):
            make_reference(four(),{"MS1":quote(),"MSX":other},FIX,NOW)
    def test_no_forward_prediction_write_function_referenced(self):
        import inspect,readonly_quad_models_263
        src=inspect.getsource(readonly_quad_models_263.read_only_quad)
        self.assertNotIn("predict_quad_from_verified_gate(",src)
        self.assertNotIn(".write_text(",src)
        self.assertNotIn(".mkdir(",src)
    def test_cutoff_strict_and_missing_history_safe(self):
        # 1 target-day match cannot be used as history or recorded.
        rows=[{"league":"TUR1","home_id":"H","away_id":"A","match_date":"2026-11-08",
               "fixture_id":"future","season":"2026-2027","home_goals":"4","away_goals":"0","result":"H"}]
        with tempfile.TemporaryDirectory() as d:
            with patch("readonly_quad_models_263.use_lock",return_value=object()),\
                 patch("readonly_quad_models_263.Path.read_bytes",return_value=b"frozen"),\
                 patch("readonly_quad_models_263.hashlib.sha256") as sha,\
                 patch("readonly_quad_models_263.json.loads",return_value={
                    "frozen_source_sha256":"35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1",
                    "m4_engine_sha256":"expected"}):
                sha.return_value.hexdigest.return_value="expected"
                p=read_only_quad(rows,FIX,lock_path=Path(d)/"dummy.json")
                self.assertTrue(all(x["status"]=="UNAVAILABLE" for x in p.values()))

if __name__=="__main__":unittest.main()
