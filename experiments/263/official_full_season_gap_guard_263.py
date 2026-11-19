"""Read-only 2.6.3 official season-calendar gap verification (research only).

Never promotes a private 4,618 snapshot, unlocks M4, or creates a seal.
An official URL / a single round / date-only excerpt cannot prove a date gap.
For genuine evidence this module fetches official HTML itself, validates its
redirect, and requires a complete 2026/27 round-robin fixture list.
Suspicious matches in a supposedly empty gap BLOCK; no inferred final scores.
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone

EXPECTED_TEAMS = {'BEL1':18,'ENG1':20,'ENG2':24,'ESP1':20,'FRA1':18,
                  'GER1':18,'ITA1':20,'NED1':18,'POR1':18,'TUR1':18}
SEASON_FIRST, SEASON_LAST = date(2026,8,1), date(2027,6,30)

class OfficialGapBlocked(ValueError):
    pass


def evaluate_full_fixture_set(league: str, start: str, end: str, events: list):
    """Reject partial fixture pages; never infer the existence of full-time scores."""
    if league not in EXPECTED_TEAMS:
        raise OfficialGapBlocked('LEAGUE_NOT_SUPPORTED')
    begin, finish = date.fromisoformat(start), date.fromisoformat(end)
    if not SEASON_FIRST <= begin <= finish <= SEASON_LAST:
        raise OfficialGapBlocked('WINDOW_OUTSIDE_2026_27_SEASON')
    if not isinstance(events, list):
        raise OfficialGapBlocked('SOURCE_EVENTS_NOT_LIST')
    n = EXPECTED_TEAMS[league]
    expected = n*(n-1)
    if len(events) < expected:
        raise OfficialGapBlocked('OFFICIAL_SOURCE_PARTIAL_LEAGUE_FIXTURES')
    fixtures = {}; teams=set()
    for e in events:
        if not isinstance(e,dict):
            raise OfficialGapBlocked('INVALID_OFFICIAL_EVENT')
        h,a=e.get('home'),e.get('away')
        if not isinstance(h,str) or not isinstance(a,str) or not h.strip() or not a.strip() or h==a:
            raise OfficialGapBlocked('INVALID_TEAM_PAIR')
        d=date.fromisoformat(str(e.get('match_date','')))
        if not SEASON_FIRST<=d<=SEASON_LAST:
            raise OfficialGapBlocked('OTHER_SEASON_IN_OFFICIAL_SOURCE')
        key=(h.casefold().strip(),a.casefold().strip())
        teams.update(key)
        if key in fixtures:
            raise OfficialGapBlocked('DUPLICATE_DIRECTED_PAIR_OR_PLAYOFF_MIXED')
        fixtures[key]=d
    if len(teams)!=n or len(fixtures)!=expected:
        raise OfficialGapBlocked('OFFICIAL_SOURCE_NOT_COMPLETE_ROUND_ROBIN')
    if min(fixtures.values())>date(2026,9,5) or max(fixtures.values())<date(2027,4,15):
        raise OfficialGapBlocked('OFFICIAL_SOURCE_DATE_SPAN_TOO_SHORT')
    inside=sorted((d.isoformat(),h,a) for (h,a),d in fixtures.items() if begin<=d<=finish)
    return {'schema':'263_OFFICIAL_FULL_SEASON_FIXTURE_WINDOW_RESEARCH_V1',
            'league':league,'window_start':start,'window_end':end,
            'season_fixtures_verified':len(fixtures),'teams_verified':len(teams),
            'status':('OFFICIAL_SCHEDULE_CONTAINS_MATCH_IN_GAP_REVIEW_RESULTS'
                      if inside else 'OFFICIAL_FULL_SCHEDULE_HAS_NO_MATCH_IN_GAP'),
            'scheduled_in_gap':[list(x) for x in inside],
            'calendar_gap_supported':not bool(inside),
            'full_time_results_independently_verified':False,
            'production_forecast_allowed':False}


def fetch_official_full_window(league, start, end, *, source_url=None, fetcher=None,
                               parser=None, now_utc=None):
    """Fetch official bytes once, then parse with existing repo adapters.

    Callable injectors are test-only. They never grant independent live approval.
    """
    from official_page_lookup_263 import (SOURCES,is_approved_url,_default_fetch,
                                          parse_official_events)
    if league not in EXPECTED_TEAMS:
        raise OfficialGapBlocked('LEAGUE_NOT_SUPPORTED')
    url=source_url or SOURCES[league][0]
    if not is_approved_url(url,league):
        raise OfficialGapBlocked('SOURCE_NOT_OFFICIAL_LEAGUE_HOST')
    fetch=fetcher or _default_fetch
    target,html=fetch(url,league)
    if not is_approved_url(target,league):
        raise OfficialGapBlocked('REDIRECT_NOT_OFFICIAL_LEAGUE_HOST')
    if not isinstance(html,str) or not 100<=len(html)<=2_000_000:
        raise OfficialGapBlocked('OFFICIAL_HTML_EMPTY_OR_TOO_LARGE')
    events=(parser or parse_official_events)(league,html)
    out=evaluate_full_fixture_set(league,start,end,events)
    observed=now_utc or datetime.now(timezone.utc)
    if observed.tzinfo is None:raise OfficialGapBlocked('NAIVE_OBSERVATION_TIME')
    return {**out,'source_url':target,
            'source_html_sha256':hashlib.sha256(html.encode('utf-8')).hexdigest(),
            'observed_at_utc':observed.astimezone(timezone.utc).isoformat(),
            'source_bytes_actually_fetched_by_script':fetcher is None,
            'real_official_source_acceptance':False,
            'research_only_no_m4_lock_or_seal_change':True}
