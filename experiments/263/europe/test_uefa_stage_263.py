"""Only new isolated UEFA source-candidate checks; no backtest."""
import unittest
from copy import deepcopy
from uefa_stage_263 import stage,UEFAStageError

NOW="2026-11-02T12:00:00+03:00"
CL="https://www.uefa.com/uefachampionsleague/match/2049614--galatasaray-vs-stuttgart/"
EL="https://www.uefa.com/uefaeuropaleague/match/2050116--celtic-vs-besiktas/"
def mk(c,url,h,a,k):
    return {"competition":c,"season":"2026-2027","round":"LEAGUE_PHASE",
            "home":h,"away":a,"source_url":url,
            "kickoff":k,"observed_at":NOW,"result_status":"SCHEDULED",
            "neutral_venue":False}
def two():
    return [mk("UEFA_CL",CL,"Galatasaray","Stuttgart","2026-11-03T17:45:00Z"),
            mk("UEFA_EL",EL,"Celtic","Beşiktaş","2026-11-05T20:00:00Z")]

class IsolatedUEFA(unittest.TestCase):
    def test_separate_cl_el_and_no_model_approval(self):
        rows=two();before=deepcopy(rows)
        output=stage(rows,NOW)
        self.assertEqual(before,rows)
        self.assertEqual(output["audit"]["counts"],{"UEFA_CL":1,"UEFA_EL":1})
        self.assertEqual(output["audit"]["verified_training_result_count"],0)
        self.assertFalse(output["audit"]["four_model_forecasts_allowed"])
        self.assertFalse(output["audit"]["pilot_recorded"])
        self.assertTrue(all(x["domestic_home_id"] is None for x in output["fixtures"]))
    def test_official_id_stays_same_after_kickoff_reschedule(self):
        first=two()[0];new=dict(first,kickoff="2026-11-04T18:45:00Z")
        self.assertEqual(stage([first],NOW)["fixtures"][0]["id"],stage([new],NOW)["fixtures"][0]["id"])
    def test_wrong_domain_scheme_competition_rejected(self):
        for url in (EL,CL.replace("www.uefa.com","uefa.com.evil.test"),
                    CL.replace("https://","http://")):
            with self.subTest(url=url),self.assertRaises(UEFAStageError):
                stage([dict(two()[0],source_url=url)],NOW)
    def test_repeated_official_id_is_rejected(self):
        with self.assertRaisesRegex(UEFAStageError,"DUPLICATE"):
            stage([two()[0],two()[0]],NOW)
    def test_second_leg_has_distinct_official_id(self):
        a=two()[0];b=dict(a,source_url=CL.replace("2049614","2049999"))
        self.assertEqual(len(stage([a,b],NOW)["fixtures"]),2)
    def test_no_partial_results_or_future_goals(self):
        for item in (dict(two()[0],home_goals=2),
                     dict(two()[0],result_status="FINAL",home_goals=2,away_goals=1)):
            with self.assertRaises(UEFAStageError):stage([item],NOW)
    def test_past_final_claim_is_still_unverified_not_training(self):
        a=dict(two()[0],result_status="FINAL",home_goals=2,away_goals=1,
               kickoff="2026-10-21T17:45:00Z",observed_at="2026-10-22T11:00:00Z")
        output=stage([a],NOW)
        self.assertEqual(output["fixtures"][0]["result_state"],"CLAIMED_FINAL_PENDING_SOURCE_VERIFICATION")
        self.assertFalse(output["fixtures"][0]["model_eligible"])
    def test_naive_kickoff_refused_not_guessed_CET(self):
        with self.assertRaisesRegex(UEFAStageError,"KICKOFF_TIMEZONE"):
            stage([dict(two()[0],kickoff="2026-11-03T18:45:00")],NOW)
    def test_past_blank_results_remain_unresolved(self):
        a=dict(two()[0],kickoff="2026-10-21T17:45:00Z")
        x=stage([a],NOW)
        self.assertEqual(x["fixtures"][0]["result_state"],"PAST_UNRESOLVED_CANDIDATE")
    def test_unsupported_tournament_rejected(self):
        with self.assertRaises(UEFAStageError):
            stage([dict(two()[0],competition="UEFA_CONF")],NOW)
if __name__=="__main__":unittest.main()
