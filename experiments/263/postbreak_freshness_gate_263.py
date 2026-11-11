"""One-season, strictly dated 2026 international-break data-age gate.

Allows research calculations for an independently confirmed Nov 2026 match
when source results were last recorded immediately before the actual league
hiatus. This is not general permission to ignore stale data: the league,
fixture source, one first-return round, signed snapshot and pre-kickoff official
check must ALL qualify. Never rewrites old forecasts or approves betting.
"""
from __future__ import annotations
from datetime import datetime,date,timezone

# League-approved, published 2026/27 first-return sources. The league must
# actually offer a named, timezone-aware fixture at these URLs; data-age alone
# NEVER promotes a fixture. POR1's Nov 27 return has a longer verified hiatus.
EXCEPTIONS={
 "ENG1":{"source":"https://www.premierleague.com/en/news/4725574","official_scope":"2026-11-21/2026-11-23","max_age":16},
 "ENG2":{"source":"https://www.efl.com/news/2026/july/30/see-the-latest-sky-sports-tv-selections/","official_scope":"2026-11-21/2026-11-22","max_age":16},
 "GER1":{"source":"https://products.bundesliga.com/fixtures","official_scope":"2026-11-20/2026-11-22","max_age":16},
 "ESP1":{"source":"https://www.laliga.com/laliga-easports/resultados/2026-27/jornada-13","official_scope":"2026-11-20/2026-11-23","max_age":16},
 "ITA1":{"source":"https://api-sdp.legaseriea.it/v1/serie-a/football/seasons/serie-a%3A%3AFootball_Season%3A%3Aed7fdc2a3e7b408b942ec177b7b956b5/matches?locale=en-GB","official_scope":"2026-11-21/2026-11-23","max_age":16},
 "FRA1":{"source":"https://ligue1.com/fr/articles/l1_article_5839-","official_scope":"2026-11-20/2026-11-22","max_age":16},
 "NED1":{"source":"https://www.knvb.nl/competities/eredivisie/programma","official_scope":"2026-11-21/2026-11-22","max_age":16},
 "TUR1":{"source":"https://www.tff.org/Default.aspx?hafta=12&pageId=198","official_scope":"2026-11-21/2026-11-23","max_age":16},
 "POR1":{"source":"https://www.ligaportugal.pt/noticias/28531/horarios-definidos-ate-a-12.a-jornada","official_scope":"2026-11-27/2026-11-30","max_age":23},
 "BEL1":{"source":"https://www.proleague.be/jpl-kalender!","official_scope":"2026-11-20/2026-11-22","max_age":16},
}
def freshness_gate(*,league,latest,match_date,gate,now,max_age=10):
    try:
        newest=date.fromisoformat(latest)
        day=date.fromisoformat(match_date)
        delta=(day-newest).days
    except (ValueError,TypeError):
        return {"status":"BLOCKED_INVALID_DATES","age_days":None}
    if delta<0:return {"status":"BLOCKED_FUTURE_RESULT_DATE","age_days":delta}
    if delta<=max_age:return {"status":"NORMAL_TEN_DAY_LIMIT","age_days":delta}
    cfg=EXCEPTIONS.get(league)
    if not cfg or delta>cfg["max_age"] or not date(2026,11,7)<=newest<=date(2026,11,8):
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
        if checked.tzinfo is None or kickoff.tzinfo is None:raise ValueError("not aware")
        checked=checked.astimezone(timezone.utc)
        kickoff=kickoff.astimezone(timezone.utc)
    except (KeyError,ValueError,TypeError):
        return {"status":"BLOCKED_NO_REAL_KICKOFF_EVIDENCE","age_days":delta}
    current=now.astimezone(timezone.utc)
    if not checked<=current<kickoff or (current-checked).total_seconds()>86400:
        return {"status":"BLOCKED_SOURCE_EXPIRED_OR_KICKOFF_PASSED","age_days":delta}
    return {
       "status":"REVIEWED_FIRST_POST_BREAK_SCHEDULE_ONLY",
       "age_days":delta,"league":league,"source":cfg["source"],
       "no_blanket_stale_history_waiver":True,
       "independently_verified_all_results":False,"betting_authorized":False}
