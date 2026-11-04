"""Independent-looking source CLAIMS must not become automatic source approval.

Scores in a copied manifest matching the CSV are circular, not independent
verification. This read-only audit verifies specific web-result references
were supplied for one example in each league, with stable dates and identities.
It does NOT fetch the external URLs, archive external page bytes or impersonate
a human reviewer. The entire 96-match extra cohort remains unapproved.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

SCHEMA = "263_ten_league_match_specific_external_review_v1"
STAGE_SHA = "69d687965500a260cc965a1482c23c1e07f11ebcabb1adaa9441dc6a17334a14"
SOURCES = {
    "ENG1": "premierleague.com", "ENG2": "efl.com",
    "GER1": "bundesliga.com", "ESP1": "laliga.com",
    "ITA1": "legaseriea.it", "FRA1": "staderennais.com",
    "NED1": "eredivisie.nl", "POR1": "ligaportugal.pt",
    "BEL1": "proleague.be", "TUR1": "beinsports.com.tr",
}
ALLOWED_TIERS = {
    "OFFICIAL_LEAGUE_RESULT_NEWS", "OFFICIAL_LEAGUE_MATCH_PAGE",
    "OFFICIAL_CLUB_MATCH_PAGE", "OFFICIAL_LEAGUE_MATCH_RESULT_RECAP",
    "LICENSED_BROADCASTER_MATCH_REPORT"
}
BANNED_GENERIC_LAST_PART = {
    "results", "fixtures", "programma", "resultados", "uitslagen",
    "index", "calendar", "calendario", "standings", "table"
}


def audit(*, source_rows: dict, evidence: dict) -> dict:
    if not isinstance(evidence, dict) or evidence.get("schema") != SCHEMA:
        raise ValueError("NOT_A_SPECIFIC_SOURCE_REVIEW_MANIFEST")
    if evidence.get("staged_history_sha256") != STAGE_SHA:
        raise ValueError("WRONG_PINNED_HISTORY")
    if evidence.get("human_sources_reviewed") is not False:
        raise ValueError("HUMAN_SOURCE_APPROVAL_NOT_ALLOWED_HERE")
    items = evidence.get("evidence")
    if not isinstance(items, list) or len(items) != len(SOURCES):
        raise ValueError("NEEDS_ONE_SPECIFIC_EXAMPLE_PER_LEAGUE")
    leagues = set()
    matches = set()
    for e in items:
        lg = e.get("league")
        if lg not in SOURCES or lg in leagues:
            raise ValueError("UNKNOWN_OR_DUPLICATE_LEAGUE")
        leagues.add(lg)
        fid = e.get("fixture_id")
        if not isinstance(fid, str) or fid in matches or fid not in source_rows:
            raise ValueError("UNKNOWN_OR_DUPLICATE_FIXTURE")
        matches.add(fid)
        r = source_rows[fid]
        if any(e.get(k) != r.get(k) for k in ("league", "match_date")):
            raise ValueError("WRONG_SOURCE_FIXTURE_IDENTITY")
        if e.get("score") != r["home_goals"] + "-" + r["away_goals"]:
            raise ValueError("WRONG_EXTERNAL_SCORE")
        if not ("2026-10-30" <= e["match_date"] <= "2026-11-01"
                and r["season"] == "2026-2027"):
            raise ValueError("NOT_ONE_OF_PREVIOUS_88")
        if e.get("human_approved") is not False:
            raise ValueError("SYNTHETIC_HUMAN_APPROVAL_FORBIDDEN")
        if e.get("source_tier") not in ALLOWED_TIERS:
            raise ValueError("EVIDENCE_TYPE_NOT_ALLOWED")
        url = e.get("source_url")
        if not isinstance(url,str):
            raise ValueError("NO_SOURCE_URL")
        u = urlparse(url)
        hostname = str(u.hostname or "").lower().removeprefix("www.")
        if (u.scheme != "https" or hostname != SOURCES[lg]
                or u.username or u.password or u.query or u.fragment):
            raise ValueError("SOURCE_DOMAIN_OR_PROTOCOL_MISMATCH")
        path = u.path.rstrip("/").split("/")[-1].lower()
        if (path in BANNED_GENERIC_LAST_PART or len(path) < 12
                or not any(c.isdigit() for c in u.path)):
            # Liga / result reports should identify a concrete competition
            # round/date/year/match or news story, not generic score landing.
            raise ValueError("GENERIC_SOURCE_PAGE_IS_NOT_MATCH_EVIDENCE")
        if not isinstance(e.get("observed_source_text_summary"),str) or len(e["observed_source_text_summary"]) < 22:
            raise ValueError("SPECIFIC_PAGE_OBSERVATION_MISSING")
    if leagues != set(SOURCES):
        raise ValueError("TEN_LEAGUE_EVIDENCE_NOT_COMPLETE")
    return {
        "schema": "263_source_evidence_review_only_v1",
        "status": "SPECIFIC_EXTERNAL_RESULT_PAGES_OBSERVED_NOT_LIVE_MACHINE_AUTHENTICATED",
        "ten_leagues_sampled": len(leagues),
        "specific_external_result_examples": len(matches),
        "previous_88_not_directly_reexamined_as_match_specific": 88-len(matches),
        "new_eight_excluded_from_this_review": 8,
        "source_urls_not_fetched_by_this_python_audit": True,
        "score_matches_staged_rows_not_independent_proof_by_itself": True,
        "human_source_acceptance_complete": False,
        "quad_forward_source_gate_unlocked": False,
        "S1_S2_authorized": False,
        "models_unchanged": True,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--stage",required=True)
    ap.add_argument("--evidence",default="data/staged_263/2026_11_04_ten_league_specific_web_results.json")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    b=Path(args.stage).read_bytes()
    if hashlib.sha256(b).hexdigest()!=STAGE_SHA:
        raise ValueError("CURRENT_4509_SOURCE_SHA_MISMATCH")
    with Path(args.stage).open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=4509 or len({x["fixture_id"] for x in rows})!=4509:
        raise ValueError("WRONG_CURRENT_STAGE_COUNT_OR_DUPLICATE")
    evidence=json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    result=audit(source_rows={x["fixture_id"]:x for x in rows},evidence=evidence)
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    with Path(args.out).open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps(result,ensure_ascii=False))


if __name__=="__main__":
    main()
