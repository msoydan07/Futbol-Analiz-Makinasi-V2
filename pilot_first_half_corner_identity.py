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
  if name:
   base[(r["league"],r["match_date"],name["home"].casefold().strip(),name["away"].casefold().strip())].append(r)
 report={"source":"open-matchday","read_only":True,"matched":0,"unmatched":0,"ambiguous":0,"invalid":0,"sample_source_columns":{},"by_league":[],"rule":"Only exact verified team/date/score + whole-match corner agreement; no fuzzy joins; no database writes"}
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
     vals=("home_corners_1h","away_corners_1h","home_corners","away_corners")
     if not all((r.get(v) or "").strip() for v in vals):continue
     date=r[date_key][:10]
     options=base.get((league,date,r[home_key].casefold().strip(),r[away_key].casefold().strip()),[])
     if not options:n["unmatched"]+=1;continue
     if len(options)!=1:n["ambiguous"]+=1;continue
     h=options[0]
     try:
      if int(r["home_corners"])!=int(h["home_corners"]) or int(r["away_corners"])!=int(h["away_corners"]):n["invalid"]+=1;continue
     except (ValueError,TypeError):n["invalid"]+=1;continue
     n["matched"]+=1
  except Exception as exc:n["source_error"]+=1;report.setdefault("source_errors",{})[league]=str(exc)[:180]
  report["by_league"].append({"league":league,**n})
  for key in ("matched","unmatched","ambiguous","invalid"):report[key]+=n[key]
 P.joinpath("first_half_corner_match_pilot.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({k:report[k] for k in ("matched","unmatched","ambiguous","invalid")},ensure_ascii=False))
if __name__=="__main__":main()
