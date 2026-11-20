"""Independent 263 exploratory audit. Only previously sealed/as-of forecasts, no mutation."""
import argparse, collections, hashlib, json, math, random
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from scipy.special import gammaln
from sklearn.linear_model import LogisticRegression
from chrono_goal_stage2_263 import load_predictions
from chrono_goal_decision_263 import MARKETS, outcome

ROOT=Path(__file__).resolve().parents[2]
GROUP={"MS":('MS1','MSX','MS2'),"KG":('BTTS_YES','BTTS_NO'),"O25":('OVER_2.5','UNDER_2.5')}
SEVEN=GROUP['MS']+GROUP['KG']+GROUP['O25']
EVAL_MARKETS=('MS','KG','O25')
SEED=26320261120

def checks(a):
    if abs(sum(a[k] for k in GROUP['MS'])-1)>1e-5:return False
    for f in ('KG','O25'):
        if abs(sum(a[k] for k in GROUP[f])-1)>1e-5:return False
    return all(math.isfinite(v) and 0<=v<=1 for v in a.values())

def from_markets(m):
    ms=m.get('1X2') or {c:m['MS'+s] for c,s in (('H','1'),('D','X'),('A','2'))}
    p={'MS1':ms['H'],'MSX':ms['D'],'MS2':ms['A']}
    p.update({key:m[key] for key in MARKETS if key not in p})
    return p if checks(p) else None

def add_nov8():
    p=ROOT/'data/results_only_263/nov8_new100_terminal_archive_20261112.json'
    data=json.loads(p.read_text())
    assert data['registered']==40 and data['completed']==39 and data['postponed']==1
    rows=[]
    for entry in data['rows']:
        if entry.get('score') is None:continue
        f=json.loads((ROOT/entry['forecast_path']).read_text())
        fx=f['fixture']; h,a=entry['score']
        assert f['created_at_utc']<fx['kickoff_utc'] and fx['match_local_date']=='2026-11-08'
        bpath=ROOT/'experiments/263/sabah_research/new100/2026-11-08'/Path(entry['forecast_path']).stem/'baseline.json'
        baseline=json.loads(bpath.read_text())
        assert baseline['forecast_sha256']==f['payload_sha256']
        pred={}
        for name,item in f['model_predictions'].items():
            if item.get('status')=='AVAILABLE':
                v=from_markets(item['goals']['markets'])
                if v:pred[name]=v
        targets={key:outcome({'home_goals':h,'away_goals':a},key) for key in MARKETS}
        rows.append({'league':entry['league'],'date':'2026-11-08','obs':targets,
                     'base':baseline['markets'],'p':pred})
    assert len(rows)==39
    return rows

def poisson_pmf(mu,n=25):
    x=np.arange(n+1)
    return np.exp(-mu+x*np.log(mu)-gammaln(x+1))

def distributions(lh,la,typ):
    if typ.startswith('DC'):
        rho=-.1 if typ=='DC_MINUS_0.1' else .1
        ph,pa=poisson_pmf(lh),poisson_pmf(la)
        mat=np.outer(ph,pa)
        fac=[1-lh*la*rho, 1+lh*rho, 1+la*rho, 1-rho]
        if min(fac)<0:return None
        for (i,j),v in zip(((0,0),(0,1),(1,0),(1,1)),fac):mat[i,j]*=v
    elif typ=='BIVARIATE_0.15':
        s=min(.15,lh-.01,la-.01)
        if s<=0:return None
        ph,pa=poisson_pmf(lh-s),poisson_pmf(la-s)
        shared=poisson_pmf(s)
        mat=np.zeros((26,26))
        for z in range(26):
            if shared[z]<1e-14:break
            mat[z:,z:]+=shared[z]*np.outer(ph[:26-z],pa[:26-z])
    elif typ.startswith('NB'):
        k=3 if typ=='NB_K3' else 8
        n=50;x=np.arange(n+1)
        def nb(mu):
            return np.exp(gammaln(x+k)-gammaln(k)-gammaln(x+1)+k*np.log(k/(k+mu))+x*np.log(mu/(k+mu)))
        mat=np.outer(nb(lh),nb(la))
    else:raise ValueError('unknown distribution')
    mass=float(mat.sum())
    if not .999<=mass<=1.000001:return None
    mat/=mass
    h=np.arange(mat.shape[0])[:,None];a=np.arange(mat.shape[1])[None,:]
    ms=[float(mat[h>a].sum()),float(np.trace(mat)),float(mat[h<a].sum())]
    yes=float(mat[(h>0)&(a>0)].sum());p=dict(zip(GROUP['MS'],ms))
    p['BTTS_YES']=yes;p['BTTS_NO']=1-yes
    for line in (1.5,2.5,3.5):
        o=float(mat[(h+a)>line].sum());p['OVER_'+str(line)]=o;p['UNDER_'+str(line)]=1-o
    return p if checks(p) else None

