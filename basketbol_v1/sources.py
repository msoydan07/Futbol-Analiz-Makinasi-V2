"""Real historical basketball scores, research only, no bookmaker inputs."""
from __future__ import annotations
import csv,gzip,hashlib,io,json,re,urllib.request
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

NBA_COMMIT="2c98a8cc6beae31f425fb1380c794d598d2d74b6"
NBA_YEARS=(2023,2024,2025,2026,2027)
EL_YEARS=(2022,2023,2024,2025,2026)
NBA_ROOT=f"https://raw.githubusercontent.com/roni-altshuler/nba_predictor/{NBA_COMMIT}/backend/data/history"
EL_ROOT="https://675hoops.com/downloads"
MAX_BYTES=3_000_000
class SourceError(ValueError):pass

@dataclass(frozen=True)
class Game:
    league:str
    season:int
    day:str
    game_id:str
    home:str
    away:str
    home_score:int
    away_score:int
    neutral:bool=False
    @property
    def margin(self):return self.home_score-self.away_score
    @property
    def total(self):return self.home_score+self.away_score

def check(g):
    if g.league not in ("NBA","EL","EC") or type(g.season)!=int or not 2000<=g.season<=2100:
        raise SourceError("INVALID_LEAGUE_SEASON")
    if not isinstance(g.game_id,str) or not 1<=len(g.game_id)<=75:
        raise SourceError("INVALID_GAME_ID")
    datetime.strptime(g.day,"%Y-%m-%d")
    if any(not isinstance(x,str) or not re.fullmatch(r"[A-Za-z0-9_.-]{2,30}",x) for x in (g.home,g.away)) or g.home==g.away:
        raise SourceError("INVALID_TEAM_IDENTITY")
    if any(type(v)!=int or not 0<=v<=250 for v in (g.home_score,g.away_score)):
        raise SourceError("INVALID_FINAL_SCORE")
    if g.home_score==g.away_score:raise SourceError("TIED_FINAL_NOT_A_TWO_WAY_RESULT")
    if type(g.neutral)!=bool:raise SourceError("INVALID_NEUTRAL")
    return g

def nba_games(payload,year):
    if not isinstance(payload,dict) or payload.get("season")!=year or not isinstance(payload.get("games"),list):
        raise SourceError("NBA_SEASON_MISMATCH")
    seen=set();out=[]
    for x in payload["games"]:
        if (x.get("type")!=2 or x.get("home_score") is None or x.get("away_score") is None
            or x.get("phase") in ("NBA Cup Championship","NBA In-Season Tournament Championship")):
            continue
        stamp=datetime.fromisoformat(x["date"].replace("Z","+00:00"))
        if stamp.tzinfo is None:raise SourceError("NBA_DATE_WITHOUT_ZONE")
        day=stamp.astimezone(ZoneInfo("America/New_York")).date().isoformat()
        gid=str(x["id"])
        if gid in seen:raise SourceError("NBA_DUPLICATE_GAME")
        seen.add(gid)
        g=Game("NBA",year,day,gid,str(x["home"]),str(x["away"]),
               x["home_score"],x["away_score"],bool(x.get("neutral",False)))
        out.append(check(g))
    return sorted(out,key=lambda x:(x.day,x.game_id))

def euroleague_games(raw,year):
    try:txt=gzip.decompress(raw)
    except OSError as exc:raise SourceError("EL_INVALID_GZIP") from exc
    if len(txt)>4_000_000:raise SourceError("EL_DECOMPRESSED_TOO_LARGE")
    reader=csv.DictReader(io.StringIO(txt.decode("utf-8-sig")))
    required={"season","game_id","date","phase","home","away","home_score","away_score","neutral"}
    if not required.issubset(set(reader.fieldnames or [])):raise SourceError("EL_REQUIRED_COLUMNS_MISSING")
    seen=set();out=[]
    for x in reader:
        if not x.get("home_score") or not x.get("away_score") or x["phase"]!="RS":
            continue
        try:
            if int(x["season"])!=year:raise SourceError("EL_YEAR_MISMATCH")
            gid=str(x["game_id"]).strip()
            if gid in seen:raise SourceError("EL_DUPLICATE_GAME")
            seen.add(gid)
            neutral=x["neutral"].strip()
            if neutral not in ("0","1"):raise SourceError("EL_BAD_NEUTRAL")
            g=Game("EL",year,x["date"],gid,x["home"],x["away"],
                   int(x["home_score"]),int(x["away_score"]),neutral=="1")
            out.append(check(g))
        except (ValueError,TypeError) as exc:
            raise SourceError("EL_SCORE_OR_SEASON_INVALID") from exc
    return sorted(out,key=lambda x:(x.day,x.game_id))

