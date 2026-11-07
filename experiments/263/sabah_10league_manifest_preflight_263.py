"""Read-only 10-league official fixture discovery for the Turkey morning session.

Do not claim empty official pages prove zero fixtures. Only timed official-page
entries with unique canonical 2026-27 membership can enter the candidate
manifest, and those still MUST pass sabah_batch's fresh named-match official gate.
NO bookmaker calls, predictions, pilot registration, result rewriting, or retries.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from official_page_lookup_263 import SOURCES
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway

SCHEMA="263_10_LEAGUE_SAME_DAY_OFFICIAL_MANIFEST_PREFLIGHT_V1"
TR=ZoneInfo("Europe/Istanbul")
DAY_INPUT="SABAH_TOPLU_V1"
class IntakeBlocked(ValueError):pass

def inspect(day,*,gateway=None,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise IntakeBlocked("AWARE_TIME_REQUIRED")
    now=now.astimezone(timezone.utc)
    if not isinstance(day,str) or date.fromisoformat(day)!=now.astimezone(TR).date():
        raise IntakeBlocked("ONLY_CURRENT_TURKEY_DAY")
    gateway=gateway or OfficialFixtureGateway(clock=lambda:now)
    results=[];candidates=[];keys=set()
    for league in SOURCES:
        source=gateway._get(league)
        status=source.get("status")
        events=source.get("events") or []
        league_candidates=[]
        rejects=Counter()
        per_pair=defaultdict(list)
        for event in events:
            if not isinstance(event,dict):
                rejects["INVALID_EVENT"]+=1;continue
            iso=event.get("kickoff_utc")
            if not iso:
                rejects["DATE_ONLY_OR_NO_KICKOFF"]+=1;continue
            try:
                ko=datetime.fromisoformat(iso.replace("Z","+00:00"))
                if ko.tzinfo is None:raise ValueError("NAIVE_KO")
                ko=ko.astimezone(timezone.utc)
                if ko.astimezone(TR).date().isoformat()!=day:continue
                if ko<=now:rejects["ALREADY_STARTED"]+=1;continue
                home=gateway.resolve_id(league,event.get("home"))
                away=gateway.resolve_id(league,event.get("away"))
                if home==away:raise ValueError("SAME_TEAM")
            except (TypeError,KeyError,ValueError) as exc:
                rejects["NOT_CANONICAL_OR_WRONG_KICKOFF"]+=1
                continue
            pair=(home,away)
            per_pair[pair].append((ko,event))
        for pair,items in per_pair.items():
            if len(items)!=1:
                rejects["DUPLICATE_OR_AMBIGUOUS"]+=len(items);continue
            ko,e=items[0]
            key=(league,pair[0],pair[1],ko.isoformat())
            if key in keys:raise IntakeBlocked("DUPLICATE_CROSS_SOURCE_ENTRY")
            keys.add(key)
            row={"league":league,"home":e["home"],"away":e["away"],
                 "home_id":pair[0],"away_id":pair[1],
                 "kickoff_utc":ko.isoformat(),
                 "official_source_url":source.get("effective_url") or source.get("source_url"),
                 "official_html_sha256":source.get("html_sha256"),
                 "source_parser":e.get("format"),
                 "status":"CANONICAL_OFFICIAL_PAGE_CANDIDATE_REQUIRES_FRESH_NAMED_GATE"}
            league_candidates.append(row)
            candidates.append(row)
        results.append({
            "league":league,"source_status":status,
            "official_source_url":source.get("effective_url") or source.get("source_url"),
            "official_html_sha256":source.get("html_sha256"),
            "source_event_count":len(events),
            "same_day_canonical_timed_candidates":len(league_candidates),
            "rejected":dict(rejects),
            "coverage_claim":"PARTIAL_OFFICIAL_SOURCE_OBSERVATION_NOT_COMPLETE_LEAGUE",
            "blocker":(
                "SOURCE_FETCH_FAILED" if status!="FETCHED_OFFICIAL_PAGE" else
                "SOURCE_HAS_NO_CANONICAL_TIMED_MATCHES_FOR_DAY_OR_JS_UNREADABLE"
                if not league_candidates else
                "UNIQUE_OFFICIAL_CANDIDATES_FOUND_STILL_NEEDS_NAMED_GATE"),
            "source_failure":source.get("reason")})
    if len(results)!=10:raise IntakeBlocked("MUST_INSPECT_ALL_TEN_LEAGUES")
    out={"schema":SCHEMA,"day_turkey":day,"checked_at_utc":now.isoformat(),
         "league_count":len(results),"source_coverage":results,
         "candidate_count":len(candidates),"candidates":candidates,
         "all_ten_leagues_claimed_fully_covered":False,
         "zero_matches_is_not_evidence_of_no_fixtures":True,
         "does_not_write_pilot_or_place_bets":True,
         "bookmaker_api_calls":0,"new100_pilot_count_change":0}
    return out

def manifest(result):
    if result.get("schema")!=SCHEMA:raise IntakeBlocked("INVALID_PREFLIGHT_RESULT")
    rows=[{"league":r["league"],"home":r["home"],"away":r["away"]}
          for r in result["candidates"]]
    # Do not write files that trigger the user-named pilot flow.
    return {"schema":DAY_INPUT,"day_turkey":result["day_turkey"],
            "matches":rows,"candidate_only_not_new100_authorized":True}

def mobile(result):
    lines=["# Makina 2.6.3 — 10 lig canlı resmî fikstür ön-denetimi",
           "Türkiye günü: "+result["day_turkey"],"",
           "**Bu, maç analizi ve Pinnacle mühürü değildir.**",
           "Kaynak boşsa o ligde maç YOK denmez. Resmî ad+kickoff kapısı sonraki aşamada ayrıca uygulanır.","",
           "| Lig | Kaynak | Zamanlı kanonik aday | Durum |",
           "|---|---|---:|---|"]
    for r in result["source_coverage"]:
        lines.append("| "+r["league"]+" | "+str(r["source_status"])+" | "+
                     str(r["same_day_canonical_timed_candidates"])+" | "+r["blocker"]+" |")
    lines+=["","Toplam görülen kanonik, kaynak zamanlı aday: **"+
            str(result["candidate_count"])+"**",
            "Sessizce atlanan lig: **0/10**; kaynağı eksik olanlar tabloda engel olarak görünüyor.",
            "Kredi: **0**; pilotta yeni maç: **0**."]
    return "\n".join(lines)+"\n"

def write(path,data):
    dest=Path(path);dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf-8") as f:
        if isinstance(data,str):f.write(data)
        else:json.dump(data,f,ensure_ascii=False,indent=2,sort_keys=True);f.write("\n")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--day",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--mobile",required=True)
    p.add_argument("--candidate-manifest",required=True)
    args=p.parse_args()
    result=inspect(args.day)
    write(args.out,result);write(args.mobile,mobile(result))
    write(args.candidate_manifest,manifest(result))
    print(json.dumps({"ten_leagues_checked":10,
         "official_timed_candidates":result["candidate_count"],
         "source_blockers":{r["league"]:r["blocker"] for r in result["source_coverage"]},
         "pilot_records":0,"bookmaker_api_calls":0},ensure_ascii=False))
if __name__=="__main__":main()
