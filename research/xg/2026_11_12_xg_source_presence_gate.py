#!/usr/bin/env python3
"""One-time source availability probe. Never commits/stores licensed match rows.

Counts only published public CSV xG coverage for five missing leagues across two
seasons. Do not mistake an xG row for a fixture-matched or as-of-verified row.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone

URL_ROOT="https://matchdaysync.com/api/public/csv"
LEAGUES={
    "ENG2":"championship", "NED1":"eredivisie", "TUR1":"super-lig",
    "POR1":"primeira-liga", "BEL1":"belgian-pro-league"
}
SEASONS=("2025-26","2026-27")
FINISHED={"finished","final","full_time","full-time","ft","completed","full time"}
FIELDS={"date","status","home","away","home_goals","away_goals",
        "home_xg","away_xg"}
MAX_BYTES=8_000_000

def valid(x):
    try:
        v=float(x)
        return math.isfinite(v) and 0<=v<=20
    except (ValueError,TypeError):return False

def scan(content):
    if not content.startswith(b"# Source:"):
        raise ValueError("SOURCE_COMMENT_REQUIRED")
    data=content.decode("utf-8-sig").splitlines()
    parsed=csv.DictReader(io.StringIO("\n".join(data[1:])))
    if not parsed.fieldnames or not FIELDS.issubset(set(parsed.fieldnames)):
        raise ValueError("MISSING_EXPECTED_CSV_FIELDS:"+",".join(sorted(set(FIELDS)-set(parsed.fieldnames or []))))
    result={"rows":0,"status_counts":{},"xg_pairs_any_status":0,
            "finished_status_rows":0,"finished_xg_pairs":0,
            "finished_without_pair":0,"ill_formed":0}
    statuses=Counter()
    for row in parsed:
        result["rows"]+=1
        status=(row.get("status") or "").strip().lower()
        statuses[status]+=1
        ready=valid(row.get("home_xg")) and valid(row.get("away_xg"))
        if ready:result["xg_pairs_any_status"]+=1
        if status in FINISHED:
            result["finished_status_rows"]+=1
            if ready and row.get("home_goals") and row.get("away_goals") and row.get("date") and row.get("home") and row.get("away"):
                result["finished_xg_pairs"]+=1
            else:result["finished_without_pair"]+=1
        if not row.get("home") or not row.get("away") or not row.get("date"):
            result["ill_formed"]+=1
    result["status_counts"]=dict(statuses)
    return result

def run():
    results=[]
    for league,slug in LEAGUES.items():
        for season in SEASONS:
            url=f"{URL_ROOT}/{slug}/{season}/matches"
            record={"league":league,"season":season,"url":url,"status":"NOT_FETCHED"}
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"ResearchSourceCoverageAudit/1.0 (documented public CSV, metadata-only; no republishing)","Accept":"text/csv"})
                with urllib.request.urlopen(req,timeout=18) as resp:
                    content_type=resp.headers.get("content-type","")
                    if "csv" not in content_type.lower():raise ValueError("WRONG_CONTENT_TYPE:"+content_type[:64])
                    data=resp.read(MAX_BYTES+1)
                if len(data)>MAX_BYTES:raise ValueError("FILE_TOO_LARGE")
                record.update(scan(data))
                record.update(status="FETCHED_SOURCE_ONLY_UNMATCHED",bytes=len(data),
                              raw_sha256=hashlib.sha256(data).hexdigest())
            except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError,ValueError,UnicodeError) as ex:
                record.update(status="NOT_VERIFIED_NO_MATCH",error=type(ex).__name__+":"+str(ex)[:130])
            results.append(record)
            # Do not hammer public service.
            time.sleep(0.65)
    report={"schema":"263_TEN_PUBLIC_XG_CSV_METADATA_PROBE_V1",
            "checked_utc":datetime.now(timezone.utc).isoformat(),
            "private_raw_rows_uploaded":0,"model_updates":0,"main_changed":False,
            "source_accepted_to_training":0,"provider_live_warning":"restored Oct 11 snapshot, current updates disconnected",
            "not_a_canonical_match_or_asof_check":True,
            "sources":results}
    print(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2))
    print("DONE: fetched=",sum(x["status"]=="FETCHED_SOURCE_ONLY_UNMATCHED" for x in results),
          "out_of_10; source_xg_rows=",sum(x.get("finished_xg_pairs",0) for x in results),
          "; training_accepted=0; user_step=none")
if __name__=="__main__":run()
