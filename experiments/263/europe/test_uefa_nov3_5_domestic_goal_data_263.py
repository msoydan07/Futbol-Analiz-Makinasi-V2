"""Deterministic stage-4 tests; synthetic results only, no network or scoring model."""
from __future__ import annotations
import csv
import io
import json
import unittest
from datetime import date,datetime,timezone
from pathlib import Path

from uefa_nov3_5_domestic_goal_data_263 import (
    DataAuditError,DIVS,decode_league,parse_date,opponent_earlier_ppg,
    team_profile,preview,side_of,MIN_LEAGUE_GAMES)
from mackolik_identity_gate_263 import _memberships

INDEX=json.loads(Path("experiments/263/evidence/identity_index_263.json").read_text(encoding="utf8"))
COHORT=json.loads(Path("experiments/263/evidence/elo_uefa_active_cohort_2026_11_03.json").read_text(encoding="utf8"))
IDS=INDEX["season_memberships"]["2026-2027"]["ENG1"]
NOW=datetime.fromisoformat("2026-11-03T06:30:00+00:00")
FIELDS=["Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"]

def create_rows():
    out=[]
    for period in (1,2):
        for j in range(20):
            h=IDS[j]
            a=IDS[(j+period)%20]
            # All teams play twice home and twice away across the two rounds.
            # Distinct oriented pair, strictly before 2026-11-03.
            day="01/10/2026" if period==1 else "28/10/2026"
            n_h=(j+period)%4;n_a=(j+1)%3
            out.append({"Date":day,"HomeTeam":INDEX["teams"][h]["name"],
                        "AwayTeam":INDEX["teams"][a]["name"],
                        "FTHG":str(n_h),"FTAG":str(n_a),
                        "FTR":"H" if n_h>n_a else "A" if n_a>n_h else "D"})
    return out

def csv_bytes(rows):
    buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=FIELDS)
    w.writeheader();w.writerows(rows)
    return buf.getvalue().encode("utf8")

