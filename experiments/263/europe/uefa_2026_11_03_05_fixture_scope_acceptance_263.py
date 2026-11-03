"""One read-only official UEFA stage-3 fixture audit: 3-5 Nov 2026.
No analyses, odds, xG, model, predictions, ledger or prod changes.
"""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

from uefa_requested_match_entry_263 import (
    get_official_article, extract_one_official_fixture,
    index_with_reviewed_uefa_names, SOURCES, UEFA_OFFICIAL_NAME_EQUIVALENCES)
from uefa_ten_league_scope_gate_263 import (
    check_europe_scope,validated_index,norm)

INDEX=Path("experiments/263/evidence/identity_index_263.json")
COHORT=Path("experiments/263/evidence/elo_uefa_active_cohort_2026_11_03.json")
REVIEW=Path("experiments/263/evidence/uefa_2026_11_03_05_fixture_scope_review.json")
OUTPUT=Path("data/europe_staged_263/2026_11_03_05_fixture_scope_acceptance/fixture_scope_status.json")
REFERENCE_NOW=datetime.fromisoformat("2026-11-03T06:10:00+00:00")
class AuditError(ValueError): pass

def run(provider=get_official_article):
    index=json.loads(INDEX.read_text(encoding="utf8"))
    validated_index(index)
    original_aliases=dict(index["aliases"])
    reviewed=index_with_reviewed_uefa_names(index)
    if index["aliases"]!=original_aliases:
        raise AuditError("CANONICAL_ALIAS_REGISTRY_MUTATED")
    cohort=json.loads(COHORT.read_text(encoding="utf8"))
    audit=json.loads(REVIEW.read_text(encoding="utf8"))
    active=set(cohort["eligible_team_ids"])
    if len(active)!=167 or len(cohort["excluded_team_ids"])!=25:
        raise AuditError("ACTIVE_ELO_SCOPE_CHANGED")
    if audit["schema"]!="UEFA_263_NOV3_5_OFFICIAL_FIXTURE_SCOPE_ACCEPTANCE_REVIEW":
        raise AuditError("REVIEW_SCHEMA_UNEXPECTED")
    selected=audit["verified_fixtures"];other=audit["unselected_fixtures"]
    if len(selected)!=17 or len(other)!=19 or len({m["uefa_match_id"] for m in selected})!=17:
        raise AuditError("FIXTURE_REVIEW_COUNTS_CHANGED")
    for source_name,(official,league) in UEFA_OFFICIAL_NAME_EQUIVALENCES.items():
        original=original_aliases.get(norm(source_name))
        if original is not None:
            raise AuditError("UNEXPECTED_PRIOR_ALIAS_EXISTS")
        tid=reviewed["aliases"][norm(source_name)]
        team=index["teams"][tid]
        if team["name"]!=official or tid not in index["season_memberships"]["2026-2027"][league]:
            raise AuditError("ALIAS_OFFICIAL_ID_MISMATCH")

    # Exactly one current official article fetch per competition; not 17 individual
    # requests, no external fixture feed, no model or statistics requests.
    html={}
    source_urls={}
    for comp in ("UEFA_CL","UEFA_EL"):
        raw,url=provider(comp)
        if url!=SOURCES[comp]:
            raise AuditError("UEFA_FIXTURE_ARTICLE_URL_CHANGED")
        html[comp]=raw;source_urls[comp]=url
    success=[];miss=[]
    for rec in selected:
        h=rec["home_uefa"];a=rec["away_uefa"];comp=rec["competition"]
        checked=check_europe_scope(h,a,reviewed)
        if not checked["allow_further_research"]:
            raise AuditError("SELECTED_CLUBS_FAIL_TEN_LEAGUE_GATE:"+h+" / "+a)
        hid=checked["home"]["canonical_team_id"]
        aid=checked["away"]["canonical_team_id"]
        if (hid!=rec["home_identity"]["canonical_team_id"] or
            aid!=rec["away_identity"]["canonical_team_id"] or
            hid not in active or aid not in active):
            raise AuditError("SELECTED_CANONICAL_OR_ELO_SCOPE_CHANGED")
        status,fixture=extract_one_official_fixture(
            html[comp],comp,hid,aid,reviewed,REFERENCE_NOW)
        if not fixture:
            miss.append({"home":h,"away":a,"competition":comp,"status":status})
            continue
        if (fixture["date"]!=rec["date"] or
            fixture["kickoff_utc"]!=rec["kickoff_utc"] or
            fixture["fixture_source_url"]!=source_urls[comp] or
            fixture["round"]!="LEAGUE_PHASE" or
            fixture["matchday"]!=4):
            raise AuditError("OFFICIAL_UEFA_FIXTURE_DATE_OR_TIME_DRIFT:"+h+" / "+a)
        if not rec["official_match_url"].startswith(
            "https://www.uefa.com/"+
            ("uefachampionsleague" if comp=="UEFA_CL" else "uefaeuropaleague")+
            "/match/"+str(rec["uefa_match_id"])+"--"):
            raise AuditError("INDIVIDUAL_OFFICIAL_MATCH_LINK_INVALID")
        success.append({"competition":comp,"date":fixture["date"],
                        "home":h,"away":a,
                        "home_id":hid,"away_id":aid,
                        "uefa_match_id":rec["uefa_match_id"],
                        "kickoff_utc":fixture["kickoff_utc"],
                        "turkey_local_time":rec["kickoff_turkey"],
                        "official_match_url":rec["official_match_url"],
                        "verification":"ONE_OFFICIAL_UEFA_LISTING_EXACT_MATCH"})
    if miss or len(success)!=17:
        raise AuditError("NOT_ALL_17_MATCHES_IN_CURRENT_UEFA_ARTICLES:"+json.dumps(miss,ensure_ascii=False))
    for rec in other:
        # Unresolved team name != demonstrated out-of-scope: no false exclusion.
        h=rec["home_scope"]["canonical_team_id"]
        a=rec["away_scope"]["canonical_team_id"]
        if h in active and a in active:
            raise AuditError("UNSELECTED_BOTH_TEAMS_ACTUALLY_IN_SCOPE")
    days=Counter(r["date"] for r in success)
    cups=Counter(r["competition"] for r in success)
    team_ids={tid for r in success for tid in (r["home_id"],r["away_id"])}
    if days!=Counter({"2026-11-03":6,"2026-11-04":6,"2026-11-05":5}):
        raise AuditError("CANDIDATE_COUNT_PER_DATE_CHANGED")
    if cups!=Counter({"UEFA_CL":12,"UEFA_EL":5}) or len(team_ids)!=34:
        raise AuditError("COMPETITION_OR_DISTINCT_CLUB_COUNT_CHANGED")
    return {
        "schema":"263_UEFA_NOV3_NOV5_FOCUSED_STAGE3_ACCEPTANCE_V1",
        "status":"17_OFFICIAL_FIXTURES_AND_BOTH_TEAMS_CANONICALLY_CONFIRMED",
        "study_reference_utc":REFERENCE_NOW.isoformat(),
        "study_reference_is_not_proof_of_actual_retrieval_time":True,
        "uefa_articles_fetched":source_urls,
        "official_fixture_total":36,
        "candidate_total":len(success),
        "unselected_total":len(other),
        "candidate_competitions":dict(cups),
        "candidate_days":dict(sorted(days.items())),
        "distinct_eligible_clubs":len(team_ids),
        "uefa_2026_27_name_aliases_reviewed":list(UEFA_OFFICIAL_NAME_EQUIVALENCES),
        "base_team_alias_registry_unchanged":True,
        "production_main_unchanged":True,
        "match_registration_done":False,
        "prediction_recorded":False,
        "model_forecast_authorized":False,
        "new_fitted_elo_weight_approved":False,
        "source_proof_level":"OFFICIAL_UEFA_ARTICLE_FIXTURE_AND_INDIVIDUAL_PAGE_LINKED;NO_TEAM_NUMERIC_UEFA_ID_CONFIRMATION",
        "eligible":success
    }

def main():
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    try:
        report=run()
    except Exception as exc:
        report={
            "status":"STAGE3_OFFICIAL_UEFA_FIXTURE_ACCEPTANCE_BLOCKED",
            "error_type":type(exc).__name__,
            "reason":str(exc)[:700],
            "model_forecast_authorized":False,
            "match_registration_done":False,
            "production_main_unchanged":True}
        OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print("UEFA_STAGE3_BLOCKED="+json.dumps(report,ensure_ascii=False))
        raise
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("UEFA_STAGE3="+json.dumps({
        "status":report["status"],"candidate_days":report["candidate_days"],
        "candidate_competitions":report["candidate_competitions"],
        "eligible_teams":report["distinct_eligible_clubs"],
        "model_forecast_authorized":False},ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