def invert_pois(p):
    q=p['OVER_2.5']; b=p['BTTS_YES']
    if not 0.00001<q<.99999:return None
    f=lambda u:1-math.exp(-u)*(1+u+.5*u*u)-q
    mu=brentq(f,.05,10)
    fun=lambda v:(1-math.exp(-v))*(1-math.exp(-(mu-v)))
    hi=fun(mu/2)
    if b<0 or b>hi+.002:return None
    if b>=hi:low=mu/2
    else:
        if b<=fun(.00001):return None
        low=brentq(lambda x:fun(x)-b,.00001,mu/2)
    lh,la=(mu-low,low) if p['MS1']>=p['MS2'] else (low,mu-low)
    if not (.05<=lh<=5 and .05<=la<=5):return None
    return lh,la

def add_alternatives(rows):
    failed=collections.Counter()
    for r in rows:
        pp=r['p']
        bb=dict(r['base'])
        if checks(bb):pp['ASOF_LEAGUE_RATE']=bb
        if 'C3' in pp and 'M4' in pp:
            ensemble={k:.5*(pp['C3'][k]+pp['M4'][k]) for k in MARKETS}
            if checks(ensemble):pp['ENSEMBLE_50_50']=ensemble
        if 'M4' not in pp:continue
        lam=invert_pois(pp['M4'])
        if lam is None:
            failed['M4_lambda_inversion']+=1;continue
        for key in ('DC_MINUS_0.1','DC_PLUS_0.1','BIVARIATE_0.15','NB_K3','NB_K8'):
            val=distributions(*lam,key)
            if val is not None:pp[key]=val
            else:failed[key]+=1
    return dict(failed)

def score(p,o,family):
    keys=GROUP[family]
    if family=='MS':
        err=sum((p[k]-o[k])**2 for k in keys)
        yes=next(k for k in keys if o[k]);ll=-math.log(max(1e-12,p[yes]))
        correct=int(max(keys,key=lambda k:p[k])==yes)
    else:
        k=keys[0];y=o[k];err=(p[k]-y)**2
        ll=-math.log(max(1e-12,p[k] if y else 1-p[k]))
        correct=int((p[k]>=.5)==bool(y))
    return err,ll,correct

def score_all(rows,name,family):
    arr=[score(r['p'][name],r['obs'],family) for r in rows if name in r['p']]
    if not arr:return {'n':0}
    z=np.asarray(arr)
    return {'n':len(arr),'days':len({r['date'] for r in rows if name in r['p']}),
            'brier':round(float(z[:,0].mean()),7),'logloss':round(float(z[:,1].mean()),7),
            'classification_accuracy':round(float(z[:,2].mean()),5)}

def frozen_shrink(dev):
    # One weight for each coherent family vector; choose only development Brier.
    chosen={}
    for name in ('M4','C3','ENSEMBLE_50_50'):
        if not any(name in r['p'] for r in dev):continue
        chosen[name]={}
        for fam in GROUP:
            grid={}
            for w in (0,.25,.5,.75,1):
                scores=[]
                for r in dev:
                    if name not in r['p']:continue
                    q={k:(1-w)*r['base'][k]+w*r['p'][name][k] for k in MARKETS}
                    scores.append(score(q,r['obs'],fam)[0])
                grid[w]=sum(scores)/len(scores)
            chosen[name][fam]=min(grid,key=lambda k:(grid[k],k))
    return chosen

