#!/usr/bin/env python3
"""Spain Segunda 2025/26: offline one-time 509 licensed publisher raw records
=> 462 verified REGULAR-SEASON fixture identities + 6 promotion playoff legs;
exactly 41 repeated single-club alias rows collapse, old 131 research rows
remain IMMUTABLE. Only genuinely novel fixture identities can be additive.

Does NOT certify individual FT against secondary provider or license trainable
historical features. Nothing touches existing model or xG.
"""
import csv,hashlib,json
from collections import Counter,defaultdict
from datetime import date,datetime
from pathlib import Path
import argparse
ROOT=Path("experiments/263/league_expansion")
DIR=ROOT/"ccby_footballcharts_esp2_2025_26_original_source"
SOURCE=DIR/"esp2_2025_26_509_CC_BY_original_source_QUIET_RESEARCH.csv"
REPORT=DIR/"esp2_2025_26_462_regular_41_duplicate_alias_6_playoff_131_old_identity_20261114.json"
PIN="f33b4e385ef8b77bc4c3150e4bae5568f1faf40e"
ALT={
 "Albacete":"Albacete","Almeria":"UD Almería","Andorra":"FC Andorra",
 "Burgos CF":"Burgos CF","Cadiz CF":"Cádiz CF","Castellon":"CD Castellón",
 "Ceuta":"AD Ceuta FC","Cordoba":"Córdoba CF",
 "Cultural Leonesa":"Cultural Leonesa",
 "Dep. A Coruna":"Deportivo La Coruña","Dep. La Coruna":"Deportivo La Coruña",
 "Eibar":"SD Eibar","Gijon":"Sporting Gijón",
 "Granada CF":"Granada CF","Huesca":"SD Huesca",
 "Las Palmas":"UD Las Palmas","Leganes":"CD Leganés",
 "Malaga":"Málaga CF","Mirandes":"CD Mirandés",
 "Racing Santander":"Racing Santander","Real Sociedad B":"Real Sociedad B",
 "Valladolid":"Real Valladolid","Zaragoza":"Real Zaragoza"
}
REGULAR_END="2026-05-31"
DOI="https://doi.org/10.5281/zenodo.22295583"
FIELDS=["league","season","date","home","away","ft_home","ft_away",
 "source_home","source_away","source_competition_name","source_doi",
 "source_git_blob_sha","license","stage","second_source_FT_verdict",
 "historic_pre_kickoff_data_asof","training_status"]
