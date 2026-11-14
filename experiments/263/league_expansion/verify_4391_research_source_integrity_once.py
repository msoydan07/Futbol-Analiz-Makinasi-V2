#!/usr/bin/env python3
"""ONE offline 4,391 distinct research identity accounting gate; NOT training QA.

Assembles pointers into 2,396 original SHA-pinned research rows plus 1,995
separately licensed original-source research CSV results (GER2 306, CHE1 161,
Danish 192, Swiss novel67, seven 2025/26 regular-stage league groups 1,269).
Never alters original data, reruns 871/904 or 306/155+6 match QA, fetches
external score sources, or modifies existing 10-league M4.
"""
import csv,hashlib,json,re
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
from prepare_2396_provenance_rights_quality_gate_20261114 import EXPECTED,read_csv,match_key
from verify_public_season_csv_2526 import name_map,norm
from reconcile_3041_CC_BY_eight_history_vs_old_once import first
ROOT=Path("experiments/263/league_expansion")
REPORT=ROOT/"research_historical_4391_distinct_source_accounting_20261114.json"
FILES={
 "odbl_openligadb_germany2/ger2_2025_2026_207_novel_only_quarantine.csv":("5a2f228fb9faa50626417262e2a6a798c346e18d",207),
 "odbl_openligadb_germany2/ger2_2026_2027_ODbL_research_quarantine.csv":("83f612c849c81591c3ee952d68be4d9e46f067d6",99),
 "odbl_openligadb_swiss1/che1_2025_26_161_ODbL_official_corrected_RESEARCH_ONLY.csv":("b907493671386dd81dff7b272e922272be512808",161),
 "ccby_footballcharts_historic_2025_26/dnk1_2025_26_192_CC_BY_historic_original_research_only.csv":("7fb613889d223530ec0b45e3daca52ac971dc2db",192),
 "ccby_footballcharts_historic_2025_26/che1_2025_26_67_NOVEL_CC_BY_research_only.csv":("e950f59f949b24dcac049c9f4442349b555c5c13",67),
 "ccby_footballcharts_2025_26_regular_stage_novel_only/eng3_2025_26_NEW_REGULAR_SOURCE_ONLY_QA_PENDING.csv":("25936108b009fb0003f56d269289dcdff37b9281",208),
 "ccby_footballcharts_2025_26_regular_stage_novel_only/eng4_2025_26_NEW_REGULAR_SOURCE_ONLY_QA_PENDING.csv":("742d5ada75cd538ddcef8a47b5d371f1a9947f2a",277),
 "ccby_footballcharts_2025_26_regular_stage_novel_only/eng5_2025_26_NEW_REGULAR_SOURCE_ONLY_QA_PENDING.csv":("85e62700a900c847941ae3c665ebb38efe32022c",262),
 "ccby_footballcharts_2025_26_regular_stage_novel_only/ita2_2025_26_NEW_REGULAR_SOURCE_ONLY_QA_PENDING.csv":("fff8d8a9673d38141287ad32f0d5b474b0bd04d7",72),
 "ccby_footballcharts_2025_26_regular_stage_novel_only/fra2_2025_26_NEW_REGULAR_SOURCE_ONLY_QA_PENDING.csv":("b12ba6b7fc11367894b07470edfa93b5d9c3ec59",190),
 "ccby_footballcharts_2025_26_regular_stage_novel_only/gre1_2025_26_NEW_REGULAR_SOURCE_ONLY_QA_PENDING.csv":("10782d9b7a94a06fb113c09e3a327883d232880c",120),
 "ccby_footballcharts_2025_26_regular_stage_novel_only/sco1_2025_26_NEW_REGULAR_SOURCE_ONLY_QA_PENDING.csv":("e9d938ae62e8b05158bdba3f518d21f2e2670372",140)
}
def blob_sha(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def canon(x):
 league,season,d,h,a=match_key(x)
 if league=="CHE1":
  look=name_map("CHE1")
  hc=look.get(norm(h));ac=look.get(norm(a))
  if not hc or not ac:raise ValueError("SWISS_CANONICAL_TEAM_UNMAPPED: "+h+" "+a)
  return (league,season,d,hc,ac)
 if league=="GER2":
  return (league,season,d,
    "Arminia Bielefeld" if h=="DSC Arminia Bielefeld" else h,
    "Arminia Bielefeld" if a=="DSC Arminia Bielefeld" else a)
 return (league,season,d,h,a)
def archive():
 old_holds=first()[1]
 if len(old_holds)!=296:raise ValueError("EXACT_HOLD_296_DRIFT")
 rows=[];counts=Counter();by_block=[];distinct=set();errors=[]
 for filename,(sha,n,rights) in EXPECTED.items():
  original,got=read_csv(filename)
  if got!=sha or len(original)!=n:raise ValueError("ORIGINAL_2396_PIN_DRIFT_"+filename)
  for x in original:
   key=canon(x)
   if key in distinct:errors.append({"source":filename,"fixture":key})
   distinct.add(key);rows.append(x)
   counts["baseline"]+=1
  by_block.append({"source":filename,"rows":len(original),"source_git_blob_sha":got,"license_class":rights})
 if counts["baseline"]!=2396:raise ValueError("2396_BASELINE_INVALID")
 for filename,(expected,n) in FILES.items():
  file=ROOT/filename
  data=file.read_bytes();got=blob_sha(data)
  if got!=expected:raise ValueError("RESEARCH_ARCHIVE_NEW_BLOB_CHANGED_"+filename)
  parsed=list(csv.DictReader(data.decode("utf-8-sig").splitlines()))
  if len(parsed)!=n:raise ValueError("RESEARCH_ARCHIVE_NEW_COUNT_CHANGED_"+filename)
  for x in parsed:
   key=canon(x)
   if key in distinct:errors.append({"source":filename,"fixture":key})
   distinct.add(key);rows.append(x)
   counts["new"]+=1
   if "regular_stage_novel_only" in filename:counts["new_regular_stage_source_score_ONLY"]+=1
  by_block.append({"source":filename,"rows":len(parsed),"source_git_blob_sha":got,
   "license_class":"ODbL-1.0" if "/odbl_" in "/"+filename else "CC-BY-4.0"})
 if errors:raise ValueError("CROSS_SOURCE_DUPLICATE_CANONICAL_IDENTITY: "+str(errors[:5]))
 if counts["new"]!=1995 or counts["new_regular_stage_source_score_ONLY"]!=1269:
  raise ValueError("SOURCE_RECORD_COUNT_DRIFT: "+str(counts))
 if len(distinct)!=4391 or len(rows)!=4391:raise ValueError("UNIQUE_RESEARCH_COUNT_NOT_4391")
 source=Counter();season=Counter()
 for x in rows:
  lg,ss,d,h,a=canon(x)
  if ss not in ("2025-26","2026-27"):
   raise ValueError("SEASON_OUTSIDE_FROZEN_CONSENT")
  if not date(2025,7,1)<=date.fromisoformat(d)<=date(2026,11,13):
   raise ValueError("FUTURE_OR_OLD_RESULT")
  if h==a:raise ValueError("MATCH_WITH_SAME_CLUB")
  if not re.fullmatch(r"\d{1,2}",str(x["ft_home"])) or not re.fullmatch(r"\d{1,2}",str(x["ft_away"])):
   raise ValueError("BLANK_OR_BAD_MATCH_FT")
  source[lg]+=1;season[ss]+=1
 if any(k[0]=="ENG5" and k[2]=="2025-12-06" and k[3]=="Rochdale AFC" and k[4]=="Southend United" for k in distinct):
  raise ValueError("ABANDONED_ROCHDALE_DEC_CONFLATED_AS_COMPLETED")
 if any(k[0]=="ENG5" and k[2]=="2025-09-06" and k[3]=="Scunthorpe United" and k[4]=="Wealdstone FC" for k in distinct):
  raise ValueError("ADMINISTRATIVE_AWARDED_0_0_FT_POLLUTED_SCORED_POOL")
 original_stage=json.loads((ROOT/"ccby_footballcharts_2025_26_regular_stage_novel_only/novel_1376_stage_eligibility_and_research_archive_20261114.json").read_text())
 eng5=json.loads((ROOT/"ccby_footballcharts_2025_26_regular_stage_novel_only/eng5_2025_26_official_abandonment_262_new_regular_scores_gate_20261114.json").read_text())
 if original_stage["new_research_rows_only_from_schedule_complete_groups"]!=1007 or eng5["new_distinct_research_ENG5_fixture_identities"]!=262:
  raise ValueError("OLDER_SOURCE_STAGE_QA_DRIFT")
 return {
  "status":"PASS_4391_UNIQUE_HISTORIC_RESEARCH_FIXTURES_CROSS_SOURCE_QA",
  "checked_at_utc":datetime.now(timezone.utc).isoformat(),
  "research_league_fixture_records":len(rows),
  "unique_league_season_date_home_away_keys":len(distinct),
  "old_research_rows_frozen":counts["baseline"],
  "new_source_specific_research_rows":counts["new"],
  "new_2025_26_normal_stage_source_score_ONLY":counts["new_regular_stage_source_score_ONLY"],
  "previous_research_rows_prior_to_new_normal":3122,
  "new_normal_stage_GER3_ENG4_ENG5_ITA2_FRA2_GRE1_SCO1":1269,
  "source_files":by_block,
  "by_league":dict(sorted(source.items())),
  "by_season":dict(season),
  "old_296_HOLD_unchanged":True,
  "old_871_plus_904_external_source_score_QA_rerun":0,
  "prior_306_GER2_and_Swiss_161_and_Danish_192_independent_fact_QA_rerun":0,
  "new_2025_26_regular_stage_source_ONLY_NOT_INDEPENDENTLY_FT_CHECKED":1269,
  "historic_published_at_pre_match_feature_vintage_missing":True,
  "new_training_rows_approved":0,
  "production_10_league_M4_SHA_and_old_predictions_untouched":True,
  "user_manual_1855_xG_untouched":True,
  "excluded_abandoned_eng5_no_goal_technical_event":True,
  "next_distinct_step":"New independent FT witness only on 1269 previously uncorroborated source-only scored research records, then find rights-clean 2026/27 remaining five leagues. Do not rerun prior 1,775/461 verified facts."
 }
def test():
 assert sum(n for _,n in FILES.values())==1995
 assert sum(n for path,(_,n) in FILES.items() if "regular_stage_novel_only/" in path)==1269
 print("PASS pinned 2,396 + 1,995 new ledger = 4,391, original source files immutable")
if __name__=="__main__":
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true");args=p.parse_args()
 if args.self_test:test()
 if args.run:
  try:report=archive()
  except Exception as e:
   report={"status":"FAIL_CLOSED_NO_4391_QA_CLAIM","error_class":type(e).__name__,
    "reason":str(e)[:320],"new_training_rows_approved":0}
  print("4391_SOURCE_ACCOUNT_START")
  print(json.dumps(report,indent=2,ensure_ascii=False))
  print("4391_SOURCE_ACCOUNT_END")
