"""The 99-score closeout has no silent result, team or claimed-proof changes."""
import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from close_99_results_source_audit_263 import ROOT,MANIFEST43,MANUAL21,audit,Rejected

class Close99ScoreAndSourceEvidence(unittest.TestCase):
    def docs(self):
        return (
            json.loads((ROOT/MANIFEST43).read_text(encoding="utf-8")),
            json.loads((ROOT/MANUAL21).read_text(encoding="utf-8"))
        )
    def test_all_99_results_persist_and_exactly_21_more_reviewed(self):
        p=audit()
        self.assertTrue(p["99_results_permanently_archived"])
        self.assertEqual(p["new_completed_score_rows"],99)
        self.assertEqual(p["automated_browser_source_body_matching_finished_scores"],22)
        self.assertEqual(p["alternate_public_official_page_reviews"],21)
        self.assertFalse(p["all_43_live_automated_source_body_proved"])
        self.assertFalse(p["github_browser_proleague_403_issue_resolved"])
        self.assertEqual(p["archived_score_conflicts"],0)
    def test_changed_goal_is_rejected_even_when_url_looks_official(self):
        a,b=self.docs();b["primary_evidence_rows"][0]["home_goals"]=9
        with self.assertRaisesRegex(Rejected,"EXTERNAL_SOURCE_RESULT_NOT_FROZEN"):
            audit(source43=a,source21=b)
    def test_cross_match_identity_cannot_steal_an_official_url(self):
        a,b=self.docs();b["primary_evidence_rows"][0]["away_id"]=b["primary_evidence_rows"][1]["away_id"]
        with self.assertRaisesRegex(Rejected,"EXTERNAL_SOURCE_WRONG_MATCH"):
            audit(source43=a,source21=b)
    def test_different_primary_site_not_allowed(self):
        a,b=self.docs();b["primary_evidence_rows"][0]["primary_evidence_url"]="https://evil.tld/en/match/Arsenal-Hull"
        with self.assertRaisesRegex(Rejected,"UNTRUSTED_ALTERNATE_WEB_EVIDENCE_URL"):
            audit(source43=a,source21=b)
    def test_cannot_double_count_one_review(self):
        a,b=self.docs();b["primary_evidence_rows"][0]=copy.deepcopy(b["primary_evidence_rows"][1])
        with self.assertRaisesRegex(Rejected,"NOT_EXACTLY_UNRESOLVED_21"):
            audit(source43=a,source21=b)
    def test_fabricated_github_web_attestation_fails(self):
        a,b=self.docs();b["github_ci_independently_fetched_all_21"]=True
        with self.assertRaisesRegex(Rejected,"EXTERNAL_PUBLIC_PAGE_REVIEW_MISREPRESENTED"):
            audit(source43=a,source21=b)
    def test_fabricated_provider_match_id_fails(self):
        a,b=self.docs();b["primary_evidence_rows"][4]["official_provider_single_fixture_id_independently_attested"]=True
        with self.assertRaisesRegex(Rejected,"OFFICIAL_ID_OR_INDEPENDENT_BROWSER_ATTESTATION_FABRICATED"):
            audit(source43=a,source21=b)
    def test_cannot_turn_22_browser_matches_into_43(self):
        a,b=self.docs();a["live_browser_latest_counts"]["EXACT_SCORE_AND_TEAMS_IN_VISIBLE_BODY"]=43
        with self.assertRaisesRegex(Rejected,"GITHUB_BROWSER_22_OF_43_NOT_RESEARCH_ONLY"):
            audit(source43=a,source21=b)

if __name__=="__main__":
    unittest.main()
