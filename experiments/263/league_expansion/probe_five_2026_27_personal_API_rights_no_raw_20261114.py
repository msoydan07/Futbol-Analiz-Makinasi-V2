#!/usr/bin/env python3
"""Once-only personal-research API source scope gate for five 2026/27 gaps.

Permissive CC BY 4.0 historical SNAPSHOT expires mid-2026. Its LIVE API is
different: personal research allowed WITH attribution; redistribution,
substantial extracts and public raw data tables forbidden. This program
persists ONLY small derived metadata/coverage counts and source references.

NEVER log, print, commit, store in workflow artifact, or redistribute a
provider match result row, a substantial source extract, or a secret.
NEVER use post-match features to certify a pre-kickoff feature vintage.

No original 4,505 existing research result files touched. Strict date cutoff
2026-11-13 and selected CURRENT winter season 2026-2027. Public GitHub
pipeline collects only statistics; raw provider responses in RAM and discarded.
Provider keyless budget ~25 requests/day; cap ONE catalog + FIVE leagues.
"""
import argparse,json,re
from datetime import date,datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

ROOT=Path("experiments/263/league_expansion")
OUT=ROOT/"current_2026_27_five_leagues_footballcharts_personal_research_API_rights_probe_20261114.json"
API="https://footballcharts-backend.onrender.com/api/v1"
BASE_SITE="https://www.football-charts.com"
CUTOFF=date(2026,11,13)
TARGET={
 "ENG5":{"country":("england","english"),"name":("national league",),"code":("national",)},
 "ESP2":{"country":("spain","spanish","espana"),"name":("segunda division","la liga 2","laliga 2","la liga hyprmotion","segunda","laliga2"),"code":("spain2",)},
 "ITA2":{"country":("italy","italia"),"name":("serie b",),"code":("italy2",)},
 "FRA2":{"country":("france","french"),"name":("ligue 2",),"code":("france2",)},
 "DNK1":{"country":("denmark","danish","danmark"),"name":("superliga","superligaen","super league"),"code":("denmark1","denmark",)}
}
def norm(v):
 import unicodedata
 v="".join(x for x in unicodedata.normalize("NFKD",str(v).casefold()) if not unicodedata.combining(x))
 return re.sub(r"[^a-z0-9]+"," ",v).strip()
def get_json(url):
 req=Request(url,headers={"Accept":"application/json","User-Agent":"FutbolAnalizMakinesi/0.1 (one-time personal-research metadata proof; no raw redistribution)"})
 with urlopen(req,timeout=24) as response:
  raw=response.read(3_500_001)
 if len(raw)>3_500_000:raise ValueError("SOURCE_OVERSIZE_FAIL_CLOSED")
 return json.loads(raw)
def catalog_candidates(j):
 if isinstance(j,list):return [x for x in j if isinstance(x,dict)]
 if not isinstance(j,dict):raise ValueError("LEAGUE_CATALOG_UNEXPECTED_ROOT")
 for key in ("leagues","results","data","items","competitions"):
  if isinstance(j.get(key),list):return [x for x in j[key] if isinstance(x,dict)]
 raise ValueError("LEAGUE_CATALOG_NO_LIST")
def recognized_code(x):
 for key in ("code","slug","league_code","id"):
  if isinstance(x.get(key),str) and re.fullmatch(r"[a-zA-Z0-9_-]+",x[key]):
   return x[key]
 return ""
def match_catalog(items,lg):
 t=TARGET[lg];chosen=[]
 for entry in items:
  code=recognized_code(entry)
  textname=" ".join(str(entry.get(key) or "") for key in ("name","league_name","title","competition","display_name"))
  country=" ".join(str(entry.get(key) or "") for key in ("country","country_name","region"))
  nn=norm(textname);cc=norm(country)
  code_is_target=code in t["code"]
  name_matches=any(norm(s)==nn or nn.startswith(norm(s)+" ") for s in t["name"])
  country_matches=any(norm(s) in cc for s in t["country"])
  # An exact known code can be used in lieu of a missing catalog country
  # field. Explicitly reject potential women's and youth competitions.
  women_youth=any(s in nn for s in ("women","woman","femenin","under 21","under 19","u19","u21","girls","ladies"))
  if code and not women_youth and (code_is_target or (name_matches and (country_matches or not cc))):
   chosen.append({"code":code,"catalog_name":textname or None})
 # Do not report the full catalog and never choose ambiguously.
 if len({x["code"] for x in chosen})!=1:return None,{"candidate_code_count":len({x["code"] for x in chosen})}
 return chosen[0],{"candidate_code_count":1}
