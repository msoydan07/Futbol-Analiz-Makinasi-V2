#!/usr/bin/env python3
"""One-time OFFLINE 2025/26 stage-separated result research archive: 106 matches.

Select only matches beyond each competition's normal season from 7 previously
SHA-pinned licensed Football Charts CC BY 4.0 source CSVs. Preserve the
regular-season 4,391 original research match identities; NEVER add second-stage
scores to ordinary league form training or fit models. Use exact canonical team
rosters, official competition group membership and complete-round sanity checks.

The eight relegation/promotion INTERDIVISION crossover fixtures (FRA2 2, SCO1 6)
are kept in a separate source-specific HOLD ledger, not modeled as normal league.
One previously quarantined abandoned ENG5 fixture is not considered here.
No network calls, old result quality checks or re-fetches.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from datetime import datetime,date,timezone
from pathlib import Path
from reconcile_3041_CC_BY_eight_history_vs_old_once import first,alias_table
from stage_gate_1376_novel_2025_26_match_candidates_once import source_rows,RULES
from verify_4391_research_source_integrity_once import FILES
import audit_6_leagues_967_scores_one_batch_20261114 as aliases
ROOT=Path("experiments/263/league_expansion")
DEST=ROOT/"ccby_footballcharts_2025_26_106_separate_secondary_phase"
CSV_FIELDS=["league","season","date","home","away","ft_home","ft_away",
 "source_home","source_away","stage","source_league_code",
 "source_Doi","source_license","score_quality","asof_gate","research_status"]
HOLD_FIELDS=["league","season","date","source_home","source_away","ft_home","ft_away",
 "reason","source_Doi","license","training_status"]
AFTER={"ENG3":5,"ENG4":4,"ENG5":2,"ITA2":10,"FRA2":3,"GRE1":54,"SCO1":36}
IN_SCOPE={"ENG3":5,"ENG4":4,"ENG5":2,"ITA2":10,"FRA2":1,"GRE1":54,"SCO1":30}
EXTERNAL={"ENG3":0,"ENG4":0,"ENG5":0,"ITA2":0,"FRA2":2,"GRE1":0,"SCO1":6}
STAGE_COUNT={
 "ENG3_EFL_PROMOTION_PLAYOFF":5,
 "ENG4_EFL_PROMOTION_PLAYOFF_PARTIAL":4,
 "ENG5_NATIONAL_LEAGUE_PROMOTION_PLAYOFF_PARTIAL":2,
 "ITA2_SERIE_B_PROMOTION_PLAYOFF":8,
 "ITA2_SERIE_B_PLAYOUT":2,
 "FRA2_LIGUE_2_PROMOTION_PLAYOFF_PARTIAL":1,
 "GRE1_CHAMPIONSHIP_PLAYOFF_1_TO_4":12,
 "GRE1_EUROPE_PLAYOFF_5_TO_8":12,
 "GRE1_RELEGATION_PLAYOUT_9_TO_14":30,
 "SCO1_PREMIERSHIP_POST_SPLIT_TOP_6":15,
 "SCO1_PREMIERSHIP_POST_SPLIT_BOTTOM_6":15
}
GRE_GROUP_RAW={
 "GRE1_CHAMPIONSHIP_PLAYOFF_1_TO_4":("AEK Athens","Olympiacos Piraeus","PAOK","Panathinaikos"),
 "GRE1_EUROPE_PLAYOFF_5_TO_8":("Aris","OFI Crete","Volos","Levadiakos"),
 "GRE1_RELEGATION_PLAYOUT_9_TO_14":("AEL Larissa","Asteras Tripolis","Kifisia","Panetolikos","Panserraikos","Atromitos")
}
SCO_GROUP_RAW={
 "SCO1_PREMIERSHIP_POST_SPLIT_TOP_6":("Celtic","Falkirk","Hearts","Hibernian","Motherwell","Rangers"),
 "SCO1_PREMIERSHIP_POST_SPLIT_BOTTOM_6":("Aberdeen","Dundee FC","Dundee Utd","Kilmarnock","Livingston","St. Mirren")
}
OFFICIAL_SOURCES={
 "ITA2":"https://d5rzfs5ck83rq.cloudfront.net/legab.it/documenti/2025-26/C.U._LNPB_n._176_del_09.05.2026_-_Accoppiamenti_gare_playoff_e_playout_Serie_BKT_2025-2026.pdf",
 "GRE1":"https://www.rsssf.org/tablesg/grk2026.html",
 "SCO1":"https://spfl.co.uk/news/press-release-post-split-fixtures-51159",
 "ENG3":"https://www.efl.com/news/2026/march/24/sky-bet-efl-end-of-season-schedule--now-confirmed/",
 "ENG4":"https://www.efl.com/news/2026/march/24/sky-bet-efl-end-of-season-schedule--now-confirmed/",
 "ENG5":"https://eastleighfc.com/2025/06/2025-26-national-league-key-dates-confirmed/",
 "FRA2":"https://www.lfp.fr/article/ligue-2-bkt-le-calendrier-de-la-saison-2025-2026"
}
def blob(x):
 return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()
def groups_for(lg,look):
 rawgroups=GRE_GROUP_RAW if lg=="GRE1" else SCO_GROUP_RAW
 result={}
 for name,clubnames in rawgroups.items():
  converted=[]
  for n in clubnames:
   c=aliases.match_name(n,look)
   if not c:raise ValueError("OFFICIAL_GROUP_CLUB_NOT_MAPPED_"+lg+"_"+n)
   converted.append(c)
  if len(set(converted))!=len(clubnames):raise ValueError("OFFICIAL_GROUP_TEAM_DUPLICATION")
  result[name]=set(converted)
 allteams=[c for value in result.values() for c in value]
 if len(allteams)!=len(set(allteams)):raise ValueError("OFFICIAL_GROUP_OVERLAP")
 return result
def phase(lg,h,a,clubgroups):
 if lg=="ITA2":
  return "ITA2_SERIE_B_PLAYOUT" if {h,a}=={"SSC Bari","FC Südtirol"} else "ITA2_SERIE_B_PROMOTION_PLAYOFF"
 if lg=="GRE1" or lg=="SCO1":
  matches=[key for key,members in clubgroups.items() if h in members and a in members]
  if len(matches)!=1:raise ValueError("CROSS_GROUP_OR_INVALID_POSTSEASON_PAIR_"+lg+":"+h+"/"+a)
  return matches[0]
 return {
 "ENG3":"ENG3_EFL_PROMOTION_PLAYOFF",
 "ENG4":"ENG4_EFL_PROMOTION_PLAYOFF_PARTIAL",
 "ENG5":"ENG5_NATIONAL_LEAGUE_PROMOTION_PLAYOFF_PARTIAL",
 "FRA2":"FRA2_LIGUE_2_PROMOTION_PLAYOFF_PARTIAL"
 }[lg]
def verify_postphase_pairs(entries,lg,group_set):
 if lg=="GRE1":
  for stage in GRE_GROUP_RAW:
   rows=[r for r in entries if r["stage"]==stage]
   members=group_set[stage]
   directed=Counter((r["home"],r["away"]) for r in rows)
   expected_count=len(members)*(len(members)-1)
   if len(rows)!=expected_count or set(c for t in directed for c in t)!=members or len(directed)!=expected_count or any(v!=1 for v in directed.values()):
    raise ValueError("GREEK_TWO_LEG_GROUP_SCHEDULE_NOT_COMPLETE_"+stage)
 if lg=="SCO1":
  for stage in SCO_GROUP_RAW:
   rows=[r for r in entries if r["stage"]==stage]
   members=group_set[stage]
   unordered=Counter(tuple(sorted((r["home"],r["away"]))) for r in rows)
   appearance=Counter()
   for r in rows:
    appearance[r["home"]]+=1;appearance[r["away"]]+=1
   if len(rows)!=15 or len(unordered)!=15 or any(v!=1 for v in unordered.values()) or any(appearance[t]!=5 for t in members) or set(appearance)!=members:
    raise ValueError("SCOTTISH_POST_SPLIT_FIVE_MATCHES_PER_CLUB_GATE_"+stage)
def load_existing(lg,old):
 done={(r["date"],r["home"],r["away"]) for r in old}
 p=ROOT/"ccby_footballcharts_2025_26_regular_stage_novel_only"/(lg.lower()+"_2025_26_NEW_REGULAR_SOURCE_ONLY_QA_PENDING.csv")
 if p.exists():
  raw=p.read_bytes()
  src_key="ccby_footballcharts_2025_26_regular_stage_novel_only/"+p.name
  expected,n=FILES[src_key]
  if blob(raw)!=expected:raise ValueError("PREVIOUS_1269_ARCHIVE_BLOB_CHANGED")
  parsed=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
  if len(parsed)!=n:raise ValueError("PREVIOUS_1269_SOURCE_COUNT_DRIFT")
  done.update((r["date"],r["home"],r["away"]) for r in parsed)
 return done
def archive():
 old,priorheld=first()
 if len(priorheld)!=296:raise ValueError("OLDER_296_HOLD_CHANGED")
 existing=json.loads((ROOT/"research_historical_4391_distinct_source_accounting_20261114.json").read_text())
 if existing["status"]!="PASS_4391_UNIQUE_HISTORIC_RESEARCH_FIXTURES_CROSS_SOURCE_QA" or existing["unique_league_season_date_home_away_keys"]!=4391:
  raise ValueError("4391_PREVIOUS_QA_NOT_FROZEN")
 output={};officialouts=[];allnew=[];counts=Counter();sha=[]
 for lg in AFTER:
  inp,gitsha=source_rows(lg)
  prior=old[lg]
  known=load_existing(lg,prior)
  look=alias_table(lg,prior)
  groups=groups_for(lg,look) if lg in ("GRE1","SCO1") else {}
  records=[];outs=[];dates=set()
  for r in inp:
   if r["date"]<=RULES[lg]["last"]:continue
   date_str=r["date"]
   h=aliases.match_name(r["source_home"],look)
   a=aliases.match_name(r["source_away"],look)
   if not h or not a or h==a:
    outs.append({
      "league":lg,"season":"2025-26","date":date_str,
      "source_home":r["source_home"],"source_away":r["source_away"],
      "ft_home":r["source_ft_home"],"ft_away":r["source_ft_away"],
      "reason":"OUT_OF_PRIOR_LEAGUE_ROSTER_CROSS_TIER_PROMOTION_RELEGATION_PLAYOFF",
      "source_Doi":r["source_doi"],"license":"CC-BY-4.0",
      "training_status":"HOLD_DIFFERENT_COMPETITION_IDENTITY_NO_TRAINING"
    })
    continue
   key=(date_str,h,a)
   if key in known:raise ValueError("EXISTS_IN_4391_RESEARCH_ALREADY_"+lg+":"+str(key))
   if key in dates:raise ValueError("DUPLICATE_NEW_STAGE_MATCH_KEY_"+str(key))
   dates.add(key)
   st=phase(lg,h,a,groups)
   row={
      "league":lg,"season":"2025-26","date":date_str,
      "home":h,"away":a,
      "ft_home":r["source_ft_home"],"ft_away":r["source_ft_away"],
      "source_home":r["source_home"],"source_away":r["source_away"],
      "stage":st,
      "source_league_code":r["source_league_code"],
      "source_Doi":r["source_doi"],"source_license":"CC-BY-4.0",
      "score_quality":"ONE_SOURCE_ONLY__SECOND_INDEPENDENT_MATCH_FACT_WITNESS_PENDING",
      "asof_gate":"NO_HISTORIC_BEFORE_KICKOFF_PUBLICATION_PROOF",
      "research_status":"SEPARATE_PHASE_RESEARCH_ONLY__NOT_NORMAL_LEAGUE_OR_TRAINING"
   }
   records.append(row)
   counts[st]+=1
  if len(records)!=IN_SCOPE[lg] or len(outs)!=EXTERNAL[lg] or len(records)+len(outs)!=AFTER[lg]:
   raise ValueError("POSTSEASON_GROUP_COUNT_DRIFT_"+lg+":"+str((len(records),len(outs))))
  verify_postphase_pairs(records,lg,groups)
  allnew.extend(records);officialouts.extend(outs)
  sha.append({"league":lg,"pinned_original_CC_BY_source_git_blob":gitsha,
              "expected_after_normal_source":AFTER[lg],
              "separate_stage_candidates":len(records),"outside_roster_HOLD":len(outs)})
  output[lg]=records
 if dict(counts)!=STAGE_COUNT:raise ValueError("COMPETITION_STAGE_DISTRIBUTION_NOT_AS_EXPECTED:"+str(counts))
 if len(allnew)!=106 or len(officialouts)!=8:
  raise ValueError("EXPLICIT_POST_REGULAR_STAGE_COUNTS_INVALID")
 newkeys={(r["league"],r["season"],r["date"],r["home"],r["away"]) for r in allnew}
 if len(newkeys)!=106:raise ValueError("NEW_STAGE_DUPLICATE_GLOBAL")
 # Abandoned Rochdale-Southend December 6 and the awarded Scunthorpe-
 # Wealdstone cannot be represented as FT results; they were already excluded
 # from normal source and SHALL NOT be fabricated in this poststage extract.
 ARCH=ROOT/"ccby_footballcharts_2025_26_regular_stage_novel_only"
 former=json.loads((ARCH/"eng5_2025_26_official_abandonment_262_new_regular_scores_gate_20261114.json").read_text())
 if former["new_distinct_research_ENG5_fixture_identities"]!=262:
  raise ValueError("ABANDONMENT_POLICY_NOT_PRESERVED")
 DEST.mkdir(parents=True,exist_ok=True)
 for lg,rows in output.items():
  p=DEST/(lg.lower()+"_2025_26_SECOND_PHASE_ONLY_LICENSED_SOURCE_QA_PENDING.csv")
  with p.open("w",newline="",encoding="utf-8") as f:
   wr=csv.DictWriter(f,fieldnames=CSV_FIELDS,lineterminator="\n")
   wr.writeheader()
   wr.writerows(sorted(rows,key=lambda x:(x["date"],x["home"],x["away"])))
 with (DEST/"eight_interdivision_playoff_2025_26_HOLD_source_only.csv").open("w",newline="",encoding="utf-8") as f:
  wr=csv.DictWriter(f,fieldnames=HOLD_FIELDS,lineterminator="\n")
  wr.writeheader();wr.writerows(sorted(officialouts,key=lambda x:(x["league"],x["date"],x["source_home"])))
 report={
 "status":"PASS_ARCHIVED_106_DISTINCT_2025_26_SECOND_PHASE_MATCH_IDENTITIES_8_CROSS_TIER_HOLD",
 "snapshot_at_utc":datetime.now(timezone.utc).isoformat(),
 "source":"Football Charts (Damir Devetak), one original CC BY 4.0 research source snapshot (existing GitHub pinned files only)",
 "source_doi":"https://doi.org/10.5281/zenodo.22295583",
 "license_url":"https://creativecommons.org/licenses/by/4.0/",
 "source_git_blob_pins":sha,
 "seasons":["2025-26"],
 "source_after_cutoff_scored_rows_considered":114,
 "new_2025_26_additional_stage_research_source_match_identities":106,
 "new_phase_by_name":dict(counts),
 "different_league_transition_playoff_HOLD":8,
 "different_league_transition_HOLD_breakdown":{"FRA2":2,"SCO1":6},
 "research_base_4391_original_identity_rows_untouched":True,
 "other_source_separate_stage_identity_total_after_addition":4497,
 "old_one_source_original_FRA2_abandoned_Bastia_RedStar_0_0_still_held":True,
 "one_old_National_League_abandoned_replay_and_awarded_event_retained_as_technical_no_goals":True,
 "no_previous_1268_and_461_and_1775_score_fact_checks_reexecuted":True,
 "stage_allocation_validated_by_source_round_robin":{
   "GREEK_4_plus_4_plus_6_groups":"12 championship + 12 Europe + 30 relegation, complete group 2-leg source round-robin",
   "SCOTTISH_TOP_AND_BOTTOM_SIX":"15+15, each club five games, full single round-robin"
 },
 "official_competition_stage_reference_urls":OFFICIAL_SOURCES,
 "stage_ENG4_and_FRA2_are_partial_source_club_playoff_result_sets":True,
 "not_model_training_or_normal_league_matches":True,
 "fresh_independent_score_facts_verified":0,
 "source_upstream_rights_asof_gate_still_pending":True,
 "new_training_rows_approved":0,
 "production_M4_and_10_league_signed_results_unchanged":True,
 "user_manual_xg_workbook_unchanged":True,
 "next_distinct_step":"Compare ONLY 106 new separate-stage fixture scores to second source; keep 8 interdivision source rows under HOLD pending explicit cross-competition identity and provenance, without changing original regular league score history."
 }
 (DEST/"2025_26_106_second_phase_8_cross_tier_source_gate_20261114.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 (DEST/"ATTRIBUTION_LICENSE.md").write_text(
    "# Separate second-phase / playoff match-result research-only archive\n\n"
    "Data by football-charts.com / Damir Devetak. CC BY 4.0.\n"
    "DOI: https://doi.org/10.5281/zenodo.22295583\n"
    "Source original publisher snapshot: previously SHA-pinned 2025/26 league CSV extracts.\n\n"
    "Modified by filtering only post-normal-season matches and mapping the\n"
    "publisher's team names to the 2025/26 league-specific research team IDs;\n"
    "classifying Championship / Europe / relegation / Premiership-split phases;\n"
    "and quarantining 8 matches involving lower-tier teams. No final-result\n"
    "source was re-downloaded. This database has NO model training approval:\n"
    "original-source result facts await an independent witness, historical\n"
    "pre-kickoff availability and source provenance rights proof.\n",encoding="utf-8")
 return report
def test():
 assert sum(AFTER.values())==114 and sum(IN_SCOPE.values())==106
 assert sum(EXTERNAL.values())==8 and sum(STAGE_COUNT.values())==106
 for lg in IN_SCOPE:
  assert lg in RULES
 print("PASS 114 source post-reg split into 106 own-tier and 8 cross-tier HOLD; groups separate; zero old FT recheck")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true")
 opt=p.parse_args()
 if opt.self_test:test()
 if opt.run:
  try:d=archive()
  except Exception as ex:d={"status":"FAIL_CLOSED_STAGE_ARCHIVE_NOT_APPROVED",
                         "error_class":type(ex).__name__,"reason":str(ex)[:300],
                         "new_training_rows_approved":0}
  print("STAGE_106_START")
  print(json.dumps(d,ensure_ascii=False,indent=2))
  print("STAGE_106_END")
