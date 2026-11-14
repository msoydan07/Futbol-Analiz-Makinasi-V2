#!/usr/bin/env python3
"""ONE further, distinct source-only historical archival scope:
9 unclosed 2025/26 *other* leagues from the same SHA-pinned publisher CC-BY
source. Does NOT repeat Denmark/Swiss source checks or old FT QA.
Records licensed source candidates, but does NOT add to deduped 3122 until
canonical matching against existing 2396 and previously licensed ODbL
is separately completed. No new fixtures, no 2024/25, no M4 changes.
"""
import argparse,csv,hashlib,io,json,re
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path("experiments/263/league_expansion")
OUT=ROOT/"ccby_footballcharts_9_other_2025_26_source_ledger"
SRC="https://huggingface.co/datasets/Damir81/football-charts-results-goal-timing/resolve/main/football_charts_matches.csv"
EXPECTED_SHA="08d1a0863d703550fe6e7fb1ef9faed4ea3cea95c664012373b1a1e1f159be10"
DOI="https://doi.org/10.5281/zenodo.22295583"
CCBY="https://creativecommons.org/licenses/by/4.0/"
# Strict country + name prevents National League South/North, Austrian 2. Liga
# and Italian Serie C from accidentally being treated as in-scope teams.
TARGETS={
 "ENG3":("england",("league one","league 1")),
 "ENG4":("england",("league two","league 2")),
 "ENG5":("england",("national league",)),
 "ESP2":("spain",("laliga2","laliga 2","segunda division","segunda división")),
 "ITA2":("italy",("serie b",)),
 "FRA2":("france",("ligue 2",)),
 "GRE1":("greece",("super league",)),
 "SCO1":("scotland",("premiership",)),
 "AUT1":("austria",("bundesliga",)),
}
BOUNDS={
 "ENG3":(400,650),"ENG4":(400,650),"ENG5":(400,650),
 "ESP2":(300,500),"ITA2":(300,450),"FRA2":(250,370),
 "GRE1":(160,330),"SCO1":(190,270),"AUT1":(170,270)}
HEADER=["league","season","date","source_home","source_away",
 "source_ft_home","source_ft_away","source_ht_result",
 "source_kickoff_utc","source_league_code","source_competition_name",
 "source_license","source_doi","gate","stage_gate","asof_gate"]
def norm(s):
 import unicodedata
 s=str(s).casefold().replace("ß","ss").replace("ø","o").replace("æ","ae")
 s="".join(c for c in unicodedata.normalize("NFKD",s) if not unicodedata.combining(c))
 return re.sub(r"[^a-z0-9]+"," ",s).strip()
def fetch():
 req=Request(SRC,headers={"User-Agent":"FutbolAnalizMakinesi-One-New-9League-Scope/1.0 (+https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2)","Accept":"text/csv"})
 with urlopen(req,timeout=65) as res:
  raw=res.read(16_000_001)
 if len(raw)>16_000_000:raise ValueError("SOURCE_OVER_SIZE")
 if hashlib.sha256(raw).hexdigest()!=EXPECTED_SHA:
  raise ValueError("PINNED_CC_BY_SOURCE_SHA_CHANGED__DO_NOT_ASSUME_SAME_SOURCE")
 return raw
def which(r):
 c=norm(r.get("country"))
 n=norm(r.get("league_name"))
 for lg,(country,aliases) in TARGETS.items():
  if c==country and n in {norm(z) for z in aliases}:return lg
 return None
