#!/usr/bin/env python3
"""NEW-only 1,269 source-licensed 2025/26 *scored results* second-witness check.

Input exactly the new 1,269 fixture keys from seven pinned source-specific
CC BY original research CSVs, all separate from main 10-league M4. Read one
light CSV per 2025/26 league for match fact comparison, never rehost raw
secondary sources or older score rows. No rerun of old 1,775/461 match FT QA.
No modelling, no original 2,396 source modifications, zero training approvals.

This is a TWO-PROVIDER fact witness only; underlying data lineage, exact
historic as-of availability and training rights are separate questions.
"""
from __future__ import annotations
import csv,hashlib,io,json,re,argparse
from collections import Counter,defaultdict
from datetime import datetime,date,timezone
from pathlib import Path
from urllib.request import Request,urlopen
import audit_6_leagues_967_scores_one_batch_20261114 as prev
from reconcile_six_leagues_228_exceptions_no_repeat_20261114 import ALIAS_DELTA
from reconcile_3041_CC_BY_eight_history_vs_old_once import CUSTOM as CC_BY_NAMES
from verify_4391_research_source_integrity_once import FILES
ROOT=Path("experiments/263/league_expansion")
STAGE=ROOT/"ccby_footballcharts_2025_26_regular_stage_novel_only"
REPORT=STAGE/"new1269_target_only_second_provider_FT_evidence_20261114.json"
SECONDARY={
 "ENG3":"E2","ENG4":"E3","ENG5":"EC",
 "ITA2":"I2","FRA2":"F2","GRE1":"G1","SCO1":"SC0"
}
EXPECTED={"ENG3":208,"ENG4":277,"ENG5":262,"ITA2":72,"FRA2":190,"GRE1":120,"SCO1":140}
# Reuse the exact previously audited club alias tables. Supplement with
# explicit known football-data provider abbreviations, NEVER fuzzy match.
EXPLICIT={
 "ENG3":{"peterboro":"Peterborough United","plymouth":"Plymouth Argyle","port vale":"Port Vale FC"},
 "ENG4":{"bristol rvs":"Bristol Rovers","crewe":"Crewe Alexandra","mk dons":"Milton Keynes Dons","notts co":"Notts County","cambridge utd":"Cambridge United"},
 "ENG5":{"boston utd":"Boston United","halifax":"Halifax Town","fc halifax":"Halifax Town",
         "forest green":"Forest Green Rovers","southend":"Southend United","rochdale":"Rochdale AFC"},
 "ITA2":CC_BY_NAMES["ITA2"],
 "FRA2":CC_BY_NAMES["FRA2"],
 "GRE1":CC_BY_NAMES["GRE1"] | {"levadeiakos":"Levadiakos"},
 "SCO1":{"hearts":"Heart of Midlothian","st mirren":"St. Mirren FC","dundee":"Dundee FC","dundee utd":"Dundee United"}
}
def local_source(lg):
 p=STAGE/(lg.lower()+"_2025_26_NEW_REGULAR_SOURCE_ONLY_QA_PENDING.csv")
 target="ccby_footballcharts_2025_26_regular_stage_novel_only/"+p.name
 expected_blob,n=FILES[target]
 data=p.read_bytes()
 blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
 if blob!=expected_blob or n!=EXPECTED[lg]:raise ValueError("SOURCE_PIN_COUNT_INVALID_"+lg)
 rows=list(csv.DictReader(data.decode("utf-8-sig").splitlines()))
 if len(rows)!=n:raise ValueError("NEW_1269_TARGET_COUNT_CHANGED_"+lg)
 if {x["league"] for x in rows}!={lg} or {x["season"] for x in rows}!={"2025-26"}:
  raise ValueError("TARGET_NOT_2025_26_REGULAR")
 if {x["research_status"] for x in rows}==set():raise ValueError("NO_NEW_ROWS")
 return rows,blob

