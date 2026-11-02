"""Only NEW combined same-season sample/coverage/identity safety checks."""
from __future__ import annotations
import copy,json,unittest
from pathlib import Path
from uefa_cl_el_union_scope_263 import (
    CL_NAME_CROSSWALK,CL_RESULT_ANCHORS,
    UnionCoverageError,partition_cl,canonical_membership,render_markdown,
    resolve_cl_name,verified_cl_source,combine_same_season
)

INDEX=json.loads(Path("experiments/263/evidence/identity_index_263.json").read_text(encoding="utf-8"))
class SameSeasonUnionChecks(unittest.TestCase):
    def test_curated_all_exact_membership_only_from_2025_26(self):
        ix=copy.deepcopy(INDEX)
        membership=canonical_membership(ix)
        for expanded,(short,country) in CL_NAME_CROSSWALK.items():
            with self.subTest(expanded=expanded):
                got,kind=resolve_cl_name(expanded+" ("+country+")",ix,membership)
                self.assertEqual(kind,"CURATED_UEFA_SOURCE_TO_DOMESTIC_ALIAS_ID_UNVERIFIED")
                self.assertIsNotNone(got)
                self.assertIn(got["team_id"],membership)
        self.assertEqual(ix,INDEX)
        self.assertEqual(len(CL_NAME_CROSSWALK),19)
    def test_monaco_mco_is_french_league_not_discarded_by_country(self):
        m=canonical_membership(INDEX)
        result,_=resolve_cl_name("AS Monaco FC (MCO)",INDEX,m)
        self.assertEqual(result["league"],"FRA1")
    def test_country_marker_alias_conflict_must_fail_closed(self):
        m=canonical_membership(INDEX)
        with self.assertRaisesRegex(UnionCoverageError,"COUNTRY_MARKER_CONFLICT"):
            resolve_cl_name("Arsenal FC (TUR)",INDEX,m)
    def test_2026_27_season_is_not_2025_26_proxy(self):
        m=canonical_membership(INDEX)
        self.assertEqual(set(m.values()),set(INDEX["season_memberships"]["2025-2026"]))
        self.assertNotIn("AS Roma WRONG",INDEX["aliases"])
    def test_unknown_source_name_never_guessed(self):
        m=canonical_membership(INDEX)
        got,_=resolve_cl_name("Unrelated FC (ENG)",INDEX,m)
        self.assertIsNone(got)
    def test_uefa_cl_anchor_checks_are_predeclared_and_conservative(self):
        self.assertEqual(len(CL_RESULT_ANCHORS),6)
        self.assertIn(("2025-09-30","Galatasaray SK (TUR)","Liverpool FC (ENG)",1,0),CL_RESULT_ANCHORS)
    def test_no_repeat_club_identity_from_curated_links(self):
        aliases=[]
        for full,(short,marker) in CL_NAME_CROSSWALK.items():
            club,_=resolve_cl_name(full+" ("+marker+")",INDEX,canonical_membership(INDEX))
            aliases.append(club["team_id"])
        self.assertEqual(len(set(aliases)),19)
    def test_union_requires_raw_source_bytes(self):
        with self.assertRaisesRegex(UnionCoverageError,"TWO_RAW_SOURCES_REQUIRED"):
            combine_same_season(None,None,INDEX)
    def test_cl_parser_refuses_arbitrary_fake_source_and_scores(self):
        with self.assertRaises(Exception):
            verified_cl_source(b"not official results")
    def test_union_summary_is_explicitly_review_only(self):
        report={"coverage":{"CL":{"games_retained":50,"curated_source_name_clubs_in_ten_leagues":19},
                    "EL":{"2025_26_both_in_ten_leagues_name_candidates":37},
                    "both_clubs_in_ten_league_name_review_candidates":87,
                    "source_games_excluded_by_scope_or_identity":201,
                    "candidate_uefa_leagues_present":["ENG1"],
                    "candidate_leagues_without_uefa_match":["ENG2"]}}
        text=render_markdown(report)
        self.assertIn("REVIEW-ONLY",text.upper())
        self.assertIn("NO",text)
        self.assertIn("288",text)
if __name__=="__main__":unittest.main()