def _get(url,host):
    req=urllib.request.Request(url,headers={"User-Agent":"BasketbolResearchV1/1.0 noncommercial"})
    with urllib.request.urlopen(req,timeout=25) as resp:
        end=urlsplit(resp.geturl());orig=urlsplit(url)
        if (end.scheme!="https" or end.hostname!=host or end.port is not None
            or end.username or end.password or end.path!=orig.path or end.query!=orig.query or end.fragment):
            raise SourceError("UNAPPROVED_SOURCE_REDIRECT")
        raw=resp.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:raise SourceError("SOURCE_TOO_LARGE")
    return raw

def eurocup_games(payload,year):
    """EuroCup v2 public official schedule/results; parsed only for PLAYED RS games."""
    if not isinstance(payload,dict) or not isinstance(payload.get("data"),list):
        raise SourceError("EC_API_ENVELOPE_INVALID")
    data=payload["data"]
    total=payload.get("total")
    if type(total)!=int or total!=len(data):
        raise SourceError("EC_API_PAGINATION_INCOMPLETE_OR_INVALID")
    seen=set();out=[]
    for x in data:
        if not isinstance(x,dict):raise SourceError("EC_GAME_ROW_INVALID")
        if x.get("season",{}).get("code")!=f"U{year}":
            raise SourceError("EC_SEASON_INCORRECT")
        if x.get("played") is not True or x.get("phaseType",{}).get("code")!="RS":
            continue
        local=x.get("local",{});road=x.get("road",{})
        if local.get("score") is None or road.get("score") is None:
            raise SourceError("EC_PLAYED_BUT_NO_SCORE")
        gamecode=str(x.get("gameCode") or "")
        if not gamecode or gamecode in seen:raise SourceError("EC_DUPLICATE_OR_NO_GAMECODE")
        seen.add(gamecode)
        when=x.get("localDate")
        if not isinstance(when,str) or not re.match(r"^20\d\d-\d\d-\d\dT",when):
            raise SourceError("EC_KICKOFF_DATE_MISSING")
        g=Game("EC",year,when[:10],gamecode,
               local["club"]["code"],road["club"]["code"],
               local["score"],road["score"],x.get("isNeutralVenue",False))
        out.append(check(g))
    return sorted(out,key=lambda x:(x.day,x.game_id))

def download(league):
    if league not in ("NBA","EL","EC"):raise SourceError("UNSUPPORTED_LEAGUE")
    years=NBA_YEARS if league=="NBA" else EL_YEARS
    games=[];manifest=[]
    for year in years:
        if league=="NBA":
            url=f"{NBA_ROOT}/season_{year}.json"
            raw=_get(url,"raw.githubusercontent.com")
            data=nba_games(json.loads(raw.decode("utf-8")),year)
        elif league=="EL":
            url=f"{EL_ROOT}/games-{year}.csv.gz"
            raw=_get(url,"675hoops.com")
            data=euroleague_games(raw,year)
        else:
            url=f"https://api-live.euroleague.net/v2/competitions/U/seasons/U{year}/games?limit=500&offset=0"
            raw=_get(url,"api-live.euroleague.net")
            data=eurocup_games(json.loads(raw.decode("utf-8")),year)
        if year!=years[-1] and len(data)<150:raise SourceError(f"INSUFFICIENT_ARCHIVE:{league}:{year}:{len(data)}")
        if not data:raise SourceError(f"EMPTY_YEAR:{league}:{year}")
        manifest.append({"year":year,"url":url,"sha256":hashlib.sha256(raw).hexdigest(),
                         "regular_season_games":len(data),"first_day":data[0].day,"last_day":data[-1].day})
        games.extend(data)
    if len({(g.league,g.season,g.game_id) for g in games})!=len(games):
        raise SourceError("DUPLICATE_GLOBAL_GAME_ID")
    return games,manifest
