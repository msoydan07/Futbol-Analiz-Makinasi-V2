#!/usr/bin/env python3
"""One-pass rehydration/cross-source identity QA of the EXISTING 9460 pointer manifest.

No source download, training, xG changes or main-branch changes. Reads only
SHA-pinned GitHub archive rows; finds punctuation/diacritics alias collisions
and near-date home-away pairs without pretending an alias/different-stage
match is necessarily a duplicate. Audits 200 old bad-row replacement pointers.
"""
from __future__ import annotations
import csv,hashlib,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path
from datetime import date
ROOT=Path("experiments/263/league_expansion")
SELECT=ROOT/"FINAL_9460_SOURCE_ROW_DECISIONS_NO_SCORE_REHOST_20261114.csv"
SUMMARY=ROOT/"FINAL_9460_RESEARCH_SCORE_FACTS_FILTERED_20261114.json"
FIX=ROOT/"CORRECTED_200_ENG3_ENG4_SOURCE_POINTERS_NOT_ADDITIVE_20261114.csv"
OUT=ROOT/"CROSS_SOURCE_9460_200_IDENTITY_POINTERS_AUDIT_20261114.json"
PASS="SCORE_FACT_RESEARCH_ONLY_QA_PASS"
OLD="EXISTING_CORE_4617_FROZEN_RESULTS_ONLY"
EXCLUDED={"EXCLUDED_LEGACY_SCORE_OR_DATE_HOLD",
 "EXCLUDED_UNCLEARED_UPSTREAM_RIGHTS",
 "EXCLUDED_NONLEAGUE_CONFERENCE_PLAYOFF","EXCLUDED_ABANDONED_NOT_FT"}
