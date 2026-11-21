import csv
import tempfile
import unittest
from pathlib import Path
from p1_historical_intake import inspect, review_manifest

class TestHistoricalIntake(unittest.TestCase):
    def setUp(self):
        self.meta = dict(source_name='SYNTHETIC_CASE', source_url='https://example.org/terms',
                         research_use_authorized=True,rights_basis='Synthetic data from local unit tests',
                         bookmaker='SYNTHETIC_NOT_IDDAA',price_phase='OPENING')
        self.row = dict(league='ENG1',match_date='2025-08-20',
                  kickoff_utc='2025-08-20T20:00:00+00:00',
                  observed_at_utc='2025-08-20T10:00:00+00:00',
                  home='Test home',away='Test away',
                  MS1='2.10',MSX='3.20',MS2='3.50',
                  BTTS_YES='1.70',BTTS_NO='2.00',
                  FTHG='2',FTAG='1',result_source='https://example.org/final')
        self.row['UNDER_2.5']='1.80'
        self.row['OVER_2.5']='1.90'

    def run_one(self,row):
        with tempfile.TemporaryDirectory() as root:
            source=Path(root)/'test.csv'
            with source.open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,list(self.row))
                writer.writeheader()
                writer.writerow(row)
            return inspect(source,self.meta)

    def test_complete_row(self):
        self.assertEqual(self.run_one(self.row)['n_accepted'],1)
    def test_missing_user_rights(self):
        with self.assertRaises(ValueError):
            review_manifest(dict(self.meta,research_use_authorized=False))
    def test_after_kickoff(self):
        x=self.run_one(dict(self.row,observed_at_utc='2025-08-20T22:00:00+00:00'))
        self.assertEqual(x['n_rejected'],1)
    def test_missing_market(self):
        x=self.run_one(dict(self.row,BTTS_NO=''))
        self.assertEqual(x['n_rejected'],1)
    def test_untimed_opening(self):
        x=self.run_one(dict(self.row,observed_at_utc=''))
        self.assertIn('UNTIMESTAMPED',x['accepted'][0]['time_grade'])
    def test_result_source_missing(self):
        x=self.run_one(dict(self.row,result_source=''))
        self.assertEqual(x['n_rejected'],1)

if __name__=='__main__':
    unittest.main()
