"""Synthetic safety tests ONLY; no data collection and no probability backtests."""
import csv
import io
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from m4_xg_forward_snapshot_263 import capture_xg_snapshot, inspect_for_target, SnapshotGateError

OBS = datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc)
KO = datetime(2026, 11, 11, 20, 0, tzinfo=timezone.utc)
FIELDS = ["fixture_id", "league", "season", "match_date", "home_id", "away_id", "home_xg", "away_xg", "understat_source_url"]

def data(rows=None):
    if rows is None:
        rows = [{"fixture_id":"old","league":"ENG1","season":"2026-2027",
                 "match_date":"2026-11-09","home_id":"H","away_id":"A",
                 "home_xg":"1.5","away_xg":"0.9",
                 "understat_source_url":"https://understat.com/match/1"}]
    buff=io.StringIO()
    w=csv.DictWriter(buff,fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
    return buff.getvalue().encode()

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store=Path(self.tmp.name)/"restricted"
        self.kw=dict(payload=data(),private_store=self.store,provider="UNDERSTAT",
            source_url="https://understat.com/",
            rights_evidence_ref="SYNTHETIC_INTERNAL_RIGHTS_REVIEW_ONLY",
            synthetic_test=True,_test_clock=OBS)

    def capture(self,**changes):
        return capture_xg_snapshot(**dict(self.kw,**changes))

    def test_capture_private_and_readonly_status(self):
        m=self.capture()
        self.assertEqual(m["row_count"],1)
        self.assertEqual(m["vintage_status"],"LOCAL_OBSERVATION_NOT_EXTERNALLY_ANCHORED")
        self.assertEqual(self.store.stat().st_mode & 0o777,0o700)
        self.assertEqual((self.store/(m["snapshot_id"]+".csv")).stat().st_mode & 0o777,0o600)
        result=inspect_for_target(private_store=self.store,snapshot_id=m["snapshot_id"],
                                  target_kickoff_utc=KO,league="ENG1")
        self.assertEqual(result["historical_same_league_rows_before_target_date"],1)
        self.assertFalse(result["approved_for_live_model"])
        self.assertFalse(result["raw_values_exported"])

    def test_no_missing_permission_reference(self):
        with self.assertRaisesRegex(SnapshotGateError,"rights_evidence"):
            self.capture(rights_evidence_ref="")

    def test_reject_same_day_source_even_if_finished(self):
        rows=list(csv.DictReader(io.StringIO(data().decode())))
        rows[0]["match_date"]="2026-11-10"
        with self.assertRaisesRegex(SnapshotGateError,"not_prior_date"):
            self.capture(payload=data(rows))

    def test_reject_future_xg(self):
        rows=list(csv.DictReader(io.StringIO(data().decode())))
        rows[0]["match_date"]="2026-11-12"
        with self.assertRaisesRegex(SnapshotGateError,"not_prior_date"):
            self.capture(payload=data(rows))

    def test_pre_match_lock_only(self):
        m=self.capture()
        with self.assertRaisesRegex(SnapshotGateError,"not_observed_before_kickoff"):
            inspect_for_target(private_store=self.store,snapshot_id=m["snapshot_id"],
                               target_kickoff_utc=OBS,league="ENG1")

    def test_tampered_payload_rejected(self):
        m=self.capture()
        p=self.store/(m["snapshot_id"]+".csv")
        p.write_bytes(data().replace(b"1.5",b"3.5"))
        with self.assertRaisesRegex(SnapshotGateError,"hash_changed"):
            inspect_for_target(private_store=self.store,snapshot_id=m["snapshot_id"],
                               target_kickoff_utc=KO,league="ENG1")

    def test_duplicate_snapshot_id_not_reused(self):
        a=self.capture()
        b=self.capture()
        self.assertNotEqual(a["snapshot_id"],b["snapshot_id"])
        self.assertTrue((self.store/(a["snapshot_id"]+".csv")).exists())

    def test_no_git_checkout_store(self):
        d=Path(self.tmp.name)/"myrepo"
        d.mkdir()
        (d/".git").mkdir()
        with self.assertRaisesRegex(SnapshotGateError,"outside_git"):
            self.capture(private_store=d/"private")

    def test_no_public_github_action_capture(self):
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"true"}):
            with self.assertRaisesRegex(SnapshotGateError,"public_actions"):
                capture_xg_snapshot(**{k:v for k,v in self.kw.items() if k not in ("synthetic_test","_test_clock")})

    def test_reject_nonfinite_xg(self):
        rows=list(csv.DictReader(io.StringIO(data().decode())))
        rows[0]["away_xg"]="nan"
        with self.assertRaisesRegex(SnapshotGateError,"invalid_xg_range"):
            self.capture(payload=data(rows))

    def test_unauthorized_clock_override_rejected(self):
        with self.assertRaisesRegex(SnapshotGateError,"clock_override"):
            self.capture(synthetic_test=False)

if __name__=="__main__":unittest.main()
