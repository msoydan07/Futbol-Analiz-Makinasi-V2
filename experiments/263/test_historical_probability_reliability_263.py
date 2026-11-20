import unittest
# Regression is intentionally synthetic; it is not empirical performance evidence.
from datetime import datetime,timedelta,timezone
from historical_probability_reliability_263 import similar,rank_candidates

NOW="2026-11-20T14:00:00+00:00"
def record(i,p=.58,occurred=True,market="UNDER_2.5",league="ESP1"):
    return {"fixture_id":str(i),"league":league,"market":market,
            "model_probability":p,"occurred":occurred,
            "forecast_created_at_utc":"2026-10-01T10:00:00+00:00",
            "kickoff_utc":"2026-10-01T18:00:00+00:00",
            "result_known_at_utc":"2026-10-01T21:00:00+00:00",
            "forecast_origin":"SEALED_BEFORE_KICKOFF",
            "forecast_sha256":format(i,"064x")}

class ReliabilityTests(unittest.TestCase):
    def test_bilbao_58_percent_uses_historical_success_not_60_cutoff(self):
        rows=[record(i,occurred=i<15) for i in range(25)]
        e=similar(rows,league="ESP1",market="UNDER_2.5",
                  probability=.5813,asof=NOW)
        self.assertEqual(e["n"],25)
        self.assertEqual(e["wins"],15)
        self.assertEqual(e["observed_hit_rate"],.6)
        self.assertGreater(e["wilson_lower95"],0)
        self.assertEqual(rank_candidates([{"market":"UNDER_2.5",
                   "calibrated_probability":.5813}],rows,
                   league="ESP1",asof=NOW)[0]["decision_evidence_status"],
                   "HISTORICALLY_EVALUATED")
    def test_sparse_evidence_is_unknown_not_false_success(self):
        e=similar([record(1)],league="ESP1",market="UNDER_2.5",
                  probability=.5813,asof=NOW)
        self.assertIsNone(e["observed_hit_rate"])
        self.assertEqual(e["status"],"INSUFFICIENT_HISTORICAL_PREMATCH_EVIDENCE")
    def test_future_result_rejected(self):
        r=record(1);r["result_known_at_utc"]="2026-11-21T00:00:00+00:00"
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_RETROACTIVE"):
            similar([r],league="ESP1",market="UNDER_2.5",probability=.58,asof=NOW)
    def test_post_kickoff_forecast_rejected(self):
        r=record(1);r["forecast_created_at_utc"]="2026-10-01T19:00:00+00:00"
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_RETROACTIVE"):
            similar([r],league="ESP1",market="UNDER_2.5",probability=.58,asof=NOW)
    def test_duplicate_match_rejected(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            similar([record(1),record(1)],league="ESP1",
                    market="UNDER_2.5",probability=.58,asof=NOW)
    def test_no_score_only_backfill(self):
        r=record(1);r.pop("forecast_sha256")
        with self.assertRaisesRegex(ValueError,"PREMATCH_FORECAST_SHA_REQUIRED"):
            similar([r],league="ESP1",market="UNDER_2.5",probability=.58,asof=NOW)
    def test_market_and_league_separate(self):
        rows=[record(i) for i in range(30)]
        self.assertEqual(similar(rows,league="GER1",market="UNDER_2.5",
            probability=.58,asof=NOW)["n"],0)
        self.assertEqual(similar(rows,league="ESP1",market="BTTS_NO",
            probability=.58,asof=NOW)["n"],0)

if __name__=="__main__":unittest.main()
