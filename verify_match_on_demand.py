"""Stage 5: on-demand official fixture verification, maximum 7 days ahead.

Do not fetch season-long feeds, fabricate match dates, or calculate predictions.
An official-source observation is accepted only after its source is actually checked.
"""
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
from identity import Registry
from official_fixture_source_policy import OFFICIAL

def verify_requested_fixture(league,home,away,kickoff_iso,source_url,retrieved_at_iso,now=None,source_checked=False,registry_path="data/match_registry.json"):
 now=now or datetime.now(timezone.utc)
 if league not in OFFICIAL:return {"status":"REJECTED","reason":"unsupported_league"}
 if not source_checked:return {"status":"NOT_VERIFIED","reason":"official_source_not_checked"}
 try:
  from urllib.parse import urlparse
  expected=urlparse(OFFICIAL[league]["url"]).hostname
  actual=urlparse(source_url).hostname
  if not actual or not expected or not (actual==expected or actual.endswith("."+expected)):
   return {"status":"REJECTED","reason":"not_registered_official_domain"}
  kickoff=datetime.fromisoformat(kickoff_iso.replace("Z","+00:00"))
  retrieved=datetime.fromisoformat(retrieved_at_iso.replace("Z","+00:00"))
  if kickoff.tzinfo is None or retrieved.tzinfo is None:raise ValueError("timezone_missing")
  kickoff=kickoff.astimezone(timezone.utc)
  retrieved=retrieved.astimezone(timezone.utc)
  if retrieved>now+timedelta(minutes=5) or now-retrieved>timedelta(hours=24):
   return {"status":"NOT_VERIFIED","reason":"source_timestamp_not_fresh"}
  if not now<=kickoff<=now+timedelta(days=7):
   return {"status":"OUTSIDE_WINDOW","reason":"not_within_next_7_days"}
  reg=Registry(registry_path)
  home_id=reg.resolve_team(home);away_id=reg.resolve_team(away)
  if home_id==away_id:raise ValueError("same_team")
  return {"status":"VERIFIED","league":league,"home_id":home_id,"away_id":away_id,"kickoff_utc":kickoff.isoformat(),"kickoff_turkey":kickoff.astimezone(ZoneInfo("Europe/Istanbul")).isoformat(),"source_url":source_url,"retrieved_at_utc":retrieved.isoformat()}
 except (KeyError,ValueError,TypeError) as e:
  return {"status":"REVIEW_REQUIRED","reason":str(e)}

# The caller must actually fetch the official source and confirm the fixture.
# source_checked=True is an explicit trusted integration assertion, never inferred from a URL.

def match_unplayed_candidate(league, home, away, candidates_path="data/unplayed_fixture_candidates.csv", season="2026-2027"):
 """Find the requested pairing in the existing unplayed list; date is NOT required to match."""
 import csv
 from pathlib import Path
 p=Path(candidates_path)
 if not p.is_file():
  return {"status":"LIST_UNAVAILABLE","path":str(p)}
 from identity import normalize
 with p.open(encoding="utf-8-sig",newline="") as f:
  rows=list(csv.DictReader(f))
 hits=[r for r in rows if r.get("league")==league and r.get("season")==season
       and r.get("classification")=="FUTURE_CANDIDATE"
       and normalize(r.get("home",""))==normalize(home)
       and normalize(r.get("away",""))==normalize(away)]
 if not hits:return {"status":"NOT_IN_LIST"}
 if len(hits)!=1:return {"status":"AMBIGUOUS","count":len(hits)}
 return {"status":"MATCHED_UNPLAYED","league":league,"season":season,"home":hits[0]["home"],"away":hits[0]["away"]}

def verify_listed_match(league,home,away,kickoff_iso,source_url,retrieved_at_iso,now=None,
                        source_checked=False,candidates_path="data/unplayed_fixture_candidates.csv",
                        registry_path="data/match_registry.json"):
 """One requested match: unplayed pair first, official kickoff second. No date equality gate."""
 listed=match_unplayed_candidate(league,home,away,candidates_path)
 if listed["status"]!="MATCHED_UNPLAYED":return listed
 checked=verify_requested_fixture(league,home,away,kickoff_iso,source_url,retrieved_at_iso,
                                  now=now,source_checked=source_checked,registry_path=registry_path)
 if checked["status"]=="VERIFIED":
  checked["unplayed_list_match"]=True
 return checked
