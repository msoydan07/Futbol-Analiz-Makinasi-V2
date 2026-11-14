#!/usr/bin/env python3
"""Only remaining 2 unrecognized live league names: Portugal & Belgium.
Catalog name is mandatory + country match. Saves only aggregate scores count
through Nov 13, not match results. No rerun of already completed other 15+5.
"""
import json,re
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path("experiments/263/league_expansion")
OUT=ROOT/"2026_27_only_2_portugal_belgium_catalog_name_freshness_20261114.json"
BASE=ROOT/"2026_27_17_persisted_leagues_one_freshness_aggregates_only_20261114.json"
API="https://footballcharts-backend.onrender.com/api/v1"
def fetch(x):
 req=Request(API+x,headers={"Accept":"application/json","User-Agent":"OnePrivatePortugalBelgiumSourceNameOnly/1.0"})
 with urlopen(req,timeout=28) as r:raw=r.read(2_000_001)
 if len(raw)>2_000_000:raise ValueError("SOURCE_OVERSIZE")
 return json.loads(raw)
def run():
 older=json.loads(BASE.read_text())
 if older["league_coverage_resolved"]!=15 or older["counts"]["POR1"]["status"]!="CATALOG_LEAGUE_UNRESOLVED_HOLD" or older["counts"]["BEL1"]["status"]!="CATALOG_LEAGUE_UNRESOLVED_HOLD":
  raise ValueError("NOT_TWO_OLD_UNRESOLVED")
 matches=fetch("/leagues/")
 if isinstance(matches,dict):matches=matches.get("leagues",[])
 if not isinstance(matches,list):raise ValueError("CATALOG_NOT_LIST")
 out={"status":"TWO_REMAINING_PORTUGAL_BELGIUM_LIVE_CATALOG_FRESHNESS_ONLY",
  "by_league":{},"repeated_other_15_plus_previous_5_FT_source_reads":0,
  "bulk_raw_score_records_committed":0,"model_training_approved":0,
  "cutoff":"2026-11-13","source_terms":"https://www.football-charts.com/terms"}
 for lg,country in (("POR1","Portugal"),("BEL1","Belgium")):
  catalog=[x for x in matches if isinstance(x,dict) and x.get("country")==country]
  out["by_league"][lg]={"catalog_names_and_codes":[{"name":x.get("name"),"code":x.get("league")} for x in catalog],
                        "existing":older["counts"][lg]["persisted_research_or_core"]}
  expected={"POR1":["Liga Portugal","Primeira Liga","Liga Portugal Betclic"],
            "BEL1":["Jupiler Pro League","Pro League","Belgian Pro League"]}
  chosen=[x for x in catalog if str(x.get("name") or "").casefold().strip() in [n.casefold() for n in expected[lg]]]
  if len(chosen)!=1:
   out["by_league"][lg]["status"]="CATALOG_NO_UNIQUE_EXPECTED_NAME_HOLD";continue
  code=chosen[0].get("league")
  try:
   rows=fetch(f"/leagues/{code}/results/?season=2026-2027")
   if isinstance(rows,dict):rows=rows.get("results") or rows.get("matches") or rows.get("data")
   if not isinstance(rows,list):raise ValueError("RESULTS_NOT_LIST")
   keys=set();duplicate=0
   for r in rows:
    if not isinstance(r,dict):continue
    d=str(r.get("date") or "")[:10];score=str(r.get("score") or "").strip().replace("–","-")
    home=str(r.get("homeTeam") or "").strip().casefold()
    away=str(r.get("awayTeam") or "").strip().casefold()
    if not "2026-07-01"<=d<="2026-11-13" or not home or not away or not re.fullmatch(r"\d{1,2}[-:]\d{1,2}",score):continue
    k=(d,home,away)
    if k in keys:duplicate+=1
    keys.add(k)
   out["by_league"][lg].update({"status":"SOURCE_COUNT_READ_METADATA_ONLY",
      "provider_code":code,"count_through_cutoff":len(keys),"duplicate_input_keys_skipped":duplicate,
      "provider_minus_persisted":len(keys)-older["counts"][lg]["persisted_research_or_core"]})
  except Exception as e:
   out["by_league"][lg].update({"status":"SOURCE_FETCH_FAIL_CLOSED","error_type":type(e).__name__})
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 return out
if __name__=="__main__":print(json.dumps(run(),ensure_ascii=False,indent=2))
