"""Only NEW goal-input and provenance invariants, no old model reruns."""
import copy
import unittest
from datetime import date
from uefa_goal_only_asof_feature_readiness_263 import goals_features,load_locked_history,ReadinessError

def row(day,home="H",away="C",league="ENG1",season="2025-2026",hg=2,ag=1):
    return {"fixture_id":day+home+away,"date":date.fromisoformat(day),"league":league,
            "season":season,"home_id":home,"away_id":away,"home_goals":hg,"away_goals":ag}
def fixture():
    return {"uefa_official_match_id":2045927,"date":"2025-10-10",
            "competition":"UEFA_CL","home_id_candidate":"H","away_id_candidate":"A"}
def idx():
    leagues={s:{k:[] for k in ("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")}
             for s in ("2025-2026","2026-2027")}
    for s in leagues:
        leagues[s]["ENG1"]=["H","C"];leagues[s]["TUR1"]=["A","D"]
    return {"index_type":"CANONICAL_REGISTRY_READ_ONLY_IDENTITY_CACHE_V1",
            "teams":{t:{"name":t} for t in ("H","A","C","D")},
            "aliases":{"home":"H","away":"A"},
            "season_memberships":leagues}
class NewGoalOnlyFeatureGuards(unittest.TestCase):
    def test_same_day_and_later_goals_excluded(self):
        old=[row("2025-10-01"),row("2025-10-10",hg=15),
             row("2025-10-11",hg=21),
             row("2025-10-01",home="A",away="D",league="TUR1",hg=3)]
        rep,m=goals_features(old,[fixture()],idx()) if False else (None,None)
        # Our function refuses incomplete 132; synthetic tests use pure
        # deterministic fixture replication with unique match IDs.
        f=[{**fixture(),"uefa_official_match_id":3000000+i} for i in range(95)]
        f+=[{**fixture(),"competition":"UEFA_EL","uefa_official_match_id":4000000+i} for i in range(37)]
        rep,m=goals_features(old,f,idx())
        g=m[0]["team_goals_inputs"]["home"]
        self.assertEqual(g["past_domestic_games"],1)
        self.assertEqual(g["past_team_scored_goals"],2)
        self.assertFalse(m[0]["asof_source_publication_time_proven"])
    def test_all_data_after_cutoff_cannot_change_prior_features(self):
        before=[row("2025-10-01"),row("2025-10-01",home="A",away="D",league="TUR1")]
        f=[{**fixture(),"uefa_official_match_id":3000000+i} for i in range(95)]
        f+=[{**fixture(),"competition":"UEFA_EL","uefa_official_match_id":4000000+i} for i in range(37)]
        _,original=goals_features(before,f,idx())
        after=before+[row("2025-10-20",hg=30,ag=0)]
        _,mutated=goals_features(after,f,idx())
        self.assertEqual(original,mutated)
    def test_unknown_team_membership_rejected(self):
        f=[{**fixture(),"away_id_candidate":"FOREIGN","uefa_official_match_id":3000000+i} for i in range(95)]
        f+=[{**fixture(),"competition":"UEFA_EL","away_id_candidate":"FOREIGN",
             "uefa_official_match_id":4000000+i} for i in range(37)]
        with self.assertRaisesRegex(ReadinessError,"OUTSIDE_2025_26"):
            goals_features([],f,idx())
    def test_empty_histories_not_silent_zero_references(self):
        f=[{**fixture(),"uefa_official_match_id":3000000+i} for i in range(95)]
        f+=[{**fixture(),"competition":"UEFA_EL","uefa_official_match_id":4000000+i} for i in range(37)]
        report,rows=goals_features([],f,idx())
        self.assertEqual(rows[0]["team_goals_inputs"]["home"]["domestic_league_home_goals_per_game_before_target"],None)
        self.assertEqual(report["by_competition"]["UEFA_CL"]["both_4_plus_past_goal_games"],0)
        self.assertFalse(report["candidate_model_training_approved"])
        self.assertFalse(report["xg_proxy_constructed"])
    def test_archived_csv_alone_cannot_prove_retrievability(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"spoof.csv";p.write_text("fixture_id,league")
            with self.assertRaisesRegex(ReadinessError,"SHA_MISMATCH"):
                load_locked_history(p)
if __name__=="__main__":unittest.main()
