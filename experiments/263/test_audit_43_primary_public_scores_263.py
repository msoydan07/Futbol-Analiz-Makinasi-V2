"""43 completed scores and original 99 checksum: source URL research fail closed."""
import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_43_primary_public_scores_263 import ROOT,PROOF,verify,Unsafe

class Source43AuditTests(unittest.TestCase):
    def data(self):
        return json.loads((ROOT/PROOF).read_text(encoding="utf-8"))
    def test_all_43_10_15_10_8_same_orig_scores_and_4518_untouched(self):
        a=verify()
        self.assertEqual(a["matches"],43)
        self.assertEqual(a["league_breakdown"],{"ENG1":10,"ENG2":15,"BEL1":10,"POR1":8})
        self.assertEqual(a["original_score_conflicts"],0)
        self.assertTrue(a["4617_training_input_sha_unchanged"])
        self.assertEqual(a["independent_network_score_attestations_by_this_CI"],0)
        self.assertFalse(a["betting_authorized"])
    def test_change_score_fails(self):
        d=self.data();d["records"][0]["home_goals"]=8
        with self.assertRaisesRegex(Unsafe,"OFFICIAL_SCORE_NOT_EQUAL_TO_FROZEN_99"):
            verify(overridden=d)
    def test_forged_efl_hostname_fails(self):
        d=self.data();d["records"][11]["score_source_url"]="https://www.efl.com.evil.tld/07-scores"
        with self.assertRaisesRegex(Unsafe,"PRIMARY_SITE_OR_EVIDENCE_GRADE_INVALID"):
            verify(overridden=d)
    def test_wrong_competition_or_fake_video_fails(self):
        d=self.data();d["records"][40]["score_source_url"]="https://www.ligaportugal.pt/calendar"
        with self.assertRaisesRegex(Unsafe,"PORTUGUESE_EXPLICIT_SCORELINE_VIDEO_REQUIRED"):
            verify(overridden=d)
    def test_mismatched_belgium_league_article_fails(self):
        d=self.data();d["records"][27]["score_source_url"]="https://www.proleague.be/fr/jpl-calendar"
        with self.assertRaisesRegex(Unsafe,"BELGIAN_MATCH_LEVEL_URL_REQUIRED"):
            verify(overridden=d)
    def test_missing_or_duplicate_match_fails(self):
        d=self.data();d["records"][42]=copy.deepcopy(d["records"][41])
        with self.assertRaisesRegex(Unsafe,"DUPLICATE_OR_UNMATCHED_SECONDARY"):
            verify(overridden=d)
    def test_fabricated_official_venue_or_network_attestation_fails(self):
        d=self.data();d["records"][0]["independently_fetched_and_parsed_by_ci"]=True
        with self.assertRaisesRegex(Unsafe,"FABRICATED_PROVIDER_ATTESTATION"):
            verify(overridden=d)
        d=self.data();d["all_43_official_provider_unique_match_ids_verified"]=True
        with self.assertRaisesRegex(Unsafe,"PROVENANCE_CONTRACT_NOT_RESEARCH_ONLY"):
            verify(overridden=d)
if __name__=="__main__":
    unittest.main()
