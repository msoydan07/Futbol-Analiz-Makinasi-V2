"""Research-only, free-tier bulk EU market observer for 10 leagues (no iddaa claim).

Requires a user's FREE The Odds API key stored in THE_ODDS_API_KEY.
One request returns the currently listed games for one LEAGUE; never per-match polls.
Data are market research only. Never manufacture official S1/S2, bets or EV here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

API="https://api.the-odds-api.com/v4"
SCHEMA="263_free_bulk_external_odds_research_v1"
TR=ZoneInfo("Europe/Istanbul")
MARKETS=("h2h","totals")
REGION="eu"
# All ten supported leagues; official fixture verification remains independent.
SPORTS={
 "ENG1":"soccer_epl",
 "ENG2":"soccer_efl_champ",
 "GER1":"soccer_germany_bundesliga",
 "ESP1":"soccer_spain_la_liga",
 "ITA1":"soccer_italy_serie_a",
 "FRA1":"soccer_france_ligue_one",
 "NED1":"soccer_netherlands_eredivisie",
 "TUR1":"soccer_turkey_super_league",
 "POR1":"soccer_portugal_primeira_liga",
 "BEL1":"soccer_belgium_first_div",
}
MAX_RUN_CREDITS=20  # one region x two markets x ten leagues
MAX_AGE_SECONDS=1800
class QuoteUnavailable(ValueError):
    pass

def utc(v):
    if not isinstance(v,str):raise QuoteUnavailable("ODDS_TIMESTAMP_MISSING")
    try:
        dt=datetime.fromisoformat(v.replace("Z","+00:00"))
    except ValueError as exc:
        raise QuoteUnavailable("ODDS_TIMESTAMP_INVALID") from exc
    if dt.tzinfo is None:raise QuoteUnavailable("ODDS_TIMEZONE_MISSING")
    return dt.astimezone(timezone.utc)

def canonical(obj):
    return json.dumps(obj,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode("utf-8")

def _price(v):
    if (isinstance(v,bool) or not isinstance(v,(int,float))
        or not math.isfinite(v) or not 1.0 < v < 1000):
        raise QuoteUnavailable("INVALID_ODDS")
    return float(v)

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

def fetch(sport,params,key):
    """Only a fixed API host and known 10-league sport keys. Never log API key."""
    if sport not in SPORTS.values():raise QuoteUnavailable("UNSUPPORTED_SPORT")
    if not key:raise QuoteUnavailable("NO_FREE_THE_ODDS_API_KEY_CONFIGURED")
    common={"markets","oddsFormat","commenceTimeFrom","commenceTimeTo"}
    if not ((set(params)==common|{"regions"} and params.get("regions")=="eu")
            or (set(params)==common|{"bookmakers"} and params.get("bookmakers")=="pinnacle")):
        raise QuoteUnavailable("UNSAFE_API_PARAMETERS")
    url=API+"/sports/"+sport+"/odds?"+urllib.parse.urlencode({**params,"apiKey":key})
    try:
        with urllib.request.build_opener(_NoRedirect()).open(
                urllib.request.Request(url,headers={"Accept":"application/json"}),
                timeout=18) as response:
            if response.geturl().split("?")[0]!=API+"/sports/"+sport+"/odds":
                raise QuoteUnavailable("ODDS_API_REDIRECT_BLOCKED")
            raw=response.read(2_000_001)
            if len(raw)>2_000_000:raise QuoteUnavailable("ODDS_API_TOO_LARGE")
            remaining=response.headers.get("x-requests-remaining")
    except urllib.error.HTTPError as exc:
        raise QuoteUnavailable("ODDS_API_HTTP_"+str(exc.code)) from None
    except (TimeoutError,urllib.error.URLError) as exc:
        raise QuoteUnavailable("ODDS_API_NETWORK_ERROR") from None
    try:
        data=json.loads(raw)
    except ValueError as exc:
        raise QuoteUnavailable("ODDS_API_BAD_JSON") from exc
    if not isinstance(data,list):raise QuoteUnavailable("ODDS_API_NOT_EVENTS_LIST")
    try:
        budget_remaining=int(remaining) if remaining is not None else None
    except ValueError:
        budget_remaining=None
    return data,budget_remaining

def _market(m,home,away):
    if not isinstance(m,dict) or m.get("key") not in MARKETS:
        return None
    values={}
    for outcome in m.get("outcomes",[]):
        if not isinstance(outcome,dict):return None
        try:p=_price(outcome.get("price"))
        except QuoteUnavailable:return None
        if m["key"]=="h2h":
            name=str(outcome.get("name","")).strip()
            k=("H" if name==home else "A" if name==away else
               "D" if name.casefold()=="draw" else None)
        else:
            label=str(outcome.get("name","")).lower().strip()
            point=outcome.get("point")
            if label not in ("over","under") or isinstance(point,bool):
                return None
            try:point=float(point)
            except (TypeError,ValueError):return None
            k=f"{label}_{point:g}" if point in (1.5,2.5,3.5) else None
        if not k or k in values:return None
        values[k]=p
    if m["key"]=="h2h":
        if set(values)!={"H","D","A"}:return None
        margin=sum(1/x for x in values.values())
        if not 1 < margin < 1.45:return None
    else:
        if len(values)!=2:return None
        points={k.split("_",1)[1] for k in values}
        if len(points)!=1:return None
        point=next(iter(points))
        if set(values)!={"over_"+point,"under_"+point}:return None
        margin=sum(1/x for x in values.values())
        if not 1<margin<1.45:return None
    return {"market":m["key"],"prices":values,
            "source_last_update_utc":m.get("last_update")}

def normalize_event(event,sport,day,now,*,bookmaker_filter=None):
    if not isinstance(event,dict) or event.get("sport_key")!=sport:
        return None
    home,away=event.get("home_team"),event.get("away_team")
    if not all(isinstance(x,str) and x.strip() for x in (home,away)) or home==away:
        return None
    try:ko=utc(event.get("commence_time"))
    except QuoteUnavailable:return None
    if ko<=now or ko.astimezone(TR).date()!=day:return None
    books=[]
    for book in event.get("bookmakers",[]):
        if not isinstance(book,dict):continue
        name=book.get("key")
        if not isinstance(name,str) or not name or len(name)>90:continue
        if bookmaker_filter is not None and name!=bookmaker_filter:continue
        markets=[]
        for group in book.get("markets",[]):
            found=_market(group,home,away)
            if not found:continue
            try:last=utc(group.get("last_update") or book.get("last_update"))
            except QuoteUnavailable:continue
            if last>now or (now-last).total_seconds()>MAX_AGE_SECONDS:continue
            found["source_last_update_utc"]=last.isoformat()
            markets.append(found)
        if markets:
            books.append({"bookmaker_key":name,"markets":markets})
    if not books:return None
    return {"provider_event_id":str(event.get("id","")),
            "sport":sport,"home_team":home,"away_team":away,
            "kickoff_utc":ko.isoformat(),"bookmakers":books}

def day_window(day):
    start=datetime.combine(day,time.min,tzinfo=TR).astimezone(timezone.utc)
    end=datetime.combine(day.fromordinal(day.toordinal()+1),time.min,tzinfo=TR).astimezone(timezone.utc)
    return start.strftime("%Y-%m-%dT%H:%M:%SZ"),end.strftime("%Y-%m-%dT%H:%M:%SZ")

def collect(day,now,key,getter=fetch,*,bookmaker_filter=None,leagues=None,markets=None):
    """One call per league, two markets each; safe free-budget cap. No repeats."""
    if not key:raise QuoteUnavailable("NO_FREE_THE_ODDS_API_KEY_CONFIGURED")
    if not isinstance(day,date) or now.tzinfo is None:
        raise QuoteUnavailable("DATE_OR_CLOCK_INVALID")
    now=now.astimezone(timezone.utc)
    if day<now.astimezone(TR).date():raise QuoteUnavailable("NO_HISTORICAL_RECONSTRUCTION")
    if bookmaker_filter not in (None,"pinnacle"):
        raise QuoteUnavailable("UNSUPPORTED_BOOKMAKER_FILTER")
    requested_leagues=tuple(SPORTS) if leagues is None else tuple(leagues)
    requested_markets=MARKETS if markets is None else tuple(markets)
    if (not requested_leagues or len(set(requested_leagues))!=len(requested_leagues)
        or any(x not in SPORTS for x in requested_leagues)):
        raise QuoteUnavailable("INVALID_OR_DUPLICATED_LEAGUE_SELECTION")
    if (not requested_markets or len(set(requested_markets))!=len(requested_markets)
        or any(x not in MARKETS for x in requested_markets)):
        raise QuoteUnavailable("INVALID_OR_DUPLICATED_MARKETS")
    lo,hi=day_window(day)
    params={"markets":",".join(requested_markets),
            "oddsFormat":"decimal","commenceTimeFrom":lo,"commenceTimeTo":hi}
    if bookmaker_filter=="pinnacle":
        params["bookmakers"]="pinnacle"
    else:
        params["regions"]=REGION
    if len(requested_leagues)*len(requested_markets)>MAX_RUN_CREDITS:
        raise QuoteUnavailable("CONFIGURED_FREE_RUN_BUDGET_EXCEEDED")
    results={};blocked={};remaining=None
    for league in requested_leagues:
        sport=SPORTS[league]
        if remaining is not None and remaining < len(requested_markets):
            blocked[league]="FREE_QUOTA_GUARD";continue
        try:
            data,remaining=getter(sport,params,key)
            if not isinstance(data,list):
                raise QuoteUnavailable("ODDS_API_NOT_EVENTS_LIST")
            matches=[]
            for event in data:
                row=normalize_event(event,sport,day,now,bookmaker_filter=bookmaker_filter)
                if row:matches.append(row)
            results[league]=matches
        except QuoteUnavailable as exc:
            blocked[league]=str(exc)
            # Never spend remaining free credits retrying blocked access.
            if str(exc) in ("ODDS_API_HTTP_401","ODDS_API_HTTP_403","ODDS_API_HTTP_429"):
                for other in requested_leagues:
                    if other not in results and other not in blocked:
                        blocked[other]="ACCESS_OR_QUOTA_NOT_RETRIED"
                break
    out={"schema":SCHEMA,"day_turkey":day.isoformat(),"checked_at_utc":now.isoformat(),
        "provider":"The Odds API (the-odds-api.com)","source_scope":"FOREIGN_BOOKMAKER_MARKET_RESEARCH_ONLY",
        "region":REGION if bookmaker_filter is None else None,
        "bookmaker_filter":bookmaker_filter,
        "markets_requested":list(requested_markets),
        "leagues_requested":list(requested_leagues),
        "bookmaker_odds_not_iddaa":True,"independently_verified_fixture":False,
        "S1_S2_official_approved":False,"betting_authorized":False,
        "forecast_or_decision_modified":False,"max_one_run_credit_cost":len(requested_leagues)*len(requested_markets),
        "reported_remaining_credits":remaining,"leagues":results,"blocked":blocked}
    out["payload_sha256"]=hashlib.sha256(canonical(out)).hexdigest()
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--day-turkey",help="YYYY-MM-DD; defaults to current Turkish date")
    parser.add_argument("--out",required=True)
    parser.add_argument("--pinnacle-only",action="store_true",
        help="Research only: bookmaker=pinnacle, no automatic substitution")
    args=parser.parse_args()
    now=datetime.now(timezone.utc)
    day=date.fromisoformat(args.day_turkey) if args.day_turkey else now.astimezone(TR).date()
    result=collect(day,now,os.environ.get("THE_ODDS_API_KEY"),
                   bookmaker_filter="pinnacle" if args.pinnacle_only else None)
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as fp:
        json.dump(result,fp,sort_keys=True,ensure_ascii=False,indent=2)
        fp.write("\n")
    print(json.dumps({"status":"RESEARCH_ONLY_ODDS_STAGED",
                      "date":result["day_turkey"],
                      "leagues_observed":len(result["leagues"]),
                      "matches_observed":sum(len(x) for x in result["leagues"].values()),
                      "blocked":result["blocked"]},ensure_ascii=False))
if __name__=="__main__":
    main()
