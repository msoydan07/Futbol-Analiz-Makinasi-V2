"""Small checks of actual 4518 accepted file; no formula refit and no fake betting."""
import copy,json,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
from weekend_source_readiness_263 import analyze,LEAGUES,DATES

NOW=datetime(2026,11,4,20,0,tzinfo=timezone.utc)
SOURCE=Path("data/quad_accepted_263/extended_history.csv")
ACCEPTANCE=Path("data/quad_accepted_263/source_acceptance.json")
class WeekendPreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ok=analyze(SOURCE,ACCEPTANCE,now=NOW)
    def test_actual_4518_and_ten_leagues(self):
        self.assertEqual(self.ok["source_count"],4518)
        self.assertEqual(self.ok["league_count"],10)
        self.assertEqual(set(self.ok["leagues"]),set(LEAGUES))
        self.assertTrue(self.ok["ready_all"])
        self.assertEqual(set(next(iter(self.ok["leagues"].values()))["target_dates"]),set(DATES))
    def test_eligibility_shortened_dutch_match_excluded(self):
        self.assertEqual(len(self.ok["leagues"]["NED1"]["excluded_shortened_match_ids"]),1)
        self.assertEqual(self.ok["leagues"]["NED1"]["rows_in_source"]-
                         self.ok["leagues"]["NED1"]["full_match_training_rows"],1)
    def test_english_championship_nine_still_partial(self):
        self.assertEqual(self.ok["leagues"]["ENG2"]["source_rows_with_missing_extended_fields"],9)
        self.assertTrue(self.ok["leagues"]["ENG2"]["target_dates"]["2026-11-06"]["mechanical_ready"])
        self.assertFalse(self.ok["all_rows_independently_verified"])
        self.assertFalse(self.ok["odds_source_verified"])
    def test_stale_owner_acceptance_blocks(self):
        with self.assertRaisesRegex(ValueError,"EXPIRED"):
            analyze(SOURCE,ACCEPTANCE,now=NOW+timedelta(days=8))
    def test_acceptance_status_forgery_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            obj=json.loads(ACCEPTANCE.read_text())
            obj["all_4518_independently_verified"]=True
            target=Path(td)/"bad.json"
            target.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError,"PROOF_MISMATCH"):
                analyze(SOURCE,target,now=NOW)
if __name__=="__main__":unittest.main()
