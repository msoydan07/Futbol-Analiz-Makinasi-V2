#!/usr/bin/env python3
"""Personal research-only volatile 2026/27 match identity comparison for FOUR leagues.

Only four previously count-discrepant 2026/27 groups (SCO1, CHE1, GRE1, AUT1).
Reads existing SHA-pinned CC0 and evidence-only research archives; makes at
most 4 source requests and keeps raw fixture/score replies IN RAM. Publishes
ONLY derived aggregate counts (permitted under the provider's published terms).
No provider score/name bulk rehost; no prediction, training, M4, or xG changes.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re,unicodedata
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
from urllib.request import Request,urlopen
from audit_6_leagues_967_scores_one_batch_20261114 import exact_name_maps,match_name

ROOT=Path("experiments/263/league_expansion")
OUT=ROOT/"2026_27_FOUR_118_SCOPED_CROSS_SOURCE_FIXTURE_IDENTITY_METADATA_20261114.json"
PREVIOUS=ROOT/"2026_27_17_persisted_leagues_one_freshness_aggregates_only_20261114.json"
PINS=ROOT/"4505_rights_provenance_and_pre_kickoff_asof_source_gate_20261114.json"
SOURCE=ROOT/"cc0_new_485_2526_2627_QUARANTINE_20261113.csv"
AUS=ROOT/"cc0_aut1_2026_27_42_QUARANTINE_20261113.csv"
SWISS3=ROOT/"che1_2026_27_oct10_3_match_score_facts_QUARANTINE_20261114.csv"
API="https://footballcharts-backend.onrender.com/api/v1"
CUTOFF="2026-11-13"
SPECS={
 "SCO1":{"code":"scot-premier","local_expected":42,"source_expected":75},
 "CHE1":{"code":"swiss1","local_expected":57,"source_expected":78},
 "GRE1":{"code":"greece1","local_expected":35,"source_expected":69},
 "AUT1":{"code":"austria1","local_expected":42,"source_expected":72}
}
def csvrows(path):
 with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def blobsha(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
def strict_norm(s):
 s="".join(c for c in unicodedata.normalize("NFKD",str(s).casefold()) if not unicodedata.combining(c))
 return re.sub(r"[^a-z0-9]+","",s)
def reduced_norm(s):
 # Heuristic ONLY, never silent source-ID certification.
 s="".join(c for c in unicodedata.normalize("NFKD",str(s).casefold()) if not unicodedata.combining(c))
 tokens=re.findall(r"[a-z0-9]+",s)
 trims={"fc","cf","afc","sc","ac","sk","sv","fk","tsv"}
 while len(tokens)>1 and tokens[0] in trims:tokens=tokens[1:]
 while len(tokens)>1 and tokens[-1] in trims:tokens=tokens[:-1]
 return "".join(tokens)
def parse_score(r):
 text=str(r.get("score") or "").replace("–","-").replace("—","-").strip()
 m=re.fullmatch(r"(\d{1,2})\s*[-:]\s*(\d{1,2})",text)
 return (int(m.group(1)),int(m.group(2))) if m else None
def old_score(r):return (int(r["ft_home"]),int(r["ft_away"]))
def get(url):
 req=Request(url,headers={"Accept":"application/json",
  "User-Agent":"FutbolAnalizMakinasiPersonalResearch/1.0 (derived stats only)"})
 with urlopen(req,timeout=28) as resp:raw=resp.read(4_000_001)
 if len(raw)>4_000_000:raise ValueError("RESPONSE_TOO_LARGE")
 return json.loads(raw)
def rows_of(j):
 if isinstance(j,list):return j
 if isinstance(j,dict):
  for key in ("results","matches","data","items"):
   if isinstance(j.get(key),list):return j[key]
 raise ValueError("UNKNOWN_API_RESULTS_SCHEMA")
def pincheck():
 review=json.loads(PINS.read_text())
 by_name={x["path"]:x for x in review["source_files"]}
 for p in (SOURCE,AUS):
  k=p.relative_to(ROOT).as_posix()
  expected=by_name[k]["source_git_blob_sha"]
  if blobsha(p.read_bytes())!=expected:raise ValueError("SOURCE_SHA_CHANGED:"+str(p))
 # swiss3 not part of original 4505: its exact 3 rows were separately
 # verified earlier and stay evidence-only; do not equate it to licensed CC0.
 assert len(csvrows(SWISS3))==3
def old():
 pincheck()
 dataset={k:[] for k in SPECS}
 for p in (SOURCE,AUS,SWISS3):
  for r in csvrows(p):
   lg=r["league"]
   if lg not in SPECS or r["season"]!="2026-27":continue
   d=r["date"][:10]
   if d>CUTOFF:raise ValueError("OLD_ARCHIVE_POST_CUTOFF")
   h=r["home"];a=r["away"]
   if not h or not a or h==a:raise ValueError("OLD_INVALID_TEAMS")
   dataset[lg].append((d,h,a,old_score(r),p.as_posix()))
 for lg,spec in SPECS.items():
  if len(dataset[lg])!=spec["local_expected"]:
   raise ValueError("LOCAL_COUNT_CHANGED:"+lg)
  keys=[(d,strict_norm(h),strict_norm(a)) for d,h,a,score,p in dataset[lg]]
  if len(set(keys))!=len(keys):raise ValueError("OLD_SAME_DAY_DUPLICATE:"+lg)
 return dataset
def source_matches(code):
 data=rows_of(get(API+"/leagues/"+code+"/results/?season=2026-2027"))
 fixtures={};counts=Counter()
 for x in data:
  if not isinstance(x,dict):counts["bad_entry"]+=1;continue
  d=str(x.get("date") or "")[:10]
  if not ("2026-07-01"<=d<=CUTOFF):counts["outside_scope"]+=1;continue
  h=x.get("homeTeam");a=x.get("awayTeam")
  goals=parse_score(x)
  if not h or not a or strict_norm(h)==strict_norm(a) or goals is None:
   counts["no_finished_score_or_team"]+=1;continue
  stage=str(x.get("stage") or "").lower()
  if re.search(r"abandon|postpone|cancel|suspend|awarded",stage):
   counts["unsafe_stage_held"]+=1;continue
  key=(d,strict_norm(h),strict_norm(a))
  if key in fixtures:
   if fixtures[key][3]!=goals:raise ValueError("CONFLICTING_SOURCE_RESULTS_SAME_FIXTURE")
   counts["duplicate_api_row"]+=1
   continue
  fixtures[key]=(d,h,a,goals)
 return list(fixtures.values()),dict(counts)
def reconcile(local,remote,league):
 def key(r,fn):
  d,h,a=r[:3]
  return (d,fn(h),fn(a))
 olds={key(r,strict_norm):r for r in local}
 srcs={key(r,strict_norm):r for r in remote}
 direct=set(olds)&set(srcs)
 conflicting_exact=sum(olds[k][3]!=srcs[k][3] for k in direct)
 # Existing, explicitly pinned season-club alias table (independent older
 # model-free 967-match source QA). Every mapped club must be in local roster.
 roster={team for _,h,a,_,_ in local for team in (h,a)}
 canonical=exact_name_maps(league,roster)
 mapped={};ambiguous_alias=0;score_conflicting_canonical=0
 for r in remote:
  d,h,a,score=r
  ch=match_name(h,canonical);ca=match_name(a,canonical)
  if not ch or not ca or ch==ca:
   ambiguous_alias+=1;continue
  k=(d,ch,ca)
  if k in mapped and mapped[k][3]!=score:
   raise ValueError("DIFFERENT_SCORES_SAME_CANONICAL_SOURCE_FIXTURE")
  mapped[k]=r
 canonical_exact=0
 for r in local:
  d,h,a,score,_=r
  k=(d,h,a)
  if k in mapped:
   if score==mapped[k][3]:canonical_exact+=1
   else:score_conflicting_canonical+=1
 # Remaining unpaired: only strict spelling is unquestionably identical.
 ol=[r for k,r in olds.items() if k not in direct]
 re=[r for k,r in srcs.items() if k not in direct]
 oa=defaultdict(list);ra=defaultdict(list)
 for x in ol:oa[key(x,reduced_norm)].append(x)
 for x in re:ra[key(x,reduced_norm)].append(x)
 safe_alias=set()
 score_conflict=0
 for k in set(oa)&set(ra):
  if len(oa[k])==len(ra[k])==1:
   l,r=oa[k][0],ra[k][0]
   if l[3]==r[3]:safe_alias.add(k)
   else:score_conflict+=1
 # all pairs from same local/remote with same date+ft that are not definitely
 # identified as same clubs remain unverified candidates; no silent addition.
 return {
  "local":len(local),
  "source":len(remote),
  "strict_same_date_home_away":len(direct),
  "known_pinned_roster_alias_same_date_FT_confirmed":canonical_exact,
  "known_pinned_roster_alias_same_date_FT_conflicts_hold":score_conflicting_canonical,
  "provider_teams_not_mappable_by_pinned_club_aliases":ambiguous_alias,
  "provider_canonical_fixture_keys_total":len(mapped),
  "source_not_covered_by_canonical_pinned_matches":len(remote)-canonical_exact,
  "local_not_covered_by_canonical_pinned_matches":len(local)-canonical_exact,
  "strict_score_conflicts_hold":conflicting_exact,
  "additional_suffix_alias_same_date_FT_candidate_only":len(safe_alias),
  "suffix_alias_same_date_but_score_conflict_hold":score_conflict,
  "source_fixture_identities_not_accounted_for_strictly":len(remote)-len(direct),
  "source_fixture_identities_not_accounted_for_after_candidate_alias":len(remote)-len(direct)-len(safe_alias),
  "local_not_accounted_for_after_candidate_alias":len(local)-len(direct)-len(safe_alias),
  "confidence":"PERSONAL_SOURCE_METADATA_ONLY_NOT_FINAL_CROSS_SOURCE_FT_CERTIFICATION",
 }
def run():
 before=json.loads(PREVIOUS.read_text())
 locally=old()
 report={
  "date":"2026-11-14","cutoff":"2026-11-13",
  "status":"FOUR_SOURCE_IDENTITY_RECONCILIATION_VOLATILE_METADATA_ONLY",
  "source":"Football Charts personal free research API",
  "terms":"https://www.football-charts.com/terms",
  "scope":list(SPECS),"requests_max":4,
  "source_raw_rows_rehosted":0,"source_match_urls_published":0,
  "new_model_training_rows":0,"old_9460_and_200_source_manifest_modified":False,
  "main_M4_or_xG_file_modified":False,
  "league_results":{},
  "limitations":[
   "Exact date and normalized club spelling is stronger than counts but not a universal canonical team-ID proof.",
   "Trimming FC/SC prefixes/suffixes is a candidate alias only; matching FT does not establish independent source lineage.",
   "Only counts, not source raw scores, full match identities or substantial extraction, can be written to this public repository.",
   "The source's results may include a misleading completed 0-0 or nonregular stage; fresh official fixture identification required before promotion.",
   "The 118 pre-existing figure is an aggregate difference, not automatically 118 individually verified novel fixtures.",
   "Source raw results were volatile and never written to git, files or logs."],
  "actionable_next":"For a public scores archive, license-clean primary data or explicit reuse permission and independent FT corroboration are required. Do not promote source-only fixtures."
 }
 for lg,spec in SPECS.items():
  earlier=before["counts"][lg]
  if (earlier["source_minus_local_count"]!=spec["source_expected"]-spec["local_expected"]
     or earlier["persisted_research_or_core"]!=spec["local_expected"]):
   raise ValueError("BASE_SOURCE_COUNTS_CHANGED:"+lg)
  try:
   live,qa=source_matches(spec["code"])
   counts=reconcile(locally[lg],live,lg)
   counts["source_qa_status"]=qa
   counts["source_league_code"]=spec["code"]
   counts["prior_count_only_gap"]=earlier["source_minus_local_count"]
   counts["source_count_matches_prior_snapshot"]=(counts["source"]==spec["source_expected"])
   report["league_results"][lg]=counts
  except Exception as exc:
   report["league_results"][lg]={"status":"SOURCE_UNAVAILABLE_FAIL_CLOSED",
     "exception_type":type(exc).__name__,
     "previous_source_count_only":spec["source_expected"],
     "previous_local_count":spec["local_expected"],
     "no_new_match_approved":True}
 report["source_successful"]=sum("strict_same_date_home_away" in x for x in report["league_results"].values())
 report["source_access_blocked"]=4-report["source_successful"]
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],
   "successful":report["source_successful"],"blocked":report["source_access_blocked"],
   "aggregate":{k:{q:v.get(q) for q in ("local","source","strict_same_date_home_away","known_pinned_roster_alias_same_date_FT_confirmed",
      "source_not_covered_by_canonical_pinned_matches",
      "known_pinned_roster_alias_same_date_FT_conflicts_hold",
      "provider_teams_not_mappable_by_pinned_club_aliases",
      "additional_suffix_alias_same_date_FT_candidate_only",
      "source_fixture_identities_not_accounted_for_after_candidate_alias",
      "source_count_matches_prior_snapshot","status")}
     for k,v in report["league_results"].items()},
   "model_training":0},ensure_ascii=False))
def selftest():
 assert len(SPECS)==4 and sum(s["source_expected"]-s["local_expected"] for s in SPECS.values())==118
 assert strict_norm("F.C. Zürich")==strict_norm("FC Zurich")
 assert reduced_norm("FC Thun")==reduced_norm("Thun FC")
 a=[("2026-10-01","FC Thun","Basel",(1,0),"src")]
 b=[("2026-10-01","Thun","Basel",(1,0))]
 q=reconcile(a,b,"CHE1")
 assert q["known_pinned_roster_alias_same_date_FT_confirmed"]==1
 assert q["strict_same_date_home_away"]==0
 print("PASS 4 leagues 118 historical count gap, deterministic string and match-identity guard")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true")
 p.add_argument("--run",action="store_true")
 a=p.parse_args()
 if a.self_test:selftest()
 if a.run:run()
