"""Read-only exact-key first-half corner match pilot. No guessing team aliases."""
import csv,io,json,urllib.request
from collections import defaultdict,Counter
from pathlib import Path
from probe_first_half_corner_source import FOLDERS,BASE
P=Path("data")
def get(path):
 with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def main():
 candidates=get(P/"fixture_candidates.csv")
 hist=get(P/"historical_results.csv")
 # Source names can differ; only use reviewed exact identity names.
 lookup={(r["league"],r["season"],str(r["source_row"])):r for r in candidates}
 base=defaultdict(list)
 for r in hist:
  name=lookup.get((r["league"],r["season"],r["source_row"]))
  if name and r["season"]=="2026-2027":
   base[(r["league"],r["match_date"],name["home"].casefold().strip(),name["away"].casefold().strip())].append(r)
 report={"source":"open-matchday","read_only":True,"matched":0,"unmatched":0,"ambiguous":0,"invalid":0,"sample_source_columns":{},"by_league":[],"rule":"Only exact league, 2026-2027 season, team/date/score and full-match corner agreement; no fuzzy joins; no database writes"}
 for league,folder in FOLDERS.items():
  url=f"{BASE}/{folder}/results_2627.csv"
  n=Counter()
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"FutbolAnalizV2/1.0"})
   with urllib.request.urlopen(req,timeout=20) as f:
    reader=csv.DictReader(io.StringIO(f.read().decode("utf-8-sig")))
    report["sample_source_columns"][league]=reader.fieldnames
    rows=list(reader)
   # Source schema must be independently mapped. No speculative column interpretation.
   date_key=next((x for x in ("match_date","date") if x in (reader.fieldnames or [])),None)
   home_key=next((x for x in ("home_team","home") if x in (reader.fieldnames or [])),None)
   away_key=next((x for x in ("away_team","away") if x in (reader.fieldnames or [])),None)
   if not all((date_key,home_key,away_key)):
    n["schema_unmapped"]=len(rows)
   else:
    for r in rows:
     n["source_rows"]+=1
     vals=("home_corners_1h","away_corners_1h","home_corners","away_corners")
     if not all((r.get(v) or "").strip() for v in vals):
      n["missing_corner_fields"]+=1;continue
     date=r[date_key][:10]
     options=base.get((league,date,r[home_key].casefold().strip(),r[away_key].casefold().strip()),[])
     if not options:
      n["unmatched"]+=1
      if len(n.setdefault("_examples",[]))<8:n["_examples"].append({"date":date,"home":r[home_key],"away":r[away_key]})
      continue
     if len(options)!=1:n["ambiguous"]+=1;continue
     h=options[0]
     # Full-time goals are a mandatory cross-source identity check.
     home_goal_key=next((k for k in ("home_goals","fthg","FTHG") if k in r),None)
     away_goal_key=next((k for k in ("away_goals","ftag","FTAG") if k in r),None)
     if not home_goal_key or not away_goal_key:
      n["score_schema_unmapped"]+=1;continue
     try:
      if int(r[home_goal_key])!=int(h["home_goals"]) or int(r[away_goal_key])!=int(h["away_goals"]):
       n["score_mismatch"]+=1;continue
     except (ValueError,TypeError):n["score_mismatch"]+=1;continue
     try:
      if int(r["home_corners"])!=int(h["home_corners"]) or int(r["away_corners"])!=int(h["away_corners"]):n["invalid"]+=1;continue
     except (ValueError,TypeError):n["invalid"]+=1;continue
     n["matched"]+=1
  except Exception as exc:n["source_error"]+=1;report.setdefault("source_errors",{})[league]=str(exc)[:180]
  report["by_league"].append({"league":league,**n})
  for key in ("matched","unmatched","ambiguous","invalid","score_mismatch","score_schema_unmapped","schema_unmapped","source_error","missing_corner_fields"):report[key]=report.get(key,0)+n[key]
 P.joinpath("first_half_corner_match_pilot.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({k:report.get(k,0) for k in ("matched","unmatched","ambiguous","invalid","score_mismatch","score_schema_unmapped","schema_unmapped","source_error","missing_corner_fields")},ensure_ascii=False))
if __name__=="__main__":main()
