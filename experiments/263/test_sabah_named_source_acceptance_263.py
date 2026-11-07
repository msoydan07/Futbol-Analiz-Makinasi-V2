"""Targeted 18-page/identity/source acceptance contract tests: offline only."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path

from sabah_named_source_acceptance_263 import (
    audit,read_source_readiness,named_only_runner,utc,PreflightError)

NOW=datetime(2026,11,7,7,0,tzinfo=timezone.utc)
FUTURE=(NOW+timedelta(hours=4)).isoformat()
PAST=(NOW-timedelta(minutes=5)).isoformat()
def candidate(status="TIMED_OFFICIAL_PAGE_MATCH_NEEDS_NAMED_GATE",
              home="A",kickoff=FUTURE):
    return {"league":"ESP1","home":home,"away":"B","status":status,
            "source_url":"https://www.laliga.com/matches",
            "official_html_sha256":"sha",
            "kickoff_utc":kickoff}
def preflight(*rows):
    return {"day_turkey":"2026-11-07","cohort":"legacy96","candidates":list(rows),
            "counts":{},"league_sources":{"ESP1":{"status":"FETCHED_OFFICIAL_PAGE"}}}
class FakeGateway:
    def __init__(self,answers):
        self.answers=answers
        self.called=[]
    def lookup(self,league,home,away):
        self.called.append((league,home,away))
        return self.answers.get(home,{"status":"NOT_VERIFIED","reason":"UNKNOWN_ID"})
    def latest_match_evidence(self,league,home,away):
        return {"selected_lookup":"OFFICIAL_PAGE_IN_TEST"}
def verified(kickoff=FUTURE):
    return {"status":"VERIFIED","home_id":"HOME_UUID","away_id":"AWAY_UUID",
            "kickoff_utc":kickoff}
class AcceptanceTests(unittest.TestCase):
    def _audit(self,rows,answers,now=NOW):
        gateway=FakeGateway(answers)
        r=audit("2026-11-07",now=now,gateway=gateway,preflight=preflight(*rows),
                data_status={"status":"RESEARCH_ONLY_TEST"})
        return r,gateway
    def test_named_gate_success_does_not_issue_forecast(self):
        r,g=self._audit([candidate()],{"A":verified()})
        self.assertEqual(r["gate_status_counts"],{"OFFICIAL_NAMED_GATE_OK_DATA_REVIEW_SEPARATE":1})
        self.assertEqual(r["fixtures"][0]["canonical_home_id"],"HOME_UUID")
        self.assertEqual(r["new_forward_predictions"],0)
        self.assertEqual(r["pinnacle_calls"],0)
        self.assertEqual(len(g.called),1)
    def test_date_only_and_missing_never_calls_named_gate(self):
        r,g=self._audit([candidate("DATE_ONLY_NO_LIVE_KICKOFF"),
                           candidate("SOURCE_PAGE_MATCH_NOT_VERIFIED",home="X")],{})
        self.assertEqual(r["gate_status_counts"]["BLOCKED_NO_OFFICIAL_KICKOFF_ON_THIS_PAGE"],2)
        self.assertFalse(g.called)
    def test_gate_identity_failure_does_not_upgrade(self):
        r,g=self._audit([candidate()],{"A":{"status":"REVIEW_REQUIRED","reason":"UNKNOWN_ID"}})
        self.assertEqual(r["gate_status_counts"]["BLOCKED_CANONICAL_NAMED_GATE"],1)
        self.assertNotIn("canonical_home_id",r["fixtures"][0])
    def test_source_and_named_kickoff_mismatch(self):
        r,_=self._audit([candidate()],{"A":verified((NOW+timedelta(hours=5)).isoformat())})
        self.assertEqual(r["gate_status_counts"]["BLOCKED_KICKOFF_MISMATCH"],1)
    def test_at_two_minutes_is_blocked(self):
        near=(NOW+timedelta(minutes=2)).isoformat()
        r,_=self._audit([candidate(kickoff=near)],{"A":verified(near)})
        self.assertEqual(r["gate_status_counts"]["BLOCKED_T_MINUS_2_MINS_OR_PAST"],1)
    def test_past_gate_cannot_be_accepted(self):
        r,_=self._audit([candidate(kickoff=PAST)],{"A":verified(PAST)})
        self.assertEqual(r["gate_status_counts"]["BLOCKED_T_MINUS_2_MINS_OR_PAST"],1)
    def test_wrong_day_never_backdates(self):
        with self.assertRaises(PreflightError):
            audit("2026-11-06",now=NOW,preflight=preflight(candidate()),gateway=FakeGateway({}))
    def test_named_only_fallback_never_fetches_older_html(self):
        self.assertEqual(named_only_runner("ESP1","A","B")["status"],"NOT_VERIFIED")
        self.assertEqual(named_only_runner("ESP1","A","B")["reason"],
                         "OLDER_FALLBACK_NOT_RETRIED_IN_THIS_AUDIT")
    def test_utc_tz_required(self):
        with self.assertRaises(PreflightError):utc("2026-11-07T17:00:00")
    def test_data_source_files_missing_block(self):
        with tempfile.TemporaryDirectory() as temp:
            x=read_source_readiness(temp,NOW)
            self.assertEqual(x["status"],"BLOCKED_SOURCE_OR_LOCK_MISSING")
            self.assertIn("data/quad_accepted_263/extended_history.csv",x["missing"])
    def test_owner_research_only_cannot_become_betting_approval(self):
        from sabah_named_source_acceptance_263 import (
          HISTORY,ACCEPTANCE,M4LOCK,M4CODE,DEVLOCK,FROZEN)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for path in (HISTORY,ACCEPTANCE,M4LOCK,M4CODE,DEVLOCK):
                (root/path).parent.mkdir(parents=True,exist_ok=True)
            (root/HISTORY).write_text("fixture,example\n",encoding="utf-8")
            (root/M4CODE).write_text("locked original model\n",encoding="utf-8")
            actual=hashlib.sha256((root/HISTORY).read_bytes()).hexdigest()
            engine=hashlib.sha256((root/M4CODE).read_bytes()).hexdigest()
            (root/ACCEPTANCE).write_text(json.dumps({
                "schema":"263_owner_accepted_research_source_v1",
                "status":"HUMAN_VERIFIED_SOURCE_ACCEPTANCE",
                "source_links":["https://www.tff.org/"],
                "reviewer":"owner","reviewed_at_utc":"2026-11-05T10:00:00+00:00",
                "baseline_sha256":FROZEN,"snapshot_sha256":actual,
                "research_only":True,"betting_authorized":False,
                "all_4518_independently_verified":False}),encoding="utf-8")
            (root/M4LOCK).write_text(json.dumps({
                "schema":"m4_dev_lock_263_v1","m4_engine_sha256":engine,
                "frozen_source_sha256":FROZEN}),encoding="utf-8")
            (root/DEVLOCK).write_text(json.dumps({
                "schema":"263_forward_dev_calibration_lock_v1",
                "official_approval":False}),encoding="utf-8")
            r=read_source_readiness(root,NOW)
            self.assertEqual(r["status"],"OWNER_ACCEPTED_LIMITED_EXPERIMENTAL_INPUTS_ONLY")
            self.assertFalse(r["betting_authorized"])
            self.assertFalse(r["independently_verified_all_4518"])
            (root/M4CODE).write_text("tampered\n",encoding="utf-8")
            broken=read_source_readiness(root,NOW)
            self.assertEqual(broken["status"],"BLOCKED_SOURCE_INTEGRITY_OR_REVIEW")
    def test_no_broad_approval_on_manifest_tag_only(self):
        from sabah_named_source_acceptance_263 import (
          HISTORY,ACCEPTANCE,M4LOCK,M4CODE,DEVLOCK,FROZEN)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for path in (HISTORY,ACCEPTANCE,M4LOCK,M4CODE,DEVLOCK):
                (root/path).parent.mkdir(parents=True,exist_ok=True)
                (root/path).write_text("{}")
            r=read_source_readiness(root,NOW)
            self.assertNotEqual(r["status"],"OWNER_ACCEPTED_LIMITED_EXPERIMENTAL_INPUTS_ONLY")
if __name__=="__main__":unittest.main()
