#!/usr/bin/env python3
"""Read-only research preflight: pinned 4,618 scores + calendar-aware freshness.

Does NOT grant production admission, patch forward_quad/M4, change forecasts,
update source data, or fetch/attest official fixtures itself.  A supplied
live adapter must provide a complete interval; a claimed URL alone isn't proof.
"""
from __future__ import annotations
import csv
import hashlib
import json
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

BASE_SHA = '35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1'
SCORES_SHA = '54250bb6107250d0623b74ad9c56f90731f02d10dab3bf386deefb27aae487ea'
BASE_COUNT, TOTAL, EXTRA = 4413, 4618, 205
LEAGUES = frozenset(('ENG1','ENG2','GER1','ESP1','ITA1','FRA1','NED1','TUR1','POR1','BEL1'))
OFFICIAL_HOSTS = {
    'ENG1': frozenset(('premierleague.com',)),
    'ENG2': frozenset(('efl.com',)),
    'GER1': frozenset(('bundesliga.com',)),
    'ESP1': frozenset(('laliga.com',)),
    'ITA1': frozenset(('legaseriea.it',)),
    'FRA1': frozenset(('ligue1.com','lfp.fr')),
    'NED1': frozenset(('eredivisie.nl',)),
    'POR1': frozenset(('ligaportugal.pt',)),
    'BEL1': frozenset(('proleague.be',)),
    'TUR1': frozenset(('tff.org',)),
}
IDENTITY = ('fixture_id','league','season','match_date','home_id','away_id','home_goals','away_goals','result')
SCORE_FIELDS = ('home_goals','away_goals')
PRIVATE_DATA_FIELDS = ('home_xg','away_xg','home_xga','away_xga')

class GateBlocked(ValueError):
    pass

def _hash(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(128*1024), b''):
            h.update(block)
    return h.hexdigest()

def _csv(p):
    with Path(p).open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        return tuple(reader.fieldnames or ()), list(reader)

def validate_rows(fields, old, projected):
    """Pure data contract; pin hashes separately before using this result."""
    if not set(IDENTITY).issubset(fields) or set(fields) & set(PRIVATE_DATA_FIELDS):
        raise GateBlocked('SCORE_SCHEMA_INVALID_OR_PRIVATE_XG_EXPOSED')
    if len(old)!=BASE_COUNT or len(projected)!=TOTAL:
        raise GateBlocked('ROW_COUNT_MISMATCH')
    if len({r['fixture_id'] for r in old})!=BASE_COUNT or len({r['fixture_id'] for r in projected})!=TOTAL:
        raise GateBlocked('DUPLICATE_FIXTURE_ID')
    if old != projected[:BASE_COUNT]:
        raise GateBlocked('BASE_4413_WAS_MODIFIED_OR_REORDERED')
    for row in projected:
        if row['league'] not in LEAGUES or row['season'] not in ('2025-2026','2026-2027'):
            raise GateBlocked('UNSUPPORTED_LEAGUE_OR_SEASON')
        if date.fromisoformat(row['match_date']) > date(2026,11,8):
            raise GateBlocked('FROZEN_CUTOFF_VIOLATED')
        try:
            hg, ag = (int(row[f]) for f in SCORE_FIELDS)
        except (ValueError, KeyError, TypeError) as exc:
            raise GateBlocked('NON_NUMERIC_GOALS') from exc
        if min(hg,ag)<0 or row['result']!=('H' if hg>ag else 'D' if hg==ag else 'A'):
            raise GateBlocked('RESULT_SCORE_INCONSISTENT')
    for row in projected[BASE_COUNT:]:
        if row.get('source_row')!='PRIVATE_FROZEN_4618_SCORE_ONLY_RESEARCH_NOT_OFFICIAL_ACCEPTANCE':
            raise GateBlocked('NEW_SOURCE_LABEL_WRONG')
        if not row.get('source_url'):
            raise GateBlocked('NEW_SCORE_SOURCE_URL_MISSING')
    latest = {league: max(date.fromisoformat(r['match_date']) for r in projected if r['league']==league)
              for league in sorted(LEAGUES)}
    return latest

def verify_private_projection(legacy, projected):
    """Hard pinned hash, not source/provider acceptance. Never upload CSV to GitHub."""
    if _hash(legacy)!=BASE_SHA or _hash(projected)!=SCORES_SHA:
        raise GateBlocked('PINNED_PRIVATE_OR_LEGACY_SHA_MISMATCH')
    old_fields,old=_csv(legacy)
    fields,new=_csv(projected)
    if old_fields!=fields:
        raise GateBlocked('FIELD_LAYOUT_DIFFERS_FROM_LEGACY')
    latest=validate_rows(fields,old,new)
    return {'status':'PRIVATE_4618_RESEARCH_INTEGRITY_ONLY_NOT_OFFICIAL_ACCEPTANCE',
            'old_rows':BASE_COUNT,'new_rows':EXTRA,'all_rows':TOTAL,
            'legacy_sha256':BASE_SHA,'private_score_projection_sha256':SCORES_SHA,
            'latest_by_league':{k:v.isoformat() for k,v in latest.items()},
            'data_accepted_for_production':False}

def _aware(x):
    try:
        parsed=datetime.fromisoformat(str(x).replace('Z','+00:00'))
    except (ValueError,TypeError) as exc:
        raise GateBlocked('OFFICIAL_ADAPTER_TIME_INVALID') from exc
    if parsed.tzinfo is None:
        raise GateBlocked('OFFICIAL_ADAPTER_TIME_NAIVE')
    return parsed.astimezone(timezone.utc)

