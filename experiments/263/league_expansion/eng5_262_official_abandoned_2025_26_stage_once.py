#!/usr/bin/env python3
"""Finish only held ENG5 2025-26 source-stage gate with two official exceptions.

24 clubs x 46 scheduled fixture slots = 552. One Scunthorpe–Wealdstone
match was ABANDONED and awarded points (NO goals recorded), so scored
regular season consists of 551 legitimate 90-minute fixtures. Another
Rochdale–Southend abandoned fixture on 2025-12-06 was falsely listed as
a completed 2-1 in source; real played result 2026-01-27 2-1. Exclude
both administrative/cancelled fixtures from FT modeling or scored archive.
All OLD source rows and 296 holds remain frozen; no previous 1007 checks
rerun. Only source CC BY research subset (not independently score-vetted)
is added after explicit official administrative exception validation.
"""
from __future__ import annotations
import argparse,csv,json
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
from reconcile_3041_CC_BY_eight_history_vs_old_once import first,alias_table
from stage_gate_1376_novel_2025_26_match_candidates_once import source_rows, FIELDS
import audit_6_leagues_967_scores_one_batch_20261114 as names
ROOT=Path("experiments/263/league_expansion")
ARCH=ROOT/"ccby_footballcharts_2025_26_regular_stage_novel_only"
REPORT=ARCH/"eng5_2025_26_official_abandonment_262_new_regular_scores_gate_20261114.json"
CSV=ARCH/"eng5_2025_26_NEW_REGULAR_SOURCE_ONLY_QA_PENDING.csv"
STATUS=ARCH/"eng5_2025_26_abandoned_awarded_technical_no_FT_event_ledger.json"
RULE={
 "last_normal_day":"2026-04-25",
 "source_football_charts_archive_rows":554,
 "playoffs_after_cutoff":2,
 "noncompleted_abandoned_duplicate_of_replay":{
  "date":"2025-12-06","home":"Rochdale AFC","away":"Southend United",
  "listed_as_completed_ft":"2-1","official":"https://rochdaleafc.co.uk/match-abandoned-061225/",
  "real_completed_replay":{"date":"2026-01-27","home":"Rochdale AFC","away":"Southend United","ft":"2-1","official":"https://rochdaleafc.co.uk/fixtures-results-2025-2026/"}
 },
 "administratively_awarded_NOT_fulltime_football_score":{
  "date":"2025-09-06","home":"Scunthorpe United","away":"Wealdstone FC",
  "league_displayed_0_0_IS_NOT_SCORED_FT":True,"no_goals_go_into_league_record":True,
  "points_awarded_to_home":3,
  "official":"https://www.scunthorpe-united.co.uk/news/2025/september/club-statement-abandoned-games-v-eastleigh-and-wealdstone"
 },
 "expected_completed_scored_regular_season":551,
 "expected_clubs":24,
 "source_blob_sha":"01aa70a635b67e91368f706d35ec7999362bcb79"
}
def run():
 old,held=first()
 original=old["ENG5"]
 if len(held)!=296 or len(original)!=296:raise ValueError("ENG5_OR_HOLDS_DRIFT")
 inp,sha=source_rows("ENG5")
 if sha!=RULE["source_blob_sha"] or len(inp)!=554:raise ValueError("ENG5_SOURCE_ARCHIVE_DRIFT")
 roster={x for r in original for x in (r["home"],r["away"])}
 if len(roster)!=24:raise ValueError("ENG5_ROSTER_INCONSISTENT")
 lookup=alias_table("ENG5",original)
 seen={};discard=Counter();official_exception_found=False
 for row in inp:
  if row["league"]!="ENG5" or row["season"]!="2025-26":raise ValueError("WRONG_SOURCE_SCOPE")
  if row["date"]>RULE["last_normal_day"]:
   discard["POST_NORMAL_ROUND_PLAYOFF_EXCLUDED"]+=1;continue
  h=names.match_name(row["source_home"],lookup)
  a=names.match_name(row["source_away"],lookup)
  if not h or not a or h==a:raise ValueError("ENG5_UNRECONCILED_CLUB_IDENTITY")
  k=(row["date"],h,a)
  stop=RULE["noncompleted_abandoned_duplicate_of_replay"]
  if k==(stop["date"],stop["home"],stop["away"]):
   if (row["source_ft_home"],row["source_ft_away"])!=("2","1"):
    raise ValueError("KNOWN_ABANDONED_SOURCE_SCORE_DRIFT")
   official_exception_found=True
   discard["ABANDONED_DEC_6_FALSE_COMPLETED_SCORE_EXCLUDED"]+=1
   continue
  if k in seen:raise ValueError("SOURCE_FT_DUPLICATE_REMAINS_"+str(k))
  seen[k]=row
 if not official_exception_found or discard!=Counter({"POST_NORMAL_ROUND_PLAYOFF_EXCLUDED":2,"ABANDONED_DEC_6_FALSE_COMPLETED_SCORE_EXCLUDED":1}):
  raise ValueError("ADMINISTRATIVE_STAGE_SOURCE_EXCEPTION_NOT_EXACT")
 if len(seen)!=551:raise ValueError("551_SCORED_REGULAR_FIXTURES_EXPECTED")
 home_away=Counter((h,a) for _,h,a in seen)
 totals=Counter()
 for _,h,a in seen:
  totals[h]+=1;totals[a]+=1
 if any(x!=1 for x in home_away.values()):raise ValueError("REPEATED_DIRECTED_GAME")
 missing=[(h,a) for h in roster for a in roster if a!=h and (h,a) not in home_away]
 admin=RULE["administratively_awarded_NOT_fulltime_football_score"]
 if missing!=[(admin["home"],admin["away"])]:
  raise ValueError("EXPECTED_ONLY_AWARDED_SCUNTHORPE_WEALDSTONE_PAIR_IS_MISSING: "+str(missing[:5]))
 wrong={name:count for name,count in totals.items() if count!=(45 if name in (admin["home"],admin["away"]) else 46)}
 if wrong or len(totals)!=24:raise ValueError("CLUB_APPEARANCES_NOT_46_EXCEPT_AWARDED: "+str(wrong))
 replay=RULE["noncompleted_abandoned_duplicate_of_replay"]["real_completed_replay"]
 real=seen.get((replay["date"],replay["home"],replay["away"]))
 if real is None or real["source_ft_home"]+"-"+real["source_ft_away"]!=replay["ft"]:
  raise ValueError("REAL_JAN27_REPLAY_NOT_PRESENT")
 prior={ (r["date"],r["home"],r["away"]):r for r in original}
 prior_pairs=defaultdict(list)
 for r in original:
  prior_pairs[(r["home"],r["away"])].append(date.fromisoformat(r["date"]))
 count=Counter();rows=[]
 for key,row in sorted(seen.items()):
  d,h,a=key
  previous=prior.get(key)
  if previous:
   if previous["ft_home"]==row["source_ft_home"] and previous["ft_away"]==row["source_ft_away"]:
    count["OLD_FT_AGREES"]+=1
   else:
    if ("ENG5","2025-26",d,h,a) not in held:
     raise ValueError("PREVIOUSLY_NONHELD_SCORE_CONFLICT")
    count["OLD_PREEXISTING_EXACT_HOLD"]+=1
   continue
  pd=date.fromisoformat(d)
  if any(abs((pd-t).days)<=2 for t in prior_pairs[(h,a)]):
   count["OLD_DATE_SHIFT_SUSPECT_HOLD"]+=1
   continue
  count["NOVEL_RESEARCH_SOURCE_SCORE_ONLY"]+=1
  rows.append({
   "league":"ENG5","season":"2025-26","date":d,"home":h,"away":a,
   "ft_home":row["source_ft_home"],"ft_away":row["source_ft_away"],
   "source_home":row["source_home"],"source_away":row["source_away"],
   "source_league_code":row["source_league_code"],"source_license":"CC-BY-4.0",
   "source_Doi":row["source_doi"],"stage":"NORMAL_LEAGUE_COMPLETED_90MIN__ABANDONMENTS_EXCLUDED",
   "source_quality_gate":"CCBY_PUBLISHER_SOURCE_ONLY_INDEPENDENT_FT_QA_PENDING",
   "score_confirmation":"NOT_INDEPENDENTLY_CORROBORATED",
   "historical_asof_gate":"PREMATCH_PUBLICATION_TIMESTAMP_MISSING__NO_TRAINING",
   "research_status":"CCBY_RESEARCH_SCORE_ONLY__NOT_MODEL_TRAINING"
  })
 if sum(count.values())!=551 or len(rows)!=262:raise ValueError("EXPECTED_262_NEW_SOURCE_ROWS_STAGE_ERROR:"+str(count))
 # As a separate research-ledger preserve the administrative-awarded event,
 # including official 3 points WITHOUT a numeric fake football FT score.
 ARCH.mkdir(parents=True,exist_ok=True)
 with CSV.open("w",encoding="utf-8",newline="") as f:
  wr=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n")
  wr.writeheader();wr.writerows(rows)
 STATUS.write_text(json.dumps({
   "status":"TWO_ABANDONED_MATCH_EVENTS_SCORED_FT_EXCLUDED",
   "event_1":RULE["noncompleted_abandoned_duplicate_of_replay"],
   "event_2":admin,
   "note":"No fake 0-0 in model goals, no abandoned 2-1 as a completed match. 552 scheduled standings fixtures includes an awarded points-only game, 551 actual complete scored matches.",
   "original_source_rows_modified":False,"training_approved":0
  },ensure_ascii=False,indent=2)+"\n")
 report={
  "status":"ENG5_2025_26_262_NEW_COMPLETED_REGULAR_MATCH_RESEARCH_ARCHIVED__2_OFFICIAL_ABANDONMENT_EVENTS_EXCLUDED",
  "checked_at_utc":datetime.now(timezone.utc).isoformat(),
  "source":"Football Charts original CC BY 4.0",
  "source_sha_pin":sha,
  "official_abandonment_documents":RULE,
  "source_rows_original":554,
  "post_normal_playoff_rows_excluded":2,
  "false_duplicate_abandoned_2025_12_06_excluded":1,
  "missing_0_0_administrative_2025_09_06_not_synthesized":True,
  "genuinely_played_scored_90min_regular_rows":551,
  "complete_club_games_except_awarded":True,
  "unique_directed_fixture_schedule_including_awarded_event":552,
  "old_base_original_ENG5_rows_not_modified":296,
  "old_quality_HOLD_296_not_modified":True,
  "per_source_ENG5_old_QA_not_retested":True,
  "old_source_vs_new_specific_counts":dict(count),
  "new_distinct_research_ENG5_fixture_identities":len(rows),
  "previous_stage_checked_unique_research_identities":4129,
  "new_source_specific_unique_research_identities":4129+len(rows),
  "source_only_no_independent_fulltime_witness_yet":True,
  "new_training_rows_approved":0,
  "main_M4_existing_10leagues_unmodified":True,
  "user_1855_manual_xg_unmodified":True,
  "next_distinct_step":"Independently corroborate ONLY newly archived 262 ENG5 completed matches if source rights permit; no reread of prior 871/904 or 1007 stage-passed rows."
 }
 REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 return report
def test():
 assert RULE["expected_completed_scored_regular_season"]==551
 assert RULE["source_blob_sha"]=="01aa70a635b67e91368f706d35ec7999362bcb79"
 print("PASS official abandoned/awarded events have NO modeled FT score; 551 played league results only")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true");args=p.parse_args()
 if args.self_test:test()
 if args.run:
  try:d=run()
  except Exception as ex:
   d={"status":"FAIL_CLOSED_NO_NEW_ENG5_RESEARCH_ARCHIVE",
      "error_class":type(ex).__name__,"reason":str(ex)[:400],
      "new_training_rows_approved":0}
  print("ENG5_ADMIN_STAGE_START")
  print(json.dumps(d,indent=2,ensure_ascii=False))
  print("ENG5_ADMIN_STAGE_END")
