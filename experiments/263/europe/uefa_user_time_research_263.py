"""User-named 2026/27 UEFA match: research can begin WITHOUT fixture verification.

Ten-league scope is FIRST. User-supplied Istanbul kickoff is a planning
cutoff only; cannot qualify immutable real prediction/pilot registration.
This gateway does not fetch stats or run any prediction model.
"""
import argparse
import json
import re
from datetime import datetime,date,time,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from uefa_ten_league_scope_gate_263 import check_europe_scope, INDEX_DEFAULT

VERSION="263_UEFA_USER_TIME_RESEARCH_GATE_V1"
COMPETITIONS={"UEFA_CL","UEFA_EL"}
IST=ZoneInfo("Europe/Istanbul")

class UserTimeError(ValueError):pass

def interpret_istanbul_kickoff(local_date, local_time):
    if not isinstance(local_date,str) or re.fullmatch(r"20\d{2}-\d{2}-\d{2}",local_date) is None:
        raise UserTimeError("DATE_MUST_BE_YYYY_MM_DD")
    if not isinstance(local_time,str) or re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",local_time) is None:
        raise UserTimeError("TIME_MUST_BE_24H_HH_MM")
    try:
        day=date.fromisoformat(local_date)
        h,m=map(int,local_time.split(":"))
        return datetime.combine(day,time(h,m),IST).astimezone(timezone.utc)
    except ValueError as e:
        raise UserTimeError("INVALID_CALENDAR_DATE_OR_CLOCK") from e

def requested_europe_research(competition,home,away,local_date,local_time,
                              *,index,now=None,downstream=None):
    """Optional downstream research callback is NEVER called on a rejected request."""
    if competition not in COMPETITIONS:raise UserTimeError("UNSUPPORTED_COMPETITION")
    now=now or datetime.now(timezone.utc)
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise UserTimeError("AWARE_NOW_REQUIRED")
    now=now.astimezone(timezone.utc)
    scope=check_europe_scope(home,away,index)
    result={"schema":VERSION,"competition":competition,"requested_home":home,
        "requested_away":away,"reported_local_date":local_date,
        "reported_local_time":local_time,"reported_timezone":"Europe/Istanbul",
        "analysis_asof_utc":now.isoformat(),"scope":scope,
        "status":scope["status"],"message":scope["message"],
        "reported_kickoff_utc":None,"kickoff_provenance":"USER_SUPPLIED_NOT_VERIFIED",
        "official_fixture_verified":False,"data_research_allowed":False,
        "model_predictions_approved":False,"ABC_approved":False,
        "odds_EV":None,"pilot_registration_allowed":False,
        "pilot_recorded":False,"production_modified":False}
    if not scope["allow_further_research"]:
        return result,None
    try:
        kickoff=interpret_istanbul_kickoff(local_date,local_time)
    except UserTimeError as e:
        result["status"]="USER_DATE_TIME_INVALID"
        result["message"]="Verilen maç tarihi veya Türkiye saati geçersiz; analiz araştırması başlatılmadı."
        result["reason"]=str(e)
        return result,None
    result["reported_kickoff_utc"]=kickoff.isoformat()
    if kickoff<=now:
        result["status"]="USER_REPORTED_KICKOFF_ALREADY_PASSED"
        result["message"]="Bildirilen başlama saati geçmiş; maç öncesi araştırma başlatılmadı."
        return result,None
    if kickoff-now>timedelta(days=7):
        result["status"]="OUTSIDE_NEXT_SEVEN_DAYS"
        result["message"]="Maç 7 günlük çalışma penceremizin dışında; araştırma başlatılmadı."
        return result,None
    result["status"]="READY_FOR_PREMATCH_DATA_RESEARCH_USER_TIME"
    result["message"]="Kapsam uygun; kullanıcı tarafından bildirilen Türkiye saatine göre maç öncesi veri araştırmasına geçilebilir. Resmî fikstür doğrulaması bu aşamada zorunlu değil."
    result["data_research_allowed"]=True
    return result,(downstream(result) if downstream is not None else None)

def main(argv=None):
    p=argparse.ArgumentParser(description="UEFA research without compulsory official fixture search")
    p.add_argument("--competition",choices=sorted(COMPETITIONS),required=True)
    p.add_argument("--home",required=True)
    p.add_argument("--away",required=True)
    p.add_argument("--date",required=True)
    p.add_argument("--time",required=True)
    p.add_argument("--index",default=INDEX_DEFAULT)
    args=p.parse_args(argv)
    index=json.loads(Path(args.index).read_text(encoding="utf-8"))
    result,_=requested_europe_research(args.competition,args.home,args.away,
                                      args.date,args.time,index=index)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
if __name__=="__main__":main()
