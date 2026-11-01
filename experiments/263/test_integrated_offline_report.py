"""Integration tests are deliberately synthetic; no backtests rerun."""
import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from analysis_math_core import build_analysis
from test_analysis_math_core import synthetic_rows
from quality_gate_263 import locked_evidence, HISTORICAL_SHA256, QualityGateError
from integrated_offline_report import (
    SECTIONS, IntegratedReportError, build_offline_bundle,
    render_bundle_markdown, _check_cases,
)

HERE=Path(__file__).resolve().parent

class Combined263Suite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=synthetic_rows(120)
        cls.source={'sha256':'SYNTHETIC_ONLY','rows':len(cls.rows),'market_quarantine':{}}
        cls.evidence=locked_evidence(HERE/'evidence'/'acceptance_263.json')
        cls.case={'league':'SYN','season':'S2','previous_season':'S1','target_date':'2025-11-18','home_id':'T0','away_id':'T1'}
        cls.bundle=build_offline_bundle(cls.rows,cls.source,cls.evidence,[cls.case],require_locked_source=False)

    def test_chain_produces_no_recommendation(self):
        b=self.bundle
        self.assertTrue(b['not_live_match_analysis'])
        self.assertFalse(b['real_fixture_verified'])
        self.assertEqual(b['recommendations'],[])
        for c in b['cases']:
            self.assertEqual(c['quality']['recommendations'],[])
            self.assertTrue(all(x['can_recommend'] is False for x in c['quality']['markets']))

    def test_exactly_17_sections_and_not_full(self):
        self.assertEqual(len(self.bundle['sections']),17)
        self.assertFalse(any(s['status']=='TAMAMLANDI' for s in self.bundle['sections']))
        self.assertEqual(self.bundle['sections'][-1]['status'],'SONRA')

    def test_c3_does_not_replace_missing_c2(self):
        c=copy.deepcopy(self.case)
        c['home_id']='T0'
        b=build_offline_bundle(self.rows,self.source,self.evidence,[c],require_locked_source=False)
        self.assertIn('C3', b['cases'][0]['quality']['model_coverage'])
        self.assertEqual(b['cases'][0]['quality']['recommendations'],[])

    def test_document_explicitly_distinguishes_calculation_from_proof(self):
        md=render_bundle_markdown(self.bundle)
        self.assertIn('GERÇEK MAÇ TAHMİNİ DEĞİLDİR',md)
        self.assertIn('TAM UYUM YOK',md)
        self.assertIn('KISMI',md)
        self.assertIn('HAYIR',md)
        self.assertNotIn('ÖNERİ: KG',md)

    def test_duplicate_cases_rejected(self):
        with self.assertRaisesRegex(IntegratedReportError,'Duplicate case'):
            _check_cases([self.case,self.case])

    def test_unknown_team_rejected(self):
        c={**self.case, 'home_id':'NONEXISTENT'}
        with self.assertRaisesRegex(IntegratedReportError,'Unknown team'):
            build_offline_bundle(self.rows,self.source,self.evidence,[c],require_locked_source=False)

    def test_future_rows_do_not_affect_results(self):
        modified=copy.deepcopy(self.rows)
        for r in modified:
            if r['match_date']>=self.case['target_date']:
                r.update({'home_goals':'888','away_goals':'777','home_corners':'99'})
        outcome=build_offline_bundle(modified,self.source,self.evidence,[self.case],require_locked_source=False)
        self.assertEqual(outcome,self.bundle)

    def test_wrong_history_sha_fails_closed(self):
        with self.assertRaisesRegex(IntegratedReportError,'SHA-256 mismatch'):
            build_offline_bundle(self.rows,self.source,self.evidence,[self.case])

    def test_corrupt_evidence_is_rejected(self):
        fake=copy.deepcopy(self.evidence)
        fake['coverage']['target_matches']=42
        with self.assertRaisesRegex(IntegratedReportError,'Acceptance'):
            build_offline_bundle(self.rows,self.source,fake,[self.case],require_locked_source=False)

    def test_invalid_live_flag_cannot_be_input(self):
        with self.assertRaises(IntegratedReportError):
            _check_cases([{**self.case,'fixture_verified':True}])

    def test_many_case_mode(self):
        second={**self.case,'home_id':'T2','away_id':'T3'}
        b=build_offline_bundle(self.rows,self.source,self.evidence,[self.case,second],require_locked_source=False)
        self.assertEqual(len(b['cases']),2)
        self.assertEqual(len(b['sections']),17)

if __name__=='__main__':unittest.main()
