"""2.6.3 SALT-DENEYSEL toplu karsilastirma. Canli motoru degistirmez.
C0 lig frekansi, C1 dokunulmaz Model B matematik esdegeri, C2 k5/w.5,
C3 rakip-ozel reguler Poisson, C4 sadece onceki maclarin isabetli sut artigi.
Onceki sonuca gore C3 hiperparametresi ayarlanmaz. xG C5 veri yoksa atlanir.
"""
import csv, hashlib, json, math, sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.sparse import csr_matrix

SEED=20261101
K=5.0; W=.5; MIN_CONTEXT=4; C1_WINDOW=20; REG=6.0
SHOT_BETAS=(0.0,0.15,0.30,0.5)
TRAIN_SEASON='2025-2026'; EVAL_SEASON='2026-2027'
OUT=Path('outputs_263'); OUT.mkdir(exist_ok=True)

def scores(lh,la):
    if not all(math.isfinite(x) and .05<=x<=5 for x in (lh,la)):
        return None
    ph=np.array([math.exp(-lh)*lh**i/math.factorial(i) for i in range(11)])
    pa=np.array([math.exp(-la)*la**i/math.factorial(i) for i in range(11)])
    mat=np.outer(ph,pa)
    mass=float(mat.sum()); tail=1.-mass
    if tail>0.001:return None
    arr=np.array([float(np.tril(mat,-1).sum()),float(np.trace(mat)),float(np.triu(mat,1).sum())])
    # i>j (lower triangle) home win
    return list(arr/mass),tail

def clean_rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    assert rows and len({r['fixture_id'] for r in rows})==len(rows),'duplicate fixture ids or empty'
    req=('league','season','match_date','home_id','away_id','home_goals','away_goals','result')
    for r in rows:
        assert all(r.get(k) for k in req),'missing required field'
        datetime.fromisoformat(r['match_date'])
        assert r['result'] in 'HDA'
        assert int(r['home_goals'])>=0 and int(r['away_goals'])>=0
        assert r['result']==('H' if int(r['home_goals'])>int(r['away_goals']) else 'A' if int(r['home_goals'])<int(r['away_goals']) else 'D')
    rows.sort(key=lambda r:(r['match_date'],r['fixture_id']))
    return rows

def c0(past):
    n=len(past)
    return [(sum(r['result']==s for r in past)+1)/(n+3) for s in ('H','D','A')] if n>=30 else None

def c1(past,home,away):
    """Static reproduction of experimental_poisson_baseline.estimate(window=20,shrink=5)."""
    if len(past)<30:return None
    home_rows=[r for r in past if r['home_id']==home][-20:]
    away_rows=[r for r in past if r['away_id']==away][-20:]
    if len(home_rows)<5 or len(away_rows)<5:return None
    mh=sum(int(r['home_goals']) for r in past)/len(past)
    ma=sum(int(r['away_goals']) for r in past)/len(past)
    if min(mh,ma)<=0:return None
    def sm(rows,key,mu):return (sum(int(r[key]) for r in rows)+5*mu)/(len(rows)+5)/mu
    lh=max(.05,min(5.,mh*sm(home_rows,'home_goals',mh)*sm(away_rows,'home_goals',mh)))
    la=max(.05,min(5.,ma*sm(away_rows,'away_goals',ma)*sm(home_rows,'away_goals',ma)))
    return scores(lh,la)

def c2(past_season,prior_season,home,away):
    """Birebir 2.6.3 section 6.2: four contextual prior ratios and k=5,w=.5."""
    home_rows=[r for r in past_season if r['home_id']==home]
    away_rows=[r for r in past_season if r['away_id']==away]
    if min(len(home_rows),len(away_rows))<MIN_CONTEXT or len(past_season)<30:return None
    mh=sum(int(r['home_goals']) for r in past_season)/len(past_season)
    ma=sum(int(r['away_goals']) for r in past_season)/len(past_season)
    if min(mh,ma)<=0:return None
    pmh=sum(int(r['home_goals']) for r in prior_season)/len(prior_season) if prior_season else None
    pma=sum(int(r['away_goals']) for r in prior_season)/len(prior_season) if prior_season else None
    def adjusted(team,role,field,ref,prev_ref):
        team_rows=home_rows if role=='home' else away_rows
        prev_team=[r for r in prior_season if r[role+'_id']==team]
        rho=(sum(int(r[field]) for r in prev_team)/len(prev_team)/prev_ref) if prev_team and prev_ref and prev_ref>0 else 1.0
        prior=ref*(W*rho+(1-W))
        return (sum(int(r[field]) for r in team_rows)+K*prior)/(len(team_rows)+K)
    ha=adjusted(home,'home','home_goals',mh,pmh)
    hd=adjusted(home,'home','away_goals',ma,pma)
    aa=adjusted(away,'away','away_goals',ma,pma)
    ad=adjusted(away,'away','home_goals',mh,pmh)
    lh=ha*ad/mh;la=aa*hd/ma
    if not (.05<=lh<=5 and .05<=la<=5):return None
    return scores(lh,la)

