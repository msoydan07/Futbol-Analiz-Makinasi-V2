#!/usr/bin/env python3
"""NEW current-season freshness dimension for 17 persisted 2026/27 leagues.

5 league results already probed and frozen: DNK1, ENG5, ESP2, ITA2, FRA2.
Never call those sources again, never persist provider raw result tables.
Catalog 1 request + each of the OTHER 17 scoped single results requests.
This is an aggregate-only factual source count and timing gap diagnostic.
Remaining date-level identities need license-cleared original source before
they can be added to public repository; no model, no xG.
"""
import csv,hashlib,json,re,unicodedata
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path("experiments/263/league_expansion")
REPORT=ROOT/"2026_27_17_persisted_leagues_one_freshness_aggregates_only_20261114.json"
BASE=ROOT/"22x2_full_production_plus_research_inventory_diagnostic_20261114.json"
FIVE=ROOT/"current_2026_27_five_leagues_footballcharts_personal_research_API_rights_probe_20261114.json"
API="https://footballcharts-backend.onrender.com/api/v1"
EXCLUDED_FROZEN=("DNK1","ENG5","ESP2","ITA2","FRA2")
# Catalog name & country must match; never guess based solely on a short code
TARGET={
 "ENG1":("England",["Premier League"]),
 "ENG2":("England",["Championship"]),
 "GER1":("Germany",["Bundesliga"]),
 "ESP1":("Spain",["La Liga","LaLiga"]),
 "ITA1":("Italy",["Serie A"]),
 "FRA1":("France",["Ligue 1"]),
 "NED1":("Netherlands",["Eredivisie"]),
 "TUR1":("Turkey",["Super Lig","Süper Lig"]),
 "POR1":("Portugal",["Primeira Liga"]),
 "BEL1":("Belgium",["Pro League","Belgian Pro League"]),
 "SCO1":("Scotland",["Premiership","Scottish Premiership"]),
 "CHE1":("Switzerland",["Super League","Swiss Super League"]),
 "ENG3":("England",["League One"]),
 "ENG4":("England",["League Two"]),
 "GER2":("Germany",["2. Bundesliga","Bundesliga 2"]),
 "GRE1":("Greece",["Super League","Super League 1"]),
 "AUT1":("Austria",["Bundesliga"])
}
CUTOFF="2026-11-13"
def norm(s):
 return re.sub(r"[^a-z0-9]+"," ", "".join(ch for ch in unicodedata.normalize("NFKD",str(s).casefold()) if not unicodedata.combining(ch))).strip()
def get(url):
 req=Request(url,headers={"Accept":"application/json","User-Agent":"FutbolAnalizMakinasiPersonalResearchFreshnessV1 (17 aggregate metadata only)"})
 with urlopen(req,timeout=27) as resp:raw=resp.read(4_000_001)
 if len(raw)>4_000_000:raise ValueError("RESPONSE_TOO_BIG")
 return json.loads(raw)
def get_results(j):
 if isinstance(j,list):return j
 if isinstance(j,dict):
  for k in ("results","matches","data","items"):
   if isinstance(j.get(k),list):return j[k]
 raise ValueError("SOURCE_RESULTS_SCHEMA_UNKNOWN")
def count_done(rows):
 seen={};duplicates=0;invalid=0;late=0
 for r in rows:
  if not isinstance(r,dict):invalid+=1;continue
  d=str(r.get("date") or "")[:10]
  if not (len(d)==10 and "2026-07-01"<=d<=CUTOFF):late+=1;continue
  h=str(r.get("homeTeam") or "").strip().lower()
  a=str(r.get("awayTeam") or "").strip().lower()
  score=str(r.get("score") or "").strip().replace("–","-")
  if not h or not a or h==a or not re.fullmatch(r"\d{1,2}\s*[-:]\s*\d{1,2}",score):
   invalid+=1;continue
  k=(d,h,a)
  if k in seen:
   if seen[k]!=score:raise ValueError("SOURCE_SAME_FIXTURE_SCORE_CONFLICT")
   duplicates+=1
  else:seen[k]=score
 return {"unique_scored_finished_matches_through_2026_11_13":len(seen),
   "duplicates_removed_in_RAM":duplicates,"skipped_future_or_other_season":late,
   "unparseable_or_unscored":invalid,
   "latest_result_date":max((k[0] for k in seen),default=None)}
