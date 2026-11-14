#!/usr/bin/env python3
"""Immutable source-pointer selection for the 22-league / two-season closeout.

Does NOT rehost provider scores, delete a source, alter production M4, or promote
historical sources to model training. Reuses previously VERIFIED score-fact QA;
keeps unlicensed/suspect fixtures in a separate excluded class.
"""
from __future__ import annotations
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from datetime import date

from check_2396_296_hold_and_feature_vintage_once import holds
from check_1871_stage_vintage_shadow_gates_once import recognize_stage

ROOT=Path("experiments/263/league_expansion")
REVIEW=ROOT/"4505_rights_provenance_and_pre_kickoff_asof_source_gate_20261114.json"
FINAL=ROOT/"TEK_RAPOR_22_LIG_IKI_SEZON_GUNCEL_KAPANIS_20261114.md"
ESP=ROOT/"ccby_footballcharts_esp2_2025_26_original_source"
BEL=ROOT/"bel1_2025_26_one_official_missing/bel1_2025_26_312_source_stage_identity_completion_20261114.json"
CORE=Path("data/results_only_263/2026-11-10_completed_4617_scores_only.csv")
PROV=Path("data/results_only_263/4617_research_input_provenance.json")
OUT_CSV=ROOT/"FINAL_9460_SOURCE_ROW_DECISIONS_NO_SCORE_REHOST_20261114.csv"
OUT_JSON=ROOT/"FINAL_9460_RESEARCH_SCORE_FACTS_FILTERED_20261114.json"
CUT=date(2026,11,13)
ANALYSIS=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1","SCO1","DNK1","CHE1")
TRAIN=("ENG3","ENG4","ENG5","GER2","ESP2","ITA2","FRA2","GRE1","AUT1")
ALLOWED=set(ANALYSIS+TRAIN)
SEASONS={"2025-26","2026-27"}
BASE_RIGHTS={"PUBLISHER_CC0_CLAIM","CCBY_COMPILATION_UPSTREAM_UNCLEAR","THIRD_PARTY_REHOST_UNCLEARED"}
DECISIONS={
 "EXISTING_CORE_4617_FROZEN_RESULTS_ONLY",
 "SCORE_FACT_RESEARCH_ONLY_QA_PASS",
 "EXCLUDED_LEGACY_SCORE_OR_DATE_HOLD",
 "EXCLUDED_UNCLEARED_UPSTREAM_RIGHTS",
 "EXCLUDED_NONLEAGUE_CONFERENCE_PLAYOFF",
 "EXCLUDED_ABANDONED_NOT_FT"
}
def rows(path):
 with path.open(encoding="utf-8-sig",newline="") as f:
  return list(csv.DictReader(f))
def gitsha(b):
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def sourceid(r):
 return (r.get("league","").strip(), r.get("season","").strip(),
         r.get("date","").strip(), (r.get("home") or r.get("source_home") or "").strip(),
         (r.get("away") or r.get("source_away") or "").strip())
def is_false_fra2(r):
 k=sourceid(r)
 return k[0]=="FRA2" and k[1]=="2025-26" and k[2]=="2025-12-05" and "Bastia" in k[3] and "Red Star" in k[4]
def validate(r):
 k=sourceid(r)
 if k[0] not in ALLOWED or k[1] not in SEASONS:
  raise ValueError("SOURCE_OUTSIDE_22_BY_2: "+str(k))
 try: d=date.fromisoformat(k[2])
 except ValueError: raise ValueError("INVALID_DATE: "+str(k))
 if d>CUT or k[3]=="" or k[4]=="" or k[3]==k[4]:
  raise ValueError("INVALID_OR_FUTURE_MATCH: "+str(k))
 try:
  a=int(r.get("ft_home",""));b=int(r.get("ft_away",""))
 except ValueError: raise ValueError("UNSCORED_MATCH: "+str(k))
 if min(a,b)<0 or max(a,b)>25:raise ValueError("IMPLAUSIBLE_RESULT: "+str(k))
 return k
def ref_entry(path,idx,r,blob,decision,reason):
 key=validate(r)
 match_digest=hashlib.sha256(("\x1f".join(key)).encode()).hexdigest()
 return {"source_path":str(path),"source_row_1based":idx,
         "league":key[0],"season":key[1],"fixture_key_sha256":match_digest,
         "source_git_blob_sha":blob,"decision":decision,"reason":reason}
