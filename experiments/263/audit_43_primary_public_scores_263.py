"""43 previously-secondary scores: direct primary-site URL research + exact 99 archive joining.

CI deliberately does not claim to have fetched or authenticated all official
page bodies. Score facts are unchanged, no model refit, no fake official IDs.
"""
from __future__ import annotations
import json
import re
import hashlib
from pathlib import Path
from collections import Counter
from urllib.parse import urlsplit
from verify_completed99_results_archive import build, load_archive, ROOT

PROOF="data/results_only_263/43_primary_public_score_review_20261110.json"
GRADE="OFFICIAL_LEAGUE_OR_CLUB_POSTMATCH_PUBLIC_PAGE_REVIEW"
HOSTS={"ENG1":{"www.premierleague.com"},
       "ENG2":{"www.efl.com","www.wrexhamafc.co.uk","www.pnefc.net","www.qpr.co.uk","www.watfordfc.com","www.wolves.co.uk","www.whufc.com","www.portsmouthfc.co.uk"},
       "BEL1":{"www.proleague.be","kvmechelen.be"},
       "POR1":{"www.ligaportugal.pt"}}

class Unsafe(ValueError):pass

def key(row):
    return (row["league"],row["match_date"],row["home_id"],row["away_id"])

def verify(root=ROOT,overridden=None):
    root=Path(root)
    facts=build(root)
    assert facts["new_result_records"]==99
    assert facts["results_only_4617_snapshot_sha256"]=="637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89"
    proof=overridden if overridden is not None else json.loads((root/PROOF).read_text(encoding="utf-8"))
    if (proof.get("schema")!="263_COMPLETED_43_PRIMARY_PUBLIC_SCORE_LINKS_V1"
        or proof.get("cohort")!="99_COMPLETED_RESULTS_RESEARCH_EVIDENCE_UPGRADE_ONLY"
        or proof.get("reviewed_records")!=43
        or proof.get("network_fetched_live_by_ci") is not False
        or proof.get("all_43_official_provider_unique_match_ids_verified") is not False
        or proof.get("model_training_input_changed") is not False
        or proof.get("old_4518_records_changed") is not False
        or proof.get("source_grades")!={GRADE:43}):
        raise Unsafe("PROVENANCE_CONTRACT_NOT_RESEARCH_ONLY")
    all_old=load_archive(root)["records"]
    secondary={key(x):x for x in all_old if x["source_class"]=="PUBLIC_SECONDARY_SCORE_WITH_PARTIAL_OFFICIAL_FIXTURE"}
    if len(secondary)!=43:raise Unsafe("ORIGINAL_99_SECONDARY_COUNT_CHANGED")
    seen=set();counts=Counter()
    for x in proof.get("records",[]):
        k=key(x)
        if k in seen or k not in secondary:raise Unsafe("DUPLICATE_OR_UNMATCHED_SECONDARY")
        seen.add(k)
        original=secondary[k]
        if (type(x["home_goals"]) is not int or type(x["away_goals"]) is not int
            or (x["home_goals"],x["away_goals"])!=(original["home_goals"],original["away_goals"])
            or x.get("home_alias")!=original.get("home_name")
            or x.get("away_alias")!=original.get("away_name")):
            raise Unsafe("OFFICIAL_SCORE_NOT_EQUAL_TO_FROZEN_99")
        u=urlsplit(x.get("score_source_url",""))
        if (u.scheme!="https" or u.hostname not in HOSTS[x["league"]] or not u.path
            or u.port or u.username or u.password
            or x.get("primary_evidence_grade")!=GRADE):
            raise Unsafe("PRIMARY_SITE_OR_EVIDENCE_GRADE_INVALID")
        if x["league"]=="BEL1" and not ("/matchs/" in u.path or "/match/" in u.path):
            raise Unsafe("BELGIAN_MATCH_LEVEL_URL_REQUIRED")
        if x["league"]=="POR1" and not u.path.startswith("/video/"):
            raise Unsafe("PORTUGUESE_EXPLICIT_SCORELINE_VIDEO_REQUIRED")
        if (x.get("official_unique_provider_match_id_attested") is not False
            or x.get("independently_fetched_and_parsed_by_ci") is not False):
            raise Unsafe("FABRICATED_PROVIDER_ATTESTATION")
        if x.get("manual_web_review_day")!="2026-11-10":
            raise Unsafe("REVIEW_DATE_REQUIRED")
        counts[x["league"]]+=1
    if set(seen)!=set(secondary) or len(seen)!=43:
        raise Unsafe("NOT_ALL_43_PRIMARY_RESEARCH_LINKS")
    if dict(counts)!={"ENG1":10,"ENG2":15,"BEL1":10,"POR1":8}:
        raise Unsafe("LEAGUE_COUNTS_CHANGED")
    return {
       "schema":"263_43_PRIMARY_PUBLIC_SCORE_RESEARCH_JOIN_AUDIT_V1",
       "status":"43_DIRECT_PRIMARY_PUBLIC_WEB_PAGE_LINKS_JOINED_TO_ORIGINAL_99",
       "matches":43,"league_breakdown":dict(counts),
       "original_score_conflicts":0,"original_4518_changed":False,
       "4617_training_input_sha_unchanged":True,
       "primary_site_url_grade":43,
       "independent_network_score_attestations_by_this_CI":0,
       "per_match_provider_ids_independently_attested_by_CI":0,
       "original_old_SHA_sealed_predictions_unchanged":True,
       "betting_authorized":False,
       "limitations":[
         "Primary official public result URLs manually researched and associated with each game",
         "URL+match+score integrity DOES NOT itself prove page contents or official score ID",
         "Some EFL press pages dynamically render scores; source-page score extraction requires follow-up provider verification",
         "No 99-score rewrite or official model promotion performed"]
    }

if __name__=="__main__":
    print(json.dumps(verify(),ensure_ascii=False,indent=2))
