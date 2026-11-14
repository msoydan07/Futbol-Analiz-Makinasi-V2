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
# Explicit factual club-name identities from earlier pinned league rosters.
# Punctuation/suffix heuristics by themselves are NOT enough for an approval.
# No score info is used to invent a club mapping.
ALIASES={
"SCO1":{
"hearts":"hearts","heartofmidlothian":"hearts",
"stjohnstone":"stjohnstone","saintjohnstonefc":"stjohnstone",
"saintjohnstone":"stjohnstone","stjohnstonefc":"stjohnstone",
"stmirren":"stmirren","stmirrenfc":"stmirren",
"falkirk":"falkirk","falkirkfc":"falkirk",
"dundee":"dundee","dundeefc":"dundee",
"dundeeunited":"dundeeunited","dundeeutd":"dundeeunited",
"hibernian":"hibernian","hibernianfc":"hibernian",
"aberdeen":"aberdeen","aberdeenfc":"aberdeen",
"celtic":"celtic","celticfc":"celtic",
"rangers":"rangers","rangersfc":"rangers",
"kilmarnock":"kilmarnock","kilmarnockfc":"kilmarnock",
"motherwell":"motherwell","motherwellfc":"motherwell"},
"CHE1":{
"basel":"basel","fcbasel":"basel","fcbasel1893":"basel",
"lausanne":"lausanne","lausannesport":"lausanne","fclausannesport":"lausanne",
"luzern":"luzern","fcluzern":"luzern",
"stgallen":"stgallen","fcstgallen":"stgallen","fcsanktgallen":"stgallen",
"stgallenfc":"stgallen","sanktgallen":"stgallen",
"sion":"sion","fcsion":"sion",
"thun":"thun","fcthun":"thun",
"vaduz":"vaduz","fcvaduz":"vaduz",
"zurich":"zurich","fczurich":"zurich",
"grasshoppers":"grasshoppers","grasshopper":"grasshoppers",
"grasshopperclubzurich":"grasshoppers",
"lugano":"lugano","fclugano":"lugano",
"youngboys":"youngboys","bscyoungboys":"youngboys",
"servette":"servette","servettefc":"servette"},
"GRE1":{
"aek":"aek","aekathens":"aek","aekathensfc":"aek","aekathen":"aek",
"aris":"aris","aristhessaloniki":"aris","aristhessalonikis":"aris","arissaloniki":"aris",
"asterastripolis":"asterastripolis","asterasaktors":"asterastripolis",
"atromitos":"atromitos","atromitosathinon":"atromitos",
"iraklis1908":"iraklis","iraklis":"iraklis",
"kalamata":"kalamata","kalamatapss":"kalamata",
"kifisia":"kifisia","aekifisias":"kifisia","kifissia":"kifisia",
"levadiakos":"levadiakos",
"ofi":"ofi","oficrete":"ofi","ofiheraklion":"ofi",
"olympiakospiraeus":"olympiakos","olympiacospiraeus":"olympiakos",
"olympiacos":"olympiakos","olympiakos":"olympiakos",
"paok":"paok","paokfc":"paok","paoksaloniki":"paok",
"panathinaikos":"panathinaikos",
"panetolikos":"panetolikos",
"volos":"volos","volosnfc":"volos"},
"AUT1":{}}
def canonical_team(league,name):
 key=strict_norm(name)
 return ALIASES.get(league,{}).get(key,key)

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
 # Each team alias is explicit and local season-roster grounded, never fuzzy.
 old_names={canonical_team(league,n) for _,h,a,_,_ in local for n in (h,a)}
 oldmap={}
 for d,h,a,score,p in local:
  k=(d,canonical_team(league,h),canonical_team(league,a))
  if k in oldmap:raise ValueError("CANONICAL_LOCAL_DATE_TEAM_DUPLICATE")
  oldmap[k]=score
 srcmap={}
 unknown_count=0
 for d,h,a,score in remote:
  x=canonical_team(league,h);y=canonical_team(league,a)
  if x not in old_names or y not in old_names:
   unknown_count+=1
   continue
  k=(d,x,y)
  if k in srcmap and srcmap[k]!=score:raise ValueError("CANONICAL_SOURCE_SCORE_CONFLICT")
  srcmap[k]=score
 common=set(oldmap)&set(srcmap)
 conflicts=sum(oldmap[k]!=srcmap[k] for k in common)
 confirmed=len(common)-conflicts
 gap=len(remote)-confirmed
 strict_old={(d,strict_norm(h),strict_norm(a)):score for d,h,a,score,p in local}
 strict_src={(d,strict_norm(h),strict_norm(a)):score for d,h,a,score in remote}
 strict_common=set(strict_old)&set(strict_src)
 return {
   "local":len(local),"source":len(remote),
   "exact_club_spelling_same_date_matches":len(strict_common),
   "curated_team_roster_date_score_matches":confirmed,
   "curated_team_roster_source_date_or_FT_conflicts_hold":conflicts,
   "provider_source_rows_unmatched_club_roster":unknown_count,
   "source_missing_identity_candidates_after_curated_aliases":gap,
   "old_rows_not_recovered_from_source":len(local)-confirmed,
   "source_minus_local_simple_count":len(remote)-len(local),
   "confidence":"CURATED_CLUB_NAMES_AND_DATE_FT_AGREE_NO_INDEPENDENT_RIGHTS_OR_PREMATCH_CERTIFICATION"
 }
