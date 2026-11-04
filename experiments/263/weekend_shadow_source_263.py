"""Hard-coded Nov4 4509-source artifact guard for research shadow ONLY.

Raw football results are from provider CSVs, independently sourced only for a
subset. Verifies machine data lineage, NEVER declares human source acceptance.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path

SHA="69d687965500a260cc965a1482c23c1e07f11ebcabb1adaa9441dc6a17334a14"
BASE="35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1"
PRIOR="279cb00096da270f6987ae9e518fbe7248c17c993c34508499a971cae76ca4e8"
SOURCE_PREFIX="https://www.football-data.co.uk/mmz4281/2627/"
CODES={"ENG1":"E0","ENG2":"E1","GER1":"D1","ESP1":"SP1","ITA1":"I1",
       "FRA1":"F1","NED1":"N1","TUR1":"T1","POR1":"P1","BEL1":"B1"}

def verify_shadow_evidence(snapshot_sha, n, path, now):
    if snapshot_sha!=SHA or n!=4509:
        raise ValueError("shadow_only_exact_nov4_staged_4509_sha")
    if now.tzinfo is None:raise ValueError("shadow_aware_now_required")
    report=json.loads(Path(path).read_text(encoding="utf-8"))
    if (report.get("schema")!="263_weekend_source_live_fetch_preflight_v1"
        or report.get("status")!="STAGED_UNVERIFIED_HUMAN_ACCEPTANCE_REQUIRED"
        or report.get("snapshot_sha256")!=SHA
        or report.get("source_status")!="STAGED_UNVERIFIED_SOURCE_FILES"
        or report.get("human_source_acceptance_completed") is not False
        or report.get("independent_official_result_verification_completed") is not False
        or report.get("model_pilot_unlocked") is not False
        or report.get("source_files_cross_checked_against_receipts") is not True):
        raise ValueError("shadow_provenance_is_not_machine_preflight")
    proof=report["append_only_proof"]
    if (proof.get("prior_4501_sha")!=PRIOR or
        proof.get("prior_4501_unchanged")!=4501 or
        proof.get("new_snapshot_sha")!=SHA or
        proof.get("new_snapshot_rows")!=4509 or
        report.get("newly_added_versus_old_4501")!=8):
        raise ValueError("shadow_append_only_stage_proof_missing")
    receipts=report.get("10_source_receipts",{})
    if set(receipts)!=set(CODES):
        raise ValueError("shadow_ten_provider_source_receipts_required")
    for lg,code in CODES.items():
        r=receipts[lg]
        if (r.get("league")!=lg or r.get("url")!=SOURCE_PREFIX+code+".csv"
            or r.get("http_status")!=200
            or r.get("independently_checked_against_official_federation") is not False
            or not isinstance(r.get("bytes"),int) or r["bytes"]<=1000
            or not isinstance(r.get("sha256"),str) or len(r["sha256"])!=64):
            raise ValueError("shadow_bad_provider_receipt_"+lg)
    stamp=datetime.fromisoformat(report["created_at_utc"].replace("Z","+00:00"))
    if (stamp.tzinfo is None or stamp>now or
        (now-stamp).total_seconds()>7*86400):
        raise ValueError("shadow_receipts_expired")
    return "PROVISIONAL_RESEARCH_ONLY_NOT_HUMAN_ATTESTATION"
