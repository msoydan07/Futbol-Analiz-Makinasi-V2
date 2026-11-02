"""Pre-match UEFA incentive/phase schema tests; NO model fitting."""
import copy
import unittest
from uefa_stage_263 import stage
from uefa_match_context_263 import context_for, EuropeContextError

NOW="2026-11-02T12:00:00+03:00"
SRC="https://www.uefa.com/uefachampionsleague/match/2049614--synthetic-vs-synthetic2/"
SRC2="https://www.uefa.com/uefachampionsleague/match/2049999--synthetic2-vs-synthetic/"
STANDING_URL="https://www.uefa.com/uefachampionsleague/standings/"
def fixture(round="LEAGUE_PHASE",neutral=False):
    raw={"competition":"UEFA_CL","season":"2026-2027","round":round,
         "home":"Synthetic FC","away":"Fictional FC","source_url":SRC,
         "kickoff":"2026-11-03T18:45:00Z","observed_at":NOW,
         "result_status":"SCHEDULED","neutral_venue":neutral}
    return stage([raw],NOW)["fixtures"][0]
def league_context():
    return {"observed_at":NOW,"source_url":STANDING_URL,"matchday":5,
            "standings":{"home":{"played":4,"points":7,"goal_difference":1,"rank":16},
                         "away":{"played":4,"points":10,"goal_difference":4,"rank":7}}}
def second_leg():
    return {"observed_at":NOW,"source_url":SRC,"leg":2,"first_leg_source_url":SRC2,
            "first_leg_goals_for_current_home":0,"first_leg_goals_for_current_away":2}

class EuropeMatchContext(unittest.TestCase):
    def test_league_phase_points_table_and_no_assumed_tactics(self):
        c=fixture();d=league_context();before=copy.deepcopy(d)
        result=context_for(c,d,NOW)
        self.assertEqual(d,before)
        self.assertEqual(result["points_gap_home_minus_away"],-3)
        self.assertEqual(result["home_standing_before_kickoff"]["remaining_league_games"],4)
        self.assertEqual(result["away_standing_before_kickoff"]["current_table_zone_not_final_result"],"CURRENT_TOP_8")
        self.assertIsNone(result["goal_multiplier"])
        self.assertFalse(result["forecast_authorized"])
        self.assertFalse(result["pilot_registered"])
        self.assertTrue(result["must_win_or_cautious_tactics_not_deduced"])
    def test_points_exceed_possible_game_totals_are_rejected(self):
        d=league_context();d["standings"]["home"]["points"]=13
        with self.assertRaisesRegex(EuropeContextError,"GREATER_THAN_MAX"):
            context_for(fixture(),d,NOW)
    def test_no_table_from_after_kickoff_even_if_historical_result_exists(self):
        d=league_context();d["observed_at"]="2026-11-04T12:00:00Z"
        with self.assertRaisesRegex(EuropeContextError,"LEAKAGE"):
            context_for(fixture(),d,NOW)
        d=league_context()
        with self.assertRaisesRegex(EuropeContextError,"LEAKAGE"):
            context_for(fixture(),d,"2026-11-04T12:00:00Z")
    def test_missing_standings_are_not_faked_as_zero(self):
        d=league_context();del d["standings"]["away"]
        with self.assertRaisesRegex(EuropeContextError,"TWO_PREMATCH_STANDINGS"):
            context_for(fixture(),d,NOW)
    def test_context_source_must_be_same_competition_official_shape(self):
        d=league_context();d["source_url"]="https://www.uefa.com.evil.org/uefachampionsleague/standings/"
        with self.assertRaisesRegex(EuropeContextError,"SOURCE_NOT_OFFICIAL"):
            context_for(fixture(),d,NOW)
    def test_knockout_second_leg_detects_aggregate_but_does_not_reduce_goals(self):
        result=context_for(fixture("KNOCKOUT"),second_leg(),NOW)
        self.assertEqual(result["aggregate_before_kickoff"]["aggregate_difference_for_home_before_kickoff"],-2)
        self.assertIsNone(result["goal_multiplier"])
        self.assertFalse(result["forecast_authorized"])
        self.assertTrue(result["extra_time_penalties_excluded_from_90min_market"])
    def test_knockout_first_leg_has_no_past_score(self):
        d={"observed_at":NOW,"source_url":SRC,"leg":1}
        result=context_for(fixture("KNOCKOUT"),d,NOW)
        self.assertIsNone(result["aggregate_before_kickoff"])
        d["first_leg_goals_for_current_home"]=1
        with self.assertRaisesRegex(EuropeContextError,"FIRST_LEG"):
            context_for(fixture("KNOCKOUT"),d,NOW)
    def test_second_leg_unknown_first_leg_result_cannot_be_guessed(self):
        d=second_leg();del d["first_leg_goals_for_current_away"]
        with self.assertRaisesRegex(EuropeContextError,"SECOND_LEG"):
            context_for(fixture("KNOCKOUT"),d,NOW)
    def test_final_is_neutral_and_no_league_standings(self):
        d={"observed_at":NOW,"source_url":SRC}
        result=context_for(fixture("FINAL",neutral=True),d,NOW)
        self.assertEqual(result["format"],"SINGLE_NEUTRAL_VENUE_FINAL")
        with self.assertRaisesRegex(EuropeContextError,"FINAL_NEUTRAL"):
            context_for(fixture("FINAL",neutral=False),d,NOW)
    def test_europa_league_identical_rules_with_correct_links(self):
        c=fixture()
        c["competition"]="UEFA_EL"
        c["source_url"]=c["source_url"].replace("uefachampionsleague","uefaeuropaleague")
        d=league_context();d["source_url"]=d["source_url"].replace("uefachampionsleague","uefaeuropaleague")
        self.assertEqual(context_for(c,d,NOW)["competition"],"UEFA_EL")
    def test_wrong_standing_fields_do_not_pass(self):
        d=league_context();d["standings"]["home"]["points_after_match"]=10
        with self.assertRaisesRegex(EuropeContextError,"STANDING_FIELDS"):
            context_for(fixture(),d,NOW)
if __name__=="__main__":unittest.main()
