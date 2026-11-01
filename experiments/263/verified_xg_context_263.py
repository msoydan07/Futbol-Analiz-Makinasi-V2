"""Immutable historical xG evidence bridge for 2.6.3 offline report.

Only accepts the output of audited fixture-ID joins with an accompanying audit report.
The join proves identity consistency inside supplied files, NOT independent online
source re-verification. Strict as-of cutoff; never modifies model input or lambdas.
"""
from __future__ import annotations

import csv
import hashlib
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

EXPECTED_FIELDS = ('fixture_id','league','season','match_date','home_id','away_id',
                   'home_goals','away_goals','home_xg','away_xg','understat_source_url')
ALLOWED_XG_LEAGUES = frozenset({'ENG1','GER1','ESP1','ITA1','FRA1'})
VERSION = '263_verified_xg_context_readonly_v1'

class XGContextError(ValueError):
    pass


def _parse_xg(v: object) -> float:
    try:
        if isinstance(v,bool): raise ValueError
        n=float(v)
    except (ValueError, TypeError):
        raise XGContextError('invalid_xg_value') from None
    if not math.isfinite(n) or not 0<=n<=15:
        raise XGContextError('invalid_xg_value')
    return n


def _understat_url(url: str) -> bool:
    if not isinstance(url,str): return False
    try:
        p=urlparse(url)
        return (p.scheme=='https' and p.hostname in ('understat.com','www.understat.com')
                and not p.username and not p.password and p.port in (None,443))
    except ValueError:
        return False


def load_audited_xg(path: str | Path, audit: dict, historical: list[dict]) -> tuple[list[dict], dict]:
    """Validate supplied audit+file consistency against untouched historical fixture IDs.

    Caller must supply a file generated under the existing audited Understat join.
    This does not independently fetch Understat and cannot prove reported provenance.
    """
    data=Path(path).read_bytes()
    digest=hashlib.sha256(data).hexdigest()
    with Path(path).open(encoding='utf-8-sig',newline='') as handle:
        rdr=csv.DictReader(handle)
        if not set(EXPECTED_FIELDS).issubset(rdr.fieldnames or ()):
            raise XGContextError('missing_audited_xg_columns')
        rows=list(rdr)
    if not isinstance(audit,dict) or audit.get('verified_xg_rows')!=len(rows) or audit.get('historical_rows')!=len(historical):
        raise XGContextError('xg_audit_count_mismatch')
    if audit.get('prediction_engine_modified') is not False:
        raise XGContextError('not_a_readonly_audit')
    if audit.get('prediction_asof_rule')!='match_date strictly earlier than target match_date':
        raise XGContextError('xg_asof_rule_unacceptable')
    history_by_id={r['fixture_id']:r for r in historical}
    if len(history_by_id)!=len(historical):raise XGContextError('duplicate_historical_fixture_id')
    seen=set()
    sanitized=[]
    for r in rows:
        fid=r['fixture_id']
        if fid in seen:raise XGContextError('duplicate_xg_fixture_id')
        seen.add(fid)
        hist=history_by_id.get(fid)
        if hist is None:raise XGContextError('xg_fixture_not_in_history')
        if r['league'] not in ALLOWED_XG_LEAGUES:raise XGContextError('unverified_xg_league')
        if any(str(r[k])!=str(hist[k]) for k in ('league','season','match_date','home_id','away_id','home_goals','away_goals')):
            raise XGContextError('xg_match_identity_mismatch')
        try:
            if date.fromisoformat(r['match_date']).isoformat()!=r['match_date']:
                raise ValueError
        except ValueError: raise XGContextError('invalid_xg_match_date') from None
        if not _understat_url(r['understat_source_url']):raise XGContextError('xg_source_not_understat_https')
        sanitized.append({'fixture_id':fid,'league':r['league'],'season':r['season'],
                          'match_date':r['match_date'],'home_id':r['home_id'],'away_id':r['away_id'],
                          'home_xg':_parse_xg(r['home_xg']),'away_xg':_parse_xg(r['away_xg'])})
    info={'status':'AUDIT_FILE_AND_HISTORY_IDENTITY_MATCHED_NOT_LIVE_REVERIFIED',
          'provider':'UNDERSTAT','rows':len(rows),'sha256':digest,
          'source_record_claim':'EXISTING_AUDIT_OUTPUT_NOT_INDEPENDENTLY_FETCHED',
          'model_performance_reused_without_retest':True,'model_xg_promoted':False,
          'math_parameters_changed':False}
    return sanitized,info


def descriptive_xg_asof(rows: list[dict], case: dict, info: dict) -> dict:
    """Current/previous season observations before target day, venue-specific last five.

    Never infer unavailable xG or use observations from target date or later.
    """
    target=case['target_date']
    league=case['league'];seasons={case['season'],case['previous_season']}
    matches=sorted((r for r in rows if r['league']==league and r['season'] in seasons
                    and r['match_date']<target),key=lambda r:(r['match_date'],r['fixture_id']))
    answer={'status':'DESCRIPTIVE_AUDITED_HISTORICAL_XG' if matches else 'NO_PRIOR_AUDITED_XG_FOR_LEAGUE',
            'source':'AUDITED_UNDERSTAT_MATCHED_CSV', 'audit_status':info['status'],
            'league':league,'asof_exclusive':target,
            'prior_league_matches_with_xg':len(matches),
            'latest_prior_observation_date':matches[-1]['match_date'] if matches else None,
            'used_as_lambda_multiplier':False,'used_to_select_primary_model':False,
            'independent_live_source_recheck':False,'model_xg_promoted':False}
    for role,team_key,goal_key,allowed in (
        ('home','home_id','home_xg','home_id'), ('away','away_id','away_xg','away_id')):
        selected=[r for r in matches if r[allowed]==case[team_key]][-5:]
        if selected:
            answer[role]={'venue_matches_with_xg':len(selected),'last_date':selected[-1]['match_date'],
                          'mean_xg_for':round(sum(r[goal_key] for r in selected)/len(selected),4),
                          'mean_xg_against':round(sum(r['away_xg' if role=='home' else 'home_xg'] for r in selected)/len(selected),4)}
        else:
            answer[role]={'venue_matches_with_xg':0,'last_date':None,'mean_xg_for':None,'mean_xg_against':None}
    return answer
