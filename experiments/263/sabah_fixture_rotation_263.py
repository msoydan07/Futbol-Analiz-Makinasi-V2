"""2.6.3 read-only fixture preparation and qualitative congestion notes.

This module NEVER discovers or fabricates an official fixture. The legacy
96-candidate file is date-only; preparing it is NOT a pre-match prediction.
Live fixtures must separately pass the repository's official on-demand gate.
Adjacent competition schedules may be incomplete; report that explicitly.
"""
from __future__ import annotations
import argparse
import json
import hashlib
from collections import Counter
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TR = ZoneInfo("Europe/Istanbul")
CANDIDATES_SCHEMA = "263_LOCAL_TEN_LEAGUE_DATE_ONLY_WEEKEND_PREP_V1"
PLAN_SCHEMA = "SABAH_FIKSTUR_HAZIRLIK_V1"
ROT_SCHEMA = "ROTASYON_BILGI_V1"
EXPECTED_DAYS = {"2026-11-06":10,"2026-11-07":44,"2026-11-08":42,"2026-11-09":0}
LEAGUES = frozenset(("ENG1","ENG2","GER1","ESP1","ITA1","FRA1",
                      "NED1","TUR1","POR1","BEL1"))
COMPETITIONS = frozenset(("LIG","UCL","UEL","UECL","YEREL_KUPA","DIGER_KUPA"))
RISK_STATUSES = frozenset(("BELIRGIN_ISARET_YOK","INCELENMELI",
                            "YUKSEK_RISK_UYARISI","VERI_YETERSIZ"))
class FixturePreparationError(ValueError): pass

def aware(value):
    if not isinstance(value,str):
        raise FixturePreparationError("TIME_REQUIRED")
    try: t=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc: raise FixturePreparationError("BAD_TIME") from exc
    if t.tzinfo is None: raise FixturePreparationError("TIMEZONE_REQUIRED")
    return t.astimezone(timezone.utc)

def validate_legacy_candidates(data):
    if not isinstance(data,dict) or data.get("schema")!=CANDIDATES_SCHEMA:
        raise FixturePreparationError("WRONG_LEGACY_COHORT_SCHEMA")
    if data.get("fixture_count")!=96 or data.get("day_counts")!=EXPECTED_DAYS:
        raise FixturePreparationError("LEGACY_96_COHORT_COUNTS_CHANGED")
    rows=data.get("fixtures")
    if not isinstance(rows,list) or len(rows)!=96:
        raise FixturePreparationError("LEGACY_96_COHORT_LENGTH_CHANGED")
    seen=set()
    for r in rows:
        if not isinstance(r,dict) or r.get("date") not in EXPECTED_DAYS or r.get("league") not in LEAGUES:
            raise FixturePreparationError("INVALID_LEGACY_FIXTURE")
        if not all(isinstance(r.get(k),str) and r[k].strip() for k in ("home","away")) or r["home"]==r["away"]:
            raise FixturePreparationError("BAD_LEGACY_TEAMS")
        key=(r["date"],r["league"],r["home"],r["away"])
        if key in seen: raise FixturePreparationError("DUPLICATE_LEGACY_FIXTURE")
        seen.add(key)
        if (r.get("status")!="DAY_ONLY_PREPARATION_NOT_FORECAST" or
            r.get("kickoff_turkey") is not None or
            r.get("fixture_verified_kickoff_utc") is not None):
            raise FixturePreparationError("LEGACY_FIXTURE_IMPROPERLY_UPGRADED")
    if dict(Counter(r["date"] for r in rows)) != {k:v for k,v in EXPECTED_DAYS.items() if v}:
        raise FixturePreparationError("LEGACY_DAY_BREAKDOWN_CHANGED")
    return rows

