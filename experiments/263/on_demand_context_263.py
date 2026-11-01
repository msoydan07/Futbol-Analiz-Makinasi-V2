"""2.6.3 named-match context gate, isolated experiment; NEVER selects fixtures.

Only the existing trusted on-demand official lookup may accept a fixture. This
module does not fetch a fixture list, infer a match from historical data, or
modify C2/C3 expected goals. Absent or unpublished lineups never block math.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from typing import Callable, Any

VERSION = '263_named_match_evidence_gate_v1'
LEAGUE_DOMAINS = {
    'ENG1': 'premierleague.com', 'ENG2': 'efl.com',
    'GER1': 'bundesliga.com', 'ESP1': 'laliga.com',
    'ITA1': 'legaseriea.it', 'FRA1': 'ligue1.com',
    'NED1': 'eredivisie.nl', 'TUR1': 'tff.org',
    'POR1': 'ligaportugal.pt', 'BEL1': 'proleague.be',
}
EVIDENCE_FIELDS = ('lineups', 'injuries_suspensions', 'tactics')
LEAGUE_TIMEZONES = {
    'ENG1': 'Europe/London', 'ENG2': 'Europe/London',
    'GER1': 'Europe/Berlin', 'ESP1': 'Europe/Madrid',
    'ITA1': 'Europe/Rome', 'FRA1': 'Europe/Paris',
    'NED1': 'Europe/Amsterdam', 'TUR1': 'Europe/Istanbul',
    'POR1': 'Europe/Lisbon', 'BEL1': 'Europe/Brussels',
}


def _utc(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError('Missing timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timezone required')
    return parsed.astimezone(timezone.utc)


def _official_url(url: Any, domains: set[str]) -> bool:
    if not isinstance(url, str):
        return False
    p = urlparse(url)
    host = (p.hostname or '').lower()
    return (p.scheme == 'https' and not p.username and not p.password
            and any(host == domain or host.endswith('.' + domain) for domain in domains))


def _observed_context(value: Any, kind: str, fixture: dict,
                      now: datetime, approved_domains: set[str]) -> dict:
    """Whitelist official-source evidence; a news report cannot edit goal lambdas.

    The calling integration MUST obtain observation via its trusted source adapter,
    never from a user-supplied JSON flag. No observation means NOT_CHECKED.
    """
    if value is None:
        return {'status': 'NOT_CHECKED', 'source': None, 'math_effect': False}
    if not isinstance(value, dict) or value.get('field') != kind:
        return {'status': 'UNVERIFIED', 'reason': 'invalid_evidence_shape', 'math_effect': False}
    claimed = value.get('status')
    if claimed not in ('VERIFIED', 'NOT_PUBLISHED', 'UNVERIFIED'):
        return {'status': 'UNVERIFIED', 'reason': 'unknown_evidence_status', 'math_effect': False}
    if claimed == 'UNVERIFIED':
        return {'status': 'UNVERIFIED', 'reason': 'source_not_verified', 'math_effect': False}
    if not _official_url(value.get('source_url'), approved_domains):
        return {'status': 'UNVERIFIED', 'reason': 'non_official_source', 'math_effect': False}
    try:
        at = _utc(value.get('retrieved_at_utc'))
        if at > now + timedelta(minutes=5) or now - at > timedelta(hours=24):
            raise ValueError('stale_or_future_evidence')
    except (ValueError, TypeError, OverflowError):
        return {'status': 'UNVERIFIED', 'reason': 'invalid_or_stale_evidence_time', 'math_effect': False}
    if value.get('home_id') != fixture['home_id'] or value.get('away_id') != fixture['away_id']:
        return {'status': 'UNVERIFIED', 'reason': 'different_match_identity', 'math_effect': False}
    if claimed == 'VERIFIED':
        details = value.get('details')
        if not isinstance(details, dict) or not details:
            return {'status': 'UNVERIFIED', 'reason': 'missing_qualified_details', 'math_effect': False}
        if kind == 'lineups':
            home_xi, away_xi = details.get('home_starting_xi'), details.get('away_starting_xi')
            def valid_xi(xi):
                return (isinstance(xi, list) and len(xi) == 11 and
                        all(isinstance(x, str) and x.strip() for x in xi) and
                        len({x.strip().casefold() for x in xi}) == 11)
            if not valid_xi(home_xi) or not valid_xi(away_xi):
                return {'status': 'UNVERIFIED', 'reason': 'incomplete_or_repeated_starting_xi', 'math_effect': False}
    return {'status': 'VERIFIED_SOURCE_RECORD' if claimed == 'VERIFIED' else 'NOT_PUBLISHED_OFFICIAL_CHECK',
            'source': value['source_url'], 'retrieved_at_utc': at.isoformat(),
            'source_data': value.get('details', {}) if claimed == 'VERIFIED' else None,
            'math_effect': False,
            'note': 'Evidence-only until independent model effect is tested.'}


def prepare_named_match(league: str, home: str, away: str, *, now: datetime | None = None,
                        fixture_gate: Callable | None = None,
                        observation_provider: Callable | None = None,
                        extra_official_domains: tuple[str, ...] = (),
                        registry_path: str = 'data/match_registry.json') -> dict:
    """Check user-selected match, then prepare 2.6.3 context; no forecast yet.

    fixture_gate injection exists for deterministic unit tests; in production the
    callable is the existing analyze_named_match_gate.run official live parser.
    Only a trusted callable may obtain current lineup/absence observations.
    Direct user-provided evidence dictionaries are NEVER accepted as input.
    """
    if not all(isinstance(s, str) and s.strip() for s in (league, home, away)):
        return {'status': 'REJECTED', 'reason': 'named_match_required'}
    if league not in LEAGUE_DOMAINS:
        return {'status': 'REJECTED', 'reason': 'unsupported_league'}
    now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None:
        return {'status': 'REJECTED', 'reason': 'timezone_required'}
    now = now.astimezone(timezone.utc)
    if fixture_gate is None:
        from analyze_named_match_gate import run as fixture_gate
    try:
        # No fixture CSV, match search, prebuilt schedule or Module 0 call.
        fixture = fixture_gate(league, home, away, registry_path=registry_path)
    except Exception as e:
        return {'status': 'NOT_VERIFIED', 'reason': 'official_lookup_failed', 'detail':str(e)[:160]}
    if not isinstance(fixture, dict) or fixture.get('status') != 'VERIFIED':
        return {'status': 'NOT_VERIFIED', 'verification': fixture,
                'next_step': 'CHECK_OFFICIAL_FIXTURE_ON_DEMAND'}
    try:
        if fixture.get('league') != league or not isinstance(fixture.get('home_id'), str) or not isinstance(fixture.get('away_id'), str):
            raise ValueError('invalid_fixture_identity')
        if not fixture['home_id'] or not fixture['away_id'] or fixture['home_id'] == fixture['away_id']:
            raise ValueError('invalid_participants')
        kickoff, retrieved = _utc(fixture.get('kickoff_utc')), _utc(fixture.get('retrieved_at_utc'))
        if not now <= kickoff <= now + timedelta(days=7):
            raise ValueError('kickoff_outside_request_window')
        if retrieved > now + timedelta(minutes=5) or now - retrieved > timedelta(hours=24):
            raise ValueError('stale_fixture_observation')
        approved = {LEAGUE_DOMAINS[league]}
        if league == 'TUR1':
            approved.add('bjk.com.tr')  # Legacy first-party club exception in existing fixture gate.
        if not _official_url(fixture.get('source_url'), approved):
            raise ValueError('source_domain_mismatch')
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        return {'status': 'NOT_VERIFIED', 'reason': 'invalid_official_verification',
                'detail':str(exc)[:140]}
    domains = approved | {d.lower() for d in extra_official_domains if isinstance(d, str) and d}
    # No caller-supplied evidence dictionary: observation provider must FETCH and PARSE
    # an official source, and is trusted code, never derived from a chat/user flag.
    context_collection_error = None
    if observation_provider is None:
        obs = {}
    elif not callable(observation_provider):
        return {'status': 'REJECTED', 'reason': 'trusted_observation_provider_required'}
    else:
        try:
            obs = observation_provider(fixture)
            if not isinstance(obs, dict):
                raise ValueError('observation_adapter_must_return_dict')
        except Exception as exc:
            obs = {}
            context_collection_error = 'official_context_adapter_failed: ' + type(exc).__name__
    facts = {kind: _observed_context(obs.get(kind), kind, fixture, now, domains)
             for kind in EVIDENCE_FIELDS}
    # Date must be interpreted in the match location, not blindly in UTC.
    local_date = kickoff.astimezone(ZoneInfo(LEAGUE_TIMEZONES[league])).date().isoformat()
    return {
        'version': VERSION,
        'status': 'READY_FOR_DATA_AUDIT',
        'request': {'league': league, 'home': home, 'away': away},
        'fixture': {'verification': 'OFFICIAL_CHECKED_ON_DEMAND',
                    'home_id': fixture['home_id'], 'away_id': fixture['away_id'],
                    'league': league, 'kickoff_utc': kickoff.isoformat(),
                    'source_url': fixture['source_url'], 'retrieved_at_utc': retrieved.isoformat(),
                    'local_date': local_date,
                    'local_timezone': LEAGUE_TIMEZONES[league],
                    'timezone_note': 'Match date interpreted in league timezone, not UTC calendar date.'},
        'facts': facts,
        'context_collection_error': context_collection_error,
        'lineups_missing_blocks_analysis': False,
        'external_context_modified_lambdas': False,
        'c2_c3_must_pass_separate_historical_data_audit': True,
        'analysis_completed': False,
        'prediction_recorded': False,
        'fixture_list_required': False,
        'module_0_used': False,
        'next_step': 'VALIDATE_HISTORY_AND_RUN_2_6_3_ANALYSIS',
    }