"""Synthetic contract tests only; actual 4509 artifact audited by the action."""
import copy
import unittest

from source_evidence_strict_263 import audit, SCHEMA, SOURCES, STAGE_SHA

class SourceSpecificEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data={"schema":SCHEMA,"staged_history_sha256":STAGE_SHA,
                   "human_sources_reviewed":False,"evidence":[]}
        self.rows={}
        for i,(lg,host) in enumerate(SOURCES.items()):
            fid="synthetic-id-"+lg
            self.data["evidence"].append({
                "league":lg,"fixture_id":fid,"match_date":"2026-10-31",
                "score":"2-1","source_url":"https://www."+host+"/matches/2026/fixture-result-"+lg.lower(),
                "source_tier":"OFFICIAL_LEAGUE_MATCH_PAGE",
                "human_approved":False,
                "observed_source_text_summary":"Synthetic 2-1 test page result for "+lg})
            self.rows[fid]={"fixture_id":fid,"league":lg,"match_date":"2026-10-31",
                            "home_goals":"2","away_goals":"1","season":"2026-2027"}
    def run_audit(self):
        return audit(source_rows=self.rows,evidence=self.data)
    def test_ten_qualify_as_specific_research_not_accepted(self):
        o=self.run_audit()
        self.assertEqual(o["specific_external_result_examples"],10)
        self.assertFalse(o["human_source_acceptance_complete"])
        self.assertEqual(o["previous_88_not_directly_reexamined_as_match_specific"],78)
    def test_reject_generic_results_page(self):
        self.data["evidence"][0]["source_url"]="https://www.premierleague.com/en/results"
        with self.assertRaisesRegex(ValueError,"GENERIC"):self.run_audit()
    def test_reject_score_mismatch(self):
        self.data["evidence"][0]["score"]="4-0"
        with self.assertRaisesRegex(ValueError,"WRONG_EXTERNAL_SCORE"):self.run_audit()
    def test_reject_other_bookmaker_or_domain(self):
        self.data["evidence"][0]["source_url"]="https://iddaa.com/result/20261031"
        with self.assertRaisesRegex(ValueError,"SOURCE_DOMAIN"):self.run_audit()
    def test_reject_duplicate_fixture(self):
        self.data["evidence"][1]["fixture_id"]=self.data["evidence"][0]["fixture_id"]
        with self.assertRaisesRegex(ValueError,"UNKNOWN_OR_DUPLICATE_FIXTURE"):self.run_audit()
    def test_reject_fake_human_approval(self):
        self.data["evidence"][0]["human_approved"]=True
        with self.assertRaisesRegex(ValueError,"SYNTHETIC_HUMAN"):self.run_audit()
    def test_reject_staged_history_sha_change(self):
        self.data["staged_history_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"WRONG_PINNED_HISTORY"):self.run_audit()
    def test_reject_no_ten_leagues(self):
        self.data["evidence"].pop()
        with self.assertRaisesRegex(ValueError,"NEEDS_ONE"):self.run_audit()
    def test_reject_future_result(self):
        self.rows["synthetic-id-ENG1"]["match_date"]="2026-11-06"
        with self.assertRaisesRegex(ValueError,"WRONG_SOURCE_FIXTURE_IDENTITY"):self.run_audit()
    def test_reject_missing_specific_observation(self):
        self.data["evidence"][0]["observed_source_text_summary"]=""
        with self.assertRaisesRegex(ValueError,"SPECIFIC_PAGE_OBSERVATION_MISSING"):self.run_audit()

if __name__=="__main__":unittest.main()
