#!/usr/bin/env python3
"""One NEW, pinned, 22 leagues x 2 seasons source inventory with 10 league baseline.

Strictly OFFLINE except optional one-time named Spanish 2025/26 source *metadata*
probe from previously vetted CC BY source. No prior 22-season source results are
modified; NO rerun of old score, playoff, xG, model-fitting or pilot QA.
No model training approvals. No duplicate sum of 4,617 and 4,505.
"""
import csv, hashlib, json, argparse, sys, re
from collections import Counter,defaultdict
from pathlib import Path
from datetime import date
from urllib.request import Request, urlopen
ROOT=Path("experiments/263/league_expansion")
OUT=ROOT/"22x2_full_production_plus_research_inventory_diagnostic_20261114.json"
MAIN=Path("data/results_only_263/2026-11-10_completed_4617_scores_only.csv")
MAIN_PROV=Path("data/results_only_263/4617_research_input_provenance.json")
R45=ROOT/"4505_rights_provenance_and_pre_kickoff_asof_source_gate_20261114.json"
API= "https://huggingface.co/datasets/Damir81/football-charts-results-goal-timing/resolve/main/football_charts_matches.csv"
PINNED="08d1a0863d703550fe6e7fb1ef9faed4ea3cea95c664012373b1a1e1f159be10"
CUT="2026-11-13"
ANALYSIS=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1","SCO1","DNK1","CHE1")
TRAIN=("ENG3","ENG4","ENG5","GER2","ESP2","ITA2","FRA2","GRE1","AUT1")
NAMES={
"ENG1":"Premier League","ENG2":"Championship","GER1":"Bundesliga","ESP1":"La Liga",
"ITA1":"Serie A","FRA1":"Ligue 1","NED1":"Eredivisie","TUR1":"Süper Lig",
"POR1":"Primeira Liga","BEL1":"Pro League","SCO1":"Scottish Premiership",
"DNK1":"Danish Superliga","CHE1":"Swiss Super League","ENG3":"League One",
"ENG4":"League Two","ENG5":"National League","GER2":"2. Bundesliga",
"ESP2":"Segunda","ITA2":"Serie B","FRA2":"Ligue 2",
"GRE1":"Greek Super League","AUT1":"Austrian Bundesliga"}
# 2025/26 season regular basic expected, not including separately tagged
# playoffs, European qualifiers, awarded/abandoned scores. Scottish/Danish/
# Swiss/Austrian/Greek formats require stage-specific checks too.
NORMAL_EXPECTED={
"ENG1":380,"ENG2":552,"GER1":306,"ESP1":380,"ITA1":380,"FRA1":306,
"NED1":306,"TUR1":306,"POR1":306,"BEL1":240,
"SCO1":228,"DNK1":192,"CHE1":228,
"ENG3":552,"ENG4":552,"ENG5":551,"GER2":306,"ESP2":462,
"ITA2":380,"FRA2":305,"GRE1":236,"AUT1":192}
SOURCE="Football Charts CC BY 4.0 2025/26 original snapshot"
def readcsv(path):
 with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def gitsha(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()
def sea(x):
 y=str(x or "").strip().replace("_","-")
 if y in ("2025-2026","2025/26","2025-26"):return "2025-26"
 if y in ("2026-2027","2026/27","2026-27"):return "2026-27"
 return y
def get_date(row):
 return str(row.get("date") or row.get("match_date") or "").strip()[:10]
def source_report():
 report=json.loads(R45.read_text())
 if report["frozen_historical_source_only_fixture_identities"]!=4505 or len(report["source_files"])!=26:
  raise ValueError("FROZEN_4505_AUDIT_CHANGED")
 return report
def inventory():
 p=json.loads(MAIN_PROV.read_text())
 raw=MAIN.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=p["source_snapshot_sha256"]:
  raise ValueError("CORE_4617_SHA256_CHANGED")
 main=readcsv(MAIN)
 if len(main)!=4617 or p["usable_total_rows"]!=4617:
  raise ValueError("CORE_4617_COUNT_CHANGED")
 base=Counter();base_rows_by_cell=defaultdict(list);bad_main=Counter()
 main_unique=set();id_dupes=[]
 for r in main:
  lg=r.get("league","").strip();se=sea(r.get("season",""));dt=get_date(r)
  if lg not in ANALYSIS[:10]:
   bad_main["out_of_core_10_league"]+=1
  if se not in ("2025-26","2026-27"):
   bad_main["outside_2025_26_2026_27"]+=1
  if len(dt)!=10 or dt>CUT:
   bad_main["future_or_unparseable_date"]+=1
  idd=r.get("fixture_id") or ""
  if idd:
   if idd in main_unique:id_dupes.append(idd[:10])
   main_unique.add(idd)
  base[(lg,se)]+=1
  base_rows_by_cell[(lg,se)].append(r)
 audit=source_report()
 ref=Counter();sources=defaultdict(list);all_ids=set();dup_research=Counter()
 bad_research=Counter()
 for entry in audit["source_files"]:
  f=ROOT/entry["path"]
  raw=f.read_bytes()
  if gitsha(raw)!=entry["source_git_blob_sha"]:
   raise ValueError("RESEARCH_PIN_DRIFT "+entry["path"])
  rows=readcsv(f)
  if len(rows)!=entry["research_rows"]:raise ValueError("RESEARCH_ROW_COUNT_DRIFT "+entry["path"])
  per=Counter()
  for r in rows:
   lg=r.get("league","").strip();se=sea(r.get("season",""));dt=get_date(r)
   if lg not in ANALYSIS+TRAIN:bad_research["outside_22_leagues"]+=1
   if se not in ("2025-26","2026-27"):bad_research["outside_2_seasons"]+=1
   if len(dt)!=10 or dt>CUT:bad_research["future_or_invalid_date"]+=1
   h=(r.get("home") or r.get("source_home") or "").strip()
   a=(r.get("away") or r.get("source_away") or "").strip()
   k=(lg,se,dt,h,a)
   if k in all_ids:dup_research[(lg,se)]+=1
   all_ids.add(k)
   ref[(lg,se)]+=1;per[(lg,se)]+=1
  sources[entry["group"]].append({"path":entry["path"],"n":len(rows),"league_season":dict(sorted(("/".join(k),v) for k,v in per.items()))})
 if sum(ref.values())!=4505:raise ValueError("4505_TOTAL_COUNT_INVALID")
 rows=[]
 for lg in ANALYSIS+TRAIN:
  for se in ("2025-26","2026-27"):
   nmain=base[(lg,se)];nresearch=ref[(lg,se)]
   if lg in ANALYSIS[:10]:
    stat="PRODUCTION_BASELINE_ONLY" if nmain>0 else "PRODUCTION_BASELINE_NO_TARGET_SEASON_ROWS"
   else:
    stat="RESEARCH_SCORE_SOURCE_ROWS_PRESENT" if nresearch>0 else "RESEARCH_NO_PERSISTED_SCORE_RESULTS"
   note="2026/27 is ongoing; completeness means played matches <= 2026-11-13, NOT whole season" if se=="2026-27" else "2025/26 full regular season and stage expected, actual match IDs and quality gates required"
   rows.append({
    "league":lg,"name":NAMES[lg],
    "group":"analysis" if lg in ANALYSIS else "training_only",
    "season":se,
    "expected_2025_26_regular_scored_results_approx":NORMAL_EXPECTED[lg] if se=="2025-26" else None,
    "production_results_only_baseline_count":nmain,
    "research_source_specific_count":nresearch,
    "source_status":stat,
    "research_pinned_public_source_files":sum(1 for e in audit["source_files"] if e["path"] and any(
       (lg+"/"+se) in "/".join([lg,se]) for _ in [])) if False else None,
    "completeness_proven":False,
    "incomplete_or_uncertain_reason":note,
    "new_training_approved":0
   })
 sourcecounts=Counter((r["league"],r["season"]) for r in rows if r["research_source_specific_count"]>0)
 totals={"main_core_archive":len(main),"research_source_specific":sum(ref.values()),
          "core_current_seasons":sum(v for (l,s),v in base.items() if l in ANALYSIS[:10] and s in ("2025-26","2026-27")),
          "research_season_2025_26":sum(v for (l,s),v in ref.items() if s=="2025-26"),
          "research_season_2026_27":sum(v for (l,s),v in ref.items() if s=="2026-27"),
          "research_scoped_league_season_cells_nonzero":sum(1 for v in rows if v["research_source_specific_count"]>0),
          "production_scoped_league_season_cells_nonzero":sum(1 for v in rows if v["production_results_only_baseline_count"]>0)}
 return {
 "status":"READONLY_22_BY_2_INVENTORY_FROM_CORE_4617_AND_EXPANSION_4505",
 "run_scope":"One-time pure source coverage audit; no score result second-provider QA repeated",
 "cutoff_results_through_date":CUT,
 "two_seasons":["2025-26","2026-27"],
 "analysis_13":list(ANALYSIS),"training_only_9":list(TRAIN),
 "research_branch":"research/263-13-lig-22-havuz-20261113",
 "source_sha_protected":True,
 "main_provenance":p,
 "counts":totals,
 "non_target_main_season_or_league_counts":dict(bad_main),
 "non_target_main_league_season":{"/".join(k):v for k,v in base.items() if k[0] not in ANALYSIS[:10] or k[1] not in ("2025-26","2026-27")},
 "main_fixture_id_duplicate_count":len(id_dupes),
 "research_provenance_misaligned_counts":dict(bad_research),
 "raw_name_research_identity_overlap_warnings":{"/".join(k):v for k,v in dup_research.items()},
 "matches_before_2026_11_13_only":True,
 "do_not_add_4617_to_4505_without_scope_proven":True,
 "new_model_training_admissions":0,
 "data_gaps_or_incomplete_source_signoff":"A league-season is only VERIFIED complete once normal-season and playoff stage, independent score, source rights and temporal provenance all meet separate controls. Counts alone do not certify completeness.",
 "cells":rows,
 "new_2026_27_5_league_keyless_personal_api_count_not_persisted":{"ENG5":190,"ESP2":141,"ITA2":110,"FRA2":108,"DNK1":84},
 "spanish_2025_26_source_metadata_probe":None,
 "next_unresolved_work":"One original CC BY publisher 2025/26 Spain Segunda metadata scope & 2026/27 five rights-cleared original provider league data acquisition."
 }
def spanish_metadata():
 req=Request(API,headers={"User-Agent":"FutbolAnaliz263-historical-ESP2-one-unused-scope/1.0","Accept":"text/csv"})
 with urlopen(req,timeout=45) as f:
  raw=f.read(17_000_001)
 if len(raw)>17_000_000 or hashlib.sha256(raw).hexdigest()!=PINNED:
  raise ValueError("PUBLISHER_ORIGINAL_CC_BY_SHA_CHANGED")
 reader=csv.DictReader(raw.decode("utf-8-sig").splitlines())
 if not {"country","league_name","league","season"}.issubset(reader.fieldnames or []):
  raise ValueError("PUBLISHER_METADATA_SCHEMA_CHANGED")
 names=Counter()
 for r in reader:
  if r.get("season")!="2025-2026":continue
  if "spain" not in str(r.get("country","")).lower() and "esp" not in str(r.get("country","")).lower():continue
  key=(r.get("country",""),r.get("league_name",""),r.get("league",""))
  names[key]+=1
 # No raw match score or team fixtures leave memory to JSON/GitHub.
 return {"status":"ONE_PASS_PINNED_ORIGINAL_CC_BY_SPANISH_COMPETITION_LABEL_ONLY",
  "source_sha256":PINNED,"source_doi":"https://doi.org/10.5281/zenodo.22295583",
  "season":"2025-26","country_competition_row_counts":[
   {"country":a,"competition":b,"code":c,"row_count":v} for (a,b,c),v in names.most_common(30)],
  "raw_provider_FT_rows_saved":0}
def selftest():
 assert len(ANALYSIS)==13 and len(TRAIN)==9 and len(set(ANALYSIS+TRAIN))==22
 assert sea("2025-2026")=="2025-26"
 assert sea("2026-2027")=="2026-27"
 assert len(NORMAL_EXPECTED)==22
 print("PASS 13+9, 44 cells, date cutoff, source 4505 SHA pins, no training")
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("--self-test",action="store_true");ap.add_argument("--run",action="store_true");ap.add_argument("--probe-esp2",action="store_true")
 x=ap.parse_args()
 if x.self_test:selftest()
 if x.run:
  data=inventory()
  if x.probe_esp2:
   try:data["spanish_2025_26_source_metadata_probe"]=spanish_metadata()
   except Exception as e:data["spanish_2025_26_source_metadata_probe"]={"status":"FAIL_CLOSED","error_type":type(e).__name__}
  OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
  print(json.dumps({"status":data["status"],"counts":data["counts"],"main_outside":data["non_target_main_league_season"],"ESP2_source":data["spanish_2025_26_source_metadata_probe"]},ensure_ascii=False))
