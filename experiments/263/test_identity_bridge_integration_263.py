"""No performance estimates are recomputed; uses existing synthetic model fixtures."""
import unittest
from pathlib import Path
from test_analysis_math_core import synthetic_rows
from quality_gate_263 import locked_evidence
from integrated_offline_report import build_offline_bundle, render_bundle_markdown, IntegratedReportError

HERE=Path(__file__).resolve().parent

class IdentityBridgeIntegration263Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=synthetic_rows(120)
        cls.source={'sha256':'SYNTHETIC_ONLY','rows':len(cls.rows),'market_quarantine':{}}
        cls.evidence=locked_evidence(HERE/'evidence'/'acceptance_263.json')
        cls.case={'league':'SYN','season':'S2','previous_season':'S1','target_date':'2025-11-18','home_id':'T0','away_id':'T1'}
    def test_when_no_registry_no_false_claims(self):
        b=build_offline_bundle(self.rows,self.source,self.evidence,[self.case],require_locked_source=False)
        self.assertEqual(b['historical_identity_linkage']['status'],'NOT_CHECKED')
        self.assertEqual(b['cases'][0]['data_context']['registry_linkage']['status'],'NOT_CHECKED')
        self.assertIn('NOT_CHECKED',render_bundle_markdown(b))
    def test_matching_attestation_does_not_upgrade_recommendations(self):
        attestation={'status':'OFFLINE_REGISTRY_LINKAGE_VALIDATED','history_sha256':'SYNTHETIC_ONLY',
                     'historical_rows_linked':len(self.rows),'registry_sha256':'a'*64,
                     'independently_verified_official_fixture':False,
                     'independently_verified_squad_or_lineups':False}
        b=build_offline_bundle(self.rows,self.source,self.evidence,[self.case],require_locked_source=False,identity_audit=attestation)
        self.assertEqual(b['historical_identity_linkage']['status'],'OFFLINE_REGISTRY_LINKAGE_VALIDATED')
        self.assertFalse(b['real_fixture_verified'])
        self.assertFalse(b['cases'][0]['data_context']['recommendation_eligible'])
        self.assertEqual(b['cases'][0]['quality']['recommendations'],[])
    def test_mismatched_identity_proof_rejected(self):
        fake={'status':'OFFLINE_REGISTRY_LINKAGE_VALIDATED','history_sha256':'WRONG',
              'historical_rows_linked':len(self.rows),'registry_sha256':'b'*64,
              'independently_verified_official_fixture':False,
              'independently_verified_squad_or_lineups':False}
        with self.assertRaisesRegex(IntegratedReportError,'identity attestation'):
            build_offline_bundle(self.rows,self.source,self.evidence,[self.case],require_locked_source=False,identity_audit=fake)
    def test_claim_of_live_verification_fails_closed(self):
        fake={'status':'OFFLINE_REGISTRY_LINKAGE_VALIDATED','history_sha256':'SYNTHETIC_ONLY',
              'historical_rows_linked':len(self.rows),'registry_sha256':'b'*64,
              'independently_verified_official_fixture':True,
              'independently_verified_squad_or_lineups':False}
        with self.assertRaises(IntegratedReportError):
            build_offline_bundle(self.rows,self.source,self.evidence,[self.case],require_locked_source=False,identity_audit=fake)

if __name__=='__main__':unittest.main()