def apply_shrink(rows,w):
    for r in rows:
        for model,ws in w.items():
            if model not in r['p']:continue
            out={}
            for family,keys in GROUP.items():
                weight=ws[family]
                out.update({key:(1-weight)*r['base'][key]+weight*r['p'][model][key] for key in keys})
            # all three families only; enough for 7-choice selection
            assert checks(out)
            r['p'][model+'_DEV_SHRINK']=out

def logistic_features(r):
    if 'C3' not in r['p'] or 'M4' not in r['p']:return None
    # pre-match forecasts and pre-match past-result rate, never the result
    def logit(p):
        p=min(.999,max(.001,p));return math.log(p/(1-p))
    return [logit(r['p'][m][k]) for m in ('C3','M4','ASOF_LEAGUE_RATE')
            for k in ('MS1','MSX','BTTS_YES','OVER_2.5')]

def fit_direct(dev,rows):
    train=[r for r in dev if logistic_features(r) is not None]
    x=np.asarray([logistic_features(r) for r in train])
    labels={fam:np.array([next(i for i,k in enumerate(GROUP[fam]) if r['obs'][k]) if fam=='MS'
                       else r['obs'][GROUP[fam][0]] for r in train]) for fam in GROUP}
    mods={}
    for fam in GROUP:
        clf=LogisticRegression(C=.5,max_iter=500,random_state=SEED % (2**32))
        clf.fit(x,labels[fam]);mods[fam]=clf
    for r in rows:
        features=logistic_features(r)
        if features is None:continue
        q={}
        for fam in GROUP:
            pred=mods[fam].predict_proba(np.asarray([features]))[0]
            if fam=='MS':q.update(dict(zip(GROUP[fam],map(float,pred))))
            else:
                yes=float(pred[list(mods[fam].classes_).index(1)])
                q[GROUP[fam][0]]=yes;q[GROUP[fam][1]]=1-yes
        assert checks(q)
        r['p']['DIRECT_LOGIT_C0.5']=q
    return {'n_train':len(train),'features':len(x[0]),'C':.5}

def block_interval(rows,name,benchmark,fam,nboot=1600):
    groups=collections.defaultdict(list)
    for r in rows:
        if name in r['p'] and benchmark in r['p']:
            old=score(r['p'][benchmark],r['obs'],fam)[0]
            new=score(r['p'][name],r['obs'],fam)[0]
            groups[r['date']].append(old-new)
    days=sorted(groups);n=sum(map(len,groups.values()))
    if len(days)<4:return {'n':n,'days':len(days),'ci95':None}
    rng=random.Random(SEED)
    sims=[]
    for _ in range(nboot):
        ds=[rng.choice(days) for __ in days]
        vals=[v for d in ds for v in groups[d]]
        sims.append(sum(vals)/len(vals))
    sims.sort();d=[v for day in days for v in groups[day]]
    return {'n':n,'days':len(days),'benchmark_minus_candidate_brier':round(sum(d)/len(d),8),
            'ci95':[round(sims[int(.025*nboot)],8),round(sims[int(.975*nboot)],8)]}