def run():
 diag=json.loads(BASE.read_text())
 five=json.loads(FIVE.read_text())
 if diag["counts"]["main_core_archive"]!=4617 or five["available_personal_source_league_count"]!=5:
  raise ValueError("OLD_DONE_SOURCE_FROZEN_NOT_AS_EXPECTED")
 current={x["league"]:x["production_results_only_baseline_count"]+x["research_source_specific_count"]
          for x in diag["cells"] if x["season"]=="2026-27"}
 if set(current)!=set(TARGET).union(EXCLUDED_FROZEN):raise ValueError("NOT_22_LEAGUES")
 out={"status":"17_CURRENT_LEAGUE_SOURCE_FRESHNESS_AGGREGATES_ONLY",
      "scope":"ONLY 17 persisted groups; 5 live-only previously frozen were NOT called again",
      "previous_five_frozen":list(EXCLUDED_FROZEN),"source":"Football Charts LIVE API personal research",
      "source_terms":"https://www.football-charts.com/terms",
      "cutoff":CUTOFF,
      "new_raw_provider_result_rows_published":0,
      "new_model_training_approved":0,
      "target_leagues":list(TARGET),
      "source_identity_match_delta_not_score_label_validation":True,
      "previous_5_live_only_counts":{k:five["by_league"][k]["derived_metadata_only"]["matched_completed_historical_result_field_rows"] for k in EXCLUDED_FROZEN},
      "counts":{}}
 try:
  catalog=get(API+"/leagues/")
  if isinstance(catalog,dict):catalog=catalog.get("leagues",[])
  if not isinstance(catalog,list):raise ValueError("CATALOG_SCHEMA")
 except Exception as e:
  catalog=[]
  out["catalog_status"]="UNAVAILABLE_FAIL_CLOSED"
  out["catalog_error_type"]=type(e).__name__
 if catalog:
  out["catalog_status"]="AVAILABLE";out["catalog_entries"]=len(catalog)
 for lg,(country,names) in TARGET.items():
  nbase=current[lg]
  matches=[x for x in catalog if norm(x.get("country",""))==norm(country)
           and norm(x.get("name","")) in {norm(n) for n in names}]
  if len(matches)!=1:
   out["counts"][lg]={"status":"CATALOG_LEAGUE_UNRESOLVED_HOLD",
                    "persisted_research_or_core":nbase,"catalog_candidates":len(matches)}
   continue
  code=matches[0].get("league")
  if not isinstance(code,str) or not re.fullmatch(r"[a-z0-9_-]+",code):
   out["counts"][lg]={"status":"CODE_UNSAFE_HOLD","persisted_research_or_core":nbase};continue
  try:
   rows=get(API+"/leagues/"+code+"/results/?season=2026-2027")
   stats=count_done(get_results(rows))
   diff=stats["unique_scored_finished_matches_through_2026_11_13"]-nbase
   out["counts"][lg]={"status":"SOURCE_COMPARABLE_COUNT_ONLY_NOT_LICENSED_REHOST",
      "source_league_code":code,"source_league_name":matches[0]["name"],
      "persisted_research_or_core":nbase,"source_distinct_finished_count":stats["unique_scored_finished_matches_through_2026_11_13"],
      "source_minus_local_count":diff,
      "possible_unarchived_if_source_additional":max(0,diff),
      "source_difference_warning":"Count parity is NOT proof same fixtures; no raw match data retained",
      "quality_flags_without_match_rows":stats}
  except Exception as e:
   out["counts"][lg]={"status":"SOURCE_FETCH_UNAVAILABLE_FAIL_CLOSED",
         "source_league_code":code,"error_type":type(e).__name__,
         "persisted_research_or_core":nbase}
 out["league_coverage_resolved"]=sum(x["status"]=="SOURCE_COMPARABLE_COUNT_ONLY_NOT_LICENSED_REHOST" for x in out["counts"].values())
 out["source_possible_new_unarchived_count_sum"]=sum(x.get("possible_unarchived_if_source_additional",0) for x in out["counts"].values())
 out["count_match_leagues"]=sum(x.get("source_minus_local_count")==0 for x in out["counts"].values())
 out["source_more_than_persisted_leagues"]=[k for k,v in out["counts"].items() if v.get("source_minus_local_count",0)>0]
 out["persisted_more_than_source_leagues"]=[k for k,v in out["counts"].items() if v.get("source_minus_local_count",0)<0]
 out["closing_rule"]="No claim of complete 22/22 played-fixture matches until original licensed match identities, fixture stages and duplicates are checked. This probe never republishes source scores."
 REPORT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 return out
def selftest():
 assert len(TARGET)==17 and len(EXCLUDED_FROZEN)==5
 assert count_done([{"date":"2026-08-01","homeTeam":"A","awayTeam":"B","score":"1-0"},{"date":"2026-08-01","homeTeam":"A","awayTeam":"B","score":"1-0"}])["duplicates_removed_in_RAM"]==1
 print("PASS 17 distinct current research leagues, five immutable exclusions, strict cutoff, source counts not raw")
if __name__=="__main__":
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--run",action="store_true")
 x=p.parse_args()
 if x.test:selftest()
 if x.run:
  out=run()
  print(json.dumps({"status":out["status"],"resolved":out["league_coverage_resolved"],
      "possible_source_plus":out["source_possible_new_unarchived_count_sum"],
      "comparisons":{k:{"status":v["status"],"persisted":v.get("persisted_research_or_core"),"source":v.get("source_distinct_finished_count"),"delta":v.get("source_minus_local_count")} for k,v in out["counts"].items()}},ensure_ascii=False))
