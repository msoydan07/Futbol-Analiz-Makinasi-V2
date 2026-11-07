"""Synthetic explicit manual bridge: no official web or bookmaker API calls."""
import copy,json,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
from sabah_10league_manifest_preflight_263 import inspect
from test_sabah_10league_manifest_preflight_263 import Fake, NOW, DAY
from sabah_manual_preflight_bridge_263 import review,prepare,save_request,BridgeBlocked
class ManualBridgeTests(unittest.TestCase):
    def setUp(self):
        self.raw=inspect(DAY,gateway=Fake(),now=NOW)
        self.now=NOW+timedelta(minutes=2)
    def choices(self,data):
        return [{k:r[k] for k in ("league","home_id","away_id","kickoff_utc")}
                for r in data["candidates"]]
    def test_no_command_never_promotes(self):
        r=review(self.raw,now=self.now)
        self.assertEqual(len(r["candidates"]),2)
        self.assertTrue(r["not_a_pilot_seal"])
        with self.assertRaisesRegex(BridgeBlocked,"USER_ANALYSIS_COMMAND"):
            prepare(self.raw,self.choices(r),now=self.now)
    def test_explicit_same_day_request_validated_by_new100_named_schema(self):
        x=review(self.raw,now=self.now)
        out=prepare(self.raw,self.choices(x),command_authorized=True,now=self.now)
        self.assertEqual(set(out),{"schema","day_turkey","matches"})
        self.assertEqual(len(out["matches"]),2)
        with tempfile.TemporaryDirectory() as d:
            with patch("pathlib.Path.cwd",return_value=Path(d)):
                # Use relative safety-controlled channel under isolated directory.
                old=Path.cwd()
            import os
            loc=os.getcwd()
            try:
                os.chdir(d)
                f=save_request("experiments/263/sabah_requests/user_20261108.json",out)
                self.assertEqual(json.loads(f.read_text())["matches"],out["matches"])
                with self.assertRaises(FileExistsError):save_request(f,out)
            finally:os.chdir(loc)
    def test_stale_and_wrong_day_blocked(self):
        with self.assertRaisesRegex(BridgeBlocked,"OLDER_THAN_10MIN"):
            review(self.raw,now=NOW+timedelta(minutes=11))
        x=copy.deepcopy(self.raw);x["day_turkey"]="2026-11-07"
        with self.assertRaisesRegex(BridgeBlocked,"NOT_SAME_TURKEY_DAY"):
            review(x,now=self.now)
    def test_tampered_sha_and_incomplete_leagues_denied(self):
        x=copy.deepcopy(self.raw);x["candidates"][0]["official_html_sha256"]="?"
        with self.assertRaisesRegex(BridgeBlocked,"INVALID_SOURCE_HASH"):review(x,now=self.now)
        x=copy.deepcopy(self.raw);x["league_count"]=9
        with self.assertRaisesRegex(BridgeBlocked,"INCOMPLETE_TEN_LEAGUE"):review(x,now=self.now)
    def test_duplicate_wrong_ID_and_partial_source_never_promoted(self):
        data=review(self.raw,now=self.now)
        ids=self.choices(data)
        with self.assertRaisesRegex(BridgeBlocked,"DUPLICATE_USER_SELECTION"):
            prepare(self.raw,[ids[0],ids[0]],command_authorized=True,now=self.now)
        ids[0]["home_id"]="ANOTHER_TEAM"
        with self.assertRaisesRegex(BridgeBlocked,"NOT_IN_FRESH_OFFICIAL"):
            prepare(self.raw,ids,command_authorized=True,now=self.now)
        self.assertFalse(data["all_leagues_fully_covered"])
        self.assertTrue(any(x["league"]=="ENG2" for x in data["unresolved_league_blockers"]))
    def test_started_games_not_promoted_and_after_window_blocked(self):
        x=copy.deepcopy(self.raw)
        x["candidates"][0]["kickoff_utc"]=(self.now+timedelta(seconds=60)).isoformat()
        r=review(x,now=self.now)
        self.assertEqual(len(r["candidates"]),1)
        with self.assertRaisesRegex(BridgeBlocked,"OUTSIDE_USER_ANALYSIS_WINDOW"):
            review(self.raw,now=datetime(2026,11,8,12,0,tzinfo=timezone.utc))
    def test_invalid_request_does_not_leave_trigger_file(self):
        import os
        original=os.getcwd()
        with tempfile.TemporaryDirectory() as d:
            try:
                os.chdir(d)
                path=Path("experiments/263/sabah_requests/invalid.json")
                bad={"schema":"SABAH_TOPLU_V1","day_turkey":DAY,
                     "matches":[{"league":"ENG1","home":"Same","away":"Same"}]}
                with self.assertRaises(Exception):
                    save_request(path,bad)
                self.assertFalse(path.exists())
            finally:
                os.chdir(original)
    def test_invalid_trigger_filename_rejected(self):
        data=review(self.raw,now=self.now)
        out=prepare(self.raw,self.choices(data),command_authorized=True,now=self.now)
        with self.assertRaisesRegex(BridgeBlocked,"ONLY_USER_NAMED_REQUEST_CHANNEL"):
            save_request("experiments/263/sabah_requests/bad.name.json",out)
    def test_never_writes_live_request_in_review_or_unauthorized_mode(self):
        x=review(self.raw,now=self.now)
        self.assertEqual(x["odds_api_calls"],0)
        self.assertEqual(x["model_executions"],0)
        with self.assertRaisesRegex(BridgeBlocked,"ONLY_USER_NAMED"):
            save_request("experiments/263/sabah_preflight_requests/bad.json",
                         {"schema":"SABAH_TOPLU_V1","day_turkey":DAY,"matches":[]})
if __name__=="__main__":unittest.main()
