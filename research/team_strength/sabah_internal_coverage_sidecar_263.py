"""Silent, independent, read-only research sidecar for a *finished* new100 seal.

Never writes under repository, never changes a forecast, odds, market, mobile
view, receipt or business decision. Main GitHub workflow runs the sidecar only
after the normal forecast/PDF work, best-effort with a separate artifact.

These sample-count flags are descriptive engineering hypotheses, NOT a
validated confidence grading and NEVER directly modify an estimated percent.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"experiments/263"))
from sabah_batch_263 import sha as payload_sha
from market_fifth_baseline_263 import sealed_payload
from sabah_new100_commit_guard_263 import RECEIPT
from team_coverage_audit_263 import load_verified_prematch, matchup_check, LEAGUES, EXPECTED

class SidecarBlocked(ValueError):pass
def require(ok,message):
    if not ok:raise SidecarBlocked(message)
def source_json(path):return json.loads(Path(path).read_text(encoding="utf-8"))

def report_and_receipt(root,report_path,receipt_path,history_root):
    root=Path(root).resolve()
    report=source_json(report_path);receipt=source_json(receipt_path)
    require(report.get("schema")=="SABAH_TOPLU_KAYIT_V1" and report.get("cohort")=="new100",
            "NOT_ORIGINAL_NEW100_BATCH_REPORT")
    require(receipt.get("schema")==RECEIPT and receipt.get("cohort")=="new100",
            "NOT_ORIGINAL_NEW100_RECEIPT")
    for name,doc in (("REPORT",report),("RECEIPT",receipt)):
        require(doc.get("payload_sha256")==payload_sha({k:v for k,v in doc.items() if k!="payload_sha256"}),
                "TAMPERED_"+name+"_SHA")
    require(receipt.get("batch_report_sha256")==report["payload_sha256"],
            "RECEIPT_NOT_LINKED_TO_REPORT")
    require(report.get("betting_authorized") is False and receipt.get("betting_authorized") is False,
            "NOT_RESEARCH_ONLY")
    day=report.get("day_turkey")
    require(isinstance(day,str) and re.fullmatch(r"202\d-\d{2}-\d{2}",day),
            "INVALID_MATCH_DAY")
    n=receipt.get("new_count")
    require(type(n) is int and 1<=n<=100 and n==len(receipt.get("records",[])),
            "NO_VALID_NEW_MATCH_RECORDS")
    rows,excluded,policy_sha=load_verified_prematch(day,history_root)
    sidecars=[]
    seen=set()
    for rec in receipt["records"]:
        p=rec.get("forecast_path")
        require(isinstance(p,str) and re.fullmatch(
            r"forward_morning_263/\d{4}-\d{2}-\d{2}/[0-9a-f]{24}\.json",p),
            "UNSAFE_FORECAST_PATH")
        target=(root/p).resolve()
        require(target.is_relative_to(root) and target.is_file(),
                "FORECAST_FILE_NOT_FOUND")
        f=source_json(target)
        sealed_payload(f,"quad_forward_263_v1")
        fx=f["fixture"]
        h=f["payload_sha256"]
        require(h==rec.get("forecast_sha256") and h not in seen,
                "FORECAST_SHA_WRONG_OR_DUPLICATE")
        seen.add(h)
        require(fx["match_local_date"]==day and fx["league"] in LEAGUES
                and fx.get("fixture_verification")=="VERIFIED_BY_LIVE_OFFICIAL_GATE",
                "GATE_OR_DATE_NOT_VERIFIED")
        require((fx["league"],fx["kickoff_utc"])==(rec.get("league"),rec.get("kickoff_utc")),
                "FIXTURE_RECEIPT_IDENTITY_CHANGED")
        require(f.get("data",{}).get("snapshot_sha256")==EXPECTED["source_4617"],
                "NOT_4617_TRAINING_INPUT")
        match=matchup_check(rows,fx["league"],fx["home_id"],fx["away_id"],day)
        sidecars.append({
            "forecast_sha256":h,"league":fx["league"],
            "home":match["home"],"away":match["away"],
            "has_unseen_team":match["has_unseen_team"],
            "has_low_or_stale_context":match["has_low_or_stale_context"]
        })
    return {
        "schema":"263_NEW100_SILENT_TEAM_COVERAGE_SIDECAR_V1",
        "status":"BACKGROUND_READ_ONLY_RESEARCH_NOT_USER_VIEW",
        "day_turkey":day,
        "batch_sha256":report["payload_sha256"],
        "receipt_sha256":receipt["payload_sha256"],
        "new_forecast_count":len(sidecars),
        "outcome_count_with_thin_or_stale_context":sum(x["has_low_or_stale_context"] for x in sidecars),
        "outcome_count_with_unseen_team":sum(x["has_unseen_team"] for x in sidecars),
        "early_awarded_non90min_excluded":len(excluded),
        "training_snapshot_sha256":EXPECTED["source_4617"],
        "forecast_percentages_modified":False,
        "model_coefficients_modified":False,
        "forecast_receipts_modified":False,
        "mobile_report_modified":False,
        "odds_query_count":0,
        "betting_authorized":False,
        "engineering_heuristic_not_empirical_trust_grade":True,
        "records":sidecars,
        "limitations":[
           "Internal sample-count warning only: NOT a calibrated confidence score.",
           "Research report is separate from the user's mobile output.",
           "A failed sidecar cannot block a valid signed forecast or change its odds."
        ]
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--report",required=True)
    parser.add_argument("--receipt",required=True)
    parser.add_argument("--root",default=".")
    parser.add_argument("--out",required=True)
    opts=parser.parse_args()
    target=Path(opts.out).resolve()
    require(not target.is_relative_to(Path(opts.root).resolve()),
            "OUTPUT_MUST_REMAIN_OUTSIDE_GIT_WORKTREE")
    doc=report_and_receipt(opts.root,opts.report,opts.receipt,
                           Path(__file__).resolve().parents[2])
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n",
                      encoding="utf-8")
    print(json.dumps({
       "status":doc["status"],"count":doc["new_forecast_count"],
       "flagged":doc["outcome_count_with_thin_or_stale_context"],
       "probability_modified":False,
    },ensure_ascii=False))

if __name__=="__main__":
    main()