class Stage4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.members=_memberships(INDEX,"2026-2027")
        cls.rows=create_rows()
        cls.raw=csv_bytes(cls.rows)
        cls.matches,cls.audit=decode_league(cls.raw,"ENG1",INDEX,cls.members,NOW)
    def test_all_nine_codes_no_championship_and_no_elo_prediction(self):
        self.assertEqual(set(DIVS),{"BEL1","ENG1","ESP1","FRA1","GER1","ITA1","NED1","POR1","TUR1"})
        self.assertEqual(len(COHORT["eligible_team_ids"]),167)
        self.assertNotIn("ENG2",DIVS)
    def test_all_40_realistic_synthetic_completed_rows_resolve_exact_ids(self):
        self.assertEqual(len(self.matches),40)
        self.assertTrue(self.audit["source_fully_usable"],self.audit)
        self.assertEqual(self.audit["unmapped_source_names"],{})
    def test_scoreless_fixture_never_becomes_zero_zero_result(self):
        rows=[*self.rows,{"Date":"30/11/2026","HomeTeam":self.rows[0]["HomeTeam"],
                          "AwayTeam":self.rows[0]["AwayTeam"],
                          "FTHG":"","FTAG":"","FTR":""}]
        matches,audit=decode_league(csv_bytes(rows),"ENG1",INDEX,self.members,NOW)
        self.assertEqual(len(matches),40)
        self.assertEqual(audit["unplayed_source_rows"],1)
        self.assertTrue(audit["source_fully_usable"])
    def test_partial_and_future_scored_are_quarantined(self):
        partial=[*self.rows,{"Date":"31/10/2026","HomeTeam":self.rows[0]["HomeTeam"],
                            "AwayTeam":self.rows[0]["AwayTeam"],"FTHG":"2","FTAG":"","FTR":""}]
        _,aud=decode_league(csv_bytes(partial),"ENG1",INDEX,self.members,NOW)
        self.assertFalse(aud["source_fully_usable"])
        self.assertEqual(aud["invalid_result_or_duplicate_rows"][0]["reason"],"PARTIAL_SCORE")
        bad=[*self.rows,{"Date":"03/11/2026","HomeTeam":self.rows[0]["HomeTeam"],
                         "AwayTeam":self.rows[0]["AwayTeam"],"FTHG":"2","FTAG":"1","FTR":"H"}]
        _,aud=decode_league(csv_bytes(bad),"ENG1",INDEX,self.members,NOW)
        self.assertFalse(aud["source_fully_usable"])
        self.assertEqual(aud["invalid_result_or_duplicate_rows"][0]["reason"],"SCORED_ROW_AT_OR_AFTER_FETCH_DATE")
    def test_unknown_provider_alias_causes_not_complete(self):
        corrupted=[dict(r) for r in self.rows]
        corrupted[0]["HomeTeam"]="UNREVIEWED IDENTITY 263"
        matches,aud=decode_league(csv_bytes(corrupted),"ENG1",INDEX,self.members,NOW)
        self.assertEqual(len(matches),39)
        self.assertFalse(aud["source_fully_usable"])
        self.assertIn("UNREVIEWED IDENTITY 263",aud["unmapped_source_names"])
    def test_role_stats_and_last_five_never_use_target_date(self):
        team=IDS[0]
        p=team_profile(self.matches,team,date.fromisoformat("2026-11-03"))
        self.assertEqual(p["past_current_season_games"],4)
        self.assertEqual(p["past_current_season_home_games"],2)
        self.assertEqual(p["past_current_season_away_games"],2)
        self.assertEqual(p["domestic_league_games_before_match"],40)
        self.assertEqual(len(p["recent_5"]),4)
        self.assertEqual(p["last_completed_domestic_match"],"2026-10-28")
        self.assertTrue(all(r["date"]<"2026-11-03" for r in p["recent_5"]))
    def test_opponent_ppg_requires_three_earlier_games_and_no_same_day_leak(self):
        team=IDS[0]
        p=opponent_earlier_ppg(self.matches,team,date.fromisoformat("2026-10-28"))
        # Only the first period is earlier; 2 games -> insufficient.
        self.assertIsNone(p)
        # 4 games strictly before a later day yields points from 4 only.
        p=opponent_earlier_ppg(self.matches,team,date.fromisoformat("2026-11-02"))
        self.assertIsNotNone(p)
    def test_ready_and_after_kickoff_block(self):
        home,away=IDS[0],IDS[2]
        fixture={"uefa_match_id":999999,"competition":"UEFA_CL","date":"2026-11-03",
                 "home_uefa":"Synthetic A","away_uefa":"Synthetic B",
                 "home_identity":{"canonical_team_id":home,"league":"ENG1"},
                 "away_identity":{"canonical_team_id":away,"league":"ENG1"},
                 "kickoff_utc":"2026-11-03T17:45:00+00:00"}
        data={"ENG1":self.matches};aud={"ENG1":self.audit}
        a=preview(data,aud,[fixture],set(COHORT["eligible_team_ids"]),NOW)
        self.assertEqual(a[0]["status"],"DESCRIPTIVE_GOAL_PROFILE_SOURCE_READY")
        self.assertFalse(a[0]["model_forecast_authorized"])
        later=datetime.fromisoformat("2026-11-03T18:00:00+00:00")
        b=preview(data,aud,[fixture],set(COHORT["eligible_team_ids"]),later)
        self.assertEqual(b[0]["status"],"SOURCE_CAPTURE_AT_OR_AFTER_KICKOFF")
    def test_corrupted_csv_does_not_silently_turn_into_model_inputs(self):
        with self.assertRaises(DataAuditError):
            decode_league(b"nonsense,no csv\n", "ENG1",INDEX,self.members,NOW)
        self.assertEqual(parse_date("28/10/2026"),date(2026,10,28))

if __name__=="__main__":unittest.main()
