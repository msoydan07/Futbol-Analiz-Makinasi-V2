"""Read-only same-day official source coverage diagnostic for pinned 96 candidates.

No prediction, score, bookmaker request or permanent match registration.
A retrieved official page is only one evidence source; missing or date-only
rows remain blocked until the separate live canonical named-match gate passes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from sabah_fixture_rotation_263 import validate_legacy_candidates
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway
from official_page_lookup_263 import official_page_lookup

SCHEMA="SABAH_RESMI_KAYNAK_KAPSAM_ON_DENETIM_V1"
TR=ZoneInfo("Europe/Istanbul")
def inspect(day,source,*,gateway=None,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError("AWARE_TIME_REQUIRED")
    if day!=now.astimezone(TR).date().isoformat():
        raise ValueError("SOURCE_PROBE_ONLY_CURRENT_TURKEY_DATE")
    raw=Path(source).read_bytes()
    blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if blob!="803378e8ef0f1f285a3393a7231567eea8f25e80":
        raise ValueError("PINNED_96_SOURCE_CHANGED")
    data=json.loads(raw)
    matches=[{"league":r["league"],"home":r["home"],"away":r["away"]}
             for r in validate_legacy_candidates(data) if r["date"]==day]
    gateway=gateway or OfficialFixtureGateway(clock=lambda:now)
    statuses=Counter();rows=[]
    # _get is cached by league: at most one HTTP page per league.
    for match in matches:
        league=match["league"]
        entry=gateway._get(league)
        row={"league":league,"home":match["home"],"away":match["away"],
             "status":"NOT_VERIFIED",
             "source_url":entry["effective_url"] or entry["source_url"],
             "official_html_sha256":entry["html_sha256"],
             "page_fetch":entry["status"],"parser":None,"kickoff_utc":None,
             "not_final_named_gate":True}
        if entry["status"]=="FETCHED_OFFICIAL_PAGE":
            observation=official_page_lookup(
                league,match["home"],match["away"],now=now,
                source_url=entry["effective_url"],html=entry["html"],
                same_team=lambda a,b:gateway._same(league,a,b))
            row["parser"]=observation.get("source_parser")
            status=observation.get("status")
            if status=="VERIFIED_OFFICIAL_FIXTURE":
                row["status"]="TIMED_OFFICIAL_PAGE_MATCH_NEEDS_NAMED_GATE"
                row["kickoff_utc"]=observation["kickoff_utc"]
            elif status=="VERIFIED_OFFICIAL_FIXTURE_DATE_ONLY":
                row["status"]="DATE_ONLY_NO_LIVE_KICKOFF"
            else:
                row["status"]="SOURCE_PAGE_MATCH_NOT_VERIFIED"
                row["reason"]=observation.get("reason")
        else:
            row["status"]="SOURCE_PAGE_FETCH_NOT_VERIFIED"
        statuses[row["status"]]+=1
        rows.append(row)
    return {"schema":SCHEMA,"day_turkey":day,
            "observed_at_utc":now.astimezone(timezone.utc).isoformat(),
            "cohort":"legacy96","candidate_count":len(matches),
            "counts":dict(statuses),"league_sources":gateway.coverage(),
            "candidates":rows,
            "zero_model_calculations":True,"new_forward_record_count":0,
            "no_Pinnacle_or_other_bookmaker_calls":True,
            "not_an_official_named_fixture_acceptance":True,
            "no_final_rotation_conclusion":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--day",required=True)
    p.add_argument("--source",default="experiments/263/local_leagues/2026-11-06_09_10_league_date_only_candidates.json")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    x=inspect(a.day,a.source)
    dst=Path(a.out);dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open("x",encoding="utf-8") as f:
        json.dump(x,f,indent=2,sort_keys=True,ensure_ascii=False);f.write("\n")
    print(json.dumps({"day":a.day,"candidates":x["candidate_count"],
                      "statuses":x["counts"],"sources":{k:v["status"] for k,v in x["league_sources"].items()},
                      "predictions_created":0,"bookmaker_calls":0},ensure_ascii=False))
if __name__=="__main__":main()