def _host_valid(url, league):
    if not isinstance(url,str): return False
    parsed=urlsplit(url)
    host=(parsed.hostname or '').casefold().removeprefix('www.')
    return (parsed.scheme=='https' and host in OFFICIAL_HOSTS[league] and
            not parsed.username and not parsed.password and parsed.port is None)

def inspect_official_interval(*,league,last_result_day,target_day,now_utc,fetch_official_window):
    """Verify claimed official-adapter result coverage, no artificial 10-day limit.

    The callback must query current official complete fixture/result schedule
    when executed. This layer cannot independently attest what callback saw.
    """
    if league not in LEAGUES:
        raise GateBlocked('LEAGUE_NOT_ACCEPTED')
    previous=date.fromisoformat(str(last_result_day))
    target=date.fromisoformat(str(target_day))
    now=_aware(now_utc)
    if target>now.astimezone(ZoneInfo("Europe/Istanbul")).date():
        # The fixture date is Turkey-local, not the UTC calendar day.
        raise GateBlocked('FUTURE_DAY_OFFICIAL_COVERAGE_NOT_YET_PROVABLE')
    if previous>=target:
        raise GateBlocked('SAME_OR_FUTURE_MATCH_RESULTS_IN_SOURCE')
    if fetch_official_window is None:
        raise GateBlocked('OFFICIAL_RESULTS_ADAPTER_NOT_PROVIDED')
    start=previous+timedelta(days=1)
    end=target-timedelta(days=1)
    if start>end:
        return {'status':'NO_FULL_DAYS_TO_RECONCILE','calendar_verified_by_code':False,
                'age_days':(target-previous).days,'missing_results':[]}
    proof=fetch_official_window(league,start.isoformat(),end.isoformat())
    if not isinstance(proof,dict) or proof.get('schema')!='263_official_result_window_v1':
        raise GateBlocked('OFFICIAL_WINDOW_PROOF_SCHEMA_INVALID')
    if (proof.get('league'),proof.get('coverage_start'),proof.get('coverage_end')) != (
        league,start.isoformat(),end.isoformat()):
        raise GateBlocked('OFFICIAL_WINDOW_COVERAGE_INCOMPLETE')
    if not _host_valid(proof.get('source_url'),league):
        raise GateBlocked('OFFICIAL_WINDOW_SOURCE_UNRECOGNIZED')
    fetched=_aware(proof.get('observed_at_utc'))
    if fetched>now or (now-fetched)>timedelta(hours=24):
        raise GateBlocked('OFFICIAL_WINDOW_OBSERVATION_STALE_OR_FUTURE')
    if proof.get('coverage_claim')!='COMPLETE_RESULTS_AND_RESCHEDULED_FIXTURES':
        raise GateBlocked('OFFICIAL_ADAPTER_CANNOT_PROVE_COVERAGE')
    fixtures=proof.get('matches')
    if not isinstance(fixtures,list):
        raise GateBlocked('OFFICIAL_WINDOW_MATCH_LIST_MISSING')
    seen=set(); missing=[]
    for fixture in fixtures:
        if not isinstance(fixture,dict) or set(fixture)!={'match_date','home_id','away_id','status'}:
            raise GateBlocked('OFFICIAL_WINDOW_FIXTURE_FIELDS_INVALID')
        d=date.fromisoformat(fixture['match_date'])
        if not start<=d<=end:raise GateBlocked('OFFICIAL_WINDOW_MATCH_OUTSIDE_RANGE')
        h,a=fixture['home_id'],fixture['away_id']
        if not isinstance(h,str) or not isinstance(a,str) or not h or not a or h==a:
            raise GateBlocked('OFFICIAL_WINDOW_TEAM_IDENTITY_INVALID')
        key=(d.isoformat(),h,a)
        if key in seen:raise GateBlocked('OFFICIAL_WINDOW_DUPLICATE_FIXTURE')
        seen.add(key)
        if fixture['status'] not in ('FULL_TIME','POSTPONED','CANCELLED'):
            raise GateBlocked('OFFICIAL_WINDOW_UNKNOWN_FIXTURE_STATUS')
        if fixture['status']=='FULL_TIME': missing.append(key)
    return {'status':('BLOCKED_NEW_COMPLETED_MATCH_MISSING' if missing
                      else 'RESEARCH_GAP_CANDIDATE_OFFICIAL_ADAPTER_REPORTED_NO_NEW_FULL_TIME'),
            'age_days':(target-previous).days,
            'source_url':proof['source_url'],'observed_at_utc':fetched.isoformat(),
            'calendar_verified_by_code':False,
            'source_admission':'UPSTREAM_OFFICIAL_ADAPTER_CLAIM_NOT_INDEPENDENTLY_RECHECKED',
            'missing_results':[list(x) for x in missing],
            'can_study_frozen_snapshot':not missing,
            'production_forecast_allowed':False}

def preflight(legacy,score_projection,league,target_day,now_utc,fetch_official_window):
    data=verify_private_projection(legacy,score_projection)
    day=data['latest_by_league'][league]
    calendar=inspect_official_interval(league=league,last_result_day=day,
        target_day=target_day,now_utc=now_utc,fetch_official_window=fetch_official_window)
    return {'schema':'263_4618_PRIVATE_MATCHDAY_PREFLIGHT_V1',
            'league':league,'target_day':target_day,'data':data,'calendar':calendar,
            'live_model_pipeline_updated':False,'model_forecast_generated':False,
            'status':('BLOCKED_COMPLETED_RESULTS_NEED_APPEND'
                      if calendar.get('missing_results') else
                      'RESEARCH_DATA_AND_CALENDAR_PREFLIGHT_ONLY_NO_LIVE_ADMISSION')}
