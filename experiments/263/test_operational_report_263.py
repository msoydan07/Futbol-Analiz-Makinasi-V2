"""Only software invariants; NO model performance rerun or real forecast."""
import json
import copy
import unittest
from pathlib import Path
from test_analysis_math_core import synthetic_rows
from quality_gate_263 import locked_evidence
from operational_report_263 import (build_operational_offline_bundle, named_cases,
                                   _reference_model_b, _ranking, OperationalError,
                                   render_operational_markdown)

HERE=Path(__file__).resolve().parent

class OperationalCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=synthetic_rows(140)
        cls.source={'sha256':'SYNTHETIC_ONLY','rows':len(cls.rows),'market_quarantine':{}}
        cls.evidence=locked_evidence(HERE/'evidence'/'acceptance_263.json')
        cls.case={'league':'SYN','season':'S2','previous_season':'S1',
                  'target_date':'2025-11-18','home_id':'T0','away_id':'T1'}
        cls.bundle=build_operational_offline_bundle(cls.rows,cls.source,cls.evidence,
                                                    [cls.case],require_locked_source=False)

    def test_model_b_is_a_separate_existing_comparator(self):
        b=self.bundle['cases'][0]['model_b_existing']
        self.assertEqual(b['status'],'CALCULATED_EXISTING_B_NOT_263_CANONICAL')
        self.assertEqual(b['parameters'],{'window':20,'shrink':5})
        self.assertAlmostEqual(sum(b['probabilities'][k] for k in ('MS1','MSX','MS2')),1,places=8)
        self.assertFalse(b['recommended'])

    def test_c2_is_only_canonical_when_calculated(self):
        e=self.bundle['cases'][0]
        self.assertEqual(e['model_arbitration']['canonical_primary'],
                         'C2' if 'C2' in e['analysis']['model_outputs'] else None)
        self.assertFalse(e['model_arbitration']['automatic_fallback_promoted'])
        self.assertEqual(e['model_arbitration']['c3_status'],'SEPARATE_EXPERIMENT_ONLY')

    def test_ranked_probabilities_are_not_a_betting_pick(self):
        e=self.bundle['cases'][0]
        rank=e['probability_ranking']
        self.assertFalse(rank['recommended'])
        self.assertEqual(rank['rows'],sorted(rank['rows'],key=lambda x:(-x['probability'],x['market'])))
        self.assertEqual(self.bundle['recommendations'],[])
        self.assertIsNone(self.bundle['odds_EV'])

    def test_when_canonical_absent_never_auto_promote_existing_b(self):
        b=self.bundle['cases'][0]['model_b_existing']
        out=_ranking(None,b)
        self.assertIn('EXPLORATORY_ONLY_C2_MISSING',out['model'])
        self.assertFalse(out['recommended'])

    def test_missing_history_model_b_reports_no_number(self):
        tiny=[r for r in self.rows if r['match_date'] < '2025-04-10']
        b=_reference_model_b(tiny,self.case)
        self.assertEqual(b['status'],'NOT_AVAILABLE_INSUFFICIENT_HISTORY')
        self.assertIsNone(b['probabilities'])

    def test_same_day_target_outcomes_have_no_effect(self):
        e=self.bundle['cases'][0]
        before=e['model_b_existing']['probabilities']
        altered=copy.deepcopy(self.rows)
        for r in altered:
            if r['match_date']>=self.case['target_date']:
                r['home_goals']='99';r['away_goals']='1'
        b=_reference_model_b(altered,self.case)
        self.assertEqual(before,b['probabilities'])

    def test_modifying_unlocked_snapshot_rejected_in_production_mode(self):
        with self.assertRaisesRegex(OperationalError,'Historical snapshot changed'):
            build_operational_offline_bundle(self.rows,self.source,self.evidence,
                                             [self.case],require_locked_source=True)

    def test_17_sections_kept_and_no_false_completeness(self):
        self.assertEqual(len(self.bundle['sections']),17)
        self.assertTrue(self.bundle['does_not_claim_live_readiness'])
        self.assertFalse(self.bundle['production_changed'])
        self.assertFalse(self.bundle['real_fixture_verified'])
        self.assertIn('Gerçek maç doğrulaması',render_operational_markdown(self.bundle))

    def test_descriptive_form_has_no_lambda_adjustment(self):
        e=self.bundle['cases'][0]
        for v in e['descriptive_form'].values():
            self.assertFalse(v['used_as_lambda_multiplier'])
            self.assertEqual(v['wins']+v['draws']+v['losses'],v['last_5_current_season_matches'])
        self.assertEqual(e['external_factors']['verified_external_lambda_adjustments'],0)

    def test_named_case_league_membership_and_user_names(self):
        requests=[{'home':'Bayern Münih','away':'B. Dortmund','league':'GER1','target_date':'2026-10-30'},
                  {'home':'PSG','away':'Marsilya','league':'FRA1','target_date':'2026-10-30'}]
        r=named_cases(HERE/'evidence/identity_index_263.json',HERE/'mackolik_reviewed_aliases.csv',requests)
        self.assertEqual(len(r),2)
        self.assertEqual([x['league'] for x in r],['GER1','FRA1'])

    def test_unknown_team_is_not_fuzzy_matched(self):
        with self.assertRaisesRegex(OperationalError,'Identity unresolved'):
            named_cases(HERE/'evidence/identity_index_263.json',HERE/'mackolik_reviewed_aliases.csv',
                        [{'home':'FC NOTEXIST','away':'B. Dortmund','league':'GER1','target_date':'2026-10-30'}])

    def test_unsafe_score_row_cannot_generate_probability(self):
        from operational_report_263 import _safe_probability
        for v in (float('nan'),float('inf'),-0.1,1.1,True):
            with self.subTest(v=v),self.assertRaises(OperationalError):_safe_probability(v)

if __name__=='__main__':unittest.main()
