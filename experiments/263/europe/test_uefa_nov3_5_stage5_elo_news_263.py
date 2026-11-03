"""One new 8-test batch for stage5 Elo-news source gates, archived fixtures only."""
import copy
import csv
import io
import json
import unittest
from pathlib import Path
from uefa_nov3_5_stage5_elo_news_263 import (
    validate_inputs,Stage5Error,ELO_SHA,CL_NEWS,EL_NEWS)

ROOT=Path("data/europe_staged_263/stage5_inputs")
FIXTURE="experiments/263/evidence/uefa_2026_11_03_05_fixture_scope_review.json"
NEWS="experiments/263/evidence/uefa_nov3_5_stage5_34_club_news_source_review_2026_11_03.json"

class SourceAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(ROOT/"elo/source_csv/current.csv").read_bytes()
        cls.integrity=json.loads((ROOT/"elo/single_integrity_report.json").read_text(encoding="utf8"))
        cls.crosswalk=json.loads((ROOT/"bridge/elo_bridge_crosswalk_167.json").read_text(encoding="utf8"))
        cls.stage4=json.loads((ROOT/"goals/stage4_goal_data_readiness.json").read_text(encoding="utf8"))
        cls.fixtures=json.loads(Path(FIXTURE).read_text(encoding="utf8"))
        cls.news=json.loads(Path(NEWS).read_text(encoding="utf8"))
    def build(self,raw=None,integrity=None,crosswalk=None,stage4=None,fixtures=None,news=None):
        return validate_inputs(
            self.raw if raw is None else raw,
            self.integrity if integrity is None else integrity,
            self.crosswalk if crosswalk is None else crosswalk,
            self.stage4 if stage4 is None else stage4,
            self.fixtures if fixtures is None else fixtures,
            self.news if news is None else news)
    def test_full_17_34_source_aligned_without_new_fetch(self):
        r=self.build()
        self.assertEqual(r["coverage"]["matches"],17)
        self.assertEqual(r["coverage"]["elo_with_rd_and_before_kickoff"],34)
        self.assertEqual(len(r["matches"]),17)
        self.assertEqual(r["coverage"]["news_cl_uefa_editorial_team_reports"],24)
        self.assertEqual(r["coverage"]["news_el_secondary_provisional_team_reports"],10)
        self.assertTrue(r["source_evidence"]["all_prior_data_captured_pre_kickoff"])
        self.assertFalse(r["safety"]["elo_influence_on_lambda"])
        self.assertFalse(r["safety"]["model_forecast_authorized"])
        self.assertFalse(r["safety"]["pilot_recorded"])
    def test_nothing_can_promote_unofficial_lineups(self):
        r=self.build()
        self.assertEqual(r["coverage"]["confirmed_starting_XIs"],0)
        self.assertFalse(r["source_evidence"]["source_news_has_exclusive_first_seen_utc"])
        self.assertTrue(r["coverage"]["first_XI_missing_does_not_block"])
        self.assertTrue(all(not s["confirmed_starting_eleven_available"]
           for m in r["matches"] for s in (m["home_team"]["news"],m["away_team"]["news"])))
    def test_elo_original_csv_bit_modified_rejected(self):
        a=bytearray(self.raw);a[len(a)//2]=ord('A') if a[len(a)//2]!=ord('A') else ord('B')
        with self.assertRaisesRegex(Stage5Error,"ELO_SOURCE_SHA_MISMATCH"):
            self.build(raw=bytes(a))
    def test_after_kickoff_elo_replay_blocked(self):
        integrity=copy.deepcopy(self.integrity)
        integrity["audited_utc"]="2026-11-03T18:00:00+00:00"
        with self.assertRaisesRegex(Stage5Error,"DATA_SNAPSHOT_NOT_BEFORE_UEFA_KICKOFF"):
            self.build(integrity=integrity)
    def test_wrong_uefa_team_news_identity_is_rejected(self):
        news=copy.deepcopy(self.news)
        tid=next(iter(news["clubs"]))
        news["clubs"][tid]["official_club_name"]="Unverified New Club"
        with self.assertRaisesRegex(Stage5Error,"NEWS_PLAYER_IDENTITY_OR_MATCH_SCOPE_MISMATCH"):
            self.build(news=news)
    def test_false_official_el_news_source_rejected(self):
        news=copy.deepcopy(self.news)
        tid=next(tid for tid,r in news["clubs"].items()
                 if r["confidence"]=="SECONDARY_UNCONFIRMED_REPORT_REQUIRES_OFFICIAL_RECHECK")
        news["clubs"][tid]["confidence"]="UEFA_EDITORIAL_PREMATCH_REPORT_NOT_CONFIRMED_TEAM_SHEET"
        with self.assertRaisesRegex(Stage5Error,"TEAM_NEWS_SOURCE_TIER_INCORRECT"):
            self.build(news=news)
    def test_source_snapshot_after_ko_is_rejected(self):
        stage4=copy.deepcopy(self.stage4)
        stage4["analysis_time_utc"]="2026-11-03T18:00:00+00:00"
        with self.assertRaisesRegex(Stage5Error,"DATA_SNAPSHOT_NOT_BEFORE_UEFA_KICKOFF"):
            self.build(stage4=stage4)
    def test_unapproved_elo_coefficient_gate_never_activates(self):
        cross=copy.deepcopy(self.crosswalk)
        cross["model_weight_approved"]=True
        with self.assertRaisesRegex(Stage5Error,"167_ELO_CROSSWALK_NOT_LOCKED"):
            self.build(crosswalk=cross)
if __name__=="__main__":unittest.main()
