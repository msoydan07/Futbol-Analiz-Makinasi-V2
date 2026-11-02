"""Novel direct official URL, result, uniqueness, 132 integrity; no old experiments."""
import copy,json,unittest
from pathlib import Path
from uefa_2025_26_match_id_link_audit_263 import audit,club_slug_index,MatchAuditError
HOME=Path("experiments/263/evidence")
INDEX=json.loads((HOME/"identity_index_263.json").read_text())
PROFILES=json.loads((HOME/"uefa_2025_26_article_club_links_web_review.json").read_text())
MATCHES=json.loads((HOME/"uefa_cl_el_2025_26_official_132_match_links_web_review.json").read_text())
def synthetic_union():
    slug_ids=club_slug_index(INDEX,PROFILES)
    from uefa_2025_26_match_id_link_audit_263 import URL_SLUG_TO_PROFILE_SLUG
    results=[]
    for r in MATCHES["matches"]:
        comp=r["competition"];home,away=r["uefa_match_slug"].split("-vs-",1)
        alias=URL_SLUG_TO_PROFILE_SLUG[comp]
        results.append({"competition":comp,"season":"2025-2026",
                        "date":r["match_date"],"home_club_id_candidate":slug_ids[(comp,alias.get(home,home))],
                        "away_club_id_candidate":slug_ids[(comp,alias.get(away,away))],
                        "home_goals":r["source_score_home"],"away_goals":r["source_score_away"],
                        "model_training_allowed":False,
                        "identity_link_status":"REVIEW_ONLY_NOT_OFFICIAL_UEFA_NUMERIC_ID"})
    return {"schema":"263_UEFA_2025_26_BOTH_TEN_LEAGUES_UNION_COVERAGE_V1",
            "status":"REVIEW_ONLY_TRAINING_FORBIDDEN","matches":results}
class MatchLinkGuards(unittest.TestCase):
    def test_full_synthetic_132_mapping_internal(self):
        report,rows=audit(INDEX,PROFILES,MATCHES,synthetic_union())
        self.assertEqual(report["official_uefa_match_id_links_count"],132)
        self.assertEqual(report["uefa_linked_matches_by_competition"],{"UEFA_CL":95,"UEFA_EL":37})
        self.assertFalse(report["model_comparison_or_calibration_permitted"])
    def test_no_github_html_fetch_claim(self):
        self.assertFalse(MATCHES["claimed_independent_github_uefa_fetch"])
    def test_slug_unknown_team_rejected(self):
        m=copy.deepcopy(MATCHES)
        m["matches"][0]["uefa_match_slug"]="unknown-vs-juventus"
        r=m["matches"][0]
        r["official_uefa_match_url"]=r["official_uefa_match_url"].replace("monaco-vs-juventus","unknown-vs-juventus")
        with self.assertRaisesRegex(MatchAuditError,"NOT_TWO_IN_SCOPE"):
            audit(INDEX,PROFILES,m,synthetic_union())
    def test_score_conflict_rejected(self):
        m=copy.deepcopy(MATCHES);m["matches"][0]["source_score_home"]+=1
        with self.assertRaisesRegex(MatchAuditError,"SCORE_CONFLICT"):
            audit(INDEX,PROFILES,m,synthetic_union())
    def test_wrong_article_hand_off_rejected(self):
        m=copy.deepcopy(MATCHES);m["official_result_articles"]["UEFA_CL"]="https://example.com"
        with self.assertRaisesRegex(MatchAuditError,"PROVENANCE_INVALID"):
            audit(INDEX,PROFILES,m,synthetic_union())
    def test_fake_uefa_host_rejected(self):
        m=copy.deepcopy(MATCHES)
        m["matches"][0]["official_uefa_match_url"]=m["matches"][0]["official_uefa_match_url"].replace("www.uefa.com","www.uefa.com.attacker.com")
        with self.assertRaisesRegex(MatchAuditError,"MATCH_ID_URL_MISMATCH"):
            audit(INDEX,PROFILES,m,synthetic_union())
    def test_repeated_official_id_rejected(self):
        m=copy.deepcopy(MATCHES);m["matches"][1]["uefa_match_id"]=m["matches"][0]["uefa_match_id"]
        m["matches"][1]["official_uefa_match_url"]=m["matches"][1]["official_uefa_match_url"].replace("2046045","2046043")
        with self.assertRaisesRegex(MatchAuditError,"DUPLICATE_OFFICIAL_MATCH_ID"):
            audit(INDEX,PROFILES,m,synthetic_union())
    def test_wrong_side_rejected(self):
        m=copy.deepcopy(MATCHES);m["matches"][0]["uefa_match_slug"]="juventus-vs-monaco"
        m["matches"][0]["official_uefa_match_url"]=m["matches"][0]["official_uefa_match_url"].replace("monaco-vs-juventus","juventus-vs-monaco")
        with self.assertRaisesRegex(MatchAuditError,"NOT_ONE_TO_ONE"):
            audit(INDEX,PROFILES,m,synthetic_union())
    def test_wrong_date_rejected(self):
        m=copy.deepcopy(MATCHES);m["matches"][0]["match_date"]="2025-10-10"
        with self.assertRaisesRegex(MatchAuditError,"NOT_ONE_TO_ONE"):
            audit(INDEX,PROFILES,m,synthetic_union())
    def test_missing_records_rejected(self):
        m=copy.deepcopy(MATCHES);m["matches"].pop()
        with self.assertRaisesRegex(MatchAuditError,"NOT_132"):
            audit(INDEX,PROFILES,m,synthetic_union())
    def test_existing_canonical_registry_read_only(self):
        old=copy.deepcopy(INDEX)
        audit(INDEX,PROFILES,MATCHES,synthetic_union())
        self.assertEqual(INDEX,old)
if __name__=="__main__":unittest.main()
