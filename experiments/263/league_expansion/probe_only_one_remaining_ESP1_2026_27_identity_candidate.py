#!/usr/bin/env python3
"""One leftover Spain LaLiga 2026/27 identity candidate only.

Previous current cutoff counts: 120 source vs 119 base. Official 6-8 Nov
10/10 complete already; therefore inspect earlier match score/date DIFF only.
This is NOT a rerun of FT source QA for old 119, no raw feed archive.
Select a single case only when date & score identify exactly one source match.
Requires subsequent independent official league witness before adding score.
"""
from pathlib import Path
from urllib.request import Request,urlopen
import json,csv,hashlib,re
from collections import Counter
ROOT=Path("experiments/263/league_expansion")
D=ROOT/"esp1_2026_27_official_2026_nov8_gap_only"
OUT=D/"one_rest_ESP1_2026_27_source_only_candidate_before_nov6_20261114.json"
CURRENT=ROOT/"2026_27_17_persisted_leagues_one_freshness_aggregates_only_20261114.json"
URL="https://footballcharts-backend.onrender.com/api/v1/leagues/spain1/results/?season=2026-2027"
BASE=Path("data/results_only_263/2026-11-10_completed_4617_scores_only.csv")
PROV=Path("data/results_only_263/4617_research_input_provenance.json")
def run():
 x=json.loads(CURRENT.read_text())["counts"]["ESP1"]
 if x["persisted_research_or_core"]!=119 or x["source_distinct_finished_count"]!=120:raise ValueError("OLD SOURCE DIFF CHANGED")
 if hashlib.sha256(BASE.read_bytes()).hexdigest()!=json.loads(PROV.read_text())["source_snapshot_sha256"]:
  raise ValueError("BASE_SOURCE_CHANGED")
 rows=[r for r in csv.DictReader(BASE.open(encoding="utf-8-sig",newline="")) if r["league"]=="ESP1" and r["season"]=="2026-2027"]
 if len(rows)!=119:raise ValueError("CORE_ESP1_NOT_119")
 old=Counter((r["match_date"],int(r["home_goals"]),int(r["away_goals"])) for r in rows)
 req=Request(URL,headers={"Accept":"application/json","User-Agent":"OnePrivateLaLigaResultCandidateOutsideNov8/1.0"})
 with urlopen(req,timeout=28) as f:blob=f.read(4000001)
 if len(blob)>4000000:raise ValueError("SOURCE_RESPONSE_TOO_LARGE")
 j=json.loads(blob)
 if isinstance(j,list):raw=j
 elif isinstance(j,dict):
  raw=None
  for field in ("results","matches","data","items"):
   v=j.get(field)
   if isinstance(v,list):raw=v;break
   if isinstance(v,dict):
    for inner in ("results","matches","data","items"):
     if isinstance(v.get(inner),list):raw=v[inner];break
    if raw is not None:break
 else:raw=None
 if not isinstance(raw,list):raise ValueError("LIVE_SCHEMA")
 source=Counter();examples={}
 for r in raw:
  if not isinstance(r,dict):continue
  dt=str(r.get("date") or "")[:10];sc=str(r.get("score") or "").strip().replace("–","-")
  match=re.fullmatch(r"(\d{1,2})\s*[-:]\s*(\d{1,2})",sc)
  if not match or not "2026-07-01"<=dt<="2026-11-13":continue
  pair=(dt,int(match.group(1)),int(match.group(2)))
  home=str(r.get("homeTeam") or "");away=str(r.get("awayTeam") or "")
  if not home or not away:continue
  source[pair]+=1
  examples.setdefault(pair,[]).append({"date":dt,"home":home,"away":away,"ft_home":pair[1],"ft_away":pair[2]})
 delta=source-old;extra=old-source
 safe=[]
 for key,n in delta.items():
  if n==1 and source[key]==1:
   safe.append(examples[key][0])
 # Do not infer identity when date+score ambiguous
 status="ONE_EXACT_DATE_FT_SOURCE_CANDIDATE_PENDING_OFFICIAL" if len(safe)==1 and sum(delta.values())==1 and not extra else "HOLD_CANNOT_DISTINGUISH_SOURCE_DATE_SCORE_CANDIDATE"
 out={
  "status":status,"old_core_119_not_rewritten":True,
  "provider_result_rows_counted":sum(source.values()),
  "old_119_source_same_date_score_counts_not_retested_with_other_provider":True,
  "source_new_date_score_multiset_extra_count":sum(delta.values()),
  "core_date_score_extra_count":sum(extra.values()),
  "candidate_only_not_model_label":safe if status.startswith("ONE_") else [],
  "candidate_deduction_caveat":"Unique date+score only; name witness still needed",
  "provider_source":URL,
  "publisher_terms":"https://www.football-charts.com/terms",
  "raw_provider_result_rows_archived":0,
  "model_training_approved":0
 }
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 return out
if __name__=="__main__":print(json.dumps(run(),ensure_ascii=False,indent=2))
