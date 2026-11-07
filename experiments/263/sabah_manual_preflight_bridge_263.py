"""Explicit operator bridge: today's official preflight -> reviewed new100 manifest.

PREVIEW: zero side effects. AUTHORIZE: only after fresh same-day user command,
with exact selected fixture IDs and the operator's explicit CLI attestation.
Writing the file alone does not activate a GitHub action. A separate Git commit
of one ADDED file in sabah_requests is needed. The live named official gate
still validates each match afresh, so preflight is NOT a pilot seal.
"""
from __future__ import annotations
import argparse,json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from sabah_10league_manifest_preflight_263 import SCHEMA as PREFLIGHT
from sabah_manual_window_263 import in_manual_window
from sabah_batch_263 import named
TR=ZoneInfo("Europe/Istanbul")
OUT_SCHEMA="263_EXPLICIT_USER_DAY_MANIFEST_PREPARATION_V1"
REQUEST="SABAH_TOPLU_V1"
class BridgeBlocked(ValueError):pass

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,
        separators=(",",":")).encode("utf-8")).hexdigest()

def _clock(now):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise BridgeBlocked("AWARE_TIME_REQUIRED")
    if not in_manual_window(now):raise BridgeBlocked("OUTSIDE_USER_ANALYSIS_WINDOW")
    return now.astimezone(timezone.utc)

def review(preflight,*,now=None):
    now=_clock(now)
    if not isinstance(preflight,dict) or preflight.get("schema")!=PREFLIGHT:
        raise BridgeBlocked("INVALID_OFFICIAL_PREFLIGHT")
    day=now.astimezone(TR).date().isoformat()
    if preflight.get("day_turkey")!=day:raise BridgeBlocked("NOT_SAME_TURKEY_DAY")
    checked=datetime.fromisoformat(str(preflight.get("checked_at_utc","")).replace("Z","+00:00"))
    if checked.tzinfo is None:raise BridgeBlocked("UNTRUSTED_PREFLIGHT_CLOCK")
    age=(now-checked.astimezone(timezone.utc)).total_seconds()
    if not 0<=age<=600:raise BridgeBlocked("OFFICIAL_OBSERVATION_OLDER_THAN_10MIN_OR_FUTURE")
    if preflight.get("league_count")!=10 or len(preflight.get("source_coverage",[]))!=10:
        raise BridgeBlocked("INCOMPLETE_TEN_LEAGUE_AUDIT")
    if preflight.get("candidate_count")!=len(preflight.get("candidates",[])):
        raise BridgeBlocked("PREFLIGHT_COUNT_MISMATCH")
    if preflight.get("does_not_write_pilot_or_place_bets") is not True or preflight.get("bookmaker_api_calls")!=0:
        raise BridgeBlocked("PREFLIGHT_SIDE_EFFECT_FLAG_INVALID")
    seen=set();selected=[]
    for r in preflight["candidates"]:
        if not isinstance(r,dict) or r.get("status")!="CANONICAL_OFFICIAL_PAGE_CANDIDATE_REQUIRES_FRESH_NAMED_GATE":
            raise BridgeBlocked("NOT_CANONICAL_OFFICIAL_CANDIDATE")
        required=("league","home","away","home_id","away_id","kickoff_utc",
                  "official_source_url","official_html_sha256")
        if any(not isinstance(r.get(k),str) or not r[k].strip() for k in required):
            raise BridgeBlocked("MISSING_OFFICIAL_PROVENANCE")
        try:ko=datetime.fromisoformat(r["kickoff_utc"].replace("Z","+00:00"))
        except ValueError as e:raise BridgeBlocked("INVALID_KICKOFF") from e
        if ko.tzinfo is None:raise BridgeBlocked("NAIVE_KICKOFF")
        ko=ko.astimezone(timezone.utc)
        if ko.astimezone(TR).date().isoformat()!=day or (ko-now).total_seconds()<=120:
            continue # no backdated or imminent pilot request
        if len(r["official_html_sha256"])!=64 or any(c not in "0123456789abcdef" for c in r["official_html_sha256"]):
            raise BridgeBlocked("INVALID_SOURCE_HASH")
        key=(r["league"],r["home_id"],r["away_id"],r["kickoff_utc"])
        if key in seen:raise BridgeBlocked("DUPLICATE_CANDIDATE")
        seen.add(key)
        selected.append({k:r[k] for k in required})
    return {"schema":OUT_SCHEMA,"day_turkey":day,"checked_at_utc":checked.isoformat(),
            "reviewed_at_utc":now.isoformat(),"preflight_sha256":digest(preflight),
            "candidates":selected,"candidate_count":len(selected),
            "all_leagues_fully_covered":False,"unresolved_league_blockers":[
                {"league":r["league"],"reason":r.get("blocker"),"fallback":r.get("fallback_status")}
                for r in preflight["source_coverage"]
                if r.get("same_day_canonical_timed_candidates")==0],
            "not_a_verified_live_named_gate":True,"not_a_pilot_seal":True,
            "odds_api_calls":0,"model_executions":0}

