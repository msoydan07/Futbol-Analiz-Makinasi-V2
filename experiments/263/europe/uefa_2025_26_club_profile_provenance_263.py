"""2025/26 CL+EL: official UEFA article-linked numeric CLUB identities, no model.

Reads assistant-web-reviewed UEFA 2025/26 season club-profile link evidence,
unchanged 132-match historical review artifact, and unchanged 2025/26 local
canonical registry. All 47 UEFA numeric IDs are directly exposed in official
2025/26 CL/EL season team article links; GitHub does NOT fetch UEFA.com.
Keep provenance: CI is a structural consistency check, not independent
online verification, not match-by-match official fixture evidence.

NO external league analysis, H2H, λ, odds, live predictions, or promotion.
"""
import argparse,hashlib,json,re
from collections import Counter,defaultdict
from pathlib import Path
from urllib.parse import urlsplit
from uefa_ten_league_scope_gate_263 import norm,validated_index

SCHEMA="263_UEFA_2025_26_CL_EL_OFFICIAL_CLUB_PROFILE_WEB_REVIEW_V1"
UNION_SCHEMA="263_UEFA_2025_26_BOTH_TEN_LEAGUES_UNION_COVERAGE_V1"
ARTICLES={
 "UEFA_CL":"https://www.uefa.com/uefachampionsleague/news/029d-1ea2e7e3e5d8-c5227ee0ab3c-1000--meet-the-2025-26-champions-league-league-phase-teams/",
 "UEFA_EL":"https://www.uefa.com/uefaeuropaleague/news/029c-1e982c79daa1-597a684fc805-1000--2025-26-europa-league-meet-the-league-phase-teams/",
}
EXPECTED_CLUBS={"UEFA_CL":29,"UEFA_EL":18}
EXPECTED_MATCHES={"UEFA_CL":95,"UEFA_EL":37}
VERSION="263_UEFA_CROSSWALK_PROFILE_ID_LINK_READ_ONLY_V1"
class AuditError(ValueError):pass

def validate_links(index,payload):
    validated_index(index)
    if payload.get("schema")!=SCHEMA or payload.get("reviewed_by")!="ASSISTANT_BROWSED_OFFICIAL_ARTICLE_CLUB_LINKS" or payload.get("approval")!="OFFICIAL_PROFILE_LINK_CANDIDATE_FOR_INTEGRITY_REVIEW":
        raise AuditError("UNCHECKED_OR_MALFORMED_WEB_HANDOFF")
    clubs=payload.get("clubs")
    if not isinstance(clubs,list) or len(clubs)!=47:
        raise AuditError("EXPECTED_47_OFFICIAL_PROFILE_LINKS")
    members={tid:league for league,ids in index["season_memberships"]["2025-2026"].items() for tid in ids}
    by_key={};by_uefa={};by_canon={}
    for row in clubs:
        keys={"competition","uefa_article_label","canonical_existing_alias","uefa_numeric_club_id",
              "official_uefa_club_profile","official_2025_26_participant_article"}
        if not isinstance(row,dict) or set(row)!=keys:
            raise AuditError("CLUB_EVIDENCE_FIELDS_EXACTLY_REQUIRED")
        comp=row["competition"]
        if comp not in ARTICLES or row["official_2025_26_participant_article"]!=ARTICLES[comp]:
            raise AuditError("ARTICLE_MUST_BE_2025_26_OFFICIAL_COMPETITION_SOURCE")
        u=urlsplit(row["official_uefa_club_profile"])
        group="uefachampionsleague" if comp=="UEFA_CL" else "uefaeuropaleague"
        expected=r"/"+group+r"/clubs/(\d+)--([a-z0-9-]+)/"
        match=re.fullmatch(expected,u.path)
        if (u.scheme!="https" or u.netloc!="www.uefa.com" or not match or
            u.query or u.fragment or u.username or u.password):
            raise AuditError("NOT_DIRECT_OFFICIAL_PROFILE_LINK")
        numeric=row["uefa_numeric_club_id"]
        if type(numeric)!=int or numeric<=0 or int(match.group(1))!=numeric:
            raise AuditError("CLUB_ID_NOT_EQUAL_OFFICIAL_URL_ID")
        alias=row["canonical_existing_alias"]
        label=row["uefa_article_label"]
        if not isinstance(alias,str) or not isinstance(label,str) or not label.strip():
            raise AuditError("CLUB_ALIAS_OR_LABEL_INVALID")
        canonical=index["aliases"].get(norm(alias))
        if canonical is None or canonical not in members:
            raise AuditError("OFFICIAL_SOURCE_LINK_TARGET_NOT_IN_2025_26_TEN_LEAGUES")
        if numeric in by_uefa and by_uefa[numeric]!=canonical:
            raise AuditError("SAME_OFFICIAL_UEFA_CLUB_ID_POINTS_TO_DIFFERENT_LOCAL_CLUBS")
        if canonical in by_canon and by_canon[canonical]!=numeric:
            raise AuditError("ONE_LOCAL_CLUB_LINKED_TO_TWO_OFFICIAL_UEFA_IDS")
        key=(comp,canonical)
        if key in by_key:raise AuditError("DUPLICATE_IN_COMPETITION")
        by_uefa[numeric]=canonical
        by_canon[canonical]=numeric
        by_key[key]={**row,"canonical_team_id":canonical,"domestic_2025_26_league":members[canonical]}
    count=Counter(comp for comp,tid in by_key)
    if dict(count)!=EXPECTED_CLUBS:
        raise AuditError("PREVIEW_2025_26_CLUB_COUNTS_NOT_29_AND_18")
    return by_key

