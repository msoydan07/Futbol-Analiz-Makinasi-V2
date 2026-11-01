import copy, json, unittest
from pathlib import Path
from section_acceptance_263 import audit, SectionAcceptanceError
from decision_preflight_263 import evaluate_case
BASE=Path(__file__).parent/'evidence'/'section_contract_sample_263.json'
class SectionGateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.report=json.loads(BASE.read_text(encoding='utf-8'))
  rows=[{'league':e['identity']['league'],'season':e['identity']['season'],
         'match_date':'2026-10-01','home_goals':'2','away_goals':'1'} for e in cls.report['cases']]
  for e in cls.report['cases']:e['decision_preflight_263']=evaluate_case(e,rows)
 def check_bad(self, mutate):
  x=copy.deepcopy(self.report);mutate(x)
  with self.assertRaises(SectionAcceptanceError):audit(x)
 def test_valid_offline_bundle_is_not_live_accepted(self):
  r=audit(self.report)
  self.assertEqual(r['status'],'PASS_OFFLINE_INTEGRATION_ONLY')
  self.assertFalse(r['live_263_accepted'])
  self.assertEqual([s['number'] for s in r['sections']],list(range(1,18)))
  self.assertEqual(r['c2_available_cases'],1)
 def test_tuesday_lock(self):self.check_bad(lambda x:x['weekly_update_policy'].update(day='WEDNESDAY'))
 def test_automation_not_claimed(self):self.check_bad(lambda x:x['weekly_update_policy'].update(automation_verified=True))
 def test_recommendation_forbidden(self):self.check_bad(lambda x:x.update(recommendations=[{'market':'MS1'}]))
 def test_live_fixture_not_faked(self):self.check_bad(lambda x:x.update(real_fixture_verified=True))
 def test_c2_k_locked(self):self.check_bad(lambda x:x['cases'][0]['analysis']['model_outputs']['C2']['details'].update(k=7))
 def test_bad_probability_sum(self):self.check_bad(lambda x:x['cases'][0]['analysis']['model_outputs']['C2']['goals']['markets'].update(MS1=0.91))
 def test_invalid_cutoff(self):self.check_bad(lambda x:x['cases'][0]['data_context'].update(cutoff_exclusive='2026-11-04'))
 def test_xg_cannot_change_lambda(self):self.check_bad(lambda x:x['cases'][0]['descriptive_xg'].update(used_as_lambda_multiplier=True))
 def test_wrong_ranking_model(self):self.check_bad(lambda x:x['cases'][1]['probability_ranking'].update(model='C3'))
 def test_c2_cannot_be_fallback(self):self.check_bad(lambda x:x['cases'][1]['model_arbitration'].update(canonical_primary='C1'))
 def test_sections_must_be_seventeen(self):self.check_bad(lambda x:x['sections'].pop())
 def test_section_names_must_be_canonical(self):self.check_bad(lambda x:x['sections'][10].update(title='İlk yarı korner'))
 def test_market_cannot_claim_calibration(self):self.check_bad(lambda x:x['cases'][0]['quality']['markets'][0].update(calibrated=True))
 def test_old_snapshot_immutable(self):self.check_bad(lambda x:x['data_provenance'].update(rows=4414))
 def test_missing_first_xi_does_not_block(self):
  x=copy.deepcopy(self.report)
  self.assertEqual(x['cases'][0]['external_factors']['lineups'],'NOT_CHECKED')
  self.assertEqual(audit(x)['status'],'PASS_OFFLINE_INTEGRATION_ONLY')
if __name__=='__main__': unittest.main()