def fit_c3(past):
    """Ridge-Poisson joint team attack/defence, single log link (opponent accounted ONCE).
    One fit per league/day using only strictly earlier match days.
    """
    if len(past)<30:return None
    teams=sorted(set(r['home_id'] for r in past)|set(r['away_id'] for r in past))
    m=len(teams); ix={t:i for i,t in enumerate(teams)}
    n=len(past); ind=[]; cols=[]; vals=[]; ys=[]
    for j,r in enumerate(past):
        hi=ix[r['home_id']]; ai=ix[r['away_id']]
        # intercept home and away, attacks of scoring teams, defences of opponents.
        for side,rowid,att,defe,inter,g in [('h',2*j,hi,ai,0,'home_goals'),('a',2*j+1,ai,hi,1,'away_goals')]:
            for c in [inter,2+att,2+m+defe]:ind.append(rowid);cols.append(c);vals.append(1.)
            ys.append(int(r[g]))
    x=csr_matrix((vals,(ind,cols)),shape=(2*n,2+2*m))
    y=np.array(ys,dtype=float)
    mh=max(0.05,float(y[::2].mean()));ma=max(.05,float(y[1::2].mean()))
    init=np.zeros(2+2*m);init[0]=math.log(mh);init[1]=math.log(ma)
    def f_grad(beta):
        eta=np.clip(x@beta,-6,5)
        mu=np.exp(eta)
        penalty=REG/2*float(np.dot(beta[2:],beta[2:]))
        loss=float(np.sum(mu-y*eta))+penalty
        grad=np.asarray(x.T@(mu-y)).ravel()
        grad[2:]+=REG*beta[2:]
        return loss,grad
    res=minimize(f_grad,init,jac=True,method='L-BFGS-B',options={'maxiter':70,'ftol':1e-8})
    if not res.success and res.jac is not None and np.linalg.norm(res.jac)>0.05:
        return None
    return (res.x,ix,m)

def predict_c3(fit,home,away):
    beta,ix,m=fit
    # unseen teams centered at league average; no fabricated team ratings
    def v(team,pos):return beta[pos+ix[team]] if team in ix else 0.
    lh=float(np.exp(beta[0]+v(home,2)+v(away,2+m)))
    la=float(np.exp(beta[1]+v(away,2)+v(home,2+m)))
    return (lh,la) if .05<=lh<=5 and .05<=la<=5 else None

def shot_signal(past,home,away,lh,la):
    """Historical shots on target only. Residualizes against C3 goal strength;
    controls for existing goal evidence and tests incremental value, not guaranteed independence.
    Missing shot fields are excluded, never imputed as zero.
    """
    usable=[r for r in past if all(r.get(k,'')!='' for k in ('home_shots_on_target','away_shots_on_target'))]
    if len(usable)<30:return None
    mh=sum(int(r['home_shots_on_target']) for r in usable)/len(usable)
    ma=sum(int(r['away_shots_on_target']) for r in usable)/len(usable)
    gh=sum(int(r['home_goals']) for r in past)/len(past)
    ga=sum(int(r['away_goals']) for r in past)/len(past)
    if min(mh,ma,gh,ga)<=0:return None
    h=[r for r in usable if r['home_id']==home];a=[r for r in usable if r['away_id']==away]
    if min(len(h),len(a))<4:return None
    def smooth(rr,key,mu):return (sum(int(r[key]) for r in rr)+K*mu)/(len(rr)+K)
    predicted_home_sot=smooth(h,'home_shots_on_target',mh)*smooth(a,'home_shots_on_target',mh)/mh
    predicted_away_sot=smooth(a,'away_shots_on_target',ma)*smooth(h,'away_shots_on_target',ma)/ma
    # 'shot pressure' net of existing goals-based matchup strength.
    return (math.log(predicted_home_sot/mh)-math.log(lh/gh),
            math.log(predicted_away_sot/ma)-math.log(la/ga))

def apply_shots(base,signal,beta):
    lh,la=base;fh,fa=signal
    h=lh*math.exp(beta*fh);a=la*math.exp(beta*fa)
    return scores(h,a)

def loss(ps,y):
    idx=('H','D','A').index(y)
    return (-math.log(max(1e-12,ps[idx])),sum((p-int(i==idx))**2 for i,p in enumerate(ps)))

def summarize(items,key):
    vals=[loss(r['pred'][key][0],r['result']) for r in items if key in r['pred']]
    return {'n':len(vals),'logloss':sum(x[0] for x in vals)/len(vals) if vals else None,'brier':sum(x[1] for x in vals)/len(vals) if vals else None}

