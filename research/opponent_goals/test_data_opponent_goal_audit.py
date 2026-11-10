"""Synthetic no-leakage, scope and strength-band tests; do not fake real evidence."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from data_opponent_goal_audit import strength_band,past_only_elo,strength_metrics,audit,SourceBlocked

def row(i,day,home,away,h,a,league="ENG1",shots_h="10",shots_a="8"):
    return dict(fixture_id=str(i),match_date=day,season="2025-2026",league=league,
                home_id=home,away_id=away,home_goals=str(h),away_goals=str(a),
                home_shots=shots_h,away_shots=shots_a,result=("H" if h>a else "A" if a>h else "D"))

class DataTests(unittest.TestCase):
    def test_directional_bands(self):
        self.assertEqual(strength_band(-160),"away_150_plus")
        self.assertEqual(strength_band(160),"home_150_plus")
        self.assertEqual(strength_band(0),"close_under_50")
        self.assertEqual(strength_band(-50),"away_50_to_150")
    def test_same_match_date_does_not_consume_results(self):
        rows=[row(1,"2025-08-01","A","B",4,0),row(2,"2025-08-01","A","C",0,3),
             row(3,"2025-08-08","A","B",1,1)]
        s=past_only_elo(rows)
        self.assertEqual(s["1"]["home_pre_rating"],1500)
        self.assertEqual(s["2"]["home_pre_rating"],1500)
        self.assertNotEqual(s["3"]["home_pre_rating"],1500)
    def test_league_elo_isolation(self):
        s=past_only_elo([row(1,"2025-08-01","A","B",4,0),
                         row(2,"2025-08-08","A","C",2,0,"GER1")])
        self.assertEqual(s["2"]["home_pre_rating"],1500)
    def test_descriptive_shot_coverage(self):
        rows=[row(1,"2025-08-01","A","B",1,1,shots_h="",shots_a="")]
        ans=strength_metrics(rows,past_only_elo(rows))
        self.assertEqual(ans["ALL/close_under_50"]["shot_share_n"],0)
        self.assertIsNone(ans["ALL/close_under_50"]["home_shot_share_avg"])
    def test_source_sha_fixed_and_ten_leagues(self):
        # Original source bytes + 10 leagues prove inventory is derived from real archive.
        result=audit("data/quad_accepted_263/extended_history.csv")
        self.assertEqual(result["match_count"],4518)
        self.assertEqual(len(result["leagues"]),10)
        self.assertNotIn("xG",result["leagues"]["ENG1"]["statistics"])
if __name__=="__main__":unittest.main()
