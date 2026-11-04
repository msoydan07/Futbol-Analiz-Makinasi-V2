"""One targeted pinned live-gate bridge test. No source or model acceptance."""
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from analyze_named_match_gate import run

PIN=Path("experiments/263/evidence/identity_index_263.json")
NOW=datetime.now(timezone.utc)

class CurrentIdentityBridgeTests(unittest.TestCase):
    def test_pinned_215_team_index_exists(self):
        self.assertTrue(PIN.is_file())
    def test_tff_current_team_ids_well_defined(self):
        # This is a SYNTHETIC official observation to test identity only.
        o={"status":"VERIFIED_OFFICIAL_FIXTURE",
           "home":"GAZİANTEP FUTBOL KULÜBÜ A.Ş.",
           "away":"KASIMPAŞA A.Ş.",
           "kickoff_utc":(NOW+timedelta(days=2)).isoformat(),
           "source_url":"https://www.tff.org/default.aspx?ftxtID=2966&pageID=600",
           "retrieved_at_utc":NOW.isoformat()}
        result=run("TUR1","Gaziantep FK","Kasımpaşa",
                   lookup_override=lambda h,a:o)
        self.assertEqual(result.get("status"),"VERIFIED",result)
        self.assertNotEqual(result.get("home_id"),result.get("away_id"))
    def test_outside_league_cannot_be_accepted(self):
        result=run("TUR1","Arsenal","Kasımpaşa",lookup_override=lambda h,a:None)
        self.assertEqual(result["status"],"REVIEW_REQUIRED",result)
    def test_unknown_registry_is_never_auto_created(self):
        result=run("TUR1","Gaziantep FK","Kasımpaşa",
                   registry_path="data/MISSING_REGISTRY_NEVER_CREATE.json")
        self.assertEqual(result.get("reason"),"canonical_registry_file_missing")
    def test_wrong_observed_official_team_rejected(self):
        o={"status":"VERIFIED_OFFICIAL_FIXTURE",
           "home":"KASIMPAŞA A.Ş.","away":"GAZİANTEP FUTBOL KULÜBÜ A.Ş.",
           "kickoff_utc":(NOW+timedelta(days=2)).isoformat(),
           "source_url":"https://www.tff.org/default.aspx?ftxtID=2966&pageID=600",
           "retrieved_at_utc":NOW.isoformat()}
        result=run("TUR1","Gaziantep FK","Kasımpaşa",lookup_override=lambda h,a:o)
        self.assertEqual(result.get("reason"),"official_match_identity_mismatch")

if __name__=="__main__":unittest.main()
