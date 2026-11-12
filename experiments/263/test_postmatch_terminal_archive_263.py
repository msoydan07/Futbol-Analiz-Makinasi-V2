"""Test real 40 pregame SHA-matched archived results, no repeat source fetch."""
import copy
import unittest
from postmatch_csv_bridge_263 import ROOT,sealed,registered_names,evaluate
from postmatch_terminal_archive_263 import checked,ArchiveRejected

class OneTimeResults(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.sealed=sealed(ROOT)
  cls.named=registered_names(ROOT)
 def test_original_40_real_sha_39_final_one_postponed(self):
  a=checked(ROOT,self.sealed,self.named)
  self.assertEqual(len(a["rows"]),40)
  self.assertEqual(sum(r["score"] is not None for r in a["rows"]),39)
  self.assertEqual(sum(r["score"] is None for r in a["rows"]),1)
 def test_daily_reuses_saved_archive_with_zero_external_queries(self):
  a=evaluate(ROOT)
  self.assertTrue(a["archive_closed"])
  self.assertEqual(a["daily_external_csv_calls"],0)
  self.assertEqual((a["registered"],a["provisional_scored"],a["pending"]),(40,39,1))
  self.assertEqual(a["independent_federation_verified"],3)
  self.assertEqual(a["per_model"]["ALL_PROVISIONAL"]["M4"]["MS"]["n"],39)
  self.assertEqual(a["human_attestations_written"],0)
 def test_wrong_sha_is_rejected_not_repaired(self):
  a=copy.deepcopy(checked(ROOT,self.sealed,self.named))
  a["rows"][0]["forecast_sha256"]="0"*64
  with self.assertRaises(ArchiveRejected):checked(ROOT,self.sealed,self.named,doc=a)
 def test_wrong_result_is_rejected_not_scored(self):
  a=copy.deepcopy(checked(ROOT,self.sealed,self.named))
  r=next(r for r in a["rows"] if r["score"] is not None)
  r["score"]=[19,0]
  with self.assertRaises(ArchiveRejected):checked(ROOT,self.sealed,self.named,doc=a)
 def test_postponed_score_cannot_be_invented(self):
  a=copy.deepcopy(checked(ROOT,self.sealed,self.named))
  r=next(r for r in a["rows"] if r["score"] is None)
  r["score"]=[0,0];r["match_state"]="FINISHED_ARCHIVED"
  with self.assertRaises(ArchiveRejected):checked(ROOT,self.sealed,self.named,doc=a)
 def test_web_review_cannot_become_official_network_attestation(self):
  a=copy.deepcopy(checked(ROOT,self.sealed,self.named))
  r=next(r for r in a["rows"] if r["evidence_grade"]=="OFFICIAL_LEAGUE_WEB_RESEARCH")
  r["official_network_verified"]=True
  with self.assertRaises(ArchiveRejected):checked(ROOT,self.sealed,self.named,doc=a)
 def test_no_fabricated_human_approval(self):
  a=copy.deepcopy(checked(ROOT,self.sealed,self.named))
  a["human_attestation_count"]=39
  with self.assertRaises(ArchiveRejected):checked(ROOT,self.sealed,self.named,doc=a)
 def test_second_daily_check_returns_exact_same_without_fresh_network(self):
  a=evaluate(ROOT);b=evaluate(ROOT)
  for k in ("registered","provisional_scored","pending","status_counts","per_model"):
   self.assertEqual(a[k],b[k])
  self.assertEqual(a["daily_external_csv_calls"]+b["daily_external_csv_calls"],0)

if __name__=="__main__":unittest.main()
