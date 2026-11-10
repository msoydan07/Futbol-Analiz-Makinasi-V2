"""Single light source preflight: privacy-safe 10-league current-season audit.

Provider allows light personal/academic downloading at most twice a week.
Fetch each league ONCE in this deliberately one-shot GitHub Actions run.
DO NOT publish raw supplier rows, inferred results or team lists.
Accepted 4518 score snapshot, model files and original sealed records IMMUTABLE.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,urllib.request
from collections import Counter,defaultdict
from datetime import date,datetime
from pathlib import Path
from urllib.parse import urlparse
from data_opponent_goal_audit import read_rows

FEEDS={"ENG1":"E0","ENG2":"E1","GER1":"D1","ESP1":"SP1","ITA1":"I1",
       "FRA1":"F1","NED1":"N1","TUR1":"T1","POR1":"P1","BEL1":"B1"}
BASE="https://www.football-data.co.uk/mmz4281/2627/"
LIMIT_BYTES=2_000_000
USER_AGENT="PrivateResearchFooty263/1.0 (one-time personal noncommercial QA; no bulk scraping)"

def parse_day(raw):
    if not raw:return None
    s=str(raw).strip()
    for pattern in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d"):
        try:return datetime.strptime(s,pattern).date().isoformat()
        except ValueError:pass
    return None

def rows_from_source(data):
    try:text=data.decode("utf-8-sig")
    except UnicodeDecodeError:text=data.decode("latin-1")
    io_file=io.StringIO(text,newline="")
    reader=csv.DictReader(io_file)
    needed={"Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"}
    if not needed.issubset(set(reader.fieldnames or [])):
        raise ValueError("CURRENT_CSV_SCHEMA_MISSING")
    result={}
    for idx,row in enumerate(reader,start=2):
        if row.get("Date") in (None,""):continue
        if idx in result:raise ValueError("PROVIDER_ROW_NOT_UNIQUE")
        result[idx]=row
    return result

def validate_old_anchor(league,code,current,history):
    historical=[r for r in history if r["league"]==league
       and r["season"]=="2026-2027"
       and r.get("source_url","").rstrip("/").endswith(f"/2627/{code}.csv")
       and r.get("source_row","").isdigit()]
    anchored=0;fail=Counter()
    names_to_ids=defaultdict(set)
    ids_to_names=defaultdict(set)
    oldkeys=set()
    for r in historical:
        idx=int(r["source_row"])
        if idx in oldkeys:
            fail["REUSED_SOURCE_ROW"]+=1;continue
        oldkeys.add(idx)
        old=current.get(idx)
        if old is None:
            fail["HISTORICAL_ROW_NO_LONGER_AT_INDEX"]+=1;continue
        date_now=parse_day(old.get("Date"))
        if (date_now!=r["match_date"] or
            old.get("FTHG","")!=r["home_goals"] or
            old.get("FTAG","")!=r["away_goals"] or
            old.get("FTR","")!=r["result"]):
            fail["HISTORICAL_ANCHOR_CHANGED"]+=1;continue
        home=str(old.get("HomeTeam","")).strip()
        away=str(old.get("AwayTeam","")).strip()
        if not home or not away or home==away:
            fail["INVALID_OLD_TEAM_NAMES"]+=1;continue
        anchored+=1
        names_to_ids[home.casefold()].add(r["home_id"])
        names_to_ids[away.casefold()].add(r["away_id"])
        ids_to_names[r["home_id"]].add(home.casefold())
        ids_to_names[r["away_id"]].add(away.casefold())
    # Failing ANY historical exact-row anchor prohibits building new mappings.
    identity_safe=(len(historical)>=20 and anchored==len(historical) and
                   all(len(v)==1 for v in names_to_ids.values()))
    if any(len(v)>1 for v in names_to_ids.values()):
        fail["AMBIGUOUS_NAME_TO_CANONICAL_ID"]+=1
    return identity_safe,anchored,len(historical),dict(fail),names_to_ids

def inspect_feed(league,code,data,history):
    feed=rows_from_source(data)
    latest=max(r["match_date"] for r in history if r["league"]==league)
    safe,anchored,oldcount,fail,names=validate_old_anchor(league,code,feed,history)
    completed=0;postcutoff=0;reasons=Counter()
    for _,r in feed.items():
        when=parse_day(r.get("Date"))
        if when is None:
            reasons["INVALID_PROVIDER_DATE"]+=1;continue
        gh,ga=r.get("FTHG",""),r.get("FTAG","")
        if gh in ("",None) or ga in ("",None):continue
        if not str(gh).isdigit() or not str(ga).isdigit() or (r.get("FTR") not in ("H","D","A")):
            reasons["INVALID_FULLTIME_SCORE"]+=1;continue
        completed+=1
        if when<=latest:continue
        if when>"2026-11-10":
            reasons["FUTURE_RESULT_NOT_ELIGIBLE"]+=1;continue
        postcutoff+=1
        if not safe:reasons["HISTORICAL_SOURCE_CROSSWALK_NOT_ACCEPTED"]+=1;continue
        home=str(r.get("HomeTeam","")).strip().casefold()
        away=str(r.get("AwayTeam","")).strip().casefold()
        if len(names.get(home,set()))!=1 or len(names.get(away,set()))!=1 or home==away:
            reasons["UNRESOLVED_TEAM_CANONICAL_ID"]+=1;continue
        # Counts only; no third-party results persisted here.
        reasons["TEAM_NAME_AND_OLD_SCORE_ANCHOR_RESOLVED_PROVISIONAL_ONLY"]+=1
    return {"provider_url":BASE+code+".csv",
       "provider_payload_sha256":hashlib.sha256(data).hexdigest(),
       "provider_rows_with_a_fulltime_score":completed,
       "accepted_snapshot_latest_match_date":latest,
       "newer_completed_score_rows_candidate_count":postcutoff,
       "historical_provider_source_rows_in_accepted_snapshot":oldcount,
       "historical_exact_row_score_date_anchors":anchored,
       "old_anchor_rejections":fail,"safe_historical_name_to_id_crosswalk":safe,
       "newer_candidate_provisional_identity_summary":dict(reasons),
       "source_status":"SOURCE_IDENTITIES_PROVISIONAL_NEVER_AUTO_APPEND",
       "note":"Provider's league row index and scores checked against owner-accepted old source. Not independent official federation score verification. No raw rows or private data re-published."}

def single_fetch(url):
    if urlparse(url).hostname!="www.football-data.co.uk":
        raise ValueError("UNEXPECTED_PROVIDER_HOST")
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT})
    with urllib.request.urlopen(req,timeout=20) as res:
        data=res.read(LIMIT_BYTES+1)
    if not data or len(data)>LIMIT_BYTES:
        raise ValueError("EMPTY_OR_UNREASONABLY_LARGE_PROVIDER_FEED")
    return data

def audit(source,offline_feeds=None):
    history,_,sha=read_rows(source)
    offline_feeds=offline_feeds or {}
    outputs={}
    for league,code in FEEDS.items():
        url=BASE+code+".csv"
        try:
            blob=offline_feeds[league] if league in offline_feeds else single_fetch(url)
            outputs[league]=inspect_feed(league,code,blob,history)
        except Exception as exc:
            # No retry / no fallback to stale provider labels / no aggressive bot demand.
            outputs[league]={"source_status":"BLOCKED_NO_DATA_APPENDED",
              "provider_url":url,"reason":type(exc).__name__,
              "no_retry_in_this_job":True}
    return {"schema":"263_20261110_LIGHT_CURRENT_SOURCE_SAFETY_PREFLIGHT_V1",
        "source_4518_sha256":sha,
        "provider_usage_policy":"Personal/academic; at most two light downloads per week. One GET per league in this one-shot job. Not commercial machine learning product.",
        "source_data_mutated":False,"model_or_seal_mutated":False,
        "raw_supplier_rows_published":False,"upstream_data_requested_once_each":True,
        "cutoff":"2026-11-10","leagues":outputs,
        "note":"A green workflow is only a read-only source-compatibility audit, not acceptance of fresh goals, club mapping or production forecast use."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data/quad_accepted_263/extended_history.csv")
    p.add_argument("--out",required=True)
    args=p.parse_args();report=audit(args.source)
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():raise ValueError("ONE_TIME_PRELIGHT_REPORT_ALREADY_EXISTS")
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({"league_preflight":{
        k:{i:v.get(i) for i in ("source_status","newer_completed_score_rows_candidate_count",
          "historical_exact_row_score_date_anchors","historical_provider_source_rows_in_accepted_snapshot",
          "safe_historical_name_to_id_crosswalk","reason")}
            for k,v in report["leagues"].items()}},ensure_ascii=False))

if __name__=="__main__":main()
