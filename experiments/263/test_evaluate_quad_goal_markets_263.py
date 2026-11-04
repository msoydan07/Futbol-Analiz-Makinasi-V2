"""One focused synthetic pre/post-KO evaluation test; no old model refit."""
from __future__ import annotations
import copy,hashlib,json,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch

from evaluate_quad import collect,report
from forward_quad import SCHEMA
from forward_c3 import canonical_bytes

CREATED="2026-11-05T16:00:00+00:00"
KICKOFF="2026-11-05T17:00:00+00:00"
NOW=datetime(2026,11,6,13,0,tzinfo=timezone.utc)
def make_record(home="SYNTH_A",away="SYNTH_B"):
    markets={"1X2":{"H":.60,"D":.25,"A":.15},
             "BTTS_YES":.40,"OVER_1.5":.70,
             "OVER_2.5":.55,"OVER_3.5":.25}
    r={"schema":SCHEMA,"created_at_utc":CREATED,
       "fixture":{"league":"ENG1","home_id":home,"away_id":away,
                 "match_local_date":"2026-11-05",
                 "kickoff_utc":KICKOFF,
                 "source_checked_at_utc":"2026-11-05T15:58:00+00:00",
                 "fixture_verification":"VERIFIED_BY_LIVE_OFFICIAL_GATE"},
       "model_predictions":{model:{"status":"AVAILABLE",
                                   "goals":{"markets":copy.deepcopy(markets)}}
                             for model in ("B","C2","C3","M4")}}
    r["payload_sha256"]=hashlib.sha256(canonical_bytes(r)).hexdigest()
    return r
def outcome(home="SYNTH_A",away="SYNTH_B",goals=(2,0)):
    a,b=goals
    return {"league":"ENG1","home_id":home,"away_id":away,
            "match_date":"2026-11-05",
            "result":"H" if a>b else "D" if a==b else "A",
            "home_goals":str(a),"away_goals":str(b)}
class ExpandedForwardResultCoverage(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.records=self.root/"records"
        (self.records/"2026-11-05").mkdir(parents=True)
        self.forecast=make_record()
        self.file=self.records/"2026-11-05"/("a"*24+".json")
        self.file.write_text(json.dumps(self.forecast),encoding="utf-8")
    def _collect(self,actuals,now=NOW):
        with patch("evaluate_quad.clean_rows",return_value=actuals):
            return collect(self.records,self.root/"unused.csv",now)
    def _report(self,actuals,now=NOW):
        with patch("evaluate_quad.clean_rows",return_value=actuals):
            return report(self.records,self.root/"unused.csv",now)
    def test_two_goal_result_scores_each_line_independently(self):
        complete,meta=self._collect([outcome()])
        self.assertEqual(meta["registered"],1)
        self.assertEqual(meta["finished_matched"],1)
        mk=complete[0]["markets"]["M4"]
        self.assertEqual({x:mk[x]["y"] for x in ("OVER_1.5","OVER_2.5","OVER_3.5")},
                         {"OVER_1.5":1,"OVER_2.5":0,"OVER_3.5":0})
        self.assertAlmostEqual(mk["OVER_1.5"]["brier"],.09)
        self.assertAlmostEqual(mk["OVER_2.5"]["brier"],.3025)
        self.assertAlmostEqual(mk["OVER_3.5"]["brier"],.0625)
    def test_four_goal_result_all_goal_lines_over(self):
        complete,_=self._collect([outcome(goals=(3,1))])
        self.assertTrue(all(complete[0]["markets"]["C2"][x]["y"]==1 for x in
                            ("OVER_1.5","OVER_2.5","OVER_3.5")))
    def test_one_goal_result_all_goal_lines_under(self):
        complete,_=self._collect([outcome(goals=(1,0))])
        self.assertTrue(all(complete[0]["markets"]["B"][x]["y"]==0 for x in
                            ("OVER_1.5","OVER_2.5","OVER_3.5")))
    def test_report_exposes_all_goal_lines_with_matching_sample(self):
        report_obj=self._report([outcome()])
        self.assertEqual(report_obj["finished_matched"],1)
        for model in ("B","C2","C3","M4"):
            self.assertEqual(set(report_obj["markets"][model]),
                             {"BTTS","OVER_1.5","OVER_2.5","OVER_3.5"})
            for market in ("OVER_1.5","OVER_2.5","OVER_3.5"):
                self.assertEqual(report_obj["markets"][model][market]["n"],1)
                self.assertEqual(sum(b["n"] for b in report_obj["markets"][model][market]["calibration_bins"]),1)
        self.assertEqual(report_obj["four_way_common"]["n"],1)
        self.assertFalse(report_obj["status"].startswith("PRODUCTION"))
    def test_no_result_does_not_invent_postmatch_metrics(self):
        out=self._report([])
        self.assertEqual(out["finished_matched"],0)
        self.assertEqual(out["unresolved_fixtures"],1)
        self.assertEqual(out["markets"]["M4"]["OVER_1.5"]["n"],0)
        self.assertIsNone(out["markets"]["M4"]["OVER_3.5"]["brier"])
    def test_locked_forecast_is_unchanged_by_result_scoring(self):
        before=self.file.read_bytes()
        self._report([outcome()])
        self.assertEqual(self.file.read_bytes(),before)
        self.assertEqual(json.loads(self.file.read_text())["payload_sha256"],
                         self.forecast["payload_sha256"])
    def test_not_retroactively_score_before_kickoff(self):
        pre_ko=datetime(2026,11,5,16,40,tzinfo=timezone.utc)
        result=self._report([outcome()],now=pre_ko)
        self.assertEqual(result["finished_matched"],0)
if __name__=="__main__":unittest.main()
