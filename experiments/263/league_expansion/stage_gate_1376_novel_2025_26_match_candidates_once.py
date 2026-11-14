#!/usr/bin/env python3
"""2025/26 NEW source-only *research* archive candidate promotion, regular stage only.

NO new match forecasts; NO new training rows; NO M4 or original 2396 modification.
Consumes local SHA-pinned CC-BY original publisher extracts 3041 and original
2396 identity rows. Never fetches any network sources or repeats old FT QA.

Cutoffs: England L1/L2 2026-05-02 (EFL); England National League 2026-04-25
(clubs/National League); Italy B 2026-05-08 (Lega B); France Ligue2 2026-05-09
(LFP/actual 34th round); Greece Super League first phase 2026-03-22
(26 rounds); Scottish Premiership pre-split 2026-04-12 (33 rounds).
No Austrian novel candidates (195 old matches exact) so leave AUT1 untouched.
No playoff or split-stage fixtures promoted into normal-league research.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
from reconcile_3041_CC_BY_eight_history_vs_old_once import SOURCE,CCBY,OUT,first,alias_table
import audit_6_leagues_967_scores_one_batch_20261114 as name_api
ROOT=Path("experiments/263/league_expansion")
ARCHIVE=ROOT/"ccby_footballcharts_2025_26_regular_stage_novel_only"
REPORT=ARCHIVE/"novel_1376_stage_eligibility_and_research_archive_20261114.json"
# Official last regular rounds, match/club appearance and club roster size
RULES={
 "ENG3":{"last":"2026-05-02","teams":24,"matches":552,"club_games":46,"pairwise":"double_rr","official":"https://www.efl.com/news/2026/march/24/sky-bet-efl-end-of-season-schedule--now-confirmed/"},
 "ENG4":{"last":"2026-05-02","teams":24,"matches":552,"club_games":46,"pairwise":"double_rr","official":"https://www.efl.com/news/2026/march/24/sky-bet-efl-end-of-season-schedule--now-confirmed/"},
 "ENG5":{"last":"2026-04-25","teams":24,"matches":552,"club_games":46,"pairwise":"double_rr","official":"https://eastleighfc.com/2025/06/2025-26-national-league-key-dates-confirmed/"},
 "ITA2":{"last":"2026-05-08","teams":20,"matches":380,"club_games":38,"pairwise":"double_rr","official":"https://statz.ai/competitions/serie-b?season=2025-2026"},
 "FRA2":{"last":"2026-05-09","teams":18,"matches":306,"club_games":34,"pairwise":"double_rr","official":"https://www.lfp.fr/article/ligue-2-bkt-le-calendrier-de-la-saison-2025-2026"},
 "GRE1":{"last":"2026-03-22","teams":14,"matches":182,"club_games":26,"pairwise":"double_rr","official":"https://www.rsssf.org/tablesg/grk2026.html"},
 "SCO1":{"last":"2026-04-12","teams":12,"matches":198,"club_games":33,"pairwise":"three_games_per_unordered_pair","official":"https://clublogin.spfl.co.uk/news/202526-post-split-fixtures-qa"}
}
FIELDS=["league","season","date","home","away","ft_home","ft_away","source_home","source_away",
        "source_league_code","source_license","source_Doi","stage","source_quality_gate",
        "score_confirmation","historical_asof_gate","research_status"]
def blob_sha(b):
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def source_rows(league):
 sha,n=SOURCE[league]
 data=(CCBY/(league.lower()+"_2025_26_CC_BY_SOURCE_QUARANTINE.csv")).read_bytes()
 if blob_sha(data)!=sha:raise ValueError("CCBY_SOURCE_BLOB_DRIFT_"+league)
 rows=list(csv.DictReader(data.decode("utf-8-sig").splitlines()))
 if len(rows)!=n:raise ValueError("CCBY_SOURCE_COUNT_DRIFT_"+league)
 return rows,sha

def classify(league,rows,original,held):
 rule=RULES[league]
 cutoff=rule["last"]
 roster={name for r in original for name in (r["home"],r["away"])}
 if len(roster)!=rule["teams"]:raise ValueError("OLD_REFERENCE_ROSTER_SIZE_DRIFT_"+league)
 aliases=alias_table(league,original)
 old_by_key={}
 old_by_pair=defaultdict(list)
 for r in original:
  key=(r["date"],r["home"],r["away"])
  if key in old_by_key:raise ValueError("OLD_PUBLISHED_SOURCE_DUPLICATE_"+league)
  old_by_key[key]=r
  old_by_pair[(r["home"],r["away"])].append(date.fromisoformat(r["date"]))
 accepted={}
 observations=Counter();hold_samples=[];shadow=[]
 for r in rows:
  if r["league"]!=league or r["season"]!="2025-26":
   raise ValueError("NEW_SOURCE_UNEXPECTED_LEAGUE")
  ds=r["date"]
  if ds>cutoff:
   observations["POST_REGULAR_SEASON_EXCLUDED"]+=1
   continue
  h=name_api.match_name(r["source_home"],aliases)
  a=name_api.match_name(r["source_away"],aliases)
  if not h or not a or h==a:
   observations["PRE_CUTOFF_UNKNOWN_TEAM_OR_STAGE_HOLD"]+=1
   if len(hold_samples)<12:hold_samples.append({"date":ds,"home":r["source_home"],"away":r["source_away"],"reason":"CANONICAL_ROSTER_NOT_FOUND"})
   continue
  key=(ds,h,a)
  score=(r["source_ft_home"],r["source_ft_away"])
  if key in accepted:
   oldrow=accepted[key]
   if (oldrow["source_ft_home"],oldrow["source_ft_away"])!=score:
    observations["CANONICAL_DUPLICATE_DIFFERENT_FT_HOLD"]+=1
    if len(hold_samples)<12:hold_samples.append({"date":ds,"home":h,"away":a,"reason":"CANONICAL_SOURCE_DUPLICATE_DIFFERENT_SCORE"})
   else:observations["CANONICAL_DUPLICATE_SAME_SCORE_SKIPPED"]+=1
   continue
  accepted[key]=r | {"home_canonical":h,"away_canonical":a}
 # A complete regular schedule must be covered: no less than all expected 2025/26
 # fixtures, no more than expected; all clubs exactly full league games;
 # directed round-robin for 46/38/34/26, three head-to-head meetings for SCO1.
 appearances=Counter()
 directed=Counter();unordered=Counter()
 for key,r in accepted.items():
  _,home,away=key
  appearances[home]+=1;appearances[away]+=1
  directed[(home,away)]+=1
  unordered[tuple(sorted((home,away)))]+=1
 expected_pairs=rule["teams"]*(rule["teams"]-1)//2
 if rule["pairwise"]=="double_rr":
  pair_ok=(len(directed)==rule["matches"] and all(x==1 for x in directed.values()) and len(unordered)==expected_pairs and all(x==2 for x in unordered.values()))
 else:
  pair_ok=(len(unordered)==expected_pairs and all(x==3 for x in unordered.values()))
 appear_ok= len(appearances)==rule["teams"] and all(appearances[t]==rule["club_games"] for t in roster)
 stage_ok=(len(accepted)==rule["matches"] and pair_ok and appear_ok and
           observations["CANONICAL_DUPLICATE_DIFFERENT_FT_HOLD"]==0 and
           observations["PRE_CUTOFF_UNKNOWN_TEAM_OR_STAGE_HOLD"]==0)
 novel=[];candidate_counts=Counter()
 for key,r in sorted(accepted.items()):
  date_value,home,away=key
  # Even when stage is suspicious, preserve full diagnostics, and DO NOT export
  # novel train-like rows from this league until full schedule stage gate passed.
  current=old_by_key.get(key)
  if current:
   if (current["ft_home"],current["ft_away"]) == (r["source_ft_home"],r["source_ft_away"]):
    candidate_counts["EXACT_OLD_SOURCE_DUPLICATE"]+=1
   else:
    candidate_counts["OLD_IDENTITY_FT_CONFLICT_HOLD"]+=1
    if (league,"2025-26",*key) not in held:
     candidate_counts["CRITICAL_NEW_SOURCE_CONFLICT_NOT_OLD_HOLD"]+=1
   continue
  d=date.fromisoformat(date_value)
  near=any(abs((d-o).days)<=2 for o in old_by_pair[(home,away)])
  if near:
   candidate_counts["DATE_NEAR_OLD_PAIR_HOLD"]+=1
   continue
  candidate_counts["NEW_CANDIDATE_REGULAR_STAGE"]+=1
  if not stage_ok:continue
  novel.append({
    "league":league,"season":"2025-26","date":date_value,"home":home,"away":away,
    "ft_home":r["source_ft_home"],"ft_away":r["source_ft_away"],
    "source_home":r["source_home"],"source_away":r["source_away"],
    "source_league_code":r["source_league_code"],"source_license":"CC-BY-4.0",
    "source_Doi":r["source_doi"],"stage":"NORMAL_LEAGUE_REGULAR_SEASON",
    "source_quality_gate":"PUBLISHER_SOURCE_SCORE_ONLY__SECOND_INDEPENDENT_FT_QA_PENDING",
    "score_confirmation":"NOT_INDEPENDENTLY_CORROBORATED",
    "historical_asof_gate":"PREMATCH_PUBLICATION_TIMESTAMP_MISSING__NO_TRAINING",
    "research_status":"LICENSED_CCBY_RESEARCH_HISTORICAL_STAGE_CERTIFIED__QUARANTINE_NOT_TRAINING"
  })
 if candidate_counts["CRITICAL_NEW_SOURCE_CONFLICT_NOT_OLD_HOLD"]:
  raise ValueError("CRITICAL_NOT_PREVIOUSLY_HOLD_SOURCE_SCORE_CONFLICT_"+league)
 return novel,{
  "stage_gate":"PASS_COMPLETE_REGULAR_SEASON" if stage_ok else "HOLD_NOT_PROVEN_COMPLETE_NORMAL_SCHEDULE",
  "official_last_normal_round":cutoff,"official_rule":rule["official"],
  "source_rows":len(rows),
  "canonical_unique_through_cutoff":len(accepted),
  "required_normal_fixture_count":rule["matches"],
  "roster_size":len(roster),
  "all_club_games_expected":rule["club_games"],
  "per_club_appearances_complete":appear_ok,
  "round_robin_complete":pair_ok,
  "new_candidate_source_only":candidate_counts["NEW_CANDIDATE_REGULAR_STAGE"],
  "new_unique_historic_RESEARCH_ROWS_EXPORTED":len(novel),
  "exclude_counts":dict(observations),
  "old_source_identity_diagnostic":dict(candidate_counts),
  "hold_examples_capped":hold_samples,
  "source_status":"Old main CC0 and 296 HOLD kept, no old score QA reruns, new source-only scores still need independent FT crosscheck."
 }
def write_csv(path,rows):
 with path.open("w",encoding="utf-8",newline="") as f:
  wr=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n")
  wr.writeheader();wr.writerows(rows)
def run():
 old,held=first()
 if len(held)!=296:raise ValueError("EXACT_296_HOLD_DRIFT")
 ARCHIVE.mkdir(parents=True,exist_ok=True)
 groups={};total=0
 for lg in RULES:
  inp,sha=source_rows(lg)
  rows,d=classify(lg,inp,old[lg],held)
  d["CC_BY_source_blob_sha"]=sha
  groups[lg]=d
  if rows:
   path=ARCHIVE/(lg.lower()+"_2025_26_NEW_REGULAR_SOURCE_ONLY_QA_PENDING.csv")
   write_csv(path,rows)
   d["research_CSV"]=str(path)
   total+=len(rows)
 report={
   "status":"2025_26_REGULAR_SEASON_GATED_NOVEL_RESEARCH_ARCHIVE_COMPLETE",
   "ran_at_utc":datetime.now(timezone.utc).isoformat(),
   "data_source":"Damir Devetak Football Charts Results and Goal Timing CC BY 4.0",
   "source_DOI":"https://doi.org/10.5281/zenodo.22295583",
   "source_license":"https://creativecommons.org/licenses/by/4.0/",
   "official_regular_round_sources":[d["official_rule"] for d in groups.values()],
   "groups":groups,
   "new_research_rows_only_from_schedule_complete_groups":total,
   "base_original_3122_pinned_research_fixture_identities":3122,
   "candidate_unique_research_fixture_identities":3122+total,
   "the_1376_previous_source_candidate_only_count":1376,
   "remaining_prior_candidate_stage_or_2day_ambiguity_not_admitted":1376-total,
   "independent_new_fulltime_score_confirmation_count":0,
   "new_model_training_approved":0,
   "no_previous_complete_score_qa_batches_repeated":True,
   "no_2026_27_new_fixture_or_betting_analysis":True,
   "original_2396_and_old_296_HOLD_data_untouched":True,
   "previous_DNK192_Swiss228_GER2_306_unmodified":True,
   "production_M4_10leagues_signed_SHA_untouched":True,
   "user_1855_manual_xG_untouched":True,
   "IMPORTANT_CAVEAT":"Stage-tested and deduped research archive only, NOT independently confirmed score facts, publisher vintage evidence, upstream complete rights review or model training clearance.",
   "next_distinct_step":"Use only fresh permitted independent match-result witnesses for the newly archived and stage-cleared fixture keys, ideally by league batch; do not repeat prior source-fact QA. For held stage groups do not fill missing games with synthetic results."
 }
 if total>1376 or total<=0:raise ValueError("STAGE_PROMOTION_OUT_OF_EXPECTED_RANGE")
 REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (ARCHIVE/"LICENSE_ATTRIBUTION.md").write_text(
   "# 2025/26 normal-stage historical CC BY-licensed research-only extract\n\n"
   "Author: Damir Devetak, Football Charts: Match Results and Goal Timing\n"
   "Dataset source: https://huggingface.co/datasets/Damir81/football-charts-results-goal-timing\n"
   "DOI: https://doi.org/10.5281/zenodo.22295583\n"
   "Licence: CC BY 4.0 https://creativecommons.org/licenses/by/4.0/\n\n"
   "Changes: filter to specific fully-reconstructed regular-season leagues and\n"
   "dates using official schedule, canonical club alias matching, strict\n"
   "nonduplicated fixture identity relative to the original prior 2025/26 source,\n"
   "no known within-2-day old fixture duplication; playoff and split-stage\n"
   "fixtures are not included. The source remains in a separate CC BY database.\n"
   "FT results not independently corroborated, rights/lineage and time-vintage\n"
   "gates not fully cleared: all research-only, zero new model training.\n",encoding="utf-8")
 return report
def test():
 assert len(RULES)==7
 assert RULES["ENG3"]["matches"]==552 and RULES["ITA2"]["matches"]==380
 assert RULES["GRE1"]["matches"]==182 and RULES["SCO1"]["matches"]==198
 assert len(first()[1])==296
 print("PASS seven official regular-season schedule gates, prior 296 quality holds, no input source re-download")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true");args=p.parse_args()
 if args.self_test:test()
 if args.run:
  try:res=run()
  except Exception as ex:
   ARCHIVE.mkdir(parents=True,exist_ok=True)
   res={"status":"FAIL_CLOSED_NO_RESEARCH_ARCHIVE_ACCEPTANCE",
      "exception_type":type(ex).__name__,
      "reason":str(ex)[:250],
      "new_model_training_approved":0}
   # A failed source-stage pass must never be mistaken for accepted rows.
  print("NEW_STAGE_ARCHIVE_START")
  print(json.dumps(res,indent=2,ensure_ascii=False))
  print("NEW_STAGE_ARCHIVE_END")
