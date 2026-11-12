"""Exact, independent TFF result-page research for ONE missing Nov-8 new100 game.

No new prediction, no archive rewrite, no human attestation, no prices.
Only previously SHA-locked Corum-Fenerbahce fixture/match-id 317879 qualifies.
"""
from __future__ import annotations
import hashlib,re,urllib.request
from datetime import datetime,timezone,timedelta
from html.parser import HTMLParser
from urllib.parse import urlsplit,parse_qs

URL="https://www.tff.org/Default.aspx?macId=317879&pageId=29"
FORECAST_SHA="610fbf97fd6728b071359debd600c9d3614c00b5fc931c1a5ff4ebcb81975f83"
HOME_ID="95647a3b-0347-5eb9-ae2f-d444d31a7d3b"
AWAY_ID="b70be320-82df-539d-9dc1-09f05137f08d"
KICKOFF="2026-11-08T13:00:00+00:00"
MAX_BYTES=2000000

class Blocked(ValueError):pass

class Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
        self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript"):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript") and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)

def parse_tff(raw):
    """Read TFF's visible exact team-score-date header; NEVER guess from goals."""
    if isinstance(raw,bytes):
        text=None
        for charset in ("utf-8-sig","cp1254","iso8859-9"):
            try:text=raw.decode(charset);break
            except UnicodeDecodeError:pass
        if text is None:raise Blocked("TFF_TEXT_UNDECODABLE")
    elif isinstance(raw,str):text=raw
    else:raise Blocked("TFF_BODY_NOT_TEXT")
    if len(text)>MAX_BYTES:raise Blocked("TFF_HTML_TOO_LARGE")
    vis=Visible()
    vis.feed(text)
    flat=" ".join(" ".join(vis.parts).split()).replace("\xa0"," ")
    if not re.search(r"Trendyol\s+Süper\s+Lig",flat,re.IGNORECASE):
        raise Blocked("TFF_SUPER_LIG_IDENTITY_MISSING")
    if not re.search(r"(?<!\d)8\.11\.2026\s*-\s*16:00(?!\d)",flat):
        raise Blocked("TFF_KICKOFF_DATE_TIME_MISMATCH")
    hits=list(re.finditer(
        r"ARCA\s+ÇORUM\s+FK\s+(?P<h>\d{1,2})\s+FENERBAHÇE\s+A\.Ş\.\s+(?P<a>\d{1,2})(?!\d)",
        flat,re.IGNORECASE))
    pairs={(int(m["h"]),int(m["a"])) for m in hits}
    if not hits or len(pairs)!=1:raise Blocked("TFF_SCORE_OR_TEAM_ORDER_NOT_UNIQUE")
    h,a=next(iter(pairs))
    if max(h,a)>20:raise Blocked("TFF_INVALID_SCORE")
    return [h,a]

def _download(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Futbol263-TFF-source-audit/1.0"})
    with urllib.request.urlopen(req,timeout=15) as res:
        u=urlsplit(res.geturl())
        if (u.scheme!="https" or u.hostname!="www.tff.org" or
            u.path.casefold()!="/default.aspx" or u.port is not None or
            u.username or u.password or
            {k.casefold():v for k,v in parse_qs(u.query).items()}
                !={"macid":["317879"],"pageid":["29"]}):
            raise Blocked("TFF_REDIRECT_MATCH_ID_CHANGED")
        raw=res.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:raise Blocked("TFF_HTML_TOO_LARGE")
    return raw

def verify_one(forecast,registered,*,now=None,fetcher=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise Blocked("SOURCE_CHECK_AWARE_TIME_REQUIRED")
    x=forecast.get("fixture",{})
    if (forecast.get("schema")!="quad_forward_263_v1" or
        forecast.get("payload_sha256")!=FORECAST_SHA or
        x.get("league")!="TUR1" or x.get("home_id")!=HOME_ID or
        x.get("away_id")!=AWAY_ID or x.get("kickoff_utc")!=KICKOFF or
        x.get("match_local_date")!="2026-11-08" or
        x.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE" or
        registered.get("forecast_sha256")!=FORECAST_SHA or
        registered.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL" or
        registered.get("home")!="Çorum FK" or
        registered.get("away")!="Fenerbahçe"):
        raise Blocked("TFF_EXACT_PINNED_FORECAST_MISMATCH")
    if now.astimezone(timezone.utc)<datetime.fromisoformat(KICKOFF)+timedelta(hours=4):
        raise Blocked("TFF_PREMATURE_SCORE_CHECK")
    raw=fetcher(URL) if fetcher is not None else _download(URL)
    if not isinstance(raw,(bytes,str)) or len(raw)>MAX_BYTES:
        raise Blocked("TFF_SOURCE_RESPONSE_TOO_LARGE")
    score=parse_tff(raw)
    return {"status":"OFFICIAL_TFF_PUBLIC_PAGE_NETWORK_CHECK_RESEARCH_ONLY",
        "forecast_sha256":FORECAST_SHA,"league":"TUR1",
        "match_date":"2026-11-08","kickoff_utc":KICKOFF,
        "source_url":URL,"source_sha256":hashlib.sha256(
            raw if isinstance(raw,bytes) else raw.encode("utf-8")).hexdigest(),
        "score":score,"federation_page_read":True,
        "human_attestation_written":False,
        "original_forecast_modified":False}

