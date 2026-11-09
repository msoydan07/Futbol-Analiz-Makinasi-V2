"""Offline invariants for real-history forecast engine."""
import csv,gzip,io,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sources import Game,SourceError,nba_games,euroleague_games,eurocup_games,check
from engine import Ratings,replay,before_game
from benchmark import grade,choose_dev
class Tests(unittest.TestCase):
    def test_nba_archive_does_not_reuse_external_model_or_current_box(self):
        doc={"season":2025,"games":[
            {"id":"1","type":2,"date":"2024-11-04T00:20:00+00:00",
             "home":"NY","away":"BOS","home_score":110,"away_score":105,
             "p_model":.999,"box_home":{"pts":1000}},
            {"id":"2","type":3,"date":"2024-11-04T02:00:00+00:00",
             "home":"NY","away":"BOS","home_score":150,"away_score":100}]}
        g=nba_games(doc,2025)
        self.assertEqual(len(g),1)
        self.assertEqual(g[0].day,"2024-11-03")
        self.assertEqual(g[0].margin,5)
    def test_nba_cup_final_excluded_from_regular_season(self):
        game=lambda n,phase:{"id":str(n),"type":2,"phase":phase,
          "date":"2024-12-19T00:00:00+00:00","home":"NY","away":"BOS",
          "home_score":111,"away_score":99}
        rs=nba_games({"season":2025,"games":[game(1,"Final"),game(2,"NBA Cup Championship")]},2025)
        self.assertEqual([g.game_id for g in rs],["1"])
    def test_euroleague_gzip_parsing_regular_season_only(self):
        stream=io.StringIO()
        w=csv.writer(stream);w.writerow(["season","game_id","date","phase","home","away","home_score","away_score","neutral"])
        w.writerow([2025,1,"2025-10-08","RS","OLY","FEN",90,80,0])
        w.writerow([2025,2,"2025-10-09","PO","FEN","OLY",95,85,0])
        g=euroleague_games(gzip.compress(stream.getvalue().encode()),2025)
        self.assertEqual(len(g),1);self.assertEqual(g[0].home,"OLY")
        with self.assertRaises(SourceError):
            euroleague_games(gzip.compress(b"nonCSV"),2025)
    def test_eurocup_results_only_played_unchanged_regular_season(self):
        row={"season":{"code":"U2025"},"gameCode":1,"played":True,
             "phaseType":{"code":"RS"},"localDate":"2025-10-10T18:00:00",
             "local":{"club":{"code":"ULM"},"score":92},
             "road":{"club":{"code":"BDK"},"score":84},"isNeutralVenue":False}
        x=eurocup_games({"data":[row,{**row,"played":False,"gameCode":2}],"total":2},2025)
        self.assertEqual(len(x),1)
        self.assertEqual(x[0].total,176)
        with self.assertRaises(SourceError):
            eurocup_games({"data":[row],"total":25},2025)
    def test_same_day_cannot_peek_other_results(self):
        a=Game("NBA",2025,"2024-11-01","1","AA","BB",140,80)
        b=Game("NBA",2025,"2024-11-01","2","CC","DD",80,140)
        c=Game("NBA",2025,"2024-11-02","3","AA","CC",112,100)
        x=replay([a,b,c])
        y=replay([a,Game("NBA",2025,"2024-11-01","2","CC","DD",150,50),c])
        get=lambda rows,gid:{p.variant:(p.margin,p.total) for g,p in rows if g.game_id==gid}
        self.assertEqual(get(x,"1"),get(y,"1"))
        self.assertEqual(get(x,"2"),get(y,"2"))
        self.assertNotEqual(get(x,"3"),get(y,"3"))
    def test_before_game_never_sees_current_or_future_scores(self):
        a=Game("NBA",2025,"2024-11-01","1","AA","BB",140,80)
        b=Game("NBA",2025,"2024-11-08","2","AA","BB",80,140)
        p=before_game([a,b],"NBA",2025,"2024-11-07","AA","BB")
        q=before_game([a,Game("NBA",2025,"2024-11-08","2","AA","BB",210,20)],
                     "NBA",2025,"2024-11-07","AA","BB")
        self.assertEqual(p["HYBRID"].json(),q["HYBRID"].json())
    def test_probabilities_and_sums_coherent(self):
        e=Ratings("NBA");e.start_season(2025)
        p=e.predict(2025,"2024-11-01","AA","BB")["HYBRID"]
        self.assertAlmostEqual(p.home_score+p.away_score,p.total)
        self.assertAlmostEqual(p.home_score-p.away_score,p.margin)
        self.assertAlmostEqual(p.over(220.5)+1-p.over(220.5),1)
        self.assertAlmostEqual(p.cover(-4.5)+1-p.cover(-4.5),1)
        with self.assertRaises(ValueError):p.over(220)
    def test_no_ties_no_duplicates(self):
        with self.assertRaises(SourceError):
            check(Game("EL",2024,"2024-01-01","1","AA","BB",80,80))
        a=Game("NBA",2025,"2024-11-01","1","AA","BB",100,90)
        with self.assertRaises(ValueError):replay([a,a])
    def test_model_selection_dev_only_and_empty_metrics(self):
        self.assertIsNone(grade([])["accuracy"])
        base={"n":200,"brier":.25,"margin_mae":10,"total_mae":15}
        better={**base,"brier":.21,"margin_mae":9,"total_mae":13}
        v={"BASE":base,"ELO":better,"FORM":base,"HYBRID":base}
        self.assertEqual(choose_dev(v)[0],"ELO")
        with self.assertRaises(ValueError):
            choose_dev({k:{**z,"n":90} for k,z in v.items()})
if __name__=="__main__":unittest.main()
