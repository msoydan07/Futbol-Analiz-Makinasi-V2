"""One-time read-only Lega Serie A official API diagnostic.

No predictions, no odds, no bookmaker calls. Connect only to league-owned
api-sdp.legaseriea.it via HTTPS; never accept third-party redirects or content.
Do not take season/match identity from third-party documentation as proof.
"""
from __future__ import annotations
import json
from datetime import datetime
from urllib.parse import quote,urlsplit
from urllib.request import Request,build_opener,HTTPRedirectHandler

HOST="api-sdp.legaseriea.it"
BASE="https://"+HOST+"/v1/serie-a/football"
COMP="serie-a::Football_Competition::ec93b94f74294dc98ab5bcfd67fc0d88"
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if urlsplit(newurl).hostname!=HOST or urlsplit(newurl).scheme!="https":
            raise ValueError("OFFICIAL_API_REDIRECT_DISALLOWED")
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def official_json(path):
    url=BASE+"/"+path
    u=urlsplit(url)
    if u.hostname!=HOST or u.scheme!="https":raise ValueError("NOT_OFFICIAL_SOURCE")
    with build_opener(NoRedirect()).open(
       Request(url,headers={"User-Agent":"Mozilla/5.0",
         "Accept":"application/json","Referer":"https://www.legaseriea.it/"}),
       timeout=14) as r:
        if r.status!=200:raise ValueError("NON_OK_OFFICIAL_RESPONSE")
        end=urlsplit(r.geturl())
        if end.hostname!=HOST or end.scheme!="https":
            raise ValueError("OFFICIAL_API_HOST_CHANGED")
        raw=r.read(4_000_001)
        if len(raw)>4_000_000:raise ValueError("OFFICIAL_API_TOO_LARGE")
        if "json" not in r.headers.get("Content-Type",""):
            raise ValueError("NOT_JSON_CONTENT")
    return json.loads(raw),len(raw)
def shape(o):
    return {"type":type(o).__name__,"keys":list(o)[:15] if isinstance(o,dict) else None,
            "len":len(o) if isinstance(o,(dict,list)) else None}
def main():
    try:
        seasons,n=official_json("competitions/"+quote(COMP,safe="")+"/seasons?locale=en-GB")
        print("SERIEA_SEASONS="+json.dumps({"bytes":n,"shape":shape(seasons)},ensure_ascii=False),flush=True)
        options=[]
        stack=[seasons]
        while stack:
            obj=stack.pop()
            if isinstance(obj,list):
                stack.extend(obj)
            elif isinstance(obj,dict):
                if obj.get("seasonName") in ("2026/2027","2026-2027","2026/27"):
                    options.append({"seasonId":obj.get("seasonId"),"seasonName":obj.get("seasonName"),
                                    "keys":list(obj)})
                for key,val in obj.items():
                    if isinstance(val,(dict,list)):stack.append(val)
        print("SERIEA_SEASON_SELECTION="+json.dumps(options,ensure_ascii=False),flush=True)
        if len(options)!=1 or not isinstance(options[0]["seasonId"],str):
            print("SERIEA_API_RESULT=BLOCKED_SEASON_NOT_UNIQUE");return
        sid=options[0]["seasonId"]
        matches,bytes_n=official_json("seasons/"+quote(sid,safe="")+"/matches?locale=en-GB")
        print("SERIEA_MATCHES="+json.dumps({"bytes":bytes_n,"shape":shape(matches)},ensure_ascii=False),flush=True)
        raw=matches.get("matches",[]) if isinstance(matches,dict) else []
        checks={"n_matches":len(raw),"status_counts":{},"schema_issues":{}}
        from seriea_official_sdp_263 import SEASON_ID,COMP_ID,parse_sdp_events
        for m in raw:
            if not isinstance(m,dict):checks["schema_issues"]["not_dict"]=checks["schema_issues"].get("not_dict",0)+1;continue
            status=str(m.get("status"))
            checks["status_counts"][status]=checks["status_counts"].get(status,0)+1
            reasons=[]
            if m.get("seasonId")!=SEASON_ID:reasons.append("season_wrong")
            matchset=m.get("matchSet")
            if not isinstance(matchset,dict):reasons.append("missing_match_set")
            elif matchset.get("seasonId")!=SEASON_ID:reasons.append("match_set_season_wrong")
            elif matchset.get("competitionId")!=COMP_ID:reasons.append("competition_wrong")
            if status=="UPCOMING":
                for tname in ("home","away"):
                    t=m.get(tname)
                    if not isinstance(t,dict):reasons.append(tname+"_not_dict")
                    else:
                        if t.get("isTeamFake") is not False:reasons.append(tname+"_fake_not_false")
                        if t.get("countryCode")!="IT":reasons.append(tname+"_country_not_IT")
            for reason in reasons:
                checks["schema_issues"][reason]=checks["schema_issues"].get(reason,0)+1
        checks["strict_events"]=len(parse_sdp_events(matches))
        print("SERIEA_PARSER_INSPECTION="+json.dumps(checks,ensure_ascii=False),flush=True)

        fixtures=[]
        stack=[matches]
        while stack:
            x=stack.pop()
            if isinstance(x,list):stack.extend(x)
            elif isinstance(x,dict):
                if any("2026-11-2" in str(v) for k,v in x.items() if k.lower() in ("matchdateutc","dateutc","startdateutc")):
                    fixtures.append({k:v for k,v in x.items() if k in (
                        "matchDateUtc","matchSet","home","away","status","statusLabel","seasonId","competition")})
                for k,v in x.items():
                    if isinstance(v,(dict,list)):stack.append(v)
        print("SERIEA_LATE_NOV_SAMPLES="+json.dumps(fixtures[:3],ensure_ascii=False)[:5500],flush=True)
        print("SERIEA_API_RESULT="+("HAS_LATE_NOV_MATCHES" if fixtures else "BLOCKED_NO_DATE_OR_SCHEMA"),flush=True)
    except Exception as e:
        print("SERIEA_API_RESULT=BLOCKED_"+type(e).__name__+":"+str(e)[:155],flush=True)
if __name__=="__main__":main()
