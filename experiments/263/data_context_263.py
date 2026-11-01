"""2.6.3 offline historical-data context and evidence-honesty gate.

Only describes records already held at historical cut-off, with no external web/network
access. A URL in CSV is *a reference*, not independent verification of its content,
retrieval time, fixture, lineup or squad. Does not change expected-goal lambdas.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Any
from urllib.parse import urlparse
import hashlib
import json

VERSION = '263_data_context_v1_offline'
REQUIRED = ('league','season','previous_season','target_date','home_id','away_id')
GOAL_FIELDS = ('home_goals','away_goals')
HALF_FIELDS = ('half_time_home_goals','half_time_away_goals')
CORNER_FIELDS = ('home_corners','away_corners')
SHOT_FIELDS = ('home_shots','away_shots','home_shots_on_target','away_shots_on_target')

class DataContextError(ValueError):
    pass


def _count(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    s = str(value).strip()
    return int(s) if s.isascii() and s.isdigit() else None


def _source_provider(url: str) -> str | None:
    if not url:
        return None
    p = urlparse(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password:
        return None
    return p.hostname.lower().removeprefix('www.')


def _fields_status(rows: list[dict]) -> dict:
    n = len(rows)
    available = {key:0 for key in ('final_goals','first_half','full_time_corners','shots','xg')}
    for r in rows:
        hg, ag = _count(r.get('home_goals')), _count(r.get('away_goals'))
        if hg is not None and ag is not None:
            available['final_goals'] += 1
        ht = [_count(r.get(k)) for k in HALF_FIELDS]
        if all(v is not None for v in ht) and hg is not None and ag is not None and ht[0] <= hg and ht[1] <= ag:
            available['first_half'] += 1
        corners = [_count(r.get(k)) for k in CORNER_FIELDS]
        if all(v is not None and v <= 100 for v in corners):
            available['full_time_corners'] += 1
        shots = [_count(r.get(k)) for k in SHOT_FIELDS]
        if (all(v is not None for v in shots) and
            shots[2] <= shots[0] and shots[3] <= shots[1]):
            available['shots'] += 1
        # Historical core CSV does not provide per-match xG by default. A separate
        # joined vetted xG table would require an independently specified join.
        if all(str(r.get(k, '')).strip() for k in ('home_xg','away_xg')):
            try:
                xh, xa = float(r['home_xg']), float(r['away_xg'])
                if 0 <= xh <= 10 and 0 <= xa <= 10:
                    available['xg'] += 1
            except (TypeError, ValueError):
                pass
    return {key: {'usable': count, 'total': n, 'missing_or_quarantined': n-count}
            for key, count in available.items()}


def build_data_context(rows: list[dict], source: dict, case: dict) -> dict:
    """Describe historical evidence, not a verified future fixture or fresh news.

    Must be called with already validated rows and snapshot/source identity. Never
    reads later target-day observations, regardless of CSV containing newer data.
    """
    if not isinstance(case, dict) or not all(isinstance(case.get(k), str) and case[k] for k in REQUIRED):
        raise DataContextError('Missing context identity')
    try:
        target = date.fromisoformat(case['target_date'])
        if target.isoformat() != case['target_date']:
            raise ValueError('Noncanonical target date')
    except ValueError as ex:
        raise DataContextError('Invalid target date') from ex
    if case['home_id'] == case['away_id'] or case['season'] == case['previous_season']:
        raise DataContextError('Invalid team or season identity')
    if not isinstance(rows, list) or source.get('rows') != len(rows):
        raise DataContextError('Source row count mismatch')
    if not isinstance(source.get('sha256'), str) or not source['sha256']:
        raise DataContextError('Source hash missing')

    # Explicitly exclude later matches, other leagues, and other seasons. No same-day.
    selected = [r for r in rows if r.get('league') == case['league']
                and r.get('season') in (case['season'], case['previous_season'])
                and isinstance(r.get('match_date'), str) and r['match_date'] < case['target_date']]
    current = [r for r in selected if r['season'] == case['season']]
    previous = [r for r in selected if r['season'] == case['previous_season']]
    home = case['home_id']
    away = case['away_id']
    team_context = {
        'home': {
            'team_id': home,
            'current_home': sum(r['home_id'] == home for r in current),
            'current_all': sum(home in (r['home_id'],r['away_id']) for r in current),
            'previous_home': sum(r['home_id'] == home for r in previous),
        },
        'away': {
            'team_id': away,
            'current_away': sum(r['away_id'] == away for r in current),
            'current_all': sum(away in (r['home_id'],r['away_id']) for r in current),
            'previous_away': sum(r['away_id'] == away for r in previous),
        },
    }

    def last_date(records: list[dict]) -> str | None:
        return max((r['match_date'] for r in records), default=None)

    data_dates = {
        'last_league_result': last_date(current),
        'last_home_team_result': last_date([r for r in current if home in (r['home_id'],r['away_id'])]),
        'last_away_team_result': last_date([r for r in current if away in (r['home_id'],r['away_id'])]),
    }
    observed_lags = {
        key: (target - date.fromisoformat(value)).days if value else None
        for key, value in data_dates.items()
    }

    # A long observed gap is a *check request*, not proof that source is stale:
    # international breaks etc. may explain it. There is no official completed
    # fixtures comparison here, hence no claim all latest matches are captured.
    review = []
    if team_context['home']['current_home'] < 4 or team_context['away']['current_away'] < 4:
        review.append('C2_CURRENT_VENUE_SAMPLE_LT_4')
    if any(n is None or n > 10 for n in observed_lags.values()):
        review.append('RECENT_RESULTS_REQUIRE_OFFICIAL_CROSSCHECK')
    providers = Counter()
    invalid_source_rows = 0
    for r in selected:
        p = _source_provider(str(r.get('source_url','')).strip())
        if p:
            providers[p] += 1
        else:
            invalid_source_rows += 1
    if invalid_source_rows:
        review.append('SOURCE_URL_MISSING_OR_INVALID')
    if not providers:
        review.append('NO_PROVIDER_REFERENCES')
    usage = _fields_status(current)
    if usage['shots']['missing_or_quarantined']:
        review.append('SHOT_DATA_PARTIAL')
    if usage['first_half']['missing_or_quarantined']:
        review.append('FIRST_HALF_DATA_PARTIAL')
    if usage['full_time_corners']['missing_or_quarantined']:
        review.append('CORNERS_DATA_PARTIAL')
    if usage['xg']['missing_or_quarantined']:
        review.append('XG_NOT_IN_CORE_HISTORY')

    return {
        'version': VERSION,
        'scope': 'OFFLINE_HISTORICAL_CONTEXT_NOT_CURRENT_MATCH_VERIFICATION',
        'case': dict((k,case[k]) for k in REQUIRED),
        'cutoff_exclusive': case['target_date'],
        'provenance': {
            'snapshot_sha256': source['sha256'],
            'snapshot_rows': source['rows'],
            'snapshot_downloaded_at_utc': None,
            'historical_source_references': dict(sorted(providers.items())),
            'historical_source_references_verified_online_now': False,
            'official_fixture_crosscheck_performed': False,
            'source_url_missing_or_invalid': invalid_source_rows,
        },
        'eligible_league_games': {'current_season':len(current),'previous_season':len(previous)},
        'team_context': team_context,
        'last_historical_result_dates': data_dates,
        'lag_to_target_date_days_not_proof_of_missing_games': observed_lags,
        'current_season_market_coverage': usage,
        'official_match_fixture': {'status':'NOT_CHECKED','source':None},
        'official_lineups': {'status':'NOT_CHECKED','source':None},
        'injuries_suspensions': {'status':'NOT_CHECKED','source':None},
        'tactical_context': {'status':'NOT_CHECKED','source':None},
        'verified_external_xg_join': {'status':'NOT_CONNECTED'},
        'review_flags': sorted(set(review)),
        'confidence_eligible': False,
        'recommendation_eligible': False,
        'math_parameters_changed': False,
    }
