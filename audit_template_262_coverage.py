"""2.6.2 field coverage by league/season; availability is not data accuracy."""
import csv,io,json,urllib.request
from pathlib import Path
from collections import Counter
from collect_team_candidates import LEAGUES,SEASONS,BASE

FIELDS={
 "full_time_goals":["FTHG","FTAG","FTR"],
 "half_time_goals":["HTHG","HTAG","HTR"],
 "shots":["HS","AS"],
 "shots_on_target":["HST","AST"],
 "corners":["HC","AC"],
 "fouls":["HF","AF"],
 "yellow_cards":["HY","AY"],
 "red_cards":["HR","AR"],
 "referee":["Referee"],
 "xg_xga":["xG","xGA"],
}
# xG uses provider-specific formats and is deliberately NOT inferred from goals/shots.
OUT=Path("data")
def audit():
 OUT.mkdir(exist_ok=True)
 report=[]
 for season,short in SEASONS.items():
  for league,code in LEAGUES.items():
   url=f"{BASE}/{short}/{code}.csv"
   entry={"league":league,"season":season,"url":url,"status":"FAILED"}
   try:
    req=urllib.request.Request(url,headers={"User-Agent":"FutbolAnalizV2/1.0"})
    with urllib.request.urlopen(req,timeout=25) as response:
     rows=list(csv.DictReader(io.StringIO(response.read().decode("utf-8-sig",errors="replace"))))
    headers=set(rows[0]) if rows else set()
    entry.update(status="OK",rows=len(rows),fields={})
    for name,columns in FIELDS.items():
     present=all(c in headers for c in columns)
     filled=sum(all((r.get(c) or "").strip() for c in columns) for r in rows) if present else 0
     entry["fields"][name]={"columns_present":present,"filled_rows":filled,
                             "coverage_pct":round(100*filled/len(rows),2) if rows else 0}
    entry["fields"]["league_home_away_goals"]={"derivable_from":"full_time_goals"}
    entry["fields"]["recent_form"]={"derivable_from":"dated historical results"}
    entry["fields"]["elo"]={"status":"DERIVE_SEPARATELY; not raw CSV"}
    for name in ("injuries_suspensions","confirmed_lineups","tactics","rest_travel",
                 "verified_xg_provider","opening_closing_odds","official_fixture"):
     entry["fields"][name]={"status":"EXTERNAL_OR_SEPARATE_VERIFICATION"}
   except Exception as exc:
    entry["error"]=str(exc)[:200]
   report.append(entry)
 result={"version":"2.6.2_source_field_coverage_v1",
         "caution":"Field presence and nonempty counts do not verify accuracy or model sufficiency.",
         "sources":report,"sources_ok":sum(r["status"]=="OK" for r in report)}
 (OUT/"template_262_coverage.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"sources_ok":result["sources_ok"],"source_count":len(report)},indent=2))
 if result["sources_ok"]!=20:raise SystemExit("Coverage scan incomplete")
if __name__=="__main__":audit()
