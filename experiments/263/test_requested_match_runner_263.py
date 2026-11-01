"""New path-only tests. Does NOT re-run xG/C3 retrospective performance tests."""
import copy,json,unittest,os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from requested_match_runner_263 import requested_match, write_outputs, RequestedMatchError
from operational_report_263 import named_cases

HERE=Path(__file__).resolve().parent
NOW=datetime(2026,11,2,15,0,tzinfo=timezone.utc)
INDEX=HERE/'evidence'/'identity_index_263.json'
ALIASES=HERE.parents[1]/'data'/'team_aliases_reviewed.csv'
HISTORY=Path(os.environ.get('M263_FROZEN_HISTORY',str(HERE/'frozen_historical_results.csv')))
EVIDENCE=HERE/'evidence'/'acceptance_263.json'
IDENTITY=named_cases(INDEX,ALIASES,[{'league':'TUR1','home':'Galatasaray','away':'Konyaspor','target_date':'2026-11-03'}])[0]

def gate(league,home,away,registry_path):
    return {'status':'VERIFIED','league':league,'home_id':IDENTITY['home_id'],
            'away_id':IDENTITY['away_id'],'kickoff_utc':'2026-11-03T16:00:00+00:00',
            'retrieved_at_utc':NOW.isoformat(),
            'source_url':'https://www.tff.org/default.aspx?pageID=28'}