def match_list(payload):
 if isinstance(payload,list):return [x for x in payload if isinstance(x,dict)]
 if not isinstance(payload,dict):raise ValueError("RESULTS_RESPONSE_UNRECOGNIZED")
 for k in ("results","matches","data","items","fixtures","games"):
  if isinstance(payload.get(k),list):return [x for x in payload[k] if isinstance(x,dict)]
  if isinstance(payload.get(k),dict):
   q=payload[k]
   for sub in ("results","matches","data","items"):
    if isinstance(q.get(sub),list):return [x for x in q[sub] if isinstance(x,dict)]
 raise ValueError("RESULTS_MATCH_LIST_MISSING")
def parse_date(item):
 for k in ("date","match_date","kickoff_utc","kickoff","datetime","started_at"):
  x=item.get(k)
  if x:
   try:return date.fromisoformat(str(x)[:10])
   except ValueError:pass
 return None
def string_team(x):
 if isinstance(x,dict):
  for k in ("name","short_name","team_name","club","display_name"):
   if isinstance(x.get(k),str):return x[k]
  return ""
 return x if isinstance(x,str) else ""
def scored(item):
 home=string_team(item.get("home_team") or item.get("home") or item.get("team1"))
 away=string_team(item.get("away_team") or item.get("away") or item.get("team2"))
 if not home or not away or norm(home)==norm(away):return None
 sh=item.get("home_goals",item.get("home_score",item.get("score_home")))
 sa=item.get("away_goals",item.get("away_score",item.get("score_away")))
 if isinstance(item.get("score"),dict):
  sc=item["score"]
  sh=sh if sh is not None else sc.get("home")
  sa=sa if sa is not None else sc.get("away")
 def goal_int(x):
  if type(x) is int:return x
  if isinstance(x,str) and x.isdigit():return int(x)
  return None
 sh,sa=goal_int(sh),goal_int(sa)
 if sh is None or sa is None or not (0<=sh<=30 and 0<=sa<=30):return None
 return (home,away,sh,sa)
def aggregate(rows):
 count={"raw_provider_rows":len(rows),"date_outside_frozen_cutoff":0,
        "matched_completed_historical_result_field_rows":0,
        "missing_scored_fields_or_unparseable":0,
        "source_duplicate_historical_date_team_ids":0}
 seen=set();clubs=set();dated=[]
 for r in rows:
  day=parse_date(r)
  if day is None:
   count["missing_scored_fields_or_unparseable"]+=1;continue
  if not date(2026,7,1)<=day<=CUTOFF:
   count["date_outside_frozen_cutoff"]+=1;continue
  score=scored(r)
  if score is None:
   count["missing_scored_fields_or_unparseable"]+=1;continue
  home,away,_,_=score
  key=(day,norm(home),norm(away))
  if key in seen:
   count["source_duplicate_historical_date_team_ids"]+=1;continue
  seen.add(key);clubs.update((norm(home),norm(away)));dated.append(day.isoformat())
  count["matched_completed_historical_result_field_rows"]+=1
 count["distinct_clubs_covered"]=len(clubs)
 count["first_finished_date"]=min(dated,default=None)
 count["last_finished_date"]=max(dated,default=None)
 return count
