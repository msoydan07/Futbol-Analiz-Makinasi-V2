"""Single postmatch acceptance gate for a NEW SHA-sealed 2.6.3 fixture.

A one-time, non-retroactive result record: either one trusted official
league/federation/registered-club observation, or matching reports from two
separately registered publishers. The observation producer MUST have fetched
and parsed a live source; claims in JSON are not, by themselves, an HTTP proof.
No model fitting, odds, historical data edits or fabricated human attestation.
"""
from __future__ import annotations
import hashlib,json,re
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import urlsplit

ARCHIVE="data/results_only_263/accepted_forward_263"
SCHEMA="263_ONEPASS_NEW100_FINAL_SCORE_V1"
OBS="263_LIVE_RESULT_OBSERVATION_V1"
LEAGUE_DOMAINS={
 "ENG1":{"premierleague.com"},"ENG2":{"efl.com"},
 "GER1":{"bundesliga.com"},"ESP1":{"laliga.com"},
 "ITA1":{"legaseriea.it"},"FRA1":{"ligue1.com"},
 "NED1":{"eredivisie.nl"},"TUR1":{"tff.org"},
 "POR1":{"ligaportugal.pt"},"BEL1":{"proleague.be"}}
SECONDARY_PUBLISHERS={
 "football-data.co.uk":"football-data",
 "espn.com":"espn",
 "sofascore.com":"sofascore",
 "fotmob.com":"fotmob"}
STATES={"FULL_TIME","POSTPONED"}
HEX=re.compile(r"[0-9a-f]{64}\Z")
class Reject(ValueError):pass

def fingerprint(payload):
 return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,
                          separators=(",",":"),allow_nan=False).encode()).hexdigest()

def aware(s):
 try:d=datetime.fromisoformat(s.replace("Z","+00:00"))
 except (ValueError,AttributeError):raise Reject("INVALID_TIMESTAMP")
 if d.tzinfo is None:raise Reject("TIMEZONE_REQUIRED")
 return d.astimezone(timezone.utc)

def verify_forecast(f):
 if f.get("schema")!="quad_forward_263_v1":raise Reject("WRONG_FORECAST_SCHEMA")
 sha=f.get("payload_sha256")
 if not isinstance(sha,str) or not HEX.fullmatch(sha):raise Reject("BAD_FORECAST_SHA")
 if fingerprint({k:v for k,v in f.items() if k!="payload_sha256"})!=sha:
  raise Reject("FORECAST_SHA_TAMPERED")
 x=f["fixture"];league=x["league"]
 if league not in LEAGUE_DOMAINS or x.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE":
  raise Reject("UNVERIFIED_PREMATCH_FIXTURE")
 made,checked,ko=(aware(f["created_at_utc"]),aware(x["source_checked_at_utc"]),
                  aware(x["kickoff_utc"]))
 if not(made<ko and checked<ko and checked<=made+timedelta(seconds=60)):
  raise Reject("NOT_AUTHENTIC_PRE_KO_SEAL")
 if ko.astimezone(timezone(timedelta(hours=3))).date().isoformat()!=x["match_local_date"]:
  raise Reject("FIXTURE_LOCAL_DATE_INVALID")
 return sha,ko,x

def host(url):
 if not isinstance(url,str):raise Reject("SOURCE_URL_NOT_STRING")
 u=urlsplit(url);h=(u.hostname or "").lower()
 if (u.scheme!="https" or u.username or u.password or u.port or
     u.fragment or not h or h.replace(".","").isdigit()):
  raise Reject("UNTRUSTED_SOURCE_URL")
 return h.removeprefix("www.")

