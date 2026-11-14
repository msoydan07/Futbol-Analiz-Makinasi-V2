#!/usr/bin/env python3
"""One-shot Swiss Super League 2025-26 ODbL historical fact source selection.

The TWO source LEAGUE SHORTCUTS are already discovered in the one-time metadata
audit: ch1 and bsl. Query each ONCE, inspect finished proper football fixtures.
Store only highest-coverage structurally validated source under ODbL; never mix
two provider source feeds as if they were distinct matches. No scores from
unlicensed external sites or 2024/25, no new fixture predictions, no M4 changes.
"""
import csv,hashlib,json,re,unicodedata,argparse
from datetime import datetime,date,timezone
from pathlib import Path
from urllib.request import Request,urlopen
BASE=Path("experiments/263/league_expansion/odbl_openligadb_swiss1")
YEAR=2025
SHORTCUTS=("ch1","bsl")
SOURCE="https://api.openligadb.de/getmatchdata/"
SCORE_COLS=["league","season","date","kickoff_utc","home","away","ft_home","ft_away",
 "match_id","source_shortcut","source_url","stage","source_last_updated_at",
 "archive_observed_at_utc","source_license","research_status"]
NAMES={"basel","zurich","young boys","lausanne","luzern","lugano","sion","thun",
       "servette","grasshopper","winterthur","gallen","vaduz"}
def normalize(x):
  x=str(x).casefold().replace("ß","ss")
  x="".join(c for c in unicodedata.normalize("NFKD",x) if not unicodedata.combining(c))
  return re.sub(r"[^a-z0-9]+"," ",x).strip()
def score(x):
  rr=[z for z in (x.get("matchResults") or []) if z.get("resultTypeID")==2]
  if not x.get("matchIsFinished"):return None
  if len(rr)!=1:raise ValueError("FINISHED_WITHOUT_EXACT_FT_RESULT")
  a,b=rr[0].get("pointsTeam1"),rr[0].get("pointsTeam2")
  if type(a) is not int or type(b) is not int or not 0<=a<=30 or not 0<=b<=30:
    raise ValueError("SCORE_MISSING_OR_OUT_OF_RANGE")
  return (a,b)
def source(shortcut):
  url=SOURCE+shortcut+"/"+str(YEAR)
  req=Request(url,headers={"User-Agent":"FutbolAnalizMakinasiResearch/0.1 (+https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2)","Accept":"application/json"})
  with urlopen(req,timeout=36) as res:raw=res.read(1_500_001)
  if len(raw)>1_500_000:raise ValueError("SOURCE_TOO_LARGE")
  data=json.loads(raw)
  if not isinstance(data,list):raise ValueError("SOURCE_NO_MATCHES")
  out=[];seen=set();teams=set();stats={"source_total":len(data),"unplayed":0,"final_extracted":0,"outside_target_window":0}
  now=datetime.now(timezone.utc).isoformat()
  for m in data:
    if m.get("leagueShortcut")!=shortcut or m.get("leagueSeason")!=YEAR:
      raise ValueError("UNEXPECTED_SOURCE_LEAGUE_SEASON")
    kick=m.get("matchDateTimeUTC")
    if not kick:
      if m.get("matchIsFinished"):raise ValueError("PLAYED_MISSING_KICKOFF")
      stats["unplayed"]+=1;continue
    at=datetime.fromisoformat(kick.replace("Z","+00:00"))
    if at.tzinfo is None:raise ValueError("KICKOFF_HAS_NO_TIMEZONE")
    day=at.astimezone(timezone.utc).date()
    if not date(2025,7,1)<=day<=date(2026,6,30):
      stats["outside_target_window"]+=1;continue
    ft=score(m)
    if ft is None:stats["unplayed"]+=1;continue
    home=str((m.get("team1") or {}).get("teamName") or "").strip()
    away=str((m.get("team2") or {}).get("teamName") or "").strip()
    if not home or not away or home==away:raise ValueError("INVALID_FIXTURE_TEAMS")
    mid=m.get("matchID")
    key=(day.isoformat(),normalize(home),normalize(away))
    if not isinstance(mid,int) or key in seen:raise ValueError("SOURCE_IDENTITY_DUPLICATION")
    seen.add(key);teams.update((home,away))
    grp=m.get("group") or {}
    out.append({
      "league":"CHE1","season":"2025-26","date":day.isoformat(),
      "kickoff_utc":at.astimezone(timezone.utc).isoformat(),
      "home":home,"away":away,"ft_home":ft[0],"ft_away":ft[1],"match_id":mid,
      "source_shortcut":shortcut,"source_url":url,
      "stage":str(grp.get("groupName") or "UNDECLARED"),
      "source_last_updated_at":str(m.get("lastUpdateDateTime") or ""),
      "archive_observed_at_utc":now,
      "source_license":"ODbL-1.0",
      "research_status":"ODBL_SWISS_HISTORIC_RESULT_CANDIDATE_SECOND_FT_QA_AND_ASOF_PENDING__NO_MODEL_TRAINING"
    })
    stats["final_extracted"]+=1
  out.sort(key=lambda x:(x["date"],x["home"],x["away"]))
  match_names={word for n in teams for word in NAMES if word in normalize(n)}
  stats["unique_clubs"]=len(teams)
  stats["swiss_club_keyword_hits"]=len(match_names)
  stats["club_name_examples"]=sorted(teams)[:15]
  stats["source_sha256"]=hashlib.sha256(raw).hexdigest()
  stats["source_url"]=url
  stats["is_swiss_football_club_set"]=len(match_names)>=9 and len(teams)>=10 and len(teams)<=15
  stats["is_season_usable"]=stats["is_swiss_football_club_set"] and len(out)>=170 and len(out)<=260
  return out,stats