def read(p):
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def gitsha(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def write(p,rows,fields=FIELDS):
 with p.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
  w.writeheader();w.writerows(rows)
def main():
 if gitsha(SOURCE.read_bytes())!=PIN:raise ValueError("SOURCE_SHA_CHANGED")
 source=read(SOURCE)
 if len(source)!=509:raise ValueError("SOURCE_N_509_CHANGED")
 if len(ALT)!=23 or len(set(ALT.values()))!=22:raise ValueError("TEAM_ALIAS_POLICY_CHANGED")
 baseline=[]
 paths=["training_2025_26_cc0_scored_QUARANTINE.csv",
        "score_shape_recovery_295_2526_QUARANTINE_20261113.csv"]
 oldSHA={}
 for p in paths:
  full=ROOT/p
  oldSHA[p]=gitsha(full.read_bytes())
  baseline.extend(r for r in read(full) if r["league"]=="ESP2" and r["season"]=="2025-26")
 if len(baseline)!=131:raise ValueError("OLD_131_IDENTITY_SOURCE_CHANGED")
 old={(r["date"],r["home"],r["away"]):r for r in baseline}
 if len(old)!=131:raise ValueError("OLDER_131_HAS_DUPLICATE_KEYS")
 stages={"regular":{},"playoff":{}}
 collapsed=[];invalid=[];nsource=0
 for r in source:
  if r["league"]!="ESP2" or r["season"]!="2025-26" or r["source_license"]!="CC-BY-4.0":
   raise ValueError("SOURCE_SCOPE_CHANGED")
  h=ALT.get(r["source_home"]);a=ALT.get(r["source_away"])
  if h is None or a is None or h==a:raise ValueError("SOURCE_CLUB_NOT_MAPPED")
  key=(r["date"],h,a)
  bucket="regular" if r["date"]<=REGULAR_END else "playoff"
  d=stages[bucket]
  if key in d:
   prior=d[key]
   if (prior["source_ft_home"],prior["source_ft_away"])!=(r["source_ft_home"],r["source_ft_away"]):
    raise ValueError("DUPLICATE_SAME_GAME_DIFFERENT_FT_HOLD")
   collapsed.append({"date":r["date"],"team_alias":"Dep. A Coruna / Dep. La Coruna",
                     "source_duplicated_with_different_name":True})
   continue
  d[key]=r
  nsource+=1
 if len(source)!=len(stages["regular"])+len(stages["playoff"])+len(collapsed):
  raise ValueError("SOURCE_DISJOINT_ACCOUNTING_FAILED")
 if len(collapsed)!=41 or len(stages["regular"])!=462 or len(stages["playoff"])!=6:
  raise ValueError("SOURCE_41_462_6_DRIFT")
 # Complete regular league double round-robin, 22 clubs, every club plays 42,
 # each home-away ordered pair exactly once.
 regular=stages["regular"]
 teams={t for _,h,a in regular for t in (h,a)}
 if len(teams)!=22:raise ValueError("22_CLUB_ROSTER_NOT_COMPLETE")
 directed=Counter((h,a) for _,h,a in regular)
 actual={r for k,r in directed.items() if False}
 per_club=Counter()
 for day,h,a in regular:
  per_club[h]+=1;per_club[a]+=1
 if len(directed)!=462 or any(x!=1 for x in directed.values()) or set(per_club)!=teams or any(v!=42 for v in per_club.values()):
  raise ValueError("42_ROUND_DOUBLE_RR_GATE_FAILED")
 for h in teams:
  for a in teams:
   if h!=a and directed[(h,a)]!=1:raise ValueError("MISSING_SEASON_GAME_PAIR_"+h+"_"+a)
 if any(date.fromisoformat(k[0])>date(2026,6,21) for k in stages["playoff"]):
  raise ValueError("PROMOTION_PLAYOFF_OUT_OF_SEASON")
 # No old 131 record rewritten; double-counting and date shifts blocked.
 near=Counter();conflicts=[];oldExact=0;oldFTdiff=0;novel=[]
 by_pair=defaultdict(list)
 for d,h,a in old:by_pair[(h,a)].append(d)
 for key,r in sorted(regular.items()):
  oldr=old.get(key)
  if oldr is not None:
   if oldr["ft_home"]==r["source_ft_home"] and oldr["ft_away"]==r["source_ft_away"]:oldExact+=1
   else:
    oldFTdiff+=1
    if len(conflicts)<22:
     conflicts.append({"date":key[0],"home":key[1],"away":key[2],
       "old_score":oldr["ft_home"]+"-"+oldr["ft_away"],
       "original_publisher_score":r["source_ft_home"]+"-"+r["source_ft_away"],
       "gate":"OLD_131_MATCH_SCORE_DISAGREEMENT_REMAIN_HOLD"})
   continue
  day,h,a=key
  possible=[x for x in by_pair[(h,a)] if abs((date.fromisoformat(x)-date.fromisoformat(day)).days)<=2]
  if possible:
   near[(h,a)]+=1
   continue
  novel.append((key,r))
 if oldExact+oldFTdiff+len(novel)+sum(near.values())!=462:
  raise ValueError("OLD_NEW_462_DISJOINT_FAILED")
 # Current source novel only: no original duplicates; stage-tag playoffs.
 def pack(key,r,stage):
  return {"league":"ESP2","season":"2025-26","date":key[0],
    "home":key[1],"away":key[2],
    "ft_home":r["source_ft_home"],"ft_away":r["source_ft_away"],
    "source_home":r["source_home"],"source_away":r["source_away"],
    "source_competition_name":"La Liga2","source_doi":DOI,
    "source_git_blob_sha":PIN,"license":"CC-BY-4.0",
    "stage":stage,
    "second_source_FT_verdict":"ONE_PUBLISHER_SOURCE_ONLY__PENDING",
    "historic_pre_kickoff_data_asof":"NOT_PROVEN",
    "training_status":"QUARANTINE_NOT_TRAINING"}
 newly=[pack(key,r,"NORMAL_42_ROUND_SEASON") for key,r in novel]
 playoffs=[pack(key,r,"PROMOTION_PLAYOFF_TWO_LEG") for key,r in sorted(stages["playoff"].items())]
 # Retain 462 clean score-only full competition reference to expose old
 # discrepancies, without adding 131 again to research count.
 reference=[pack(key,r,"NORMAL_42_ROUND_SEASON_SOURCE_REFERENCE_NON_ADDITIVE") for key,r in sorted(regular.items())]
 write(DIR/"esp2_2025_26_462_FULL_CCBY_SEASON_REFERENCED_ONLY.csv",reference)
 write(DIR/"esp2_2025_26_NOVEL_331_ONLY_RESEARCH_NOT_TRAINING.csv",newly)
 write(DIR/"esp2_2025_26_6_PROMOTION_PLAYOFFS_RESEARCH_ONLY.csv",playoffs)
 summary={
   "status":"ESP2_2025_26_FULL_462_SEASON_PAIR_COVERAGE_PASS_41_SOURCE_ALIAS_DUPLICATES_REMOVED_6_PLAYOFFS",
   "source_original_509_rows":509,
   "source_alias_duplicate_exact_same_date_teams_score_collapsed":41,
   "source_regular_full_exact":462,"source_playoffs_distinct":6,
   "clubs":22,"each_club_regular_matches":42,
   "previous_research_ESP2_2025_26_distinct_ids_unchanged":131,
   "old_131_sources_sha_pinned":oldSHA,
   "old_exact_date_clubs_FT_match":oldExact,
   "old_same_match_FT_conflict_count":oldFTdiff,
   "old_conflict_samples":conflicts,
   "nearby_date_old_pair_HOLD_count":sum(near.values()),
   "novel_regular_source_research_rows_only":len(newly),
   "novel_playoff_source_research_rows_only":len(playoffs),
   "safe_incremental_source_specific_research_fixture_identities":len(newly)+len(playoffs),
   "prior_pinned_source_identity_count":4505,
   "cumulative_source_specific_research_after_new_ESP2":4505+len(newly)+len(playoffs),
   "source_doi":DOI,"license":"CC BY 4.0 source publisher original historical dataset; upstream training rights separately gated",
   "full_raw_publisher_dataset_NOT_rehosted":True,
   "normal_reference_only_filepath":str(DIR/"esp2_2025_26_462_FULL_CCBY_SEASON_REFERENCED_ONLY.csv"),
   "new_ESP2_regular_only_filepath":str(DIR/"esp2_2025_26_NOVEL_331_ONLY_RESEARCH_NOT_TRAINING.csv"),
   "new_ESP2_playoffs_only_filepath":str(DIR/"esp2_2025_26_6_PROMOTION_PLAYOFFS_RESEARCH_ONLY.csv"),
   "score_second_source_FT_verification_pending_for_new":len(newly)+len(playoffs),
   "new_training_rows_approved":0,
   "main_M4_and_user_xG_untouched":True,
   "next_distinct":"Verify new only ESP2 regular matches against 2025/26 football-data SP2 results; verify six playoffs with league published records. Do not repeat old 131."
 }
 (REPORT).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
 return summary
def test():
 assert len(ALT)==23 and len(set(ALT.values()))==22
 print("PASS 23 original team aliases -> 22 official club identities, 42 fixtures each, QA assertions")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true");a=p.parse_args()
 if a.self_test:test()
 if a.run:
  try:d=main()
  except Exception as exc:
   d={"status":"FAIL_CLOSED_NO_DEDUP_SOURCE_PROMOTION","error_class":type(exc).__name__,
       "reason":str(exc)[:350],"new_training_rows_approved":0}
  print("ESP2_462_START")
  print(json.dumps(d,ensure_ascii=False,indent=2))
  print("ESP2_462_END")