def prepare(preflight,chosen_ids,*,command_authorized=False,now=None):
    """Explicit operator action after user's current-day analysis request."""
    if command_authorized is not True:
        raise BridgeBlocked("USER_ANALYSIS_COMMAND_REQUIRED")
    data=review(preflight,now=now)
    if not isinstance(chosen_ids,list) or not chosen_ids or len(chosen_ids)>100:
        raise BridgeBlocked("EMPTY_OR_OVERSIZED_SELECTION")
    available={(r["league"],r["home_id"],r["away_id"],r["kickoff_utc"]):r
               for r in data["candidates"]}
    selected=[];seen=set()
    for item in chosen_ids:
        if not isinstance(item,dict) or set(item)!=set(("league","home_id","away_id","kickoff_utc")):
            raise BridgeBlocked("ONLY_EXACT_OFFICIAL_ID_SELECTION")
        key=tuple(item[x] for x in ("league","home_id","away_id","kickoff_utc"))
        if key in seen:raise BridgeBlocked("DUPLICATE_USER_SELECTION")
        seen.add(key)
        if key not in available:raise BridgeBlocked("NOT_IN_FRESH_OFFICIAL_OBSERVATION")
        x=available[key]
        selected.append({"league":x["league"],"home":x["home"],"away":x["away"]})
    return {"schema":REQUEST,"day_turkey":data["day_turkey"],"matches":selected}

def save_request(path,request):
    path=Path(path)
    parts=path.parts
    if len(parts)!=4 or parts[:3]!=("experiments","263","sabah_requests") or path.suffix!=".json":
        raise BridgeBlocked("ONLY_USER_NAMED_REQUEST_CHANNEL")
    # A preparatory local file; separate intentional Git commit triggers live model workflow.
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        json.dump(request,f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
    named("new100",request["day_turkey"],path)
    return path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--preflight",required=True)
    p.add_argument("--mode",choices=("review","prepare"),required=True)
    p.add_argument("--selection")
    p.add_argument("--user-command-authorized",action="store_true")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    with open(a.preflight,encoding="utf-8") as f:preflight=json.load(f)
    if a.mode=="review":
        out=review(preflight)
    else:
        if not a.selection:raise BridgeBlocked("SELECTION_FILE_REQUIRED")
        with open(a.selection,encoding="utf-8") as f:ids=json.load(f)
        out=prepare(preflight,ids,command_authorized=a.user_command_authorized)
    path=Path(a.output)
    if a.mode=="prepare":save_request(path,out)
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("x",encoding="utf-8") as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write("\n")
    print(json.dumps({"mode":a.mode,"day_turkey":out["day_turkey"],
                      "matches":len(out.get("matches",out.get("candidates",[]))),
                      "pilots_sealed":0,"bookmaker_api_calls":0},ensure_ascii=False))
if __name__=="__main__":main()
