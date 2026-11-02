"""2.6.3 UEFA named-match on-demand entry. Scope gate FIRST, official article SECOND.

2026/27 CL + EL LEAGUE PHASE ONLY. One fixed official UEFA article per
competition, no candidate club research, no automatic match discovery, no
H2H, no statistics or betting. Official text must explicitly confirm the
given pair, match date and kickoff. Never infer from an offline fixture list.
Fail closed when UEFA source is inaccessible, dynamic, or unparseable.
"""
from __future__ import annotations
import argparse
from datetime import date, datetime, time, timedelta, timezone
from html.parser import HTMLParser
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
import urllib.request
from uefa_ten_league_scope_gate_263 import check_europe_scope, norm, INDEX_DEFAULT

VERSION="263_EUROPE_REQUESTED_MATCH_SCOPE_TO_UEFA_OFFICIAL_v1"
SOURCES={
 "UEFA_CL":"https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures/",
 "UEFA_EL":"https://www.uefa.com/uefaeuropaleague/news/02a8-2174cafa5bb6-82bbc20c9b92-1000--2026-27-europa-league-all-the-league-phase-fixtures-and-results/",
}
MAX_BYTES=2_000_000
CET=timezone(timedelta(hours=1))
MATCH_RE=re.compile(r"^(?P<home>.+?)\s+vs\s+(?P<away>.+?)(?:\s+\((?P<clock>\d\d:\d\d)\))?$",re.I)
DATE_RE=re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) (\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December) (20\d\d)$",re.I)
MD_RE=re.compile(r"^Matchday\s+([1-8])$",re.I)

class EuropeRequestError(ValueError):pass

def official_url_ok(url,competition):
    if not isinstance(url,str) or competition not in SOURCES:return False
    try:
        u=urlsplit(url)
        return (u.scheme=="https" and u.netloc.lower()=="www.uefa.com"
            and not u.query and not u.fragment and u.username is None
            and u.password is None and u.port is None
            and u.path==urlsplit(SOURCES[competition]).path)
    except ValueError:return False

