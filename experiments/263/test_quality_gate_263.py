"""Software / integrity tests only. No statistical backtest or real match selection."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
MATH_PATH=HERE if (HERE/'analysis_math_core.py').exists() else HERE.parent/'263_acceptance'
sys.path.insert(0,str(MATH_PATH))
sys.path.insert(0,str(HERE))
from test_analysis_math_core import synthetic_rows
from analysis_math_core import build_analysis
import quality_gate_263 as q

EVIDENCE=(HERE/'evidence'/'acceptance_263.json') if (HERE/'evidence'/'acceptance_263.json').exists() else MATH_PATH/'results'/'acceptance_263.json'

class Quality263Suite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=q.locked_evidence(EVIDENCE)
        cls.rows=synthetic_rows(120)
        cls.source={'sha256':'SYNTHETIC_ONLY','rows':len(cls.rows), 'market_quarantine':{}}
        cls.analysis=build_analysis(cls.rows,cls.source,'SYN','S2','S1','2025-11-18','T0','T1')
        cls.report=q.build_quality_report(cls.analysis,cls.rows,cls.source,cls.evidence)

    def test_decisions_locked_not_recalculated(self):
        self.assertEqual(len(q.EXPECTED_DECISIONS),16)
        self.assertEqual(q.EVIDENCE_SHA256,q._digest(EVIDENCE))
        self.assertFalse(self.report['evidence']['independent_forward_validation'])
        self.assertFalse(self.report['fixture_verified'])

    def test_never_recommend_or_mark_calibrated(self):
        r=self.report
        self.assertEqual(r['recommendations'],[])
        self.assertIsNone(r['best_pick'])
        self.assertIsNone(r['high_probability_alert'])
        self.assertTrue(all(m['can_recommend'] is False and m['calibrated'] is False
                            for m in r['markets']+r['experimental_audit']))

    def test_1x2_teams_c2_and_c3_separate(self):
        c2=[m for m in self.report['markets'] if m['market']=='FT_MS1']
        c3=[m for m in self.report['experimental_audit'] if m['market']=='FT_MS1']
        self.assertEqual(len(c2),1)
        self.assertEqual(len(c3),1)
        self.assertEqual(c2[0]['status'],'KANONIK_HESAPLANDI_AMA_DOGRULANMADI')
        self.assertEqual(c3[0]['status'],'DENEYSEL_RETROSPEKTIF_SINYAL')

    def test_frozen_benchmark_never_approves_goal_totals(self):
        for r in self.report['markets']:
            if r['market'].startswith('FT_OVER_'):
                self.assertNotEqual(r['status'],'DENEYSEL_RETROSPEKTIF_SINYAL')

    def test_halftime_1x2_positive_but_totals_only_league(self):
        for x in ('MS1','MSX','MS2'):
            r=next(m for m in self.report['markets'] if m['market']=='HALF_'+x)
            self.assertEqual(r['status'],'DENEYSEL_RETROSPEKTIF_SINYAL')
        for m in self.report['markets']:
            if m['market'].startswith('HALF_OVER_'):
                self.assertEqual(m['status'],'LIG_REFERANSI_TEK_BASINA')
                self.assertIn('LEAGUE_',m['probability_type'])

    def test_corners_league_only_and_no_first_half_corners(self):
        for m in self.report['markets']:
            if m['market'].startswith('CORN_'):
                self.assertEqual(m['status'],'LIG_REFERANSI_TEK_BASINA')
                self.assertGreaterEqual(m['reference_sample'],40)
        self.assertFalse(any('FIRST_HALF_CORNER' in m['market'] for m in self.report['markets']))
        self.assertIn('FIRST_HALF_CORNERS_EXCLUDED',self.report['omitted'])

    def test_reject_live_or_unverified_cutoff(self):
        v=copy.deepcopy(self.analysis);v['fixture_verified']=True
        with self.assertRaises(q.QualityGateError): q.build_quality_report(v,self.rows,self.source,self.evidence)
        v=copy.deepcopy(self.analysis);v['provenance']['cutoff_exclusive_date']='2025-11-17'
        with self.assertRaises(q.QualityGateError): q.build_quality_report(v,self.rows,self.source,self.evidence)
        v=copy.deepcopy(self.analysis);v['provenance']['sha256']='OTHER'
        with self.assertRaises(q.QualityGateError): q.build_quality_report(v,self.rows,self.source,self.evidence)

    def test_same_day_mutations_cannot_affect_report(self):
        modified=copy.deepcopy(self.rows)
        for r in modified:
            if r['match_date']>=self.analysis['fixture']['target_date']:
                r.update({'home_goals':'999','half_time_home_goals':'999','home_corners':'999'})
        result=q.build_quality_report(self.analysis,modified,self.source,self.evidence)
        self.assertEqual(result,self.report)

    def test_malformed_ft_probabilities_are_quarantined(self):
        v=copy.deepcopy(self.analysis)
        v['model_outputs']['C2']['goals']['markets']['MS1']=1.12
        r=q.build_quality_report(v,self.rows,self.source,self.evidence)
        self.assertEqual(r['model_coverage']['C2'],'KARANTINA')
        self.assertIsNone(next(m['probability'] for m in r['markets'] if m['market']=='FT_ALL'))

    def test_missing_c2_never_fills_from_c3(self):
        v=copy.deepcopy(self.analysis)
        v['model_outputs'].pop('C2',None)
        r=q.build_quality_report(v,self.rows,self.source,self.evidence)
        self.assertEqual(r['model_coverage']['C2'],'VERI_YETERSIZ')
        self.assertIsNone(next(m['probability'] for m in r['markets'] if m['market']=='FT_MS1'))

    def test_inadequate_league_reference_stays_blank(self):
        v=copy.deepcopy(self.rows)
        for r in v:
            r['_ht_usable']=False
        r=q.build_quality_report(self.analysis,v,self.source,self.evidence)
        first=next(x for x in r['markets'] if x['market']=='HALF_OVER_1.5')
        self.assertEqual(first['status'],'VERI_YETERSIZ')
        self.assertIsNone(first['probability'])

    def test_no_over_100pct_or_nonfinite(self):
        for x in (float('nan'),float('inf'),-0.01,1.01,True):
            with self.subTest(x=x):
                with self.assertRaises(q.QualityGateError):q._prob(x)

    def test_tampered_result_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'fake.json'
            obj=copy.deepcopy(self.evidence)
            obj['comparisons'][0]['decision']='PROMOTED'
            p.write_text(json.dumps(obj))
            with self.assertRaisesRegex(q.QualityGateError,'SHA-256 mismatch'):q.locked_evidence(p)

    def test_safe_renderer_explicit_uncertainty(self):
        text=q.render_markdown(self.report)
        self.assertIn('bir maç tahmini veya bahis önerisi değildir',text)
        self.assertIn('HAYIR',text)
        self.assertIn('bağımsız ileri test yok',text)
        self.assertNotIn('ÖNERİ: KG',text)

if __name__=='__main__':unittest.main()
