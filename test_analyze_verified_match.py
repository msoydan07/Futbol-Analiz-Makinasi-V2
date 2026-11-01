"""Deterministic integration gate checks; no fabricated official lookup in production."""
import csv,tempfile
from pathlib import Path
from datetime import datetime,timedelta,timezone
from identity import Registry
from analyze_verified_match import run

def main():
 with tempfile.TemporaryDirectory() as d:
  registry=Path(d)/"registry.json";history=Path(d)/"history.csv"
  reg=Registry(registry);h=reg.register_team("home","Home");a=reg.register_team("away","Away");reg.save()
  with history.open("w",newline="") as f:
   w=csv.DictWriter(f,fieldnames=["fixture_id","league","match_date","home_id","away_id","home_goals","away_goals","result"]);w.writeheader()
   for i in range(40):
    w.writerow({"fixture_id":str(i),"league":"ENG1","match_date":"2025-01-%02d"%(i%28+1),"home_id":h if i%2==0 else a,"away_id":a if i%2==0 else h,"home_goals":2,"away_goals":1,"result":"H"})
  now=datetime.now(timezone.utc)
  observation={"status":"VERIFIED_OFFICIAL_FIXTURE","home":"Home","away":"Away","kickoff_utc":(now+timedelta(days=1)).isoformat(),"source_url":"https://www.premierleague.com/en/fixtures","retrieved_at_utc":now.isoformat()}
  kw={"registry_path":str(registry),"history_path":str(history)}
  assert run("ENG1","Home","Away",lookup_override=lambda *_:{"status":"NOT_VERIFIED"},**kw)["status"]=="NOT_ANALYZED"
  assert run("ENG1","Home","Away",lookup_override=lambda *_:dict(observation,away="Other"),**kw)["status"]=="NOT_ANALYZED"
  result=run("ENG1","Home","Away",lookup_override=lambda *_:observation,**kw)
  assert result["status"]=="ANALYZED_EXPERIMENTAL",result
  assert result["fixture_verified"] is True
  assert result["model"]["markets"]["1x2"]
  assert result["lineup_status"]=="NOT_CHECKED_NOT_BLOCKING"
  print("verified_match_integration_smoke_pass")
if __name__=="__main__":main()
