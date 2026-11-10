"""Adversarial offline verification of additional 28 source-side observations."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_additional_official_28 import audit,check_new,EvidenceError,load
ROOT=Path(__file__).resolve().parents[2]
class TestOfficialAdditional(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=load(ROOT/"research/opponent_goals/official_additional_28_nov06_08_2026.json")
        cls.registry=load(ROOT/"experiments/263/evidence/identity_index_263.json")
        cls.old=load(ROOT/"research/opponent_goals/official_rounds_nov06_08_2026.json")
    def test_56_not_56_provider_concordances(self):
        r=audit(ROOT)
        self.assertEqual(r["observed_official_or_club_source_total"],56)
        self.assertEqual(r["without_official_or_club_source_research_observation"],43)
        self.assertEqual(r["new_official_club_source_not_yet_provider_concordant"],28)
        self.assertEqual(r["official_match_provider_independent_api_attestation_count_new"],0)
        self.assertFalse(r["production_history_updated"])
    def test_alias_tampering_blocked(self):
        doc=copy.deepcopy(self.doc)
        doc["records"][0]["home_id"]="not-a-verified-team"
        with self.assertRaisesRegex(EvidenceError,"TEAM_ALIAS"):check_new(doc,self.registry,self.old)
    def test_faked_supplier_confirmation_blocked(self):
        doc=copy.deepcopy(self.doc)
        doc["records"][0]["source_supplier_crosscheck"]="PROVIDER_CONCORDANT"
        with self.assertRaisesRegex(EvidenceError,"FALSE_PROVIDER"):check_new(doc,self.registry,self.old)
    def test_score_and_result_conflict_blocked(self):
        doc=copy.deepcopy(self.doc);doc["records"][0]["result"]="H"
        with self.assertRaisesRegex(EvidenceError,"RESULT_SCORE"):check_new(doc,self.registry,self.old)
    def test_duplicate_fixture_blocked(self):
        doc=copy.deepcopy(self.doc);doc["records"][1]=doc["records"][0]
        with self.assertRaisesRegex(EvidenceError,"REPEATED_CANONICAL"):check_new(doc,self.registry,self.old)
    def test_wrong_host_blocked(self):
        doc=copy.deepcopy(self.doc)
        doc["records"][0]["score_evidence_url"]="https://random.example/score"
        with self.assertRaisesRegex(EvidenceError,"UNAPPROVED"):check_new(doc,self.registry,self.old)

if __name__=="__main__":unittest.main()
