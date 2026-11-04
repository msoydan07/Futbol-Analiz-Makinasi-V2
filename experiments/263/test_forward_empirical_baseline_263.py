import csv
import hashlib
import tempfile
import unittest
from pathlib import Path
from test_forward_baseline_provenance_263 import forecast
from forward_calibration_bridge_263 import _digest
from forward_empirical_baseline_263 import produce
from forward_baseline_provenance_263 import connect_verified_baseline
from test_forward_calibration_bridge_263 import lock

class TestRealShape(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"history.csv"
        with self.path.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["fixture_id","league","match_date","home_goals","away_goals","result"])
            w.writeheader()
            for i in range(150):
                h=i%4;a=(i+1)%3
                w.writerow({"fixture_id":str(i),"league":"TUR1","match_date":"2026-11-05",
                    "home_goals":h,"away_goals":a,"result":"H" if h>a else "D" if h==a else "A"})
        self.f=forecast()
        self.f["data"]["snapshot_sha256"]=hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.f["data"]["league_history_rows"]=150
        self.f["payload_sha256"]=_digest({k:v for k,v in self.f.items() if k!="payload_sha256"})
    def test_end_to_end(self):
        b=produce(self.f,self.path,now=__import__("datetime").datetime(2026,11,6,16,0,tzinfo=__import__("datetime").timezone.utc))
        out=connect_verified_baseline(self.f,lock(),b)
        self.assertFalse(out["betting_authorized"])
        self.assertEqual(out["pilot_count_increment"],0)
        self.assertEqual(b["historical_match_count"],150)
        self.assertAlmostEqual(sum(b["markets"][m] for m in ("MS1","MSX","MS2")),1)
    def test_true_calculation_time_recorded(self):
        from datetime import datetime, timezone
        t=datetime(2026,11,6,16,2,tzinfo=timezone.utc)
        b=produce(self.f,self.path,now=t)
        self.assertEqual(b["created_at_utc"],t.isoformat())
        self.assertEqual(b["forecast_created_at_utc"],self.f["created_at_utc"])
        self.assertFalse(connect_verified_baseline(self.f,lock(),b)["betting_authorized"])

    def test_after_kickoff_and_late_reconstruction_blocked(self):
        from datetime import datetime, timezone
        for t in (datetime(2026,11,6,17,0,tzinfo=timezone.utc),
                  datetime(2026,11,6,16,11,tzinfo=timezone.utc)):
            with self.subTest(at=t.isoformat()):
                with self.assertRaisesRegex(ValueError,"BASELINE_NOT_CALCULATED_PRE_KICKOFF"):
                    produce(self.f,self.path,now=t)

    def test_result_on_forecast_day_without_time_proof_blocked(self):
        from datetime import datetime, timezone
        self.f["created_at_utc"]="2026-11-05T16:00:00+00:00"
        self.f["payload_sha256"]=_digest({k:v for k,v in self.f.items() if k!="payload_sha256"})
        with self.assertRaisesRegex(ValueError,"RESULT_NOT_PRIOR_TO_FORECAST_DATE"):
            produce(self.f,self.path,now=datetime(2026,11,5,16,2,tzinfo=timezone.utc))

    def test_future_results_block(self):
        with self.path.open("a") as f:f.write("new,TUR1,2026-11-06,1,0,H\n")
        self.f["data"]["snapshot_sha256"]=hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.f["payload_sha256"]=_digest({k:v for k,v in self.f.items() if k!="payload_sha256"})
        with self.assertRaisesRegex(ValueError,"FUTURE_LEAGUE_RESULTS"):
            produce(self.f,self.path,now=__import__("datetime").datetime(2026,11,6,16,0,tzinfo=__import__("datetime").timezone.utc))
    def test_wrong_history_hash(self):
        with self.path.open("a") as f:f.write("new,TUR1,2026-11-05,1,0,H\n")
        with self.assertRaisesRegex(ValueError,"HISTORY_SHA"):
            produce(self.f,self.path,now=__import__("datetime").datetime(2026,11,6,16,0,tzinfo=__import__("datetime").timezone.utc))
if __name__=="__main__":unittest.main()
