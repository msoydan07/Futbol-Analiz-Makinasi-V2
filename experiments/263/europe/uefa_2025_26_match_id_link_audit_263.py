"""2025/26 UEFA CL+EL: article-linked official match ID and score audit.

Uses assistant-web-reviewed official UEFA result article hrefs, source
date/score text, the existing 47 official club profile links and the
PREVIOUSLY accepted, immutable 132 review-only match artifact.

No UEFA HTTP in GitHub runner, no full historical game rerun, no
new leagues, no forward data, no M0/M1/M2 fit, no pilot or main.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from uefa_2025_26_club_profile_provenance_263 import (
    validate_links, accept_prior_132, ARTICLES as PROFILE_ARTICLES)
from uefa_ten_league_scope_gate_263 import validated_index

VERSION="263_UEFA_2025_26_CL_EL_132_OFFICIAL_MATCH_ID_SOURCE_REVIEW_V1"
SCHEMA="263_UEFA_CL_EL_2025_26_MATCH_ID_FROM_OFFICIAL_RESULTS_ARTICLE_HANDOFF_V1"
SOURCES={
 "UEFA_CL":"https://www.uefa.com/uefachampionsleague/news/029c-1e9a2f63fe2d-ebf9ad643892-1000--champions-league-2025-26-all-the-results/",
 "UEFA_EL":"https://www.uefa.com/uefaeuropaleague/news/029c-1e9b4e18c28e-3bb76afa22ac-1000--europa-league-league-phase-results-by-team/",
}
GROUPS={"UEFA_CL":"uefachampionsleague","UEFA_EL":"uefaeuropaleague"}
COUNTS={"UEFA_CL":95,"UEFA_EL":37}
# Exact UEFA match URL shortening exceptions, NOT approximate string matching.
# Match-page slugs were directly inspected from official article hrefs.
URL_SLUG_TO_PROFILE_SLUG={
 "UEFA_CL":{"b-dortmund":"dortmund","atleti":"atletico",
            "bayern-munchen":"bayern"},
 "UEFA_EL":{"nott-m-forest":"nottm-forest"},
}
class MatchAuditError(ValueError):pass

def club_slug_index(idx,profiles):
    links=validate_links(idx,profiles)
    out={}
    for (cup,cid),value in links.items():
        segment=value["official_uefa_club_profile"].rstrip("/").split("/")[-1]
        match=re.fullmatch(r"\d+--([a-z0-9-]+)",segment)
        if not match:raise MatchAuditError("PREVIOUS_OFFICIAL_CLUB_PROFILE_SLUG_INVALID")
        slug=match.group(1)
        key=(cup,slug)
        if key in out:raise MatchAuditError("PROFILE_SLUG_COLLISION")
        out[key]=cid
    return out

def audit(index,profiles,official,union):
    validated_index(index)
    if (official.get("schema")!=SCHEMA or official.get("retrieval_method")!=
        "ASSISTANT_WEB_CLICK_THROUGH_DIRECT_OFFICIAL_UEFA_RESULT_ARTICLE_LINKS"
        or official.get("claimed_independent_github_uefa_fetch") is not False
        or official.get("official_result_articles")!=SOURCES):
        raise MatchAuditError("OFFICIAL_MATCH_ID_HANDOFF_PROVENANCE_INVALID")
    evidence=official.get("matches")
    if not isinstance(evidence,list) or len(evidence)!=132:
        raise MatchAuditError("NOT_132_OFFICIAL_RESULT_LINKS")
    previously=accept_prior_132(union)
    slug_to_id=club_slug_index(index,profiles)
    previous_by_key={}
    for row in previously:
        key=(row["competition"],row["date"],
             row["home_club_id_candidate"],row["away_club_id_candidate"])
        if key in previous_by_key:raise MatchAuditError("PREVIOUS_MATCH_KEY_DUPLICATE")
        previous_by_key[key]=row
    ids=set();links=set();numbers=set();used=set();accepted=[];counts=Counter()
    for match in evidence:
        required={"competition","uefa_article_link_number","uefa_match_id",
                  "match_date","source_score_home","source_score_away",
                  "uefa_match_slug","official_uefa_match_url"}
        if not isinstance(match,dict) or set(match)!=required:
            raise MatchAuditError("OFFICIAL_HREF_RECORD_FIELDS_INVALID")
        cup=match["competition"];group=GROUPS.get(cup)
        if not group:raise MatchAuditError("OFFICIAL_LINK_UNSUPPORTED_CUP")
        mid=match["uefa_match_id"];ln=match["uefa_article_link_number"]
        if type(mid)!=int or not 2000000<=mid<3000000 or type(ln)!=int or not 1<=ln<=220:
            raise MatchAuditError("OFFICIAL_ID_OR_ARTICLE_INDEX_INVALID")
        url=match["official_uefa_match_url"]
        if not isinstance(url,str):raise MatchAuditError("INVALID_UEFA_LINK_URL")
        u=urlsplit(url)
        fullpattern="/"+group+"/match/"+str(mid)+"--"+str(match["uefa_match_slug"])+"/"
        if (u.scheme!="https" or u.netloc!="www.uefa.com" or u.path!=fullpattern or
            u.query or u.fragment or u.username or u.password):
            raise MatchAuditError("OFFICIAL_UEFA_MATCH_ID_URL_MISMATCH")
        if mid in ids or url in links or (cup,ln) in numbers:
            raise MatchAuditError("DUPLICATE_OFFICIAL_MATCH_ID_OR_LINK")
        ids.add(mid);links.add(url);numbers.add((cup,ln))
        slug=match["uefa_match_slug"]
        if not isinstance(slug,str) or not re.fullmatch("[a-z0-9-]+-vs-[a-z0-9-]+",slug):
            raise MatchAuditError("BAD_MATCH_SLUG_SHAPE")
        home_slug,away_slug=slug.split("-vs-",1)
        aliases=URL_SLUG_TO_PROFILE_SLUG[cup]
        home=slug_to_id.get((cup,aliases.get(home_slug,home_slug)))
        away=slug_to_id.get((cup,aliases.get(away_slug,away_slug)))
        if home is None or away is None or home==away:
            raise MatchAuditError("OFFICIAL_MATCH_LINK_NOT_TWO_IN_SCOPE_2025_TEAMS")
        day=match["match_date"]
        if not isinstance(day,str) or not re.fullmatch(r"202[56]-\d\d-\d\d",day):
            raise MatchAuditError("MATCH_DATE_SHAPE_INVALID")
        key=(cup,day,home,away)
        prior=previous_by_key.get(key)
        if prior is None or key in used:
            raise MatchAuditError("OFFICIAL_MATCH_ID_NOT_ONE_TO_ONE_WITH_PRIOR_132")
        for side in ("home","away"):
            actual=match["source_score_"+side]
            old=prior[side+"_goals"]
            if type(actual)!=int or not 0<=actual<=40 or actual!=int(old):
                raise MatchAuditError("OFFICIAL_RESULT_ARTICLE_SCORE_CONFLICT_WITH_PREVIOUS")
        used.add(key);counts[cup]+=1
        accepted.append({"competition":cup,"date":day,
                         "uefa_official_match_id":mid,
                         "uefa_official_match_url":url,
                         "uefa_official_result_article_url":SOURCES[cup],
                         "article_link_number":ln,
                         "home_id_candidate":home,"away_id_candidate":away,
                         "home_goals":match["source_score_home"],
                         "away_goals":match["source_score_away"],
                         "match_id_retrieved_from_UEFA_web_by_assistant":True,
                         "UEFA_match_HTML_fetched_by_GitHub_CI":False,
                         "historical_prematch_source_timestamps_confirmed":False,
                         "model_eligible":False})
    if dict(counts)!=COUNTS or used!=set(previous_by_key):
        raise MatchAuditError("OFFICIAL_132_MATCH_COVERAGE_NOT_EXACT")
    report={"schema":VERSION,"status":"132_MATCH_IDS_SOURCE_LINKED_BUT_HISTORICAL_ASOF_DATA_UNVERIFIED",
            "official_uefa_match_id_links_count":len(accepted),
            "uefa_linked_matches_by_competition":dict(counts),
            "unique_official_uefa_match_numbers":len(ids),
            "source_result_articles":SOURCES,
            "identity_and_score_date_orientation_match_previous_132":True,
            "all_links_from_official_uefa_result_articles_clicked":True,
            "GitHub_CI_independently_downloaded_UEFA_HTML":False,
            "source_link_evidence_is_assistant_web_handoff":True,
            "only_2025_26_ten_domestic_league_teams":True,
            "pre_kickoff_source_availability_verified":False,
            "verified_pregame_lambda":False,
            "model_comparison_or_calibration_permitted":False,
            "m0_m1_m2_or_production_modified":False,
            "pilot_recorded":False}
    return report,accepted

def run():
    ap=argparse.ArgumentParser()
    ap.add_argument("--union",required=True)
    ap.add_argument("--profiles",default="experiments/263/evidence/uefa_2025_26_article_club_links_web_review.json")
    ap.add_argument("--matches",default="experiments/263/evidence/uefa_cl_el_2025_26_official_132_match_links_web_review.json")
    ap.add_argument("--identity",default="experiments/263/evidence/identity_index_263.json")
    ap.add_argument("--output",default="data/europe_staged_263/uefa_2025_26_132_official_match_ids")
    a=ap.parse_args()
    paths={field:Path(getattr(a,field)) for field in ("union","profiles","matches","identity")}
    source={k:json.loads(v.read_text(encoding="utf8")) for k,v in paths.items()}
    report,rows=audit(source["identity"],source["profiles"],source["matches"],source["union"])
    report["input_sha256"]={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in paths.items()}
    out=Path(a.output)
    if Path("data/europe_staged_263") not in out.parents:
        raise MatchAuditError("ONLY_EXPERIMENT_EUROPE_QUARANTINE_OUTPUT")
    out.mkdir(parents=True,exist_ok=True)
    (out/"132_official_match_id_links_report.json").write_text(
        json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    (out/"132_UEFA_MATCH_IDS_REVIEW_ONLY.json").write_text(
        json.dumps({"schema":VERSION,"status":"REVIEW_ONLY_NO_MODEL",
                    "matches":rows,"model_training_permitted":False},
                    ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("UEFA_132_MATCH_LINK_ACCEPTANCE="+json.dumps(report,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":run()
