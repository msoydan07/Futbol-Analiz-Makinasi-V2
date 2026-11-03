"""Only new T-60 lock intake tests. Never register a real prediction."""
from __future__ import annotations
import copy
import json
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path

from uefa_t60_shadow_lock_263 import (
    REQUEST_SCHEMA,validate_slot,LockError,score_mode,model_output,source_url_ok)
SLOTS=json.loads(Path("experiments/263/evidence/uefa_nov3_5_t60_six_slots_263.json").read_text(encoding="utf8"))
FIXTURES=json.loads(Path("experiments/263/evidence/uefa_2026_11_03_05_fixture_scope_review.json").read_text(encoding="utf8"))
FX={x["uefa_match_id"]:x for x in FIXTURES["verified_fixtures"]}
SLOT=SLOTS["slots"][0]
KO=datetime.fromisoformat(FX[SLOT["uefa_match_ids"][0]]["kickoff_utc"])
NOW=KO-timedelta(minutes=60)
def fresh_request(slot=SLOT,now=NOW):
    return {"schema":REQUEST_SCHEMA,"slot_key":slot["slot_key"],
       "fixture_review":{"status":"ASSISTANT_WEB_OFFICIAL_PAGE_REVIEWED",
           "reviewed_at_utc":(now-timedelta(minutes=8)).isoformat(),
           "official_urls":{str(mid):FX[mid]["official_match_url"]
                            for mid in slot["uefa_match_ids"]}},
       "lineups":{str(mid):{"status":"NOT_CONFIRMED","observed_at_utc":None,
           "source_url":None,"home_starting_xi":None,"away_starting_xi":None}
           for mid in slot["uefa_match_ids"]}}
