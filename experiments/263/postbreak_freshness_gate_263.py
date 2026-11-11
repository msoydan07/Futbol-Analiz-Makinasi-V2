"""Narrow Nov 2026 international-break history freshness exception.

No general 10->30-day expansion. Only ENG1/ENG2, only a strictly bounded
first weekend after the officially published 9-17 Nov international window,
and ONLY an already live-verified named fixture from the reviewed official
schedule. This rule is research-only; official scores remain independently
source-graded. All other leagues and dates keep the original 10-day cap.
"""
from __future__ import annotations
from datetime import datetime,date,timezone

EXCEPTIONS={
 "ENG1":{
   "source":"https://www.premierleague.com/en/news/4725574",
   "support":"https://www.premierleague.com/en/news/4675097",
   "official_scope":"2026-11-21/2026-11-23",
 },
 "ENG2":{
   "source":"https://www.efl.com/news/2026/july/30/see-the-latest-sky-sports-tv-selections/",
   "support":"https://www.efl.com/supporters/faqs/fixtures/",
   "official_scope":"2026-11-21/2026-11-22",
 }
}
def freshness_gate(*,league,latest,match_date,gate,now,max_age=10):
    try:
        newest=date.fromisoformat(latest)
        day=date.fromisoformat(match_date)
        delta=(day-newest).days
    except (ValueError,TypeError):
        return {"status":"BLOCKED_INVALID_DATES","age_days":None}
    if delta<0:
        return {"status":"BLOCKED_FUTURE_RESULT_DATE","age_days":delta}
    if delta<=max_age:
        return {"status":"NORMAL_TEN_DAY_LIMIT","age_days":delta}
    cfg=EXCEPTIONS.get(league)
    if not cfg or delta>16 or not date(2026,11,7)<=newest<=date(2026,11,9):
        return {"status":"BLOCKED_STALE_REFRESH_REQUIRED","age_days":delta}
    first,last=cfg["official_scope"].split("/")
    if not date.fromisoformat(first)<=day<=date.fromisoformat(last):
        return {"status":"BLOCKED_OUTSIDE_REVIEWED_BREAK_WINDOW","age_days":delta}
    if not isinstance(gate,dict) or gate.get("status")!="VERIFIED" or gate.get("source_url")!=cfg["source"]:
        return {"status":"BLOCKED_NO_LIVE_NAMED_SCHEDULE","age_days":delta}
    if not isinstance(now,datetime) or now.tzinfo is None:
        return {"status":"BLOCKED_AWARE_NOW_REQUIRED","age_days":delta}
    try:
        checked=datetime.fromisoformat(gate["retrieved_at_utc"].replace("Z","+00:00"))
        kickoff=datetime.fromisoformat(gate["kickoff_utc"].replace("Z","+00:00"))
        if checked.tzinfo is None or kickoff.tzinfo is None:
            raise ValueError("not aware")
        checked=checked.astimezone(timezone.utc)
        kickoff=kickoff.astimezone(timezone.utc)
    except (KeyError,ValueError,TypeError):
        return {"status":"BLOCKED_NO_REAL_KICKOFF_EVIDENCE","age_days":delta}
    current=now.astimezone(timezone.utc)
    if not checked<=current<kickoff or (current-checked).total_seconds()>86400:
        return {"status":"BLOCKED_SOURCE_EXPIRED_OR_KICKOFF_PASSED","age_days":delta}
    return {
       "status":"REVIEWED_FIRST_POST_BREAK_SCHEDULE_ONLY",
       "age_days":delta,
       "league":league,
       "source":cfg["source"],
       "official_schedule_context":cfg["support"],
       "no_blanket_stale_history_waiver":True,
       "independently_verified_all_results":False,
       "betting_authorized":False,
    }
