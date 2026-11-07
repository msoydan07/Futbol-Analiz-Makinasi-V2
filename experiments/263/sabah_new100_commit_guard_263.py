"""Fail-closed new100 GitHub commit and mobile/SHA receipt gate.

Only NEW named pre-KO real forecasts are eligible. No model modification,
no bookmaker, no 96/acceptance3 reclassification, no back-dated registration.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
from forward_c3 import read_aware
from sabah_batch_263 import SCHEMA,DIRS,sha,precommit
from sabah_mobile_screens_263 import build,load_row,decision
from market_fifth_baseline_263 import sealed_payload

RECEIPT="263_NEW100_FORWARD_MOBILE_ACCEPTANCE_V1"
MODELS=("B","C2","C3","M4")
class PilotBlocked(ValueError):pass

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))

def verify(report_path,mobile_dir,*,root=".",now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise PilotBlocked("AWARE_TIME_REQUIRED")
    now=now.astimezone(timezone.utc)
    root=Path(root)
    report=read(report_path)
    if (report.get("schema")!=SCHEMA or report.get("cohort")!="new100"
        or report.get("payload_sha256")!=sha({k:v for k,v in report.items()
                                               if k!="payload_sha256"})):
        raise PilotBlocked("UNSEALED_OR_WRONG_COHORT_REPORT")
    rows=report.get("outcomes")
    if (not isinstance(rows,list) or not 1<=len(rows)<=100
        or report.get("input_count")!=len(rows)
        or report.get("odds_api_calls")!=0
        or report.get("betting_authorized") is not False
        or report.get("official_S1_S2_approved") is not False):
        raise PilotBlocked("INPUT_COUNT_OR_NO_ODDS_POLICY_INVALID")
    new=[r for r in rows if r.get("status")=="REGISTERED_FOUR_MODELS_EXPERIMENTAL"]
    blocked=[r for r in rows if r.get("status")=="BLOCKED_NO_FORECAST"]
    previous=[r for r in rows if r.get("status")=="ALREADY_SEALED_UNCHANGED"]
    if (len(new)!=report.get("new_forecasts") or len(blocked)!=report.get("blocked")
        or len(previous)!=report.get("already_sealed")
        or len(new)+len(blocked)+len(previous)!=len(rows)):
        raise PilotBlocked("UNRECOGNISED_OR_MISCOUNTED_ROW_STATUS")
    if not new:raise PilotBlocked("ZERO_NEW_USER_PILOT_FORECASTS_CANNOT_BE_SEALED")
    # Every new forecast must still be at least 2 minutes before its KO.
    precommit(report,root,now=now)
    summary,singles=build(root,report)
    mobile=Path(mobile_dir)
    if (mobile/"summary.md").read_text(encoding="utf-8")!=summary:
        raise PilotBlocked("MOBILE_SUMMARY_NOT_REPRODUCIBLE")
    if {p.name for p in (mobile/"matches").glob("*.md")}!={n+".md" for n in singles}:
        raise PilotBlocked("MOBILE_SINGLE_FILENAMES_NOT_EXACT")
    if len(singles)!=len(new):
        raise PilotBlocked("MOBILE_COUNT_DIFFERS_FROM_NEW_FORECASTS")
    evidence=[]
    unique_keys=set()
    for row in new:
        rel=row.get("forecast_path","")
        if not re.fullmatch(r"forward_morning_263/\d{4}-\d{2}-\d{2}/[0-9a-f]{24}\.json",rel):
            raise PilotBlocked("FORECAST_NOT_INSIDE_NEW100")
        f=load_row(root,row)
        fixture=f.get("fixture",{})
        key=(fixture.get("league"),fixture.get("home_id"),
             fixture.get("away_id"),fixture.get("kickoff_utc"))
        if key in unique_keys:raise PilotBlocked("DUPLICATE_NEW100_FIXTURE")
        unique_keys.add(key)
        if fixture.get("league")!=row.get("league"):
            raise PilotBlocked("SOURCE_FIXTURE_LEAGUE_MISMATCH")
        if fixture.get("match_local_date")!=report["day_turkey"]:
            raise PilotBlocked("SOURCE_FIXTURE_TURKEY_DATE_MISMATCH")
        if (f.get("status")!="EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING"
            or fixture.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE"
            or f.get("data",{}).get("snapshot_acceptance")!="APPEND_ONLY_HUMAN_SOURCE_ATTESTED_NOT_INDEPENDENTLY_RECHECKED"):
            raise PilotBlocked("OFFICIAL_RESEARCH_ONLY_SOURCE_INVALID")
        model_results=f.get("model_predictions",{})
        if set(model_results)!=set(MODELS):
            raise PilotBlocked("ALL_FOUR_MODELS_MUST_BE_ATTEMPTED")
        statuses={name:model_results[name].get("status") for name in MODELS}
        available=sum(v=="AVAILABLE" for v in statuses.values())
        if (available<3 or statuses["C3"]!="AVAILABLE" or statuses["M4"]!="AVAILABLE"
            or statuses["B"] not in ("AVAILABLE","UNAVAILABLE_INSUFFICIENT_CONTEXT")
            or statuses["C2"] not in ("AVAILABLE","UNAVAILABLE")):
            raise PilotBlocked("MODEL_READINESS_OR_UNAVAILABLE_STATUS_INVALID")
        if statuses["C2"]=="UNAVAILABLE" and not model_results["C2"].get("reason"):
            raise PilotBlocked("C2_MISSING_REASON")
        stem=Path(rel).stem
        page=mobile/"matches"/(stem+".md")
        if page.read_text(encoding="utf-8")!=singles[stem]:
            raise PilotBlocked("SINGLE_MOBILE_CHANGED_AFTER_SEAL")
        d=decision(root,"new100",report["day_turkey"],stem,f)
        if d is None or d.get("status")!="RESEARCH_PAS":
            raise PilotBlocked("NO_VERIFIED_CALIBRATION_PAS")
        if (d.get("betting_authorized") is not False
            or d.get("quote_sha256") is not None
            or d.get("main_candidate") is not None
            or d.get("alternative_candidate") is not None
            or d.get("forecast_sha256")!=f["payload_sha256"]
            or row.get("decision_status")!=d["status"]
            or row.get("decision_sha256")!=d["payload_sha256"]):
            raise PilotBlocked("DECISION_OR_SOURCE_SHA_NOT_RECONCILED")
        base=root/"experiments/263/sabah_research/new100"/report["day_turkey"]/stem/"baseline.json"
        baseline=read(base)
        if (baseline.get("payload_sha256")!=sha({k:v for k,v in baseline.items()
                                                  if k!="payload_sha256"})
            or baseline.get("forecast_sha256")!=f["payload_sha256"]
            or d.get("baseline_sha256")!=baseline["payload_sha256"]):
            raise PilotBlocked("BASELINE_FORECAST_LINK_INVALID")
        if not (read_aware(f["created_at_utc"])<=read_aware(d["created_at_utc"])<=now):
            raise PilotBlocked("UNSAFE_PREMATCH_TIMING")
        evidence.append({
            "fixture":row["home"]+" - "+row["away"],"league":row["league"],
            "forecast_path":rel,"forecast_sha256":f["payload_sha256"],
            "baseline_sha256":baseline["payload_sha256"],
            "decision_sha256":d["payload_sha256"],
            "mobile_sha256":digest(page),"kickoff_utc":fixture["kickoff_utc"],
            "model_statuses":statuses,"available_models":available})
    outcome={
        "schema":RECEIPT,"cohort":"new100","day_turkey":report["day_turkey"],
        "checked_at_utc":now.isoformat(),
        "batch_report_sha256":report["payload_sha256"],
        "mobile_summary_sha256":digest(mobile/"summary.md"),
        "input_count":len(rows),"new_count":len(new),
        "blocked_count":len(blocked),"existing_same_cohort_count":len(previous),
        "previous_96_and_acceptance3_unchanged":True,
        "all_new_records_are_before_kickoff":True,
        "mobile_sha_equal_to_seal":True,
        "no_verified_odds":True,"decisions":"RESEARCH_PAS",
        "minimum_available_models":3,"mandatory_models":["C3","M4"],
        "bookmaker_api_calls":0,"betting_authorized":False,
        "records":evidence}
    outcome["payload_sha256"]=sha(outcome)
    return outcome

STABLE=("schema","cohort","day_turkey","batch_report_sha256",
        "mobile_summary_sha256","input_count","new_count","blocked_count",
        "existing_same_cohort_count","previous_96_and_acceptance3_unchanged",
        "all_new_records_are_before_kickoff","mobile_sha_equal_to_seal",
        "no_verified_odds","decisions","minimum_available_models",
        "mandatory_models","bookmaker_api_calls","betting_authorized","records")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",required=True);p.add_argument("--mobile",required=True)
    p.add_argument("--receipt",required=True);p.add_argument("--check-existing",action="store_true")
    a=p.parse_args()
    out=verify(a.report,a.mobile)
    dest=Path(a.receipt)
    if a.check_existing:
        receipt=read(dest)
        if receipt.get("payload_sha256")!=sha({k:v for k,v in receipt.items()
                                               if k!="payload_sha256"}):
            raise PilotBlocked("RECEIPT_SHA_TAMPERED")
        if any(receipt.get(k)!=out.get(k) for k in STABLE):
            raise PilotBlocked("RECEIPT_NOT_REPRODUCIBLE")
        print("NEW100_PREPUSH_RECHECK_OK",out["new_count"])
        return
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf-8") as f:
        json.dump(out,f,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)
        f.write("\n")
    print("NEW100_MOBILE_SHA_SEALED",out["new_count"],"RESEARCH_PAS_NO_ODDS")
if __name__=="__main__":main()
