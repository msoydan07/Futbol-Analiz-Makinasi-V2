"""Identity-first on-demand fixture gateway, offline model stays unchanged.

This module connects the already-reviewed Maçkolik identity cache to the new
source-page parsers. No per-week fixture lists, no Module 0, no live prediction.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from mackolik_identity_gate_263 import (
    _validate_identity_source, _reviewed, _memberships,
    _candidate_id, resolve_requested_match, _check_observation,
)
from official_page_lookup_263 import official_page_lookup,coverage_inventory

DEFAULT_INDEX='experiments/263/evidence/identity_index_263.json'
DEFAULT_ALIASES='data/team_aliases_reviewed.csv'


def prepare_requested_match(home,away,*,league=None,season='2026-2027',
                            identity_index=DEFAULT_INDEX, reviewed_aliases=DEFAULT_ALIASES,
                            now=None, fetcher=None, html=None,source_url=None):
    """One user-named match; one approved official page fetch at most.

    html is exclusively an injectable deterministic test input. In production,
    omit it and the page must be actually fetched. NOT_VERIFIED is not proof that
    no fixture exists: official publishers may omit events or change schemas.
    """
    now=now or datetime.now(timezone.utc)
    if not isinstance(home,str) or not isinstance(away,str) or not home.strip() or not away.strip():
        return {'status':'REJECTED','reason':'user_must_name_both_teams'}
    try:
        registry=json.loads(Path(identity_index).read_text(encoding='utf-8'))
        _validate_identity_source(registry)
        reviewed=_reviewed(Path(reviewed_aliases),registry) if reviewed_aliases else {}
        resolved=resolve_requested_match(registry,home,away,league,season,reviewed)
        if resolved['status']!='RESOLVED_IDENTITY':return resolved
        lg=resolved['league']; members=_memberships(registry,season)
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as ex:
        return {'status':'REVIEW_REQUIRED','reason':'identity_cache_or_alias_problem','detail':str(ex)[:140]}
    def same_team(observed,requested):
        obs=_candidate_id(registry,observed,lg,members,reviewed)
        req=_candidate_id(registry,requested,lg,members,reviewed)
        return obs is not None and obs==req
    observation=official_page_lookup(lg,home,away,now=now,fetcher=fetcher,
                                      source_url=source_url,html=html,same_team=same_team)
    if observation.get('status') not in ('VERIFIED_OFFICIAL_FIXTURE','VERIFIED_OFFICIAL_FIXTURE_DATE_ONLY'):
        return {'status':'NOT_VERIFIED' if observation.get('status') not in ('REVIEW_REQUIRED','REJECTED') else observation['status'],
                'reason':observation.get('reason','official_observation_missing'),
                'official_lookup':observation,
                'model_ran':False,'does_not_prove_no_fixture':True}
    outcome=_check_observation(observation,resolved,registry,members,reviewed,now)
    # An injected page is strictly a software test, never an actual verification.
    if html is not None or fetcher is not None:
        if outcome.get('status')=='VERIFIED':
            outcome['status']='SIMULATED_OFFICIAL_PAGE_ONLY'
            outcome['ready_for_data_audit']=False
            outcome['official_source_parser_attested']=False
        outcome['test_injection']=True
    outcome['adapter']='263_official_page_parser'
    outcome['model_ran']=False
    outcome['lineups_status']='NOT_CHECKED'
    return outcome


def report_coverage():
    return {'league_count':10,'operational_coverage_10_of_10_proven':False,
            'reason':'Providers differ; standard parsers require live per-league acceptance, no blanket success',
            'leagues':coverage_inventory()}
