#!/usr/bin/env python3
"""PRIVATE on-PC source-score candidate vault, 2026/27 through 2026-11-13.

No betting forecasts, no math, no model training, no public data-set rehost.
Uses Football Charts FREE personal API in at most NINE requests; never commits
raw provider rows, never runs automatically in GitHub Actions. It does not
declare candidates independently verified or grant model training rights.

Run from repo ROOT on *your own computer*:
 py experiments/263/league_expansion/build_751_PRIVATE_LOCAL_ONLY_score_vault_20261114.py --self-test
 py experiments/263/league_expansion/build_751_PRIVATE_LOCAL_ONLY_score_vault_20261114.py --build-private

Default output is %USERPROFILE%/Futbol-Analiz-Ozel-Veri/ outside Git.
"""
from __future__ import annotations
import argparse,hashlib,json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path

# Import only prior, source-frozen standard-library fixture identity gates.
from resolve_118_four_2026_27_identities_personal_metadata_only import (
 CUTOFF,API,SPECS,canonical_team,old,source_matches
)

PROJECT=Path(__file__).resolve().parents[3]
DEFAULT=Path.home()/"Futbol-Analiz-Ozel-Veri"
PRIVATE_NAME="2026-27_to_2026-11-13_source_scores_QUARANTINE_PRIVATE.jsonl"
MANIFEST="2026-27_to_2026-11-13_source_scores_QUARANTINE_PRIVATE_SUMMARY.json"
FIVE={"ENG5":("national",190),"ESP2":("spain2",141),
      "ITA2":("italy2",110),"FRA2":("france2",108),
      "DNK1":("denmark1",84)}
SOURCE_NAME="Football Charts"
SOURCE_TERMS="https://www.football-charts.com/terms"
SOURCE_CREDIT="Data by football-charts.com"
FROZEN_COUNTS={"SCO1":(42,75,33),"CHE1":(57,78,21),
               "GRE1":(35,69,34),"AUT1":(42,72,30)}
LEAGUES=tuple(FIVE)+tuple(FROZEN_COUNTS)

def is_under(path,root):
 try:path.relative_to(root);return True
 except ValueError:return False
def private_dir(root):
 path=Path(root).expanduser().resolve()
 if is_under(path,PROJECT) or path==PROJECT:
  raise ValueError("REFUSE_TO_WRITE_RAW_DATA_INSIDE_PUBLIC_GIT_CHECKOUT")
 if path==Path.cwd().resolve() or path==Path.cwd().resolve().parent:
  raise ValueError("REFUSE_CURRENT_DIRECTORY_OUTPUT")
 # Keep the private cache inside the user's home, never on cloud-mounted
 # repository paths by default; no --dest to reduce accidental sharing.
 if not is_under(path,Path.home().resolve()):
  raise ValueError("REFUSE_OUTPUT_OUTSIDE_USER_HOME")
 return path
def source_research_only_match(d,h,a,ft,code):
 if not d or d>CUTOFF or d<"2026-07-01":
  raise ValueError("EXCLUDED_DATE_OR_UNKNOWN_MATCH")
 if not h or not a or h==a or len(ft)!=2:
  raise ValueError("INVALID_MATCH")
 if any(type(n)!=int or not 0<=n<=25 for n in ft):
  raise ValueError("INVALID_FT")
 return {"league":code,"season":"2026-27","played_date":d,
  "home":str(h),"away":str(a),"ft_home":ft[0],"ft_away":ft[1],
  "source":SOURCE_NAME,"source_terms":SOURCE_TERMS,
  "identity_status":"SOURCE_ONLY_NOT_INDEPENDENTLY_VERIFIED",
  "score_eligibility":"PRIVATE_RESEARCH_QUARANTINE_ONLY",
  "training_eligibility":"NOT_APPROVED",
  "raw_publication_permitted":False}
