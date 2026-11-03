"""NEW stage8 glue checks against frozen REAL 17 UEFA fixture archives.
Do not persist real match forecasts in unit tests.
"""
from __future__ import annotations
import copy,json,unittest,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
from uefa_stage8_dual_shadow_record_263 import candidate_batch,parse_lineup,LockError
from uefa_nov3_5_stage6_shadow_math_preflight_263 import SOURCES

ROOT=Path("data/europe_staged_263/stage8_fixture")
UTC=timezone.utc
OFFICIAL="https://www.uefa.com/uefachampionsleague/"
class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s4=json.loads((ROOT/"stage4/stage4_goal_data_readiness.json").read_text(encoding="utf8"))
        cls.s5=json.loads((ROOT/"stage5/17_match_elo_news_readiness.json").read_text(encoding="utf8"))
        cls.retro=json.loads((ROOT/"retro/retrospective_elo_vs_m0_report.json").read_text(encoding="utf8"))
        cls.scope=json.loads(Path("experiments/263/evidence/uefa_2026_11_03_05_fixture_scope_review.json").read_text(encoding="utf8"))
        cls.now=datetime.fromisoformat("2026-11-03T16:45:00+00:00")
        cls.ko="2026-11-03T17:45:00+00:00"
        cls.match=next(f for f in cls.s4["fixtures"] if f["kickoff_utc"]==cls.ko)
        cls.evidence=cls.make(cls.match["uefa_match_id"],cls.now)
    @staticmethod
    def make(mid,now,home_status="NOT_PUBLISHED",away_status="NOT_PUBLISHED"):
        def one(status):
            return {"status":status,
                    "source_urls":[OFFICIAL] if status!="UNVERIFIED" else [],
                    "reviewed_utc":(now-timedelta(minutes=2)).isoformat(),
                    "human_reviewed":True}
        return {"schema":"263_UEFA_STAGE8_REVIEWED_LINEUP_EVIDENCE_V1",
                "purpose":"REAL_PREMATCH_USER_REQUESTED_SHADOW_ONLY",
                "fixtures":[{"uefa_match_id":mid,"home_lineup":one(home_status),
                             "away_lineup":one(away_status)}]}
    def call(self, evidence=None,now=None,stage4=None,stage5=None):
        return candidate_batch(stage4 or self.s4,stage5 or self.s5,
                 self.retro,self.scope,evidence or self.evidence,now or self.now)
    def test_01_real_numeric_UEFA_match_id_is_accepted(self):
        self.assertIs(type(self.match["uefa_match_id"]),int)
        rec=self.call()[0]
        self.assertEqual(rec["uefa_match_id"],self.match["uefa_match_id"])
        self.assertEqual(set(rec["model_outputs"]),{"M0_REFERENCE_ONLY","M0_PLUS_ELO_EXPERIMENTAL"})
        self.assertEqual(rec["lineup_status"],"NOT_ANNOUNCED")
        self.assertFalse(rec["elo_beta_production_approved"])
        self.assertFalse(rec["pilot_100_matches_affected"])
        self.assertTrue(rec["source_sha256"]==SOURCES)
    def test_02_11_unannounced_does_not_block(self):
        self.assertEqual(len(self.call()),1)
    def test_03_not_verified_cannot_claim_no_11(self):
        e=self.make(self.match["uefa_match_id"],self.now,"UNVERIFIED","UNVERIFIED")
        self.assertEqual(self.call(e)[0]["lineup_status"],"NOT_VERIFIED")
    def test_04_1_official_11_requires_link(self):
        e=self.make(self.match["uefa_match_id"],self.now,"OFFICIAL","NOT_PUBLISHED")
        self.assertEqual(self.call(e)[0]["lineup_status"],"ONE_OFFICIAL")
        e["fixtures"][0]["home_lineup"]["source_urls"]=[]
        with self.assertRaisesRegex(LockError,"CLAIMED_OFFICIAL_LINEUP_NEEDS_SOURCE_URL"):
            self.call(e)
    def test_05_missing_real_lineup_review_blocks(self):
        e=copy.deepcopy(self.evidence)
        e["fixtures"][0].pop("away_lineup")
        with self.assertRaisesRegex(LockError,"LINEUP_REVIEW_NOT_PROVIDED"):
            self.call(e)
    def test_06_cutoff_passed_not_backdate(self):
        with self.assertRaisesRegex(LockError,"OUTSIDE_T_MINUS_75_KICKOFF_WINDOW"):
            self.call(now=datetime.fromisoformat("2026-11-03T17:46:00+00:00"))
    def test_07_too_early_for_60_window_not_a_real_forecast(self):
        with self.assertRaisesRegex(LockError,"OUTSIDE_T_MINUS_75_KICKOFF_WINDOW"):
            self.call(now=datetime.fromisoformat("2026-11-03T15:00:00+00:00"))
    def test_08_mixed_ko_batch_blocks(self):
        later=next(f for f in self.s4["fixtures"] if f["date"]=="2026-11-03" and f["kickoff_utc"]!=self.ko)
        e=copy.deepcopy(self.evidence)
        e["fixtures"].append(self.make(later["uefa_match_id"],self.now)["fixtures"][0])
        with self.assertRaisesRegex(LockError,"MIXED_KICKOFFS_REQUIRE_SEPARATE_RECORDS"):
            self.call(e)
    def test_09_other_day_stale_archive_blocks(self):
        nextday=next(f for f in self.s4["fixtures"] if f["date"]=="2026-11-04")
        run=datetime.fromisoformat("2026-11-04T16:45:00+00:00")
        e=self.make(nextday["uefa_match_id"],run)
        with self.assertRaisesRegex(LockError,"SAME_DAY_FRESH_SOURCE_REQUIRED_BEFORE_RECORD"):
            self.call(e,run)
    def test_10_real_23_00_batch_same_kickoff_five_matches(self):
        match=[f for f in self.s4["fixtures"]
            if f["kickoff_utc"]=="2026-11-03T20:00:00+00:00"]
        self.assertEqual(len(match),5)
        run=datetime.fromisoformat("2026-11-03T19:00:00+00:00")
        e=self.make(match[0]["uefa_match_id"],run)
        e["fixtures"]=[self.make(f["uefa_match_id"],run)["fixtures"][0] for f in match]
        records=self.call(e,run)
        self.assertEqual(len(records),5)
        self.assertEqual(len({v["uefa_match_id"] for v in records}),5)
    def test_11_unverifiable_future_news_review_blocks(self):
        e=copy.deepcopy(self.evidence)
        e["fixtures"][0]["home_lineup"]["reviewed_utc"]="2026-11-03T17:40:00+00:00"
        with self.assertRaisesRegex(LockError,"LINEUP_REVIEW_NOT_FRESH_OR_AFTER_KO"):
            self.call(e)
    def test_12_exact_data_source_hashes_frozen(self):
        for field in SOURCES:
            self.assertEqual(len(SOURCES[field]),64)
    def test_13_bad_club_id_cannot_be_accepted(self):
        changed=copy.deepcopy(self.s5)
        changed["matches"][0]["home_team"]["canonical_team_id"]="incorrect"
        with self.assertRaisesRegex(Exception,"PREMATCH_CANONICAL_CLUB_ID_MISMATCH"):
            self.call(stage5=changed)
    def test_14_no_betting_odds_or_Ev(self):
        rec=self.call()[0]
        self.assertFalse(rec["odds_or_ev_present"])
        self.assertEqual(set(rec["model_outputs"]["M0_REFERENCE_ONLY"]["1x2"]),{"home","draw","away"})

if __name__=="__main__":unittest.main()
