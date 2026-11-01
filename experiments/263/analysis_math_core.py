"""2.6.3 offline analysis MATH LAYER — experimental, no fixture search or betting.

C2 = canonical 6.2 k=5, w=.5, contextual previous-season priors.
C3 = frozen experimental opponent-adjusted ridge-Poisson (imported unchanged).
1H and FT corners are separately fitted, UNVALIDATED experimental candidates.
No actual upcoming match selection or historical outcome evaluation occurs here.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

from exp_263_batch import fit_c3, predict_c3

VERSION = '263_analysis_math_architecture_v1'
K = 5.0
W = 0.5
MIN_CONTEXT = 4
MIN_LEAGUE_MATCHES = 30
MIN_OTHER_MARKET_MATCHES = 40
MAX_FT_LAMBDA = 5.0
REG = 6.0  # inherited, frozen C3 coefficient; do not modify by outcome
MARKET_LINES = (0.5, 1.5, 2.5, 3.5, 4.5)
CORNER_LINES = (7.5, 8.5, 9.5, 10.5)


class InvalidHistory(ValueError):
    pass


def _parse_count(value: Any) -> int | None:
    if value is None or str(value).strip() == '':
        return None
    if not re.fullmatch(r'\d+', str(value).strip()):
        return None
    return int(value)


def load_history(path: str | Path) -> tuple[list[dict], dict]:
    """Validate FT history; missing/bad 1H/corners quarantined by market.

    Data must contain actual completed results, not future fixture rows.
    All matches on target calendar date are excluded at query time.
    """
    path = Path(path)
    data = path.read_bytes()
    rows: list[dict] = []
    seen: set[str] = set()
    quarantine = Counter()
    with path.open(newline='', encoding='utf-8-sig') as f:
        dr = csv.DictReader(f)
        required = {'fixture_id','league','season','match_date','home_id','away_id','home_goals','away_goals','result'}
        if not dr.fieldnames or not required.issubset(dr.fieldnames):
            raise InvalidHistory('Missing required columns: ' + str(sorted(required - set(dr.fieldnames or []))))
        for line_no, r in enumerate(dr, 2):
            fixture = r.get('fixture_id','').strip()
            if not fixture or fixture in seen:
                raise InvalidHistory(f'duplicate / empty fixture ID at line {line_no}')
            seen.add(fixture)
            if not all(str(r.get(k,'')).strip() for k in ('league','season','match_date','home_id','away_id')):
                raise InvalidHistory(f'incomplete identity line {line_no}')
            if r['home_id']==r['away_id']:
                raise InvalidHistory(f'same home and away team line {line_no}')
            try:
                d=date.fromisoformat(r['match_date'])
            except ValueError as ex:
                raise InvalidHistory(f'invalid date line {line_no}') from ex
            if d.isoformat()!=r['match_date']:
                raise InvalidHistory(f'noncanonical date line {line_no}')
            hg, ag = _parse_count(r.get('home_goals')), _parse_count(r.get('away_goals'))
            if hg is None or ag is None:
                raise InvalidHistory(f'missing/invalid final goals line {line_no}')
            expected = 'H' if hg>ag else 'A' if hg<ag else 'D'
            if r['result'] != expected:
                raise InvalidHistory(f'final result/score conflict line {line_no}')
            # Missing or impossible 1H and corners do not become zero. FT still usable.
            hh,ha = (_parse_count(r.get(k)) for k in ('half_time_home_goals','half_time_away_goals'))
            if hh is None or ha is None or hh>hg or ha>ag:
                r['_ht_usable'] = False
                quarantine['first_half'] += 1
            else:
                r['_ht_usable'] = True
            hc,ac = (_parse_count(r.get(k)) for k in ('home_corners','away_corners'))
            if hc is None or ac is None or hc>100 or ac>100:
                r['_corner_usable'] = False
                quarantine['corners'] += 1
            else:
                r['_corner_usable'] = True
            rows.append(r)
    rows.sort(key=lambda r:(r['match_date'], r['fixture_id']))
    return rows, {'sha256':hashlib.sha256(data).hexdigest(), 'rows':len(rows),
                  'market_quarantine':dict(quarantine), 'source_filename':path.name}


def _mean(rs: list[dict], field: str) -> float:
    return sum(int(r[field]) for r in rs)/len(rs)


def _shrink(current: list[dict], previous: list[dict], team: str, role: str,
            field: str, reference: float, previous_reference: float | None) -> dict:
    context = [r for r in current if r[f'{role}_id']==team]
    old = [r for r in previous if r[f'{role}_id']==team]
    rho = _mean(old,field)/previous_reference if old and previous_reference and previous_reference>0 else 1.0
    prior = reference*(W*rho+(1-W))
    total = sum(int(r[field]) for r in context)
    smoothed = (total+K*prior)/(len(context)+K)
    return {'n':len(context),'total':total,'league_reference':reference,
            'prior_n':len(old),'rho':rho,'prior_mean':prior,'adjusted_mean':smoothed}


def canonical_c2_lambda(current: list[dict], previous: list[dict], home: str, away: str) -> tuple[dict | None, str | None]:
    """Exact canonical 2.6.3 section 6.2, no inferred missing data."""
    hcontext = [r for r in current if r['home_id']==home]
    acontext = [r for r in current if r['away_id']==away]
    if len(hcontext)<MIN_CONTEXT or len(acontext)<MIN_CONTEXT:
        return None, 'CURRENT_SEASON_CONTEXT_LT_4'
    mh,ma = _mean(current,'home_goals'),_mean(current,'away_goals')
    if min(mh,ma)<=0:
        return None, 'NONPOSITIVE_LEAGUE_REFERENCE'
    old_h = _mean(previous,'home_goals') if previous else None
    old_a = _mean(previous,'away_goals') if previous else None
    values = {
        'home_scored':_shrink(current,previous,home,'home','home_goals',mh,old_h),
        'home_conceded':_shrink(current,previous,home,'home','away_goals',ma,old_a),
        'away_scored':_shrink(current,previous,away,'away','away_goals',ma,old_a),
        'away_conceded':_shrink(current,previous,away,'away','home_goals',mh,old_h),
    }
    lh = values['home_scored']['adjusted_mean']*values['away_conceded']['adjusted_mean']/mh
    la = values['away_scored']['adjusted_mean']*values['home_conceded']['adjusted_mean']/ma
    if not all(math.isfinite(x) and 0.05<=x<=MAX_FT_LAMBDA for x in (lh,la)):
        return None, 'UNSAFE_C2_LAMBDA'
    return {'lambda_home':lh,'lambda_away':la,'league_home_goals':mh,'league_away_goals':ma,
            'team_contexts':values,'current_sample':len(current),'previous_sample':len(previous),
            'k':K,'w':W, 'description':'CANONICAL_C2_INDEPENDENT_POISSON'},None


def _poisson_pmf(mu: float, tolerance: float = 1e-12) -> tuple[np.ndarray,float]:
    if not (math.isfinite(mu) and 0.0<=mu<=MAX_FT_LAMBDA):
        raise ValueError('unsafe expected count')
    out=[math.exp(-mu)]
    while 1.0-sum(out)>tolerance and len(out)<100:
        out.append(out[-1]*mu/len(out))
    tail=max(0.,1.-sum(out))
    if tail>1e-9:
        raise ValueError('Poisson tail too large')
    return np.asarray(out),tail


def _negative_binomial_pmf(mu:float,alpha:float,tolerance:float=1e-11) -> tuple[np.ndarray,float]:
    if not math.isfinite(mu) or mu<0 or not math.isfinite(alpha) or alpha<0:
        raise ValueError('invalid corner distribution parameters')
    if alpha==0:
        # A corner lambda can exceed FT goal lambda; separate recurrence.
        out=[math.exp(-mu)]
        while 1-sum(out)>tolerance and len(out)<300:
            out.append(out[-1]*mu/len(out))
    else:
        r=1/alpha;p=r/(r+mu)
        out=[math.exp(r*math.log(p))]
        while 1-sum(out)>tolerance and len(out)<300:
            k=len(out)
            out.append(out[-1]*(k-1+r)/k*(1-p))
    tail=max(0.,1.-sum(out))
    if tail>1e-8:
        raise ValueError('corner distribution tail too large')
    return np.asarray(out),tail


def _matrix(ph:np.ndarray,pa:np.ndarray,tail_h:float,tail_a:float) -> tuple[np.ndarray,float]:
    m=np.outer(ph,pa)
    tail=1-float(m.sum())
    if tail>1e-8 or tail_h>1e-8 or tail_a>1e-8:
        raise ValueError('joint score distribution mass insufficient')
    return m/m.sum(), max(0.,tail)


def score_market(lh:float,la:float,lines=MARKET_LINES,top_n:int=5) -> dict:
    ph,th=_poisson_pmf(lh)
    pa,ta=_poisson_pmf(la)
    m,tail=_matrix(ph,pa,th,ta)
    n=len(ph); k=len(pa)
    h=np.arange(n)[:,None]; a=np.arange(k)[None,:]
    result={'MS1':float(m[h>a].sum()), 'MSX':float(m[h==a].sum()), 'MS2':float(m[h<a].sum())}
    markets={**result,'1X':result['MS1']+result['MSX'],
             'X2':result['MSX']+result['MS2'],'12':result['MS1']+result['MS2'],
             'BTTS_YES':float(m[(h>0)&(a>0)].sum())}
    markets['BTTS_NO']=1-markets['BTTS_YES']
    for line in lines:
        over=float(m[(h+a)>line].sum())
        markets[f'OVER_{line:g}']=over
        markets[f'UNDER_{line:g}']=1-over
    for line in (0.5,1.5,2.5):
        markets[f'HOME_OVER_{line:g}']=float(m[h.repeat(k,axis=1)>line].sum())
        markets[f'AWAY_OVER_{line:g}']=float(m[a.repeat(n,axis=0)>line].sum())
    pairs=sorted(((float(m[i,j]),int(i),int(j)) for i in range(n) for j in range(k)),reverse=True)[:top_n]
    return {'model':'INDEPENDENT_POISSON','lambda_home':lh,'lambda_away':la,
            'markets':markets,'correct_scores':[{'score':f'{i}-{j}','probability':v} for v,i,j in pairs],
            'truncation_tail':tail,'probability_sum':sum(result.values())}


def _count_lambdas(fit:tuple,home:str,away:str,cap:float) -> tuple[float,float] | None:
    # Existing frozen C3 probability model uses a 5-goal limit.
    # Corners need their own wider physical count domain; never clamp them to goals.
    beta,ix,m=fit
    def val(team,pos):return beta[pos+ix[team]] if team in ix else 0.
    h=math.exp(float(beta[0]+val(home,2)+val(away,2+m)))
    a=math.exp(float(beta[1]+val(away,2)+val(home,2+m)))
    return (h,a) if all(math.isfinite(x) and .001<=x<=cap for x in (h,a)) else None

def _corner_dispersion(context: list[dict], fit:tuple, cap=1.0) -> dict:
    """Residual overdispersion method-of-moments, no use of target outcomes."""
    residual=[]; predicted=[]
    for r in context:
        lam=_count_lambdas(fit,r['home_id'],r['away_id'],cap=30.)
        if lam is None:
            continue
        for y,mu in zip((int(r['home_goals']),int(r['away_goals'])),lam):
            residual.append((y-mu)**2-y)
            predicted.append(mu**2)
    if len(residual)<20 or sum(predicted)<=0:
        return {'alpha':0.,'status':'INSUFFICIENT_DISPERSION_EVIDENCE'}
    raw=max(0.,sum(residual)/sum(predicted))
    return {'alpha':min(cap,raw),'status':'EXPERIMENTAL_MOMENTS','raw_alpha':raw}


def _independent_count_model(past: list[dict],home:str,away:str,market:str) -> dict:
    if market=='first_half':
        sub=[r for r in past if r['_ht_usable']]
        hfield,afield='half_time_home_goals','half_time_away_goals'
    elif market=='corners':
        sub=[r for r in past if r['_corner_usable']]
        hfield,afield='home_corners','away_corners'
    else:
        raise ValueError('unknown market')
    hc=sum(r['home_id']==home for r in sub);ac=sum(r['away_id']==away for r in sub)
    if len(sub)<MIN_OTHER_MARKET_MATCHES or hc<MIN_CONTEXT or ac<MIN_CONTEXT:
        return {'status':'INSUFFICIENT_MARKET_DATA','available':len(sub),
                'home_context':hc,'away_context':ac,'required_minimums':{'league':MIN_OTHER_MARKET_MATCHES,'context':MIN_CONTEXT}}
    # Dedicated model fit using only the respective count. Goals are NOT used as
    # features in half-time or corners; fit_c3 is only a generic ridge count fitter.
    adapted=[{**r,'home_goals':r[hfield],'away_goals':r[afield]} for r in sub]
    fit=fit_c3(adapted)
    if fit is None:
        return {'status':'COUNT_MODEL_FIT_FAILED','available':len(sub)}
    lambdas=_count_lambdas(fit,home,away,cap=5. if market=='first_half' else 30.)
    if lambdas is None:
        return {'status':'COUNT_MODEL_LAMBDA_OUT_OF_RANGE','available':len(sub)}
    lh,la=lambdas
    if market=='first_half':
        result=score_market(lh,la,lines=(0.5,1.5,2.5))
        return {'status':'EXPERIMENTAL_NOT_VALIDATED','sample':len(sub),
                'home_context':hc,'away_context':ac, 'source_fields':[hfield,afield],
                'estimate':result,'description':'separate first-half ridge Poisson; not half the FT lambda'}
    dispersion=_corner_dispersion(adapted,fit)
    ph,th=_negative_binomial_pmf(lh,dispersion['alpha'])
    pa,ta=_negative_binomial_pmf(la,dispersion['alpha'])
    m,tail=_matrix(ph,pa,th,ta)
    hi=np.arange(len(ph))[:,None];ai=np.arange(len(pa))[None,:]
    probabilities={f'OVER_{line:g}':float(m[hi+ai>line].sum()) for line in CORNER_LINES}
    probabilities.update({f'UNDER_{line:g}':1-probabilities[f'OVER_{line:g}'] for line in CORNER_LINES})
    probabilities['MORE_CORNERS_HOME']=float(m[hi>ai].sum())
    probabilities['MORE_CORNERS_AWAY']=float(m[hi<ai].sum())
    probabilities['CORNERS_EQUAL']=float(m[hi==ai].sum())
    return {'status':'EXPERIMENTAL_NOT_VALIDATED','sample':len(sub),
            'home_context':hc,'away_context':ac,'source_fields':[hfield,afield],
            'model':'SEPARATE_RIDGE_COUNT_AND_NB','expected_home_corners':lh,
            'expected_away_corners':la,'dispersion':dispersion,'markets':probabilities,
            'truncation_tail':tail,'description':'NB dispersion from historical corner residuals only; not tested for predictive superiority'}


def sensitivity(lh:float,la:float,variation=.10) -> dict:
    cases={}
    for hsc in (1-variation,1,1+variation):
        for asc in (1-variation,1,1+variation):
            if not (.05<=lh*hsc<=5 and .05<=la*asc<=5):
                continue
            p=score_market(lh*hsc,la*asc)['markets']
            cases[f'{hsc:.2f}_{asc:.2f}']={k:p[k] for k in ('MS1','MSX','MS2','OVER_2.5','BTTS_YES')}
    if len(cases)<9:
        return {'status':'NOT_CALCULATED_OUT_OF_RANGE','note':'No clipping or fake probability ranges'}
    ranges={k:[min(c[k] for c in cases.values()),max(c[k] for c in cases.values())] for k in ('MS1','MSX','MS2','OVER_2.5','BTTS_YES')}
    winners={max(('MS1','MSX','MS2'),key=lambda k:c[k]) for c in cases.values()}
    return {'status':'HEURISTIC_NOT_CONFIDENCE_INTERVAL','input_variation':variation,
            'ranges':ranges,'ms_winner_flips':len(winners)>1}


def build_analysis(rows: list[dict], source:dict, league:str, season:str,
                   previous_season:str, target_date:str,home:str,away:str,
                   include_experimental_markets:bool=True) -> dict:
    """Offline math only; target is an abstract hypothetical fixture, NOT verified.

    No current result and no rows on target day can affect any model.
    """
    d=date.fromisoformat(target_date)
    if d.isoformat()!=target_date or not league or not season or not home or not away or home==away:
        raise ValueError('invalid target identity/date')
    if previous_season==season:
        raise ValueError('previous/current seasons must differ')
    past=[r for r in rows if r['league']==league and r['match_date']<target_date]
    current=[r for r in past if r['season']==season]
    previous=[r for r in past if r['season']==previous_season]
    out={'version':VERSION, 'fixture_verified':False,'is_real_match_forecast':False,
         'fixture':{'league':league,'season':season,'previous_season':previous_season,'target_date':target_date,
                    'home_id':home,'away_id':away},
         'provenance':{**source,'cutoff_exclusive_date':target_date,'historical_games':len(past),
                       'current_season_games':len(current),'previous_season_games':len(previous)},
         'model_status':{'C2':'NOT_TESTED','C3':'NOT_TESTED'},
         'model_outputs':{}, 'other_markets':{},'excluded_features':['xG','Elo','lineups','odds','EV','first_half_corners'],
         'note':'Offline architecture only. No real fixture is verified. Do not emit as live prediction or recommendation.'}
    c2,reason=canonical_c2_lambda(current,previous,home,away)
    if c2 is None:
        out['model_status']['C2']='YOK: '+str(reason)
    else:
        out['model_status']['C2']='BASIT_CANONICAL_NOT_VALIDATED'
        out['model_outputs']['C2']={'details':c2,'goals':score_market(c2['lambda_home'],c2['lambda_away']),
                                    'sensitivity':sensitivity(c2['lambda_home'],c2['lambda_away'])}
    hc=sum(r['home_id']==home for r in past);ac=sum(r['away_id']==away for r in past)
    if len(past)<MIN_LEAGUE_MATCHES or min(hc,ac)<MIN_CONTEXT:
        out['model_status']['C3']='NOT_AVAILABLE: history/context too small'
    else:
        fit=fit_c3(past)
        lambdas=predict_c3(fit,home,away) if fit is not None else None
        if lambdas is None:
            out['model_status']['C3']='NOT_AVAILABLE: numerical fit or lambda unsafe'
        else:
            out['model_status']['C3']='EXPERIMENTAL_NOT_PROMOTED'
            out['model_outputs']['C3']={'details':{'lambda_home':lambdas[0],'lambda_away':lambdas[1],
                                                   'sample':len(past),'home_context':hc,'away_context':ac,
                                                   'regularization':REG,'opponent_effect_once':True},
                                        'goals':score_market(*lambdas),'sensitivity':sensitivity(*lambdas)}
    if include_experimental_markets:
        out['other_markets']['first_half']=_independent_count_model(past,home,away,'first_half')
        out['other_markets']['full_time_corners']=_independent_count_model(past,home,away,'corners')
    return out


def write_report(data:dict,path:str|Path) -> None:
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='OFFLINE mathematical audit ONLY, not a live match forecaster')
    parser.add_argument('--history',required=True)
    parser.add_argument('--league',required=True)
    parser.add_argument('--season',required=True)
    parser.add_argument('--previous-season',required=True)
    parser.add_argument('--target-date',required=True)
    parser.add_argument('--home-id',required=True)
    parser.add_argument('--away-id',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    history,source=load_history(args.history)
    result=build_analysis(history,source,args.league,args.season,args.previous_season,args.target_date,args.home_id,args.away_id)
    write_report(result,args.out)
    print(json.dumps({'status':'OFFLINE_ONLY_NO_FIXTURE_VERIFICATION',
                      'model_status':result['model_status'],
                      'first_half':result['other_markets'].get('first_half',{}).get('status'),
                      'corners':result['other_markets'].get('full_time_corners',{}).get('status')},ensure_ascii=False))