def prepare_four(rows,loc,league,expected):
 src_count,existing_count=None,None
 oldmap={}
 for d,h,a,ft,_ in loc:
  k=(d,canonical_team(league,h),canonical_team(league,a))
  if k in oldmap:raise ValueError("OLD_CANONICAL_DUPLICATE")
  oldmap[k]=ft
 new=[];matched=0;seen=set()
 for d,h,a,ft in rows:
  k=(d,canonical_team(league,h),canonical_team(league,a))
  if k in seen:raise ValueError("PROVIDER_CANONICAL_DUPLICATE")
  seen.add(k)
  if k in oldmap:
   if oldmap[k]!=ft:raise ValueError("EXISTING_MATCH_FT_CONFLICT")
   matched+=1
  else:new.append(source_research_only_match(d,h,a,ft,league))
 n_existing,n_total,n_new=expected
 if (len(loc),len(rows),matched,len(new))!=(n_existing,n_total,n_existing,n_new):
  raise ValueError("OLD_OR_NEW_MATCH_COUNT_DRIFT:"+league)
 return new,matched
def prepare_five(rows,league,expected):
 if len(rows)!=expected:raise ValueError("FIVE_COUNT_DRIFT:"+league)
 out=[];seen=set()
 for d,h,a,ft in rows:
  k=(d,h.casefold(),a.casefold())
  if k in seen:raise ValueError("FIVE_DUPLICATE")
  seen.add(k)
  out.append(source_research_only_match(d,h,a,ft,league))
 return out

