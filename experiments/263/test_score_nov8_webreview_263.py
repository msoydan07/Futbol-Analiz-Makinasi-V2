"""Guardrails for the retrospective scorer: no guessing, no overwrite."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from score_nov8_webreview_263 import audit,AuditBlocked,markdown,ROOT
class TestWebReview(unittest.TestCase):
    def test_exact_40_39_1_and_source_separation(self):
        r=audit(ROOT)
        self.assertEqual((r["sealed_registered"],r["scored"],r["postponed"]),(40,39,1))
        self.assertEqual((r["source_counts"]["primary_scored"],r["source_counts"]["media_crosschecked_scored"]),(35,4))
        self.assertEqual(r["model_scores"]["ALL_WEB_REVIEW"]["M4"]["MS"]["n"],39)
        self.assertTrue(r["no_accepted_new100_attestations_written"])
        self.assertEqual(r["status"],"EVIDENCE_GROUPED_DESCRIPTIVE_NO_MODEL_PROMOTION")
    def test_primary_subset_and_postponed_never_scored(self):
        r=audit(ROOT)
        self.assertEqual(r["model_scores"]["PRIMARY_ONLY"]["M4"]["MS"]["n"],35)
        self.assertEqual(len([x for x in r["matches"] if x["status"]=="POSTPONED_NO_SCORE"]),1)
        self.assertIn("Ertelenmiş",markdown(r))
if __name__=="__main__":unittest.main()
