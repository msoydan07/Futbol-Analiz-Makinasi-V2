import unittest
from datetime import datetime,timezone
from test_forward_empirical_baseline_263 import TestRealShape
from test_forward_calibration_bridge_263 import lock
from forward_integrated_research_263 import integrate
from forward_calibration_bridge_263 import _digest

class TestIntegrated(TestRealShape):
    def test_full_chain_and_pas_or_candidate(self):
        baseline,decision,screen=integrate(self.f,lock(),self.path,now=datetime(2026,11,6,16,0,tzinfo=timezone.utc))
        self.assertEqual(baseline["forecast_sha256"],self.f["payload_sha256"])
        self.assertIn(decision["status"],("RESEARCH_PAS","RESEARCH_CANDIDATE_NOT_APPROVED"))
        self.assertEqual(decision["pilot_count_increment"],0)
        self.assertIn("RESMÎ TERCİH YOK",screen)
    def test_shadow_rejected(self):
        self.f["status"]="EXPERIMENTAL_EARLY_SHADOW_UNVERIFIED_SOURCE_NO_BETTING"
        self.f["payload_sha256"]=_digest({k:v for k,v in self.f.items() if k!="payload_sha256"})
        with self.assertRaisesRegex(ValueError,"SHADOW_NOT_ACCEPTED"):
            integrate(self.f,lock(),self.path,now=datetime(2026,11,6,16,0,tzinfo=timezone.utc))
    def test_frozen_archive_without_human_acceptance_rejected(self):
        self.f["data"]["snapshot_acceptance"]="PINNED_FROZEN_HISTORICAL_ARCHIVE"
        self.f["payload_sha256"]=_digest({k:v for k,v in self.f.items() if k!="payload_sha256"})
        with self.assertRaisesRegex(ValueError,"UPDATED_SOURCE_NOT_HUMAN_ACCEPTED"):
            integrate(self.f,lock(),self.path,now=datetime(2026,11,6,16,0,tzinfo=timezone.utc))
if __name__=="__main__":unittest.main()
