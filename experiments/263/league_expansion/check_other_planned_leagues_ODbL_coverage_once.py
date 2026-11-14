#!/usr/bin/env python3
"""ONE allowed OpenLigaDB availability-list read per 2025 and 2026 season.
Find potential rights-clean historic archives for remaining planned leagues.
Metadata-only; no scores, unplayed fixtures, model training or old rechecks.
"""
import argparse,json,re
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
OUT=Path("experiments/263/league_expansion/odbl_openligadb_germany2/odbl_other_planned_leagues_source_catalog_once_20261114.json")
WORDS={
 "ENG5":[r"national league",r"england.*5",r"engl.*5"],
 "ESP2":[r"segunda",r"laliga.?2",r"span.*2",r"espana.*2"],
 "ITA2":[r"serie.?b",r"ital.*2",r"italia.*2"],
 "FRA2":[r"ligue.?2",r"frankreich.*2",r"france.*2"],
 "CHE1":[r"schweiz",r"swiss",r"super league.*ch"],
 "DNK1":[r"denmark",r"danemark",r"danmark",r"superliga"],
 "GER2":[r"2\..*bundesliga",r"2.*bundesliga"],
}
def run():
  found={};other={};calls=0
  for year in (2025,2026):
    url=f"https://api.openligadb.de/getavailableleagues/{year}"
    req=Request(url,headers={"User-Agent":"FutbolAnalizMakinasiResearch/0.1 (+https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2)","Accept":"application/json"})
    with urlopen(req,timeout=24) as resp:raw=resp.read(900_001)
    if len(raw)>900000:raise ValueError("LEAGUE_INDEX_OVERSIZED")
    data=json.loads(raw)
    if not isinstance(data,list):raise ValueError("LEAGUE_INDEX_NOT_A_LIST")
    calls+=1
    matched=[]
    for x in data:
      if not isinstance(x,dict):continue
      name=str(x.get("leagueName") or "")
      short=str(x.get("leagueShortcut") or "")
      if not name or not short:continue
      match=[code for code,pat in WORDS.items() if any(re.search(p,name,re.I) or re.search(p,short,re.I) for p in pat)]
      if match:matched.append({"name":name,"shortcut":short,"match_targets":match,"season":str(x.get("leagueSeason"))})
    found[str(year)]=matched
    other[str(year)]={"response_size_bytes":len(raw),"all_listed_leagues_count":len(data),"candidate_names_count":len(matched)}
  report={"status":"ODBL_OTHER_SEVEN_LEAGUES_METADATA_SOURCE_DISCOVERY_ONLY",
    "captured_at_utc":datetime.now(timezone.utc).isoformat(),"source":"https://api.openligadb.de/getavailableleagues/{year}",
    "license":"ODbL-1.0","season_scans":2,"source_requests":calls,
    "stats":other,"keyword_candidates_NOT_VALIDATED":found,
    "warning":"Match by name is only candidate discovery, never evidence that a league contains the target competition/season or sufficient score rows. Always verify actual teams/season and finished results first.",
    "original_2396_405_and_296_holds_unchanged":True,
    "new_training_rows":0,"new_score_downloads":0,"no_main_M4_or_prior_SHA_changes":True}
  OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  return report
def selftest():
 assert any(re.search(p,"2. Bundesliga",re.I) for p in WORDS["GER2"])
 print("PASS league-name candidate-only; no score claims")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--live",action="store_true");args=p.parse_args()
 if args.self_test:selftest()
 if args.live:
  try:r=run()
  except Exception as e:
   r={"status":"FAIL_CLOSED_LEAGUE_SOURCE_DISCOVERY","error":str(e)[:200] if isinstance(e,ValueError) else "source unavailable","new_training_rows":0}
  print("ODBL_LEAGUES_START")
  print(json.dumps(r,ensure_ascii=False,indent=2))
  print("ODBL_LEAGUES_END")
