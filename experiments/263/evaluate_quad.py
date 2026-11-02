"""Evaluate only sealed B/C2/C3/M4 pilot records after kickoff; never rewrite them.

Paired metrics use identical matches. Model non-coverage is measured explicitly.
At N=25 inspection is strictly operational; at N=100 statistical evidence
is reported with date-block confidence intervals, without auto promotion.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from random import Random

from exp_263_batch import clean_rows
from forward_c3 import canonical_bytes, read_aware
from forward_quad import SCHEMA

MODELS=('B','C2','C3','M4')


def _metrics(probs,actual,states):
    p=[float(probs[k]) for k in states]
    if any(not math.isfinite(x) or x<0 or x>1 for x in p) or abs(sum(p)-1)>1e-8:
        raise ValueError('invalid_probability_vector')
    pos=states.index(actual)
    return {'logloss':-math.log(max(.001,p[pos])),
            'brier':sum((p[i]-int(i==pos))**2 for i in range(len(p))),
            'is_correct':int(states[p.index(max(p))]==actual)}


def _binary(p,y):
    p=float(p)
    if not math.isfinite(p) or not 0<=p<=1:raise ValueError('invalid_binary_probability')
    return {'logloss':-math.log(max(.001,p if y else 1-p)),
            'brier':(p-int(y))**2,'p':p,'y':int(y)}


def collect(records_dir,actual_csv,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError('aware_time_required')
    now=now.astimezone(timezone.utc)
    actuals=defaultdict(list)
    for r in clean_rows(actual_csv):
        key=(r['league'],r['home_id'],r['away_id'],r['match_date'])
        actuals[key].append(r)
    files=sorted(Path(records_dir).glob('*/*.json'))
    if len(files)>100:raise ValueError('more_than_100_pilot_records')
    seen=set();complete=[];coverage={m:0 for m in MODELS}
    for f in files:
        raw=json.loads(f.read_text(encoding='utf-8'))
        if raw.get('schema')!=SCHEMA:raise ValueError('unexpected_record_schema')
        digest=raw.pop('payload_sha256',None)
        if not digest or hashlib.sha256(canonical_bytes(raw)).hexdigest()!=digest:
            raise ValueError('tampered_prediction_record')
        raw['payload_sha256']=digest
        item=raw['fixture'];kickoff=read_aware(item['kickoff_utc']);made=read_aware(raw['created_at_utc'])
        checked=read_aware(item['source_checked_at_utc'])
        if not checked<=made<kickoff or item.get('fixture_verification')!='VERIFIED_BY_LIVE_OFFICIAL_GATE':
            raise ValueError('not_authentic_prekickoff_record')
        key=(item['league'],item['home_id'],item['away_id'],item['match_local_date'])
        if key in seen:raise ValueError('duplicate_fixture_record')
        seen.add(key)
        preds=raw['model_predictions']
        if set(preds)!=set(MODELS):raise ValueError('missing_required_model_field')
        for m in MODELS:
            if preds[m]['status']=='AVAILABLE':coverage[m]+=1
        if kickoff>=now:continue
        matched=actuals.get(key,[])
        if len(matched)>1:raise ValueError('ambiguous_final_score')
        if not matched:continue
        actual=matched[0]
        h,a=int(actual['home_goals']),int(actual['away_goals'])
        model_scores={};market_scores={}
        for m in MODELS:
            if preds[m]['status']!='AVAILABLE':continue
            market=preds[m]['goals']['markets']
            model_scores[m]=_metrics(market['1X2'],actual['result'],('H','D','A'))
            market_scores[m]={'BTTS':_binary(market['BTTS_YES'],h>0 and a>0),
                              'OVER_2.5':_binary(market['OVER_2.5'],h+a>2)}
        complete.append({'key':key,'date':item['match_local_date'],'league':item['league'],
                         'scores':model_scores,'markets':market_scores,'sha':digest})
    return complete,{'registered':len(files),'finished_matched':len(complete),'coverage':coverage,
                      'unresolved_fixtures':len(files)-len(complete)}


def _avg(items,model,name='logloss'):
    v=[r['scores'][model][name] for r in items if model in r['scores']]
    return sum(v)/len(v) if v else None


def _paired_bootstrap(items,base,candidate,rep=600,seed=20261102):
    days=defaultdict(list)
    for r in items:
        days[r['date']].append([r['scores'][base][k]-r['scores'][candidate][k] for k in ('logloss','brier')])
    if len(days)<10:return None
    daylist=sorted(days);rng=Random(seed);out=[[],[]]
    for _ in range(rep):
        values=[z for day in (daylist[rng.randrange(len(daylist))] for _ in daylist) for z in days[day]]
        for i in range(2):out[i].append(sum(z[i] for z in values)/len(values))
    return {k:{'low':sorted(out[i])[int(.025*rep)],'high':sorted(out[i])[int(.975*rep)-1]}
            for i,k in enumerate(('logloss','brier'))}


def _binary_summary(rows,model,market):
    parts=[r['markets'][model][market] for r in rows if model in r['markets']]
    n=len(parts)
    if not n:return {'n':0,'brier':None,'logloss':None,'calibration_bins':[]}
    bins=[]
    for k in range(5):
        part=[p for p in parts if (k*.2<=p['p']<(k+1)*.2 if k<4 else k*.2<=p['p']<=1)]
        if part:bins.append({'range':[round(k*.2,1),round((k+1)*.2,1)],'n':len(part),
                             'mean_pred':sum(t['p'] for t in part)/len(part),
                             'observed':sum(t['y'] for t in part)/len(part)})
    return {'n':n,'brier':sum(x['brier'] for x in parts)/n,
            'logloss':sum(x['logloss'] for x in parts)/n,'calibration_bins':bins}


def report(records_dir,actual_csv,now=None):
    rows,info=collect(records_dir,actual_csv,now)
    result={'schema':'quad_evaluation_263_v1','status':'EXPERIMENTAL_NO_AUTO_PROMOTION',
            'pilot_goal':100,'registered':info['registered'],
            'finished_matched':info['finished_matched'],
            'unresolved_fixtures':info['unresolved_fixtures'],
            'coverage_registered':info['coverage'],'model_scores':{},'markets':{},
            'four_way_common':{},'paired':{},'by_league':{},
            'record_hashes':sorted(r['sha'] for r in rows)}
    for m in MODELS:
        avail=[r for r in rows if m in r['scores']];n=len(avail)
        result['model_scores'][m]={'n':n,'logloss':_avg(avail,m),
                                   'brier':_avg(avail,m,'brier'),
                                   'top1_accuracy':_avg(avail,m,'is_correct')}
        result['markets'][m]={market:_binary_summary(rows,m,market) for market in ('BTTS','OVER_2.5')}
    common=[r for r in rows if all(m in r['scores'] for m in MODELS)]
    result['four_way_common']={'n':len(common),'scores':{
        m:{'logloss':_avg(common,m),'brier':_avg(common,m,'brier')} for m in MODELS}}
    for ref in ('B','C2','C3'):
        paired=[r for r in rows if ref in r['scores'] and 'M4' in r['scores']]
        result['paired'][f'{ref}_versus_M4']={'n':len(paired),
             'ref_minus_m4_positive_is_better':{
                 metric:_avg(paired,ref,metric)-_avg(paired,'M4',metric) if paired else None
                 for metric in ('logloss','brier')},
             'date_block_bootstrap_95':_paired_bootstrap(paired,ref,'M4')}
    for league in sorted({r['league'] for r in rows}):
        sub=[r for r in rows if r['league']==league]
        result['by_league'][league]={'n':len(sub),**{m:{'n':sum(m in r['scores'] for r in sub),
          'logloss':_avg(sub,m)} for m in MODELS}}
    result['milestone'] = ('PILOT_100_FOR_MANUAL_REVIEW' if info['registered']==100 and len(rows)==100
                           else 'OPERATIONAL_ONLY_AT_25' if info['registered']>=25 and info['registered']<100
                           else 'INCOMPLETE_OR_PENDING')
    result['limitations']=['The 25-match checkpoint never changes coefficients',
                           '100 future matches do not by themselves prove superiority',
                           'Missing C2 output remains missing; four-way comparison uses common matches',
                           'No odds, betting return, or confidence class is certified',
                           'Git hash is tamper-evident but cannot defeat privileged history rewriting']
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--records',required=True);p.add_argument('--final-scores',required=True)
    p.add_argument('--out',required=True);a=p.parse_args()
    data=report(a.records,a.final_scores)
    with Path(a.out).open('x',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'status':data['status'],'registered':data['registered'],
                       'common':data['four_way_common']['n']},ensure_ascii=False))

if __name__=='__main__':main()
