"""No bulk fixtures needed for single-match official verification."""
import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from identity import Registry
from analyze_named_match_gate import run

class TestNamedGate(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.path=str(Path(self.tmp.name)/"registry.json")
  reg=Registry(self.path)
  reg.register_team("arsenal","Arsenal")
  reg.register_team("chelsea","Chelsea")
  reg.save()
  self.now=datetime.now(timezone.utc)
 def observation(self):
  return {"status":"VERIFIED_OFFICIAL_FIXTURE",
          "home":"Arsenal","away":"Chelsea",
          "kickoff_utc":(self.now+timedelta(days=1)).isoformat(),
          "source_url":"https://www.premierleague.com/en/fixtures",
          "retrieved_at_utc":self.now.isoformat()}
 def test_official_observation_without_bulk_csv(self):
  r=run("ENG1","Arsenal","Chelsea",lookup_override=lambda h,a:self.observation(),registry_path=self.path)
  self.assertEqual(r["status"],"VERIFIED")
  self.assertEqual(r["next_step"],"COLLECT_AND_VALIDATE_2_6_2_INPUTS")
  self.assertFalse(r["first_xi_required"])
 def test_unverified_never_enters_analysis(self):
  r=run("ENG1","Arsenal","Chelsea",lookup_override=lambda h,a:{"status":"NOT_VERIFIED"},registry_path=self.path)
  self.assertEqual(r["status"],"NOT_VERIFIED")
 def test_unofficial_url_rejected(self):
  r=run("ENG1","Arsenal","Chelsea",lookup_override=lambda h,a:dict(self.observation(),source_url="https://fake.example"),registry_path=self.path)
  self.assertEqual(r["status"],"REJECTED")
 def test_wrong_observed_teams_rejected(self):\n  r=run("ENG1","Arsenal","Chelsea",lookup_override=lambda h,a:dict(self.observation(),away="Liverpool"),registry_path=self.path)\n  self.assertEqual(r["status"],"NOT_VERIFIED")\n def test_missing_team_registry_never_fakes_success(self):
  r=run("ENG1","Arsenal","Unknown",lookup_override=lambda h,a:self.observation(),registry_path=self.path)
  self.assertEqual(r["status"],"REVIEW_REQUIRED")

if __name__=="__main__":unittest.main()
