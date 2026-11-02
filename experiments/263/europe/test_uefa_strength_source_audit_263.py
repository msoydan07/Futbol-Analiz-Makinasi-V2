"""Independent safety checks for new 432-game cross-league identity review."""
import copy
import unittest
from uefa_strength_source_audit_263 import (
    CoverageError,split_uefa_club,label_review,validate_index,review_csv,
)
class SourceAuditTests(unittest.TestCase):
    def index(self):
        ids={"alpha":"alpha-uuid","beta":"beta-uuid"}
        return {"index_type":"CANONICAL_REGISTRY_READ_ONLY_IDENTITY_CACHE_V1",
            "teams":{"alpha-uuid":{"name":"Aston Villa"},"beta-uuid":{"name":"Other"}},
            "aliases":{"aston villa":"alpha-uuid","other":"beta-uuid"},
            "season_memberships":{season:{
                league:(["alpha-uuid"] if league=="ENG1" else [])
                for league in ("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")}
                for season in ("2025-2026","2026-2027")}}
    def test_uefa_country_marker_not_assumed_as_domestic_membership(self):
        self.assertEqual(split_uefa_club("Aston Villa (ENG)"),("Aston Villa","ENG"))
        idx=self.index();before=copy.deepcopy(idx)
        row=label_review("Aston Villa (ENG)",idx)
        self.assertEqual(idx,before)
        self.assertEqual(row["status"],"EXACT_NAME_CANDIDATE_NOT_VERIFIED")
        self.assertFalse(row["uefa_identity_approved"])
        self.assertFalse(row["historical_2024_25_membership_verified"])
        self.assertEqual(len(row["candidate_domestic_memberships_2025_27_only"]),2)
    def test_no_fuzzy_matching_or_country_based_guessed_id(self):
        row=label_review("Aston Villa FC (ENG)",self.index())
        self.assertIsNone(row["candidate_canonical_id_DO_NOT_USE_IN_MODEL"])
        self.assertEqual(row["status"],"NO_EXACT_NAME_NEEDS_MANUAL_REVIEW")
    def test_foreign_country_does_not_force_unknown_or_fake_name(self):
        row=label_review("Other (SCO)",self.index())
        self.assertFalse(row["country_in_ten_league_universe"])
        self.assertFalse(row["uefa_identity_approved"])
    def test_missing_country_rejected_not_silent(self):
        with self.assertRaises(CoverageError):split_uefa_club("Aston Villa")
    def test_index_wrong_universe_rejected(self):
        d=self.index();del d["season_memberships"]["2026-2027"]["ENG1"]
        with self.assertRaisesRegex(CoverageError,"UNEXPECTED_DOMESTIC_LEAGUES"):
            validate_index(d)
    def test_csv_explicit_unverified_label(self):
        row=label_review("Aston Villa (ENG)",self.index())
        csvtext=review_csv({"review_rows":[{**row,"participant_appearances_in_three_cohorts":8}]})
        self.assertIn("EXACT_NAME_CANDIDATE_NOT_VERIFIED",csvtext)
        self.assertIn("2025-2026/ENG1",csvtext)
    def test_non_uefa_or_malformed_club_names_rejected(self):
        for value in ("Galatasaray"," (TUR)","Galatasaray (Turkey)"):
            with self.subTest(value=value),self.assertRaises(CoverageError):
                split_uefa_club(value)
if __name__=="__main__":unittest.main()