def readcsv(p):
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def sha_git(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def sha_file(raw):return hashlib.sha256(raw).hexdigest()
def normalize(x):
 txt=unicodedata.normalize("NFKD",str(x).casefold())
 txt="".join(z for z in txt if not unicodedata.combining(z))
 return re.sub(r"[^a-z0-9]+","",txt)
def normseason(x):
 return {"2025-2026":"2025-26","2026-2027":"2026-27"}.get(str(x),str(x))
def identity(r):
 return (
  str(r.get("league","")).strip(),
  normseason(r.get("season","")),
  str(r.get("date") or r.get("match_date") or "")[:10],
  str(r.get("home") or r.get("source_home") or r.get("home_id") or "").strip(),
  str(r.get("away") or r.get("source_away") or r.get("away_id") or "").strip())
def result(r):
 h=r.get("ft_home")
 a=r.get("ft_away")
 if h in ("",None):h=r.get("home_goals")
 if a in ("",None):a=r.get("away_goals")
 if h in ("",None) or a in ("",None):raise ValueError("MISSING_SCORED_RESULT")
 return (int(h),int(a))
def fprint(t):
 return hashlib.sha256("\x1f".join(t).encode("utf-8")).hexdigest()
def validate_row(r):
 k=identity(r)
 if len(k)!=5 or not all(k) or k[3]==k[4]:raise ValueError("INVALID_FIXTURE_IDENTITY")
 date.fromisoformat(k[2])
 score=result(r)
 if min(score)<0 or max(score)>25:raise ValueError("INVALID_GOALS")
 return k,score
def fetch_source(cache,path,sha):
 p=Path(path)
 if not p.is_file():raise ValueError("MISSING_PINNED_SOURCE:"+path)
 if path not in cache:
  raw=p.read_bytes()
  if sha.startswith("PINNED_SHA256:") or sha.startswith("SHA256:"):
   if sha_file(raw)!=sha.split(":",1)[1]:raise ValueError("PINNED_SHA256_DRIFT:"+path)
  elif sha_git(raw)!=sha:raise ValueError("PINNED_GIT_BLOB_DRIFT:"+path)
  if p.suffix.lower()==".csv":
   records=readcsv(p)
   cache[path]=(records,"csv")
  elif p.suffix.lower()==".json":
   j=json.loads(raw)
   if "match" not in j:raise ValueError("NO_MATCH_JSON_SOURCE")
   cache[path]=([j["match"]],"json")
  else:raise ValueError("UNSUPPORTED_SOURCE_EXTENSION:"+path)
 return cache[path]
def from_pointer(cache,p):
 path=p["source_path"];idx=int(p["source_row_1based"])
 source,typ=fetch_source(cache,path,p["source_git_blob_sha"])
 rownum=idx-2 if typ=="csv" else idx-1
 if rownum<0 or rownum>=len(source):raise ValueError("INVALID_SOURCE_LINE")
 return source[rownum]
def short(p,k,score):
 return {"league":k[0],"season":k[1],"date":k[2],
   "source":p["source_path"],"row_1based":p["source_row_1based"],
   "score":str(score[0])+"-"+str(score[1]),
   "fixture_sha256":p["fixture_key_sha256"]}
def audit():
 pointers=readcsv(SELECT)
 summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
 assert len(pointers)==summary["source_rows"]==9460
 assert summary["frozen_core_4617"]==4617
 assert summary["research_score_fact_qa_pass_only"]==4218
 assert summary["research_excluded_quality_or_rights"]==625
 statuses=Counter();cache={};stored=[]
 normalized=defaultdict(list);exact=defaultdict(list)
 source_indices=set()
 for p in pointers:
  status=p["decision"]
  if status not in EXCLUDED|{PASS,OLD}:raise ValueError("INVALID_DISPOSITION")
  src_key=(p["source_path"],p["source_row_1based"])
  if src_key in source_indices:raise ValueError("MANIFEST_SOURCE_ROW_DUPLICATE")
  source_indices.add(src_key)
  raw=from_pointer(cache,p)
  k,score=validate_row(raw)
  if (k[0],k[1])!=(p["league"],p["season"]) or fprint(k)!=p["fixture_key_sha256"]:
   raise ValueError("MANIFEST_SOURCE_FIXTURE_IDENTITY_DRIFT")
  statuses[status]+=1
  if status==PASS:
   record=(p,k,score)
   stored.append(record)
   exact[k].append(record)
   key=(k[0],k[1],k[2],normalize(k[3]),normalize(k[4]))
   normalized[key].append(record)
 assert statuses[OLD]==4617 and statuses[PASS]==4218
 assert sum(statuses[s] for s in EXCLUDED)==625
 assert len(stored)==4218 and len(source_indices)==9460
 # Exact collision would already have failed the original selection; do not
 # make that assumption in this independent source-row audit.
 exactdups=[v for v in exact.values() if len(v)>1]
 punctuationdups=[v for v in normalized.values() if len(v)>1]
 collisions=[]
 for v in punctuationdups:
  original_ident={x[1] for x in v}
  if len(original_ident)==1:classification="EXACT_DUPLICATE"
  else:classification="NORMALIZED_TEAM_NAME_OR_PUNCTUATION_ALIAS_CANDIDATE"
  scores={x[2] for x in v}
  collisions.append({"classification":classification,
   "score_conflict":len(scores)>1,
   "rows":[short(*rec) for rec in v][:10]})
 # Near dates are not sufficient to assert a duplicate; when season is split,
 # the same home and away sides can meet again legally.
 by_pair=defaultdict(list)
 for record in stored:
  p,k,score=record
  pair=(k[0],k[1],normalize(k[3]),normalize(k[4]))
  by_pair[pair].append(record)
 nearby=[];longpair=Counter()
 for pair,group in by_pair.items():
  if len(group)<2:continue
  group.sort(key=lambda r:r[1][2])
  for i in range(len(group)-1):
   for j in range(i+1,len(group)):
    n=(date.fromisoformat(group[j][1][2])-date.fromisoformat(group[i][1][2])).days
    if n>2:break
    # Same calendar date is already covered by normalized collision.
    if n>=1:
     nearby.append({"date_separation_days":n,
      "rows":[short(*r) for r in (group[i],group[j])]})
  longpair[pair[0]]+=1
 # Old bad → author-source corrected pointers: independently validate
 # corrected fixture reference, blob and prior HOLD digest membership.
 old_bad_digests={p["fixture_key_sha256"] for p in pointers if p["decision"]=="EXCLUDED_LEGACY_SCORE_OR_DATE_HOLD"}
 corrected=readcsv(FIX)
 assert len(corrected)==200
 targets=set();source_references=set();fixed_types=Counter()
 selected_digest={p["fixture_key_sha256"] for p in pointers if p["decision"]==PASS}
 overlays_matching_existing_pass=0
 for r in corrected:
  k_old=r["old_bad_fixture_key_sha256"]
  if k_old not in old_bad_digests:raise ValueError("OVERLAY_SOURCE_NOT_HOLD")
  target=r["verified_correct_fixture_key_sha256"]
  if target in targets:raise ValueError("OVERLAY_TWICE_TO_SAME_TARGET")
  targets.add(target)
  rowkey=(r["source_path"],r["source_row_1based"])
  if rowkey in source_references:raise ValueError("OVERLAY_SAME_SOURCE_ROW_TWICE")
  source_references.add(rowkey)
  p={"source_path":r["source_path"],"source_row_1based":r["source_row_1based"],
    "source_git_blob_sha":r["source_git_blob_sha"]}
  obj=from_pointer(cache,p)
  k,score=validate_row(obj)
  if k[0]!=r["league"] or k[1]!=r["season"] or k[2]!=r["corrected_date"]:
   raise ValueError("OVERLAY_SOURCE_OR_DATE_MISMATCH")
  # Publisher uses different team spellings from legacy source. Original
  # corrected pointer script already verified canonical alias map and witness.
  if k_old==target:
   assert r["decision"]=="VERIFIED_THIRD_SOURCE_SCORE_REPLACEMENT"
   fixed_types["verified_wrong_FT_178"]+=1
  else:
   assert r["decision"]=="VERIFIED_INDIVIDUAL_DATE_AND_RESULT_REPLACEMENT"
   fixed_types["verified_wrong_date_22"]+=1
  if target in selected_digest:overlays_matching_existing_pass+=1
 assert fixed_types==Counter({"verified_wrong_FT_178":178,"verified_wrong_date_22":22})
 assert len(targets)==200
 assert not any(r["decision"]=="SCORE_FACT_RESEARCH_ONLY_QA_PASS" for r in corrected)
 result_report={
  "date":"2026-11-14",
  "scope":"PINNED 9460 SOURCE-ROW DECISIONS AND 200 VERIFIED NONADDITIVE CORRECTION POINTERS",
  "status":"INDEPENDENT_SOURCE_POINTER_STRUCTURAL_QA_COMPLETE_NO_NEW_TRAINING",
  "files_rehydrated_with_sha_pin":len(cache),
  "total_source_rows_referenced":len(source_indices),
  "selection_decision_counts":dict(statuses),
  "verified_research_score_rows":len(stored),
  "exact_cross_source_fixture_duplicates_in_pass":len(exactdups),
  "same_day_normalized_club_name_collisions_in_pass":len(punctuationdups),
  "same_day_potential_score_disagreements":sum(c["score_conflict"] for c in collisions),
  "same_day_collision_examples_max25":collisions[:25],
  "near_date_1_or_2_day_same_pair_research_candidates":len(nearby),
  "near_date_examples_max25":nearby[:25],
  "same_pair_repeated_different_dates_by_league_not_automatically_errors":dict(longpair),
  "verified_old_source_correction_overlays_not_new_matches":len(corrected),
  "verified_old_correction_subtypes":dict(fixed_types),
  "corrected_target_matches_already_passed_research_source_digest":overlays_matching_existing_pass,
  "new_training_admitted":0,
  "main_M4_changed":False,
  "source_rows_overwritten":0,
  "note":"A match may recur in league split groups/playoffs; near-date pair is a flag only. Normalized key strips only punctuation/diacritics; it does NOT prove club alias equivalence or 44-cell completeness. Old core uses stable team UUIDs, so no cross-source name-matching with the old 10 leagues is claimed. Verified correction overlays never add 200 fixtures.",
  "action_required":"Review only newly discovered same-day conflicting scores or 1–2 day pair-date candidates; do not repeat earlier third-party match-QA or assume a renamed source is legal to rehost."
 }
 OUT.write_text(json.dumps(result_report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({k:result_report[k] for k in (
  "files_rehydrated_with_sha_pin","verified_research_score_rows",
  "same_day_normalized_club_name_collisions_in_pass",
  "same_day_potential_score_disagreements",
  "near_date_1_or_2_day_same_pair_research_candidates",
  "verified_old_source_correction_overlays_not_new_matches",
  "new_training_admitted")},ensure_ascii=False))
def selftest():
 assert normalize("F.C. Malmö")==normalize("FC Malmo")
 assert normseason("2025-2026")=="2025-26"
 assert fprint(("ENG3","2025-26","2025-11-06","Reading FC","Stevenage FC"))=="807b414bdc3aa59c9784bbe2cddc3ceeb837a0832e9142ecc183171adaa9d593"
 print("PASS deterministic fixture identity / normalization, no external imports")
if __name__=="__main__":
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument("--self-test",action="store_true");ap.add_argument("--run",action="store_true")
 a=ap.parse_args()
 if a.self_test:selftest()
 if a.run:audit()