def prepare_day(data,day):
    rows=validate_legacy_candidates(data)
    if day not in EXPECTED_DAYS: raise FixturePreparationError("DAY_NOT_IN_FROZEN_COHORT")
    items=[{"date":r["date"],"league":r["league"],"home":r["home"],"away":r["away"],
            "kickoff_turkey":None,"official_status":"TEYIT_BEKLIYOR",
            "source_grade":r.get("source_grade"),"forecast_written":False}
            for r in rows if r["date"]==day]
    return {"schema":PLAN_SCHEMA,"day_turkey":day,
            "cohort_id":"LEGACY_96_2026_11_06_08_DATE_ONLY",
            "cohort_is_immutable":True,"separate_new_100_sabah_cohort":True,
            "fixtures":items,"candidate_count":len(items),
            "officially_verified_kickoffs":0,"morning_forecast_count_increment":0,
            "price_calls":0,
            "not_a_forecast":True,"not_an_official_kickoff_verification":True}

def rotation_from_official_inputs(target, adjacent, now, *, feeds_complete=None):
    """Read-only, REQUEST-ANCHORED 7-day workload and qualitative rotation hint.

    Previous seven days and next seven days are measured from the instant the
    user requested analysis, NOT from a future kickoff. Rest hours are measured
    relative to the actual target kickoff using verified events in that window.

    The caller must independently verify official match times. A VERIFIED
    marker alone proves nothing; this code changes no model probabilities.
    Missing UEFA/cup feeds are UNKNOWN, never a clean-schedule claim.
    """
    if now.tzinfo is None: raise FixturePreparationError("AWARE_NOW_REQUIRED")
    if not isinstance(target,dict) or target.get("status")!="VERIFIED":
        raise FixturePreparationError("TARGET_OFFICIAL_GATE_REQUIRED")
    if target.get("league") not in LEAGUES: raise FixturePreparationError("TARGET_LEAGUE_NOT_ALLOWED")
    home,away=target.get("home_id"),target.get("away_id")
    if not isinstance(home,str) or not isinstance(away,str) or not home or not away or home==away:
        raise FixturePreparationError("TARGET_IDENTITY_INVALID")
    if not str(target.get("source_url","")).startswith("https://"):
        raise FixturePreparationError("TARGET_OFFICIAL_URL_REQUIRED")
    ko=aware(target.get("kickoff_utc"))
    if not now.astimezone(timezone.utc)<ko: raise FixturePreparationError("TARGET_NOT_PREMATCH")
    if not isinstance(adjacent,list):raise FixturePreparationError("ADJACENT_SCHEDULE_LIST_REQUIRED")
    asof=now.astimezone(timezone.utc)
    window_start=asof-timedelta(days=7)
    window_end=asof+timedelta(days=7)
    feeds_complete=feeds_complete or {}
    out={}
    for team in (home,away):
        past=[];upcoming=[];verified_before_target=[];verified_after_target=[]
        unknown=0;seen=set()
        for event in adjacent:
            if not isinstance(event,dict):raise FixturePreparationError("ADJACENT_EVENT_INVALID")
            if event.get("team_id")!=team:continue
            event_time=aware(event.get("kickoff_utc"))
            if event_time==ko:continue
            if not (window_start<=event_time<asof or asof<event_time<=window_end):
                continue
            key=(team,event_time,event.get("competition"))
            if key in seen:raise FixturePreparationError("DUPLICATE_ADJACENT_GAME")
            seen.add(key)
            if (event.get("verification")!="VERIFIED_OFFICIAL_ADAPTER"
                or not str(event.get("source_url","")).startswith("https://")
                or event.get("competition") not in COMPETITIONS):
                unknown+=1
                continue
            item={"utc":event_time.isoformat(),"competition":event["competition"],
                  "source_url":event["source_url"],"opponent":event.get("opponent") or "BILINMIYOR",
                  "hours_from_target":round((event_time-ko).total_seconds()/3600,1)}
            if event_time<asof:past.append(item)
            else:upcoming.append(item)
            if event_time<ko:verified_before_target.append(event_time)
            else:verified_after_target.append(event_time)
        past.sort(key=lambda x:x["utc"]);upcoming.sort(key=lambda x:x["utc"])
        prior_hours=(round((ko-max(verified_before_target)).total_seconds()/3600,1)
                     if verified_before_target else None)
        future_hours=(round((min(verified_after_target)-ko).total_seconds()/3600,1)
                      if verified_after_target else None)
        dense=(prior_hours is not None and prior_hours<=72) or (future_hours is not None and future_hours<=72)
        complete=feeds_complete.get(team) is True
        if dense or len(past)>=3 or len(upcoming)>=4:
            level="INCELENMELI"
            reason="DOGRULANMIS_YAKIN_MUSABAKA_VEYA_YOGUN_FIKSTUR"
        elif not complete or unknown:
            level="VERI_YETERSIZ"
            reason="TUM_KUPA_VE_LIG_FIKSTURU_DOGRULANMADI"
        else:
            level="BELIRGIN_ISARET_YOK"
            reason="ELDEKI_DOGRULANMIS_FIKSTURDE_KISA_DINLENME_ISARETI_YOK"
        out[team]={"past_7_days":past,"next_7_days":upcoming,
                   "last_rest_hours":prior_hours,"next_match_gap_hours":future_hours,
                   "unverified_adjacent_count":unknown,
                   "rotation_label":level,"reason":reason,
                   "schedule_completeness_reported_by_upstream":complete,
                   "actual_lineup_unknown":True,
                   "rotation_will_happen_not_assumed":True,
                   "quantitative_model_adjustment":0}
        if out[team]["rotation_label"] not in RISK_STATUSES:
            raise AssertionError("ROTATION_LABEL_UNKNOWN")
    return {"schema":ROT_SCHEMA,"analysis_requested_at_utc":asof.isoformat(),
            "window_previous_utc":window_start.isoformat(),
            "window_next_utc":window_end.isoformat(),
            "window_basis":"ANALYSIS_REQUEST_PLUS_MINUS_SEVEN_DAYS",
            "target_kickoff_utc":ko.isoformat(),
            "target_source_url":target["source_url"],"home_id":home,"away_id":away,
            "teams":out,"forecast_changed":False,"model_probabilities_changed":False,
            "schedule_source_verification_must_be_performed_upstream":True}