def run():
 report={
  "report_day":"2026-11-14",
  "status":"FIVE_2026_27_FIRST_PARTY_LIVE_PERSONAL_RESEARCH_API_RIGHTS_AND_COVERAGE_PROBE",
  "provider":"Football Charts",
  "developer_terms":"https://www.football-charts.com/developers",
  "rights_terms":"https://www.football-charts.com/terms",
  "provider_credit_required":"Data by football-charts.com",
  "rights_classification":"FREE_PERSONAL_RESEARCH_USE_ONLY_NO_RAW_DATA_REDISTRIBUTION_OR_SUBSTANTIAL_EXTRACT_PUBLICATION",
  "historical_CC_BY_snapshot_license_NOT_applied_to_LIVE_API":True,
  "research_use_context":"Single personal private research computation, public GitHub receives metadata statistics only",
  "frozen_scored_match_cutoff":"2026-11-13",
  "season_requested":"2026-2027",
  "target_groups":list(TARGET),
  "original_rights_uncleared_632_provider_compilation_rows_imported":0,
  "new_raw_source_match_rows_rehosted":0,
  "new_model_training_rows_approved":0,
  "old_pinned_4505_research_fixture_rows_unchanged":True,
  "old_1775_461_1268_and_106_historical_result_score_QA_replayed":0,
  "old_10league_M4_SHA_and_user_xG_unchanged":True,
  "source_publisher_declares_current_prev_season_data_access":True,
  "source_daily_keyless_requests_target_max":6,
  "provider_results_are_ephemeral_no_raw_logs_and_no_store":True,
  "network_metadata_failure_must_not_pretend_historical_data_ingested":True,
  "by_league":{},
  "next_distinct_task":"If response supports verified current-season league scores, use a local personal-rights-aware volatile reader (not a public raw GitHub CSV archive). Preserve per-match source rights, league identity and pre-kickoff feature-vintage gates. If catalog is unavailable, switch to a different provider rather than replaying old sources."
 }
 try:
  catalog=catalog_candidates(get_json(API+"/leagues/"))
  report["catalog_total_competitions"]=len(catalog)
 except Exception as e:
  catalog=[]
  report["catalog_status"]="UNAVAILABLE__FAIL_CLOSED"
  report["catalog_error_class"]=type(e).__name__
 if not catalog:
  for lg in TARGET:
   report["by_league"][lg]={"status":"SOURCE_CATALOG_UNAVAILABLE_HOLD","new_training_rows":0}
 else:
  for lg in TARGET:
   choice,diag=match_catalog(catalog,lg)
   if not choice:
    report["by_league"][lg]={"status":"TARGET_LEAGUE_CODE_NOT_UNAMBIGUOUS_HOLD",**diag,"new_training_rows":0}
    continue
   code=choice["code"]
   url=API+"/leagues/"+code+"/results/?season=2026-2027"
   try:
    data=get_json(url)
    counts=aggregate(match_list(data))
    report["by_league"][lg]={
     "status":"PERSONAL_RESEARCH_SOURCE_METADATA_AVAILABLE_NO_RAW_ARCHIVAL" if counts["matched_completed_historical_result_field_rows"]>0 else "SOURCE_RESPONSE_HAS_NO_VALID_SCORABLE_MATCHES_HOLD",
     "provider_competition_code":code,
     "provider_competition_label":choice["catalog_name"],
     "source_endpoint_no_key":url,
     "derived_metadata_only":counts,
     "raw_fixture_rows_written_to_GitHub":0,
     "new_training_rows":0
    }
   except Exception as e:
    report["by_league"][lg]={
     "status":"PROVIDER_ENDPOINT_FAIL_CLOSED",
     "provider_competition_code":code,
     "provider_competition_label":choice["catalog_name"],
     "error_type":type(e).__name__,
     "http_code":e.code if isinstance(e,HTTPError) else None,
     "raw_fixture_rows_written_to_GitHub":0,
     "new_training_rows":0
    }
 report["available_personal_source_league_count"]=sum(1 for x in report["by_league"].values() if x["status"]=="PERSONAL_RESEARCH_SOURCE_METADATA_AVAILABLE_NO_RAW_ARCHIVAL")
 report["scored_source_rows_only_ephemeral"]=sum(x.get("derived_metadata_only",{}).get("matched_completed_historical_result_field_rows",0) for x in report["by_league"].values())
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return report
def test():
 assert len(TARGET)==5
 assert CUTOFF==date(2026,11,13)
 assert scored({"home":"A","away":"B","home_goals":0,"away_goals":2}) is not None
 assert scored({"home":"A","away":"B","home_goals":None,"away_goals":2}) is None
 assert aggregate([{"date":"2026-11-13","home":"A","away":"B","home_goals":1,"away_goals":0}])["matched_completed_historical_result_field_rows"]==1
 print("PASS five league source scope & no persisted score rows")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true")
 args=p.parse_args()
 if args.self_test:test()
 if args.run:
  d=run()
  print("FIVE_LEAGUE_PERSONAL_API_START")
  print(json.dumps(d,ensure_ascii=False,indent=2))
  print("FIVE_LEAGUE_PERSONAL_API_END")
