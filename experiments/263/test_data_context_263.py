"""Only synthetic data integrity tests; do not rerun historical performance experiments."""
import copy
import unittest
from data_context_263 import build_data_context, DataContextError

class DataContextSuite(unittest.TestCase):
    def setUp(self):
        self.case = dict(league='ENG1', season='2026-2027',previous_season='2025-2026',
                         target_date='2026-11-01',home_id='H',away_id='A')
        self.base={'league':'ENG1','season':'2026-2027','match_date':'2026-10-25',
                   'home_id':'H','away_id':'C','home_goals':'2','away_goals':'1',
                   'half_time_home_goals':'1','half_time_away_goals':'0',
                   'home_corners':'4','away_corners':'5','home_shots':'9','away_shots':'7',
                   'home_shots_on_target':'4','away_shots_on_target':'3',
                   'source_url':'https://www.football-data.co.uk/2627/E0.csv'}
        self.rows=[self.base,dict(self.base,home_id='D',away_id='A',match_date='2026-10-26'),
                   dict(self.base,season='2025-2026',match_date='2025-10-26')]
        self.source={'sha256':'fixture-snapshot','rows':len(self.rows)}
    def build(self,rows=None):
        rows=self.rows if rows is None else rows
        return build_data_context(rows, {'sha256':'fixture-snapshot','rows':len(rows)},self.case)
    def test_contexts_seasons_and_cutoff(self):
        x=self.build()
        self.assertEqual(x['eligible_league_games'],{'current_season':2,'previous_season':1})
        self.assertEqual(x['team_context']['home']['current_home'],1)
        self.assertEqual(x['team_context']['away']['current_away'],1)
    def test_future_and_same_day_result_invariance(self):
        bad=copy.deepcopy(self.base)
        bad.update(match_date='2026-11-01', home_goals='99',away_goals='99')
        future=copy.deepcopy(bad);future['match_date']='2026-11-10'
        first=self.build(); later=self.build(self.rows+[bad,future])
        for k in ('eligible_league_games','team_context','current_season_market_coverage','last_historical_result_dates','review_flags'):
            self.assertEqual(first[k],later[k])
    def test_other_league_and_season_excluded(self):
        irrelevant=dict(self.base,league='ITA1',home_goals='100')
        irrelevant2=dict(self.base,season='2024-2025')
        first=self.build(); later=self.build(self.rows+[irrelevant,irrelevant2])
        for k in ('eligible_league_games','team_context','current_season_market_coverage','last_historical_result_dates','review_flags'):
            self.assertEqual(first[k],later[k])
    def test_source_url_not_official_verification(self):
        r=self.build()
        self.assertEqual(r['official_match_fixture']['status'],'NOT_CHECKED')
        self.assertFalse(r['provenance']['historical_source_references_verified_online_now'])
        self.assertEqual(r['provenance']['historical_source_references'],{'football-data.co.uk':3})
    def test_missing_lineup_is_not_mislabeled_unpublished(self):
        r=self.build()
        self.assertEqual(r['official_lineups']['status'],'NOT_CHECKED')
        self.assertFalse(r['recommendation_eligible'])
    def test_cannot_make_four_match_context_out_of_two(self):
        self.assertIn('C2_CURRENT_VENUE_SAMPLE_LT_4',self.build()['review_flags'])
    def test_bad_shot_quarantine_only_coverage(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['home_shots_on_target']='30'
        r=self.build(rows)
        self.assertEqual(r['current_season_market_coverage']['shots']['usable'],1)
        self.assertEqual(r['current_season_market_coverage']['final_goals']['usable'],2)
        self.assertIn('SHOT_DATA_PARTIAL',r['review_flags'])
    def test_no_xg_in_original_snapshot(self):
        x=self.build()
        self.assertEqual(x['current_season_market_coverage']['xg']['usable'],0)
        self.assertEqual(x['verified_external_xg_join']['status'],'NOT_CONNECTED')
    def test_report_does_not_claim_outdated_or_missing_fixtures(self):
        self.case['target_date']='2026-11-16'
        x=self.build()
        self.assertIn('lag_to_target_date_days_not_proof_of_missing_games',x)
        self.assertIn('RECENT_RESULTS_REQUIRE_OFFICIAL_CROSSCHECK',x['review_flags'])
    def test_identity_count_hash_requirements(self):
        with self.assertRaises(DataContextError):
            build_data_context(self.rows, {'rows':1,'sha256':'x'},self.case)
        with self.assertRaises(DataContextError):
            build_data_context(self.rows, {'rows':3},self.case)
    def test_missing_or_malformed_url_never_verified(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['source_url']='http://football-data.co.uk/test.csv'
        r=self.build(rows)
        self.assertIn('SOURCE_URL_MISSING_OR_INVALID',r['review_flags'])
        self.assertEqual(r['official_match_fixture']['status'],'NOT_CHECKED')
    def test_invalid_case_rejected(self):
        with self.assertRaises(DataContextError):
            build_data_context(self.rows,self.source,{**self.case,'home_id':'A'})
        with self.assertRaises(DataContextError):
            build_data_context(self.rows,self.source,{**self.case,'target_date':'bad'})

if __name__=='__main__':unittest.main()
