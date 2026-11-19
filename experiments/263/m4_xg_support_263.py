"""Opt-in xG evidence input for M4 (research only; no legacy seal mutation).

The baseline M4 parameters/forecasts are NEVER overwritten. All xG is from
completed matches strictly earlier than the fixture local date; source rows
must match the accepted historical score archive by fixture ID and identities.
This module does not certify first-publication time or provider license.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import date
from pathlib import Path

SCHEMA = '263_m4_xg_sidecar_v1'
ALPHA = 0.438       # value measured in earlier research; formulation is separately auditable
WINDOW = 12
PRIOR = 6
MIN_ROLE = 3
MIN_LEAGUE = 40
BIG_FIVE = frozenset(('ENG1', 'GER1', 'ESP1', 'ITA1', 'FRA1'))
TEN = BIG_FIVE | frozenset(('ENG2','NED1','POR1','BEL1','TUR1'))
BAD_STATUSES = ('KONTROL_BEKL', 'TEYIDI_BEKL', 'ADAY', 'TAMAM_DEGIL', 'UNVERIFIED')


def _valid_number(v):
    try:
        z=float(v)
        return z if math.isfinite(z) and 0.0 <= z <= 9.0 else None
    except (ValueError, TypeError):
        return None


def _expected_source(league):
    return 'Understat' if league in BIG_FIVE else 'xgEdge'


def _status_ok(r):
    s=(r.get('source_status') or '').upper().replace('İ','I').replace('Ş','S').replace('Ğ','G')
    if any(word in s for word in BAD_STATUSES):
        return False
    return True


def _key(r):
    return str(r['fixture_id'])


def _accepted_past(xg_rows, official_rows, league, cutoff):
    """Join by fixture ID, exact dated home/away identity and final scores.

    If accepted scores have duplicate/conflicting identities, fail closed.
    """
    date.fromisoformat(cutoff)
    if league not in TEN: raise ValueError('league_outside_10')
    index={}
    for r in official_rows:
        fid=_key(r)
        if fid in index: raise ValueError('duplicate_accepted_fixture_id')
        index[fid]=r
    seen=set(); usable=[]; rejected={}
    def reject(c): rejected[c]=rejected.get(c,0)+1
    for r in xg_rows:
        if r.get('league')!=league:continue
        fid=_key(r)
        if fid in seen:raise ValueError('duplicate_xg_fixture_id')
        seen.add(fid)
        if r.get('date','')>=cutoff:
            reject('future_or_same_day');continue
        base=index.get(fid)
        if base is None:
            reject('not_in_accepted_score_archive');continue
        if (r.get('date')!=base.get('match_date',base.get('date')) or
            r.get('home_id')!=base.get('home_id') or r.get('away_id')!=base.get('away_id') or
            str(r.get('home_goals'))!=str(base.get('home_goals')) or
            str(r.get('away_goals'))!=str(base.get('away_goals'))):
            reject('identity_date_score_conflict');continue
        if not _status_ok(r):reject('unconfirmed_xg_source');continue
        if _expected_source(league).lower() not in (r.get('xg_source') or '').lower():
            reject('other_xg_provider');continue
        hx,ax=_valid_number(r.get('home_xg')),_valid_number(r.get('away_xg'))
        if hx is None or ax is None:reject('invalid_xg');continue
        usable.append({'date':r['date'],'fixture_id':fid,
                       'home':r['home_id'],'away':r['away_id'],
                       'hx':hx,'ax':ax})
    usable.sort(key=lambda r:(r['date'],r['fixture_id']))
    return usable,rejected


def xg_adjustment(official_rows, xg_rows, league, home, away, cutoff,
                  baseline_home, baseline_away, alpha=ALPHA):
    """Compute optional xG-conditioned lambdas; always preserve M4 baseline.

    Venue-role xG and xGA get PRIOR league-equivalent matches; recent WINDOW
    venue-specific matches for each side. Forecast's own xG is never accessed.
    """
    if (not all(isinstance(v,(int,float)) and math.isfinite(v) and .05<=v<=5
                for v in (baseline_home,baseline_away)) or
        not isinstance(alpha,(int,float)) or not math.isfinite(alpha) or not 0<=alpha<=1):
        raise ValueError('invalid_m4_baseline_or_alpha')
    eligible,rejected=_accepted_past(xg_rows,official_rows,league,cutoff)
    out={'schema':'263_m4_xg_adjustment_v1',
         'baseline_lambdas':[baseline_home,baseline_away],
         'adjusted_lambdas':[baseline_home,baseline_away],
         'alpha':alpha,'status':'BASELINE_M4_FALLBACK',
         'league_eligible_history':len(eligible),'source_rejected':rejected,
         'used_matches':0, 'role_counts':{}, 'asof_provider_vintage_verified':False}
    if len(eligible)<MIN_LEAGUE:
        out['reason']='LESS_THAN_40_ACCEPTED_PRIOR_XG_MATCHES';return out
    league_home=sum(r['hx'] for r in eligible)/len(eligible)
    league_away=sum(r['ax'] for r in eligible)/len(eligible)
    if not all(math.isfinite(x) and x >= .1 for x in (league_home,league_away)):
        out['reason']='INVALID_LEAGUE_XG_PRIOR';return out
    # Four distinct role histories: home at home offense and defence;
    # away away offense and defence. No target match xG enters this set.
    hh=[r for r in eligible if r['home']==home][-WINDOW:]
    aa=[r for r in eligible if r['away']==away][-WINDOW:]
    out['role_counts']={'home_home':len(hh),'away_away':len(aa)}
    if min(len(hh),len(aa))<MIN_ROLE:
        out['reason']='INSUFFICIENT_VENUE_ROLE_HISTORY';return out
    def shrink(samples, key, prior):
        return (sum(r[key] for r in samples)+PRIOR*prior)/(len(samples)+PRIOR)
    home_attack=shrink(hh,'hx',league_home)
    home_defence=shrink(hh,'ax',league_away)
    away_attack=shrink(aa,'ax',league_away)
    away_defence=shrink(aa,'hx',league_home)
    if not all(z>0 for z in (home_attack,home_defence,away_attack,away_defence)):
        out['reason']='ZERO_XG_RATE';return out
    # Multiplicative offence / opposition defence relative to league prior.
    xg_home=home_attack*away_defence/league_home
    xg_away=away_attack*home_defence/league_away
    if not all(math.isfinite(z) and z>0 for z in (xg_home,xg_away)):
        out['reason']='INVALID_XG_PROJECTION';return out
    adjusted=[math.exp((1-alpha)*math.log(b)+alpha*math.log(x))
              for b,x in ((baseline_home,xg_home),(baseline_away,xg_away))]
    if not all(.05<=z<=5 for z in adjusted):
        out['reason']='ADJUSTED_LAMBDA_OUT_OF_RANGE';return out
    out.update({'status':'XG_INCLUDED_IN_M4_RESEARCH_LAMBDA',
                'adjusted_lambdas':adjusted,'xg_independent_lambdas':[xg_home,xg_away],
                'used_matches':len({r['fixture_id'] for r in hh+aa}),
                'last_used_date':max(r['date'] for r in hh+aa),
                'reason':'PREVIOUS_MATCH_XG_CORRECTION_ONLY'})
    return out


def _csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def _sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def sidecar(forecast_file, history_file, xg_file, output_file):
    """Attach xG to an EXISTING signed M4 forecast via a separate sidecar file.

    Neither the forecast nor its 96 cohort ledger is modified. Not a bookmaker
    value or ROI calculation. The existing M4 scoring function is reused.
    """
    forecast=json.loads(Path(forecast_file).read_text(encoding='utf-8'))
    if forecast.get('schema')!='quad_forward_263_v1':
        raise ValueError('not_existing_quad_forecast')
    if forecast.get('data',{}).get('snapshot_sha256')!=_sha(history_file):
        raise ValueError('m4_history_snapshot_sha_mismatch')
    from forward_c3 import canonical_bytes
    payload=dict(forecast);seal=payload.pop('payload_sha256',None)
    if not seal or hashlib.sha256(canonical_bytes(payload)).hexdigest()!=seal:
        raise ValueError('legacy_forecast_seal_invalid')
    fix=forecast['fixture'];m4=forecast['model_predictions']['M4']
    if m4.get('status')!='AVAILABLE':raise ValueError('base_m4_unavailable')
    lambdas=[m4['goals']['lambda_home'],m4['goals']['lambda_away']]
    out=xg_adjustment(_csv(history_file),_csv(xg_file),fix['league'],
                      fix['home_id'],fix['away_id'],fix['match_local_date'],*lambdas)
    if out['status']=='XG_INCLUDED_IN_M4_RESEARCH_LAMBDA':
        # Reuse existing scoring, not a second or inconsistent math core.
        from m4_integrated import score_markets
        adjusted=score_markets(*out['adjusted_lambdas'])['markets']
        baseline=m4['goals']['markets']
        out['markets']={'M4_original':baseline,'M4_with_xg':adjusted}
        out['differences']={'OVER_2.5':adjusted['OVER_2.5']-baseline['OVER_2.5'],
                            'BTTS_YES':adjusted['BTTS_YES']-baseline['BTTS_YES']}
    result={'schema':SCHEMA,'forecast_sha256':seal,'forecast_original_unmodified':True,
            'm4_frozen_unmodified':True,'xg_dataset_sha256':_sha(xg_file),
            'xg_private_values_not_in_output':True,'use':'RESEARCH_SIDECAR_NOT_PRODUCTION',
            'xg':out}
    from m4_xg_market_policy_263 import choose_market_families
    result['marketwise_research_policy']=choose_market_families(result)
    content=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n'
    Path(output_file).parent.mkdir(parents=True,exist_ok=True)
    with open(output_file,'x',encoding='utf-8') as f:f.write(content)
    return result


def main():
    p=argparse.ArgumentParser(description='Optional M4 xG sidecar; no changes to frozen M4')
    for x in ('forecast','history','xg','out'):p.add_argument('--'+x,required=True)
    args=p.parse_args()
    result=sidecar(args.forecast,args.history,args.xg,args.out)
    print(json.dumps({'status':result['xg']['status'],'out':args.out,
                      'forecast_sha256':result['forecast_sha256']},ensure_ascii=False))

if __name__=='__main__':main()
