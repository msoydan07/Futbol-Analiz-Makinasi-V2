"""Read-only evidence linkage tests; no rebacktest or live forecast."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from verified_xg_context_263 import load_audited_xg, descriptive_xg_asof, XGContextError
from operational_report_263 import build_operational_offline_bundle
from test_analysis_math_core import synthetic_rows
from quality_gate_263 import locked_evidence

HERE=Path(__file__).resolve().parent

class VerifiedXGReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)/'historical_verified_xg.csv'
        self.historical=[{'fixture_id':'f1','league':'ENG1','season':'2026-2027','match_date':'2026-10-01',
                          'home_id':'H','away_id':'A','home_goals':'2','away_goals':'1'},
                         {'fixture_id':'f2','league':'ENG1','season':'2026-2027','match_date':'2026-10-11',
                          'home_id':'H','away_id':'A','home_goals':'0','away_goals':'0'},
                         {'fixture_id':'f3','league':'ENG1','season':'2026-2027','match_date':'2026-10-20',
                          'home_id':'A','away_id':'H','home_goals':'1','away_goals':'1'}]
        self.xg=[{**{k:r[k] for k in ('fixture_id','league','season','match_date','home_id','away_id','home_goals','away_goals')},
                 'home_xg':v[0],'away_xg':v[1],
                 'understat_source_url':'https://understat.com/match/'+str(i)} for i,(r,v) in enumerate(zip(self.historical,[('1.5','0.8'),('0.8','0.4'),('1.2','0.9')]),1)]
        self.audit={'verified_xg_rows':3,'historical_rows':3,'prediction_engine_modified':False,
                    'prediction_asof_rule':'match_date strictly earlier than target match_date'}
        self.case={'league':'ENG1','season':'2026-2027','previous_season':'2025-2026',
                   'target_date':'2026-10-20','home_id':'H','away_id':'A'}

    def write_and_load(self):
        with self.p.open('w',encoding='utf-8',newline='') as f:
            wr=csv.DictWriter(f,fieldnames=list(self.xg[0]));wr.writeheader();wr.writerows(self.xg)
        return load_audited_xg(self.p,self.audit,self.historical)

    def test_valid_complete_join_and_provenance_labels(self):
        rows,info=self.write_and_load()
        self.assertEqual(len(rows),3)
        self.assertEqual(info['rows'],3)
        self.assertFalse(info['model_xg_promoted'])
        self.assertIn('NOT_LIVE_REVERIFIED',info['status'])

    def test_excludes_current_day_and_newer(self):
        rows,info=self.write_and_load()
        c=descriptive_xg_asof(rows,self.case,info)
        self.assertEqual(c['prior_league_matches_with_xg'],2)
        self.assertEqual(c['latest_prior_observation_date'],'2026-10-11')
        self.assertEqual(c['home']['venue_matches_with_xg'],2)
        self.assertEqual(c['away']['venue_matches_with_xg'],2)
        self.assertAlmostEqual(c['home']['mean_xg_for'],1.15)
        self.assertFalse(c['used_as_lambda_multiplier'])

    def test_no_data_for_other_league(self):
        rows,info=self.write_and_load()
        c=descriptive_xg_asof(rows,dict(self.case,league='TUR1'),info)
        self.assertEqual(c['status'],'NO_PRIOR_AUDITED_XG_FOR_LEAGUE')
        self.assertEqual(c['home']['venue_matches_with_xg'],0)

    def test_missing_fixture_identity_rejected(self):
        self.xg[0]['fixture_id']='fake'
        with self.assertRaisesRegex(XGContextError,'fixture_not_in_history'):self.write_and_load()

    def test_wrong_match_direction_rejected(self):
        self.xg[0]['home_id']='A';self.xg[0]['away_id']='H'
        with self.assertRaisesRegex(XGContextError,'identity_mismatch'):self.write_and_load()

    def test_score_mismatch_rejected(self):
        self.xg[0]['home_goals']='3'
        with self.assertRaisesRegex(XGContextError,'identity_mismatch'):self.write_and_load()

    def test_duplicate_xg_fixture_rejected(self):
        self.xg[2]['fixture_id']='f1'
        with self.assertRaisesRegex(XGContextError,'duplicate_xg'):self.write_and_load()

    def test_outside_allowed_xg_leagues_rejected(self):
        self.xg[0]['league']='TUR1'
        with self.assertRaisesRegex(XGContextError,'unverified_xg_league'):self.write_and_load()

    def test_invalid_nonfinite_xg_rejected(self):
        for v in ['nan','inf','-2','999','bad']:
            with self.subTest(v=v):
                self.xg[0]['home_xg']=v
                with self.assertRaisesRegex(XGContextError,'invalid_xg'):self.write_and_load()

    def test_unofficial_or_insecure_source_rejected(self):
        for v in ['http://understat.com/match/1','https://understat.com.evil.test/match/1',
                  'https://example.org/match/1','https://bad@understat.com/match/1','https://understat.com:invalid/match/1']:
            with self.subTest(url=v):
                self.xg[0]['understat_source_url']=v
                with self.assertRaisesRegex(XGContextError,'xg_source_not'):self.write_and_load()

    def test_audit_wrong_count_rejected(self):
        self.audit['verified_xg_rows']=2155
        with self.assertRaisesRegex(XGContextError,'audit_count_mismatch'):self.write_and_load()

    def test_unverified_asof_rule_rejected(self):
        self.audit['prediction_asof_rule']='same day can be included'
        with self.assertRaisesRegex(XGContextError,'asof_rule'):self.write_and_load()

    def test_report_bridge_is_descriptive_and_does_not_change_probabilities(self):
        rows=synthetic_rows(120)
        source={'sha256':'SYNTHETIC_ONLY','rows':len(rows),'market_quarantine':{}}
        evidence=locked_evidence(HERE/'evidence'/'acceptance_263.json')
        case={'league':'SYN','season':'S2','previous_season':'S1',
              'target_date':'2025-11-18','home_id':'T0','away_id':'T1'}
        base=build_operational_offline_bundle(rows,source,evidence,[case],require_locked_source=False)
        with_xg=build_operational_offline_bundle(rows,source,evidence,[case],require_locked_source=False,
                xg_rows=[],xg_info={'status':'AUDIT_FILE_AND_HISTORY_IDENTITY_MATCHED_NOT_LIVE_REVERIFIED'})
        for k in ('model_b_existing','model_arbitration','probability_ranking','analysis'):
            self.assertEqual(base['cases'][0][k],with_xg['cases'][0][k])
        self.assertEqual(base['cases'][0]['descriptive_xg']['status'],'AUDITED_XG_FILE_NOT_PROVIDED')
        self.assertEqual(with_xg['cases'][0]['descriptive_xg']['status'],'NO_PRIOR_AUDITED_XG_FOR_LEAGUE')
        self.assertFalse(with_xg['cases'][0]['descriptive_xg']['used_as_lambda_multiplier'])
        self.assertEqual(with_xg['recommendations'],[])

if __name__=='__main__':unittest.main()