def scan(raw):
 rows=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
 needed={"country","league_name","league","season","match_date","home_team","away_team",
         "home_goals","away_goals","ft_result"}
 if not needed.issubset(rows.fieldnames or []):raise ValueError("SOURCE_COLUMNS_CHANGED")
 source_total=0;cols={lg:[] for lg in TARGETS};counter=defaultdict(Counter)
 for r in rows:
  source_total+=1
  if r.get("season")!="2025-2026":continue
  league=which(r)
  if league is None:continue
  counter[league]["source_selected"]+=1
  ds=r.get("match_date","")[:10]
  try:d=date.fromisoformat(ds)
  except ValueError:
   counter[league]["invalid_date"]+=1;continue
  if not date(2025,7,1)<=d<=date(2026,6,30):
   counter[league]["out_of_season"]+=1;continue
  h=(r.get("home_team") or "").strip();a=(r.get("away_team") or "").strip()
  hg=str(r.get("home_goals") or "").strip();ag=str(r.get("away_goals") or "").strip()
  if not h or not a or h==a or not hg.isdigit() or not ag.isdigit() or int(hg)>20 or int(ag)>20:
   counter[league]["invalid_team_or_goals"]+=1;continue
  ft=(r.get("ft_result") or "").strip().replace(" ","").replace(":","-")
  if ft and ft!=hg+"-"+ag:
   counter[league]["source_total_vs_ft_shape_mismatch"]+=1;continue
  cols[league].append({
    "league":league,"season":"2025-26","date":ds,"source_home":h,
    "source_away":a,"source_ft_home":hg,"source_ft_away":ag,
    "source_ht_result":r.get("ht_result") or "",
    "source_kickoff_utc":r.get("kickoff_utc") or "",
    "source_league_code":r.get("league") or "",
    "source_competition_name":r.get("league_name") or "",
    "source_license":"CC-BY-4.0","source_doi":DOI,
    "gate":"ORIGINAL_CCBY_SOURCE_ARCHIVED__NOT_CANONICAL_DEDUP_TRAINING",
    "stage_gate":"PLAYOFF_OR_STAGE_NOT_YET_ADJUDICATED",
    "asof_gate":"HISTORIC_PRE_MATCH_AVAILABILITY_NOT_PROVEN"})
 if source_total!=76991:raise ValueError("SOURCE_PUBLISHER_ROW_COUNT_CHANGED")
 details={}
 for lg,group in cols.items():
  seen=set();clubs=set()
  for r in group:
   k=(r["date"],norm(r["source_home"]),norm(r["source_away"]))
   if k in seen:raise ValueError("DUPLICATE_SOURCE_RESULT_"+lg)
   seen.add(k)
   clubs.update((r["source_home"],r["source_away"]))
  keys={r["source_league_code"] for r in group}
  lower,upper=BOUNDS[lg]
  details[lg]={
   "available_source_scored_rows":len(group),
   "source_league_codes":sorted(keys),
   "clubs_in_source":len(clubs),
   "earliest":min((r["date"] for r in group),default=None),
   "latest":max((r["date"] for r in group),default=None),
   "shape_errors":dict(counter[lg]),
   "expected_scope_bounds":[lower,upper],
   "scope_plausible":lower<=len(group)<=upper and len(keys)==1 and len(clubs)>=10}
  group.sort(key=lambda x:(x["date"],x["source_home"],x["source_away"]))
 return cols,details,source_total
