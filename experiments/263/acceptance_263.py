"""2.6.3 OFFLINE one-shot multi-market acceptance audit (retrospective).

- Reuses frozen C0/C1/C3 1X2 predictions; does not rerun earlier Poisson fits.
- Computes NEW canonical C2, independent 1H/corner counter models vs league priors.
- Only outcomes from the 2026/27 retrospective cohort are scored.
- No candidate hyperparameter fitting by outcome, betting, promotion or live logs.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import numpy as np
from analysis_math_core import (load_history,canonical_c2_lambda,score_market,fit_c3,
    _count_lambdas,_corner_dispersion,_negative_binomial_pmf,_matrix,
    MIN_CONTEXT,MIN_OTHER_MARKET_MATCHES)

VERSION='2.6.3_acceptance_v1_experimental'
SOURCE_SHA='35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1'
EVIDENCE_SHA='e41f9fc3dd80d00714e015304ba3beb1e69f309abea5bc71ce8c71f462efdbbf'
TEST_SEASON='2026-2027'
PREV_SEASON='2025-2026'
BOOTSTRAP_SEED=20261101
BOOTSTRAP_REPS=750
CORN_LINES=(7.5,8.5,9.5,10.5)
HALF_LINES=(0.5,1.5,2.5)
FT_LINES=(1.5,2.5,3.5)
CLIP=0.001
MIN_PAIR=150
MIN_IMPROVEMENT=.005


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evidence_predictions(path):
    if sha(path)!=EVIDENCE_SHA:
        raise ValueError('Frozen evidence bytes differ from signed snapshot')
    book=defaultdict(dict)
    with open(path,encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            if r['season']!=TEST_SEASON or r['candidate'] not in {'C0','C1','C3'}:continue
            fid=r['fixture_id'];c=r['candidate']
            if c in book[fid]:raise ValueError('duplicate evidence fixture/candidate')
            ps=[float(r[k]) for k in ('p_home','p_draw','p_away')]
            if any(not math.isfinite(p) or p<0 or p>1 for p in ps) or abs(sum(ps)-1)>1e-7:
                raise ValueError('invalid frozen probabilities')
            book[fid][c]=(r['league'],r['date'],r['result'],ps)
    return book


def categorical_reference(past,field,levels,min_hist=40):
    if len(past)<min_hist:return None
    return [(sum(r[field]==name for r in past)+1)/(len(past)+len(levels)) for name in levels]


def binary_reference(past,field,threshold):
    if len(past)<MIN_OTHER_MARKET_MATCHES:return None
    hits=sum(int(r[field])>threshold for r in past)
    return (hits+1)/(len(past)+2)


def prediction_loss(prob,truth,kind):
    if kind=='binary':
        p=float(prob)
        if not math.isfinite(p) or not 0<=p<=1:raise ValueError('invalid binary p')
        y=int(truth);b=(p-y)**2
        ll=-(y*math.log(min(1-CLIP,max(CLIP,p)))+(1-y)*math.log(min(1-CLIP,max(CLIP,1-p))))
        return ll,b
    if kind=='categorical':
        if len(prob)!=3 or any(not 0<=x<=1 or not math.isfinite(x) for x in prob) or abs(sum(prob)-1)>1e-7:
            raise ValueError('invalid categorical p')
        idx=('H','D','A').index(truth)
        ll=-math.log(min(1-CLIP,max(CLIP,prob[idx])))
        b=sum((p-(i==idx))**2 for i,p in enumerate(prob))
        return ll,b
    raise ValueError('invalid market type')


def rec_stats(rows,name,kind):
    scored=[prediction_loss(r['pred'][name],r['truth'],kind) for r in rows]
    return {'n':len(scored),'logloss':float(np.mean([x[0] for x in scored])) if scored else None,
            'brier':float(np.mean([x[1] for x in scored])) if scored else None}


def day_bootstrap(rows,a,b,kind):
    groups=defaultdict(list)
    for r in rows:
        la=prediction_loss(r['pred'][a],r['truth'],kind)
        lb=prediction_loss(r['pred'][b],r['truth'],kind)
        groups[r['date']].append([la[0]-lb[0],la[1]-lb[1]])
    if not groups:return None
    days=sorted(groups)
    sums=np.asarray([np.sum(groups[d],axis=0) for d in days])
    counts=np.asarray([len(groups[d]) for d in days])
    rng=np.random.default_rng(BOOTSTRAP_SEED)
    ids=rng.integers(0,len(days),size=(BOOTSTRAP_REPS,len(days)))
    means=sums[ids].sum(axis=1)/counts[ids].sum(axis=1)[:,None]
    return {'block':'calendar_day','days':len(days),'replicates':BOOTSTRAP_REPS,
            'logloss_95':[float(x) for x in np.quantile(means[:,0],[.025,.975])],
            'brier_95':[float(x) for x in np.quantile(means[:,1],[.025,.975])]}


def reliability_bins(rows,name,kind):
    if kind!='binary':return {'status':'MULTICLASS_RELIABILITY_DEFERRED'}
    bins=[]
    for i in range(5):
        rr=[r for r in rows if name in r['pred'] and (i/5<=r['pred'][name]<(i+1)/5 or i==4 and r['pred'][name]==1)]
        bins.append({'range':[i/5,(i+1)/5],'n':len(rr),
                     'mean_prediction':round(float(np.mean([r['pred'][name] for r in rr])),6) if rr else None,
                     'event_rate':round(float(np.mean([r['truth'] for r in rr])),6) if rr else None})
    return {'status':'DESCRIPTIVE_ONLY','bins':bins}


def summarize_compare(book,market,candidate,reference,kind):
    rr=[r for r in book.get(market,[]) if candidate in r['pred'] and reference in r['pred']]
    ref=rec_stats(rr,reference,kind);cand=rec_stats(rr,candidate,kind)
    ci=day_bootstrap(rr,reference,candidate,kind)
    differences={'logloss':ref['logloss']-cand['logloss'] if rr else None,
                 'brier':ref['brier']-cand['brier'] if rr else None}
    perleague={}
    for lg in sorted({r['league'] for r in rr}):
        filtered=[r for r in rr if r['league']==lg]
        perleague[lg]={'n':len(filtered),'reference':rec_stats(filtered,reference,kind),
                       'candidate':rec_stats(filtered,candidate,kind)}
    sufficient=len(rr)>=MIN_PAIR
    signal=(sufficient and differences['logloss']>=MIN_IMPROVEMENT and differences['brier']>=0
            and ci['logloss_95'][0]>0)
    return {'market':market,'candidate':candidate,'reference':reference,'same_matches':len(rr),
            'coverage_of_2026_27':round(len(rr)/880,6),'reference_stats':ref,'candidate_stats':cand,
            'ref_minus_candidate_positive_is_better':differences,'bootstrap_by_day':ci,
            'by_league':perleague,
            'reliability':reliability_bins(rr,candidate,kind),
            'decision':'RETROSPECTIVE_SIGNAL_NOT_APPROVED' if signal else ('INSUFFICIENT_COVERAGE' if not sufficient else 'NO_ESTABLISHED_GAIN')}


def _new_categorical(markets):
    return [markets[k] for k in ('MS1','MSX','MS2')]


def prefit(past,market):
    """One model fit per league/calendar date, not per target fixture."""
    if market=='half':
        sub=[r for r in past if r['_ht_usable']]
        hfield,afield='half_time_home_goals','half_time_away_goals'
    else:
        sub=[r for r in past if r['_corner_usable']]
        hfield,afield='home_corners','away_corners'
    if len(sub)<MIN_OTHER_MARKET_MATCHES:return (sub,None,None)
    adapted=[{**r,'home_goals':r[hfield],'away_goals':r[afield]} for r in sub]
    fit=fit_c3(adapted)
    dispersion=_corner_dispersion(adapted,fit) if fit is not None and market=='corners' else None
    return sub,fit,dispersion


def count_market(fit,disp,home,away,market):
    if fit is None:return None
    lam=_count_lambdas(fit,home,away,cap=5. if market=='half' else 30.)
    if lam is None:return None
    if market=='half':
        return score_market(*lam,lines=HALF_LINES)['markets']
    alpha=disp['alpha']
    ph,th=_negative_binomial_pmf(lam[0],alpha)
    pa,ta=_negative_binomial_pmf(lam[1],alpha)
    mat,tail=_matrix(ph,pa,th,ta)
    h=np.arange(len(ph))[:,None];a=np.arange(len(pa))[None,:]
    return {f'OVER_{line:g}':float(mat[h+a>line].sum()) for line in CORN_LINES}


def run(history_path,evidence_path,output_dir):
    if sha(history_path)!=SOURCE_SHA:raise ValueError('Source data checksum changed')
    rows,quality=load_history(history_path)
    evidence=evidence_predictions(evidence_path)
    prepare_history(rows)
    if len(rows)!=4413 or len({r['league'] for r in rows})!=10:raise ValueError('Unexpected snapshot size')
    byleague=defaultdict(list)
    for r in rows:byleague[r['league']].append(r)
    book=defaultdict(list); coverage=Counter(); blocked=Counter(); evidence_found=set(); prediction_audit=[]
    for league,lr in sorted(byleague.items()):
        past=[];i=0
        while i<len(lr):
            day=lr[i]['match_date'];j=i
            while j<len(lr) and lr[j]['match_date']==day:j+=1
            group=lr[i:j]
            if group[0]['season']!=TEST_SEASON:
                past.extend(group);i=j;continue
            current=[r for r in past if r['season']==TEST_SEASON]
            previous=[r for r in past if r['season']==PREV_SEASON]
            p_half=[r for r in past if r['_ht_usable']]
            p_corn=[r for r in past if r['_corner_usable']]
            sub_h,fit_h,disp_h=prefit(past,'half')
            sub_c,fit_c,disp_c=prefit(past,'corners')
            # All training samples strictly before the first match of this group.
            if any(r['match_date']>=day for r in past):raise ValueError('DATE_LEAKAGE')
            for r in group:
                fid=r['fixture_id'];home=r['home_id'];away=r['away_id']
                coverage['target_matches']+=1
                old=evidence.get(fid,{})
                cand1={}
                for key,entry in old.items():
                    el,ed,er,probs=entry
                    if (el,ed,er)!=(league,day,r['result']):raise ValueError('frozen evidence / history mismatch')
                    cand1[key]=probs
                    evidence_found.add((fid,key))
                c2,error=canonical_c2_lambda(current,previous,home,away)
                if c2:
                    sc=score_market(c2['lambda_home'],c2['lambda_away'])['markets']
                    cand1['C2']=[sc[k] for k in ('MS1','MSX','MS2')]
                    coverage['C2']+=1
                    for line in FT_LINES:
                        m=f'FT_OVER_{line:g}'
                        prior=binary_reference(past,'_total_goals',line)
                        if prior is not None:
                            add(book,m,'binary',r,{'LEAGUE':prior,'C2':sc[f'OVER_{line:g}']},int(r['_total_goals']>line))
                    prior=binary_reference(past,'_btts',.5)
                    if prior is not None:
                        add(book,'FT_BTTS','binary',r,{'LEAGUE':prior,'C2':sc['BTTS_YES']},r['_btts'])
                else:blocked[f'C2:{error}']+=1
                if cand1:
                    add(book,'FT_1X2','categorical',r,cand1,r['result'])
                if r['_ht_usable']:
                    prior_ht1=categorical_reference(p_half,'half_time_result',('H','D','A'))
                    ctx_h=sum(x['home_id']==home for x in sub_h)
                    ctx_a=sum(x['away_id']==away for x in sub_h)
                    hm=None
                    if fit_h is not None and min(ctx_h,ctx_a)>=MIN_CONTEXT:
                        try:hm=count_market(fit_h,None,home,away,'half')
                        except (ValueError,OverflowError,FloatingPointError):blocked['HALF_NUMERIC']+=1
                    else:blocked['HALF_INSUFFICIENT_CONTEXT']+=1
                    if prior_ht1 is not None:
                        ps={'LEAGUE':prior_ht1}
                        if hm is not None:ps['RIDGE_HALF']=_new_categorical(hm)
                        add(book,'HALF_1X2','categorical',r,ps,r['half_time_result'])
                    for line in HALF_LINES:
                        prev=binary_reference(p_half,'_half_goals',line)
                        if prev is not None:
                            cand={'LEAGUE':prev}
                            if hm is not None:cand['RIDGE_HALF']=hm[f'OVER_{line:g}']
                            add(book,f'HALF_OVER_{line:g}','binary',r,cand,int(r['_half_goals']>line))
                else:blocked['HALF_TARGET_INVALID']+=1
                if r['_corner_usable']:
                    ctx_h=sum(x['home_id']==home for x in sub_c)
                    ctx_a=sum(x['away_id']==away for x in sub_c)
                    cm=None
                    if fit_c is not None and min(ctx_h,ctx_a)>=MIN_CONTEXT:
                        try:cm=count_market(fit_c,disp_c,home,away,'corners')
                        except (ValueError,OverflowError,FloatingPointError):blocked['CORN_NUMERIC']+=1
                    else:blocked['CORN_INSUFFICIENT_CONTEXT']+=1
                    for line in CORN_LINES:
                        prev=binary_reference(p_corn,'_total_corners',line)
                        if prev is not None:
                            cand={'LEAGUE':prev}
                            if cm is not None:cand['RIDGE_CORNERS']=cm[f'OVER_{line:g}']
                            add(book,f'CORN_OVER_{line:g}','binary',r,cand,int(r['_total_corners']>line))
                else:blocked['CORN_TARGET_INVALID']+=1
                prediction_audit.append({'id':fid,'league':league,'day':day,'C2':c2 is not None,
                    '1X2_evidence':sorted(k for k in cand1 if k!='C2'),
                    'history_cutoff_exclusive':day})
            past.extend(group);i=j
    all_items={(fid,c) for fid,vals in evidence.items() for c in vals}
    if all_items!=evidence_found:raise ValueError(f'frozen evidence incomplete: {len(all_items)-len(evidence_found)}')
    comparisons=[]
    for a,b in [('C2','C0'),('C2','C1'),('C2','C3'),('C3','C1')]:
        comparisons.append(summarize_compare(book,'FT_1X2',a,b,'categorical'))
    for market in sorted(book):
        if market=='FT_1X2':continue
        cand='C2' if market.startswith('FT_') else ('RIDGE_HALF' if market.startswith('HALF_') else 'RIDGE_CORNERS')
        comparisons.append(summarize_compare(book,market,cand,'LEAGUE', 'categorical' if market=='HALF_1X2' else 'binary'))
    # A decision is only about a reused retrospective cohort, and never a production promotion.
    report={'version':VERSION,'status':'RETROSPECTIVE_REUSED_2026_27_NOT_UNTOUCHED',
      'production_changes':False,'pilot_started':False,'live_match_log':False,
      'source':{'filename':Path(history_path).name,'sha256':SOURCE_SHA,'rows':len(rows),'leagues':len(byleague),
                'market_quarantine':quality['market_quarantine']},
      'old_1x2_predictions':{'sha256':EVIDENCE_SHA,'status':'REUSED_NOT_REFITTED',
                             'selected_models':['C0','C1','C3']},
      'locked_protocol':{'test_season':TEST_SEASON,'prev_season':PREV_SEASON,
          'history_cutoff':'match_date < target_match_date; whole day excluded',
          'C2':'k=5 w=.5 min_context=4', 'C3':'frozen evidence only',
          'ridge_half_and_corner':'previous source coefficients REG=6; no retuning',
          'half_min_history':MIN_OTHER_MARKET_MATCHES,'half_min_context':MIN_CONTEXT,
          'corner_min_history':MIN_OTHER_MARKET_MATCHES,'corner_min_context':MIN_CONTEXT,
          'logloss_clip':[CLIP,1-CLIP],'minimum_paired':MIN_PAIR,
          'minimum_logloss_improvement':MIN_IMPROVEMENT,'day_block_replicates':BOOTSTRAP_REPS,
          'seed':BOOTSTRAP_SEED},
      'coverage':dict(coverage),'blocked':dict(blocked),
      'num_market_pairs':len(comparisons),'comparisons':comparisons,
      'notes':['Old final period already reviewed: never promote models solely from this report',
               'Separate models for halves and corners; no use of final-goal lambda',
               'C2 scored using corrected 2.6.3 four-match context, not old C2 file',
               'No odds, xG, Elo, real fixtures, lineup, bets, bankroll or pilot',
               'Per-market scores are correlated within matches, not independent evidence',
               'No candidate hyperparameter tuning performed by these results']}
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/'acceptance_263.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    with (output_dir/'cutoff_audit.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['id','league','day','C2','1X2_evidence','history_cutoff_exclusive']);w.writeheader()
        for r in prediction_audit:w.writerow({**r,'1X2_evidence':';'.join(r['1X2_evidence'])})
    return report


def add(book,market,kind,row,pred,truth):
    # Fail early rather than silently corrupt scoring.
    for value in pred.values():prediction_loss(value,truth,kind)
    book[market].append({'fixture_id':row['fixture_id'],'league':row['league'],'date':row['match_date'],
                         'truth':truth,'pred':pred})


def prepare_history(rows):
    for r in rows:
        r['_total_goals']=int(r['home_goals'])+int(r['away_goals'])
        r['_btts']=int(int(r['home_goals'])>0 and int(r['away_goals'])>0)
        if r['_ht_usable']:
            hh=int(r['half_time_home_goals']);ha=int(r['half_time_away_goals'])
            r['_half_goals']=hh+ha
            # Cross-check source H/D/A half-time result if present.
            expected='H' if hh>ha else 'A' if hh<ha else 'D'
            if hh>int(r['home_goals']) or ha>int(r['away_goals']) or r.get('half_time_result') not in ('',expected):
                r['_ht_usable']=False
            else:r['half_time_result']=expected
        if r['_corner_usable']:
            r['_total_corners']=int(r['home_corners'])+int(r['away_corners'])


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--history',required=True)
    ap.add_argument('--frozen-predictions',required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    report=run(args.history,args.frozen_predictions,args.out)
    print(json.dumps({'status':report['status'],'targets':report['coverage']['target_matches'],
       'comparisons':[{'market':r['market'],'candidate':r['candidate'], 'n':r['same_matches'],
           'decision':r['decision']} for r in report['comparisons']]},ensure_ascii=False))
