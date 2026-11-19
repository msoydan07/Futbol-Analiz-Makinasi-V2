"""Synthetic research-only acceptance tests. No real external network or betting."""
from __future__ import annotations
import copy
import unittest
from datetime import date
from private_4618_matchday_preflight_263 import (
    BASE_COUNT,EXTRA,LEAGUES,GateBlocked,inspect_official_interval,validate_rows,
)
NOW='2026-11-19T14:00:00+00:00'

def window(league,start,end,*,matches=None,**updates):
    x={'schema':'263_official_result_window_v1','league':league,
       'coverage_start':start,'coverage_end':end,
       'source_url':'https://www.premierleague.com/en/fixtures',
       'observed_at_utc':'2026-11-19T13:30:00+00:00',
       'coverage_claim':'COMPLETE_RESULTS_AND_RESCHEDULED_FIXTURES',
       'matches': [] if matches is None else matches}
    x.update(updates)
    return x

class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fields=('fixture_id','league','season','match_date','home_id','away_id',
                'home_goals','away_goals','result','source_row','source_url')
        rows=[]
        leagues=sorted(LEAGUES)
        for i in range(BASE_COUNT+EXTRA):
            old=i<BASE_COUNT
            rows.append({'fixture_id':'fixture-%04d'%i,'league':leagues[i%10],
                 'season':'2025-2026' if old else '2026-2027',
                 'match_date':'2025-11-08' if old else '2026-11-08',
                 'home_id':'h-%04d'%i,'away_id':'a-%04d'%i,
                 'home_goals':'1','away_goals':'0','result':'H',
                 'source_row':'2' if old else 'PRIVATE_FROZEN_4618_SCORE_ONLY_RESEARCH_NOT_OFFICIAL_ACCEPTANCE',
                 'source_url':'https://www.football-data.co.uk/example.csv' if old else 'https://xgedge.com/example'})
        cls.rows=rows;cls.fields=fields

    def test_01_pinned_schema_4413_plus_205(self):
        latest=validate_rows(self.fields,self.rows[:BASE_COUNT],self.rows)
        self.assertEqual(len(latest),10)
        self.assertEqual(latest['ENG1'],date(2026,11,8))

    def test_02_original_record_changed_rejected(self):
        rows=copy.deepcopy(self.rows);rows[0]['home_goals']='3'
        with self.assertRaisesRegex(GateBlocked,'BASE_4413'):
            validate_rows(self.fields,self.rows[:BASE_COUNT],rows)

    def test_03_same_match_duplicate_rejected(self):
        rows=copy.deepcopy(self.rows);rows[-1]['fixture_id']=rows[-2]['fixture_id']
        with self.assertRaisesRegex(GateBlocked,'DUPLICATE'):
            validate_rows(self.fields,self.rows[:BASE_COUNT],rows)

    def test_04_private_xg_column_rejected(self):
        with self.assertRaisesRegex(GateBlocked,'PRIVATE_XG'):
            validate_rows(self.fields+('home_xg',),self.rows[:BASE_COUNT],self.rows)

    def test_05_wrong_score_label_rejected(self):
        rows=copy.deepcopy(self.rows);rows[-1]['result']='D'
        with self.assertRaisesRegex(GateBlocked,'RESULT_SCORE'):
            validate_rows(self.fields,self.rows[:BASE_COUNT],rows)

    def test_06_no_official_adapter_blocks(self):
        with self.assertRaisesRegex(GateBlocked,'ADAPTER_NOT_PROVIDED'):
            inspect_official_interval(league='ENG1',last_result_day='2026-11-08',
                  target_day='2026-11-19',now_utc=NOW,fetch_official_window=None)

    def test_07_international_break_empty_interval_candidate_not_prod(self):
        x=inspect_official_interval(league='ENG1',last_result_day='2026-11-08',
                  target_day='2026-11-19',now_utc=NOW,fetch_official_window=window)
        self.assertEqual(x['age_days'],11)
        self.assertTrue(x['can_study_frozen_snapshot'])
        self.assertFalse(x['production_forecast_allowed'])
        self.assertFalse(x['calendar_verified_by_code'])

    def test_08_any_unarchived_completed_match_blocks(self):
        fixture={'match_date':'2026-11-14','home_id':'h','away_id':'a','status':'FULL_TIME'}
        def fetch(league,start,end):return window(league,start,end,matches=[fixture])
        x=inspect_official_interval(league='ENG1',last_result_day='2026-11-08',
            target_day='2026-11-19',now_utc=NOW,fetch_official_window=fetch)
        self.assertEqual(x['status'],'BLOCKED_NEW_COMPLETED_MATCH_MISSING')
        self.assertFalse(x['can_study_frozen_snapshot'])

    def test_09_postponed_not_fake_completed(self):
        fixture={'match_date':'2026-11-14','home_id':'h','away_id':'a','status':'POSTPONED'}
        def fetch(league,start,end):return window(league,start,end,matches=[fixture])
        x=inspect_official_interval(league='ENG1',last_result_day='2026-11-08',
            target_day='2026-11-19',now_utc=NOW,fetch_official_window=fetch)
        self.assertTrue(x['can_study_frozen_snapshot'])

    def test_10_incomplete_interval_rejected(self):
        def fetch(league,start,end):return window(league,start,'2026-11-17')
        with self.assertRaisesRegex(GateBlocked,'INCOMPLETE'):
            inspect_official_interval(league='ENG1',last_result_day='2026-11-08',
                target_day='2026-11-19',now_utc=NOW,fetch_official_window=fetch)

    def test_11_wrong_official_host_rejected(self):
        def fetch(league,start,end):return window(league,start,end,source_url='https://example.com/fake')
        with self.assertRaisesRegex(GateBlocked,'UNRECOGNIZED'):
            inspect_official_interval(league='ENG1',last_result_day='2026-11-08',
                target_day='2026-11-19',now_utc=NOW,fetch_official_window=fetch)

    def test_12_stale_window_observation_rejected(self):
        def fetch(league,start,end):return window(league,start,end,observed_at_utc='2026-11-16T10:00:00+00:00')
        with self.assertRaisesRegex(GateBlocked,'STALE'):
            inspect_official_interval(league='ENG1',last_result_day='2026-11-08',
                target_day='2026-11-19',now_utc=NOW,fetch_official_window=fetch)

    def test_13_future_target_day_denied(self):
        with self.assertRaisesRegex(GateBlocked,'FUTURE_DAY'):
            inspect_official_interval(league='ENG1',last_result_day='2026-11-08',
                target_day='2026-11-20',now_utc=NOW,fetch_official_window=window)

    def test_14_coverage_must_claim_complete(self):
        def fetch(league,start,end):return window(league,start,end,coverage_claim='PARTIAL_WEEK_ONLY')
        with self.assertRaisesRegex(GateBlocked,'COVERAGE'):
            inspect_official_interval(league='ENG1',last_result_day='2026-11-08',
                target_day='2026-11-19',now_utc=NOW,fetch_official_window=fetch)

    def test_15_duplicate_fixture_in_window_rejected(self):
        fixture={'match_date':'2026-11-14','home_id':'h','away_id':'a','status':'POSTPONED'}
        def fetch(league,start,end):return window(league,start,end,matches=[fixture,fixture])
        with self.assertRaisesRegex(GateBlocked,'DUPLICATE_FIXTURE'):
            inspect_official_interval(league='ENG1',last_result_day='2026-11-08',
                target_day='2026-11-19',now_utc=NOW,fetch_official_window=fetch)

if __name__=='__main__':unittest.main(verbosity=2)