def run():
 raw=fetch()
 groups,details,total=scan(raw)
 passes=[code for code,v in details.items() if v["scope_plausible"]]
 failures=[code for code in TARGETS if code not in passes]
 OUT.mkdir(parents=True,exist_ok=True)
 for lg in passes:
  with (OUT/(lg.lower()+"_2025_26_CC_BY_SOURCE_QUARANTINE.csv")).open("w",newline="",encoding="utf-8") as f:
   w=csv.DictWriter(f,fieldnames=HEADER,lineterminator="\n")
   w.writeheader();w.writerows(groups[lg])
 (OUT/"ATTRIBUTION_LICENSE.md").write_text(
  "# One source snapshot, nine additional historical league scopes\n\n"
  "Author: Damir Devetak / Football Charts, Match Results and Goal Timing, version 2026.10\n"
  "DOI: "+DOI+"\nSource: "+SRC+"\n"
  "License: CC BY 4.0 "+CCBY+"\n"
  "Required attribution: Data by football-charts.com / Damir Devetak.\n\n"
  "Changes: Filtered only eligible 2025-26 result rows for nine league categories; "
  "kept source team spelling (no invented aliases), preserved full-time scores "
  "and UTC kickoff when given. Original full publisher 76,991-row CSV is NOT rehosted.\n\n"
  "Do not add these source rows directly to the 3,122 unique research fixtures: "
  "overlaps with old 2,396 and other source sources require canonical de-dup. "
  "Play-off stage, historical point-in-time availability and any third-party "
  "upstream-right claims remain research gates. No model training approved.\n",
  encoding="utf-8")
 report={
  "status":"HISTORICAL_CCBY_SOURCE_9_SCOPE_ONE_PASS_COMPLETED_RESEARCH_ONLY",
  "fetched_at_utc":datetime.now(timezone.utc).isoformat(),
  "source_original":SRC,"source_original_sha256":EXPECTED_SHA,
  "source_rows_scanned_once":total,
  "only_2025_26_season_filtered":True,"excluded_old_2024_25_or_2026_27":True,
  "requested_nine_other_leagues":list(TARGETS),
  "league_source_evidence":details,
  "plausible_source_archives_created":passes,
  "groups_not_archived_due_to_scope_quality_bounds":failures,
  "source_row_sum_for_archived_groups":sum(len(groups[x]) for x in passes),
  "cross_source_duplicate_or_extra_playoff_outcome_resolved":False,
  "new_unique_research_fixture_count_until_CANDIDATE_DEDUP":0,
  "previous_committed_research_unique_fixture_count_unchanged":3122,
  "previous_Danish192_and_Swiss67_CC_BY_source_pass_not_rechecked":True,
  "previous_GER2_306_and_SWISS_161_ODbL_QA_not_rechecked":True,
  "source_licence":"CC-BY-4.0",
  "author_credit":"Data by football-charts.com / Damir Devetak",
  "license_url":CCBY,
  "no_model_training_approved":True,
  "new_training_rows_approved":0,
  "production_10league_M4_SHA_unchanged":True,
  "user_manual_1855_xG_unchanged":True,
  "archive_rights_and_provenance":"Publisher grants CC BY 4.0 for original open file; upstream database rights, club matching and historical as-of are separate verification requirements",
  "next_distinct_action":"Offline canonical identity and same-date/FT reconciliation for ONLY these new league-source rows vs existing research baseline; do NOT re-fetch pinned 76,991-source snapshot or rerun the Danish/Swiss gates. Then resolve play-off stage before counting new distinct fixtures."
 }
 (OUT/"9_other_2025_26_source_scope_report_20261114.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return report
def test():
 assert len(TARGETS)==9 and "ENG5" in TARGETS
 assert which({"country":"England","league_name":"National League"})=="ENG5"
 assert which({"country":"England","league_name":"National League North"}) is None
 assert which({"country":"Austria","league_name":"2. Liga"}) is None
 print("PASS new 9 source scopes only; excluded other divisions and 2026/27")
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("--self-test",action="store_true");ap.add_argument("--live",action="store_true");ns=ap.parse_args()
 if ns.self_test:test()
 if ns.live:
  try:res=run()
  except Exception as exc:
   OUT.mkdir(parents=True,exist_ok=True)
   res={"status":"FAIL_CLOSED_NINE_SCOPE_NOT_ARCHIVED",
       "error_class":type(exc).__name__,
       "reason":str(exc)[:250] if isinstance(exc,ValueError) else "source request or parser unavailable",
       "new_unique_research_fixture_count_until_CANDIDATE_DEDUP":0,
       "new_training_rows_approved":0}
   (OUT/"9_other_2025_26_source_scope_report_20261114.json").write_text(json.dumps(res,indent=2)+"\n")
  print("OTHER_NINE_SOURCE_START")
  print(json.dumps(res,indent=2,ensure_ascii=False))
  print("OTHER_NINE_SOURCE_END")
