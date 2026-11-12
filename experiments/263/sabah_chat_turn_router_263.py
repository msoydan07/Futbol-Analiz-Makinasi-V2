"""Safe on-demand chat-to-GitHub request planner for existing 2.6.3 new100.

There is NO daemon listening to chat. An authenticated operator/ChatGPT
connector must create exactly one new GitHub file after an explicit SAME-DAY
user command; that push triggers the existing new100 workflow. This planner
never pushes, prices, forecasts or changes old SHA seals.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from sabah_manual_preflight_bridge_263 import review, prepare, BridgeBlocked
from sabah_batch_263 import keys_in
from market_fifth_baseline_263 import sealed_payload

TR=ZoneInfo("Europe/Istanbul")
COMMANDS={
    "bugünün maçlarını getir",
    "bugunun maclarini getir",
    "bugünün maçlarını analiz et",
    "bugunun maclarini analiz et",
}
SAFE_GIT_MARGIN=timedelta(minutes=20)
MAX_NEW100=100
NEW100="forward_morning_263"
DIRS=("forward_morning_263","forward_quad_263","forward_acceptance_263")

def _clock(now):
    now=now or datetime.now(timezone.utc)
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise BridgeBlocked("ON_DEMAND_AWARE_CLOCK_REQUIRED")
    return now.astimezone(timezone.utc)

def _command(text):
    if not isinstance(text,str):return False
    norm=" ".join(text.strip().casefold().strip(".!?").split())
    if norm.endswith(" ortak"):
        norm=norm[:-6].strip()
    return norm in COMMANDS

def _identity(row):
    return (row["league"],row["home_id"],row["away_id"],
            datetime.fromisoformat(row["kickoff_utc"].replace("Z","+00:00"))
            .astimezone(timezone.utc).isoformat())

def plan(preflight,command,*,now=None,seen=None,used_count=0):
    """Return a pure, explicitly authorized plan with zero side effects.

    A candidate is not yet a verified named-match gate. This plan is *never*
    the final forecast, odds or sealed result.
    """
    now=_clock(now)
    if not _command(command):
        raise BridgeBlocked("EXPLICIT_TODAY_ANALYSIS_COMMAND_REQUIRED")
    if not isinstance(used_count,int) or isinstance(used_count,bool) or not 0<=used_count<=MAX_NEW100:
        raise BridgeBlocked("INVALID_NEW100_CAPACITY_COUNT")
    if not isinstance(seen,set):
        raise BridgeBlocked("ORIGINAL_SEALED_MATCH_KEYS_REQUIRED")
    # Existing manual preflight bridge validates ALL 10 league slots, URL
    # page hashes, fresh checked time and canonical identifiers; we reuse it.
    preview=review(preflight,now=now)
    allowed=[];already=[];too_close=[]
    for row in preview["candidates"]:
        identity=_identity(row)
        ko=datetime.fromisoformat(identity[3])
        if identity in seen:
            already.append(row)
        elif ko-now<SAFE_GIT_MARGIN:
            too_close.append(row)
        else:
            allowed.append(row)
    allowed.sort(key=lambda x:(x["kickoff_utc"],x["league"],x["home_id"],x["away_id"]))
    remaining=MAX_NEW100-used_count
    base={
        "schema":"263_ONDEMAND_TODAY_REQUEST_PLAN_V1",
        "day_turkey":preview["day_turkey"],
        "command":"BUGUNUN_MACLARINI_GETIR",
        "source_age_limit_seconds":600,
        "observed_candidate_count":preflight["candidate_count"],
        "fresh_canonical_count":len(preview["candidates"]),
        "previously_sealed_count":len(already),
        "too_close_for_safe_prematch_git_count":len(too_close),
        "fresh_unsealed_eligible_count":len(allowed),
        "remaining_new100_capacity":remaining,
        "league_coverage_complete":False,
        "unresolved_source_leagues":preview["unresolved_league_blockers"],
        "new_forecasts_written":0,
        "new_pilot_started":False,
        "bookmaker_api_calls":0,
        "git_request_committed":False,
        "workflow_started":False,
        "source_provenance_sha256":preview["preflight_sha256"],
        "candidate_list_not_live_named_gate":True,
    }
    if not allowed:
        return {**base,"status":"NO_NEW_SAFE_OFFICIAL_FIXTURE_NO_REQUEST",
                "request":None,"selection":[]}
    if len(allowed)>remaining:
        # Do not silently drop games or start a new pilot to evade 100 cap.
        return {**base,"status":"INSUFFICIENT_EXISTING_NEW100_CAPACITY_NO_REQUEST",
                "request":None,"selection":[]}
    selection=[{k:r[k] for k in ("league","home_id","away_id","kickoff_utc")}
               for r in allowed]
    # Exact IDs, same-day user command and a still-fresh live preflight.
    request=prepare(preflight,selection,command_authorized=True,now=now)
    return {**base,"status":"SAFE_NAMED_REQUEST_READY_NOT_DISPATCHED",
            "request":request,"selection":selection}

def from_repo(root,preflight,command,*,now=None):
    """Re-verify existing SHA seal files before planning any NEW request."""
    root=Path(root)
    registered=[]
    for part in DIRS:
        for file in sorted((root/part).glob("*/*.json")):
            f=json.loads(file.read_text(encoding="utf-8"))
            sealed_payload(f,"quad_forward_263_v1")
            x=f["fixture"]
            if x["match_local_date"]!=file.parent.name:
                raise BridgeBlocked("HISTORICAL_SEALED_PATH_DATE_MISMATCH")
            registered.append((part,f))
    # Uses the already established exact team ID + kickoff duplicate key.
    keys=keys_in(*(root/part for part in DIRS))
    if len(keys)!=len(registered):
        raise BridgeBlocked("ORIGINAL_SHA_KEY_DUPLICATE_OR_MISSING")
    used=sum(p==NEW100 for p,_ in registered)
    return plan(preflight,command,now=now,seen=keys,used_count=used)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--preflight",required=True)
    parser.add_argument("--command",required=True)
    parser.add_argument("--root",default=".")
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    path=Path(args.preflight)
    source=json.loads(path.read_text(encoding="utf-8"))
    result=from_repo(args.root,source,args.command)
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x",encoding="utf-8") as dest:
        json.dump(result,dest,ensure_ascii=False,sort_keys=True,indent=2)
        dest.write("\n")
    print(json.dumps({"status":result["status"],
        "fresh_candidates":result["fresh_unsealed_eligible_count"],
        "already":result["previously_sealed_count"],
        "capacity":result["remaining_new100_capacity"],
        "request_authorized_but_not_committed":result["request"] is not None,
        "odds_api_calls":0,"forecast_writes":0},ensure_ascii=False))

if __name__=="__main__":main()
