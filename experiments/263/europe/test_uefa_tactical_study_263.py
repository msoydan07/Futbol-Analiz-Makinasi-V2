"""Only new UEFA context study guards; retrospective models stay untouched."""
import unittest
from uefa_tactical_study_263 import (
    parse_league_phase,StudyError,reconstruct_pre_match,
    metrics,features,fit,predict
)
CL=b"""= UEFA Champions League 2024/25
\x0a\xe2\x96\xaa League, Matchday 1
  Tue Sep 17 2024
    18:45  FC Alpha (ENG)     v FC Beta (ITA)         2-1 (1-0)
           FC Gamma (ESP)     v FC Delta (GER)        0-0
\x0a\xe2\x96\xaa League, Matchday 2
  Tue Oct 1
    21:00  FC Beta (ITA)      v FC Delta (GER)        1-1 (1-0)
           FC Gamma (ESP)     v FC Alpha (ENG)        4-0 (2-0)
"""
EL=b"""= UEFA Europa League 2024/25
\x0a\xe2\x96\xaa League phase
  Wed Sep 25 2024
    18:45  FC Alpha (ENG)     v FC Beta (ITA)         2-1 (1-0)
  Thu Sep 26
    21:00  FC Gamma (ESP)     v FC Delta (GER)        0-0
  Thu Oct 3
    21:00  FC Beta (ITA)      v FC Alpha (ENG)        1-0 (0-0)
"""
class StudyContract(unittest.TestCase):
    def test_parse_champions_dates_and_matchdays(self):
        x=parse_league_phase(CL,"UEFA_CL","2024-2025")
        self.assertEqual([x[0]["matchday"],x[-1]["matchday"]],[1,2])
        self.assertEqual({r["total_goals"] for r in x},{0,1,2,3,4})
    def test_europa_date_clusters_infer_matchdays_without_future(self):
        x=parse_league_phase(EL,"UEFA_EL","2024-2025")
        self.assertEqual([r["matchday"] for r in x],[1,1,2])
    def test_malformed_football_score_rejected(self):
        b=CL.replace(b"2-1 (1-0)",b"2-X (1-0)")
        with self.assertRaisesRegex(StudyError,"UNPARSED"):parse_league_phase(b,"UEFA_CL","2024-2025")
    def test_loss_metric_requires_matching_predictions(self):
        with self.assertRaisesRegex(StudyError,"INVALID_METRICS"):
            metrics([{"total_goals":2}],[])
    def test_no_real_model_changes_or_betting_logic_in_source(self):
        import inspect,uefa_tactical_study_263 as m
        src=inspect.getsource(m)
        self.assertNotIn("predict_quad_from_verified_gate(",src)
        self.assertNotIn("canonical_c2_lambda(",src)
        self.assertIn("HISTORICAL_EXPERIMENT_NO_PROMOTION",src)
if __name__=="__main__":unittest.main()