def execute():
 assert len(ALLOWED)==22 and len(ANALYSIS)==13 and len(TRAIN)==9
 review=json.loads(REVIEW.read_text())
 assert review["frozen_historical_source_only_fixture_identities"]==4505
 assert len(review["source_files"])==26 and review["newly_promoted_to_training"]==0
 prev_holds,eng5_holds,_=holds()
 assert len(prev_holds)==200 and len(eng5_holds)==96 and not (prev_holds&eng5_holds)
 prov=json.loads(PROV.read_text())
 assert hashlib.sha256(CORE.read_bytes()).hexdigest()==prov["source_snapshot_sha256"]
 original=rows(CORE)
 assert len(original)==4617
 audit=[]
 counter=Counter()
 sourcecount=Counter()
 pass_season=Counter()
 selected_ids=set()
 core_fixture_ids=set()
 for i,r in enumerate(original,2):
  k=validate(r)
  core_key=(k[0],k[1],k[2],k[3],k[4])
  if core_key in core_fixture_ids:raise ValueError("CORE_DUPLICATE_EXACT_KEY")
  core_fixture_ids.add(core_key)
  if k[0] not in ANALYSIS[:10]: raise ValueError("CORE_LEAGUE_NOT_OLD_TEN")
  audit.append(ref_entry(CORE,i,r,"PINNED_SHA256:"+prov["source_snapshot_sha256"],
     "EXISTING_CORE_4617_FROZEN_RESULTS_ONLY",
     "LEGACY_ADMISSION_UNCHANGED_99_RESULTS_ONLY_PARTIAL_OFFICIAL_CHECKS"))
  counter["EXISTING_CORE_4617_FROZEN_RESULTS_ONLY"]+=1
 assert len(audit)==4617
 seen_holds=set()
 seen_false=0
 conf=0
 for s in review["source_files"]:
  p=ROOT/s["path"]
  b=p.read_bytes()
  if gitsha(b)!=s["source_git_blob_sha"]:raise ValueError("RESEARCH_PIN_DRIFT: "+s["path"])
  data=rows(p)
  if len(data)!=s["research_rows"]:raise ValueError("RESEARCH_ROW_COUNT_DRIFT: "+s["path"])
  group=s["group"];rights=s["rights_status"]
  sourcecount[group]+=len(data)
  for i,r in enumerate(data,2):
   k=validate(r)
   if k in selected_ids:raise ValueError("RESEARCH_SOURCE_EXACT_DUPLICATE: "+str(k))
   selected_ids.add(k)
   if group=="ORIGINAL_BASE":
    if k in prev_holds or k in eng5_holds:
     decision="EXCLUDED_LEGACY_SCORE_OR_DATE_HOLD"
     reason="OLD200_OR_NEW96_EXACT_FT_DATE_HOLD"
     seen_holds.add(k)
    elif rights!="PUBLISHER_CC0_CLAIM":
     if rights not in BASE_RIGHTS:raise ValueError("UNKNOWN_BASE_RIGHTS")
     decision="EXCLUDED_UNCLEARED_UPSTREAM_RIGHTS"
     reason="PUBLISHER_CCBY_COMPILATION_OR_THIRD_PARTY_UNCLEARED"
    elif k[0]=="AUT1" and k[1]=="2025-26" and recognize_stage(r)=="conference_playoff":
     decision="EXCLUDED_NONLEAGUE_CONFERENCE_PLAYOFF"
     reason="AUT1_CONFERENCE_LEAGUE_PLAYOFF_NOT_REGULAR_LEAGUE"
     conf+=1
    else:
     decision="SCORE_FACT_RESEARCH_ONLY_QA_PASS"
     reason="CC0_PUBLISHER_SCORE_FACT_CORROBORATED_NO_PREKICKOFF_FEATURE_VINTAGE"
   else:
    if group=="NEW_SOURCE_1995" and is_false_fra2(r):
     decision="EXCLUDED_ABANDONED_NOT_FT"
     reason="BASTIA_RED_STAR_DEC5_ABANDONED_ADMIN_AWARD_NOT_FULL_TIME_0_0"
     seen_false+=1
    else:
     decision="SCORE_FACT_RESEARCH_ONLY_QA_PASS"
     reason=({"NEW_SOURCE_1995":"SOURCE_SPECIFIC_SECOND_FACT_OR_OFFICIAL_CORRECTION_QA_ONLY",
              "SEPARATE_PHASE_106":"PLAYOFF_OR_SECOND_PHASE_FT_WITNESSED_SEPARATE_STAGE",
              "TRANSITION_8":"CROSS_TIER_OR_QUALIFIER_FT_WITNESSED_NOT_LEAGUE_REGULAR"}[group])
   audit.append(ref_entry(p.relative_to(Path(".")),i,r,s["source_git_blob_sha"],decision,reason))
   counter[decision]+=1
   if decision=="SCORE_FACT_RESEARCH_ONLY_QA_PASS":
    pass_season[(k[0],k[1])]+=1
 assert sourcecount==Counter({"ORIGINAL_BASE":2396,"NEW_SOURCE_1995":1995,
                              "SEPARATE_PHASE_106":106,"TRANSITION_8":8}),sourcecount
 assert len(seen_holds)==296 and conf==3 and seen_false==1
 assert len(selected_ids)==4505
 assert counter["EXCLUDED_UNCLEARED_UPSTREAM_RIGHTS"]==325
 assert counter["SCORE_FACT_RESEARCH_ONLY_QA_PASS"]==3880,counter
 esp_reg=ESP/"esp2_2025_26_331_corrected_FT_independently_witnessed_RESEARCH_ONLY.csv"
 esp_po=ESP/"esp2_2025_26_6_PROMOTION_PLAYOFFS_RESEARCH_ONLY.csv"
 bel=json.loads(BEL.read_text())
 assert bel["additional_research_source_fixture_ids"]==1
 extras=[]
 for p,n in ((esp_reg,331),(esp_po,6)):
  data=rows(p)
  assert len(data)==n
  blob=gitsha(p.read_bytes())
  for i,r in enumerate(data,2):
   k=validate(r)
   if k in selected_ids or k in core_fixture_ids:raise ValueError("ESP2_OVERLAP")
   selected_ids.add(k)
   extras.append(ref_entry(p.relative_to(Path(".")),i,r,blob,
       "SCORE_FACT_RESEARCH_ONLY_QA_PASS",
       "ESP2_NEW_331_INDEPENDENT_FT_OR_6_PLAYOFF_WITNESS_NO_ASOF"))
   counter["SCORE_FACT_RESEARCH_ONLY_QA_PASS"]+=1
   pass_season[(k[0],k[1])]+=1
 m=bel["match"]
 if not (m["league"]=="BEL1" and m["date"]=="2026-05-03" and m["ft_home"]=="2" and m["ft_away"]=="1"):
  raise ValueError("BEL_OFFICIAL_FACT_CHANGED")
 key=validate(m)
 if key in core_fixture_ids or key in selected_ids:raise ValueError("BEL1_DUPLICATED")
 selected_ids.add(key)
 extras.append(ref_entry(BEL.relative_to(Path(".")),1,m,
    "SHA256:"+hashlib.sha256(BEL.read_bytes()).hexdigest(),
    "SCORE_FACT_RESEARCH_ONLY_QA_PASS",
    "BEL1_MISSING_ONE_OFFICIAL_CLUB_BOTH_SIDES_2_1_PLAYOFF"))
 counter["SCORE_FACT_RESEARCH_ONLY_QA_PASS"]+=1
 pass_season[(key[0],key[1])]+=1
 assert len(extras)==338 and len(selected_ids)==4843 and len(original)+len(selected_ids)==9460
 audit.extend(extras)
 assert len(audit)==9460 and counter["SCORE_FACT_RESEARCH_ONLY_QA_PASS"]==4218
 assert counter["EXCLUDED_LEGACY_SCORE_OR_DATE_HOLD"]==296
 assert sum(counter.values())==9460
 assert counter["EXCLUDED_NONLEAGUE_CONFERENCE_PLAYOFF"]==3
 assert counter["EXCLUDED_ABANDONED_NOT_FT"]==1
 # A target match is a label, never an input. Zero newly admitted training.
 fields=["source_path","source_row_1based","league","season","fixture_key_sha256",
         "source_git_blob_sha","decision","reason"]
 with OUT_CSV.open("w",encoding="utf-8",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(audit)
 stats={
  "date":"2026-11-14",
  "cutoff_matches_through":"2026-11-13",
  "branch":"research/263-13-lig-22-havuz-20261113",
  "status":"FINISHED_PINNED_SCORE_ONLY_SELECTION_NO_NEW_MODEL_TRAINING",
  "scope":{"leagues":22,"analysis_targets":13,"training_only":9,"seasons":2},
  "source_rows":9460,
  "frozen_core_4617":4617,
  "research_source_facts_4843":4843,
  "research_score_fact_qa_pass_only":4218,
  "research_excluded_quality_or_rights":625,
  "exclude_reason_counts":{"legacy_200_plus_96_exact_holds":296,
     "uncleared_upstream_rights":325,
     "Austrian_nonleague_conference_playoffs":3,
     "Bastia_Red_Star_abandoned_unplayed_FT":1},
  "selection_decisions":dict(counter),
  "research_subsources_4505":dict(sourcecount),
  "new_esp2_verified_331_regular_plus_6_playoffs":337,
  "new_belgium_official_verified_single_match":1,
  "research_score_facts_by_league_season":{"/".join(k):n for k,n in sorted(pass_season.items())},
  "core_99_results_partial_official_43_not_recertified":True,
  "original_m4_unchanged":True,
  "model_training_admitted_new_rows":0,
  "score_facts_only_not_a_features_snapshot":True,
  "remaining_5_current_league_cells_external_keyless_633_metadata_only":{"ENG5":190,"ESP2":141,"ITA2":110,"FRA2":108,"DNK1":84},
  "four_source_count_gap_unverified_118":{"SCO1":33,"CHE1":21,"GRE1":34,"AUT1":30},
  "research_only_not_ten_league_production":True,
  "strict_feature_rule":"No target fixture post-match xG/FT/HT used as an input; no fabricated historical available-at receipts; no training without rights and historical real availability proof.",
  "output_csv":str(OUT_CSV),
  "source_report":str(FINAL),
  "note":"921? Do not reinterpret score source QA as 13-league model readiness. Core 4617 is preserved and not newly certified. 4218 research match facts pass score-only and remain excluded from automatic training. 625 source rows are rejected from clean score-fact QA; original source records are preserved for audit."
 }
 # Defensive spelling: no hand-authored approximate figure embedded in manifest.
 stats["note"]=stats["note"].replace("921? ","")
 OUT_JSON.write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"count":len(audit),"score_fact_research_pass":4218,
      "research_rejected":625,"core_frozen":4617,"training_new":0,
      "csv":str(OUT_CSV)},ensure_ascii=False))
