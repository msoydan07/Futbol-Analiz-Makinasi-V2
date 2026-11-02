"""New T-60 overlay tests, no fixture search and no extra model runs."""
import copy,json,unittest
from datetime import datetime
from pathlib import Path
from uefa_t60_lineup_overlay_263 import requested_with_matchday_lineup,valid_xi
IX=json.loads(Path("experiments/263/evidence/identity_index_263.json").read_text(encoding="utf-8"))
NOW=datetime.fromisoformat("2026-11-02T20:00:00+03:00")
PLAYERS_H=[f"Home Player {i}" for i in range(1,12)]
PLAYERS_A=[f"Away Player {i}" for i in range(1,12)]
# All test players and matches are SYNTHETIC, not real lineup claims.
EVENT={"competition":"UEFA_CL","home":"Galatasaray","away":"Barcelona",
       "kickoff_utc":"2026-11-02T18:00:00+00:00",
       "observed_at_utc":"2026-11-02T17:58:00+00:00",
       "source_url":"https://www.livescore.com/en/football/champions-league/fixture/123/",
       "lineup_status":"CONFIRMED",
       "home_starting_xi":PLAYERS_H,"away_starting_xi":PLAYERS_A}
class T60Evidence(unittest.TestCase):
    def call(self,home="Galatasaray",away="Barcelona",date="2026-11-02",tm="21:00",provider=None,now=NOW):
        return requested_with_matchday_lineup("UEFA_CL",home,away,date,tm,
                                              index=IX,now=now,lineup_provider=provider)
    def test_matching_claim_never_promoted_without_actual_source_fetch(self):
        r=self.call(provider=lambda q:copy.deepcopy(EVENT))
        xi=r["lineup_observation"]
        self.assertTrue(r["data_research_allowed"])
        self.assertEqual(xi["status"],"CONFIRMED_LINEUP_SOURCE_CLAIM_MATCHED_AWAITING_SOURCE_REVIEW")
        self.assertFalse(xi["lineup_source_independently_fetched_by_github"])
        self.assertFalse(xi["lineup_math_effect_authorized"])
        self.assertFalse(r["model_predictions_approved"])
        self.assertFalse(r["pilot_registration_allowed"])
    def test_unknown_or_outside_club_calls_zero_providers(self):
        for club in ("Celtic","Leicester"):
            with self.subTest(club=club):
                calls=[]
                r=self.call(away=club,provider=lambda q:calls.append(1))
                self.assertEqual(calls,[])
                self.assertFalse(r["data_research_allowed"])
    def test_no_lineups_analytics_continue(self):
        r=self.call(provider=lambda x:None)
        self.assertTrue(r["data_research_allowed"])
        self.assertEqual(r["lineup_observation"]["status"],"LINEUPS_NOT_CONFIRMED")
        self.assertEqual(r["lineup_observation"]["reason"],"NO_MATCH_CENTRE_LINEUPS_PUBLISHED_OR_RETRIEVED")
    def test_predictions_are_rejected(self):
        x={**EVENT,"lineup_status":"PREDICTED"}
        r=self.call(provider=lambda _:x)
        self.assertEqual(r["lineup_observation"]["reason"],"PREDICTED_OR_UNPUBLISHED_XI_NOT_ACCEPTED")
    def test_wrong_match_away_rejected(self):
        x={**EVENT,"away":"Aston Villa"}
        r=self.call(provider=lambda _:x)
        self.assertEqual(r["lineup_observation"]["reason"],
                         "LINEUPS_BELONG_TO_DIFFERENT_MATCH_OR_UNRESOLVED_TEAM")
    def test_kickoff_mismatch_rejected_without_extra_fixture_lookup(self):
        x={**EVENT,"kickoff_utc":"2026-11-02T19:00:00+00:00"}
        r=self.call(provider=lambda _:x)
        self.assertEqual(r["lineup_observation"]["reason"],"USER_VS_SOURCE_KICKOFF_CONFLICT_GT_15_MIN")
    def test_future_observation_rejected(self):
        x={**EVENT,"observed_at_utc":"2026-11-02T19:30:00+00:00"}
        r=self.call(provider=lambda _:x)
        self.assertEqual(r["lineup_observation"]["reason"],"AFTER_KICKOFF_OR_FUTURE_LINEUP_OBSERVATION")
    def test_broken_xi_or_duplicates_rejected(self):
        self.assertFalse(valid_xi(["Foo"]*11))
        x={**EVENT,"home_starting_xi":["Same Player"]*11}
        r=self.call(provider=lambda _:x)
        self.assertEqual(r["lineup_observation"]["reason"],"MISSING_OR_DUPLICATE_XI_PLAYERS")
    def test_source_host_spoofing_rejected(self):
        x={**EVENT,"source_url":"https://www.livescore.com.attacker.example/en/fixture"}
        r=self.call(provider=lambda _:x)
        self.assertEqual(r["lineup_observation"]["reason"],"UNREVIEWED_LINEUP_SOURCE_HOST")
    def test_no_source_provider_is_not_blocker(self):
        r=self.call()
        self.assertTrue(r["data_research_allowed"])
        self.assertEqual(r["lineup_observation"]["status"],"LINEUPS_NOT_CONFIRMED")
    def test_more_than_120_min_before_kickoff_provider_not_invoked(self):
        calls=[]
        r=self.call(date="2026-11-03",provider=lambda q:calls.append(1))
        self.assertEqual(calls,[])
        self.assertEqual(r["lineup_observation"]["reason"],"LINEUP_CHECK_WINDOW_NOT_YET_OPEN")
    def test_read_only(self):
        before=copy.deepcopy(IX)
        self.call(provider=lambda q:copy.deepcopy(EVENT))
        self.assertEqual(before,IX)
if __name__=="__main__":unittest.main()
