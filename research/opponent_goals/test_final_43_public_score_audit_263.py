"""One regression batch: 99 public score observations are NOT 99 official attestations."""
import sys,copy,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from final_43_public_score_audit_263 import run,check_43,Blocked
ROOT=Path(__file__).resolve().parents[2]
import json
def read(p):return json.loads((ROOT/p).read_text(encoding="utf8"))
class TestIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=read("research/opponent_goals/remaining_43_public_score_observations_20261110.json")
        cls.idx=read("experiments/263/evidence/identity_index_263.json")
    def test_total_counts_conservative(self):
        d=run(ROOT)
        self.assertEqual(d["total_score_observations"],99)
        self.assertEqual(d["previous_official_or_league_score_provider_concordance_n"],28)
        self.assertEqual(d["previous_published_official_league_or_club_only_n"],28)
        self.assertEqual(d["last_external_published_scores_n"],43)
        self.assertEqual(d["total_new_federation_unique_fixture_ids_attested"],0)
        self.assertEqual(d["total_newly_accepted_provider_rows"],0)
        self.assertTrue(d["portugal_postponed_estoril_maritimo_not_scored"])
    def test_falsely_attested_fixture_blocked(self):
        x=copy.deepcopy(self.doc)
        x["records"][0]["official_fixture_id"]="not-real"
        with self.assertRaisesRegex(Blocked,"UNVERIFIED_LINK"):check_43(x,self.idx,set(),set())
    def test_bad_team_id_blocked(self):
        x=copy.deepcopy(self.doc)
        x["records"][0]["home_id"]="fake-canonical-id"
        with self.assertRaisesRegex(Blocked,"IDENTITY_ALIAS"):check_43(x,self.idx,set(),set())
    def test_goal_result_mismatch_blocked(self):
        x=copy.deepcopy(self.doc)
        x["records"][0]["result"]="D"
        with self.assertRaisesRegex(Blocked,"RESULT"):check_43(x,self.idx,set(),set())
    def test_duplicate_result_blocked(self):
        x=copy.deepcopy(self.doc)
        x["records"][1]=copy.deepcopy(x["records"][0])
        with self.assertRaisesRegex(Blocked,"DUPLICATED"):check_43(x,self.idx,set(),set())
    def test_false_vendor_join_blocked(self):
        x=copy.deepcopy(self.doc)
        x["records"][0]["provider_row_linked"]=True
        with self.assertRaisesRegex(Blocked,"UNVERIFIED_LINK"):check_43(x,self.idx,set(),set())
    def test_wrong_source_domain_blocked(self):
        x=copy.deepcopy(self.doc)
        x["records"][0]["published_score_url"]="https://example.com/unrelated"
        with self.assertRaisesRegex(Blocked,"UNTRUSTED"):check_43(x,self.idx,set(),set())
if __name__=="__main__":unittest.main()