def run():
  results={}
  for shortcut in SHORTCUTS:
    try:
      rows,diag=source(shortcut)
      results[shortcut]={"rows":rows,"diagnostics":diag}
    except Exception as ex:
      results[shortcut]={"rows":[],"diagnostics":{"status":"SOURCE_UNAVAILABLE_OR_BAD_FORMAT","error_class":type(ex).__name__,
             "reason":str(ex)[:150] if isinstance(ex,ValueError) else "network access blocked","is_season_usable":False}}
  good=[k for k in SHORTCUTS if results[k]["diagnostics"].get("is_season_usable")]
  if not good:
    return {"status":"NO_VALID_SWISS_FOOTBALL_SOURCE_DO_NOT_ARCHIVE",
      "examined_shortcuts":list(SHORTCUTS),
      "source_diagnostics":{k:results[k]["diagnostics"] for k in SHORTCUTS},
      "new_training_rows_approved":0}
  best=sorted(good,key=lambda s:(-len(results[s]["rows"]),s))[0]
  chosen=results[best]["rows"]
  BASE.mkdir(parents=True,exist_ok=True)
  csvp=BASE/"che1_2025_26_football_scores_ODbL_research_quarantine.csv"
  with csvp.open("w",encoding="utf-8",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=SCORE_COLS,lineterminator="\n")
    writer.writeheader();writer.writerows(chosen)
  lic=BASE/"LICENSE_ATTRIBUTION.md"
  lic.write_text("# Swiss Super League 2025/26 source-specific ODbL archive\n\n"
    "Data from OpenLigaDB (www.openligadb.de), licensed under ODbL 1.0. "
    "This extracted historical-results database is shared under ODbL 1.0 "
    "with attribution and share-alike.\n\n"
    "License: https://opendatacommons.org/licenses/odbl/1-0/\n"
    "Source terms: https://www.openligadb.de/en/license\n"
    "API terms: https://www.openligadb.de/en/terms-of-use\n\n"
    "Only scores from the selected Swiss football league season are retained; "
    "no provider logos, third-party images, pre-match availability claims, "
    "or training approval. The two source-shortcuts MUST NOT be double counted.\n",
    encoding="utf-8")
  report={"status":"SWISS_2025_26_ORIGINAL_ODBL_RESEARCH_ARCHIVE_CREATED",
    "selected_source_shortcut":best,
    "selected_finished_source_rows":len(chosen),
    "source_diagnostics":{k:results[k]["diagnostics"] for k in SHORTCUTS},
    "source_year":"2025-26","odbl_compilation_attribution":"Data from OpenLigaDB (www.openligadb.de), licensed under ODbL 1.0",
    "source_license":"https://www.openligadb.de/en/license",
    "csv_path":str(csvp),
    "source_2025_26_previous_independent_228_FT_verification_not_retested":True,
    "training_rows_approved":0,
    "independent_per_match_score_QA_pending":True,
    "historical_pre_kickoff_asof_timestamps_not_proven":True,
    "original_2396_and_296_holds_unchanged":True,
    "ger2_306_new_ODbL_archive_unchanged":True,
    "production_main_M4_unchanged":True,
    "source_shortcut_bsl_vs_ch1_only_selected_one":True}
  (BASE/"che1_2025_26_ODbL_source_selection_and_archive_report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
  return report
def test():
  m={"matchID":1,"matchIsFinished":True,
    "matchResults":[{"resultTypeID":1,"pointsTeam1":1,"pointsTeam2":0},
                    {"resultTypeID":2,"pointsTeam1":0,"pointsTeam2":0}]}
  assert score(m)==(0,0)
  assert score(dict(m,matchIsFinished=False)) is None
  assert normalize("FC Zürich")=="fc zurich"
  print("PASS Swiss club normalization and 0-0 FT vs half-time distinct")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--live",action="store_true");opt=p.parse_args()
 if opt.self_test:test()
 if opt.live:
   try:r=run()
   except Exception as e:r={"status":"FAIL_CLOSED_NO_SWISS_ARCHIVE","error_class":type(e).__name__,
                            "reason":str(e)[:180] if isinstance(e,ValueError) else "access or source failure",
                            "new_training_rows_approved":0}
   print("SWISS_25_ARCHIVE_START")
   print(json.dumps(r,ensure_ascii=False,indent=2))
   print("SWISS_25_ARCHIVE_END")
