"""Validate official future fixtures against historical registry; no guessed matches or times.
Input CSV columns: league,season,home,away,kickoff_iso,source_url,retrieved_at_utc.
kickoff_iso must carry a UTC offset. Official site observations only.
"""
import csv,json,sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from identity import Registry
from official_fixture_source_policy import OFFICIAL
def dt(s):
 d=datetime.fromisoformat(s.replace("Z","+00:00"))
 if d.tzinfo is None or d.utcoffset() is None:raise ValueError("timezone_required")
 return d
def validate(rows,registry,now=None):
 now=now or datetime.now(timezone.utc)
 historical=registry.data.get("fixtures",{})
 out=[];errors=[];seen=set()
 for index,r in enumerate(rows,start=2):
  try:
   league=r["league"].strip();season=r["season"].strip()
   if league not in OFFICIAL:raise ValueError("unsupported_league")
   if season!="2026-2027":raise ValueError("unsupported_season")
   source=r["source_url"].strip()
   from urllib.parse import urlparse
   if not source.startswith("https://") or not urlparse(source).hostname:raise ValueError("official_evidence_url_required")
   kickoff=dt(r["kickoff_iso"].strip()).astimezone(timezone.utc)
   retrieved=dt(r["retrieved_at_utc"].strip()).astimezone(timezone.utc)
   if retrieved>now+timedelta(minutes=5):raise ValueError("future_retrieval_timestamp")
   if not now<=kickoff<=now+timedelta(days=7):raise ValueError("outside_next_7_days")
   home=registry.resolve_team(r["home"].strip());away=registry.resolve_team(r["away"].strip())
   if home==away:raise ValueError("same_team")
   key=(league,season,home,away)
   if key in seen:raise ValueError("duplicate_pair_in_snapshot")
   seen.add(key)
   matches=[fid for fid,f in historical.items() if (f.get("league"),f.get("season"),f.get("home_id"),f.get("away_id"))==key]
   if len(matches)>1:raise ValueError("ambiguous_repeated_pair")
   # Completed historical fixtures are not future fixtures.
   if matches and historical[matches[0]].get("match_date","")<now.date().isoformat():
    raise ValueError("historical_completed_or_past_fixture_conflict")
   out.append({"league":league,"season":season,"home_id":home,"away_id":away,"existing_fixture_id":matches[0] if matches else None,"status":"MATCHED_UNPLAYED" if matches else "NEW_OFFICIAL_CANDIDATE","kickoff_utc":kickoff.isoformat(),"kickoff_turkey":kickoff.astimezone(ZoneInfo("Europe/Istanbul")).isoformat(),"source_url":source,"retrieved_at_utc":retrieved.isoformat()})
  except (KeyError,ValueError,TypeError) as exc:
   errors.append({"row":index,"reason":str(exc)})
 return out,errors
def main():
 path=Path(sys.argv[1]) if len(sys.argv)>1 else Path("data/official_future_fixture_observations.csv")
 if not path.exists():
  print(json.dumps({"status":"AWAITING_OFFICIAL_OBSERVATIONS","path":str(path),"imported":0}));return
 with path.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
 out,errors=validate(rows,Registry("data/match_registry.json"))
 report={"status":"REVIEW_REQUIRED" if errors else "OBSERVATIONS_VALIDATED_NOT_COMPLETENESS_CERTIFIED","imported":len(out),"errors":errors,"records":out,"official_coverage_by_league":{l:sum(r["league"]==l for r in out) for l in OFFICIAL},"source_completeness_verified":False,"note":"Input source URL is a claim requiring official-source review; this validator does not fetch the URL."}
 Path("data/official_future_fixture_import_audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"imported":len(out),"errors":len(errors)},ensure_ascii=False))
 if errors:raise SystemExit(1)
if __name__=="__main__":main()
