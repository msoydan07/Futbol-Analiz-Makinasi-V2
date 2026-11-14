#!/usr/bin/env python3
"""Five 2026/27 leagues' results: personal-only ephemeral research processing.

Provider LIVE API terms: https://www.football-charts.com/terms
Personal research/analysis is permitted with attribution; bulk redistribution,
public raw extracts and sublicensing are NOT. Do not commit/save raw API scores,
private credentials, score-bearing logs or one-row-per-fixture extracts.

- Current-season five-league player-season research only.
- Read one league endpoint per invocation, NEVER automatically all five.
- Explicit keyless 25-requests/day provider constraints; no auto polling.
- In RAM: validate full-time, quarantine conflicting duplicate identities.
- In RAM: assess how many historical finished targets have BOTH teams with
  prior match HISTORY at least 2 calendar days older. Not a certified
  point-in-time feature availability guarantee.
- Stdout: ONLY aggregates. No row-level scores, names, dates or results.
- No training, predictions, xG generation or M4 production changes.
This module does NOT grant permission to republish the downloaded results.
"""
import argparse,json,re
from collections import Counter,defaultdict
from datetime import date,timedelta
from urllib.request import Request,urlopen
from pathlib import Path

API="https://footballcharts-backend.onrender.com/api/v1"
CUT=date(2026,11,13)
START=date(2026,7,1)
ALLOWED={"ENG5":"national","ESP2":"spain2","ITA2":"italy2",
         "FRA2":"france2","DNK1":"denmark1"}
LICENSE="https://www.football-charts.com/terms"
def get(lg):
 if lg not in ALLOWED:raise ValueError("UNSUPPORTED_TARGET_LEAGUE")
 url=f"{API}/leagues/{ALLOWED[lg]}/results/?season=2026-2027"
 request=Request(url,headers={
   "Accept":"application/json",
   "User-Agent":"FutbolAnalizMakinasiPrivateResearch/0.2 (not redistribution)"})
 with urlopen(request,timeout=30) as response:
  raw=response.read(3_500_001)
 if len(raw)>3_500_000:raise ValueError("SOURCE_TOO_LARGE")
 content=json.loads(raw)
 if isinstance(content,list):return content
 if isinstance(content,dict):
  for k in ("results","matches","data"):
   if isinstance(content.get(k),list):return content[k]
 raise ValueError("SOURCE_SCHEMA_UNEXPECTED")
def clean(name):
 if not isinstance(name,str):return ""
 import unicodedata
 v="".join(ch for ch in unicodedata.normalize("NFKD",name.casefold()) if not unicodedata.combining(ch))
 return re.sub(r"[^a-z0-9]+"," ",v).strip()
def fixture(item):
 """Keep only original source result facts, never use post-match goal minute as pre-match feature."""
 if not isinstance(item,dict):return None
 home=item.get("homeTeam");away=item.get("awayTeam")
 raw_score=item.get("score")
 raw_date=item.get("date")
 if not isinstance(raw_date,str) or not isinstance(raw_score,str):return None
 try:day=date.fromisoformat(raw_date[:10])
 except ValueError:return None
 h=clean(home);a=clean(away)
 if not h or not a or h==a:return None
 m=re.fullmatch(r"\s*(\d{1,2})\s*[-:–]\s*(\d{1,2})\s*",raw_score)
 if not m:return None
 goals=(int(m.group(1)),int(m.group(2)))
 if any(n>30 for n in goals):return None
 return day,h,a,goals
def summarize(league,records):
 if league not in ALLOWED:raise ValueError("UNKNOWN_LEAGUE")
 by_key={};conflicted=set();flags=Counter()
 for record in records:
  f=fixture(record)
  if f is None:flags["malformed_or_missing_FT"]+=1;continue
  day,h,a,score=f
  if not START<=day<=CUT:
   flags["outside_exact_historical_cutoff"]+=1;continue
  k=(day,h,a)
  if k in conflicted:
   flags["repeated_after_conflicting_identity"]+=1;continue
  if k in by_key:
   if by_key[k]!=score:
    flags["conflicting_score_same_identity_HOLD"]+=1
    del by_key[k];conflicted.add(k)
   else:flags["exact_duplicate_skip"]+=1
   continue
  by_key[k]=score
 valid=sorted(by_key,key=lambda x:(x[0],x[1],x[2]))
 # Each 'as-of form' uses only scores dated >= two days before this
 # completed match's DATE, never same-day or the match's own result.
 by_team=defaultdict(list)
 for day,h,a in valid:
  by_team[h].append(day);by_team[a].append(day)
 for team in by_team:by_team[team].sort()
 count=Counter()
 for day,h,a in valid:
  cutoff=day-timedelta(days=2)
  p=sum(z<=cutoff for z in by_team[h])
  q=sum(z<=cutoff for z in by_team[a])
  count["candidate_past_scorable_fixture_keys"]+=1
  for need in (1,3,5,8):
   if p>=need and q>=need:count[f"both_clubs_prior_at_least_{need}"]+=1
  if p==0 or q==0:count["at_least_one_club_no_older_history"]+=1
  if p+q<6:count["low_history_both_combined_under_6"]+=1
 return {
  "status":"EPHEMERAL_DERIVED_COHORT_METADATA_ONLY_NOT_TRAINING",
  "league":league,"season":"2026-27",
  "provider":"Football Charts", "provider_licence":LICENSE,
  "provider_attribution":"Data by football-charts.com",
  "scanned_input_source_records":len(records),
  "quality_flags":dict(flags),
  "distinct_clubs_with_historical_results":len(by_team),
  "targeted_history_timing":dict(count),
  "history_strict_lag_days":2,
  "source_historic_pre_kickoff_publication_proof":False,
  "raw_football_results_exported":0,
  "model_training_rows_approved":0,
  "old_research_database_modification":False,
  "note":"Strict prior match-DATE-only history, NOT proof each source result was publicly available by actual pre-kickoff time."
 }
def selftest():
 # Synthetic match scores, no actual provider data.
 entries=[
  {"date":"2026-08-01","homeTeam":"A","awayTeam":"B","score":"2-1"},
  {"date":"2026-08-01","homeTeam":"A","awayTeam":"B","score":"2-1"}, # exact duplicate
  {"date":"2026-08-03","homeTeam":"B","awayTeam":"A","score":"1-0"},
  {"date":"2026-08-03","homeTeam":"B","awayTeam":"A","score":"0-1"}, # conflicting identity -> both held
  {"date":"2026-08-04","homeTeam":"A","awayTeam":"C","score":"1-1"},
  {"date":"2026-11-15","homeTeam":"A","awayTeam":"B","score":"0-2"}, # future excluded
  {"date":"2026-08-04","homeTeam":"C","awayTeam":"B","score":""},
 ]
 x=summarize("ENG5",entries)
 assert x["targeted_history_timing"]["candidate_past_scorable_fixture_keys"]==2
 assert x["quality_flags"]["exact_duplicate_skip"]==1
 assert x["quality_flags"]["conflicting_score_same_identity_HOLD"]==1
 assert x["quality_flags"]["outside_exact_historical_cutoff"]==1
 assert x["model_training_rows_approved"]==0
 assert x["raw_football_results_exported"]==0
 print("PASS synthetic duplicate, conflicting score HOLD, future exclusion, 2-day history lag and zero raw exports")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--one-league",choices=sorted(ALLOWED))
 a=p.parse_args()
 if a.self_test:selftest()
 if a.one_league:
  result=summarize(a.one_league,get(a.one_league))
  print(json.dumps(result,ensure_ascii=False,indent=2))
