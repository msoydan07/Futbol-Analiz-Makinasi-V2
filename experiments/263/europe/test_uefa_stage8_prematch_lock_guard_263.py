import copy
import datetime as dt
import unittest
from uefa_stage8_prematch_lock_guard_263 import validate,LockError
UTC=dt.timezone.utc
BASE=dt.datetime(2026,11,3,18,0,tzinfo=UTC)
def sample():
    def m():
        return {"1x2":{"home":.4,"draw":.3,"away":.3},
                "over_2_5":.5,"btts_yes":.4,"lambda_home":1.4,"lambda_away":1.2}
    return {"schema":"263_UEFA_STAGE8_PREMATCH_DUAL_SHADOW_RECORD_V1",
      "kickoff_utc":"2026-11-03T19:00:00+00:00",
      "data_captured_utc":"2026-11-03T17:50:00+00:00",
      "competition":"UEFA_CL","uefa_match_id":2049614,
      "lineup_status":"NOT_VERIFIED","lineup_source_urls":[],
      "lineup_used_as_numeric_adjustment":False,
      "elo_beta_production_approved":False,"pilot_100_matches_affected":False,
      "source_sha256":{x:"a"*64 for x in ("stage4","stage5","retro")},
      "model_outputs":{"M0_REFERENCE_ONLY":m(),"M0_PLUS_ELO_EXPERIMENTAL":m()},
      "odds_or_ev_present":False}
class GuardTests(unittest.TestCase):
    def test_01_good_candidate_only_is_validated(self):self.assertTrue(validate(sample(),BASE.isoformat()))
    def test_01b_real_uefa_integer_match_id_accepted(self):
        x=sample();x["uefa_match_id"]=2049614
        self.assertTrue(validate(x,BASE.isoformat()))
    def test_01c_declared_unannounced_without_source_blocked(self):
        x=sample();x["lineup_status"]="NOT_ANNOUNCED"
        with self.assertRaisesRegex(LockError,"LINEUP_SOURCE_REQUIRED"):
            validate(x,BASE.isoformat())
    def test_01d_unverified_lineup_is_nonblocking_but_honest(self):
        x=sample();x["lineup_status"]="NOT_VERIFIED"
        self.assertTrue(validate(x,BASE.isoformat()))
    def test_02_after_kickoff_blocked(self):
        with self.assertRaises(LockError):validate(sample(),"2026-11-03T19:00:00+00:00")
    def test_03_future_data_blocked(self):
        x=sample();x["data_captured_utc"]="2026-11-03T18:01:00+00:00"
        with self.assertRaises(LockError):validate(x,BASE.isoformat())
    def test_04_old_prematch_candidate_blocked(self):
        with self.assertRaises(LockError):validate(sample(),"2026-11-03T15:00:00+00:00")
    def test_05_one_model_missing_blocked(self):
        x=sample();x["model_outputs"].pop("M0_PLUS_ELO_EXPERIMENTAL")
        with self.assertRaises(LockError):validate(x,BASE.isoformat())
    def test_06_bad_probability_mass_blocked(self):
        x=sample();x["model_outputs"]["M0_REFERENCE_ONLY"]["1x2"]["home"]=.8
        with self.assertRaises(LockError):validate(x,BASE.isoformat())
    def test_07_official_lineup_without_source_blocked(self):
        x=sample();x["lineup_status"]="BOTH_OFFICIAL"
        with self.assertRaises(LockError):validate(x,BASE.isoformat())
    def test_08_unannounced_lineup_allowed(self):
        x=sample();x["lineup_status"]="NOT_ANNOUNCED"
        x["lineup_source_urls"]=["https://www.uefa.com/uefachampionsleague/"]
        self.assertTrue(validate(x,BASE.isoformat()))
    def test_09_unapproved_lineup_adjustment_blocked(self):
        x=sample();x["lineup_used_as_numeric_adjustment"]=True
        with self.assertRaises(LockError):validate(x,BASE.isoformat())
    def test_10_production_beta_promotion_blocked(self):
        x=sample();x["elo_beta_production_approved"]=True
        with self.assertRaises(LockError):validate(x,BASE.isoformat())
    def test_11_pilot_mutation_blocked(self):
        x=sample();x["pilot_100_matches_affected"]=True
        with self.assertRaises(LockError):validate(x,BASE.isoformat())
    def test_12_no_odds_ev_blocked(self):
        x=sample();x["odds_or_ev_present"]=True
        with self.assertRaises(LockError):validate(x,BASE.isoformat())
if __name__=="__main__":unittest.main()