def render_private(records,stats):
 assert len(records)==751, "FAIL CLOSED: do not invent/recount new matches"
 counts={lg:sum(r["league"]==lg for r in records) for lg in LEAGUES}
 exp={lg:n for lg,(_,n) in FIVE.items()}
 exp.update({lg:ns[2] for lg,ns in FROZEN_COUNTS.items()})
 if counts!=exp:raise ValueError("PRIVATE_RECORD_COUNTS_CHANGED")
 jsonl="".join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n"
               for r in records)
 raw=jsonl.encode("utf-8")
 overview={
  "source_credit":SOURCE_CREDIT,"source_terms":SOURCE_TERMS,
  "cutoff":CUTOFF,"status":"PRIVATE_PERSONAL_RESEARCH_QUARANTINE_NO_MODEL_APPROVAL",
  "league_distribution":counts,"fixture_rows":len(records),
  "preexisting_four_league_176_preserved_not_duplicated":True,
  "source_requests_this_run":9,
  "data_file":PRIVATE_NAME,"file_sha256":hashlib.sha256(raw).hexdigest(),
  "independent_official_result_verification":"PENDING",
  "source_raw_data_publication":"FORBIDDEN",
  "model_training_approval":0,"math_or_M4_changed":False,
  "xg_1855_workbook_changed":False,
  "privacy":"Keep entire directory only on your own computer. Never upload JSONL or its substantial extract to public GitHub, chat, or shared cloud folder.",
  "source_grade":"ONE_PROVIDER_SCORE_LABELS_ONLY_NOT_CANONICAL_OFFICIAL_MATCH_PROOF",
  "created_at_utc":datetime.now(timezone.utc).isoformat(),
  "provider_run_diagnostics":stats,
 }
 return raw,(json.dumps(overview,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
def atomic_private_write(path,data):
 # Every write uses a temp file in the private destination; fail closed on
 # pre-existing output, no updates or unintentional extra network polls.
 fd,temporary=tempfile.mkstemp(prefix=".tmp-",dir=path)
 try:
  with os.fdopen(fd,"wb") as f:
   os.chmod(temporary,0o600)
   f.write(data)
   f.flush();os.fsync(f.fileno())
  dest=path/PRIVATE_NAME
  if dest.exists():raise FileExistsError("PRIVATE_VAULT_EXISTS_DO_NOT_OVERWRITE")
  os.replace(temporary,dest)
 except Exception:
  if os.path.exists(temporary):os.unlink(temporary)
  raise
def build(root):
 path=private_dir(root)
 if (path/PRIVATE_NAME).exists():
  print("UNCHANGED: private vault already exists; no network request or overwrite.")
  return
 # Do NOT make any API calls until SHA verification of old research rows
 # succeeds, then make one results request for each of exactly nine leagues.
 archive=old()
 results=[];stats={};hits=0
 for lg,(code,n) in FIVE.items():
  data,flags=source_matches(code)
  rows=prepare_five(data,lg,n)
  stats[lg]={"league":"2026-27","expected_source":n,"private_new":len(rows),
   "old_archived":0,"api_qa_flags":flags}
  results.extend(rows);hits+=1
 for lg,spec in SPECS.items():
  data,flags=source_matches(spec["code"])
  records,matched=prepare_four(data,archive[lg],lg,FROZEN_COUNTS[lg])
  stats[lg]={"league":"2026-27","expected_source":spec["source_expected"],
             "private_new":len(records),"old_archived_matched":matched,
             "api_qa_flags":flags}
  results.extend(records);hits+=1
 if hits!=9:raise ValueError("SOURCE_REQUEST_BUDGET_OVERFLOW")
 payload,metadata=render_private(results,stats)
 # Build entire result in memory; don't write partial file if counts drift.
 path.mkdir(parents=True,exist_ok=True)
 try:os.chmod(path,0o700)
 except OSError:pass
 atomic_private_write(path,payload)
 try:
  manifest_path=path/MANIFEST
  if manifest_path.exists():raise FileExistsError("MANIFEST_ALREADY_EXISTS")
  manifest_path.write_bytes(metadata)
  try:os.chmod(manifest_path,0o600)
  except OSError:pass
 except Exception:
  # Do not leave an apparently complete vault without its manifest.
  (path/PRIVATE_NAME).unlink(missing_ok=True)
  raise
 print("PASS 751 private-source fixture candidates (633 five + 118 four), 176 old unaffected.")
 print("PRIVATE DIRECTORY:",path)
 print("NO GitHub upload, no math, no new model training, xG untouched.")
def test():
 assert sum(n for _,n in FIVE.values())==633
 assert sum(v[2] for v in FROZEN_COUNTS.values())==118
 assert len(LEAGUES)==9 and len(set(LEAGUES))==9
 sample=[("2026-10-09","Basel","Thun",(1,0))]
 local=[("2026-10-09","FC Basel","FC Thun",(1,0),"cc0")]
 new,matched=prepare_four(sample,local,"CHE1",(1,1,0))
 assert not new and matched==1
 newer=[("2026-10-09","Basel","Thun",(1,1))]
 try:prepare_four(newer,local,"CHE1",(1,1,0));raise AssertionError("MISSING_FT_CONFLICT")
 except ValueError as exc:assert str(exc)=="EXISTING_MATCH_FT_CONFLICT"
 assert len(prepare_five([("2026-11-01","A","B",(0,0))],"DNK1",1))==1
 try:private_dir(PROJECT/"data");raise AssertionError("WRITES_INSIDE_REPO")
 except ValueError as exc:assert "REFUSE_TO_WRITE" in str(exc)
 assert all(source_research_only_match("2026-08-01","A","B",(0,0),"ENG5")[k] in ("NOT_APPROVED",False)
  for k in ("training_eligibility","raw_publication_permitted"))
 print("PASS offline 9 leagues / 751 source-only, frozen duplicate guard, private path and FT conflict fail-closed")
if __name__=="__main__":
 p=argparse.ArgumentParser(description=__doc__)
 choices=p.add_mutually_exclusive_group(required=True)
 choices.add_argument("--self-test",action="store_true",
  help="Offline self-test; never fetches or writes any match")
 choices.add_argument("--build-private",action="store_true",
  help="One-time on YOUR OWN COMPUTER, 9 API calls, private personal-use vault")
 args=p.parse_args()
 if args.self_test:test()
 if args.build_private:build(DEFAULT)
