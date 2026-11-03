"""Full Stage8 preflight rehearsal using archived sources: NEVER WRITE forecasts.

Only uses synthetic T-60 operator requests and the already-accepted
3 Nov data snapshots; no live UEFA, Football-Data, beyondELO calls.
"""
import csv
import hashlib
import io
import json
import tempfile
import unittest
from datetime import datetime,timedelta
from pathlib import Path
from uefa_t60_shadow_lock_263 import batch,REQUEST_SCHEMA,DIVS,LockError
from uefa_nov3_5_stage6_shadow_math_preflight_263 import (
    SOURCES as PINNED,checked_json)
from uefa_t60_shadow_lock_263 import ELO_URL,PATH_SLOTS,PATH_STAGE3,PATH_INDEX

ROOT=Path("data/europe_staged_263/t60_inputs")
STAGE4=checked_json(ROOT/"goals/stage4_goal_data_readiness.json",PINNED["stage4"])
STAGE5=checked_json(ROOT/"news/17_match_elo_news_readiness.json",PINNED["stage5"])
RETRO=checked_json(ROOT/"retro/retrospective_elo_vs_m0_report.json",PINNED["retro"])
SLOTS=json.loads(Path(PATH_SLOTS).read_text(encoding="utf8"))
OFFICIAL=json.loads(Path(PATH_STAGE3).read_text(encoding="utf8"))
INDEX=json.loads(Path(PATH_INDEX).read_text(encoding="utf8"))
ELO_RAW=(ROOT/"source_elo/current.csv").read_bytes()
ELO_ROWS=list(csv.DictReader(io.StringIO(ELO_RAW.decode("utf-8-sig"))))
BY_DIV={x:(ROOT/"goals/source_csv"/(x+".csv")).read_bytes() for x in DIVS.values()}
INDEXED={x["uefa_match_id"]:x for x in OFFICIAL["verified_fixtures"]}

def sample(slot):
    ko=datetime.fromisoformat(INDEXED[slot["uefa_match_ids"][0]]["kickoff_utc"])
    now=ko-timedelta(minutes=60)
    req={"schema":REQUEST_SCHEMA,"slot_key":slot["slot_key"],
         "fixture_review":{"status":"ASSISTANT_WEB_OFFICIAL_PAGE_REVIEWED",
            "reviewed_at_utc":(now-timedelta(minutes=5)).isoformat(),
            "official_urls":{str(k):INDEXED[k]["official_match_url"] for k in slot["uefa_match_ids"]}},
         "lineups":{str(k):{"status":"NOT_CONFIRMED","observed_at_utc":None,
                          "source_url":None,"home_starting_xi":None,"away_starting_xi":None}
                    for k in slot["uefa_match_ids"]}}
    return req,now

def football(league,now):
    division=DIVS[league]
    return BY_DIV[division],now,"https://www.football-data.co.uk/mmz4281/2627/"+division+".csv"

def elo(_):
    return {"status":"FETCHED_AND_SCHEMA_VALID",
            "sha256":hashlib.sha256(ELO_RAW).hexdigest(),
            "last_modified":None},ELO_ROWS

class T60Rehearsal(unittest.TestCase):
    def test_all_six_slots_17_real_match_IDs_run_in_memory_with_no_records(self):
        with tempfile.TemporaryDirectory() as d:
            total=0;seen=set()
            for slot in SLOTS["slots"]:
                req,now=sample(slot)
                report=batch(req,now=now,fixture=OFFICIAL,slots=SLOTS,
                    stage4=STAGE4,stage5=STAGE5,retro=RETRO,index=INDEX,
                    fetcher=football,elo_fetch=elo,
                    dest_records=Path(d)/"records",
                    dest_reports=Path(d)/"reports",
                    write=False)
                self.assertEqual(report["matches"],len(slot["uefa_match_ids"]))
                self.assertTrue(report["utc_pre_kickoff"])
                self.assertTrue(report["registration_is_experimental_shadow_not_100_pilot"])
                self.assertTrue(report["official_XI_not_a_model_multiplier"])
                total+=report["matches"]
                seen.update(item["uefa_match_id"] for item in report["immutable_records"])
            self.assertEqual(total,17)
            self.assertEqual(len(seen),17)
            self.assertFalse((Path(d)/"records").exists())
            self.assertFalse((Path(d)/"reports").exists())
    def test_history_cannot_be_written_from_bad_source_time(self):
        req,now=sample(SLOTS["slots"][0])
        with tempfile.TemporaryDirectory() as d:
            def fake_too_late(league,utc):
                raw,_,url=football(league,utc)
                return raw,datetime.fromisoformat(INDEXED[SLOTS["slots"][0]["uefa_match_ids"][0]]["kickoff_utc"]),url
            with self.assertRaisesRegex(LockError,"LEAGUE_SOURCE_FETCH_COMPLETED_AFTER_KICKOFF"):
                batch(req,now=now,fixture=OFFICIAL,slots=SLOTS,
                    stage4=STAGE4,stage5=STAGE5,retro=RETRO,index=INDEX,
                    fetcher=fake_too_late,elo_fetch=elo,
                    dest_records=Path(d)/"records",
                    dest_reports=Path(d)/"reports",
                    write=False)
            self.assertFalse((Path(d)/"records").exists())
if __name__=="__main__":unittest.main()
