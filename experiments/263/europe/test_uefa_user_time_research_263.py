"""New user-reported kickoff policy; fixture not accessed, pilot untouched."""
import copy,json,unittest
from datetime import datetime,timedelta
from pathlib import Path
from uefa_user_time_research_263 import requested_europe_research,UserTimeError
IDX=json.loads(Path("experiments/263/evidence/identity_index_263.json").read_text(encoding="utf-8"))
NOW=datetime.fromisoformat("2026-11-02T18:31:00+03:00")
class RequestedUserTime(unittest.TestCase):
    def run_case(self,h="Galatasaray",a="Barcelona",d="2026-11-03",t="21:00",now=NOW,comp="UEFA_CL",cb=None):
        return requested_europe_research(comp,h,a,d,t,index=IDX,now=now,downstream=cb)
    def test_scope_first_user_time_without_uefa_site(self):
        calls=[]
        result,payload=self.run_case(cb=lambda r:calls.append(1) or "research only")
        self.assertEqual(calls,[1])
        self.assertEqual(payload,"research only")
        self.assertTrue(result["data_research_allowed"])
        self.assertFalse(result["official_fixture_verified"])
        self.assertFalse(result["model_predictions_approved"])
        self.assertFalse(result["pilot_registration_allowed"])
        self.assertEqual(result["reported_kickoff_utc"],"2026-11-03T18:00:00+00:00")
    def test_known_noncurrent_team_not_researched(self):
        calls=[]
        result,payload=self.run_case(a="Leicester",cb=lambda r:calls.append(1))
        self.assertEqual(result["status"],"ANALYSIS_SKIPPED_OUTSIDE_TEN_LEAGUES")
        self.assertEqual(calls,[])
        self.assertIsNone(payload)
    def test_unknown_team_never_researched(self):
        calls=[]
        result,payload=self.run_case(a="Celtic",cb=lambda r:calls.append(1))
        self.assertEqual(result["status"],"ANALYSIS_SKIPPED_TEAM_SCOPE_UNVERIFIED")
        self.assertEqual(calls,[])
        self.assertIsNone(payload)
    def test_past_match_blocks(self):
        result,_=self.run_case(d="2026-11-01")
        self.assertEqual(result["status"],"USER_REPORTED_KICKOFF_ALREADY_PASSED")
    def test_exact_now_blocks(self):
        result,_=self.run_case(d="2026-11-02",t="18:31")
        self.assertEqual(result["status"],"USER_REPORTED_KICKOFF_ALREADY_PASSED")
    def test_beyond_seven_days_blocks(self):
        result,_=self.run_case(d="2026-11-12")
        self.assertEqual(result["status"],"OUTSIDE_NEXT_SEVEN_DAYS")
    def test_7_day_boundary_is_valid(self):
        result,_=self.run_case(d="2026-11-09",t="18:31")
        self.assertTrue(result["data_research_allowed"])
    def test_invalid_time_blocks(self):
        for t in ("9:15","24:00","21","21:75"):
            with self.subTest(t=t):
                result,_=self.run_case(t=t)
                self.assertEqual(result["status"],"USER_DATE_TIME_INVALID")
    def test_invalid_calendar_date_blocks(self):
        result,_=self.run_case(d="2026-11-31")
        self.assertEqual(result["status"],"USER_DATE_TIME_INVALID")
    def test_away_team_local_istanbul_conversion(self):
        result,_=self.run_case(d="2026-11-03",t="00:30")
        self.assertEqual(result["reported_kickoff_utc"],"2026-11-02T21:30:00+00:00")
    def test_europa_as_a_supported_tournament(self):
        result,_=self.run_case(h="Crystal Palace",a="Hoffenheim",
                               d="2026-11-05",t="20:45",comp="UEFA_EL")
        self.assertTrue(result["data_research_allowed"])
    def test_bad_competition_rejected(self):
        with self.assertRaisesRegex(UserTimeError,"UNSUPPORTED_COMPETITION"):
            self.run_case(comp="UEFA_ECL")
    def test_naive_asof_rejected(self):
        with self.assertRaisesRegex(UserTimeError,"AWARE_NOW_REQUIRED"):
            self.run_case(now=datetime(2026,11,2,18,31))
    def test_index_readonly(self):
        before=copy.deepcopy(IDX)
        self.run_case()
        self.assertEqual(before,IDX)
if __name__=="__main__":unittest.main()
