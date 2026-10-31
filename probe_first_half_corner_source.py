"""Read-only first-half corners source probe; never joins by fuzzy name or changes predictions."""
import csv,io,json,urllib.request
from collections import Counter
from pathlib import Path
FOLDERS={"ENG1":"ENG_1_premier-league","ENG2":"ENG_2_championship","GER1":"GER_1_bundesliga","ESP1":"ESP_1_la-liga","ITA1":"ITA_1_serie-a","FRA1":"FRA_1_ligue-1","NED1":"NED_1_eredivisie","TUR1":"TUR_1_super-lig","POR1":"POR_1_primeira-liga","BEL1":"BEL_1_pro-league"}
BASE="https://raw.githubusercontent.com/oladeeayo/open-matchday/master/data"
def main():
 report={"source":"open-matchday","source_terms":"noncommercial informational use; upstream terms also apply","season":"2026-2027","read_only":True,"leagues":[],"accepted_rows":0,"warning":"No fixture joins; dates/team names/source rights not yet independently validated"}
 for league,folder in FOLDERS.items():
  url=f"{BASE}/{folder}/results_2627.csv"
  entry={"league":league,"url":url,"status":"UNAVAILABLE","total":0,"complete_splits":0,"valid_splits":0,"invalid_splits":0}
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"FutbolAnalizV2/1.0"})
   with urllib.request.urlopen(req,timeout=20) as f:rows=list(csv.DictReader(io.StringIO(f.read().decode("utf-8-sig"))))
   entry["status"]="OK";entry["total"]=len(rows)
   for r in rows:
    names=("home_corners_1h","away_corners_1h","home_corners_2h","away_corners_2h","home_corners","away_corners")
    if not all((r.get(k) or "").strip() for k in names):continue
    entry["complete_splits"]+=1
    try:
     a,b,c,d,h,aw=[int(r[k]) for k in names]
     if min(a,b,c,d,h,aw)<0 or a+c!=h or b+d!=aw:raise ValueError("split mismatch")
     entry["valid_splits"]+=1
    except (ValueError,TypeError):entry["invalid_splits"]+=1
  except Exception as exc:entry["error"]=str(exc)[:180]
  report["leagues"].append(entry)
 report["total_valid_split_rows"]=sum(x["valid_splits"] for x in report["leagues"])
 Path("data").mkdir(exist_ok=True)
 Path("data/first_half_corner_source_probe.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"leagues_ok":sum(x["status"]=="OK" for x in report["leagues"]),"valid_split_rows":report["total_valid_split_rows"],"invalid_split_rows":sum(x["invalid_splits"] for x in report["leagues"])},ensure_ascii=False))
if __name__=="__main__":main()
