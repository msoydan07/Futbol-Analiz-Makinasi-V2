"""Adversarial identity+provenance+same-day strength no-overclaim checks."""
import sys,unittest,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from public_scoreboard_provenance_audit import check,ProvenanceBlocked
from strength_conditioned_team_profile import opponent_band,audit,measure

ROOT=Path(__file__).resolve().parents[2]
class EvidenceTests(unittest.TestCase):
 def test_exact_provenance_counts_and_no_99_promotions(self):
  r=check(ROOT)
  self.assertEqual((r["candidate_total"],r["provider_official_scoreboard_concordant_28"],
    r["additional_public_scoreboard_only"],r["public_direct_league_or_federation_without_provider_match"],
    r["public_club_recap_without_provider_match"]), (99,28,28,19,9))
  self.assertEqual(r["accepted_new_history_rows"],0)
  self.assertEqual(r["pending_provider_plus_public_per_fixture_match_count"],71)
  self.assertFalse(r["new_28_same_supplier_row_rejoined"])
 def test_wrong_score_source_tier_must_fail(self):
  p=ROOT/"research/opponent_goals/public_matchday_28_more_20261110.json"
  x=json.loads(p.read_text(encoding="utf8"))
  self.assertEqual(x["records"][0]["status"],"PUBLIC_WEB_PAGE_SCORE_NOT_PROVIDER_SHA_REJOINED")
 def test_opponent_rating_is_directional(self):
  self.assertEqual(opponent_band(-180),"opponent_150_plus")
  self.assertEqual(opponent_band(180),"team_150_plus")
 def test_min_history_must_disallow_confident_tactical_claim(self):
  self.assertEqual(measure([dict(gf=1,ga=0,pts=3,btts=0,over25=0,
   shot_team=10,shot_opp=5,both_prior_8plus=True)])["quality_flag"],
      "TOO_FEW_FOR_OPPONENT_STYLE_OR_INDEPENDENT_PROBABILITY")
 def test_team_profile_has_no_current_match_info(self):
  r=audit(ROOT)
  self.assertEqual(r["past_accepted_matches"],4518)
  self.assertFalse(r["not_a_live_match_forecast"]==False)
  self.assertTrue(r["opponent_strength_proxy_is_not_formation_or_pressing"])
  self.assertEqual(len(r["example_besiktas"]["HOME"]),5)
if __name__=="__main__":unittest.main()
