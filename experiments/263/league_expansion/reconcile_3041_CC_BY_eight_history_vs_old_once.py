#!/usr/bin/env python3
"""OFFLINE-only and ONE PASS identity comparison of 3,041 newly archived
Football Charts CC BY 2025/26 source result records against the original
2,396 research quarantine. Does not re-fetch original Football Charts file,
does not rerun old 871+904 fact checks, 296 source holds, or previous 259
Denmark/Swiss licensed archival PASS.
No automatic training, no M4, no source overwrite, no fixture predictions.
"""
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
import csv,json,hashlib
import audit_6_leagues_967_scores_one_batch_20261114 as names
from prepare_2396_provenance_rights_quality_gate_20261114 import EXPECTED,HOLD,read_csv,match_key
ROOT=Path("experiments/263/league_expansion")
CCBY=ROOT/"ccby_footballcharts_9_other_2025_26_source_ledger"
OUT=CCBY/"8_leagues_3041_new_source_canonical_vs_old_CC0_one_batch_20261114.json"
SOURCE={
 "ENG3":("d1d481c5ef5e73f4594f9d948bfe846796645c4e",557),
 "ENG4":("512f2a7e402b10ecd25336c9058a038320f962bd",556),
 "ENG5":("01aa70a635b67e91368f706d35ec7999362bcb79",554),
 "ITA2":("995d80a9faec5854252ca8eadb6563a230202652",390),
 "FRA2":("1b7fe8ad9dd8ece9da585bdc8717e91dcb9075ca",309),
 "GRE1":("81e6cf0f8d593fbc703f453e04dc96b22df0cb7f",246),
 "SCO1":("a11d301351f1350a156defa7d973da836c0a9444",234),
 "AUT1":("6a7eddd6210d0aab4a967a67af7ca0f88856f9fe",195)
}
# Explicit equivalences from club rosters, not fuzzy inexact score inference.
# All destinations must exist in the previous source league-season roster.
CUSTOM={
 "ENG3":{"Plymouth":"Plymouth Argyle"},
 "ENG4":{"Notts Co":"Notts County","Cambridge Utd":"Cambridge United",
         "MK Dons":"Milton Keynes Dons","Crewe":"Crewe Alexandra"},
 "ENG5":{"Boston Utd":"Boston United"},
 "ITA2":{
  "Avellino":"US Avellino","Bari":"SSC Bari","Carrarese":"Carrarese Calcio",
  "Catanzaro":"US Catanzaro","Cesena":"Cesena FC","Empoli":"Empoli FC",
  "Entella":"Virtus Entella","Frosinone":"Frosinone Calcio",
  "Mantova":"Mantova 1911 SSD","Modena":"Modena FC","Monza":"AC Monza",
  "Padova":"Calcio Padova","Palermo":"Palermo FC","Pescara":"Delfino Pescara",
  "Reggiana":"AC Reggiana 1919","Spezia":"Spezia Calcio",
  "Sudtirol":"FC Südtirol","Venezia":"Venezia FC"},
 "FRA2":{
  "Amiens":"Amiens SC","Annecy":"FC Annecy","Bastia":"SC Bastia",
  "Boulogne":"US Boulogne","Clermont":"Clermont Foot 63",
  "Dunkerque":"USL Dunkerque","Grenoble":"Grenoble Foot 38",
  "Guingamp":"EA Guingamp","Laval":"Stade Lavallois",
  "Le Mans":"Le Mans FC","Montpellier":"Montpellier HSC",
  "Nancy":"AS Nancy Lorraine","Red Star":"Red Star FC",
  "Reims":"Stade de Reims","Rodez":"Rodez AF",
  "St Etienne":"AS Saint-Étienne","Troyes":"ESTAC Troyes"},
 "GRE1":{
  "AEK Athens":"AEK Athen","AEK Athens FC":"AEK Athen",
  "AEL Larissa":"AE Lárissa","Aris":"Aris Saloniki",
  "Kifisia":"AE Kifisias","OFI Crete":"OFI Heraklion",
  "Olympiacos Piraeus":"Olympiakos Piraeus",
  "PAOK":"PAOK Saloniki","Volos":"Volos NFC"},
 "SCO1":{
  "Aberdeen":"Aberdeen FC","Celtic":"Celtic FC",
  "Dundee Utd":"Dundee United","Falkirk":"Falkirk FC",
  "Hearts":"Heart of Midlothian","Hibernian":"Hibernian FC",
  "Kilmarnock":"Kilmarnock FC","Livingston":"Livingston FC",
  "Motherwell":"Motherwell FC","Rangers":"Rangers FC",
  "St. Mirren":"St. Mirren FC"},
 "AUT1":{
  "Altach":"SCR Altach","Austria Vienna":"Austria Wien",
  "BW Linz":"FC Blau Weiß Linz","Hartberg":"TSV Hartberg",
  "Ried":"SV Ried","SK Rapid":"Rapid Wien",
  "Salzburg":"RB Salzburg","Tirol":"WSG Tirol"}
}
OUTSIDE_KNOWN={
 "SCO1":{"Arbroath","Dunfermline","Partick Thistle"},
 "FRA2":{"Rouen"}
}
def git_blob(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def first():
 original=defaultdict(list);hits=0
 for filename,(expected,n,tag) in EXPECTED.items():
  if tag!="PUBLISHER_CC0_CLAIM":continue
  rows,sha=read_csv(filename)
  if sha!=expected or len(rows)!=n:raise ValueError("OLDER_PIN_CHANGED_"+filename)
  for r in rows:
   if r["season"]=="2025-26" and r["league"] in SOURCE:
    original[r["league"]].append(r);hits+=1
 assert hits>1600
 prior,oldhold_sha=read_csv(HOLD)
 if len(prior)!=200:raise ValueError("OLDER_200_HOLD_CHANGED")
 held={match_key(r) for r in prior}
 special,sha=read_csv("eng5_2025_26_96_exact_original_FT_conflict_training_HOLD_20261114.csv")
 if len(special)!=96:raise ValueError("OLDER_96_HOLD_CHANGED")
 held.update((r["league"],r["season"],r["original_date"],r["home"],r["away"]) for r in special)
 if len(held)!=296:raise ValueError("OLD_HOLDS_NOT_EXACTLY_296")
 return original,held
def alias_table(league,old_rows):
 clubs={name for r in old_rows for name in (r["home"],r["away"])}
 aliases=names.exact_name_maps(league,clubs)
 for source_name,target in CUSTOM.get(league,{}).items():
  if target not in clubs:raise ValueError("UNVERIFIED_CANONICAL_TARGET:"+league+":"+target)
  k=names.norm(source_name)
  if k in aliases and aliases[k]!=target:raise ValueError("CANONICAL_ALIAS_COLLISION:"+league+":"+source_name)
  aliases[k]=target
 return aliases
def run():
 original,held=first();grand=Counter();result={}
 for lg,(expected_sha,n) in SOURCE.items():
  path=CCBY/(lg.lower()+"_2025_26_CC_BY_SOURCE_QUARANTINE.csv")
  data=path.read_bytes()
  if git_blob(data)!=expected_sha:raise ValueError("NEW_CCBY_SOURCE_DRIFT_"+lg)
  source=list(csv.DictReader(data.decode("utf-8-sig").splitlines()))
  if len(source)!=n:raise ValueError("SOURCE_COUNT_DRIFT_"+lg)
  prior=original[lg]
  alias=alias_table(lg,prior)
  by_key={}
  by_pair=defaultdict(list)
  for r in prior:
   k=(r["date"],r["home"],r["away"])
   if k in by_key:raise ValueError("OLD_SOURCE_KEY_DUPLICATE_"+lg)
   by_key[k]=r;by_pair[(r["home"],r["away"])].append(r["date"])
  counters=Counter();flags=Counter();unknown=Counter();conflicts=[];near=[];out=[]
  mapped_keys=set()
  for r in source:
   if r["league"]!=lg or r["season"]!="2025-26" or r["source_license"]!="CC-BY-4.0":
    raise ValueError("NEW_SOURCE_SCOPE_INVALID_"+lg)
   d=r["date"];h=names.match_name(r["source_home"],alias)
   a=names.match_name(r["source_away"],alias)
   if not h or not a or h==a:
    unknown.update((x for x,y in [(r["source_home"],h),(r["source_away"],a)] if not y))
    if r["source_home"] in OUTSIDE_KNOWN.get(lg,set()) or r["source_away"] in OUTSIDE_KNOWN.get(lg,set()):
     counters["OUTSIDE_PREVIOUS_LEAGUE_ROSTER_OR_PLAYOFF_UNRESOLVED"]+=1
    else:counters["UNRESOLVED_TEAM_IDENTITY_HOLD"]+=1
    continue
   key=(d,h,a)
   if key in mapped_keys:
    counters["SOURCE_CANONICAL_DUPLICATE_HOLD"]+=1;continue
   mapped_keys.add(key)
   old=by_key.get(key)
   if old:
    old_score=(old["ft_home"],old["ft_away"])
    new_score=(r["source_ft_home"],r["source_ft_away"])
    if old_score==new_score:
     counters["OLD_IDENTITY_AND_FT_MATCH"]+=1
     if (lg,"2025-26",*key) in held:counters["EXACT_MATCH_BUT_OLDER_EXPLICIT_HOLD_STILL_KEPT"]+=1
    else:
     counters["OLD_IDENTITY_BUT_FT_CONFLICT_HOLD"]+=1
     hstat=("ALREADY_OLD_296_EXPLICIT_HOLD" if (lg,"2025-26",*key) in held else "NEWLY_NOTICED_SOURCE_CONFLICT_HOLD")
     flags[hstat]+=1
     if len(conflicts)<6:conflicts.append({"date":d,"home":h,"away":a,"old_score":"-".join(old_score),"CCBY_source_score":"-".join(new_score),"status":hstat})
   else:
    pd=date.fromisoformat(d)
    near_dates=[ds for ds in by_pair[(h,a)] if abs((date.fromisoformat(ds)-pd).days)<=2]
    if near_dates:
     counters["DATE_NEAR_SAME_HOME_AWAY_SOURCE_CONFLICT_HOLD"]+=1
     if len(near)<4:near.append({"source_date":d,"older_date":near_dates[:2],"home":h,"away":a})
    else:
     counters["NOVEL_SOURCE_IDENTITIES_STAGE_AND_SCORE_QA_PENDING"]+=1
  if sum(v for k,v in counters.items() if k not in ("EXACT_MATCH_BUT_OLDER_EXPLICIT_HOLD_STILL_KEPT",))!=n:
   raise ValueError("COUNTS_NOT_DISJOINT_"+lg)
  detail={
   "older_2025_26_pinned_research_source_rows":len(prior),
   "new_CCBY_original_author_source_rows":n,
   "new_CCBY_git_blob_sha":expected_sha,
   "canonical_aliases_explicit_this_pass":CUSTOM.get(lg,{}),
   "counts":dict(counters),
   "older_existing_key_FT_disputes_status":dict(flags),
   "still_unmapped_source_name_count":dict(unknown),
   "outside_previous_roster_team_names":sorted(OUTSIDE_KNOWN.get(lg,set())),
   "discrepancy_examples_only":conflicts,"date_shift_examples_only":near,
   "new_unique_research_count_PROMOTED":0,
   "stage_or_playoff_ready_for_training":False,
   "source_FT_validated_independently_FOR_THE_NEW_IDENTITY_ROWS":False
  }
  result[lg]=detail
  for k,v in counters.items():grand[k]+=v
 if sum(v["new_CCBY_original_author_source_rows"] for v in result.values())!=3041:
  raise ValueError("3041_SOURCE_COUNT_CHANGED")
 overall={k:v for k,v in grand.items()}
 # Auxiliary match-count term is not part of disjoint total.
 if sum(v for k,v in grand.items() if k!="EXACT_MATCH_BUT_OLDER_EXPLICIT_HOLD_STILL_KEPT")!=3041:
  raise ValueError("GRAND_TOTAL_NOT_3041")
 return {
  "status":"EIGHT_NEW_2025_26_CC_BY_SOURCE_FILES_3041_OFFLINE_CANONICAL_DEDUP_QA_COMPLETE_RESEARCH_ONLY",
  "checked_on_utc":datetime.now(timezone.utc).isoformat(),
  "source_license":"CC BY 4.0 Football Charts open source 2026.10",
  "source_integrity_sha256":"08d1a0863d703550fe6e7fb1ef9faed4ea3cea95c664012373b1a1e1f159be10",
  "only_previously_archived_local_source_files_read":True,
  "new_network_or_remote_FT_source_requests":0,
  "older_source_2396_CSVs_changed":False,
  "older_200_plus_96_holds_kept":True,
  "older_871_plus_904_crosschecks_retested":0,
  "previous_Denmark_Swiss_259_source_qa_repeated":False,
  "source_only_3041_rows_examined":3041,
  "source_identity_classification_counts":overall,
  "source_groups":result,
  "old_distinct_research_fixture_count_unchanged":3122,
  "novel_candidates_NOT_ADDED_TO_COUNT_UNTIL_STAGES_AND_SOURCE_QA":overall.get("NOVEL_SOURCE_IDENTITIES_STAGE_AND_SCORE_QA_PENDING",0),
  "training_rows_newly_approved":0,
  "model_M4_SHA_and_user_xG_touched":False,
  "next":"Resolve only previously unmapped club identity and exact held source-score/date conflicts with NEW permitted corroboration; determine playoff/regular stage, then identify truly novel 2025/26 league fixtures. Never rerun completed 3041 source scope or old 871+904 QA."
 }
if __name__=="__main__":
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true");a=p.parse_args()
 if a.self_test:
  old,h=first()
  assert len(h)==296 and len(SOURCE)==8
  for lg in SOURCE:alias_table(lg,old[lg])
  print("PASS immutable prior CC0 source PINs, 296 old hold identities and 8 explicit alias maps")
 if a.run:
  d=run()
  OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  print("OFFLINE_EIGHT_3041_START")
  print(json.dumps(d,ensure_ascii=False,indent=2))
  print("OFFLINE_EIGHT_3041_END")