def decisions(rows,policy,floor=None):
    picked=[];types=collections.Counter();pas=0
    for r in rows:
        vectors={}
        if policy=='FIXED_M4_MS_C3_OTHER':
            if 'M4' not in r['p'] or 'C3' not in r['p']:pas+=1;continue
            vectors={**{k:r['p']['M4'][k] for k in GROUP['MS']},
                     **{k:r['p']['C3'][k] for k in GROUP['KG']+GROUP['O25']}}
        else:
            if policy not in r['p']:pas+=1;continue
            vectors=r['p'][policy]
        k=max(SEVEN,key=lambda t:vectors[t]);p=vectors[k]
        if floor is not None and p<floor:pas+=1;continue
        types[k]+=1; picked.append((p,r['obs'][k],k,r['date']))
    n=len(picked)
    return {'n':n,'PAS':pas,'coverage_pct':round(n/max(1,len(rows))*100,2),
            'hit_pct':round(100*sum(int(y) for p,y,k,d in picked)/n,2) if n else None,
            'predicted_mean_pct':round(100*sum(p for p,y,k,d in picked)/n,2) if n else None,
            'selected_event_brier':round(sum((p-y)**2 for p,y,k,d in picked)/n,6) if n else None,
            'market_counts':dict(sorted(types.items()))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--predictions',required=True)
    ap.add_argument('--outdir',default='research/263_independent_audit');a=ap.parse_args()
    matrix=ROOT/'research/263_independent_audit/00_experiment_matrix.json'
    prereg=json.loads(matrix.read_text());assert prereg['seed']==SEED
    rows=load_predictions(a.predictions)
    dev=[r for r in rows if r['date']<'2026-10-01']
    octo=[r for r in rows if r['date']>='2026-10-01']
    nov=add_nov8()
    assert len(dev)==587 and len(octo)==293 and len(nov)==39
    failed=add_alternatives(rows+nov)
    weights=frozen_shrink(dev);apply_shrink(rows+nov,weights)
    trained=fit_direct(dev,octo+nov)
    names=list(prereg['models']);translate={'LEAGUE_ASOF_RATE':'ASOF_LEAGUE_RATE',
        'ENSEMBLE_50_50_C3_M4':'ENSEMBLE_50_50',
        'M4_DIXON_COLES_RHO_-0.1':'DC_MINUS_0.1','M4_DIXON_COLES_RHO_+0.1':'DC_PLUS_0.1',
        'M4_BIVARIATE_SHARED_0.15':'BIVARIATE_0.15',
        'M4_NEGATIVE_BINOMIAL_K3':'NB_K3','M4_NEGATIVE_BINOMIAL_K8':'NB_K8',
        'M4_FAMILY_SHRINK_DEV':'M4_DEV_SHRINK','C3_FAMILY_SHRINK_DEV':'C3_DEV_SHRINK',
        'ENSEMBLE_FAMILY_SHRINK_DEV':'ENSEMBLE_50_50_DEV_SHRINK',
        'DIRECT_REGULARIZED_LOGIT_FIXED_C0.5':'DIRECT_LOGIT_C0.5'}
    cand=[translate.get(s,s) for s in names]
    out={'schema':'263_INDEPENDENT_MATH_AUDIT_EXPLORATORY_V1',
         'preregistered_matrix_sha256':hashlib.sha256(matrix.read_bytes()).hexdigest(),
         'original_4413_sha256':prereg['frozen_source_sha256'],
         'evidence':'AUG_SEP_DEVELOPMENT_OCTOBER_ALREADY_INSPECTED_NOV8_ONE_DAY_SHA_NOT_BLIND',
         'n':{'dev':len(dev),'october':len(octo),'nov8_sha':len(nov)},
         'weights_from_dev':weights,'direct_training':trained,'availability_failures':failed,
         'model_metrics':{},'paired_difference_october':{},'decisions':{},
         'model_promoted':False,'seals_modified':False,'bets_authorized':False}
    bench={'MS':'M4','KG':'C3','O25':'C3'}
    for period,rr in (('october',octo),('nov8_sha',nov)):
        out['model_metrics'][period]={name:{fam:score_all(rr,name,fam) for fam in GROUP} for name in cand}
        out['decisions'][period]={}
        for name in ('M4','C3','ASOF_LEAGUE_RATE','ENSEMBLE_50_50','M4_DEV_SHRINK',
                     'C3_DEV_SHRINK','ENSEMBLE_50_50_DEV_SHRINK','DIRECT_LOGIT_C0.5',
                     'FIXED_M4_MS_C3_OTHER'):
            out['decisions'][period][name]={'unrestricted':decisions(rr,name),
                                             'p65_floor_diagnostic':decisions(rr,name,.65)}
    for name in cand:
        out['paired_difference_october'][name]={fam:block_interval(octo,name,bench[fam],fam) for fam in GROUP}
    path=ROOT/a.outdir;path.mkdir(parents=True,exist_ok=True)
    (path/'02_result.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n')
    lines=['# 2.6.3 — Bağımsız matematik alternatifleri, araştırma sonucu','',
           '**Dönemler:** 587 Ağustos-Eylül geliştirme; 293 Ekim araştırılmış değerlendirme; '
           '39 Kasım 8 orijinal maç önü SHA (tek gün). **Hiçbiri bağımsız kör final sınaması değildir.**','',
           '**Ölçek:** MS çok sınıflı Brier (3 sınıfın toplamı), KG ve 2.5 için tek olayın ikili Brier; küçük değer iyi.','',
           '| Model | Ekim n(MS) | MS Brier | KG Brier | 2.5 Brier |',
           '|---|---:|---:|---:|---:|']
    for name in cand:
        met=out['model_metrics']['october'][name]
        fmt=lambda fam:('%.6f'%met[fam]['brier']) if met[fam].get('n') else '—'
        lines.append(f"| {name} | {met['MS']['n']} | {fmt('MS')} | {fmt('KG')} | {fmt('O25')} |")
    lines+=['','## Ekim 293 maç, aynı maç eşleştirmesi — referans eksi aday Brier','',
            'Pozitif fark aday lehine; farklı model kapsaması çift-eşleme ile sınırlandı. '
            'Gün bloklu %95 aralıklar, çoklu deneme düzeltmesi değil.','',
            '| Aday | Pazar | Ortak n | Fark | Gün bloklu %95 aralık |',
            '|---|---|---:|---:|---|']
    for name in cand:
        for fam in GROUP:
            o=out['paired_difference_october'][name][fam]
            ci=o.get('ci95')
            lines.append(f"| {name} | {fam} | {o['n']} | {o.get('benchmark_minus_candidate_brier','—')} | {ci if ci is not None else 'yetersiz gün'} |")
    lines+=['','## En yüksek olasılıklı tek olay kararı (MS/KG/2.5; maç başına tek karar)','',
            '| Politikа | Ekim seçilen | İabet % | Tahmini ort. % | Seçilen Brier | Kasım 8 isabet % |',
            '|---|---:|---:|---:|---:|---:|']
    for name,vals in out['decisions']['october'].items():
        x=vals['unrestricted']; y=out['decisions']['nov8_sha'][name]['unrestricted']
        lines.append(f"| {name} | {x['n']} | {x['hit_pct']} | {x['predicted_mean_pct']} | {x['selected_event_brier']} | {y['hit_pct']} |")
    lines+=['','## Sınırlar ve mühendislik kararı','',
            '- Sonuçlar **RETROSPEKTİF / KEŞİF**: 2026/27 sonuçları geçmiş araştırmalarda görülmüştü. Ekim iyi çıkınca uygulamaya terfi yok.',
            '- xG zaman damgaları ve özel kaynaklı as-of sayılar bu araştırma dalına taşınmadı; xG ablation tamamlanmış sayılmaz.',
            '- Gol dağılımı DC, bivariate ve Negative Binomial adayları M4 lambdasını sabit tutarak test edildi; bunlar tam yeniden eğitilmiş rakip gol modelleri değildir.',
            '- Doğrudan logit yalnız önceden üretilmiş C3/M4 olasılıkları ve lig geçmişiyle eğitilmiş ikinci-aşama sınıflandırmadır; sıfırdan ham maç özelliği kullanan derin model değildir.',
            '- Model sonuçlarının 39 Kasım mühürlü karşılığı yalnız bir maç günüdür; sonuçların tamamı federasyon seviyesinde bağımsız teyit edilmiş değil.',
            '- Aynı maçtaki 7 sonuç tek bir bağımsız gözlem değildir. Karar tablosu her maç için tam **bir** olay sayar.',
            '- Bahis oranı/EV/ROI bu denetimin hedefi değildir. Herhangi bir yöntemden kâr garantisi çıkmaz.',
            '- **Karar: Mevcut 2.6.3, mühürler, aktif modeller ve PDF korunur.** Denenen adaylar yalnız aday araştırmadır; kör kanıt yokken üretim terfisi yapılamaz.',
            '', 'Ayrıntılı ham ölçümler, kapsama ve eşleşmiş güven aralıkları: `02_result.json`.']
    (path/'03_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('AUDIT_SUMMARY_JSON='+json.dumps({'n':out['n'],
       'metrics':{key:out['model_metrics']['october'][key] for key in ('M4','C3','ASOF_LEAGUE_RATE','ENSEMBLE_50_50','M4_DEV_SHRINK','C3_DEV_SHRINK','DIRECT_LOGIT_C0.5')},
       'decisions':{key:val['unrestricted'] for key,val in out['decisions']['october'].items()}},sort_keys=True))

if __name__=='__main__':main()
