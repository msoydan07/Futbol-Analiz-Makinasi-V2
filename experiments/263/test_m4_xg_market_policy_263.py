"""No write/no retro-seal market-level evidence gate checks."""
import sys,unittest,copy
from m4_integrated import score_markets
from m4_xg_market_policy_263 import choose_market_families

class Gate(unittest.TestCase):
    def setUp(self):
        self.orig=score_markets(1.35,1.05)['markets']
        self.adjust=score_markets(1.55,1.25)['markets']
        self.payload={'schema':'263_m4_xg_sidecar_v1','use':'RESEARCH_SIDECAR_NOT_PRODUCTION',
                      'xg':{'status':'XG_INCLUDED_IN_M4_RESEARCH_LAMBDA',
                      'markets':{'M4_original':self.orig,'M4_with_xg':self.adjust}}}
    def test_marketwise_policy_selects_over25_only(self):
        frozen=copy.deepcopy(self.payload)
        p=choose_market_families(self.payload)
        self.assertEqual(p['status'],'MARKETWISE_RESEARCH_SELECT_2_5_XG')
        self.assertEqual(p['market_source'],{'MS':'M4','KG':'M4','GOALS_2_5':'M4_PLUS_PRIOR_XG'})
        self.assertEqual(p['selected_probability']['KG_VAR'],self.orig['BTTS_YES'])
        self.assertEqual(p['selected_probability']['MS1'],self.orig['1X2']['H'])
        self.assertEqual(p['selected_probability']['UST_2_5'],self.adjust['OVER_2.5'])
        self.assertAlmostEqual(p['selected_probability']['ALT_2_5']+p['selected_probability']['UST_2_5'],1)
        self.assertFalse(p['official_m4_modified'] or p['betting_authorized'])
        self.assertEqual(self.payload,frozen)
    def test_missing_xg_keeps_original_and_no_fake_probs(self):
        s=copy.deepcopy(self.payload);s['xg']={'status':'BASELINE_M4_FALLBACK','reason':'NO_XG'}
        p=choose_market_families(s)
        self.assertEqual(p['market_source']['GOALS_2_5'],'M4')
        self.assertIsNone(p['selected_probability'])
    def test_out_of_coherence_xg_market_reverts_entire_goal_pair(self):
        s=copy.deepcopy(self.payload)
        s['xg']['markets']['M4_with_xg']['OVER_2.5']=.999
        s['xg']['markets']['M4_with_xg']['UNDER_2.5']=.001
        p=choose_market_families(s)
        self.assertEqual(p['status'],'MARKETWISE_RESEARCH_GOAL_COHERENCE_FALLBACK')
        self.assertEqual(p['selected_probability']['UST_2_5'],self.orig['OVER_2.5'])
    def test_malformed_group_blocked(self):
        s=copy.deepcopy(self.payload)
        s['xg']['markets']['M4_with_xg']['UNDER_2.5']=.999
        with self.assertRaisesRegex(ValueError,'MARKET_FAMILY_NOT_NORMALIZED'):
            choose_market_families(s)
    def test_non_research_sidecar_blocked(self):
        s=copy.deepcopy(self.payload);s['use']='PRODUCTION'
        with self.assertRaisesRegex(ValueError,'RESEARCH_M4_XG'):
            choose_market_families(s)
if __name__=='__main__':unittest.main()
