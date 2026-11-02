"""M4 experimental unified Poisson: learnt attack/defence, opponent and venue effects.

No percentages are averaged from B/C2/C3. Only pre-date finished matches are
accepted for each fit. A development-only chronological search locks the model
settings; 2026/27 outcomes must not be used for hyperparameter selection.
"""
from __future__ import annotations
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.sparse import csr_matrix

FEATURE_VERSION = 'm4_venue_opponent_time_poisson_v1'
MIN_TRAIN = 60

@dataclass(frozen=True)
class Settings:
    half_life_days: int
    ridge_shared: int
    ridge_venue: int

# Search choices are predeclared, not results-fitted by hand.
CANDIDATES = tuple(Settings(h,s,v) for h in (90,180,360) for s in (4,12) for v in (12,48))


def validate_history(rows,cutoff,league):
    date.fromisoformat(cutoff)
    past = [r for r in rows if r['league']==league and r['match_date']<cutoff]
    if len(past)<MIN_TRAIN:
        return None
    for r in past:
        if not r['home_id'] or not r['away_id'] or r['home_id']==r['away_id']:
            raise ValueError('invalid_team_identity')
        h,a=int(r['home_goals']),int(r['away_goals'])
        if min(h,a)<0:raise ValueError('negative_goals')
        if r['result']!=('H' if h>a else 'A' if a>h else 'D'):
            raise ValueError('incorrect_final_result')
    return sorted(past,key=lambda r:(r['match_date'],r['fixture_id']))


def _design(past,cutoff):
    teams=sorted(set(r['home_id'] for r in past)|set(r['away_id'] for r in past))
    ix={t:i for i,t in enumerate(teams)};m=len(teams);n=len(past)
    # 2 intercepts, shared team attack/defence, four venue deviations
    # venue effects are separately regularized; never multiply goal signals twice.
    ind=[];col=[];values=[];y=np.zeros(n*2);weights=np.zeros(n*2)
    for j,r in enumerate(past):
        h=ix[r['home_id']];a=ix[r['away_id']]
        for idx,columns,goal in (
            (2*j,(0,2+h,2+m+a,2+2*m+h,2+5*m+a),'home_goals'),
            (2*j+1,(1,2+a,2+m+h,2+3*m+a,2+4*m+h),'away_goals')):
            for c in columns:ind.append(idx);col.append(c);values.append(1.)
            y[idx]=int(r[goal])
            # Earlier matches get more weight, but decay is learned on dev only.
            weights[idx]=(date.fromisoformat(cutoff)-date.fromisoformat(r['match_date'])).days
    X=csr_matrix((values,(ind,col)),shape=(2*n,2+6*m))
    return X,y,weights,ix,m


def fit_m4(rows,league,cutoff,settings):
    past=validate_history(rows,cutoff,league)
    if past is None:return None
    X,y,ages,ix,m=_design(past,cutoff)
    w=np.exp(-math.log(2)*ages/settings.half_life_days)
    w/=float(w.mean())
    beta=np.zeros(X.shape[1]);beta[0]=math.log(max(0.05,float(y[::2].mean())));beta[1]=math.log(max(0.05,float(y[1::2].mean())))
    penalty=np.concatenate((np.zeros(2),np.full(2*m,settings.ridge_shared),np.full(4*m,settings.ridge_venue)))
    def objective(p):
        eta=X@p
        mu=np.exp(np.clip(eta,-20,15))
        err=w*(mu-y)
        return (float(np.dot(w,mu-y*eta)+.5*np.dot(penalty,p*p)),
                np.asarray(X.T@err).ravel()+penalty*p)
    fit=minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':150,'ftol':1e-9})
    if not fit.success and float(np.linalg.norm(fit.jac))>0.1:
        return None
    if not np.isfinite(fit.x).all():return None
    return (fit.x,ix,m,len(past))


def predict_m4(fit,home,away):
    if fit is None:return None
    beta,ix,m,n=fit
    def v(team,offset):return float(beta[offset+ix[team]]) if team in ix else 0.
    eta_h=float(beta[0])+v(home,2)+v(away,2+m)+v(home,2+2*m)+v(away,2+5*m)
    eta_a=float(beta[1])+v(away,2)+v(home,2+m)+v(away,2+3*m)+v(home,2+4*m)
    lh,la=math.exp(eta_h),math.exp(eta_a)
    if not all(math.isfinite(x) and .05<=x<=5 for x in (lh,la)):
        return None
    return lh,la


