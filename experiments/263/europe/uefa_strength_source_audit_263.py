"""2.6.3 independent UEFA-to-domestic identity COVERAGE audit only.

Audits three SHA-anchored historical UEFA league-phase files (432 fixtures)
against the frozen read-only 10-league identity index. Exact normalized name
overlap creates a REVIEW CANDIDATE, never an approved UEFA-to-domestic link.
No approximate/fuzzy aliases. No ratings, future UEFA results, model predictions,
new registrations, H2H features, modifications to domestic files, or pilot.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import re
from pathlib import Path

from uefa_tactical_study_263 import (
    SOURCES, SOURCE_COMMIT, fetch_pinned_source,
    parse_league_phase, validate_source_rows, StudyError,
)

VERSION = "263_UEFA_CROSS_LEAGUE_SOURCE_COVERAGE_V1"
INDEX_TYPE = "CANONICAL_REGISTRY_READ_ONLY_IDENTITY_CACHE_V1"
# The UEFA source country marker is an annotation, NOT a league membership.
COUNTRIES_IN_TEN = {"ENG","GER","ESP","ITA","FRA","NED","TUR","POR","BEL"}
PARTICIPANT_RE = re.compile(r"^(?P<club>.+)\s+\((?P<country>[A-Z]{3})\)$")


class CoverageError(ValueError):
    pass


def normalized(value: str) -> str:
    import unicodedata
    if not isinstance(value,str) or not value.strip():
        raise CoverageError("EMPTY_NAME")
    clean = unicodedata.normalize("NFKC",value).casefold()
    clean = "".join(ch for ch in unicodedata.normalize("NFKD",clean)
                    if not unicodedata.combining(ch))
    return re.sub(r"\s+"," ",clean).strip()


def split_uefa_club(raw: str):
    if not isinstance(raw,str):
        raise CoverageError("INVALID_UEFA_CLUB_NAME")
    m=PARTICIPANT_RE.fullmatch(raw)
    if not m or not m.group("club").strip():
        raise CoverageError("CLUB_COUNTRY_MARKER_REQUIRED_FOR_REVIEW")
    return m.group("club").strip(), m.group("country")


def validate_index(index: dict):
    if (not isinstance(index,dict) or index.get("index_type")!=INDEX_TYPE):
        raise CoverageError("EXPECTED_FROZEN_CANONICAL_INDEX")
    teams=index.get("teams");aliases=index.get("aliases")
    memberships=index.get("season_memberships")
    if not isinstance(teams,dict) or not isinstance(aliases,dict) or not isinstance(memberships,dict):
        raise CoverageError("INDEX_FIELDS_MISSING")
    if set(memberships)!={"2025-2026","2026-2027"}:
        raise CoverageError("EXPECTED_TEN_LEAGUE_TWO_SEASON_SCOPE")
    for season, leagues in memberships.items():
        if set(leagues)!={"ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1"}:
            raise CoverageError("UNEXPECTED_DOMESTIC_LEAGUES")
        for club_ids in leagues.values():
            if not isinstance(club_ids,list) or not set(club_ids)<=set(teams):
                raise CoverageError("BROKEN_MEMBERSHIP_IDS")
    if any(v not in teams for v in aliases.values()):
        raise CoverageError("BROKEN_ALIAS_IDS")


def label_review(label: str, index: dict) -> dict:
    club,country=split_uefa_club(label)
    candidate=index["aliases"].get(normalized(club))
    if candidate is not None and candidate not in index["teams"]:
        raise CoverageError("INDEX_ALIAS_REFERENCES_UNKNOWN_TEAM")
    memberships=[]
    if candidate:
        for season,leagues in index["season_memberships"].items():
            for league,ids in leagues.items():
                if candidate in ids:
                    memberships.append(season+"/"+league)
    return {
        "uefa_source_label":label,"uefa_club_name":club,
        "source_country_marker":country,
        "country_in_ten_league_universe":country in COUNTRIES_IN_TEN,
        "status":("EXACT_NAME_CANDIDATE_NOT_VERIFIED" if candidate else
                  "NO_EXACT_NAME_NEEDS_MANUAL_REVIEW"),
        "candidate_canonical_id_DO_NOT_USE_IN_MODEL":candidate,
        "candidate_domestic_name_DO_NOT_USE_IN_MODEL":index["teams"][candidate]["name"] if candidate else None,
        "candidate_domestic_memberships_2025_27_only":sorted(memberships),
        "historical_2024_25_membership_verified":False,
        "uefa_identity_approved":False,
    }


def source_audit(texts:dict[str,bytes], index:dict):
    validate_index(index)
    if set(texts)!={row[0] for row in SOURCES.values()}:
        raise CoverageError("EXPECTED_EXACTLY_THREE_PINNED_SOURCES")
    all_labels=collections.Counter()
    provenance=[]
    cohorts={}
    by_match=[]
    for (competition,season),(file,expected_matches,expected_goals) in SOURCES.items():
        payload=texts[file]
        if not isinstance(payload,bytes):
            raise CoverageError("EXPECTED_BYTES_INPUT")
        try:
            games=parse_league_phase(payload,competition,season)
            verified_shape=validate_source_rows(games,competition,season,expected_matches,expected_goals)
        except (StudyError,UnicodeError) as exc:
            raise CoverageError("HISTORIC_UEFA_SOURCE_SHAPE_REJECTED") from exc
        digest=hashlib.sha256(payload).hexdigest()
        provenance.append({
            **verified_shape,
            "source_relative":file,
            "pinned_commit":SOURCE_COMMIT,
            "source_sha256":digest,
            "official_aggregate_match_goals_parity_only":True,
            "each_match_independently_officially_verified":False,
        })
        cohorts[competition+"/"+season]={"matches":len(games),"goals":sum(x["total_goals"] for x in games)}
        for match in games:
            for side in ("home","away"):
                split_uefa_club(match[side])
                all_labels[match[side]]+=1
            by_match.append((competition,season,match["home"],match["away"]))
    clubs=[{**label_review(label,index),"participant_appearances_in_three_cohorts":n}
           for label,n in sorted(all_labels.items())]
    statuses=collections.Counter(r["status"] for r in clubs)
    country_counts=collections.Counter(r["source_country_marker"] for r in clubs)
    matched={r["uefa_source_label"] for r in clubs if r["status"]=="EXACT_NAME_CANDIDATE_NOT_VERIFIED"}
    matches_per_cohort=collections.Counter()
    for competition,season,home,away in by_match:
        if home in matched and away in matched:
            matches_per_cohort[competition+"/"+season]+=1
    # No historical team can be approved from a matching text string alone.
    result={
        "schema":VERSION,
        "status":"SOURCE_AND_IDENTITY_COVERAGE_ONLY_UNVERIFIED",
        "source":{"repository":"openfootball/champions-league",
                  "immutable_commit":SOURCE_COMMIT,
                  "corpora":provenance,
                  "match_by_match_UEFA_verification":False},
        "identity_index":{"type":INDEX_TYPE,
                          "source_registry_sha256":index.get("source_registry_sha256"),
                          "included_seasons":["2025-2026","2026-2027"],
                          "historical_2024_25_domestic_memberships_in_index":False,
                          "index_is_current_registry_not_historic_evidence":True},
        "coverage":{"corpora":cohorts,
                    "matches_total":len(by_match),
                    "team_appearances":sum(all_labels.values()),
                    "distinct_source_country_marked_labels":len(clubs),
                    "country_marker_counts":dict(sorted(country_counts.items())),
                    "candidate_status_counts":dict(statuses),
                    "matches_with_two_exact_alias_name_candidates_by_cohort":dict(sorted(matches_per_cohort.items())),
                    "2025_26_europa_holdout_available":False,
                    "UEFA_CL_2026_27_current_matches_included":False,
                    "teams_approved_for_cross_league_model":0,
                    "matches_approved_for_cross_league_model":0,
                    "missing_required_bridges":["verified_UEFA_team_canonical_identity",
                        "full_2025_26_europa_matches",
                        "pre_match_cross_league_team_strength",
                        "2024_25_domestic_season_or_verified_historical_team_membership",
                        "independent_UEFA_match_by_match_confirmation",
                        "complete_competition_specific_heldout_test"]},
        "review_rows":clubs,
        "safety":{"10_leagues_unchanged":True,"canonical_aliases_not_extended":True,
                  "suggested_ids_not_promoted":True,"model_formulas_unchanged":True,
                  "odds_or_pilot_records_created":False,
                  "goal_multipliers":None,"H2H_experiments":False,
                  "phase_motivation_not_inferred":True}
    }
    if result["coverage"]["matches_total"]!=432:
        raise CoverageError("EXPECTED_TOTAL_432_GAMES")
    if result["coverage"]["team_appearances"]!=864:
        raise CoverageError("EXPECTED_864_TEAM_APPEARANCES")
    return result


def review_csv(result):
    fields=["uefa_source_label","uefa_club_name","source_country_marker",
            "country_in_ten_league_universe","status",
            "candidate_canonical_id_DO_NOT_USE_IN_MODEL",
            "candidate_domestic_name_DO_NOT_USE_IN_MODEL",
            "candidate_domestic_memberships_2025_27_only",
            "historical_2024_25_membership_verified",
            "uefa_identity_approved","participant_appearances_in_three_cohorts"]
    buf=io.StringIO()
    writer=csv.DictWriter(buf,fieldnames=fields,lineterminator="\n")
    writer.writeheader()
    for x in result["review_rows"]:
        writer.writerow({**x,"candidate_domestic_memberships_2025_27_only":
                            ";".join(x["candidate_domestic_memberships_2025_27_only"])})
    return buf.getvalue()


def main(argv=None):
    p=argparse.ArgumentParser(description="Non-promoting UEFA 432-match / 10-league name candidate coverage")
    p.add_argument("--identity-index",default="experiments/263/evidence/identity_index_263.json")
    p.add_argument("--output-dir",default="data/europe_staged_263/strength_bridge_audit")
    args=p.parse_args(argv)
    path=Path(args.output_dir)
    if Path("data/europe_staged_263") not in path.parents:
        raise CoverageError("OUTPUT_MUST_BE_EUROPE_ONLY")
    idx=json.loads(Path(args.identity_index).read_text(encoding="utf-8"))
    source={relative:fetch_pinned_source(relative)[0] for relative,*_ in SOURCES.values()}
    result=source_audit(source,idx)
    path.mkdir(parents=True,exist_ok=True)
    (path/"source_coverage_263.json").write_text(
        json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (path/"uefa_club_identity_REVIEW_ONLY.csv").write_text(review_csv(result),encoding="utf-8")
    summary={"status":result["status"],**result["coverage"],
             "source_files":[x["source_relative"] for x in result["source"]["corpora"]]}
    print("EUROPE_SOURCE_COVERAGE="+json.dumps(summary,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    main()