def render_mobile(plan):
    if plan.get("schema")!=PLAN_SCHEMA:raise FixturePreparationError("WRONG_PLAN")
    lines=["# Makina 2.6.3 — "+plan["day_turkey"]+" TSİ fikstür ön hazırlığı",
           "",
           "**"+str(plan["candidate_count"])+" sabit kohort adayı. Başlama saatleri henüz resmen teyit edilmedi.**",
           "Bu tablo sabah tahmini, Pinnacle fiyatı veya bahis seçimi değildir.",
           ""]
    by={}
    for row in plan["fixtures"]:by.setdefault(row["league"],[]).append(row)
    for league,items in by.items():
        lines.extend(["## "+league+" — "+str(len(items))+" aday",""])
        for row in items:
            text=row["home"].replace("|","/")+" – "+row["away"].replace("|","/")
            lines.append("- **Saat: TEYİT BEKLİYOR** · "+text)
        lines.append("")
    lines.extend(["---","Kapsam: "+str(plan["candidate_count"])+" aday / 0 doğrulanmış saat / 0 yeni sabah tahmini.",
                  "96 adaylık eski kohort değiştirilmez; ayrı 100 maçlık yeni sabah pilotuna otomatik aktarılmaz.",""])
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",required=True);p.add_argument("--day",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    plan=prepare_day(json.loads(Path(args.candidates).read_text(encoding="utf-8")),args.day)
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf-8") as out:out.write(render_mobile(plan))
    print(json.dumps({"schema":plan["schema"],"day":args.day,
                      "candidate_count":plan["candidate_count"],
                      "verified_kickoffs":0,"new_predictions":0},ensure_ascii=False))
if __name__=="__main__":main()
