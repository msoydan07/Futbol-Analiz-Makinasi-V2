#!/usr/bin/env python3
"""One-shot GER2 historical CC0 gap supplement from community-entered ODbL data.

Fetch only OpenLigaDB league shortcut bl2, seasons 2025 and 2026; one request
each. Store a source-licensed, segregated historical *research* archive.
No copying from football-data.co.uk. Source attribution + ODbL share-alike.
NO admission to model training; no main M4, predictions, xG files, or legacy
pinned CC0 research source files are modified. Old records are not retested.
"""
import argparse,csv,hashlib,io,json,re
from collections import Counter
from datetime import datetime,date,timezone
from pathlib import Path
from urllib.request import Request,urlopen

BASE=Path("experiments/263/league_expansion/odbl_openligadb_germany2")
BASE_URL="https://api.openligadb.de/getmatchdata/bl2/"
SNAPSHOT_CUTOFF=date(2026,11,13) # Never archive a same-day unfinished game
LICENCE_URL="https://www.openligadb.de/en/license"
TERMS_URL="https://www.openligadb.de/en/terms-of-use"
HEADER=["league","season","date","kickoff_utc","home","away","ft_home","ft_away",
        "match_id","source_url","source_last_updated_at","archive_observed_at_utc",
        "source_license","research_status"]
def pick_ft(match):
    if not match.get("matchIsFinished"):return None
    candidates=[]
    for x in match.get("matchResults") or []:
        if x.get("resultTypeID") != 2:continue
        a,b=x.get("pointsTeam1"),x.get("pointsTeam2")
        if type(a) is not int or type(b) is not int or not 0<=a<=30 or not 0<=b<=30:
            raise ValueError("BAD_FT_SCORE_SHAPE")
        candidates.append((a,b))
    if len(candidates)!=1:raise ValueError("FINISHED_MATCH_MUST_HAVE_ONE_REAL_FT_RESULT")
    return candidates[0]
def normalize(raw,year,now):
    if not isinstance(raw,list):raise ValueError("SOURCE_NOT_A_MATCH_LIST")
    seenids=set();unique_pairs=set();rows=[];stats=Counter()
    for m in raw:
        if not isinstance(m,dict):raise ValueError("UNEXPECTED_MATCH_ITEM")
        if str(m.get("leagueShortcut","")).lower()!="bl2" or m.get("leagueSeason")!=year:
            raise ValueError("NOT_BL2_EXPECTED_SEASON")
        mid=m.get("matchID")
        if type(mid) is not int or mid in seenids:raise ValueError("MISSING_OR_DUPLICATE_MATCH_ID")
        seenids.add(mid)
        rawtime=m.get("matchDateTimeUTC")
        if not rawtime:raise ValueError("MISSING_KICKOFF")
        kick=datetime.fromisoformat(rawtime.replace("Z","+00:00"))
        if kick.tzinfo is None:raise ValueError("NON_UTC_KICKOFF")
        d=kick.astimezone(timezone.utc).date()
        # Bundesliga dates in Germany can be local-time after midnight UTC,
        # but this is a conservative 2026-11-13 archive cutoff.
        if year==2025 and not date(2025,7,1)<=d<=date(2026,6,30):
            raise ValueError("SEASON_2025_DATE_OUTSIDE_WINDOW")
        if year==2026 and d<date(2026,7,1):
            raise ValueError("SEASON_2026_DATE_OUTSIDE_WINDOW")
        if d>SNAPSHOT_CUTOFF:
            stats["future_or_current_excluded"]+=1
            continue
        ft=pick_ft(m)
        if ft is None:
            stats["unplayed_or_not_final_excluded"]+=1
            continue
        h=(m.get("team1") or {}).get("teamName")
        a=(m.get("team2") or {}).get("teamName")
        if not isinstance(h,str) or not isinstance(a,str) or not h.strip() or not a.strip() or h==a:
            raise ValueError("INVALID_TEAMS")
        k=(d.isoformat(),h.strip(),a.strip())
        if k in unique_pairs:raise ValueError("DUPLICATE_DATE_HOME_AWAY")
        unique_pairs.add(k)
        # matchResults may include half-time; require explicitly full-time typeID==2.
        rows.append({"league":"GER2","season":f"{year}-{str(year+1)[-2:]}",
                     "date":d.isoformat(),"kickoff_utc":kick.astimezone(timezone.utc).isoformat(),
                     "home":h.strip(),"away":a.strip(),
                     "ft_home":ft[0],"ft_away":ft[1],"match_id":mid,
                     "source_url":f"{BASE_URL}{year}",
                     "source_last_updated_at":str(m.get("lastUpdateDateTime") or ""),
                     "archive_observed_at_utc":now,
                     "source_license":"ODbL-1.0",
                     "research_status":"ODBL_HISTORICAL_MATCH_FACTS_QA1_SECOND_INDEPENDENT_SCORE_QA_PENDING__NOT_TRAINING"})
        stats["finished_archived"]+=1
    rows.sort(key=lambda r:(r["date"],r["home"],r["away"]))
    if year==2025 and not 250<=len(rows)<=310:raise ValueError("2025_FINISHED_COUNT_IMPLAUSIBLE")
    if year==2026 and not 55<=len(rows)<=170:raise ValueError("2026_FINISHED_COUNT_IMPLAUSIBLE")
    return rows,dict(stats)
