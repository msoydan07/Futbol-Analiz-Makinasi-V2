#!/usr/bin/env python3
"""Reclaim only verified ERRONEOUS old ENG3/ENG4 2025/26 facts as nonadditive research pointers.

Reuses SHA-pinned 178 score discrepancies confirmed by a third compilation,
and 22 individually witnessed date corrections (no calls to outside sources).
Original 200 bad records stay quarantined; no new M4 rows, training, or FT rehost.
"""
import csv,json,hashlib
from collections import Counter
from pathlib import Path
from reconcile_3041_CC_BY_eight_history_vs_old_once import SOURCE,CCBY,first,alias_table
from audit_6_leagues_967_scores_one_batch_20261114 import match_name

ROOT=Path("experiments/263/league_expansion")
HOLD=ROOT/"eng3_eng4_2025_26_200_exact_legacy_fixture_training_HOLD_20261114.csv"
SCORE=ROOT/"eng3_eng4_2025_26_all_178_external_ft_conflicts_closed_20261114.json"
DATE=ROOT/"eng3_eng4_2526_22_misdated_and_472_distinct_fixture_resolution_20261114.json"
OUT=ROOT/"CORRECTED_200_ENG3_ENG4_SOURCE_POINTERS_NOT_ADDITIVE_20261114.csv"
MANIFEST=ROOT/"CORRECTED_200_ENG3_ENG4_RESEARCH_ONLY_NOT_TRAINING_20261114.json"

def csvrows(path):
 with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def sha(blob):
 return hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
