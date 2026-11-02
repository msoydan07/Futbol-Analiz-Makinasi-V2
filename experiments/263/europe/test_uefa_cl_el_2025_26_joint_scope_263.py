import json,unittest
from pathlib import Path
from uefa_cl_el_2025_26_joint_scope_263 import check
IDX=json.loads(Path("experiments/263/evidence/identity_index_263.json").read_text())
class CoverageChecks(unittest.TestCase):
 def test_two_known(self):
  cl=[{"home":"Galatasaray (TUR)","away":"Barcelona (ESP)","date":"2025-11-01","hg":1,"ag":2}]
  r,rows=check(cl,[],IDX)
  self.assertEqual(r["selected_name_candidates"],1)
  self.assertFalse(r["can_train_strength_model"])
  self.assertFalse(rows[0]["model_eligible"])
 def test_unknown_opponent_dropped(self):
  cl=[{"home":"Galatasaray (TUR)","away":"Celtic (SCO)","date":"2025-11-01","hg":1,"ag":2}]
  r,rows=check(cl,[],IDX)
  self.assertEqual(len(rows),0)
 def test_joint_two_matches(self):
  cl=[{"home":"Galatasaray (TUR)","away":"Barcelona (ESP)","date":"2025-11-01","hg":1,"ag":2}]
  el=[{"home":"Fenerbahçe","away":"Aston Villa","date":"2026-01-22",
       "home_goals":0,"away_goals":1}]
  r,rows=check(cl,el,IDX)
  self.assertEqual(len(rows),2)
  self.assertEqual(r["official_uefa_club_id_links_verified"],0)
 def test_invalid_index_rejected(self):
  with self.assertRaises(Exception):check([],[],{})
if __name__=="__main__":unittest.main()