def run():
 before=json.loads(PREVIOUS.read_text())
 locally=old()
 report={
  "date":"2026-11-14","cutoff":"2026-11-13",
  "status":"FOUR_SOURCE_IDENTITY_RECONCILIATION_VOLATILE_METADATA_ONLY",
  "source":"Football Charts personal free research API",
  "prior_Austria_42_72_reused_without_network":True,
  "terms":"https://www.football-charts.com/terms",
  "scope":list(SPECS),"requests_max":3,
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
 earlier_run=json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else None
 # Austria was fully matched in prior successful source run: reuse its 42/42
 # without calling the same API again, preserving the no-repeat rule.
 for lg,spec in SPECS.items():
  earlier=before["counts"][lg]
  if (earlier["source_minus_local_count"]!=spec["source_expected"]-spec["local_expected"]
     or earlier["persisted_research_or_core"]!=spec["local_expected"]):
   raise ValueError("BASE_SOURCE_COUNTS_CHANGED:"+lg)
  try:
   if lg=="AUT1" and earlier_run:
    prior=earlier_run.get("league_results",{}).get("AUT1",{})
    if not (prior.get("known_pinned_roster_alias_same_date_FT_confirmed")==42
            and prior.get("source")==72 and prior.get("local")==42
            and prior.get("known_pinned_roster_alias_same_date_FT_conflicts_hold")==0):
     raise ValueError("PRIOR_AUSTRIA_IDENTITY_PASS_MISSING")
    counts={"local":42,"source":72,"exact_club_spelling_same_date_matches":1,
      "curated_team_roster_date_score_matches":42,
      "curated_team_roster_source_date_or_FT_conflicts_hold":0,
      "provider_source_rows_unmatched_club_roster":0,
      "source_missing_identity_candidates_after_curated_aliases":30,
      "old_rows_not_recovered_from_source":0,
      "source_minus_local_simple_count":30,
      "confidence":"REUSED_PREVIOUS_PINNED_42_OF_42_FT_AND_DATE_MATCH_NO_NEW_CALL"}
    qa={"reused_previous_au":
     "https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43634128246"}
   else:
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
   "aggregate":{k:{"local":v.get("local"),"source":v.get("source"),
      "matched":v.get("curated_team_roster_date_score_matches"),
      "missing_candidates":v.get("source_missing_identity_candidates_after_curated_aliases"),
      "conflicts":v.get("curated_team_roster_source_date_or_FT_conflicts_hold"),
      "unknown_roster":v.get("provider_source_rows_unmatched_club_roster"),
      "status":v.get("status")}
     for k,v in report["league_results"].items()},
   "model_training":0},ensure_ascii=False))
def selftest():
 assert len(SPECS)==4 and sum(s["source_expected"]-s["local_expected"] for s in SPECS.values())==118
 assert strict_norm("F.C. Zürich")==strict_norm("FC Zurich")
 assert reduced_norm("FC Thun")==reduced_norm("Thun FC")
 a=[("2026-10-01","FC Thun","Basel",(1,0),"src")]
 b=[("2026-10-01","Thun","Basel",(1,0))]
 q=reconcile(a,b,"CHE1")
 assert q["curated_team_roster_date_score_matches"]==1
 assert q["exact_club_spelling_same_date_matches"]==0
 print("PASS 4 leagues 118 historical count gap, deterministic string and match-identity guard")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true")
 p.add_argument("--run",action="store_true")
 a=p.parse_args()
 if a.self_test:selftest()
 if a.run:run()
