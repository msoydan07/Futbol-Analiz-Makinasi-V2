"""Focused gates: staged 4,501 preserved, ten current leagues, no fake acceptance."""
import csv
import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from season_refresh_263 import RefreshError
from weekend_source_preflight_263 import league_cutoff,validate_old_stage, SCHEMA, FIXED_CUTOFF


def row(league,day):
    return {"league":league,"season":"2026-2027","match_date":day}


class WeekendSourceTests(unittest.TestCase):
    def test_cutoff_is_before_pilot(self):
        self.assertEqual(FIXED_CUTOFF,"2026-11-05")
    def test_schema_not_human_verification(self):
        self.assertIn("preflight",SCHEMA)
    def test_reject_future_result(self):
        src=[row(k,"2026-11-01") for k in
             ("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")]
        src[0]["match_date"]="2026-11-05"
        with self.assertRaisesRegex(RefreshError,"future"):league_cutoff(src)
    def test_reject_old_history(self):
        src=[row(k,"2026-10-01") for k in
             ("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")]
        with self.assertRaisesRegex(RefreshError,"stale"):league_cutoff(src)
    def test_accept_ten_recent_leagues(self):
        src=[row(k,"2026-11-01") for k in
             ("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")]
        out=league_cutoff(src)
        self.assertEqual(len(out),10)
        self.assertEqual(out["TUR1"]["days_since_last_result_at_first_pilot_day"],5)
    def test_refuse_incomplete_league(self):
        with self.assertRaisesRegex(RefreshError,"no_current_season"):league_cutoff([row("ENG1","2026-11-01")])
    def test_refuse_stage_mutation_when_source_hash_wrong(self):
        with tempfile.TemporaryDirectory() as temp:
            t=Path(temp)/"source.csv"
            t.write_text("fixture_id,league,season,match_date,home_id,away_id,home_goals,away_goals,result\nx,ENG1,2026-2027,2026-11-01,AA,BB,1,0,H\n")
            with self.assertRaisesRegex(RefreshError,"prior_4501_stage_hash"):
                validate_old_stage(t,t)


if __name__=="__main__":unittest.main()