def pair(rows,a,b):
    subset=[r for r in rows if a in r['pred'] and b in r['pred']]
    s1=summarize(subset,a);s2=summarize(subset,b)
    return {'n':len(subset),'a':s1,'b':s2,'a_minus_b_positive_is_better':{k:s1[k]-s2[k] if subset else None for k in ('logloss','brier')}}

def bootstrap_by_day(items,a,b,replicates=600):
    groups=defaultdict(list)
    for r in items:
        if a in r['pred'] and b in r['pred']:
            al=loss(r['pred'][a][0],r['result']);bl=loss(r['pred'][b][0],r['result'])
            groups[r['date']].append([al[0]-bl[0],al[1]-bl[1]])
    days=sorted(groups)
    if not days:return None
    rng=np.random.default_rng(SEED)
    block_sum=np.array([np.sum(groups[d],axis=0) for d in days]);block_n=np.array([len(groups[d]) for d in days])
    x=rng.integers(0,len(days),size=(replicates,len(days)))
    samples=block_sum[x].sum(axis=1)/block_n[x].sum(axis=1)[:,None]
    return {'days':len(days),'replicates':replicates,
            'logloss_95':np.quantile(samples[:,0],[.025,.975]).tolist(),
            'brier_95':np.quantile(samples[:,1],[.025,.975]).tolist()}

