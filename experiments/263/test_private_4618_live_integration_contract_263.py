"""Research contract tests; NO real odds, user PDF, or private history in CI."""
from __future__ import annotations
import ast,hashlib,json,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
NOW=datetime(2026,11,19,14,30,tzinfo=timezone.utc)
SHA_4618='54250bb6107250d0623b74ad9c56f90731f02d10dab3bf386deefb27aae487ea'
GRADE='PRIVATE_4618_SECONDARY_GAP_WITNESSED_RESEARCH_NOT_OFFICIAL_RESULTS'

def source(name):
    return (HERE/name).read_text(encoding='utf-8')

def node(name,func):
    t=ast.parse(source(name))
    return next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==func)

class Boundaries(unittest.TestCase):
    def test_01_python_compiles_five_new_research_modules(self):
        names=['private_4618_provider_bundle_263.py',
               'private_4618_quad_forward_263.py',
               'private_4618_empirical_baseline_263.py',
               'private_4618_pdf_session_263.py',
               'private_4618_iddaa_model_first_one_step_263.py']
        for name in names:
            with self.subTest(module=name):compile(source(name),name,'exec')

    def test_02_original_b_and_c3_poisson_functions_unchanged(self):
        for fn in ('_legacy_joint','_b_lambdas'):
            self.assertEqual(ast.dump(node('forward_quad.py',fn),include_attributes=False),
                ast.dump(node('private_4618_quad_forward_263.py',fn),include_attributes=False))

    def test_03_locked_m4_and_c2_functions_still_imported_not_edited(self):
        s=source('private_4618_quad_forward_263.py')
        for part in ('from m4_integrated import Settings, fit_m4, predict_m4, score_markets, use_lock, FEATURE_VERSION',
                     'from analysis_math_core import canonical_c2_lambda, score_market',
                     'from exp_263_batch import c1, clean_rows, fit_c3, predict_c3, scores',
                     'lock.get(\'m4_engine_sha256\')!=sha256_file(Path(__file__).with_name(\'m4_integrated.py\'))',
                     "'private_4618_research_only':True"):
            self.assertIn(part,s)

    def test_04_price_comparison_only_after_model_decision(self):
        bridge=source('model_first_iddaa_bridge_263.py')
        self.assertLess(bridge.index('d=select(f,b,lock'),bridge.index('ref=market_reference(d,trusted_groups'))
        self.assertNotIn('from four_model_value_policy_263 import decide',bridge)
        self.assertIn('"odds_affected_selection"]=False',bridge)

    def test_05_pdf_session_imports_isolated_runner_and_baseline(self):
        self.assertIn('from private_4618_quad_forward_263 import predict_quad_from_verified_gate',
                      source('private_4618_pdf_session_263.py'))
        self.assertIn('from private_4618_empirical_baseline_263 import produce as build_baseline',
                      source('private_4618_pdf_session_263.py'))
        self.assertNotIn('private_4618_',source('iddaa_pdf_session_263.py'))

    def test_06_4618_grade_never_production(self):
        pred=source('private_4618_quad_forward_263.py')
        base=source('private_4618_empirical_baseline_263.py')
        self.assertIn(GRADE,pred)
        self.assertIn(GRADE,base)
        self.assertIn("'production_approved':False",pred)
        self.assertIn("shadow_evidence is not None",pred)
        self.assertIn("source_contains_same_day_or_future_results",pred)

    def test_07_original_sha_and_no_manual_acceptance(self):
        s=source('private_4618_iddaa_model_first_one_step_263.py')
        self.assertIn('verify_private_projection(source_baseline,history)',s)
        self.assertIn('create_witnesses(',s)
        self.assertIn('MANUALLY_SUPPLIED_ACCEPTANCE_CANNOT_REPLACE_LIVE_PROVIDER_FETCH',s)
        self.assertIn('"research_only_not_production_authorized":True',s)

    def test_08_symmetric_original_two_pdf_review_not_changed(self):
        old=source('iddaa_pdf_last_review_263.py')
        for required in ('second_model_seal_created":False','forecast_shas_replaced":False','math_refitted":False'):
            self.assertIn(required,old)
        self.assertNotIn('from private_4618_quad_forward',old)

