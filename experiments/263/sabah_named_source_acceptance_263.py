"""Read-only, one-pass real official named-match + limited data acceptance audit.

Only the current 96-fixture day, never backdated forecasts; one official
page fetch per league in a single process. Named-match gate is the EXISTING
identity/membership/official validation. Unverified page entries are NEVER
promoted, and no extra league-specific fallback fetches are permitted.
No predictions, bookmaker API calls, model fitting or ledger writes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime,timezone,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from sabah_official_coverage_probe_263 import inspect
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway

SCHEMA="263_SABAH_NAMED_SOURCE_ACCEPTANCE_READONLY_V1"
TR=ZoneInfo("Europe/Istanbul")
FROZEN="35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1"
SOURCE="experiments/263/local_leagues/2026-11-06_09_10_league_date_only_candidates.json"
HISTORY="data/quad_accepted_263/extended_history.csv"
ACCEPTANCE="data/quad_accepted_263/source_acceptance.json"
M4LOCK="experiments/263/m4_lock.json"
M4CODE="experiments/263/m4_integrated.py"
DEVLOCK="experiments/263/forward_dev_calibration_lock_263.json"
class PreflightError(ValueError):pass

def utc(value):
    if not isinstance(value,str):raise PreflightError("TIME_REQUIRED")
    try: dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as e:raise PreflightError("TIME_INVALID") from e
    if dt.tzinfo is None:raise PreflightError("TIMEZONE_REQUIRED")
    return dt.astimezone(timezone.utc)

def digest_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def read_source_readiness(root,now):
    """Integrity + owner research acceptance, NOT a substitute for model verify_snapshot."""
    root=Path(root)
    required=[HISTORY,ACCEPTANCE,M4LOCK,M4CODE,DEVLOCK]
    missing=[path for path in required if not (root/path).is_file()]
    result={"status":"BLOCKED_SOURCE_OR_LOCK_MISSING" if missing else "NOT_ASSESSED",
            "missing":missing,"source_sha256":None,"source_count":None,
            "snapshot_matches_owner_acceptance":False,
            "m4_engine_matches_lock":False,
            "human_acceptance_status":None,
            "owner_review_scope":None,"owner_review_current":False,
            "independently_verified_all_4518":False,
            "betting_authorized":False,
            "data_gate_is_complete_model_verification":False}
    if missing:return result
    accepted=json.loads((root/ACCEPTANCE).read_text(encoding="utf-8"))
    lock=json.loads((root/M4LOCK).read_text(encoding="utf-8"))
    sha=digest_file(root/HISTORY)
    source_ok=(sha==accepted.get("snapshot_sha256")
               and accepted.get("baseline_sha256")==FROZEN
               and accepted.get("status")=="HUMAN_VERIFIED_SOURCE_ACCEPTANCE"
               and accepted.get("schema")=="263_owner_accepted_research_source_v1"
               and accepted.get("research_only") is True
               and accepted.get("betting_authorized") is False
               and isinstance(accepted.get("source_links"),list)
               and len(accepted["source_links"])>0
               and bool(accepted.get("reviewer")))
    time_ok=False
    try:
        reviewed=utc(accepted["reviewed_at_utc"])
        time_ok=reviewed<=now<=reviewed+timedelta(days=7)
    except (KeyError,PreflightError,ValueError):pass
    engine_ok=(lock.get("m4_engine_sha256")==digest_file(root/M4CODE)
               and lock.get("frozen_source_sha256")==FROZEN
               and lock.get("schema")=="m4_dev_lock_263_v1")
    dev=json.loads((root/DEVLOCK).read_text(encoding="utf-8"))
    dev_ok=(dev.get("schema")=="263_forward_dev_calibration_lock_v1"
            and dev.get("official_approval") is False)
    result.update(source_sha256=sha,
                  snapshot_matches_owner_acceptance=source_ok,
                  m4_engine_matches_lock=engine_ok,
                  dev_calibration_lock_research_only=dev_ok,
                  human_acceptance_status=accepted.get("status"),
                  owner_review_scope=accepted.get("review_scope"),
                  owner_review_current=time_ok,
                  independently_verified_all_4518=accepted.get("all_4518_independently_verified") is True,
                  research_only=accepted.get("research_only") is True)
    if source_ok and time_ok and engine_ok and dev_ok:
        result["status"]="OWNER_ACCEPTED_LIMITED_EXPERIMENTAL_INPUTS_ONLY"
    else:result["status"]="BLOCKED_SOURCE_INTEGRITY_OR_REVIEW"
    return result

def named_only_runner(league,home,away,lookup_override=None):
    """Existing named-match gate, but never its separate old network fallback."""
    if lookup_override is None:
        return {"status":"NOT_VERIFIED","reason":"OLDER_FALLBACK_NOT_RETRIED_IN_THIS_AUDIT"}
    from analyze_named_match_gate import run as named_gate
    return named_gate(league,home,away,lookup_override=lookup_override)

def audit(day, *,source=SOURCE,root=".",now=None,gateway=None,preflight=None,
          data_status=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise PreflightError("AWARE_NOW_REQUIRED")
    now=now.astimezone(timezone.utc)
    if day!=now.astimezone(TR).date().isoformat():
        raise PreflightError("AUDIT_ONLY_TODAYS_TURKEY_DAY")
    if gateway is None:
        gateway=OfficialFixtureGateway(
            gate_runner=named_only_runner,
            clock=lambda:datetime.now(timezone.utc))
    if preflight is None:
        preflight=inspect(day,source,gateway=gateway,now=now)
    if preflight.get("day_turkey")!=day or preflight.get("cohort")!="legacy96":
        raise PreflightError("SOURCE_REPORT_WRONG_COHORT_OR_DAY")
    data_status=data_status or read_source_readiness(root,now)
    counters=Counter()
    rows=[]
    for row in preflight["candidates"]:
        outcome={"league":row["league"],"home":row["home"],"away":row["away"],
                 "source_status":row["status"],"source_kickoff_utc":row.get("kickoff_utc"),
                 "source_url":row.get("source_url"),
                 "source_html_sha256":row.get("official_html_sha256"),
                 "gate_status":"NOT_RUN","gate_reason":None,
                 "status":"BLOCKED_NOT_VERIFIED","forecast_generated":False}
        if row["status"]!="TIMED_OFFICIAL_PAGE_MATCH_NEEDS_NAMED_GATE":
            outcome["status"]="BLOCKED_NO_OFFICIAL_KICKOFF_ON_THIS_PAGE"
        else:
            try:
                # Even if kickoff is already past, inspect classification
                # without manufacturing a previous-time prediction.
                gate=gateway.lookup(row["league"],row["home"],row["away"])
                outcome["gate_status"]=gate.get("status","INVALID_GATE")
                outcome["gate_reason"]=gate.get("reason")
                outcome["source_gate_evidence"]=gateway.latest_match_evidence(
                    row["league"],row["home"],row["away"])
                observed=utc(row["kickoff_utc"])
                if gate.get("status")!="VERIFIED":
                    outcome["status"]="BLOCKED_CANONICAL_NAMED_GATE"
                elif utc(gate.get("kickoff_utc"))!=observed:
                    outcome["status"]="BLOCKED_KICKOFF_MISMATCH"
                elif now+timedelta(minutes=2)>=observed:
                    outcome["status"]="BLOCKED_T_MINUS_2_MINS_OR_PAST"
                else:
                    outcome["status"]="OFFICIAL_NAMED_GATE_OK_DATA_REVIEW_SEPARATE"
                    outcome["canonical_home_id"]=gate["home_id"]
                    outcome["canonical_away_id"]=gate["away_id"]
            except (OSError,ValueError,TypeError,KeyError) as err:
                outcome["status"]="BLOCKED_GATE_EXCEPTION"
                outcome["gate_reason"]=type(err).__name__
        counters[outcome["status"]]+=1
        rows.append(outcome)
    return {"schema":SCHEMA,"day_turkey":day,"checked_at_utc":now.isoformat(),
            "fixed_cohort":"legacy96","source_candidates":len(rows),
            "source_timed":sum(r["source_status"]=="TIMED_OFFICIAL_PAGE_MATCH_NEEDS_NAMED_GATE" for r in rows),
            "gate_status_counts":dict(counters),"data_source_preflight":data_status,
            "source_scan_counts":preflight["counts"],
            "official_source_coverage":preflight["league_sources"],
            "fixtures":rows,
            "no_bet_or_market_approval":True,"no_model_calculation":True,
            "new_forward_predictions":0,"pinnacle_calls":0,
            "not_live_full_engine_validation":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--day",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--source-out",required=True)
    p.add_argument("--source",default=SOURCE)
    args=p.parse_args()
    now=datetime.now(timezone.utc)
    gateway=OfficialFixtureGateway(gate_runner=named_only_runner,
                                   clock=lambda:datetime.now(timezone.utc))
    pre=inspect(args.day,args.source,gateway=gateway,now=now)
    report=audit(args.day,source=args.source,now=now,gateway=gateway,preflight=pre)
    for target,data in ((args.source_out,pre),(args.out,report)):
        path=Path(target);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("x",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)
            f.write("\n")
    print(json.dumps({"date":args.day,"candidates":report["source_candidates"],
                      "source_timed":report["source_timed"],
                      "gate":report["gate_status_counts"],
                      "source_readiness":report["data_source_preflight"]["status"],
                      "forecast_writes":0,"bookmaker_calls":0},ensure_ascii=False))
if __name__=="__main__":main()