def fetch(year):
    req=Request(BASE_URL+str(year),headers={
        "User-Agent":"FutbolAnalizMakinasiResearch/0.1 (+https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2)",
        "Accept":"application/json"})
    with urlopen(req,timeout=38) as resp:
        raw=resp.read(1_800_001)
    if len(raw)>1_800_000:raise ValueError("API_JSON_OVERSIZE")
    return raw
def build():
    BASE.mkdir(parents=True,exist_ok=True)
    now=datetime.now(timezone.utc).isoformat()
    groups={}
    for year in (2025,2026):
        raw=fetch(year)
        matches=json.loads(raw)
        rows,stats=normalize(matches,year,now)
        if not rows:raise ValueError("NO_COMPLETE_MATCHES")
        out=BASE/f"ger2_{year}_{year+1}_ODbL_research_quarantine.csv"
        with out.open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=HEADER,lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        groups[str(year)]={"path":str(out),"row_count":len(rows),
            "range":[rows[0]["date"],rows[-1]["date"]],
            "source_sha256":hashlib.sha256(raw).hexdigest(),
            "source_size_bytes":len(raw),"stats":stats,
            "unique_match_ids":len({x["match_id"] for x in rows}),
            "finish_count":sum(1 for x in rows if x["research_status"].startswith("ODBL_HISTORICAL"))}
    assert sum(x["row_count"] for x in groups.values())>=310
    lic=BASE/"LICENSE_ATTRIBUTION.md"
    lic.write_text(
        "# OpenLigaDB licensed historical result research archive\n\n"
        "Source: OpenLigaDB (https://www.openligadb.de). "
        "Data from OpenLigaDB (www.openligadb.de), licensed under ODbL 1.0.\n\n"
        "License: https://opendatacommons.org/licenses/odbl/1-0/\n"
        "Source rights: https://www.openligadb.de/en/license\n"
        "API fair-use terms: https://www.openligadb.de/en/terms-of-use\n\n"
        "The CSVs in this directory are an extracted, modified database made available "
        "under ODbL 1.0 with attribution and share-alike; no logos, team icons, "
        "source imagery or player events are stored. "
        "The source is volunteer-entered, provides no historical immutable publication snapshots "
        "and is not proof of match-by-match independent confirmation or pre-kickoff "
        "feature availability. All records remain research quarantine, NOT model training.\n",
        encoding="utf-8")
    report={
      "status":"GER2_2025_2026_ONCE_ODBL_ARCHIVED_RESEARCH_ONLY",
      "snapshot_utc":now,"source":"OpenLigaDB",
      "source_api_endpoints":[BASE_URL+"2025",BASE_URL+"2026"],
      "attribution":"Data from OpenLigaDB (www.openligadb.de), licensed under ODbL 1.0",
      "source_license_url":LICENCE_URL,"api_terms_url":TERMS_URL,
      "source_retrieval_count":2,
      "seasons":groups,
      "total_source_ODbL_rows":sum(x["row_count"] for x in groups.values()),
      "classification":"Separate original ODbL source archive. 2025-26 overlaps the prior CC0 99 rows; do NOT add both as distinct training matches. 2026-27 research season currently had zero pinned research rows.",
      "season_2025_26_overlap_resolution":"PENDING_CANONICAL_TEAM_ALIAS_AND_INDEPENDENT_SCORE_COMPARISON",
      "season_2026_27_score_confirmation":"PENDING_SECOND_INDEPENDENT_MATCH_FACT_WITNESS",
      "source_historical_postgame_vintage":"NO_IMMUTABLE_ASOF_TIME; snapshot time is observation today not score availability before historic kickoff",
      "training_rows_approved":0,"main_M4_and_10_leagues_unchanged":True,
      "prior_2396_quarantine_unchanged":True,"prior_296_holds_unchanged":True,
      "no_old_871_904_score_verification_repeated":True,
      "no_manual_1855_xg_spreadsheet_modified":True,
      "next":"Separate canonical de-duplication of old GER2/2025-26 and independent score QA for new 2026-27; other missing sources via rights-clean providers."
    }
    (BASE/"ger2_2season_archive_report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report
def selftest():
    m={"matchID":123,"matchIsFinished":True,
       "matchResults":[{"resultTypeID":1,"pointsTeam1":0,"pointsTeam2":1},
                       {"resultTypeID":2,"pointsTeam1":2,"pointsTeam2":0}]}
    assert pick_ft(m)==(2,0)
    assert pick_ft(dict(m,matchIsFinished=False)) is None
    try:pick_ft(dict(m,matchResults=m["matchResults"]*2))
    except ValueError:pass
    else:raise AssertionError("AMBIGUOUS_FULLTIME_NOT_BLOCKED")
    print("PASS FT type 2, exclusion of unplayed, ambiguity guard")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if a.self_test:selftest()
    if a.run:
        try:report=build()
        except Exception as e:
            report={"status":"FAIL_CLOSED_NO_NEW_RECORDS_PROMOTED","error_class":type(e).__name__,
                    "reason":str(e)[:180] if isinstance(e,ValueError) else "external source network or HTTP failure",
                    "training_rows_approved":0}
        print("ODBL_GER2_START")
        print(json.dumps(report,ensure_ascii=False,indent=2))
        print("ODBL_GER2_END")
