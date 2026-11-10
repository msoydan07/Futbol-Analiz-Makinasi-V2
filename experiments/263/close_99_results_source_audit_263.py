"""Final results-only closure: immutable 99 + 43 official URL + 21 alternate reviews.

This verifies *file integrity and unique score/fixture joins*, not the contents
of third-party websites. External public-page review is reported separately
from the 22 GitHub browser body score matches. Never promotes to model proof.
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
from urllib.parse import urlsplit
from collections import Counter
from verify_completed99_results_archive import ROOT,load_archive,build

MANIFEST43="data/results_only_263/43_primary_public_score_review_20261110.json"
MANUAL21="data/results_only_263/21_official_public_web_alternate_score_reviews_20261110.json"
REVIEWED_INDICES=(
 2,5,6,7,8,12,14,15,16,22,23,25,26,27,28,29,30,31,32,33,34
)
HOSTS={
 "ENG1":{"www.premierleague.com","www.afcb.co.uk"},
 "ENG2":{"www.efl.com","www.wrexhamafc.co.uk","www.portsmouthfc.co.uk",
         "www.qpr.co.uk","www.watfordfc.com"},
 "BEL1":{"www.proleague.be","kvmechelen.be"}
}
class Rejected(ValueError):pass
def require(ok,msg):
    if not ok:raise Rejected(msg)

def key(row):
    return row["league"],row["match_date"],row["home_id"],row["away_id"]

def audit(root=ROOT,source43=None,source21=None):
    root=Path(root)
    original=load_archive(root)
    from_4617=build(root)
    require(from_4617["new_result_records"]==99 and
        from_4617["logical_total_result_records"]==4617 and
        from_4617["old_ENG2_changed_stage_rows_ignored"]==9,
        "ORIGINAL_99_APPEND_ARCHIVE_NOT_STABLE")
    z43=source43 if source43 is not None else json.loads((root/MANIFEST43).read_text())
    z21=source21 if source21 is not None else json.loads((root/MANUAL21).read_text())
    require(z43.get("schema")=="263_COMPLETED_43_PRIMARY_PUBLIC_SCORE_LINKS_V1"
        and len(z43.get("records",[]))==43
        and z43.get("live_browser_latest_counts")=={
            "EXACT_SCORE_AND_TEAMS_IN_VISIBLE_BODY":22,
            "PAGE_READABLE_NO_PAIRWISE_EXPLICIT_SCORE":12,
            "HTTP_ERROR":9}
        and z43.get("independently_verified_43_of_43_live_webpage_score_body") is False
        and z43.get("all_43_official_provider_unique_match_ids_verified") is False
        and z43.get("all_43_1st_party_exact_score_attested") is False,
        "GITHUB_BROWSER_22_OF_43_NOT_RESEARCH_ONLY")
    require(z21.get("schema")=="263_LAST21_OFFICIAL_PUBLIC_RESULTS_ALTERNATE_RETRIEVAL_V1"
       and len(z21.get("primary_evidence_rows",[]))==21
       and z21.get("preceding_browser_exact_match_count")==22
       and z21.get("preceding_browser_undetermined_count")==21
       and z21.get("reviewed_public_official_web_extra_count")==21
       and z21.get("github_ci_independently_fetched_all_21") is False
       and z21.get("official_provider_unique_match_id_attested_all_21") is False
       and z21.get("original_99_scores_modified") is False
       and z21.get("original_4617_csv_modified") is False,
       "EXTERNAL_PUBLIC_PAGE_REVIEW_MISREPRESENTED")
    keys43=[key(r) for r in z43["records"]]
    require(len(set(keys43))==43,"DUPLICATED_PRIMARY_SOURCES")
    original43={key(r):r for r in original["records"] if r["source_class"]=="PUBLIC_SECONDARY_SCORE_WITH_PARTIAL_OFFICIAL_FIXTURE"}
    require(len(original43)==43 and set(keys43)==set(original43),"ORIGINAL_99_43_SOURCE_KEY_MISMATCH")
    for r in z43["records"]:
        x=original43[key(r)]
        require((r["home_goals"],r["away_goals"])==(x["home_goals"],x["away_goals"]),
                "UNVERIFIED_CHANGED_43_SCORE")
    touched=set()
    for r in z21["primary_evidence_rows"]:
        ix=r.get("prior_43_index")
        require(type(ix) is int and ix in REVIEWED_INDICES and ix not in touched,
                "NOT_EXACTLY_UNRESOLVED_21")
        touched.add(ix)
        ref=z43["records"][ix]
        require((r["league"],r["date"],r["home_id"],r["away_id"])==key(ref),
                "EXTERNAL_SOURCE_WRONG_MATCH")
        require((r["home"],r["away"])==(ref["home_alias"],ref["away_alias"]),
                "EXTERNAL_SOURCE_TEAM_NAME_MISMATCH")
        require((r["home_goals"],r["away_goals"])==(ref["home_goals"],ref["away_goals"]),
                "EXTERNAL_SOURCE_RESULT_NOT_FROZEN")
        require(r.get("verified_finished_score") is True
           and r.get("official_provider_single_fixture_id_independently_attested") is False
           and r.get("evidence_class")=="OFFICIAL_PUBLIC_PAGE_REVIEWED_VIA_ALTERNATE_WEB_RETRIEVAL_NOT_GITHUB_CI",
           "OFFICIAL_ID_OR_INDEPENDENT_BROWSER_ATTESTATION_FABRICATED")
        u=urlsplit(r.get("primary_evidence_url",""))
        require(u.scheme=="https" and u.hostname in HOSTS[r["league"]]
           and u.path not in ("","/") and u.username is None and u.password is None and u.port is None,
           "UNTRUSTED_ALTERNATE_WEB_EVIDENCE_URL")
        if r["league"]=="BEL1":
            require(("/matchs/" in u.path if u.hostname=="www.proleague.be" else "/match/" in u.path),
                    "BELGIUM_MUST_BE_OFFICIAL_SINGLE_MATCH_PAGE")
    require(touched==set(REVIEWED_INDICES),"MISSING_UNVERIFIED_21")
    require(Counter(r["league"] for r in z21["primary_evidence_rows"])=={
            "ENG1":5,"ENG2":6,"BEL1":10},"WRONG_REVIEW_LEAGUE_COUNTS")
    return {
       "schema":"263_99_RESULT_ARCHIVE_AND_43_PRIMARY_SOURCE_CLOSURE_V1",
       "99_results_permanently_archived":True,
       "4617_results_only_m4_research_input_active":True,
       "old_4518_rows_unmodified":True,
       "new_completed_score_rows":99,
       "new_score_rows_from_old_43_ledger":43,
       "matched_primary_source_site_links":43,
       "automated_browser_source_body_matching_finished_scores":22,
       "alternate_public_official_page_reviews":21,
       "not_machine_verified_in_original_43_batch":21,
       "archived_score_conflicts":0,
       "official_provider_match_ids_for_all_99_attested":False,
       "all_43_live_automated_source_body_proved":False,
       "github_browser_proleague_403_issue_resolved":False,
       "production_models_or_old_seals_modified":False,
       "new_99_training_shots_or_corners_fabricated":False,
       "model_predictive_skill_proven":False,
       "research_records_only":True,
       "next_pending":"NEXT_REAL_PREMATCH_OFFICIAL_FIXTURE_GATE_ONLY",
       "limitations":[
        "43 original secondary-grade scores each have first-party official-page URLs reviewed; no score conflicts.",
        "22 separate match scores were mechanically found in official page text in previous GitHub browser run.",
        "The other 21 had external official public web review; GitHub CI does not independently fetch their page bodies.",
        "Public official match result links are not a legal data license or universal provider fixture ID attestation.",
        "BelProLeague central calendar/game pages still return HTTP 403 to GitHub browser.",
        "Do not rewrite historical pregame forecasts or claim betting confidence."]
    }

if __name__=="__main__":
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
