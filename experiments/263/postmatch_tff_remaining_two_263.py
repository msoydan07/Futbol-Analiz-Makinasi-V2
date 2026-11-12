"""Pinned official TFF results for two existing November 8 SHA-sealed games.
Research-only: no model, price, historical archive, human attestation or seal writes.
"""
from __future__ import annotations
import re,hashlib,urllib.request
from datetime import datetime,timezone,timedelta
from urllib.parse import urlsplit,parse_qs
from postmatch_tff_one_match_263 import Visible

MAX_BYTES=2_000_000
PINS={
 "daa0d85a5e4e120e3420d35f4546c2f0d6699843cf3248c8aac9a7caf767d59a":{
  "id":"317877","home":"Çaykur Rizespor","away":"Erzurumspor FK",
  "hid":"010ec376-a0df-50e7-a57c-f5850f660053",
  "aid":"08d3f80d-eb65-50ac-9dd4-e49110a61a82",
  "ko":"2026-11-08T10:30:00+00:00","clock":"13:30","score":[2,1],
  "re":r"ÇAYKUR\s+RİZESPOR\s+A\.Ş\.\s+(?P<h>\d{1,2})\s+ERZURUMSPOR\s+FK\s+(?P<a>\d{1,2})(?!\d)"},
 "f3e5e938f2d2a84fa186f3293582ce803e2db27837899c581d6225be3d6ead81":{
  "id":"317881","home":"Beşiktaş","away":"Gençlerbirliği",
  "hid":"4e0b2072-7256-59f1-a14a-1be0aa41827c",
  "aid":"bf0f8601-77e0-528f-ac2a-5d384a7081c5",
  "ko":"2026-11-08T18:00:00+00:00","clock":"21:00","score":[3,0],
  "re":r"BEŞİKTAŞ\s+A\.Ş\.\s+(?P<h>\d{1,2})\s+GENÇLERBİRLİĞİ\s+(?P<a>\d{1,2})(?!\d)"}}
class Blocked(ValueError):pass

def url_for(pin):
 if pin not in PINS:raise Blocked("UNPINNED_SHA_FORBIDDEN")
 return "https://www.tff.org/Default.aspx?macId="+PINS[pin]["id"]+"&pageId=29"

def download(url,match_id):
 req=urllib.request.Request(url,headers={"User-Agent":"263PinnedTFFScoreAudit/1.0"})
 with urllib.request.urlopen(req,timeout=15) as response:
  u=urlsplit(response.geturl())
  q={k.casefold():v for k,v in parse_qs(u.query).items()}
  if (u.scheme!="https" or u.hostname!="www.tff.org" or
      u.port is not None or u.username or u.password or
      u.path.casefold()!="/default.aspx" or
      q!={"macid":[match_id],"pageid":["29"]}):
   raise Blocked("TFF_SOURCE_REDIRECT_UNTRUSTED")
  raw=response.read(MAX_BYTES+1)
 if len(raw)>MAX_BYTES:raise Blocked("TFF_SOURCE_TOO_LARGE")
 return raw

def parse_pinned(raw,pin):
 if pin not in PINS:raise Blocked("UNPINNED_SHA_FORBIDDEN")
 if not isinstance(raw,(bytes,str)) or len(raw)>MAX_BYTES:raise Blocked("INVALID_TFF_HTML")
 if isinstance(raw,bytes):
  decoded=None
  for encoding in ("utf-8-sig","cp1254","iso8859-9"):
   try:decoded=raw.decode(encoding);break
   except UnicodeDecodeError:pass
  if decoded is None:raise Blocked("TFF_DECODE_FAILED")
 else:decoded=raw
 vis=Visible();vis.feed(decoded)
 flat=" ".join(" ".join(vis.parts).split()).replace("\xa0"," ")
 cfg=PINS[pin]
 if not re.search(r"Trendyol\s+Süper\s+Lig",flat,re.I):raise Blocked("WRONG_TFF_COMPETITION")
 if not re.search(r"(?<!\d)8\.11\.2026\s*-\s*"+re.escape(cfg["clock"])+r"(?!\d)",flat):
  raise Blocked("WRONG_TFF_KICKOFF")
 matches=list(re.finditer(cfg["re"],flat,re.I))
 scores={(int(m["h"]),int(m["a"])) for m in matches}
 if len(scores)!=1 or len(matches)>2:raise Blocked("TFF_SCORE_NOT_UNIQUE")
 score=list(next(iter(scores)))
 if max(score)>20 or score!=cfg["score"]:raise Blocked("TFF_SCORE_CONFLICT")
 return score

def verify_two(forecast,registered,*,now=None,fetcher=None):
 now=now or datetime.now(timezone.utc)
 if now.tzinfo is None:raise Blocked("AWARE_CLOCK_REQUIRED")
 pin=forecast.get("payload_sha256")
 if pin not in PINS:raise Blocked("UNPINNED_SHA_FORBIDDEN")
 cfg=PINS[pin];fixture=forecast.get("fixture",{})
 if (forecast.get("schema")!="quad_forward_263_v1" or
     fixture.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE" or
     fixture.get("league")!="TUR1" or fixture.get("match_local_date")!="2026-11-08" or
     fixture.get("home_id")!=cfg["hid"] or fixture.get("away_id")!=cfg["aid"] or
     fixture.get("kickoff_utc")!=cfg["ko"] or
     registered.get("forecast_sha256")!=pin or
     registered.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL" or
     registered.get("home")!=cfg["home"] or registered.get("away")!=cfg["away"]):
  raise Blocked("PINNED_FORECAST_IDENTITY_MISMATCH")
 if now.astimezone(timezone.utc)<datetime.fromisoformat(cfg["ko"])+timedelta(hours=4):
  raise Blocked("SCORE_CHECK_TOO_EARLY")
 url=url_for(pin)
 raw=fetcher(url) if fetcher is not None else download(url,cfg["id"])
 score=parse_pinned(raw,pin)
 raw_bytes=raw if isinstance(raw,bytes) else raw.encode("utf-8")
 return {"status":"OFFICIAL_TFF_PUBLIC_PAGE_NETWORK_CHECK_RESEARCH_ONLY",
  "forecast_sha256":pin,"league":"TUR1","match_date":"2026-11-08",
  "kickoff_utc":cfg["ko"],"source_url":url,
  "source_sha256":hashlib.sha256(raw_bytes).hexdigest(),
  "score":score,"federation_page_read":True,"human_attestation_written":False,
  "original_forecast_modified":False}

