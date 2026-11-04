"""One-shot 10-league public-source preflight for 6–8 November 2026.

Reuses existing frozen 4,413-match base, existing season_refresh_263 identity and
append-only reconciliation. Produces STAGED data, NOT human source acceptance,
and does NOT unlock B/C2/C3/M4 forward records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path

from analysis_math_core import load_history
from quality_gate_263 import HISTORICAL_SHA256
from season_refresh_263 import (
    LEAGUES, SOURCE_PREFIX, prepare_refresh, export_snapshot, RefreshError,
)

SCHEMA = "263_weekend_source_live_fetch_preflight_v1"
EXPECTED_STAGED_SHA = "279cb00096da270f6987ae9e518fbe7248c17c993c34508499a971cae76ca4e8"
FIXED_CUTOFF = "2026-11-05"
FIRST_KICKOFF_DAY = "2026-11-06"
MAX_STALE_DAYS = 10


def validate_old_stage(older, newest, *, stage_sha=EXPECTED_STAGED_SHA):
    """No result/identity changes to ANY of the already staged 4,501 fixtures."""
    old_rows, old_meta = load_history(older)
    if old_meta["sha256"] != stage_sha or len(old_rows) != 4501:
        raise RefreshError("prior_4501_stage_hash_or_count_changed")
    new_rows, new_meta = load_history(newest)
    names = tuple(k for k in old_rows[0] if not k.startswith("_"))
    baseline = {r["fixture_id"]: r for r in old_rows}
    present = {r["fixture_id"]: r for r in new_rows}
    if len(present) != len(new_rows) or not baseline.keys() <= present.keys():
        raise RefreshError("staged_4501_fixture_removed_or_duplicate")
    if any(any(a.get(k,"") != present[fid].get(k,"") for k in names)
           for fid,a in baseline.items()):
        raise RefreshError("staged_4501_fixture_score_or_identity_changed")
    return {"prior_4501_sha": old_meta["sha256"],
            "prior_4501_unchanged": len(baseline),
            "new_snapshot_sha": new_meta["sha256"],
            "new_snapshot_rows": len(new_rows)}


def league_cutoff(rows, *, cutoff=FIXED_CUTOFF, target=FIRST_KICKOFF_DAY,
                  maximum=MAX_STALE_DAYS):
    """Mechanical freshness of completed scores, not a guarantee of factual accuracy."""
    c, t = date.fromisoformat(cutoff), date.fromisoformat(target)
    if not c < t:
        raise RefreshError("cutoff_must_precede_target")
    output = {}
    for lg in sorted(LEAGUES):
        season = [r for r in rows if r["league"] == lg and
                  r["season"] == "2026-2027"]
        if not season:
            raise RefreshError("no_current_season_results_"+lg)
        latest = max(date.fromisoformat(r["match_date"]) for r in season)
        lag = (t-latest).days
        if latest >= c:
            raise RefreshError("same_day_or_future_result_in_snapshot_"+lg)
        if lag > maximum or lag <= 0:
            raise RefreshError("league_source_stale_or_future_"+lg)
        output[lg] = {
            "current_season_completed": len(season),
            "last_completed": latest.isoformat(),
            "days_since_last_result_at_first_pilot_day": lag,
            "mechanically_fresh": True,
        }
    return output


def _fetch_one(item):
    lg, code = item
    url = SOURCE_PREFIX + code + ".csv"
    req = urllib.request.Request(url, headers={
        "User-Agent": "FootballResearchAudit/263 (public-season-data; no odds)"})
    with urllib.request.urlopen(req, timeout=35) as response:
        if response.status != 200:
            raise RefreshError("source_status_non_200_"+lg)
        raw = response.read(2_000_001)
        info = dict(response.headers)
    if not (1000 <= len(raw) <= 2_000_000):
        raise RefreshError("source_missing_or_oversize_"+lg)
    # Validate simple CSV columns and number of source season rows in existing code.
    from season_refresh_263 import _csv
    found = _csv(raw)
    receipt = {
        "league": lg, "url": url,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        "http_status": 200, "content_type": info.get("Content-Type"),
        "last_modified_http_claim": info.get("Last-Modified"),
        "etag_http_claim": info.get("ETag"),
        "source_season_rows": len(found),
        "independently_checked_against_official_federation": False,
    }
    return lg, raw, receipt


def stage(*, base_path: Path, earlier_stage: Path, identity_index: Path,
          output_dir: Path, cutoff: str = FIXED_CUTOFF) -> dict:
    if cutoff != FIXED_CUTOFF:
        raise RefreshError("weekend_preflight_cutoff_is_locked")
    if date.today() > date(2026,11,8):
        raise RefreshError("weekend_preflight_after_last_kickoff_forbidden")
    base, base_meta = load_history(base_path)
    if base_meta["sha256"] != HISTORICAL_SHA256 or len(base) != 4413:
        raise RefreshError("frozen_4413_archive_not_intact")
    index = json.loads(identity_index.read_text(encoding="utf-8"))
    receipts = {}
    provided = {}
    # Fetch all 10 once in one bounded batch. Failure does NOT get replaced by
    # cached/stale data. No personal login or non-public bookmaker endpoint.
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(_fetch_one,item) for item in sorted(LEAGUES.items())]
        for future in as_completed(futures):
            lg, content, evidence = future.result()
            provided[lg] = content
            receipts[lg] = evidence
    full, audit = prepare_refresh(base,base_meta,index,provided,cutoff)
    fresh = league_cutoff(full,cutoff=cutoff)
    output_dir.mkdir(parents=True,exist_ok=True)
    audit = export_snapshot(base,full,audit,output_dir)
    preserved = validate_old_stage(earlier_stage,output_dir/"extended_history.csv")
    consistency = all(
        audit["source_file_audit"][lg]["provider_file_sha256"] == receipts[lg]["sha256"]
        for lg in LEAGUES
    )
    if not consistency:
        raise RefreshError("source_receipt_does_not_match_refreshed_data")
    evidence = {
        "schema":SCHEMA, "status":"STAGED_UNVERIFIED_HUMAN_ACCEPTANCE_REQUIRED",
        "created_at_utc":datetime.now(timezone.utc).isoformat(),
        "cutoff_exclusive":cutoff, "pilot_dates":["2026-11-06","2026-11-07","2026-11-08"],
        "10_source_receipts":{lg:receipts[lg] for lg in sorted(receipts)},
        "10_league_freshness": fresh,
        "append_only_proof":preserved,
        "newly_added_versus_old_4501":len(full)-4501,
        "source_status":audit["status"],
        "source_files_cross_checked_against_receipts":consistency,
        "snapshot_sha256":audit["extended_history_sha256"],
        "human_source_acceptance_completed":False,
        "independent_official_result_verification_completed":False,
        "model_pilot_unlocked":False,
        "S1_S2_authorized":False,
        "main_branch_changed":False,
    }
    (output_dir/"preflight_report.json").write_text(
        json.dumps(evidence,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    return evidence


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",required=True)
    ap.add_argument("--prior-stage",default="data/staged_263/extended_history.csv")
    ap.add_argument("--identity-index",default="experiments/263/evidence/identity_index_263.json")
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    result=stage(base_path=Path(a.base),earlier_stage=Path(a.prior_stage),
                 identity_index=Path(a.identity_index),output_dir=Path(a.output))
    print(json.dumps({"status":result["status"],
                      "snapshot_sha256":result["snapshot_sha256"],
                      "total_rows":result["append_only_proof"]["new_snapshot_rows"],
                      "added_since_prior_stage":result["newly_added_versus_old_4501"],
                      "league_freshness":result["10_league_freshness"],
                      "source_acceptance":False},ensure_ascii=False))


if __name__=="__main__":main()
