"""2025/26 UEFA CL + EL, TEN LEAGUES, one-season union coverage gate.

ONE source/identity inventory only. Never fit ratings or issue predictions.
Two individually pinned/anchored historic match sources:
  CL: OpenFootball 2025-26/cl.txt pinned SHA, verified 144 games/487 goals.
  EL: fixture download 2025 JSON, verified 144 games/386 goals + 6 anchors.
CL historical source uses expanded official UEFA club names; 19 are
explicitly reviewed against UEFA's season team/results list and canonical
2025/26 team registry. No fuzzy guesses; official UEFA numeric club IDs
remain UNVERIFIED even where public short names match.

Use the 2025/26 historical domestic membership, never current 2026/27 list.
Monaco (source marker MCO) is accepted from ACTUAL FRA1 membership; code
never translates a source country marker to league identity.

Only pairs of TEN-LEAGUE clubs are retained in quarantined outputs.
No H2H as a feature, no opponent results after target match, no main changes.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
import re
from pathlib import Path

from uefa_tactical_study_263 import (
    SOURCE_COMMIT, fetch_pinned_source, parse_league_phase,
    validate_source_rows,
)
from uefa_strength_source_audit_263 import split_uefa_club
from uefa_el_2025_26_scope_source_263 import (
    fetch_public_feed, decode_feed, audit_ten_league_scope,
    UEFA_REFERENCE_ANCHORS, FEED_URL, UEFA_OFFICIAL_REFERENCE,
)
from uefa_ten_league_scope_gate_263 import norm, validated_index

VERSION="263_UEFA_2025_26_BOTH_TEN_LEAGUES_UNION_COVERAGE_V1"
SEASON="2025-2026"
CL_FILE="2025-26/cl.txt"
CL_OFFICIAL_RESULTS="https://www.uefa.com/uefachampionsleague/news/029c-1e9a2f63fe2d-ebf9ad643892-1000--champions-league-2025-26-all-the-results/"
CL_OFFICIAL_TEAM_LIST="https://www.uefa.com/uefachampionsleague/news/0296-1d21e9bdf7e4-808a7511165c-1000--2025-26-champions-league-format-dates-draws-final/"

# Exact SOURCE expanded-name spelling -> reviewed UEFA-short-name already in
# canonical index. Country markers are ASSERTIONS, NEVER league assignments.
# Official UEFA 2025/26 CL team list/results supports the short club names;
# per-club numeric UEFA IDs and all individual match records still require audit.
CL_NAME_CROSSWALK={
  "Arsenal FC":("Arsenal","ENG"),
  "Juventus FC":("Juventus","ITA"),
  "Sport Lisboa e Benfica":("Benfica","POR"),
  "Tottenham Hotspur FC":("Tottenham","ENG"),
  "Real Madrid CF":("Real Madrid","ESP"),
  "AFC Ajax":("Ajax","NED"),
  "FC Internazionale Milano":("Inter","ITA"),
  "Liverpool FC":("Liverpool","ENG"),
  "Club Atlético de Madrid":("Atlético de Madrid","ESP"),
  "Paris Saint-Germain FC":("Paris Saint-Germain","FRA"),
  "Atalanta BC":("Atalanta","ITA"),
  "Chelsea FC":("Chelsea","ENG"),
  "Club Brugge KV":("Club Brugge","BEL"),
  "Newcastle United FC":("Newcastle United","ENG"),
  "Manchester City FC":("Manchester City","ENG"),
  "SSC Napoli":("Napoli","ITA"),
  "Galatasaray SK":("Galatasaray","TUR"),
  "Sporting Clube de Portugal":("Sporting CP","POR"),
  "AS Monaco FC":("Monaco","MCO"),
}
# Predeclared, independently observable official UEFA sample.
CL_RESULT_ANCHORS=(
    ("2025-09-18","Eintracht Frankfurt (GER)","Galatasaray SK (TUR)",5,1),
    ("2025-09-30","Galatasaray SK (TUR)","Liverpool FC (ENG)",1,0),
    ("2025-10-22","Chelsea FC (ENG)","AFC Ajax (NED)",5,1),
    ("2025-11-05","AFC Ajax (NED)","Galatasaray SK (TUR)",0,3),
    ("2026-01-21","Galatasaray SK (TUR)","Club Atlético de Madrid (ESP)",1,1),
    ("2026-01-28","Manchester City FC (ENG)","Galatasaray SK (TUR)",2,0),
)

class UnionCoverageError(ValueError):
    pass

def verified_cl_source(payload):
    rows=parse_league_phase(payload,"UEFA_CL",SEASON)
    validate_source_rows(rows,"UEFA_CL",SEASON,144,487)
    for day,home,away,hg,ag in CL_RESULT_ANCHORS:
        if sum(int(x["date"]==day and x["home"]==home and x["away"]==away
                   and x["hg"]==hg and x["ag"]==ag) for x in rows)!=1:
            raise UnionCoverageError("CL_OFFICIAL_PREDECLARED_ANCHOR_MISMATCH")
    return rows

def canonical_membership(index):
    validated_index(index)
    result={}
    for league, ids in index["season_memberships"][SEASON].items():
        for team_id in ids:
            if team_id in result:
                raise UnionCoverageError("CLUB_IN_TWO_DOMESTIC_LEAGUES")
            result[team_id]=league
    return result

def resolve_cl_name(raw,index,members):
    name, marker=split_uefa_club(raw)
    x=index["aliases"].get(norm(name))
    provenance="EXACT_REVIEWED_ALIAS"
    if x is None and name in CL_NAME_CROSSWALK:
        short,expected_marker=CL_NAME_CROSSWALK[name]
        if marker!=expected_marker:
            raise UnionCoverageError("CL_CURATED_ALIAS_COUNTRY_MARKER_CONFLICT")
        x=index["aliases"].get(norm(short))
        if x is None:
            raise UnionCoverageError("CL_CURATED_ALIAS_TARGET_MISSING")
        provenance="CURATED_UEFA_SOURCE_TO_DOMESTIC_ALIAS_ID_UNVERIFIED"
    if x is None:
        return None,provenance
    return {"team_id":x,"league":members.get(x),
            "canonical_display":index["teams"][x]["name"],
            "source_label":raw,"resolution":provenance},provenance

def partition_cl(rows,index):
    members=canonical_membership(index)
    labels={n for r in rows for n in (r["home"],r["away"])}
    lookup={n:resolve_cl_name(n,index,members)[0] for n in labels}
    # Fail closed against incorrectly mapping two UEFA participants to one
    # canonical team, not merely conflicting names in one fixture.
    identities=[v["team_id"] for v in lookup.values() if v is not None]
    if len(identities)!=len(set(identities)):
        raise UnionCoverageError("CL_TWO_SOURCE_CLUBS_COLLAPSE_TO_SAME_ID")
    reasons=Counter()
    retained=[]
    for x in rows:
        h=lookup[x["home"]];a=lookup[x["away"]]
        if h is None or a is None:
            reasons["SOURCE_CLUB_NAME_NOT_IN_APPROVED_LOCAL_ALIAS_OR_CURATED_REVIEW"]+=1
            continue
        if h["league"] is None or a["league"] is None:
            reasons["CLUB_NOT_MEMBER_OF_2025_26_TEN_LEAGUES"]+=1
            continue
        if h["team_id"]==a["team_id"]:
            raise UnionCoverageError("HOME_AND_AWAY_ID_COLLISION")
        retained.append({
            "competition":"UEFA_CL","season":SEASON,"date":x["date"],
            "matchday":x["matchday"],"home_source":x["home"],"away_source":x["away"],
            "home_club_id_candidate":h["team_id"],
            "away_club_id_candidate":a["team_id"],
            "home_league":h["league"],"away_league":a["league"],
            "home_goals":x["hg"],"away_goals":x["ag"],
            "identity_link_status":"REVIEW_ONLY_NOT_OFFICIAL_UEFA_NUMERIC_ID",
            "both_clubs_in_2025_26_ten_league_registry":True,
            "model_training_allowed":False,
            "source_note":"OPENFOOTBALL_IMMUTABLE_SHA_PLUS_SIX_UEFA_ANCHORS_NOT_ALL_MATCHES"
        })
    is_in=[n for n in labels if lookup[n] is not None and lookup[n]["league"] is not None]
    curated=[n for n in is_in if lookup[n]["resolution"].startswith("CURATED_")]
    return retained,{
        "source_clubs":len(labels),
        "ten_league_member_clubs_with_exact_or_curated_source_names":len(is_in),
        "curated_source_name_clubs_in_ten_leagues":len(curated),
        "curated_source_names":sorted(curated),
        "source_names_not_resolved_or_not_in_members":len(labels)-len(is_in),
        "games_retained":len(retained),"games_excluded":len(rows)-len(retained),
        "excluded_reasons":dict(sorted(reasons.items())),
        "historical_club_id_uefa_verified":0
    }

def combine_same_season(cl_raw,el_raw,index):
    if not isinstance(cl_raw,bytes) or not isinstance(el_raw,bytes):
        raise UnionCoverageError("TWO_RAW_SOURCES_REQUIRED")
    cl=verified_cl_source(cl_raw)
    el=decode_feed(el_raw)  # includes independent 6 UEFA anchors
    cl_keep,cl_meta=partition_cl(cl,index)
    el_meta,el_keep=audit_ten_league_scope(el,index,hashlib.sha256(el_raw).hexdigest())
    members=canonical_membership(index)
    combined=list(cl_keep)
    for r in el_keep:
        h=r["home_canonical_id_candidate"];a=r["away_canonical_id_candidate"]
        if h not in members or a not in members:
            raise UnionCoverageError("EL_PREVIOUS_AUDIT_ACCEPTED_OUT_OF_LEAGUE_CLUB")
        combined.append({
            "competition":"UEFA_EL","season":SEASON,
            "date":r["date"],"matchday":r["matchday"],
            "home_source":r["home"],"away_source":r["away"],
            "home_club_id_candidate":h,"away_club_id_candidate":a,
            "home_league":members[h],"away_league":members[a],
            "home_goals":r["home_goals"],"away_goals":r["away_goals"],
            "identity_link_status":"REVIEW_ONLY_NOT_OFFICIAL_UEFA_NUMERIC_ID",
            "both_clubs_in_2025_26_ten_league_registry":True,
            "model_training_allowed":False,
            "source_note":"PUBLIC_FEED_SIX_UEFA_ANCHORS_NOT_ALL_MATCHES"
        })
    combined.sort(key=lambda r:(r["date"],r["competition"],r["matchday"],
                                r["home_club_id_candidate"],r["away_club_id_candidate"]))
    keys=[(x["competition"],x["date"],x["home_club_id_candidate"],
           x["away_club_id_candidate"]) for x in combined]
    if len(set(keys))!=len(keys):
        raise UnionCoverageError("DUPLICATE_CROSS_COMPETITION_IDENTITY_DATE")
    if len(cl_keep)+len(el_keep)!=len(combined):
        raise UnionCoverageError("UNION_CARDINALITY_INTEGRITY")
    nodes=Counter()
    edges=Counter()
    leagues=set()
    for m in combined:
        h=m["home_league"];a=m["away_league"]
        nodes[h]+=1;nodes[a]+=1
        leagues.update([h,a])
        edges[" / ".join(sorted((h,a)))]+=1
    # Descriptive connectivity only. No outcomes, odds, rating or model here.
    adj=defaultdict(set)
    for row in combined:
        adj[row["home_league"]].add(row["away_league"])
        adj[row["away_league"]].add(row["home_league"])
    seen=set();components=[]
    for node in sorted(leagues):
        if node in seen:continue
        stack=[node];component=[]
        while stack:
            n=stack.pop()
            if n in seen:continue
            seen.add(n);component.append(n)
            stack.extend(adj[n]-seen)
        components.append(sorted(component))
    all_leagues=set(index["season_memberships"][SEASON])
    report={
        "version":VERSION,"status":"SAME_SEASON_TWO_COMPETITION_IDENTITY_COVERAGE_ONLY_NOT_MODEL_TRAINING",
        "year":SEASON,
        "source":{
            "cl_openfootball":{"relative":CL_FILE,"pinned_sha":SOURCE_COMMIT,
                "sha256":hashlib.sha256(cl_raw).hexdigest(),
                "unfiltered_matches":len(cl),"official_uefa_anchor_checks":len(CL_RESULT_ANCHORS),
                "UEFA_official_results_url":CL_OFFICIAL_RESULTS,
                "UEFA_official_club_list_url":CL_OFFICIAL_TEAM_LIST,
                "all_matches_officially_verified":False},
            "el_public_feed":{"url":FEED_URL,"sha256":hashlib.sha256(el_raw).hexdigest(),
                "unfiltered_matches":len(el),"official_uefa_anchor_checks":len(UEFA_REFERENCE_ANCHORS),
                "UEFA_official_results_url":UEFA_OFFICIAL_REFERENCE,
                "all_matches_officially_verified":False}
        },
        "coverage":{
            "CL":cl_meta,
            "EL":el_meta["coverage"],
            "total_source_matches":len(cl)+len(el),
            "both_clubs_in_ten_league_name_review_candidates":len(combined),
            "source_games_excluded_by_scope_or_identity":len(cl)+len(el)-len(combined),
            "ten_domestic_leagues_in_registry":len(all_leagues),
            "candidate_uefa_leagues_present":sorted(leagues),
            "candidate_leagues_without_uefa_match":sorted(all_leagues-leagues),
            "pairs_of_domestic_leagues":dict(sorted(edges.items())),
            "team_sides_by_league":dict(sorted(nodes.items())),
            "connected_components_descriptive_only":components,
            "date_min":min(m["date"] for m in combined) if combined else None,
            "date_max":max(m["date"] for m in combined) if combined else None,
            "matches_approved_for_strength_model":0,
        },
        "quality":{
            "all_fixtures_UEFA_numerical_team_id_verified":False,
            "candidate_alias_map_is_same_as_authoritative_UEFA_crosswalk":False,
            "official_fixture_spotchecks_not_full_288":True,
            "temporal_feature_asof_table_ready":False,
            "domestic_2024_25_member_history_verified":False,
            "domestic_xG_xGA_time_aligned_for_2025_26":False,
            "selection_bias_adjustment_validated":False,
            "quantified_interleague_strength_lambda_ready":False,
            "joint_model_evaluation_done":False,
        },
        "decision":{
            "do_not_train_or_score":True,"retain_for_technical_review_only":True,
            "no_h2h_feature":True,"motivation_bonus":None,
            "no_main_promotion":True,"no_ten_leagues_modified":True,
            "no_pilot_recorded":True,
            "next_only":"SOURCE_LINKED_UEFA_TEAM_IDS_AND_DATE_SCOPED_PREMATCH_DOMESTIC_STRENGTH_INPUT_AUDIT"
        }
    }
    return report,combined

def render_markdown(report):
    c=report["coverage"]
    return ("\n".join([
       "# 2025/26 UEFA CL + EL — Same-season 10-league review-only coverage",
       "",
       "| Cohort | League-phase matches | Both teams 10-league candidates |",
       "| --- | ---: | ---: |",
       f"| Champions League | 144 | {c['CL']['games_retained']} |",
       f"| Europa League | 144 | {c['EL']['2025_26_both_in_ten_leagues_name_candidates']} |",
       f"| **TOTAL** | **288** | **{c['both_clubs_in_ten_league_name_review_candidates']}** |",
       "",
       f"Excluded from candidate historical subset: **{c['source_games_excluded_by_scope_or_identity']}**.",
       f"Present leagues: **{', '.join(c['candidate_uefa_leagues_present'])}**.",
       f"No participating UEFA league-phase match: **{', '.join(c['candidate_leagues_without_uefa_match']) or 'none'}**.",
       f"CL reviewed non-exact source club aliases: **{c['CL']['curated_source_name_clubs_in_ten_leagues']}**.",
       f"Official full UEFA club ID crosswalk completed: **NO**.",
       f"Both source corpora independently UEFA page-verified match by match: **NO**.",
       f"Cross-league rating, xG/xGA time-series, calibration, live forecasts: **NOT READY**.",
       "",
       "Data is for source and identity coverage, never for production, odds, pilot or model training.",
       "All domestic league memberships use 2025-2026, never 2026-2027.",
       "UEFA MCO label on Monaco does not mean exclusion: its canonical actual membership is FRA1.",
       "No H2H feature or fabricated motivation coefficient is computed.",
       ""
    ]))

def main(argv=None):
    p=argparse.ArgumentParser(description="Single 2025/26 CL+EL ten-league source/identity union audit")
    p.add_argument("--identity-index",default="experiments/263/evidence/identity_index_263.json")
    p.add_argument("--output",default="data/europe_staged_263/2025_26_cl_el_union_audit")
    args=p.parse_args(argv)
    index=json.loads(Path(args.identity_index).read_text(encoding="utf-8"))
    raw_cl,_=fetch_pinned_source(CL_FILE)
    raw_el=fetch_public_feed()
    report,subset=combine_same_season(raw_cl,raw_el,index)
    output=Path(args.output)
    if Path("data/europe_staged_263") not in output.parents:
        raise UnionCoverageError("OUTPUT_ONLY_IN_QUARANTINED_EUROPE_FOLDER")
    output.mkdir(parents=True,exist_ok=True)
    (output/"2025_26_cl_el_ten_league_union_report.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (output/"2025_26_cl_el_review_only_matches.json").write_text(
        json.dumps({"schema":VERSION,"status":"REVIEW_ONLY_TRAINING_FORBIDDEN","matches":subset},
                   ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (output/"2025_26_cl_el_summary.md").write_text(render_markdown(report),encoding="utf-8")
    print("UEFA_2025_26_UNION_AUDIT="+json.dumps({
        "status":report["status"],"coverage":report["coverage"],
        "quality":report["quality"],"decision":report["decision"]},
        ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
