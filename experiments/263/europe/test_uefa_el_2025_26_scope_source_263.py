"""EL 2025/26 public source safety; exact source anchors, no fitting."""
import copy,hashlib,unittest
from uefa_el_2025_26_scope_source_263 import (
    decode_feed,audit_ten_league_scope,CohortError,EXPECTED_MATCHES,
    UEFA_REFERENCE_ANCHORS
)
from uefa_ten_league_scope_gate_263 import norm
def fixture(md,home,away,hg,ag,idx):
    days={1:"2025-09-24",2:"2025-10-02",3:"2025-10-23",4:"2025-11-06",
          5:"2025-11-27",6:"2025-12-11",7:"2026-01-22",8:"2026-01-29"}
    return {"MatchNumber":idx,"RoundNumber":md,"DateUtc":days[md]+" 19:00:00Z",
            "HomeTeam":home,"AwayTeam":away,"HomeTeamScore":hg,"AwayTeamScore":ag}
class ElSourceSafety(unittest.TestCase):
    def fake_index(self):
        leagues=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
        return {"index_type":"CANONICAL_REGISTRY_READ_ONLY_IDENTITY_CACHE_V1",
         "teams":{k:{"name":k} for k in ("a","b","c")},
         "aliases":{"aston villa":"a","bologna":"b","celtic":"c"},
         "season_memberships":{s:{lg:(["a","b"] if lg=="ENG1" else [])
                 for lg in leagues} for s in ("2025-2026","2026-2027")}}
    def test_unseen_external_club_is_not_invented_or_trained(self):
        idx=self.fake_index()
        rows=[{"home":"Aston Villa","away":"Bologna","match_provider_id":1},
              {"home":"Aston Villa","away":"Celtic","match_provider_id":2},
              {"home":"Aston Villa","away":"Unknown FC","match_provider_id":3}]
        before=copy.deepcopy(idx)
        report,subset=audit_ten_league_scope(rows,idx,"0"*64)
        self.assertEqual(report["coverage"]["2025_26_both_in_ten_leagues_name_candidates"],1)
        self.assertEqual(report["coverage"]["approved_for_cross_league_model"],0)
        self.assertFalse(report["model_train_permitted"])
        self.assertFalse(subset[0]["official_uefa_team_id_crosswalk_verified"])
        self.assertEqual(idx,before)
    def test_bad_sha_rejected(self):
        with self.assertRaisesRegex(CohortError,"SHA256_REQUIRED"):
            audit_ten_league_scope([],self.fake_index(),"BAD")
    def test_null_score_rejected(self):
        rows=[fixture(1,"Aston Villa","Bologna",None,1,1) for _ in range(144)]
        import json
        with self.assertRaisesRegex(CohortError,"UNPLAYED_OR_INVALID_GOALS"):
            decode_feed(json.dumps(rows).encode())
    def test_incomplete_144_matches_rejected(self):
        import json
        rows=[fixture(1,"Aston Villa","Bologna",1,0,i) for i in range(144)]
        with self.assertRaises(CohortError):
            decode_feed(json.dumps(rows).encode())
    def test_unknown_future_2026_results_not_accepted(self):
        import json
        rows=[fixture(1,"Aston Villa","Bologna",1,0,i) for i in range(144)]
        rows[0]["DateUtc"]="2026-09-25 19:00:00Z"
        with self.assertRaisesRegex(CohortError,"UNEXPECTED_CALENDAR_DAY"):
            decode_feed(json.dumps(rows).encode())
    def test_official_uefa_anchor_count_is_explicit(self):
        self.assertEqual(len(UEFA_REFERENCE_ANCHORS),6)
        self.assertIn(("2026-01-22","Fenerbahçe","Aston Villa",0,1),UEFA_REFERENCE_ANCHORS)
    def test_provider_unfamiliar_alias_does_not_get_fuzzy_guessed(self):
        idx=self.fake_index()
        rows=[{"home":"Aston Villa FC","away":"Bologna","match_provider_id":1}]
        rep,subset=audit_ten_league_scope(rows,idx,"a"*64)
        self.assertEqual(len(subset),0)
        self.assertEqual(rep["coverage"]["excluded_reasons"]["UNKNOWN_NAME_NO_RESEARCH"],1)
    def test_only_league_phase_counts(self):
        self.assertEqual(EXPECTED_MATCHES,144)
if __name__=="__main__":unittest.main()
