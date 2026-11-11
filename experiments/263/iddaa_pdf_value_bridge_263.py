"""One original iddaa PDF -> immutable forecast SHA -> as-of baseline SHA ->
frozen development calibration -> PDF-only main/alt/PAS -> PDF report.

This orchestrator DOES NOT query odds and DOES NOT refit model weights.
Each actual source PDF is re-parsed locally once. Unmatched rows are left
untouched and NEVER block other rows. All candidate decisions are conditional
research based only on the earlier PDF price, not a current quoted price.
"""
from __future__ import annotations
import argparse,copy,json
from datetime import datetime,timezone
from pathlib import Path

from iddaa_pdf_first_quote_263 import verify_original_pdf,build_snapshot
from four_model_value_policy_263 import decide
from forward_calibration_bridge_263 import _digest,CAL_SCHEMA

def _safe(root,filename):
    if not isinstance(filename,str) or not filename.endswith(".json"):
        raise ValueError("ASOF_RESEARCH_PATH_NOT_JSON")
    root=Path(root).resolve()
    path=(root/filename).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("ASOF_RESEARCH_FILE_MISSING_OR_OUTSIDE_REPO")
    return path

def _load(root,rel):
    return json.loads(_safe(root,rel).read_text(encoding="utf-8"))

def _locked(record):
    return (isinstance(record,dict) and record.get("schema")==CAL_SCHEMA
            and record.get("official_approval") is False
            and record.get("development_period")=="2026-08-01/2026-09-30"
            and record.get("payload_sha256")==_digest(
                  {k:v for k,v in record.items() if k!="payload_sha256"}))

def _ensure_true_age_observation(now):
    if now is None:return datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError("PDF_DECISION_AWARE_NOW_REQUIRED")
    return now.astimezone(timezone.utc)

def calibrate_session(bulletin,session,*,original_pdf,repo_root=".",
                      dev_lock_path="experiments/263/forward_dev_calibration_lock_263.json",
                      now=None):
    pdf_sha=verify_original_pdf(original_pdf,bulletin)
    if session.get("pdf_sha256")!=pdf_sha:
        raise ValueError("PDF_FIRST_SOURCE_SHA_CHANGED")
    dev=_load(repo_root,dev_lock_path)
    if not _locked(dev):raise ValueError("PDF_FIRST_FROZEN_DEV_LOCK_INVALID")
    enriched=copy.deepcopy(session)
    extra_ok=0;extra_pas=0
    for row in enriched.get("rows",[]):
        if row.get("status")!="FOUR_MODELS_FORECAST_SHA_CREATED":
            continue
        try:
            forecast=_load(repo_root,row.get("model_forecast_path"))
            baseline=_load(repo_root,row.get("empirical_baseline_path"))
            if (row.get("empirical_baseline_sha256")!=baseline.get("payload_sha256")
                or row.get("model_forecast_sha256")!=forecast.get("payload_sha256")):
                raise ValueError("PDF_FIRST_ROW_SOURCE_SEAL_MISMATCH")
            snap=build_snapshot(bulletin,session,
                session["rows"][row["index"]],forecast,verified_pdf_sha=pdf_sha)
            moment=_ensure_true_age_observation(now)
            result=decide(forecast,baseline,dev,
                          pdf_first_snapshot=snap,now=moment)
            if (result.get("iddaa_pdf_only_seven_markets") is not True
                or result.get("iddaa_pdf_pre_forecast_not_live") is not True
                or result.get("quote_reverified_by_code") is not False
                or result.get("betting_authorized") is not False
                or result.get("official_pilot_count_increment")!=0
                or result.get("iddaa_original_pdf_sha256")!=pdf_sha
                or result.get("iddaa_pdf_first_sha256")!=snap["payload_sha256"]):
                raise ValueError("PDF_FIRST_DECISION_NOT_CONDITIONAL_RESEARCH")
            row["pdf_first_price_snapshot"]=snap
            row["pdf_linked_policy_decision"]=result
            row["value_decision_sha256"]=result["payload_sha256"]
            row["value_decision_status"]=result["status"]
            row["value_decision_price_condition"]="PDF_PRE_FORECAST_NOT_LIVE"
            extra_ok+=1
            if result["main_candidate"] is None:extra_pas+=1
        except (OSError,ValueError,KeyError,AssertionError,
                TypeError,ImportError,AttributeError) as err:
            row["value_decision_status"]="PDF_FIRST_PAS_INSUFFICIENT_EVIDENCE"
            row["value_decision_reason"]=str(err)[:175]
            extra_pas+=1
    enriched["n_pdf_first_decisions"]=extra_ok
    enriched["n_pdf_first_pas_or_blocked"]=extra_pas
    enriched["iddaa_pdf_first_policy"]="EXISTING_FROZEN_DEV_CALIBRATION_SEVEN_USER_MARKETS"
    enriched["source_original_pdf_verified_once_locally"]=True
    enriched["pdf_captured_before_forecast_not_current_quote"]=True
    enriched["new_bookmaker_network_calls"]=0
    enriched["policy_dev_lock_sha256"]=dev["payload_sha256"]
    enriched["pilot_count_changed"]=False
    enriched["signed_research_session_sha256"]=_digest(
        {k:v for k,v in enriched.items() if k!="signed_research_session_sha256"})
    return enriched

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--intake-json",required=True)
    p.add_argument("--session-json",required=True)
    p.add_argument("--original-iddaa-pdf",required=True)
    p.add_argument("--repo-root",default=".")
    p.add_argument("--dev-lock",default="experiments/263/forward_dev_calibration_lock_263.json")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    read=lambda path:json.loads(Path(path).read_text(encoding="utf-8"))
    out=calibrate_session(read(a.intake_json),read(a.session_json),
        original_pdf=a.original_iddaa_pdf,repo_root=a.repo_root,
        dev_lock_path=a.dev_lock)
    dest=Path(a.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf-8") as file:
        json.dump(out,file,sort_keys=True,ensure_ascii=False,indent=2)
        file.write("\n")
    print(json.dumps({"out":str(dest),"n_calibrated":out["n_pdf_first_decisions"],
        "n_pas_or_blocked":out["n_pdf_first_pas_or_blocked"],
        "iddaa_pdf_sha256":out["pdf_sha256"]},ensure_ascii=False))
if __name__=="__main__":main()