class NamedRunnerTests(unittest.TestCase):
    def args(self,**changes):
        a=dict(league='TUR1',home='Galatasaray',away='Konyaspor',index_path=INDEX,
               alias_path=ALIASES,history_path=HISTORY,evidence_path=EVIDENCE,
               fixture_gate=gate,now=NOW)
        a.update(changes)
        return a
    def test_fail_closed_before_loading_any_history(self):
        with patch('requested_match_runner_263.load_history',side_effect=AssertionError('should not load')):
            status,files=requested_match(**self.args(fixture_gate=lambda *args,**kw:{'status':'NOT_VERIFIED'}))
        self.assertEqual(status['status'],'OFFICIAL_FIXTURE_NOT_VERIFIED')
        self.assertEqual(files,{})
    def test_frozen_official_named_math_17_gate(self):
        if not HISTORY.is_file():self.skipTest("frozen 4,413-row artifact not supplied; set M263_FROZEN_HISTORY")
        status,files=requested_match(**self.args())
        self.assertEqual(status['status'],'OFFICIAL_FIXTURE_CHECKED_FROZEN_MATH_PREVIEW_ONLY')
        self.assertIs(status['live_analysis_accepted'],False)
        self.assertEqual(files['section_acceptance_263.json']['status'],'PASS_OFFLINE_INTEGRATION_ONLY')
        math=files['model_preview.json']; self.assertFalse(math['real_fixture_verified'])
        self.assertEqual(math['cases'][0]['identity']['target_date'],'2026-11-03')
        self.assertEqual(math['cases'][0]['identity']['home_id'],IDENTITY['home_id'])
        self.assertIsNone(math['odds_EV'])
        self.assertEqual(math['recommendations'],[])
        self.assertEqual(status['tuesday_policy']['day'],'TUESDAY')
        self.assertFalse(status['fixture_check']['lineups_missing_blocks_analysis'])
    def test_identity_mismatch_rejected_before_math(self):
        def bad(*args,**kwargs):
            obs=gate(*args,**kwargs);obs['home_id']='wrong';return obs
        with patch('requested_match_runner_263.load_history',side_effect=AssertionError('should not load')):
            with self.assertRaisesRegex(RequestedMatchError,'IDENTITY_MISMATCH'):
                requested_match(**self.args(fixture_gate=bad))
    def test_official_bad_domain_rejected(self):
        def bogus(*args,**kwargs):
            obs=gate(*args,**kwargs);obs['source_url']='https://tff.org.evil.invalid';return obs
        status,files=requested_match(**self.args(fixture_gate=bogus))
        self.assertEqual(status['status'],'OFFICIAL_FIXTURE_NOT_VERIFIED')
        self.assertEqual(files,{})
    def test_stale_verified_observation_rejected(self):
        def stale(*args,**kwargs):
            obs=gate(*args,**kwargs);obs['retrieved_at_utc']='2026-10-29T10:00:00Z';return obs
        status,files=requested_match(**self.args(fixture_gate=stale))
        self.assertEqual(status['status'],'OFFICIAL_FIXTURE_NOT_VERIFIED')
        self.assertFalse(files)
    def test_unauthorized_history_mutation_rejected(self):
        with self.assertRaises(Exception):requested_match(**self.args(history_path=HERE/'mackolik_reviewed_aliases.csv'))
    def test_wrong_staged_pair_fails_closed(self):
        with self.assertRaisesRegex(RequestedMatchError,'requires base'):
            requested_match(**self.args(refresh_audit_path='audit-does-not-matter.json'))
    def staged_audit(self, path):
        from quality_gate_263 import HISTORICAL_SHA256
        a={'version':'263_append_only_provider_snapshot_v1',
           'status':'STAGED_UNVERIFIED_SOURCE_FILES',
           'base_sha256':HISTORICAL_SHA256,'base_rows':4413,
           'total_rows':4413,'appended':0,
           'extended_history_sha256':HISTORICAL_SHA256,
           'source_completeness':'TEN_LEAGUES',
           'independent_source_verification':False,
           'retrospective_model_acceptance_transferred':False,
           'as_of_exclusive':'2026-11-02'}
        path.write_text(json.dumps(a),encoding='utf-8')
        return a
    def test_staged_freshness_is_not_transferred_calibration(self):
        if not HISTORY.is_file():self.skipTest("frozen 4,413-row artifact not supplied; set M263_FROZEN_HISTORY")
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'audit.json';self.staged_audit(f)
            status,files=requested_match(**self.args(history_path=HISTORY,
                 base_path=HISTORY,refresh_audit_path=f,evidence_path=None))
        self.assertEqual(status['status'],'OFFICIAL_FIXTURE_CHECKED_STAGED_MATH_PREVIEW_ONLY')
        self.assertFalse(status['live_analysis_accepted'])
        self.assertEqual(status['section_17_acceptance'],'NOT_TRANSFERRED_TO_STAGED_DATA')
        p=files['staged_math_preview.json']
        self.assertEqual(p['status'],'OFFLINE_STAGED_SOURCE_PREVIEW_NOT_ACCEPTED')
        self.assertFalse(p['retrospective_2026_27_model_acceptance_applies_to_updated_snapshot'])
        self.assertEqual(p['recommendations'],[])
        self.assertIsNone(p['odds_EV'])
    def test_tampered_staged_audit_rejected(self):
        if not HISTORY.is_file():self.skipTest("frozen 4,413-row artifact not supplied; set M263_FROZEN_HISTORY")
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'audit.json';bad=self.staged_audit(f);bad['appended']=1
            f.write_text(json.dumps(bad),encoding='utf-8')
            with self.assertRaises(Exception):requested_match(**self.args(
                history_path=HISTORY,base_path=HISTORY,refresh_audit_path=f,evidence_path=None))
    def test_output_does_not_create_betting_ledger(self):
        if not HISTORY.is_file():self.skipTest("frozen 4,413-row artifact not supplied; set M263_FROZEN_HISTORY")
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            status,files=requested_match(**self.args())
            p=write_outputs(status,files,td)
            self.assertTrue((p/'model_preview.json').exists())
            self.assertFalse((p/'betting_ledger.json').exists())
            self.assertFalse((p/'predictions.csv').exists())
    def test_no_arbitrary_external_fixture_json_accepted(self):
        import inspect
        sig=inspect.signature(requested_match)
        self.assertNotIn('fixture_json',sig.parameters)
        self.assertNotIn('verified',sig.parameters)

if __name__=='__main__':unittest.main()
