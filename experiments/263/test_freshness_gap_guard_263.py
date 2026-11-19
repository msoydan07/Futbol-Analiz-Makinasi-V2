"""Synthetic fail-closed source-gap checks. No web calls and no forecasts."""
import csv
import io
import unittest
from datetime import date,datetime,timedelta,timezone
from freshness_gap_guard_263 import review_gap,StaleLeagueData,MAX_DEFAULT_DAYS

NOW=datetime(2026,11,20,6,0,tzinfo=timezone.utc)
TARGET="2026-11-20"
SOURCE="https://www.football-data.co.uk/mmz4281/2627/E0.csv"

def prepare(*,newer=False,bad_score=False,no_future=False,missing=False):
    fields=("Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR")
    history=[]
    src=[]
    first=date(2026,11,8)-timedelta(days=39)
    for i in range(40):
        day=first+timedelta(days=i)
        score=(i%3,(i+1)%3)
        history.append({"league":"ENG1","season":"2026-2027",
            "match_date":day.isoformat(),"home_id":"h"+str(i),
            "away_id":"a"+str(i),"home_goals":str(score[0]),
            "away_goals":str(score[1])})
        rec={"Date":day.strftime("%d/%m/%Y"),"HomeTeam":"Home"+str(i),
            "AwayTeam":"Away"+str(i),"FTHG":str(score[0]),
            "FTAG":str(score[1]),
            "FTR":"H" if score[0]>score[1] else "A" if score[0]<score[1] else "D"}
        if bad_score and i==39:
            rec["FTHG"]="2" if score[0]!=2 else "1"
            rec["FTR"]="H" if int(rec["FTHG"])>score[1] else "A" if int(rec["FTHG"])<score[1] else "D"
        if not (missing and i==38):src.append(rec)
    if newer:
        src.append({"Date":"12/11/2026","HomeTeam":"NewOne","AwayTeam":"NewTwo",
                    "FTHG":"1","FTAG":"0","FTR":"H"})
    if not no_future:
        for day in ("21/11/2026","22/11/2026"):
            src.append({"Date":day,"HomeTeam":"FutureHome","AwayTeam":"FutureAway",
                        "FTHG":"","FTAG":"","FTR":""})
    f=io.StringIO(newline="")
    writer=csv.DictWriter(f,fieldnames=fields)
    writer.writeheader()
    writer.writerows(src)
    data=f.getvalue().encode()
    def fetch(url):
        assert url==SOURCE
        return data
    def resolve(name):
        return name.replace("Home","h").replace("Away","a")
    return history,fetch,resolve

class GapSafety(unittest.TestCase):
    def test_real_break_with_zero_missing_completed_matches(self):
        h,fetch,resolver=prepare()
        e=review_gap(h,"ENG1",TARGET,now=NOW,fetcher=fetch,resolver=resolver)
        self.assertEqual(e["status"],"BOUNDED_GAP_NO_MISSING_RESULTS_IN_PUBLIC_FEED_RESEARCH_ONLY")
        self.assertEqual(e["age_days"],12)
        self.assertTrue(e["not_independent_federation_verified"])
        self.assertFalse(e["betting_authorized"])
        self.assertEqual(e["provider_last_result_date"],"2026-11-08")
        self.assertGreaterEqual(e["historical_overlap_matches_verified"],20)

    def test_new_completed_match_detected_and_requires_refresh(self):
        h,fetch,resolver=prepare(newer=True)
        with self.assertRaisesRegex(StaleLeagueData,"NEW_COMPLETED_RESULTS_MUST_REFRESH_HISTORY"):
            review_gap(h,"ENG1",TARGET,now=NOW,fetcher=fetch,resolver=resolver)

    def test_changed_score_never_silently_accepted(self):
        h,fetch,resolver=prepare(bad_score=True)
        with self.assertRaisesRegex(StaleLeagueData,"SOURCE_CONFLICTS_WITH_ACCEPTED_SCORES"):
            review_gap(h,"ENG1",TARGET,now=NOW,fetcher=fetch,resolver=resolver)

    def test_missing_provider_previous_matches_rejected(self):
        h,fetch,resolver=prepare(missing=True)
        with self.assertRaisesRegex(StaleLeagueData,"SOURCE_SHORTER_THAN_ACCEPTED_CURRENT_SEASON|SOURCE_MISSING_ACCEPTED_OVERLAP_RESULTS"):
            review_gap(h,"ENG1",TARGET,now=NOW,fetcher=fetch,resolver=resolver)

    def test_results_only_source_does_not_require_unplayed_fixture_rows(self):
        h,fetch,resolver=prepare(no_future=True)
        e=review_gap(h,"ENG1",TARGET,now=NOW,fetcher=fetch,resolver=resolver)
        self.assertEqual(e["next_unplayed_provider_fixtures"],0)
        self.assertEqual(e["status"],"BOUNDED_GAP_NO_MISSING_RESULTS_IN_PUBLIC_FEED_RESEARCH_ONLY")

    def test_over21_days_blocks_before_network_request(self):
        h,fetch,resolver=prepare()
        def no_network(_):
            raise AssertionError("Network should not be called")
        with self.assertRaisesRegex(StaleLeagueData,"GAP_EXCEEDS_LIMIT_REQUIRES_REFRESH"):
            review_gap(h,"ENG1","2026-12-01",now=datetime(2026,12,1,6,tzinfo=timezone.utc),
                       fetcher=no_network,resolver=resolver)

    def test_default_ten_day_has_no_network_call(self):
        h,fetch,resolver=prepare()
        def no_network(_):
            raise AssertionError("no network needed")
        r=review_gap(h,"ENG1","2026-11-15",
                     now=datetime(2026,11,15,6,tzinfo=timezone.utc),
                     fetcher=no_network,resolver=resolver)
        self.assertEqual(r["status"],"WITHIN_NORMAL_TEN_DAY_LIMIT")
        self.assertFalse(r["source_network_called"])

    def test_future_or_same_day_snapshot_is_rejected(self):
        h,fetch,resolver=prepare()
        h.append({"league":"ENG1","season":"2026-2027","match_date":TARGET})
        with self.assertRaisesRegex(StaleLeagueData,"FUTURE_OR_SAME_DAY_HISTORY"):
            review_gap(h,"ENG1",TARGET,now=NOW,fetcher=fetch,resolver=resolver)

if __name__=="__main__":
    unittest.main()