def selftest():
 assert len(ALLOWED)==22 and len(SEASONS)==2
 assert is_false_fra2({"league":"FRA2","season":"2025-26","date":"2025-12-05",
                        "home":"SC Bastia","away":"Red Star FC","ft_home":"0","ft_away":"0"})
 assert not is_false_fra2({"league":"FRA2","season":"2025-26","date":"2025-12-06",
                           "home":"SC Bastia","away":"Red Star FC"})
 a={"league":"ENG3","season":"2025-26","date":"2025-11-08","home":"A","away":"B",
    "ft_home":"2","ft_away":"0"}
 assert validate(a)[:3]==("ENG3","2025-26","2025-11-08")
 for patch in ({"date":"2026-11-14"},{"ft_home":""},{"season":"2024-25"},
               {"home":"B","away":"B"}):
  try:validate({**a,**patch})
  except ValueError:pass
  else:raise AssertionError("INVALID_SOURCE_ACCEPTED "+str(patch))
 print("PASS 22 league code / 2 season / invalid score / false 0-0 / cutoff guards")
if __name__=="__main__":
 import argparse
 parser=argparse.ArgumentParser()
 parser.add_argument("--self-test",action="store_true")
 parser.add_argument("--run",action="store_true")
 opts=parser.parse_args()
 if opts.self_test:selftest()
 if opts.run:execute()