class VisibleUEFA(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tokens=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript","svg","iframe"):
            self.skip+=1
        if not self.skip and tag in ("p","div","li","h1","h2","h3","h4","br","tr"):
            self.tokens.append("\n")
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript","svg","iframe"):
            self.skip=max(0,self.skip-1)
        if not self.skip and tag in ("p","div","li","h1","h2","h3","h4","tr"):
            self.tokens.append("\n")
    def handle_data(self,data):
        if not self.skip:self.tokens.append(data)
    def visible_lines(self):
        return [" ".join(line.split()) for line in "".join(self.tokens).splitlines()
                if line.strip()]

def get_official_article(competition):
    url=SOURCES[competition]
    req=urllib.request.Request(url,headers={
        "User-Agent":"Mozilla/5.0 (compatible; UEFA-match-on-demand/2.6.3)",
        "Accept":"text/html"
    })
    with urllib.request.urlopen(req,timeout=15) as response:
        if not official_url_ok(response.geturl(),competition):
            raise EuropeRequestError("OFFICIAL_ARTICLE_REDIRECTED_AWAY")
        content=response.read(MAX_BYTES+1)
        media=response.headers.get("Content-Type","")
    if len(content)>MAX_BYTES or not content or "html" not in media:
        raise EuropeRequestError("OFFICIAL_ARTICLE_FORMAT_OR_SIZE_REJECTED")
    return content.decode("utf-8"),url

def extract_one_official_fixture(html,competition,home_id,away_id,index,now):
    """Parse one fixture from official visible article, never season-end scores."""
    if not isinstance(html,str) or len(html)>MAX_BYTES:
        raise EuropeRequestError("ARTICLE_INPUT_INVALID")
    parser=VisibleUEFA();parser.feed(html)
    lines=parser.visible_lines()
    text=" ".join(lines[:140])
    expected="Champions League" if competition=="UEFA_CL" else "Europa League"
    if "2026/27" not in text or expected not in text:
        raise EuropeRequestError("OFFICIAL_ARTICLE_SEASON_OR_COMPETITION_MISMATCH")
    if not any("Kick-offs are 21:00 unless stated; all times CET." in line for line in lines):
        raise EuropeRequestError("OFFICIAL_ARTICLE_DEFAULT_TIME_UNAVAILABLE")
    now=now.astimezone(timezone.utc)
    md=None;day=None
    matches=[]
    for line in lines:
        mdhit=MD_RE.fullmatch(line)
        if mdhit:
            md=int(mdhit.group(1));day=None
            continue
        dayhit=DATE_RE.fullmatch(line)
        if dayhit:
            try:
                day=datetime.strptime(line,"%A %d %B %Y").date()
                if day.strftime("%A").casefold()!=dayhit.group(1).casefold():
                    raise EuropeRequestError("OFFICIAL_ARTICLE_WEEKDAY_MISMATCH")
            except ValueError as exc:
                raise EuropeRequestError("OFFICIAL_ARTICLE_DATE_INVALID") from exc
            continue
        if md is None or day is None or day.year not in (2026,2027):
            continue
        hit=MATCH_RE.fullmatch(line)
        if not hit:continue
        # Only exact reviewed local aliases; NO fuzzy matching or guessed IDs.
        h=index["aliases"].get(norm(hit.group("home")))
        a=index["aliases"].get(norm(hit.group("away")))
        if h!=home_id or a!=away_id:continue
        t=hit.group("clock") or "21:00"
        try:
            hh,mm=map(int,t.split(":"))
            local=datetime.combine(day,time(hh,mm),tzinfo=CET)
        except ValueError as exc:
            raise EuropeRequestError("OFFICIAL_ARTICLE_INVALID_KICKOFF") from exc
        kick=local.astimezone(timezone.utc)
        if not now<kick<=now+timedelta(days=7):
            continue
        matches.append({
            "competition":competition,"season":"2026-2027",
            "matchday":md,"home_uefa_name":hit.group("home"),
            "away_uefa_name":hit.group("away"),
            "kickoff_utc":kick.isoformat(),
            "kickoff_source_time_CET":t,
            "kickoff_time_basis":("UEFA_EXPLICIT_MATCH_TIME" if hit.group("clock") else
                                  "UEFA_ARTICLE_PUBLISHED_21_00_CET_DEFAULT"),
            "date":day.isoformat(),
            "fixture_source_url":SOURCES[competition],
            "individual_UEFA_match_id":None,
            "official_article_directly_fetched":True,
            "data_source_label":"OFFICIAL_UEFA_ARTICLE_VISIBLE_LEAGUE_PHASE_FIXTURE",
            "team_identity_separately_verified_against_UEFA_club_ID":False,
            "round":"LEAGUE_PHASE",
        })
    # No duplicate conflicting schedules, even with repeated article by-team rows.
    unique={(m["date"],m["kickoff_utc"],m["home_uefa_name"],m["away_uefa_name"],
             m["matchday"]):m for m in matches}
    if len(unique)!=1:
        return ("OFFICIAL_UEFA_FIXTURE_NOT_FOUND_OR_AMBIGUOUS",None)
    return ("OFFICIAL_UEFA_ARTICLE_FIXTURE_FOUND",next(iter(unique.values())))

def requested_europe_match(competition,home,away,*,index,now=None,official_provider=None):
    """Trusted entrypoint for future European named-match orchestration.

    Call order is fixed: local index/scope -> trusted UEFA HTTPS adapter.
    This function makes ZERO other data/math calls, whether pass or fail.
    """
    if competition not in SOURCES:
        raise EuropeRequestError("UNSUPPORTED_UEFA_COMPETITION")
    now=now or datetime.now(timezone.utc)
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise EuropeRequestError("TIMEZONE_AWARE_NOW_REQUIRED")
    scope=check_europe_scope(home,away,index)
    output={"version":VERSION,"competition":competition,"requested":{"home":home,"away":away},
            "scope":scope,"status":scope["status"],"message":scope["message"],
            "fixture":None,"fixture_verified":False,
            "no_stats_requested":True,"no_other_leagues_searched":True,
            "model_forecast_authorized":False,"ABC_approved":False,"odds_EV":None,
            "pilot_recorded":False,"domestic_10_leagues_changed":False}
    if not scope["allow_further_research"]:
        return output
    provider=official_provider or get_official_article
    try:
        html,url=provider(competition)
        if not official_url_ok(url,competition):
            raise EuropeRequestError("OFFICIAL_PROVIDER_URL_NOT_ALLOWED")
        status,fixture=extract_one_official_fixture(
            html,competition,scope["home"]["canonical_team_id"],
            scope["away"]["canonical_team_id"],index,now)
    except (EuropeRequestError,ValueError,UnicodeError,TimeoutError,OSError) as exc:
        output["status"]="OFFICIAL_UEFA_FIXTURE_NOT_VERIFIED"
        output["message"]="Resmî UEFA fikstürü doğrulanamadı; analiz yapılmıyor."
        output["official_lookup_error_type"]=type(exc).__name__
        return output
    output["status"]=status
    if fixture:
        output["status"]="OFFICIAL_UEFA_FIXTURE_CONFIRMED_NO_MODEL_YET"
        output["fixture"]=fixture
        output["fixture_verified"]=True
        output["message"]="İki takım kapsamda ve UEFA fikstürü doğrulandı. Avrupa tahmin motoru henüz kabul edilmedi."
    else:
        output["message"]="Resmî UEFA kaynağında bu eşleşme gelecek 7 günde doğrulanamadı; analiz yapılmıyor."
    return output

def main(argv=None):
    p=argparse.ArgumentParser(description="UEFA named match: local scope FIRST, one UEFA official article SECOND")
    p.add_argument("--competition",choices=tuple(SOURCES),required=True)
    p.add_argument("--home",required=True);p.add_argument("--away",required=True)
    p.add_argument("--index",default=INDEX_DEFAULT)
    args=p.parse_args(argv)
    index=json.loads(Path(args.index).read_text(encoding="utf-8"))
    result=requested_europe_match(args.competition,args.home,args.away,index=index)
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True))
    return 0
if __name__=="__main__":raise SystemExit(main())
