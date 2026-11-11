"""Iddaa PDF: current official fixture page only, no static old-week adapter.

This is a narrow research-only source admission gateway. It cannot assert that
all clubs/competitions are covered by one published calendar. The EFL TV page
is explicitly a partial list. No unverified fixture is allowed to become a
forecast. No odds or external bookmaker calls.
"""
from __future__ import annotations
from datetime import datetime,timezone
from official_page_lookup_263 import (
    SOURCES,official_page_lookup,_default_fetch)
from iddaa_pdf_team_alias_preflight_263 import index_registry,resolve_label

# Explicit CURRENT fixture surface replacements for the stale week-11 news
# articles. If a source is JS-only or has no timed SportsEvent, block that row.
CURRENT_PAGES={
    "ENG1":("https://www.premierleague.com/en/news/4725574",
            "epl_nov26_confirmed","OFFICIAL_NOVEMBER_REVISED_ALL_LEAGUE_GAMES"),
    "ENG2":("https://www.efl.com/news/2026/july/30/see-the-latest-sky-sports-tv-selections/",
            "efl_2026_27_official_tv_selection","OFFICIAL_PARTIAL_TELEVISED_ONLY"),
    "TUR1":("https://www.tff.org/Default.aspx?hafta=12&pageId=198",
            "tff_2026_week12","OFFICIAL_2026_NOV12_TURKISH_SUPERLIG_FULL_ROUND"),
    "FRA1":("https://ligue1.com/fr/articles/l1_article_5839-",
            "ligue1_2026_round11_tv","OFFICIAL_NOVEMBER_ROUND11_TV_9_FIXTURES"),
    "POR1":("https://www.ligaportugal.pt/noticias/28531/horarios-definidos-ate-a-12.a-jornada",
            "ligaportugal_2026_round12_tv","OFFICIAL_NOVEMBER_ROUND12_TV_9_FIXTURES"),
    "ESP1":("https://www.laliga.com/laliga-easports/resultados/2026-27/jornada-13",
            "jsonld","TIMED_JSONLD_ONLY_NO_HTML_INFERENCE"),
    "ITA1":("https://www.legaseriea.it/serie-a/calendario-risultati",
            "jsonld","TIMED_JSONLD_ONLY_NO_HTML_INFERENCE"),
}
# Pages in the existing experiment may be date-scoped to the expired J11.
# Never reuse those stale pages for a future PDF-first prediction.
UNSAFE_OLD_WEEK={"ESP1","ITA1","FRA1"}

def lookup(league,home,away,*,now=None,fetcher=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        return {"status":"NOT_VERIFIED","reason":"timezone_required"}
    if league not in SOURCES:
        return {"status":"NOT_VERIFIED","reason":"outside_ten_leagues"}
    index,_,_=index_registry()
    def same_team(observed,requested):
        left=resolve_label(league,observed,index)
        right=resolve_label(league,requested,index)
        return (left.get("status")=="MAPPED" and right.get("status")=="MAPPED"
                and left.get("team_id")==right.get("team_id"))
    # Use only the current approved published league page. All ambiguous or
    # missing timestamps fail closed; never use stale referee announcements.
    # They are still fail-closed if the actual official page cannot be parsed.
    if league in ():
        from mackolik_identity_gate_263 import OFFICIAL_ADAPTERS
        from importlib import import_module
        if fetcher is not None:
            return {"status":"NOT_VERIFIED","reason":"no_injected_legacy_fetch"}
        return import_module(OFFICIAL_ADAPTERS[league]).lookup(home,away,now=now)
    url,parser,coverage=(CURRENT_PAGES.get(league)
                or (*SOURCES[league][::2], "SINGLE_OFFICIAL_PAGE_PARTIAL_COVERAGE"))
    if league in UNSAFE_OLD_WEEK and league not in CURRENT_PAGES:
        return {"status":"NOT_VERIFIED","reason":"no_current_official_schedule"}
    def load(page):
        return fetcher(page) if fetcher else _default_fetch(page,league)
    found=official_page_lookup(league,home,away,now=now,source_url=url,
                              parser=parser,same_team=same_team,fetcher=load)
    if found.get("status")=="VERIFIED_OFFICIAL_FIXTURE":
        # The returned page has an explicit time and exact canonical team order.
        found["coverage"]=coverage
        found["official_live_page_not_old_week"]=True
    return found
