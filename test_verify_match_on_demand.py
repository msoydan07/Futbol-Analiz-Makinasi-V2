"""Fast, isolated unit tests for on-demand seven-day fixture gate."""
import unittest
from datetime import datetime,timedelta,timezone
from verify_match_on_demand import verify_requested_fixture
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
if __name__=="__main__":unittest.main()
