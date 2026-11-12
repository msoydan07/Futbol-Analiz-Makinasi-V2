"""Read-only Serie A 2026/27 official Lega Serie A SDP fixture gate.

Uses a real official season ID and official competition ID verified at the
league-host API on 2026-11-11. The API is public but undocumented as a stable
contract: any unrecognized schema, host redirect, status, team or time blocks
the requested match. Never imports foreign fixture/odds data or creates IDs.
"""
from __future__ import annotations
import json
import re
from datetime import datetime,timedelta,timezone
from urllib.parse import quote,urlsplit
from urllib.request import Request,build_opener,HTTPRedirectHandler

HOST="api-sdp.legaseriea.it"
COMP_ID="serie-a::Football_Competition::ec93b94f74294dc98ab5bcfd67fc0d88"
SEASON_ID="serie-a::Football_Season::ed7fdc2a3e7b408b942ec177b7b956b5"
URL="https://"+HOST+"/v1/serie-a/football/seasons/"+quote(SEASON_ID,safe="")+"/matches?locale=en-GB"
class _OfficialRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        u=urlsplit(newurl)
        if u.scheme!="https" or u.hostname!=HOST or u.port or u.username or u.password:
            raise ValueError("seriea_official_redirect_outside_sdp_host")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def _fetch():
    req=Request(URL,headers={"User-Agent":"Mozilla/5.0 (official fixture verification)",
                       "Accept":"application/json",
                       "Referer":"https://www.legaseriea.it/"})
    with build_opener(_OfficialRedirect()).open(req,timeout=18) as res:
        u=urlsplit(res.geturl())
        if (u.scheme!="https" or u.hostname!=HOST or u.port or
            "json" not in res.headers.get("Content-Type","").lower()):
            raise ValueError("seriea_official_non_json_or_redirected")
        raw=res.read(3_000_001)
        if len(raw)>3_000_000:raise ValueError("seriea_official_response_too_large")
    return json.loads(raw)

def parse_sdp_events(payload):
    if not isinstance(payload,dict) or not isinstance(payload.get("matches"),list):
        return []
    matches=payload["matches"]
    if len(matches)!=380:return []  # 20 clubs, both legs; never use partial feed
    out=[];unique=set()
    for m in matches:
        if not isinstance(m,dict):return []
        if (m.get("seasonId")!=SEASON_ID or not isinstance(m.get("matchSet"),dict)
            or m["matchSet"].get("seasonId")!=SEASON_ID
            or m["matchSet"].get("competitionId")!=COMP_ID):
            return []
        if m.get("status")!="UPCOMING":
            continue  # finished or cancelled rows are never future fixtures
        home,away=m.get("home"),m.get("away")
        if not isinstance(home,dict) or not isinstance(away,dict):return []
        clubs=[]
        for t in (home,away):
            if (not isinstance(t.get("teamId"),str)
                or not re.fullmatch(r"serie-a::Football_Team::[a-f0-9]{32}",t["teamId"])
                or t.get("isTeamFake") is not False
                or t.get("countryCode")!="IT"):
                return []
            name=t.get("officialName") or t.get("shortName")
            if not isinstance(name,str) or not name.strip():return []
            clubs.append(name.strip())
        if home["teamId"]==away["teamId"]:return []
        # This very official API carries provisional 2027 calendar-only
        # placeholders such as "2027-01-17Z", with NO kickoff clock.
        # These are NEVER verified fixtures. Skip those unrelated entries
        # without rejecting the independent, timed Nov 2026 fixtures.
        raw_kick=m.get("matchDateUtc")
        if not isinstance(raw_kick,str) or not re.fullmatch(
                r"20\d\d-\d\d-\d\dT\d\d:\d\d(?::\d\d)?(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)",
                raw_kick):
            continue
        try:
            kick=datetime.fromisoformat(raw_kick.replace("Z","+00:00"))
            if kick.tzinfo is None:continue
            kick=kick.astimezone(timezone.utc)
        except ValueError:continue
        if not (datetime(2026,8,1,tzinfo=timezone.utc)
                <=kick<=datetime(2027,6,1,tzinfo=timezone.utc)):
            return []
        key=(clubs[0],clubs[1],kick.isoformat())
        if key in unique:return []
        unique.add(key)
        out.append({"home":clubs[0],"away":clubs[1],
                    "match_date":kick.date().isoformat(),
                    "kickoff_utc":kick.isoformat(),
                    "format":"lega_seriea_sdp_current_2026_27"})
    return out

def lookup(home,away,*,now=None,fetcher=None,same_team=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:return {"status":"NOT_VERIFIED","reason":"timezone_required"}
    now=now.astimezone(timezone.utc)
    if not callable(same_team):
        return {"status":"NOT_VERIFIED","reason":"canonical_team_resolver_required"}
    try:
        data=fetcher() if fetcher else _fetch()
        # Injected tests may provide decoded JSON or a raw JSON string only.
        if isinstance(data,str):data=json.loads(data)
        events=parse_sdp_events(data)
    except (ValueError,TypeError,OSError,TimeoutError,UnicodeError) as e:
        return {"status":"NOT_VERIFIED","reason":"official_api_unavailable_or_invalid",
                "error_type":type(e).__name__}
    if not events:
        return {"status":"NOT_VERIFIED","reason":"official_season_not_complete_or_schema_changed"}
    matched=[m for m in events
             if same_team(m["home"],home) and same_team(m["away"],away)]
    if len(matched)!=1:
        return {"status":"NOT_VERIFIED","reason":"official_fixture_absent_or_ambiguous",
                "count":len(matched)}
    dt=datetime.fromisoformat(matched[0]["kickoff_utc"])
    if not now<=dt<=now+timedelta(days=7):
        return {"status":"OUTSIDE_WINDOW","reason":"official_kickoff_outside_next_seven_days",
                "kickoff_utc":dt.isoformat(),"source_url":URL}
    return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":matched[0]["home"],
            "away":matched[0]["away"],"kickoff_utc":dt.isoformat(),
            "source_url":URL,"retrieved_at_utc":now.isoformat(),
            "identity_match":"PENDING","api_contract_not_officially_documented":True}
