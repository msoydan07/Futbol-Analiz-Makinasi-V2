"""Connect official named-match gate to Model B without bypassing verification."""
import csv,json,sys
from pathlib import Path
from datetime import datetime
from analyze_named_match_gate import run as verify
from single_match_model_b import analyze

def run(league,home,away,lookup_override=None,registry_path="data/match_registry.json",history_path="data/historical_results.csv"):
 checked=verify(league,home,away,lookup_override=lookup_override,registry_path=registry_path)
 if checked.get("status")!="VERIFIED":
  return {"status":"NOT_ANALYZED","fixture_verification":checked,"reason":"fixture_not_verified"}
 try:
  with Path(history_path).open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
  day=datetime.fromisoformat(checked["kickoff_utc"]).date().isoformat()
  result=analyze(rows,league,checked["home_id"],checked["away_id"],day)
 except (OSError,KeyError,ValueError) as exc:
  return {"status":"DATA_AUDIT_REQUIRED","fixture_verification":checked,"reason":str(exc)[:180]}
 result["fixture_verified"]=True
 result["fixture_verification"]={k:checked[k] for k in ("status","league","home_id","away_id","kickoff_utc","source_url","retrieved_at_utc") if k in checked}
 result["fixture"]["home_name"]=home
 result["fixture"]["away_name"]=away
 result["status"]="ANALYZED_EXPERIMENTAL" if result["status"]=="READY" else "INSUFFICIENT_HISTORY"
 return result

if __name__=="__main__":
 if len(sys.argv)!=4:raise SystemExit("Usage: python analyze_verified_match.py LEAGUE HOME AWAY")
 print(json.dumps(run(*sys.argv[1:]),ensure_ascii=False,indent=2))