class Intake(unittest.TestCase):
    def test_01_all_six_sessions_are_disjoint_seventeen_and_60_minutes(self):
        self.assertEqual(len(SLOTS["slots"]),6)
        self.assertEqual(sorted(len(x["uefa_match_ids"]) for x in SLOTS["slots"]),
                         [1,1,2,3,5,5])
        self.assertEqual(len({mid for s in SLOTS["slots"] for mid in s["uefa_match_ids"]}),17)
        for slot in SLOTS["slots"]:
            kickoff=datetime.fromisoformat(FX[slot["uefa_match_ids"][0]]["kickoff_utc"])
            now=kickoff-timedelta(minutes=60)
            got,_,_=validate_slot(fresh_request(slot,now),SLOTS,FIXTURES,now)
            self.assertEqual(got["slot_key"],slot["slot_key"])
    def test_02_missing_lineups_does_not_block(self):
        _,_,xi=validate_slot(fresh_request(),SLOTS,FIXTURES,NOW)
        self.assertEqual(xi[SLOT["uefa_match_ids"][0]]["status"],
                         "FIRST_XI_NOT_CONFIRMED_NON_BLOCKING")
    def test_03_early_or_late_pre_kickoff_lock_blocked(self):
        with self.assertRaisesRegex(LockError,"OUTSIDE_TMINUS75_TO_TMINUS15"):
            validate_slot(fresh_request(now=KO-timedelta(minutes=100)),SLOTS,FIXTURES,
                          KO-timedelta(minutes=100))
        with self.assertRaisesRegex(LockError,"OUTSIDE_TMINUS75_TO_TMINUS15"):
            validate_slot(fresh_request(now=KO-timedelta(minutes=3)),SLOTS,FIXTURES,
                          KO-timedelta(minutes=3))
        with self.assertRaisesRegex(LockError,"OUTSIDE_TMINUS75_TO_TMINUS15"):
            validate_slot(fresh_request(now=KO+timedelta(minutes=1)),SLOTS,FIXTURES,
                          KO+timedelta(minutes=1))
    def test_04_changed_official_url_fails(self):
        r=fresh_request()
        r["fixture_review"]["official_urls"][str(SLOT["uefa_match_ids"][0])]="https://not-real.uefa.com/match/1"
        with self.assertRaisesRegex(LockError,"UEFA_OFFICIAL_URLS_NOT_MATCHED"):
            validate_slot(r,SLOTS,FIXTURES,NOW)
    def test_05_unsigned_unverified_fixture_review_fails(self):
        r=fresh_request()
        r["fixture_review"]["status"]="NOT_WEB_CHECKED"
        with self.assertRaisesRegex(LockError,"CURRENT_OFFICIAL_MATCH_PAGE_REVIEW_MISSING"):
            validate_slot(r,SLOTS,FIXTURES,NOW)
    def test_06_invalid_lineup_source_url_rejected(self):
        r=fresh_request()
        row=r["lineups"][str(SLOT["uefa_match_ids"][0])]
        row.update(status="TWO_CONFIRMED_XI_SOURCE_CLAIM",
             observed_at_utc=(NOW-timedelta(minutes=5)).isoformat(),
             source_url="https://uefa.com.attacker.example/fake",
             home_starting_xi=[f"H{i}" for i in range(11)],
             away_starting_xi=[f"A{i}" for i in range(11)])
        with self.assertRaisesRegex(LockError,"XI_SOURCE_HOST_INVALID"):
            validate_slot(r,SLOTS,FIXTURES,NOW)
    def test_07_proper_XI_evidence_is_still_unverified_by_ci(self):
        r=fresh_request()
        row=r["lineups"][str(SLOT["uefa_match_ids"][0])]
        row.update(status="TWO_CONFIRMED_XI_SOURCE_CLAIM",
             observed_at_utc=(NOW-timedelta(minutes=5)).isoformat(),
             source_url=FX[SLOT["uefa_match_ids"][0]]["official_match_url"],
             home_starting_xi=[f"Home {i}" for i in range(11)],
             away_starting_xi=[f"Away {i}" for i in range(11)])
        _,_,xi=validate_slot(r,SLOTS,FIXTURES,NOW)
        v=xi[SLOT["uefa_match_ids"][0]]
        self.assertFalse(v["source_ci_verified"])
        self.assertFalse(v["xi_numeric_effect_on_model"])
    def test_08_duplicate_XI_players_rejected(self):
        r=fresh_request()
        row=r["lineups"][str(SLOT["uefa_match_ids"][0])]
        row.update(status="TWO_CONFIRMED_XI_SOURCE_CLAIM",
             observed_at_utc=NOW.isoformat(),
             source_url=FX[SLOT["uefa_match_ids"][0]]["official_match_url"],
             home_starting_xi=["Same"]*11,away_starting_xi=[f"A {i}" for i in range(11)])
        with self.assertRaisesRegex(LockError,"XI_NAMES_INCOMPLETE_OR_REPEATED"):
            validate_slot(r,SLOTS,FIXTURES,NOW)
    def test_09_source_hosts_stay_whitelisted(self):
        self.assertTrue(source_url_ok("https://www.uefa.com/uefachampionsleague/match/2049614--x/"))
        self.assertFalse(source_url_ok("http://www.uefa.com/match/x"))
        self.assertFalse(source_url_ok("https://www.uefa.com.evil.test/match/2049614"))
    def test_10_math_market_labels_are_complete_not_betting_picks(self):
        raw=(1.4,1.1,[.45,.30,.25],.47,.51)
        result=model_output(raw)
        self.assertIsNone(result["market_ev"])
        self.assertFalse(result["betting_pick_authorized"])
        self.assertAlmostEqual(sum(result["1x2"].values()),1)
        self.assertAlmostEqual(result["under_2p5"]+result["over_2p5"],1)
        self.assertAlmostEqual(result["both_teams_score_no"]+result["both_teams_score_yes"],1)
    def test_11_snapshot_has_exact_six_slot_names(self):
        self.assertEqual(set(s["slot_key"] for s in SLOTS["slots"]),{
            "2026-11-03_2045_TR","2026-11-03_2300_TR",
            "2026-11-04_2045_TR","2026-11-04_2300_TR",
            "2026-11-05_2045_TR","2026-11-05_2300_TR"})
if __name__=="__main__":unittest.main()
