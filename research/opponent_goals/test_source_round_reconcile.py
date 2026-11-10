"""Offline adversarial checks. NEVER call external supplier in tests."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from source_round_reconcile import candidate_index,match_official,verify_ledger,ReconcileBlocked
from source_current_one_shot_preflight import rows_from_source

ROOT=Path(__file__).resolve().parents[2]
class Tests(unittest.TestCase):
    def test_28_official_rows_have_real_alias_ids_and_are_not_in_archive(self):
        import json
        hist,_,_=__import__("data_opponent_goal_audit").read_rows(ROOT/"data/quad_accepted_263/extended_history.csv")
        registry=json.loads((ROOT/"experiments/263/evidence/identity_index_263.json").read_text(encoding="utf8"))
        ledger=json.loads((ROOT/"research/opponent_goals/official_rounds_nov06_08_2026.json").read_text(encoding="utf8"))
        self.assertEqual(len(verify_ledger(ledger,registry,hist)),28)
    def test_candidate_identity_no_wrong_team_fuzzy_join(self):
        data=rows_from_source(b"Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n07/11/2026,A,B,2,1,H\n")
        old=[dict(league="ENG1",match_date="2026-11-02")]
        got,errors=candidate_index("ENG1",data,old,{"A":set(),"a":{"id-a"},"b":{"id-b"}})
        self.assertEqual(len(got),1)
        self.assertEqual(errors,{})
    def test_one_mismatched_score_never_accepted(self):
        official={("ENG1","2026-11-07","A","B"):{"home_goals":2,"away_goals":1,"official_week_source":"https://tff.org/f"}}
        supplier={("ENG1","2026-11-07","A","B"):{"home_goals":3,"away_goals":1,"source_row":42}}
        passed,conflicts=match_official(official,supplier)
        self.assertEqual(passed,[])
        self.assertEqual(conflicts[0]["reason"],"OFFICIAL_PROVIDER_FINAL_SCORE_DISAGREEMENT")
    def test_ambiguous_team_name_never_resolves(self):
        feed=rows_from_source(b"Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n07/11/2026,A,B,2,1,H\n")
        got,errors=candidate_index("ENG1",feed,[dict(league="ENG1",match_date="2026-11-02")],
                      {"a":{"id-a1","id-a2"},"b":{"id-b"}})
        self.assertEqual(len(got),0)
        self.assertEqual(errors["CANONICAL_ID_UNRESOLVED"],1)

if __name__=="__main__":unittest.main()