class ReceiptTests(unittest.TestCase):
    def setUp(self):
        from private_4618_provider_bundle_263 import SCHEMA
        self.schema=SCHEMA
        self.data={'private_score_projection_sha256':SHA_4618,'legacy_sha256':'a'*64,
                   'latest_by_league':{'ENG1':'2026-11-08'}}
        self.mockbulletin={'rows':[{'league':'ENG1'}]}
        self.report={'full_time_source_rows':105,'prior_or_equal_frozen_rows':105,
                     'new_full_time_in_gap':[],'source_sha256':'b'*64}

    def _make(self,p,*,network=True):
        from private_4618_provider_bundle_263 import create_witnesses
        from unittest.mock import patch
        with patch('private_4618_provider_bundle_263.verify_private_projection',
                   return_value=self.data),patch(
                   'private_4618_provider_bundle_263.fetch_source',return_value=b'FAKE_SOURCE_BYTES'),patch(
                   'private_4618_provider_bundle_263.witness_source',return_value=self.report):
            if network:
                return create_witnesses(legacy='legacy',projection='private',
                    bulletin=self.mockbulletin,destination=p,now=NOW)
            return create_witnesses(legacy='legacy',projection='private',
                    bulletin=self.mockbulletin,destination=p,now=NOW,
                    fetcher=lambda url:(url,b'FAKE_SOURCE_BYTES'))

    def test_09_network_receipt_is_still_research_only(self):
        with tempfile.TemporaryDirectory() as d:
            record=self._make(Path(d)/'receipt')
            self.assertTrue(record['sources']['ENG1']['network_fetch_by_code'])
            self.assertFalse(record['official_results_verified'])
            self.assertFalse(record['production_approved'])

    def test_10_injected_source_always_blocked(self):
        from private_4618_provider_bundle_263 import inspect_witness,WitnessBlocked
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'receipt';self._make(root,network=False)
            with patch('private_4618_provider_bundle_263.verify_private_projection',return_value=self.data):
                with self.assertRaisesRegex(WitnessBlocked,'SYNTHETIC_SOURCE'):
                    inspect_witness(root=root,league='ENG1',legacy='x',
                        projection='y',target_day='2026-11-21',now=NOW)

    def test_11_corrupt_manifest_sha_blocks(self):
        from private_4618_provider_bundle_263 import inspect_witness,WitnessBlocked
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'receipt';self._make(root)
            path=root/'manifest.json';obj=json.loads(path.read_text())
            obj['sources']['ENG1']['source_url']='https://evil.example/fake'
            path.write_text(json.dumps(obj))
            with patch('private_4618_provider_bundle_263.verify_private_projection',return_value=self.data):
                with self.assertRaisesRegex(WitnessBlocked,'MANIFEST_OR_DATA_SHA_INVALID'):
                    inspect_witness(root=root,league='ENG1',legacy='x',
                        projection='y',target_day='2026-11-21',now=NOW)

    def test_12_new_completed_game_blocks_not_pass(self):
        from private_4618_provider_bundle_263 import inspect_witness,WitnessBlocked
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'receipt';self._make(root)
            r={**self.report,'new_full_time_in_gap':[{'day':'2026-11-12'}]}
            with patch('private_4618_provider_bundle_263.verify_private_projection',return_value=self.data),patch(
                 'private_4618_provider_bundle_263.witness_source',return_value=r):
                with self.assertRaisesRegex(WitnessBlocked,'COMPLETED_LEAGUE_RESULTS_NOT_IN_FROZEN_4618'):
                    inspect_witness(root=root,league='ENG1',legacy='x',
                        projection='y',target_day='2026-11-21',now=NOW)

    def test_13_expired_receipt_blocks(self):
        from private_4618_provider_bundle_263 import inspect_witness,WitnessBlocked
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'receipt';self._make(root)
            with patch('private_4618_provider_bundle_263.verify_private_projection',return_value=self.data):
                with self.assertRaisesRegex(WitnessBlocked,'STALE_OR_FUTURE'):
                    inspect_witness(root=root,league='ENG1',legacy='x',projection='y',
                        target_day='2026-11-21',now=NOW+timedelta(hours=2))

if __name__=='__main__':unittest.main(verbosity=2)
