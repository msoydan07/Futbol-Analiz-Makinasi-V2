import unittest
from datetime import datetime,timezone,timedelta
from sabah_fixture_rotation_263 import (prepare_day,rotation_from_official_inputs,
    FixturePreparationError,CANDIDATES_SCHEMA,EXPECTED_DAYS,LEAGUES,render_mobile)

def candidates():
    rows=[]
    for day,n in EXPECTED_DAYS.items():
        for i in range(n):
            rows.append({"date":day,"league":"TUR1","home":"E"+str(i),
                         "away":"D"+str(i),"kickoff_turkey":None,
                         "fixture_verified_kickoff_utc":None,
                         "status":"DAY_ONLY_PREPARATION_NOT_FORECAST"})
    return {"schema":CANDIDATES_SCHEMA,"fixture_count":96,
            "day_counts":EXPECTED_DAYS.copy(),"fixtures":rows}
NOW=datetime(2026,11,7,7,0,tzinfo=timezone.utc)
KO=datetime(2026,11,7,15,0,tzinfo=timezone.utc)
TARGET={"status":"VERIFIED","league":"TUR1","home_id":"HomeA",
        "away_id":"AwayB","kickoff_utc":KO.isoformat(),
        "source_url":"https://www.tff.org/example"}
def event(team,dt,competition="UCL",verified=True):
    return {"team_id":team,"kickoff_utc":dt.isoformat(),"competition":competition,
            "source_url":"https://www.uefa.com/example" if verified else "",
            "verification":"VERIFIED_OFFICIAL_ADAPTER" if verified else "UNKNOWN",
            "opponent":"OtherClub"}
class PreparationTests(unittest.TestCase):
 def test_day_44(self):
    p=prepare_day(candidates(),"2026-11-07")
    self.assertEqual(p["candidate_count"],44)
    self.assertEqual(p["officially_verified_kickoffs"],0)
    self.assertEqual(p["morning_forecast_count_increment"],0)
    self.assertIn("TEYİT BEKLİYOR",render_mobile(p))
 def test_other_days(self):
    d=candidates()
    self.assertEqual(prepare_day(d,"2026-11-06")["candidate_count"],10)
    self.assertEqual(prepare_day(d,"2026-11-08")["candidate_count"],42)
 def test_no_unknown_day(self):
    with self.assertRaises(FixturePreparationError):prepare_day(candidates(),"2026-11-10")
 def test_block_modified_legacy(self):
    d=candidates();d["fixtures"][0]["kickoff_turkey"]="16:00"
    with self.assertRaises(FixturePreparationError):prepare_day(d,"2026-11-07")
 def test_block_duplicate(self):
    d=candidates();d["fixtures"][1]=d["fixtures"][0].copy()
    with self.assertRaises(FixturePreparationError):prepare_day(d,"2026-11-06")
 def test_missing_roster(self):
    r=rotation_from_official_inputs(TARGET,[],NOW)
    self.assertEqual(r["teams"]["HomeA"]["rotation_label"],"VERI_YETERSIZ")
 def test_short_rest_is_review_not_certain_rotation(self):
    r=rotation_from_official_inputs(TARGET,[event("HomeA",KO+timedelta(days=2))],NOW,
                 feeds_complete={"HomeA":True,"AwayB":True})
    self.assertEqual(r["teams"]["HomeA"]["rotation_label"],"INCELENMELI")
    self.assertEqual(r["teams"]["HomeA"]["quantitative_model_adjustment"],0)
    self.assertEqual(r["teams"]["AwayB"]["rotation_label"],"BELIRGIN_ISARET_YOK")
 def test_window_bounds(self):
    r=rotation_from_official_inputs(TARGET,
        [event("HomeA",KO-timedelta(days=8)),event("HomeA",KO+timedelta(days=11))],NOW)
    self.assertFalse(r["teams"]["HomeA"]["past_7_days"])
    self.assertFalse(r["teams"]["HomeA"]["next_7_days"])
 def test_request_anchored_plus_seven_not_kickoff_plus_seven(self):
    inside=NOW+timedelta(days=7)
    outside=inside+timedelta(seconds=1)
    r=rotation_from_official_inputs(TARGET,[
        event("HomeA",inside),event("HomeA",outside),
        event("AwayB",NOW-timedelta(days=7))],NOW)
    self.assertEqual([x["utc"] for x in r["teams"]["HomeA"]["next_7_days"]],
                     [inside.isoformat()])
    self.assertEqual(len(r["teams"]["AwayB"]["past_7_days"]),1)
    self.assertEqual(r["window_basis"],"ANALYSIS_REQUEST_PLUS_MINUS_SEVEN_DAYS")
    self.assertEqual(r["analysis_requested_at_utc"],NOW.isoformat())
 def test_pre_target_match_after_request_still_counts_future_from_request(self):
    before_target=NOW+timedelta(hours=4)
    r=rotation_from_official_inputs(TARGET,[event("HomeA",before_target)],NOW,
                                   feeds_complete={"HomeA":True,"AwayB":True})
    self.assertEqual(len(r["teams"]["HomeA"]["past_7_days"]),0)
    self.assertEqual(len(r["teams"]["HomeA"]["next_7_days"]),1)
    self.assertEqual(r["teams"]["HomeA"]["last_rest_hours"],4.0)
    self.assertEqual(r["teams"]["HomeA"]["rotation_label"],"INCELENMELI")
    self.assertFalse(r["model_probabilities_changed"])
 def test_unverified_does_not_upgrade(self):
    r=rotation_from_official_inputs(TARGET,[event("HomeA",KO+timedelta(days=2),verified=False)],NOW)
    self.assertEqual(r["teams"]["HomeA"]["rotation_label"],"VERI_YETERSIZ")
    self.assertEqual(r["teams"]["HomeA"]["unverified_adjacent_count"],1)
 def test_postkickoff_blocked(self):
    with self.assertRaises(FixturePreparationError):rotation_from_official_inputs(TARGET,[],KO)
 def test_unverified_target_blocked(self):
    t=TARGET.copy();t["status"]="INFERRED"
    with self.assertRaises(FixturePreparationError):rotation_from_official_inputs(t,[],NOW)
 def test_no_automatic_high_risk_from_one_uefa(self):
    r=rotation_from_official_inputs(TARGET,[event("HomeA",KO+timedelta(days=3))],NOW,
                                  feeds_complete={"HomeA":True})
    self.assertNotEqual(r["teams"]["HomeA"]["rotation_label"],"YUKSEK_RISK_UYARISI")
if __name__=="__main__":unittest.main()