def norm_map(lg,rows):
 clubs={x for r in rows for x in (r["home"],r["away"])}
 # Some newly archived late-season teams never appear in original autumn
 # reference; use this new current-season local team roster only.
 d=prev.exact_name_maps(lg,clubs)
 for alias,target in (prev.CUSTOM.get(lg,{}) | ALIAS_DELTA.get(lg+"/2025-26",{}) | EXPLICIT.get(lg,{})).items():
  if target not in clubs:continue
  k=prev.norm(alias)
  if k in d and d[k]!=target:raise ValueError("WRONG_TEAM_ALIAS_COLLISION_"+lg+"_"+alias)
  d[k]=target
 return d
def get(url):
 req=Request(url,headers={
  "User-Agent":"Mozilla/5.0 (one-time personally requested research match-score-witness, no redistribution)",
  "Accept":"text/csv,application/csv;q=0.8"})
 with urlopen(req,timeout=30) as resp:content=resp.read(1_800_001)
 if len(content)>1_800_000 or b"<html" in content[:150].lower():raise ValueError("SECONDARY_RESPONSE_NOT_CSV_OR_TOO_LARGE")
 return content
def compare(lg,raw,reference):
 reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig",errors="replace"),newline=""))
 if not {"Div","Date","HomeTeam","AwayTeam","FTHG","FTAG"}.issubset(reader.fieldnames or []):
  raise ValueError("SECONDARY_CSV_SCHEMA_NOT_MATCHING")
 clubs=norm_map(lg,reference)
 source={};unknown=Counter();stats=Counter()
 for r in reader:
  if r.get("Div")!=SECONDARY[lg]:continue
  d=prev.day_of(r.get("Date"))
  if d is None or not date(2025,7,1)<=d<=date(2026,6,30):continue
  ft=prev.score(r.get("FTHG"),r.get("FTAG"))
  if ft is None:continue
  h=prev.match_name(r.get("HomeTeam"),clubs)
  a=prev.match_name(r.get("AwayTeam"),clubs)
  if not h or not a or h==a:
   for rawname,target in ((r.get("HomeTeam"),h),(r.get("AwayTeam"),a)):
    if not target:unknown[str(rawname)]+=1
   continue
  key=(d.isoformat(),h,a)
  if key in source and source[key]!=ft:
   raise ValueError("SECONDARY_SCORE_CONFLICT_WITH_ITSELF")
  source[key]=ft;stats["mapped_secondary_scored_fixtures"]+=1
 targets=Counter();examples=[];near=defaultdict(list)
 for (dt,h,a),ft in source.items():
  near[(h,a)].append(dt)
 for row in reference:
  key=(row["date"],row["home"],row["away"])
  got=source.get(key)
  first=(int(row["ft_home"]),int(row["ft_away"]))
  if got is None:
   dd=date.fromisoformat(row["date"])
   nearby=any(abs((dd-date.fromisoformat(other)).days)<=2 for other in near[(row["home"],row["away"])])
   verdict="SAME_PAIR_DIFFERENT_DATE_NEAR_2_DAYS_HOLD" if nearby else "SECONDARY_NO_EXACT_TARGET_KEY_HOLD"
  elif got==first:
   verdict="SECONDARY_SAME_DATE_CLUBS_FT_CONFIRMED"
  else:
   verdict="SECONDARY_SAME_DATE_CLUBS_FT_CONFLICT_HOLD"
  targets[verdict]+=1
  if verdict!="SECONDARY_SAME_DATE_CLUBS_FT_CONFIRMED" and len(examples)<18:
   examples.append({"source_fixture":[*key],
       "source_CCBY_ft":"-".join(map(str,first)),
       "targeted_verdict":verdict})
 if sum(targets.values())!=len(reference):raise ValueError("SOURCE_TARGET_VERDICTS_DRIFT")
 return {"new_targeted_keys":len(reference),
  "fixture_classification":dict(targets),
  "score_verified":targets["SECONDARY_SAME_DATE_CLUBS_FT_CONFIRMED"],
  "not_exactly_corrobated":len(reference)-targets["SECONDARY_SAME_DATE_CLUBS_FT_CONFIRMED"],
  "secondary_only_stat_counts":dict(stats),
  "unmapped_provider_team_names_top10":unknown.most_common(10),
  "only_unconfirmed_original_CC_BY_source_sample":examples}
