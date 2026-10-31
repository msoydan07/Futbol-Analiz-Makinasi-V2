"""Fast, isolated unit tests for on-demand seven-day fixture gate."""
import unittest
import tempfile,csv
from pathlib import Path
from identity import Registry
from datetime import datetime,timedelta,timezone
from verify_match_on_demand import verify_requested_fixture,match_unplayed_candidate,verify_listed_match
class TestOnDemand(unittest.TestCase):
 def setUp(self):
  self.now=datetime(2026,10,31,12,tzinfo=timezone.utc)
  self.args=dict(league="ENG1",home="Arsenal",away="Chelsea",kickoff_iso=(self.now+timedelta(days=1)).isoformat(),source_url="https://www.premierleague.com/en/fixtures",retrieved_at_iso=self.now.isoformat(),now=self.now)
 def test_not_checked(self):
  self.assertEqual(verify_requested_fixture(**self.args)["status"],"NOT_VERIFIED")
 def test_unofficial_domain(self):
  args=dict(self.args,source_url="https://premierleague.com.evil.example/fixtures")
  self.assertEqual(verify_requested_fixture(**args,source_checked=True)["status"],"REJECTED")
 def test_outside_window(self):
  args=dict(self.args,kickoff_iso=(self.now+timedelta(days=8)).isoformat())
  self.assertEqual(verify_requested_fixture(**args,source_checked=True)["status"],"OUTSIDE_WINDOW")
 def test_no_timezone(self):
  args=dict(self.args,kickoff_iso="2026-11-01T12:00:00")
  self.assertEqual(verify_requested_fixture(**args,source_checked=True)["status"],"REVIEW_REQUIRED")
class TestExistingUnplayedList(unittest.TestCase):
 def test_pairing_ignores_provisional_date_and_uses_aliases(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);reg=Registry(root/"match_registry.json")
   reg.register_team("kasimpasa","Kasimpasa",["Kasımpaşa"])
   reg.register_team("besiktas","Besiktas",["Beşiktaş"])
   reg.save()
   csvpath=root/"unplayed_fixture_candidates.csv"
   with csvpath.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["season","league","home","away","date","classification","verification"])
    w.writeheader()
    w.writerow(dict(season="2026-2027",league="TUR1",home="Kasimpasa",away="Besiktas",
                    date="2026-10-01",classification="PAST_UNRESOLVED",
                    verification="UNVERIFIED_FIXTURE_CANDIDATE"))
   kwargs=dict(candidates_path=str(csvpath),registry_path=str(root/"match_registry.json"))
   self.assertEqual(match_unplayed_candidate("TUR1","Kasımpaşa","Beşiktaş",**kwargs)["status"],"MATCHED_UNPLAYED")
   self.assertEqual(match_unplayed_candidate("TUR1","Beşiktaş","Kasımpaşa",**kwargs)["status"],"NOT_IN_LIST")
   now=datetime(2026,10,31,12,tzinfo=timezone.utc)
   result=verify_listed_match("TUR1","Kasımpaşa","Beşiktaş","2026-11-01T19:00:00+03:00",
       "https://www.tff.org/Default.aspx?pageId=198",now.isoformat(),now=now,
       source_checked=True,**kwargs)
   self.assertEqual(result["status"],"VERIFIED")
   self.assertTrue(result["unplayed_list_match"])

if __name__=="__main__":unittest.main()
