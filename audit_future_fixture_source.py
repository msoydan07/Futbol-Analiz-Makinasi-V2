"""Audit upcoming source fixture coverage without guessing kickoff time zones or team IDs."""
import csv,io,json,urllib.request
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path
from collect_team_candidates import LEAGUES
from identity import Registry
URL="https://www.football-data.co.uk/fixtures.csv"
def _valid_date(value,fmt):
 try: datetime.strptime(value,fmt);return True
 except ValueError:return False
def main():
 now=datetime.now(timezone.utc)
 req=urllib.request.Request(URL,headers={"User-Agent":"FutbolAnalizV2/1.0","Cache-Control":"no-cache"})
 with urllib.request.urlopen(req,timeout=30) as response:
  raw=response.read().decode("utf-8-sig",errors="replace")
 rows=list(csv.DictReader(io.StringIO(raw)))
 if not rows or not {"Div","Date","HomeTeam","AwayTeam"}.issubset(rows[0]):
  raise ValueError("Unexpected future fixture CSV schema")
 registry=Registry("data/match_registry.json")
 inverse={v:k for k,v in LEAGUES.items()}
 found=[];issues=[];coverage=Counter()
 for idx,r in enumerate(rows,start=2):
  code=(r.get("Div") or "").strip()
  if code not in inverse:continue
  league=inverse[code]
  try:
   date=next((datetime.strptime((r.get("Date") or "").strip(),fmt).date() for fmt in ("%d/%m/%Y","%d/%m/%y") if _valid_date((r.get("Date") or "").strip(),fmt)),None)
   if date is None: raise ValueError("invalid date")
  except ValueError:
   issues.append({"row":idx,"league":league,"reason":"invalid_date"});continue
  if not now.date()<=date<=now.date()+timedelta(days=7):continue
  home=(r.get("HomeTeam") or "").strip();away=(r.get("AwayTeam") or "").strip()
  try:
   hid=registry.resolve_team(home);aid=registry.resolve_team(away)
  except KeyError:
   issues.append({"row":idx,"league":league,"home":home,"away":away,"reason":"unmapped_team"});continue
  t=(r.get("Time") or "").strip()
  # Football-Data's fixture time zone is not asserted by its CSV schema.
  found.append({"league":league,"date":date.isoformat(),"source_time_unconverted":t,"kickoff_utc":None,"kickoff_turkey":None,"time_zone_status":"UNVERIFIED","home_id":hid,"away_id":aid,"home":home,"away":away,"source_url":URL,"retrieved_at_utc":now.isoformat(),"source_row":idx})
  coverage[league]+=1
 keys=[(r["league"],r["date"],r["home_id"],r["away_id"]) for r in found]
 duplicates=len(keys)-len(set(keys))
 report={"source":URL,"retrieved_at_utc":now.isoformat(),"source_rows":len(rows),"window_start_utc_date":now.date().isoformat(),"window_end_utc_date":(now.date()+timedelta(days=7)).isoformat(),"mapped_rows":len(found),"league_coverage":dict(coverage),"unmapped_or_invalid":issues,"duplicate_count":duplicates,"source_is_weekly_snapshot_not_guaranteed_7_day_complete":True,"kickoff_timezone_verified":False,"official_second_source_verified":False,"stage_5_accepted":False,"note":"Fixture time cannot be converted to UTC/TR without source timezone verification. Source may omit midweek or distant games."}
 p=Path("data");p.mkdir(exist_ok=True)
 (p/"future_fixture_source_audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 with (p/"future_fixture_candidates.json").open("w",encoding="utf-8") as f:json.dump(found,f,ensure_ascii=False,indent=2)
 print(json.dumps({"source_rows":len(rows),"mapped_rows":len(found),"league_coverage":dict(coverage),"issues":len(issues),"duplicates":duplicates,"stage_5_accepted":False},ensure_ascii=False))
if __name__=="__main__":main()