def run():
 grouped={};total=Counter()
 for lg,code in SECONDARY.items():
  src,blob=local_source(lg)
  url=f"https://www.football-data.co.uk/mmz4281/2526/{code}.csv"
  try:
   raw=get(url)
   item=compare(lg,raw,src)
   item.update({"status":"SECOND_SOURCE_FETCH_AND_NEW_ONLY_COMPARE_COMPLETED",
      "source_CCBY_git_blob_sha":blob,"secondary_source_url":url,
      "secondary_source_SHA256":hashlib.sha256(raw).hexdigest(),
      "secondary_rehosted":False,
      "old_prevalidated_fixture_keys_checked_again":0})
  except Exception as ex:
   item={"status":"SECOND_PROVIDER_NOT_AVAILABLE_FAIL_CLOSED",
      "targeted_count":len(src),"second_source_verified":0,
      "error_class":type(ex).__name__,
      "error_message":str(ex)[:180] if isinstance(ex,ValueError) else "secondary provider network blocked",
      "source_CCBY_git_blob_sha":blob,"old_prevalidated_fixture_keys_checked_again":0}
  grouped[lg]=item
  total["targets"]+=len(src)
  total["verified"]+=item.get("score_verified",0)
  total["blocked"]+=len(src)-item.get("score_verified",0)
 if total["targets"]!=1269 or total["verified"]+total["blocked"]!=1269:
  raise ValueError("FINAL_TARGETED_1269_COUNTS_DRIFT")
 return {
  "status":"ONE_PASS_ONLY_NEW_1269_RESULTS_7_SECOND_PROVIDER_FACT_WITNESSES_DONE__OR_FAIL_CLOSED_BY_GROUP",
  "when_utc":datetime.now(timezone.utc).isoformat(),
  "scope":"Only 1269 novel historical 2025/26 regular-season result keys, NOT previous 1775+461 or original 296 hold records",
  "new_1269_targeted":total["targets"],
  "two_provider_FT_exact_date_home_away":total["verified"],
  "FT_unmatched_or_conflicting_or_source_unavailable":total["blocked"],
  "source_by_league":grouped,
  "old_GitHub_source_2396_blobs_rewritten":False,
  "second_source_full_score_CSVs_redistributed":False,
  "previous_sources_FT_QA_871_904_306_161_192_redone":False,
  "new_training_approved":0,"new_model_training_or_predictions":0,
  "source_rights_original_and_historical_publication_time_gates_pending":True,
  "next_distinct_task":"Only unresolved new result source keys, never redo exact matches. After result witness, pursue licensed 2026/27 gaps and evidence-of-availability for historical pre-match features."
 }
def selftest():
 assert sum(EXPECTED.values())==1269
 for lg in SECONDARY:
  rows,_=local_source(lg)
  norm_map(lg,rows)
 print("PASS 1269 new source-pinned fixtures, local club alias maps, old score audits not invoked")
if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--self-test",action="store_true");ap.add_argument("--run",action="store_true");x=ap.parse_args()
 if x.self_test:selftest()
 if x.run:
  try:d=run()
  except Exception as ex:
   d={"status":"FAIL_CLOSED_ALL_NEW_SCORE_WITNESSES","error_type":type(ex).__name__,
      "reason":str(ex)[:220],"new_training_approved":0}
  print("1269_SCORE_START")
  print(json.dumps(d,indent=2,ensure_ascii=False))
  print("1269_SCORE_END")
