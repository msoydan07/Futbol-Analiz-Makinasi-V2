"""Synthetic official-source day preflight; no real football odds or requests."""
import copy,unittest
from datetime import datetime,timedelta,timezone
from official_page_lookup_263 import SOURCES
from sabah_10league_manifest_preflight_263 import inspect,manifest,mobile,IntakeBlocked
NOW=datetime(2026,11,8,6,0,tzinfo=timezone.utc)
DAY="2026-11-08"
class Fake:
    def __init__(self):
        self.calls=[]
        self.sources={}
        for league in SOURCES:
            self.sources[league]={
                "status":"FETCHED_OFFICIAL_PAGE","events":[],
                "source_url":SOURCES[league][0],"effective_url":SOURCES[league][0],
                "html_sha256":"f"*64,"reason":None}
        self.sources["GER1"]["events"]=[
            {"home":"Köln","away":"Leverkusen","kickoff_utc":"2026-11-08T14:30:00+00:00","format":"dfl"}]
        self.sources["POR1"]["events"]=[
            {"home":"Estoril","away":"Marítimo","kickoff_utc":"2026-11-08T15:30:00+00:00","format":"liga"}]
        self.sources["ENG2"]["status"]="NOT_VERIFIED"
        self.sources["ENG2"]["reason"]="JSONLD_UNAVAILABLE"
    def _get(self,league):
        self.calls.append(league);return self.sources[league]
    def resolve_id(self,league,name):
        if name=="Unknown":raise ValueError("UNKNOWN_CLUB")
        return league+"/"+name
class Preflight(unittest.TestCase):
    def setUp(self):self.g=Fake()
    def test_all_ten_report_even_empty(self):
        r=inspect(DAY,gateway=self.g,now=NOW)
        self.assertEqual(r["league_count"],10)
        self.assertEqual(len(set(self.g.calls)),10)
        self.assertEqual(r["candidate_count"],2)
        self.assertEqual(len(r["source_coverage"]),10)
        self.assertFalse(r["all_ten_leagues_claimed_fully_covered"])
        self.assertEqual(r["bookmaker_api_calls"],0)
        self.assertEqual(r["new100_pilot_count_change"],0)
        self.assertIn("ENG2",mobile(r))
    def test_current_day_only_no_backdating(self):
        with self.assertRaises(IntakeBlocked):inspect("2026-11-07",gateway=self.g,now=NOW)
        with self.assertRaises(IntakeBlocked):inspect("2026-11-09",gateway=self.g,now=NOW)
    def test_missing_official_source_is_not_zero_games(self):
        r=inspect(DAY,gateway=self.g,now=NOW)
        x=next(v for v in r["source_coverage"] if v["league"]=="ENG2")
        self.assertEqual(x["blocker"],"SOURCE_FETCH_FAILED")
        self.assertEqual(x["same_day_canonical_timed_candidates"],0)
        self.assertTrue(r["zero_matches_is_not_evidence_of_no_fixtures"])
    def test_unverified_team_blocked_and_unresolved(self):
        self.g.sources["BEL1"]["events"]=[{"home":"Unknown","away":"Cercle",
             "kickoff_utc":"2026-11-08T17:30:00+00:00"}]
        x=inspect(DAY,gateway=self.g,now=NOW)
        row=next(v for v in x["source_coverage"] if v["league"]=="BEL1")
        self.assertEqual(row["same_day_canonical_timed_candidates"],0)
        self.assertEqual(row["rejected"]["NOT_CANONICAL_OR_WRONG_KICKOFF"],1)
    def test_date_only_ambiguous_and_yesterday_not_promoted(self):
        self.g.sources["FRA1"]["events"]=[
            {"home":"Paris","away":"Nice","kickoff_utc":None},
            {"home":"Paris","away":"Lille","kickoff_utc":"2026-11-07T18:00:00Z"},
            {"home":"Paris","away":"Lyon","kickoff_utc":"2026-11-08T15:30:00Z"},
            {"home":"Paris","away":"Lyon","kickoff_utc":"2026-11-08T16:30:00Z"}
        ]
        x=inspect(DAY,gateway=self.g,now=NOW)
        row=next(v for v in x["source_coverage"] if v["league"]=="FRA1")
        self.assertEqual(row["same_day_canonical_timed_candidates"],0)
        self.assertEqual(row["rejected"]["DATE_ONLY_OR_NO_KICKOFF"],1)
        self.assertEqual(row["rejected"]["DUPLICATE_OR_AMBIGUOUS"],2)
    def test_no_automatic_new100_trigger_manifest(self):
        r=inspect(DAY,gateway=self.g,now=NOW)
        data=manifest(r)
        self.assertTrue(data["candidate_only_not_new100_authorized"])
        self.assertEqual(len(data["matches"]),2)
        self.assertNotEqual(set(data),{"schema","day_turkey","matches"})
        self.assertTrue(all(set(m)=={"league","home","away"} for m in data["matches"]))
    def test_zero_hour_naive_clock_block(self):
        with self.assertRaises(IntakeBlocked):inspect(DAY,gateway=self.g,now=datetime(2026,11,8))
if __name__=="__main__":unittest.main()
