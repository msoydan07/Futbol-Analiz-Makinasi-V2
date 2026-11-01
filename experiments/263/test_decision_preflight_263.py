"""Only new section 12-14 safety checks; no historical predictive-performance rerun."""
import copy,csv,json,math,unittest
from pathlib import Path
from decision_preflight_263 import evaluate_case,evaluate_bundle,DecisionPreflightError,WATCH_MARKETS
from section_acceptance_263 import audit,SectionAcceptanceError

HERE=Path(__file__).resolve().parent
class DecisionReadinessTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.bundle=json.loads((HERE/'evidence'/'section_contract_sample_263.json').read_text(encoding='utf-8'))
  cls.rows=[{'league':e['identity']['league'],'season':e['identity']['season'],
             'match_date':'2026-10-01','home_goals':'2','away_goals':'1'} for e in cls.bundle['cases']]
  for e in cls.bundle['cases']:e['decision_preflight_263']=evaluate_case(e,cls.rows)
  cls.case=cls.bundle['cases'][0]
 def test_all_section12_preflight_rows_tracked_not_picks(self):
  x=evaluate_case(self.case,self.rows)
  self.assertEqual(tuple(r['market'] for r in x['high_probability_filter']),WATCH_MARKETS)
  self.assertTrue(x['high_probability_filter'])
  self.assertEqual(x['passed_filter'],[])
  self.assertEqual(x['A_B_C_official_candidates'],[])
  self.assertEqual(x['value_selections'],[])
  self.assertIsNone(x['odds_or_EV'])
 def test_canonical_c2_only_no_model_b_fallback(self):
  x=evaluate_case(self.bundle['cases'][1],self.rows)
  self.assertIsNone(x['main_side_descriptive'])
  self.assertEqual(x['high_probability_filter'],[])
  self.assertIsNone(x['canonical_model'])
 def test_main_side_and_general_are_separate(self):
  x=evaluate_case(self.case,self.rows)
  self.assertIn(x['main_side_descriptive']['market'],('MS1','MSX','MS2'))
  self.assertNotIn(x['main_general_descriptive']['market'],('1X','X2','12','OVER_0.5'))
  self.assertEqual(x['main_side_descriptive']['market'],'MS1')
  self.assertEqual(x['main_general_descriptive']['market'],'OVER_1.5')
 def test_at_least_75_is_watch_not_pass(self):
  x=evaluate_case(self.case,self.rows)
  self.assertTrue(any(r['filter_state']=='IZLEME' for r in x['high_probability_filter']))
  self.assertTrue(all(r['filter_state']!='GECTI' and r['recommended'] is False for r in x['high_probability_filter']))
 def test_sensitivity_is_only_heuristic(self):
  with_s=copy.deepcopy(self.case)
  with_s['analysis']['model_outputs']['C2']['sensitivity']={'status':'HEURISTIC_NOT_CONFIDENCE_INTERVAL','input_variation':.1,'ranges':{'MS1':[.72,.80],'BTTS_YES':[.2,.7]}}
  x=evaluate_case(with_s,self.rows)
  ms=next(r for r in x['high_probability_filter'] if r['market']=='MS1')
  self.assertEqual(ms['lambda_stress_range'],[.72,.80])
  self.assertFalse(ms['recommended'])
  self.assertIsNone(next(r for r in x['high_probability_filter'] if r['market']=='OVER_1.5')['lambda_stress_range'])
 def test_same_season_base_rate_excludes_today_and_future(self):
  x=evaluate_case(self.case,self.rows)
  base=next(r for r in x['high_probability_filter'] if r['market']=='MS1')['base_rate']
  fake=copy.deepcopy(self.rows)
  for r in fake:
   if r['match_date']>=self.case['identity']['target_date']:
    r['home_goals']='100';r['away_goals']='0'
  after=evaluate_case(self.case,fake)
  newbase=next(r for r in after['high_probability_filter'] if r['market']=='MS1')['base_rate']
  self.assertEqual(base,newbase)
  self.assertFalse(base['changes_filter'])
  self.assertGreater(base['sample_size'],0)
 def test_conflicting_probability_rejected(self):
  bad=copy.deepcopy(self.case)
  bad['analysis']['model_outputs']['C2']['goals']['markets']['1X']=.001
  with self.assertRaises(DecisionPreflightError):evaluate_case(bad,self.rows)
 def test_broken_forecast_cutoff_rejected(self):
  bad=copy.deepcopy(self.case)
  bad['data_context']['cutoff_exclusive']='2026-11-01'
  with self.assertRaises(DecisionPreflightError):evaluate_case(bad,self.rows)
 def test_high_p_cannot_become_class_A(self):
  x=evaluate_case(self.case,self.rows)
  self.assertTrue(all(r['A_B_C']=='DEGERLENDIRILEMEDI' for r in x['high_probability_filter']))
 def test_user_odds_unavailable_no_ev(self):
  x=evaluate_case(self.case,self.rows)
  self.assertIsNone(x['odds_or_EV']);self.assertEqual(x['value_selections'],[])
  self.assertEqual(x['value_status'],'NOT_EVALUATED_NO_VERIFIED_PREMATCH_ODDS')
 def test_disabled_half_corner_markets_absent(self):
  x=evaluate_case(self.case,self.rows)
  self.assertFalse(any('CORN' in r['market'] or 'HALF' in r['market'] for r in x['high_probability_filter']))
 def test_section_gate_accepts_proper_preflight(self):
  self.assertEqual(audit(self.bundle)['status'],'PASS_OFFLINE_INTEGRATION_ONLY')
 def test_section_gate_rejects_forged_A(self):
  x=copy.deepcopy(self.bundle)
  x['cases'][0]['decision_preflight_263']['A_B_C_official_candidates']=[{'market':'1X','class':'A'}]
  with self.assertRaises(SectionAcceptanceError):audit(x)
 def test_section_gate_rejects_inflated_market(self):
  x=copy.deepcopy(self.bundle)
  x['cases'][0]['decision_preflight_263']['high_probability_filter'][0]['p_model']=0.9
  with self.assertRaises(SectionAcceptanceError):audit(x)
 def test_section_gate_rejects_model_b_fallback(self):
  x=copy.deepcopy(self.bundle)
  x['cases'][1]['decision_preflight_263']['canonical_model']='C1'
  with self.assertRaises(SectionAcceptanceError):audit(x)
 def test_section_gate_rejects_pass_claim(self):
  x=copy.deepcopy(self.bundle)
  x['cases'][0]['decision_preflight_263']['high_probability_filter'][0]['filter_state']='GECTI'
  with self.assertRaises(SectionAcceptanceError):audit(x)
 def test_section_gate_rejects_reference_rate_as_model(self):
  x=copy.deepcopy(self.bundle)
  x['cases'][0]['decision_preflight_263']['high_probability_filter'][0]['base_rate']['changes_filter']=True
  with self.assertRaises(SectionAcceptanceError):audit(x)
 def test_bundle_rejects_live_claim(self):
  x=copy.deepcopy(self.bundle);x['real_fixture_verified']=True
  with self.assertRaises(DecisionPreflightError):evaluate_bundle(x,self.rows)

if __name__=='__main__':unittest.main()
