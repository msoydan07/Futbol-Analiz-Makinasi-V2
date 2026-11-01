"""Read-only 2.6.3 link between frozen historical rows and original team registry.

Verifies referential integrity and *claimed* official-name metadata only. Never
fetches official sites or upgrades a match, lineup or model reliability status.
This is not a second independent source of match results.
"""
from __future__ import annotations
import hashlib
import json
import re
import uuid
from collections import Counter
from pathlib import Path

VERSION = '263_identity_provenance_v1_offline'
# Same namespace used by existing identity.Registry; DO NOT issue new team IDs.
ID_NAMESPACE = uuid.UUID('0c312c79-42d1-4ca9-8b1c-4c65b96ef6b2')
LEAGUES = {'ENG1','ENG2','GER1','ESP1','ITA1','FRA1','NED1','TUR1','POR1','BEL1'}
SEASONS = {'2025-2026','2026-2027'}
JOIN_FIELDS = ('league', 'season', 'match_date', 'home_id', 'away_id')

class IdentityProvenanceError(ValueError):
    pass


def load_registry(path: str | Path, expected_sha256: str | None = None) -> tuple[dict, str]:
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise IdentityProvenanceError('Registry bytes SHA-256 mismatch')
    try:
        registry = json.loads(data)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise IdentityProvenanceError('Invalid registry JSON') from exc
    if not isinstance(registry, dict):
        raise IdentityProvenanceError('Registry must be object')
    return registry, digest


def audit_registry_linkage(rows: list[dict], source: dict, registry: dict, registry_sha256: str) -> dict:
    """Cross-check ALL historical rows and canonical registry, no mutable side effects.

    The source sha/count are asserted by upstream load_history; source_audit docs,
    federation URLs and raw CSV source URLs are not independently re-fetched here.
    """
    if not isinstance(rows, list) or len(rows) == 0 or source.get('rows') != len(rows):
        raise IdentityProvenanceError('Source row count mismatch')
    if not isinstance(source.get('sha256'), str) or not re.fullmatch(r'[a-f0-9]{64}', source['sha256']):
        raise IdentityProvenanceError('Missing canonical historical snapshot digest')
    if not isinstance(registry_sha256, str) or not re.fullmatch(r'[a-f0-9]{64}', registry_sha256):
        raise IdentityProvenanceError('Invalid registry digest')
    if not isinstance(registry, dict):
        raise IdentityProvenanceError('Malformed registry')
    teams, fixtures, aliases = (registry.get(k) for k in ('teams','fixtures','aliases'))
    if not all(isinstance(v, dict) for v in (teams, fixtures, aliases)):
        raise IdentityProvenanceError('Missing canonical registry collections')
    if not teams or not fixtures:
        raise IdentityProvenanceError('Empty team or fixture registry')

    # Existing canonical IDs must map to their immutable registry keys; neither
    # fixture date nor display name is used to infer a new team identity.
    canonical_keys = set()
    for team_id, team in teams.items():
        if not isinstance(team, dict) or not isinstance(team.get('key'), str):
            raise IdentityProvenanceError('Malformed canonical team')
        key = team['key']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', key) or key in canonical_keys:
            raise IdentityProvenanceError('Repeated/invalid canonical team key')
        canonical_keys.add(key)
        if str(uuid.uuid5(ID_NAMESPACE, f'team:{key}')) != team_id:
            raise IdentityProvenanceError('Team UUID does not match immutable canonical key')
        if not isinstance(team.get('name'), str) or not team['name'].strip():
            raise IdentityProvenanceError('Missing display name')
    if any(team_id not in teams for team_id in aliases.values()):
        raise IdentityProvenanceError('Alias points outside registry')

    league_season = Counter()
    linked_fixture_ids = set()
    for row in rows:
        if not isinstance(row, dict):
            raise IdentityProvenanceError('Historical row malformed')
        fixture_id = row.get('fixture_id')
        if not isinstance(fixture_id, str) or fixture_id in linked_fixture_ids:
            raise IdentityProvenanceError('Repeated/missing historical fixture id')
        linked_fixture_ids.add(fixture_id)
        fixture = fixtures.get(fixture_id)
        if not isinstance(fixture, dict):
            raise IdentityProvenanceError('Historical match absent from canonical fixture registry')
        if any(row.get(k) != fixture.get(k) for k in JOIN_FIELDS):
            raise IdentityProvenanceError('Historical fixture identity differs from registry')
        if row['league'] not in LEAGUES or row['season'] not in SEASONS:
            raise IdentityProvenanceError('Unsupported league/season')
        if row['home_id'] == row['away_id'] or row['home_id'] not in teams or row['away_id'] not in teams:
            raise IdentityProvenanceError('Unknown or identical match participants')
        league_season[f"{row['league']}/{row['season']}"] += 1

    # Do not consider a stored 'FEDERATION_VERIFIED' flag live verification.
    claimed_official_names = sum(t.get('verification') == 'FEDERATION_VERIFIED' for t in teams.values())
    return {
        'version': VERSION,
        'status': 'OFFLINE_REGISTRY_LINKAGE_VALIDATED',
        'scope': 'HISTORICAL_IDS_ONLY_NO_LIVE_VERIFICATION',
        'history_sha256': source['sha256'],
        'registry_sha256': registry_sha256,
        'historical_rows_linked': len(rows),
        'canonical_team_count': len(teams),
        'canonical_fixture_count': len(fixtures),
        'alias_count': len(aliases),
        'league_season_counts': dict(sorted(league_season.items())),
        'claimed_official_name_flags_not_rechecked': claimed_official_names,
        'independently_verified_official_fixture': False,
        'independently_verified_squad_or_lineups': False,
        'source_is_original_github_actions_artifact_not_live': True,
        'mathematical_parameters_changed': False,
    }