def accept_prior_132(union):
    if union.get("schema")!=UNION_SCHEMA or union.get("status")!="REVIEW_ONLY_TRAINING_FORBIDDEN":
        raise AuditError("UNION_REFERENCE_MUST_STAY_REVIEW_ONLY")
    matches=union.get("matches")
    if not isinstance(matches,list) or len(matches)!=132:
        raise AuditError("PREVIOUS_132_UNION_COHORT_CHANGED")
    counts=Counter(m.get("competition") for m in matches)
    if dict(counts)!=EXPECTED_MATCHES:
        raise AuditError("PREVIOUS_95_37_SPLIT_CHANGED")
    for m in matches:
        if m.get("model_training_allowed") is not False or m.get("identity_link_status")!="REVIEW_ONLY_NOT_OFFICIAL_UEFA_NUMERIC_ID":
            raise AuditError("PREVIOUS_UNION_WRONGLY_PROMOTED")
    return matches

def audit(index,payload,union):
    links=validate_links(index,payload)
    matches=accept_prior_132(union)
    coverage=Counter()
    matched=[]
    for m in matches:
        comp=m["competition"]
        ids=[]
        for side in ("home","away"):
            cid=m[side+"_club_id_candidate"]
            ref=links.get((comp,cid))
            if ref is None:raise AuditError("UEFA_2025_26_OFFICIAL_CLUB_LINK_MISSING_IN_SELECTED_132")
            if m[side+"_league"]!=ref["domestic_2025_26_league"]:
                raise AuditError("DOMESTIC_2025_26_LEAGUE_CONFLICT")
            ids.append(ref["uefa_numeric_club_id"])
        if ids[0]==ids[1]:raise AuditError("UEFA_ID_COLLISION_IN_MATCH")
        coverage[comp]+=1
        matched.append({"competition":comp,"date":m["date"],
                        "home_canonical_id_candidate":m["home_club_id_candidate"],
                        "away_canonical_id_candidate":m["away_club_id_candidate"],
                        "home_uefa_club_profile_id":ids[0],
                        "away_uefa_club_profile_id":ids[1],
                        "official_uefa_club_profile_links_present":True,
                        "official_match_page_verified":False,
                        "fetched_UEFA_club_pages_live_by_CI":False,
                        "historical_asof_statistic_retrievability_verified":False,
                        "model_training_allowed":False})
    if dict(coverage)!=EXPECTED_MATCHES:raise AuditError("REVIEWED_MATCH_CUP_SPLIT_CHANGED")
    report={"version":VERSION,"status":"ALL_132_HAVE_OFFICIAL_2025_26_ARTICLE_LINKED_UEFA_CLUB_IDS_REVIEW_ONLY",
            "2025_26_official_club_profile_links_by_competition":EXPECTED_CLUBS,
            "distinct_uefa_numeric_profile_ids":len({x["uefa_numeric_club_id"] for x in links.values()}),
            "prior_132_candidate_matches_with_both_official_club_profile_links":len(matched),
            "coverage_by_competition":dict(coverage),
            "official_2025_26_season_articles":ARTICLES,
            "source_retrieved_by_assistant_web_not_GitHub":True,
            "CI_independently_fetched_official_UEFA_profile_html":False,
            "official_match_page_ids_for_all_132_verified":False,
            "2025_26_domestic_membership_cache_used":True,
            "same_day_UEFA_historical_match_asof_stats_proven":False,
            "official_team_source_links_compatible_with_local_candidate_registry":True,
            "numerical_UEFA_profile_links_verified_as_observed_in_2025_articles":True,
            "m0_m1_m2_comparison_allowed":False,
            "model_training_allowed":False,"main_or_existing_pilot_modified":False,
            "next_evidence_gate":"132_OFFICIAL_FIXTURE_ID_OR_HISTORICAL_STAT_SOURCE_TIMESTAMPS"}
    return report,matched

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--identity-index",default="experiments/263/evidence/identity_index_263.json")
    p.add_argument("--profiles",default="experiments/263/evidence/uefa_2025_26_article_club_links_web_review.json")
    p.add_argument("--union",required=True)
    p.add_argument("--output",default="data/europe_staged_263/2025_26_official_profile_link_review")
    a=p.parse_args()
    idx=json.loads(Path(a.identity_index).read_text(encoding="utf8"))
    profiles=json.loads(Path(a.profiles).read_text(encoding="utf8"))
    union=json.loads(Path(a.union).read_text(encoding="utf8"))
    report,rows=audit(idx,profiles,union)
    report["input_sha256"]={"profile_handoff":__import__("hashlib").sha256(Path(a.profiles).read_bytes()).hexdigest(),
         "previous_union":__import__("hashlib").sha256(Path(a.union).read_bytes()).hexdigest()}
    out=Path(a.output)
    if Path("data/europe_staged_263") not in out.parents:
        raise AuditError("ONLY_QUARANTINED_EXPERIMENT_OUTPUT")
    out.mkdir(parents=True,exist_ok=True)
    (out/"official_uefa_team_profile_link_audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    (out/"132_matches_official_club_ids_REVIEW_ONLY.json").write_text(json.dumps(
      {"schema":VERSION,"status":"REVIEW_ONLY","training_forbidden":True,"matches":rows},
      ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("UEFA_OFFICIAL_PROFILE_LINK_AUDIT="+json.dumps(report,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