def normalize_observation(o,sha,ko,fixture,now,club_hosts):
 if not isinstance(o,dict) or o.get("schema")!=OBS:
  raise Reject("UNVERIFIED_SOURCE_OBSERVATION_SCHEMA")
 if o.get("capture_mode")!="LIVE_PARSED_SCORE_ADAPTER":
  raise Reject("WEB_LINK_CLAIM_NOT_LIVE_SOURCE_EVIDENCE")
 for field in ("forecast_sha256","league","home_id","away_id","kickoff_utc"):
  expected=sha if field=="forecast_sha256" else fixture[field]
  if o.get(field)!=expected:raise Reject("WRONG_MATCH_OR_SHA_SOURCE_IDENTITY")
 checked=aware(o.get("checked_at_utc"))
 if checked>now or checked<ko+timedelta(minutes=105):
  raise Reject("NOT_FINAL_TIME_OR_FUTURE_CHECK")
 state=o.get("match_state")
 if state not in STATES:raise Reject("NOT_FULL_TIME_OR_POSTPONED")
 score=o.get("score")
 if state=="FULL_TIME":
  if not (o.get("score_scope")=="90MIN_FT" and isinstance(score,list)
          and len(score)==2 and all(type(v) is int and 0<=v<=20 for v in score)):
   raise Reject("INVALID_REGULATION_TIME_SCORE")
 elif score is not None:raise Reject("POSTPONED_CANNOT_HAVE_SCORE")
 url=o.get("source_url");domain=host(url);kind=o.get("source_kind")
 if not isinstance(o.get("response_sha256"),str) or not HEX.fullmatch(o["response_sha256"]):
  raise Reject("NO_CAPTURED_SOURCE_BODY_HASH")
 if not isinstance(o.get("source_event_id"),str) or not o["source_event_id"].strip():
  raise Reject("NO_EXACT_PROVIDER_EVENT_ID")
 league=fixture["league"]
 if kind in ("OFFICIAL_LEAGUE","OFFICIAL_FEDERATION"):
  if domain not in LEAGUE_DOMAINS[league]:raise Reject("WRONG_OFFICIAL_LEAGUE_HOST")
  publisher="OFFICIAL:"+league;upstream=publisher;official=True
 elif kind=="OFFICIAL_CLUB":
  owner=club_hosts.get((league,domain))
  if owner not in (fixture["home_id"],fixture["away_id"]):
   raise Reject("CLUB_HOST_NOT_CURATED_FOR_THIS_TEAM")
  publisher="CLUB:"+domain;upstream=publisher;official=True
 elif kind=="SECONDARY":
  publisher=SECONDARY_PUBLISHERS.get(domain)
  if not publisher:raise Reject("UNREGISTERED_SECONDARY_PROVIDER")
  # Externally curated upstream lineage is needed where a feed's actual
  # origin is known; same feed may be republished under different domains.
  upstream=o.get("upstream_owner")
  if not isinstance(upstream,str) or not upstream.strip():
   raise Reject("UNKNOWN_SECONDARY_UPSTREAM")
  official=False
 else:raise Reject("UNKNOWN_SOURCE_KIND")
 return {"source_url":url,"publisher":publisher,"upstream":upstream,
         "official":official,"kind":kind,"score":score,"state":state,
         "checked_at_utc":checked.isoformat(),"source_event_id":o["source_event_id"],
         "response_sha256":o["response_sha256"]}

def decide(forecast,observations,*,now=None,club_hosts=None):
 now=now or datetime.now(timezone.utc)
 if now.tzinfo is None:raise Reject("NOW_REQUIRES_TIMEZONE")
 now=now.astimezone(timezone.utc)
 sha,ko,x=verify_forecast(forecast)
 if not isinstance(observations,list):raise Reject("OBSERVATIONS_NOT_LIST")
 parsed=[normalize_observation(o,sha,ko,x,now,club_hosts or {})
         for o in observations]
 if not parsed:return {"status":"HOLD_NO_FINAL_SOURCE","forecast_sha256":sha}
 seen=set()
 for p in parsed:
  pair=(p["publisher"],p["source_event_id"])
  if pair in seen:raise Reject("DUPLICATE_SOURCE_OBSERVATION")
  seen.add(pair)
 states={p["state"] for p in parsed}
 scores={tuple(p["score"]) for p in parsed if p["score"] is not None}
 if len(states)!=1 or len(scores)>1:
  return {"status":"HOLD_SCORE_OR_STATUS_CONFLICT","forecast_sha256":sha}
 official=[p for p in parsed if p["official"]]
 if official:
  trusted=official[:1];grade="OFFICIAL_LEAGUE_OR_CLUB"
 else:
  # Two distinct publishers AND upstream families; no duplicate websites,
  # syndication mirrors or two pages from the same provider.
  trusted=[]
  for p in parsed:
   if any(p["publisher"]==z["publisher"] or p["upstream"]==z["upstream"]
          for z in trusted):continue
   trusted.append(p)
   if len(trusted)==2:break
  if len(trusted)<2:
   return {"status":"HOLD_NEED_INDEPENDENT_SECOND_SOURCE","forecast_sha256":sha}
  grade="TWO_INDEPENDENT_PUBLISHER_SOURCES"
 state=next(iter(states))
 if state=="FULL_TIME":score=list(next(iter(scores)));status="ACCEPTED_FULL_TIME"
 else:score=None;status="ACCEPTED_POSTPONED_NO_SCORE"
 evidence=[{k:p[k] for k in ("source_url","publisher","upstream",
                              "kind","source_event_id","response_sha256","checked_at_utc")}
           for p in trusted]
 return {"schema":SCHEMA,"status":status,"source_grade":grade,
   "cohort":"new100","forecast_sha256":sha,"league":x["league"],
   "home_id":x["home_id"],"away_id":x["away_id"],
   "kickoff_utc":x["kickoff_utc"],"match_date":x["match_local_date"],
   "score":score,"source_evidence":evidence,"human_attestation":False,
   "source_scope":"LIVE_PARSED_ADAPTER_OBSERVATIONS_NOT_HUMAN_ATTESTATION",
   "models_modified":False}

