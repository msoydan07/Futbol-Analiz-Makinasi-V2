"""UEFA named fixture OFFLINE WEB HANDOFF (source reviewed in ChatGPT browser).

This is an operational fallback when GitHub Actions cannot connect to www.uefa.com.
Must be used only after the assistant independently reads the named UEFA official
article with web search/open and writes minimal factual fixture evidence.

DOES NOT FETCH THE UEFA PAGE and cannot prove that evidence JSON is authentic.
Output is labelled ASSISTED_SOURCE_EVIDENCE, never LIVE_RUNNER_VERIFIED.
Scope gate happens before reading the evidence file. No other league research,
stats, team ratings, guesses, odds, model integration, A/B/C or pilot.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime,date,time,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from uefa_ten_league_scope_gate_263 import check_europe_scope,norm,INDEX_DEFAULT
from uefa_requested_match_entry_263 import SOURCES,index_with_reviewed_uefa_names

SCHEMA="263_UEFA_OFFICIAL_WEB_ASSISTED_FACTS_V1"
VERSION="263_UEFA_ON_DEMAND_OFFLINE_WEB_HANDOFF_V1"
TIME_RULE="Kick-offs are 21:00 unless stated; all times CET."
CET=timezone(timedelta(hours=1))
DATE_RE=re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) (\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December) 2026$",re.I)
MATCH_RE=re.compile(r"^(?P<home>.+?) vs (?P<away>.+?)(?: \((?P<clock>\d\d:\d\d)\))?$")
MAX_BYTES=32_000

class HandoffError(ValueError):pass

def validate_evidence(evidence, competition, now):
    if not isinstance(evidence,dict) or set(evidence)!={"schema","checked_on_istanbul","sources","fixtures","source_access_method"}:
        raise HandoffError("WEB_EVIDENCE_SHAPE_INVALID")
    if evidence["schema"]!=SCHEMA or evidence["source_access_method"]!="ASSISTANT_WEB_OFFICIAL_ARTICLE_REFERENCE":
        raise HandoffError("EVIDENCE_CAPTURE_METHOD_NOT_ACCEPTED")
    if not isinstance(evidence["sources"],dict) or set(evidence["sources"])!=set(SOURCES):
        raise HandoffError("OFFICIAL_SOURCE_LIST_CHANGED")
    for c,src in evidence["sources"].items():
        if not isinstance(src,dict) or set(src)!={"source_url","title","default_kickoff_statement"}:
            raise HandoffError("SOURCE_METADATA_INCOMPLETE")
        if (src["source_url"]!=SOURCES[c]
            or src["default_kickoff_statement"]!=TIME_RULE
            or "2026/27" not in src["title"]
            or ("Champions League" if c=="UEFA_CL" else "Europa League") not in src["title"]):
            raise HandoffError("SOURCE_METADATA_MISMATCH")
    try:checked=date.fromisoformat(evidence["checked_on_istanbul"])
    except (TypeError,ValueError) as exc:raise HandoffError("CHECKED_DATE_INVALID") from exc
    now_local=now.astimezone(ZoneInfo("Europe/Istanbul")).date()
    delta=(now_local-checked).days
    if not (0<=delta<=1):
        raise HandoffError("WEB_EVIDENCE_STALE_OR_FROM_FUTURE")
    if not isinstance(evidence["fixtures"],list) or len(evidence["fixtures"])>50:
        raise HandoffError("EVIDENCE_FIXTURE_COUNT_INVALID")
    return checked.isoformat()

def one_row(row,competition):
    if not isinstance(row,dict) or set(row)!={"competition","matchday","date_line","fixture_line"}:
        raise HandoffError("FIXTURE_FACT_FIELDS_INVALID")
    if row["competition"]!=competition:return None
    if type(row["matchday"]) is not int or not 1<=row["matchday"]<=8:
        raise HandoffError("MATCHDAY_INVALID")
    dm=DATE_RE.fullmatch(row["date_line"])
    if not dm:raise HandoffError("DATE_LINE_INVALID")
    try:
        day=datetime.strptime(row["date_line"],"%A %d %B %Y").date()
    except ValueError as exc:raise HandoffError("DATE_VALUE_INVALID") from exc
    if day.strftime("%A").casefold()!=dm.group(1).casefold():
        raise HandoffError("DATE_WEEKDAY_MISMATCH")
    m=MATCH_RE.fullmatch(row["fixture_line"])
    if not m:raise HandoffError("FIXTURE_LINE_IS_NOT_UNPLAYED")
    tm=m.group("clock") or "21:00"
    try:hour,minute=map(int,tm.split(":"));clock=time(hour,minute)
    except ValueError as exc:raise HandoffError("INVALID_MATCH_CLOCK") from exc
    ko=datetime.combine(day,clock,tzinfo=CET).astimezone(timezone.utc)
    return {"competition":competition,"round":"LEAGUE_PHASE","season":"2026-2027",
            "matchday":row["matchday"],"home_uefa_name":m.group("home"),
            "away_uefa_name":m.group("away"),"kickoff_utc":ko.isoformat(),
            "match_date":day.isoformat(),"kickoff_cet":tm,
            "kickoff_basis":("EXPLICIT_UEFA_ARTICLE_MATCH_CLOCK" if m.group("clock")
                             else "PUBLISHED_UEFA_ARTICLE_DEFAULT_21_CET"),
            "official_source_page":SOURCES[competition],
            "individual_match_page_independently_checked":False,
            "runner_http_fetch_verified":False}

def requested_from_web_evidence(competition,home,away,*,index,now=None,evidence=None,evidence_loader=None):
    if competition not in SOURCES:raise HandoffError("UNSUPPORTED_TOURNAMENT")
    now=now or datetime.now(timezone.utc)
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise HandoffError("AS_OF_NEEDS_TIMEZONE")
    reviewed_index=index_with_reviewed_uefa_names(index)
    scope=check_europe_scope(home,away,reviewed_index) # MUST be first; no evidence I/O
    result={"version":VERSION,"status":scope["status"],"message":scope["message"],
            "competition":competition,"requested_home":home,"requested_away":away,
            "scope":scope,"fixture":None,
            "official_UEFA_page_fetched_by_runner":False,
            "live_automated_UEFA_verification":False,
            "assisted_web_article_evidence_accepted":False,
            "real_uefa_team_id_crosswalk_verified":False,
            "model_forecast_authorized":False,"ABC_approved":False,
            "pilot_recorded":False,"main_modified":False,
            "data_provenance":"NO_OFFICIAL_EVIDENCE_PROCESSED"}
    if not scope["allow_further_research"]:
        return result
    try:
        if evidence is None and evidence_loader is not None:
            evidence=evidence_loader()
        checked=validate_evidence(evidence,competition,now)
        candidates=[]
        for raw in evidence["fixtures"]:
            fx=one_row(raw,competition)
            if fx is None:continue
            h=reviewed_index["aliases"].get(norm(fx["home_uefa_name"]))
            a=reviewed_index["aliases"].get(norm(fx["away_uefa_name"]))
            if h!=scope["home"]["canonical_team_id"] or a!=scope["away"]["canonical_team_id"]:
                continue
            kick=datetime.fromisoformat(fx["kickoff_utc"])
            if now.astimezone(timezone.utc)<kick<=now.astimezone(timezone.utc)+timedelta(days=7):
                candidates.append(fx)
        if len(candidates)!=1:
            raise HandoffError("NO_UNIQUE_FUTURE_FIXTURE_MATCH_IN_WEB_EVIDENCE")
        result["fixture"]=candidates[0]
        result["status"]="ASSISTED_WEB_OFFICIAL_ARTICLE_FIXTURE_REFERENCE_ACCEPTED"
        result["message"]="Resmî UEFA sayfasından ChatGPT web incelemesiyle alınmış kaynaklı maç bilgisi kabul edildi; GitHub canlı bağlantısı ve model henüz doğrulanmadı."
        result["assisted_web_article_evidence_accepted"]=True
        result["data_provenance"]="HUMAN_AUDITABLE_UEFA_URL_AND_ARTICLE_FACTS_NOT_RUNNER_REFETCHED"
        result["article_checked_on_istanbul"]=checked
    except (HandoffError,TypeError,ValueError) as exc:
        result["status"]="ASSISTED_OFFICIAL_WEB_EVIDENCE_NOT_ACCEPTED"
        result["message"]="Kaynaklı UEFA aktarımı doğrulanamadı veya güncel değil; analiz yapılmıyor."
        result["evidence_rejection_reason"]=str(exc)
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description="Safely consume assistant-fetched UEFA evidence, 10 league check FIRST")
    p.add_argument("--competition",choices=tuple(SOURCES),required=True)
    p.add_argument("--home",required=True)
    p.add_argument("--away",required=True)
    p.add_argument("--evidence-file",type=Path,required=True)
    p.add_argument("--index",type=Path,default=Path(INDEX_DEFAULT))
    p.add_argument("--as-of",default=None,help="UTC offset ISO; ONLY for reproducible CI demonstrations")
    args=p.parse_args(argv)
    now=datetime.fromisoformat(args.as_of.replace("Z","+00:00")) if args.as_of else datetime.now(timezone.utc)
    index=json.loads(args.index.read_text(encoding="utf-8"))
    def load():
        if not args.evidence_file.is_file() or args.evidence_file.stat().st_size>MAX_BYTES:
            raise HandoffError("EVIDENCE_FILE_MISSING_OR_OVERSIZED")
        return json.loads(args.evidence_file.read_text(encoding="utf-8"))
    output=requested_from_web_evidence(args.competition,args.home,args.away,index=index,now=now,evidence_loader=load)
    print(json.dumps(output,ensure_ascii=False,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
