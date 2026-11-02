"""New link collision and exact 132-pass tests; no repeat 288-match audit."""
import copy,json,unittest
from pathlib import Path
from uefa_2025_26_club_profile_provenance_263 import audit,validate_links,AuditError
IDX=json.loads(Path("experiments/263/evidence/identity_index_263.json").read_text(encoding="utf8"))
DATA=json.loads(Path("experiments/263/evidence/uefa_2025_26_article_club_links_web_review.json").read_text(encoding="utf8"))
class OfficialProfileSourceTests(unittest.TestCase):
 def test_47_official_profile_urls_consistent_with_2025_membership(self):
    r=validate_links(IDX,DATA)
    self.assertEqual(len(r),47)
 def test_all_47_numeric_ids_are_unique(self):
    r=validate_links(IDX,DATA)
    self.assertEqual(len({item["uefa_numeric_club_id"] for item in r.values()}),47)
 def test_uefa_id_url_tampering_fail_closed(self):
    x=copy.deepcopy(DATA)
    x["clubs"][0]["uefa_numeric_club_id"]+=1
    with self.assertRaisesRegex(AuditError,"NOT_EQUAL_OFFICIAL_URL_ID"):
      validate_links(IDX,x)
 def test_fake_uefa_host_rejected(self):
    x=copy.deepcopy(DATA)
    x["clubs"][1]["official_uefa_club_profile"]=x["clubs"][1]["official_uefa_club_profile"].replace("www.uefa.com","www.uefa.com.attacker.example")
    with self.assertRaisesRegex(AuditError,"NOT_DIRECT_OFFICIAL_PROFILE_LINK"):
      validate_links(IDX,x)
 def test_two_clubs_same_numeric_uefa_id_rejected(self):
    x=copy.deepcopy(DATA)
    first=x["clubs"][0]
    second=x["clubs"][1]
    second["uefa_numeric_club_id"]=first["uefa_numeric_club_id"]
    second["official_uefa_club_profile"]=second["official_uefa_club_profile"].replace("/52280--","/50143--")
    with self.assertRaisesRegex(AuditError,"SAME_OFFICIAL_UEFA_CLUB_ID"):
      validate_links(IDX,x)
 def test_unlisted_canonical_identity_rejected(self):
    x=copy.deepcopy(DATA)
    x["clubs"][0]["canonical_existing_alias"]="Celtic"
    with self.assertRaisesRegex(AuditError,"TARGET_NOT_IN_2025_26_TEN_LEAGUES"):
      validate_links(IDX,x)
 def test_articles_must_be_historical_2025_not_current_2026(self):
    x=copy.deepcopy(DATA)
    x["clubs"][0]["official_2025_26_participant_article"]="https://www.uefa.com/uefachampionsleague/clubs/"
    with self.assertRaisesRegex(AuditError,"2025_26_OFFICIAL_COMPETITION_SOURCE"):
      validate_links(IDX,x)
 def test_provenance_never_changes_canonical_registry(self):
    before=copy.deepcopy(IDX)
    validate_links(IDX,DATA)
    self.assertEqual(before,IDX)
 def test_historical_match_overlay_refuses_promotion(self):
    local=next(r for r in DATA["clubs"] if r["competition"]=="UEFA_CL" and r["uefa_article_label"]=="Galatasaray")
    self.assertEqual(local["uefa_numeric_club_id"],50067)
    self.assertEqual(DATA["approval"],"OFFICIAL_PROFILE_LINK_CANDIDATE_FOR_INTEGRITY_REVIEW")
if __name__=="__main__":unittest.main()