def score_markets(lh,la):
    """One coherent full-time joint distribution, no untracked mass."""
    if not all(math.isfinite(x) and .05<=x<=5 for x in (lh,la)):
        raise ValueError('unusable_expected_goals')
    def pois(mu):
        p=[math.exp(-mu)]
        while 1-sum(p)>1e-13 and len(p)<70:
            p.append(p[-1]*mu/len(p))
        if 1-sum(p)>1e-10:raise ValueError('poisson_tail_uncontrolled')
        return np.asarray(p)
    ph,pa=pois(lh),pois(la);matrix=np.outer(ph,pa)
    tail=max(0,1-float(matrix.sum()))
    if tail>1e-9:raise ValueError('joint_mass_uncontrolled')
    matrix/=matrix.sum()
    h=np.arange(len(ph))[:,None];a=np.arange(len(pa))[None,:]
    r={'H':float(matrix[h>a].sum()),'D':float(matrix[h==a].sum()),'A':float(matrix[h<a].sum())}
    markets={'1X2':r,'BTTS_YES':float(matrix[(h>0)&(a>0)].sum())}
    markets['BTTS_NO']=1-markets['BTTS_YES']
    for line in (1.5,2.5,3.5):
        over=float(matrix[(h+a)>line].sum())
        markets[f'OVER_{line:g}']=over;markets[f'UNDER_{line:g}']=1-over
    scores=sorted(((float(matrix[i,j]),f'{i}-{j}') for i in range(len(ph)) for j in range(len(pa))),reverse=True)
    if abs(sum(r.values())-1)>1e-10:raise ValueError('invalid_1x2_sum')
    for line in (1.5,2.5,3.5):
        if abs(markets[f'OVER_{line:g}']+markets[f'UNDER_{line:g}']-1)>1e-10:raise ValueError('inconsistent_goals_market')
    if abs(markets['BTTS_YES']+markets['BTTS_NO']-1)>1e-10:raise ValueError('inconsistent_btts_market')
    return {'lambda_home':lh,'lambda_away':la,'markets':markets,'top_scores':{score:prob for prob,score in scores[:5]},'tail_mass':tail,'distribution':'independent_poisson'}


def dev_select(rows):
    """Only 2025/26 chronological dev folds. Never touch future holdout season."""
    permitted=[r for r in rows if r['season']=='2025-2026' and r['match_date']<'2026-07-01']
    leagues=sorted(set(r['league'] for r in permitted))
    folds=(('2025-11-15','2025-12-06'),('2026-01-15','2026-02-05'),('2026-03-15','2026-04-05'))
    results=[]
    for setting in CANDIDATES:
        num=0;total=0.;brier=0.;failed=0;per_fold=[]
        for league in leagues:
            for train_until,end in folds:
                evalrows=[r for r in permitted if r['league']==league and train_until<=r['match_date']<end]
                if not evalrows:continue
                fit=fit_m4(permitted,league,train_until,setting)
                if fit is None:
                    failed+=len(evalrows);continue
                # Fixed fit for the following block: NO future outcome refit mid-fold.
                nf=0
                for r in evalrows:
                    lam=predict_m4(fit,r['home_id'],r['away_id'])
                    if lam is None:failed+=1;continue
                    p=score_markets(*lam)['markets']['1X2'];y=r['result']
                    total-=math.log(max(0.001,p[y]))
                    brier+=sum((p[k]-int(k==y))**2 for k in ('H','D','A'))
                    num+=1;nf+=1
                per_fold.append({'league':league,'start':train_until,'n':nf})
        results.append({'settings':asdict(setting),'n':num,'failed':failed,'logloss':total/num if num else None,
                        'brier':brier/num if num else None,'folds':per_fold})
    eligible=[r for r in results if r['n']>=200 and r['failed']<=r['n']//10]
    if not eligible:raise ValueError('insufficient_chronological_development_sample')
    # Coverage first, then log-loss, then Brier. All tie-breaks deterministic.
    best=min(eligible,key=lambda z:(z['logloss'],z['brier'],z['settings']['half_life_days'],z['settings']['ridge_shared'],z['settings']['ridge_venue']))
    return {'schema':'m4_dev_lock_263_v1','model':FEATURE_VERSION,'training_season':'2025-2026',
            'evaluation_season_excluded':'2026-2027','cutoffs':folds,'candidate_grid':[asdict(c) for c in CANDIDATES],
            'settings':best['settings'],'winner_dev':best,'all_candidates':results,
            'status':'CHRONOLOGICAL_DEVELOPMENT_ONLY_NO_PROMOTION'}


def use_lock(lock):
    if lock.get('schema')!='m4_dev_lock_263_v1' or lock.get('model')!=FEATURE_VERSION:
        raise ValueError('m4_lock_missing_or_incompatible')
    if lock.get('candidate_grid')!=[asdict(c) for c in CANDIDATES]:
        raise ValueError('m4_grid_tampered')
    st=Settings(**lock['settings'])
    if st not in CANDIDATES:raise ValueError('m4_not_predeclared_candidate')
    if lock.get('evaluation_season_excluded')!='2026-2027':raise ValueError('holdout_policy_violation')
    return st

