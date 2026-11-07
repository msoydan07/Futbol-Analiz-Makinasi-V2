"""Strict acceptance3 precommit integrity gate for actual morning batch + phone views.

No network calls, no model inference and no odds. Each acceptance3 record
must be: four real available models; linked signed baseline and no-odds PAS
decision; source verified at creation time; before KO at Git push; mobile
summary and per-match page byte-for-byte reproducible from those same seals.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
from forward_c3 import canonical_bytes,read_aware
from market_fifth_baseline_263 import sealed_payload
from sabah_batch_263 import sha,precommit
from sabah_mobile_screens_263 import build,load_row,decision

SCHEMA="263_REAL_MORNING_BATCH_COMMIT_ACCEPTANCE_V1"
MODELS=("B","C2","C3","M4")
class AcceptanceBlocked(ValueError):pass

def digest_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify(report_path,mobile_dir,*,root=".",now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise AcceptanceBlocked("AWARE_CLOCK_REQUIRED")
    root=Path(root)
    report=json.loads(Path(report_path).read_text(encoding="utf-8"))
    if (report.get("cohort")!="acceptance3" or report.get("input_count")!=3
        or report.get("new_forecasts")!=3 or report.get("blocked")!=0
        or report.get("already_sealed")!=0
        or report.get("odds_api_calls")!=0
        or report.get("betting_authorized") is not False
        or len(report.get("outcomes",[]))!=3):
        raise AcceptanceBlocked("THREE_NEW_NOSPORT_ODDS_RECORDS_REQUIRED")
    precommit(report,root,now=now)
    summary, singles=build(root,report)
    mobile=Path(mobile_dir)
    if len(singles)!=3 or (mobile/"summary.md").read_text(encoding="utf-8")!=summary:
        raise AcceptanceBlocked("MOBILE_BATCH_SUMMARY_NOT_REPRODUCIBLE")
    existing={p.name for p in (mobile/"matches").glob("*.md")}
    if existing!={stem+".md" for stem in singles}:
        raise AcceptanceBlocked("MOBILE_MATCH_COUNT_OR_NAMES_CHANGED")
    evidence=[]
    for row in report["outcomes"]:
        if row["status"]!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":
            raise AcceptanceBlocked("ACCEPTANCE_RECORD_NOT_COMPLETE")
        rel=row["forecast_path"]
        if not re.fullmatch(r"forward_acceptance_263/\d{4}-\d{2}-\d{2}/[a-f0-9]{24}\.json",rel):
            raise AcceptanceBlocked("WRONG_ACCEPTANCE_RECORD_FOLDER")
        f=load_row(root,row)
        if set(f.get("model_predictions",{}))!=set(MODELS):
            raise AcceptanceBlocked("ALL_FOUR_MODELS_MUST_BE_ATTEMPTED")
        statuses={k:f["model_predictions"][k].get("status") for k in MODELS}
        available=[m for m in MODELS if statuses[m]=="AVAILABLE"]
        # M4/C3 remain mandatory; B and C2 are diagnostics and can be
        # honestly absent for insufficient context. Never impute their %. 
        if len(available)<3 or any(statuses[x]!="AVAILABLE" for x in ("C3","M4")):
            raise AcceptanceBlocked("CORE_C3_M4_AND_THREE_MODELS_REQUIRED")
        if statuses["B"] not in ("AVAILABLE","UNAVAILABLE_INSUFFICIENT_CONTEXT"):
            raise AcceptanceBlocked("UNKNOWN_B_ABSENCE_STATUS")
        if statuses["C2"] not in ("AVAILABLE","UNAVAILABLE"):
            raise AcceptanceBlocked("UNKNOWN_C2_ABSENCE_STATUS")
        if statuses["C2"]=="UNAVAILABLE" and not f["model_predictions"]["C2"].get("reason"):
            raise AcceptanceBlocked("MISSING_C2_FAILURE_REASON")
        if f["fixture"]["match_local_date"]!=report["day_turkey"]:
            raise AcceptanceBlocked("FIXTURE_DATE_MISMATCH")
        if f["data"].get("snapshot_acceptance")!="APPEND_ONLY_HUMAN_SOURCE_ATTESTED_NOT_INDEPENDENTLY_RECHECKED":
            raise AcceptanceBlocked("SOURCE_NOT_ACCEPTED_LIMITED_RESEARCH")
        if f["status"]!="EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING":
            raise AcceptanceBlocked("PILOT_OR_BETTING_NOT_ALLOWED")
        stem=Path(rel).stem
        page=mobile/"matches"/(stem+".md")
        if page.read_text(encoding="utf-8")!=singles[stem]:
            raise AcceptanceBlocked("MOBILE_SINGLE_NOT_REPRODUCIBLE")
        d=decision(root,report["cohort"],report["day_turkey"],stem,f)
        if d is None or d.get("status")!="RESEARCH_PAS":
            raise AcceptanceBlocked("NO_DECISION_OR_NOT_PAS")
        if (d.get("quote_sha256") is not None or d.get("main_candidate") is not None
            or d.get("alternative_candidate") is not None
            or d.get("betting_authorized") is not False
            or row.get("decision_status")!="RESEARCH_PAS"
            or row.get("decision_sha256")!=d["payload_sha256"]):
            raise AcceptanceBlocked("DECISION_COHERENCE_MISMATCH")
        base=root/"experiments/263/sabah_research"/report["cohort"]/report["day_turkey"]/stem/"baseline.json"
        baseline=json.loads(base.read_text(encoding="utf-8"))
        if (baseline.get("payload_sha256")!=sha({k:v for k,v in baseline.items() if k!="payload_sha256"})
            or baseline.get("forecast_sha256")!=f["payload_sha256"]
            or d.get("baseline_sha256")!=baseline["payload_sha256"]):
            raise AcceptanceBlocked("BASELINE_NOT_SAME_FORECAST")
        if not (read_aware(f["created_at_utc"])<=read_aware(d["created_at_utc"])<=now):
            raise AcceptanceBlocked("DECISION_TIME_INVALID")
        evidence.append({"fixture":row["home"]+" - "+row["away"],"league":row["league"],
                         "forecast_path":rel,"forecast_sha256":f["payload_sha256"],
                         "baseline_sha256":baseline["payload_sha256"],
                         "decision_sha256":d["payload_sha256"],
                         "mobile_match_sha256":digest_file(page),
                         "kickoff_utc":f["fixture"]["kickoff_utc"],
                         "model_statuses":statuses,"model_available_count":len(available)})
    return {"schema":SCHEMA,"cohort":"acceptance3","day_turkey":report["day_turkey"],
            "checked_at_utc":now.astimezone(timezone.utc).isoformat(),
            "batch_report_sha256":report["payload_sha256"],
            "mobile_summary_sha256":digest_file(mobile/"summary.md"),
            "accepted_count":len(evidence),"models_attempted":list(MODELS),
            "c3_m4_mandatory":True,"minimum_models_available_per_match":3,
            "all_predictions_generated_pre_kickoff":True,
            "all_mobile_pages_exactly_reproducible":True,
            "all_decisions":"RESEARCH_PAS",
            "source_review_is_limited_human_attestation":True,
            "pilot_96_or_new100_modified":False,
            "bookmaker_api_calls":0,"betting_authorized":False,
            "records":evidence}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",required=True);p.add_argument("--mobile",required=True)
    p.add_argument("--receipt",required=True)
    p.add_argument("--check-existing",action="store_true")
    a=p.parse_args()
    out=verify(a.report,a.mobile)
    target=Path(a.receipt);target.parent.mkdir(parents=True,exist_ok=True)
    if a.check_existing:
        prior=json.loads(target.read_text(encoding="utf-8"))
        # Times are recorded at the FIRST acceptance check; compare invariant fields.
        for key in ("schema","cohort","day_turkey","batch_report_sha256",
                    "mobile_summary_sha256","accepted_count","models_attempted",
                    "c3_m4_mandatory","minimum_models_available_per_match",
                    "all_predictions_generated_pre_kickoff","all_mobile_pages_exactly_reproducible",
                    "all_decisions","pilot_96_or_new100_modified","bookmaker_api_calls",
                    "betting_authorized","records"):
            if prior[key]!=out[key]:raise AcceptanceBlocked("RECEIPT_NOT_STABLE:"+key)
        print("ACCEPTANCE_RECHECK_OK",out["accepted_count"])
        return
    with target.open("x",encoding="utf-8") as f:
        json.dump(out,f,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)
        f.write("\n")
    print("ACCEPTANCE_PASS",out["accepted_count"],"NO_IMPUTED_MODEL_PAS_MOBILE_MATCH")
if __name__=="__main__":main()
