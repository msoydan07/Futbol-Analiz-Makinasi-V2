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
        rows=[{"league":"TUR1","home_id":"H","away_id":"A","match_date":"2026-11-08",
               "fixture_id":"future","season":"2026-2027","home_goals":"4","away_goals":"0","result":"H"}]
        case={"league":"TUR1","home_id":"H","away_id":"A","target_date":"2026-11-08"}
        outputs=read_only_quad(rows,case)
        self.assertEqual(set(outputs),{"B","C2","C3","M4"})
        self.assertTrue(all(v["status"]=="UNAVAILABLE" for v in outputs.values()))

    def test_frozen_model_functions_generate_four_outputs_without_any_files(self):
        from datetime import date,timedelta
        teams=["A","B","C","D"]
        first=date(2025,9,1)
        rows=[]
        for i in range(140):
            day=(first+timedelta(days=3*i)).isoformat()
            h=teams[i%4];a=teams[(i+1+(i//4)%2)%4]
            gh=i%4;ga=(i*7+1)%3
            rows.append({"fixture_id":"SYNTHETIC_"+str(i),"league":"ENG1",
                         "season":"2025-2026" if day<"2026-07-01" else "2026-2027",
                         "match_date":day,"home_id":h,"away_id":a,
                         "home_goals":str(gh),"away_goals":str(ga),
                         "result":"H" if gh>ga else "A" if gh<ga else "D"})
        case={"league":"ENG1","home_id":"A","away_id":"B","target_date":"2026-11-08"}
        original=deepcopy(rows)
        with tempfile.TemporaryDirectory() as td:
            original_files=list(Path(td).iterdir())
            outputs=read_only_quad(rows,case)
            self.assertEqual(list(Path(td).iterdir()),original_files)
        self.assertEqual(rows,original)
        self.assertEqual(set(outputs),{"B","C2","C3","M4"})
        self.assertTrue(all(v["status"]=="AVAILABLE" for v in outputs.values()))
        for record in outputs.values():
            p=record["goals"]["markets"]
            d=p["1X2"] if "1X2" in p else {"H":p["MS1"],"D":p["MSX"],"A":p["MS2"]}
            self.assertAlmostEqual(sum(d.values()),1,places=7)

if __name__=="__main__":unittest.main()