def run(path):
    rows=clean_rows(path)
    source_sha=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    byleague=defaultdict(list)
    for r in rows:byleague[r['league']].append(r)
    records=[];failures=Counter();diagnostics=Counter()
    for league,lr in sorted(byleague.items()):
        past=[];i=0
        while i<len(lr):
            day=lr[i]['match_date'];j=i
            while j<len(lr) and lr[j]['match_date']==day:j+=1
            fixtures=lr[i:j]
            # Fit from pre-date rows once, before learning any same-day results.
            fit=fit_c3(past) if len(past)>=30 else None
            prior_seasons={s:[r for r in past if r['season']==s] for s in (TRAIN_SEASON,EVAL_SEASON)}
            for r in fixtures:
                home=r['home_id'];away=r['away_id'];season=r['season'];pred={}
                base0=c0(past)
                if base0:pred['C0']=(base0,0.0)
                base1=c1(past,home,away)
                if base1:pred['C1']=base1
                ps=prior_seasons.get(season,[])
                earlier=prior_seasons.get(TRAIN_SEASON,[]) if season==EVAL_SEASON else []
                base2=c2(ps,earlier,home,away)
                if base2:pred['C2']=base2
                if fit:
                    lam=predict_c3(fit,home,away)
                    if lam:
                        base3=scores(*lam)
                        if base3:
                            pred['C3']=base3
                            ss=shot_signal(past,home,away,*lam)
                            if ss:
                                for beta in SHOT_BETAS:
                                    p4=apply_shots(lam,ss,beta)
                                    if p4:pred[f'C4_{beta:g}']=p4
                for name in ('C0','C1','C2','C3','C4_0'):
                    if name not in pred:failures[f'{season}:{name}']+=1
                for name,(p,tail) in pred.items():
                    assert abs(sum(p)-1)<1e-10
                    assert all(0<=x<=1 for x in p)
                    if name=='C1':diagnostics['c1_success']+=1
                records.append({'fixture_id':r['fixture_id'],'league':league,'season':season,'date':day,'result':r['result'],'pred':pred})
            past+=fixtures;i=j
    # C4: Choose coefficient only using 2025/26 final ~half-year as chronological validation.
    dev=[r for r in records if r['season']==TRAIN_SEASON and r['date']>='2026-01-01']
    cv={str(b):summarize([r for r in dev if all(f'C4_{k:g}' in r['pred'] for k in SHOT_BETAS)],f'C4_{b:g}') for b in SHOT_BETAS}
    if not all(v['n']>=150 for v in cv.values()):
        chosen=None
    else:
        chosen=min(SHOT_BETAS,key=lambda b:(cv[str(b)]['logloss'],b))
        for r in records:
            if f'C4_{chosen:g}' in r['pred']:
                r['pred']['C4']=r['pred'][f'C4_{chosen:g}']
    train=[r for r in records if r['season']==TRAIN_SEASON]
    final=[r for r in records if r['season']==EVAL_SEASON]
    cols=['C0','C1','C2','C3','C4']
    comparisons={f'{a}_vs_{b}':{'train':pair(train,a,b),'final':pair(final,a,b),'ci_final':bootstrap_by_day(final,a,b)} for a,b in [('C0','C1'),('C1','C2'),('C0','C2'),('C1','C3'),('C0','C3'),('C3','C4'),('C1','C4')]}
    # Primary equal-population three-way: C0,C1,C2,C3 on precisely identical fixtures.
    common=[r for r in final if all(c in r['pred'] for c in ('C0','C1','C2','C3'))]
    common_scores={c:summarize(common,c) for c in ('C0','C1','C2','C3')}
    sensitivity={}
    for c in ('C2','C3','C4'):
        paired=[r for r in final if all(v in r['pred'] for v in ('C1','C0',c))]
        league_scores={}
        for lg in sorted(set(r['league'] for r in paired)):
            part=[r for r in paired if r['league']==lg]
            league_scores[lg]={'n':len(part),'c':summarize(part,c),'c1':summarize(part,'C1'),'c0':summarize(part,'C0')}
        sensitivity[c]=league_scores
    report={'version':'263_experimental_batch_v1','status':'RETROSPECTIVE_EXPERIMENT_ONLY','data_file':Path(path).name,'data_sha256':source_sha,
            'matches':len(rows),'leagues':len(byleague),'by_season':dict(Counter(r['season'] for r in rows)),
            'locked_settings':{'k':K,'w':W,'c2_min_context':MIN_CONTEXT,'c1_window':C1_WINDOW,'c3_ridge':REG,'shot_betas':SHOT_BETAS,'shot_validation_start':'2026-01-01','bootstrap_seed':SEED},
            'stage_eligibility':{'development':len(train),'reused_final_2026_27':len(final)},
            'coverage':{s:{c:sum(c in r['pred'] for r in rr) for c in cols} for s,rr in [('train',train),('reused_final',final)]},
            'common_c0_c1_c2_c3_final':{'n':len(common),'results':common_scores},
            'paired_comparisons':comparisons,'by_league':sensitivity,
            'c4_validation_only_train':cv,'selected_c4_beta':chosen,
            'c5':{'status':'NOT_EVALUATED','reason':'The locked 31 Oct source artifact lacks match-level verified xG history; existing 1 Nov xG comparison is preserved, not repeated.'},
            'first_half_and_corners':{'status':'NOT_REPEATED','reason':'Previous experimental backtests already failed league reference; no predeclared genuinely new viable candidate.'},
            'old_evidence_reused':['team-source-audit run 41251343847','xG paired run 41292163144','first-half & corners: devir document'],
            'limitations':['2026/27 was already inspected in previous experiments: not an untouched independent final holdout',
                'Historical source snapshot dated 31 Oct; no new data added','Same-day matches excluded from all features','Ridge strength fixed a priori (not tuned)','No claim of calibrated match predictions or production integration',
                'C4 shot evidence shares dependencies with goal variables despite residualization','C3 home/away intercept plus pooled team effects; does not use 2.6.3 fixed w prior'],
            'fit_failures':dict(failures),'diagnostics':dict(diagnostics)}
    # External prospective holdout is required before production promotion.
    decisions={}
    for c in ('C2','C3','C4'):
        # C4 is an incremental feature of C3, so it MUST beat C3, not merely C1.
        refs=('C3',) if c=='C4' else ('C0','C1')
        sub=[r for r in final if all(m in r['pred'] for m in (*refs,c))]
        if len(sub)<150:decisions[c]='KANIT_YETERSIZ_NO_PROMOTION';continue
        primary=pair(sub,refs[-1],c)
        ci=bootstrap_by_day(sub,refs[-1],c)
        improves_base=primary['a_minus_b_positive_is_better']['logloss']>=.005
        if c!='C4':
            secondary=pair(sub,'C0',c)
            improves_base=improves_base and secondary['a_minus_b_positive_is_better']['logloss']>=.005
        improved=(improves_base and primary['a_minus_b_positive_is_better']['brier']>=0 and ci['logloss_95'][0]>0)
        decisions[c]='RETROSPECTIVE_SIGNAL_FUTURE_HOLDOUT_REQUIRED' if improved else 'DO_NOT_PROMOTE'
    decisions['C1']='KEEP_UNCHANGED_EXPERIMENTAL';decisions['C5']='SKIP_UNVERIFIED_COVERAGE'
    report['decisions']=decisions
    OUT.mkdir(exist_ok=True)
    (OUT/'report_263.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (OUT/'predictions_263.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['fixture_id','league','season','date','result','candidate','p_home','p_draw','p_away','tail_mass'])
        for r in records:
            for c,(ps,tail) in r['pred'].items():
                if c.startswith('C4_'):continue
                w.writerow([r[k] for k in ('fixture_id','league','season','date','result')]+[c,*ps,tail])
    return report

if __name__=='__main__':
    rep=run(sys.argv[1] if len(sys.argv)>1 else 'historical_results.csv')
    print(json.dumps({'status':rep['status'],'matches':rep['matches'],'coverage':rep['coverage'],'common_final':rep['common_c0_c1_c2_c3_final'],'decisions':rep['decisions']},ensure_ascii=False,indent=2))