def run():
 original,other_hold=first()
 holds=csvrows(HOLD)
 score=json.loads(SCORE.read_text())
 date=json.loads(DATE.read_text())
 assert score["conflict_total"]==178 and score["independent_full_season_csv_match_total"]==178
 witnesses=date["individual_date_shift_match_witnesses"]
 assert len(holds)==200 and len(witnesses)==22
 witness={(r["league"],r["legacy_date"],r["home"],r["away"]):r for r in witnesses}
 assert len(witness)==22
 expected=Counter({"ORIGINAL_FT_SCORE_INVALID_CONFIRMED_THIRD_SOURCE":178,
                   "LEGACY_MATCH_DATE_MISRECORDED__22_INDEPENDENT_DATE_FT_WITNESSES":22})
 assert Counter(r["quality_hold_reason"] for r in holds)==expected
 sources={}
 original_by={}
 for lg in ("ENG3","ENG4"):
  blob_expected,n=SOURCE[lg]
  p=CCBY/(lg.lower()+"_2025_26_CC_BY_SOURCE_QUARANTINE.csv")
  assert sha(p.read_bytes())==blob_expected
  prior=original[lg]
  canon=alias_table(lg,prior)
  original_by[lg]={(r["date"],r["home"],r["away"]):r for r in prior}
  assert len(original_by[lg])==len(prior)
  src={}
  for line,r in enumerate(csvrows(p),start=2):
   home=match_name(r["source_home"],canon)
   away=match_name(r["source_away"],canon)
   if not home or not away:raise ValueError("Unresolved team alias")
   key=(r["date"],home,away)
   # EFL league and playoff sometimes share a home-away pair but not a same-date key.
   if key in src:raise ValueError("source duplicate "+str(key))
   src[key]=(line,r)
  assert len(src)==n
  sources[lg]={"path":p,"blob":blob_expected,"rows":src}
 out=[];counts=Counter();selected_keys=set()
 for item in holds:
  lg=item["league"];dt=item["date"];home=item["home"];away=item["away"]
  assert lg in ("ENG3","ENG4")
  identity=(lg,dt,home,away)
  assert (lg,"2025-26",dt,home,away) in other_hold
  orig=original_by[lg].get((dt,home,away))
  assert orig is not None
  reason=item["quality_hold_reason"]
  if reason=="ORIGINAL_FT_SCORE_INVALID_CONFIRMED_THIRD_SOURCE":
   corrected_date=dt
   status="VERIFIED_THIRD_SOURCE_SCORE_REPLACEMENT"
   evidence="eng3_eng4_2025_26_all_178_external_ft_conflicts_closed_20261114.json"
  elif reason=="LEGACY_MATCH_DATE_MISRECORDED__22_INDEPENDENT_DATE_FT_WITNESSES":
   witness_row=witness.get(identity)
   assert witness_row is not None
   corrected_date=witness_row["verified_played_date"]
   status="VERIFIED_INDIVIDUAL_DATE_AND_RESULT_REPLACEMENT"
   evidence=witness_row["independent_match_result_reference"]
  else:raise ValueError("unknown reason "+reason)
  source=sources[lg]
  k=(corrected_date,home,away)
  if k not in source["rows"]:raise ValueError("corrected CCBY exact source match absent "+str((lg,*k)))
  line,r=source["rows"][k]
  oldscore=(orig["ft_home"],orig["ft_away"])
  newscore=(r["source_ft_home"],r["source_ft_away"])
  if status=="VERIFIED_THIRD_SOURCE_SCORE_REPLACEMENT" and oldscore==newscore:
   raise ValueError("held incorrect score same as corrected original "+str(identity))
  if status=="VERIFIED_INDIVIDUAL_DATE_AND_RESULT_REPLACEMENT":
   if newscore!=tuple(witness_row["verified_full_time_score"].split("-")):
    raise ValueError("corrected date score differs official witness "+str(identity))
   if dt==corrected_date:raise ValueError("date not actually corrected")
  if (lg,*k) in selected_keys:raise ValueError("two replacements target same fixture")
  selected_keys.add((lg,*k))
  original_keydigest=hashlib.sha256("\x1f".join((lg,"2025-26",dt,home,away)).encode()).hexdigest()
  corrected_keydigest=hashlib.sha256("\x1f".join((lg,"2025-26",corrected_date,home,away)).encode()).hexdigest()
  out.append({"league":lg,"season":"2025-26",
    "old_bad_fixture_key_sha256":original_keydigest,
    "verified_correct_fixture_key_sha256":corrected_keydigest,
    "old_bad_date":dt,"corrected_date":corrected_date,
    "source_path":str(source["path"]),"source_git_blob_sha":source["blob"],
    "source_row_1based":line,"decision":status,
    "independent_evidence":evidence,
    "model_training_status":"NOT_APPROVED_RIGHTS_ASOF_AND_SPLIT_REQUIRED",
    "additive_new_match": "NO__SOURCE_POINTER_CORRECTION_NOT_NEW_FIXTURE"})
  counts[status]+=1
 assert counts==Counter({"VERIFIED_THIRD_SOURCE_SCORE_REPLACEMENT":178,
                         "VERIFIED_INDIVIDUAL_DATE_AND_RESULT_REPLACEMENT":22}),counts
 assert len(out)==200 and len(selected_keys)==200
 fields=list(out[0])
 with OUT.open("w",encoding="utf-8",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(out)
 manifest={
 "status":"PASS_200_OLD_WRONG_ENG3_ENG4_REPLACED_BY_VERIFIED_CC_BY_ORIGINAL_SOURCE_REFERENCES_RESEARCH_ONLY",
 "original_200_BAD_CC0_HOLDS_STILL_EXCLUDED":True,
 "source_pointer_corrections":len(out),
 "source_scored_178_independently_witnessed":counts["VERIFIED_THIRD_SOURCE_SCORE_REPLACEMENT"],
 "source_date_and_ft_22_individually_witnessed":counts["VERIFIED_INDIVIDUAL_DATE_AND_RESULT_REPLACEMENT"],
 "counts_are_nonadditive_to_9460":True,
 "source_file_git_blobs":{lg:sources[lg]["blob"] for lg in ("ENG3","ENG4")},
 "source_rows_modified":0,
 "outside_provider_downloads":0,
 "new_training_approvals":0,
 "main_M4_modified":False,
 "prior_96_ENG5_HOLD_still_excluded":True,
 "note":"Original 200 wrong source scores/dates remain excluded. Corrected original-author CC BY source pointers are available for score fact QA only, not model training. The 22 date-corrected matches may already occur among the 4218 source score candidates: never add them again blindly; 178 are correction overlays, not novel fixtures. New closed evidence did not require old external FT tests to be rerun.",
 "output_file":str(OUT)
 }
 MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({k:manifest[k] for k in ("status","source_pointer_corrections","source_scored_178_independently_witnessed","source_date_and_ft_22_individually_witnessed","new_training_approvals")},ensure_ascii=False))
def selftest():
 s=json.loads(SCORE.read_text());d=json.loads(DATE.read_text())
 assert s["conflict_total"]==178 and len(d["individual_date_shift_match_witnesses"])==22
 assert len(csvrows(HOLD))==200
 print("PASS pinned 178 previously verified score facts and 22 independent date corrections")
if __name__=="__main__":
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true")
 a=p.parse_args()
 if a.self_test:selftest()
 if a.run:run()
