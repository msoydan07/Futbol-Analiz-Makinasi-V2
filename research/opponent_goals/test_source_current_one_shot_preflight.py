"""No external requests: adversarial provider schema and source-row anchor checks."""
import sys,unittest,io,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from source_current_one_shot_preflight import rows_from_source,parse_day,validate_old_anchor,inspect_feed
class OneShotTests(unittest.TestCase):
    def test_date_formats(self):
        self.assertEqual(parse_day("10/11/2026"),"2026-11-10")
        self.assertEqual(parse_day("10/11/26"),"2026-11-10")
        self.assertIsNone(parse_day("impossible"))
    def test_source_row_shift_blocks_identity(self):
        data=rows_from_source(b"Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n01/08/2026,A,B,1,0,H\n")
        hist=[dict(league="ENG1",season="2026-2027",
             source_row="2",source_url="https://www.football-data.co.uk/mmz4281/2627/E0.csv",
             match_date="2026-08-01",home_goals="3",away_goals="0",result="H",
             home_id="uuid-a",away_id="uuid-b")]
        safe,ok,total,reasons,_=validate_old_anchor("ENG1","E0",data,hist)
        self.assertFalse(safe)
        self.assertEqual(ok,0)
        self.assertEqual(reasons["HISTORICAL_ANCHOR_CHANGED"],1)
    def test_limited_anchor_is_not_enough_for_source_identity(self):
        data=b"Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n01/08/2026,A,B,1,0,H\n05/08/2026,A,B,2,0,H\n"
        hist=[dict(league="ENG1",season="2026-2027",source_row="2",
            source_url="https://www.football-data.co.uk/mmz4281/2627/E0.csv",
            match_date="2026-08-01",home_goals="1",away_goals="0",result="H",
            home_id="uuid-a",away_id="uuid-b")]
        r=inspect_feed("ENG1","E0",data,hist)
        self.assertFalse(r["safe_historical_name_to_id_crosswalk"])
        self.assertEqual(r["newer_completed_score_rows_candidate_count"],1)
        self.assertEqual(r["historical_exact_row_score_date_anchors"],1)
        self.assertEqual(r["newer_candidate_provisional_identity_summary"]["HISTORICAL_SOURCE_CROSSWALK_NOT_ACCEPTED"],1)
if __name__=="__main__":unittest.main()