def path_for(root,forecast):
 sha,ko,x=verify_forecast(forecast)
 return Path(root)/ARCHIVE/x["match_local_date"]/(sha+".json")

def read_once(root,forecast):
 path=path_for(root,forecast)
 if not path.exists():return None
 d=json.loads(path.read_text(encoding="utf-8"))
 checksum=d.get("archive_sha256")
 if not isinstance(checksum,str) or checksum!=fingerprint({k:v for k,v in d.items() if k!="archive_sha256"}):
  raise Reject("ARCHIVED_RECORD_SHA_TAMPERED")
 sha,ko,x=verify_forecast(forecast)
 for key,value in (("schema",SCHEMA),("forecast_sha256",sha),("league",x["league"]),
                   ("home_id",x["home_id"]),("away_id",x["away_id"]),
                   ("kickoff_utc",x["kickoff_utc"]),("match_date",x["match_local_date"])):
  if d.get(key)!=value:raise Reject("ARCHIVED_MATCH_IDENTITY_TAMPERED")
 if d.get("status") not in ("ACCEPTED_FULL_TIME","ACCEPTED_POSTPONED_NO_SCORE"):
  raise Reject("ARCHIVED_STATUS_INVALID")
 if d.get("status")=="ACCEPTED_FULL_TIME":
  if not (isinstance(d.get("score"),list) and len(d["score"])==2
          and all(type(v) is int and 0<=v<=20 for v in d["score"])):
   raise Reject("ARCHIVED_FINAL_SCORE_INVALID")
 elif d.get("score") is not None:raise Reject("ARCHIVED_POSTPONED_SCORE_INVALID")
 if d.get("source_grade") not in ("OFFICIAL_LEAGUE_OR_CLUB","TWO_INDEPENDENT_PUBLISHER_SOURCES"):
  raise Reject("ARCHIVED_UNAPPROVED_SOURCE_GRADE")
 if d.get("human_attestation") is not False or d.get("models_modified") is not False:
  raise Reject("ARCHIVED_EVIDENCE_PROMOTION_INVALID")
 if not isinstance(d.get("source_evidence"),list) or not d["source_evidence"]:
  raise Reject("ARCHIVED_EVIDENCE_MISSING")
 return d

def archive_once(root,forecast,observations,*,now=None,club_hosts=None):
 # Idempotent: never query any source if this forecast SHA has been closed.
 previous=read_once(root,forecast)
 if previous is not None:return previous
 decision=decide(forecast,observations,now=now,club_hosts=club_hosts)
 if not decision["status"].startswith("ACCEPTED_"):return decision
 path=path_for(root,forecast);path.parent.mkdir(parents=True,exist_ok=True)
 d={**decision,"archive_sha256":fingerprint(decision)}
 try:
  with path.open("x",encoding="utf-8") as f:
   json.dump(d,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
   f.write("\n")
 except FileExistsError:
  return read_once(root,forecast)
 return read_once(root,forecast)
