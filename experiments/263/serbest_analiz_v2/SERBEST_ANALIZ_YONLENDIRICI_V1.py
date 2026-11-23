#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MODULAR RESEARCH router, no compulsory PDF, no compulsory M4, no fixed morning time.

Commands:
  # Any league + bookmaker PDF: P0 + Hafiza automatically; M4 when a match exists.
  python SERBEST_ANALIZ_YONLENDIRICI_V1.py --pdf bulletin.pdf --archive oran_hafizasi_tam.json \
       --rule hakem_karar_kurali_v1.json --out-dir results

  # 10-league named match: PDF-free football. Read an archived or recalculated
  # model forecast, NEVER synthesize football probabilities from bookmaker odds.
  python SERBEST_ANALIZ_YONLENDIRICI_V1.py --league TUR1 --home Besiktas \
       --away Kasimpasa --date 2026-11-28 --model-index models.json \
       --rule hakem_karar_kurali_v1.json --out-dir results

  # The main repo's actual source maths, if checked out with its research CSV:
  python SERBEST_ANALIZ_YONLENDIRICI_V1.py --league TUR1 --home Besiktas \
       --away Kasimpasa --date 2026-11-28 --engine-root /repo \
       --history /repo/data/results_only_263/2026-11-10_completed_4617_scores_only.csv \
       --registry /repo/experiments/263/evidence/identity_index_263.json \
       --rule hakem_karar_kurali_v1.json --out-dir results

Missing odds: only one missing slot per market family can be reconstructed via
observed PDF margin. The result is an estimated theoretical price, never an
actual bookmaker offer. Multiple missing slots remain unknown; remaining
markets and other experts still work. Every source has explicit provenance.

All decisions here are research, not evidence of an original pre-kickoff seal.
Never changes M4 code, football history, source PDF, or existing forecast seals.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,re,statistics,sys,unicodedata
from datetime import datetime,timezone,timedelta
from pathlib import Path
import numpy as np

from ORAN_TAMAMLAYICI_V1 import (KEYS,FAMILIES,read_iddaa_pdf,
                  complete_quote_rows,market_probabilities,OddsAuditError)
from HAKEM_KARAR_UYGULA_V1 import (NAMES,SOURCES,choose,load_weights,validate)
from HAKEM_PDF_HAFIZA_M4_KOPRU_V1 import (read_model_index, read_model_repo,
                      split_match,identify,BridgeError,digest_object,name as normalize_model,team as normal_team)
TR=timezone(timedelta(hours=3))
TEN_LEAGUES={'ENG1','ENG2','GER1','ESP1','ITA1','FRA1','NED1','TUR1','POR1','BEL1'}
EXPECTED_HAFIZA_SHA='f80d9646af7d68249afa4445266fa7c721d64ed14b88b53579bf47a691ff13d0'
RADII=(.02,.03,.04,.05,.06,.08,.10)
class RouterError(ValueError):pass


def true_archive(path, expected_sha=None):
    raw=Path(path).read_bytes();sha=hashlib.sha256(raw).hexdigest()
    data=json.loads(raw)
    if (data.get('schema')!='ORAN_HAFIZASI_MOBIL_TAM_V1'
        or data.get('count')!=len(data.get('matches',[]))):
        raise RouterError('FULL_HAFIZA_SCHEMA_OR_COUNT_INVALID')
    if expected_sha and sha!=expected_sha:
        raise RouterError('HAFIZA_EXPECTED_SHA_MISMATCH')
    hist=[x for x in data['matches'] if x.get('split')=='GECMIS' and not x.get('s')]
    test=[x for x in data['matches'] if x.get('split')=='TEST_2026_27']
    if (not hist or len(hist)!=data.get('historical_train_count')
        or len(test)!=data.get('reserved_test_count')
        or len(hist)+len(test)!=data.get('count')
        or len(set(x.get('id') for x in data['matches']))!=data['count']):
        raise RouterError('HAFIZA_SPLITS_OR_IDS_INVALID')
    p=np.array([r['p'] for r in hist],dtype=float)
    score=np.array([r['score'] for r in hist],dtype=int)
    dates=np.array([r['date'] for r in hist])
    if (p.ndim!=2 or p.shape[1]!=7 or score.shape!=(len(hist),2)
        or not np.isfinite(p).all() or not np.isfinite(score).all()
        or np.any(p<0) or np.any(p>1) or np.any(score<0)):
        raise RouterError('CORRUPT_FULL_HAFIZA')
    for ks in FAMILIES.values():
        ii=[KEYS.index(k) for k in ks]
        if np.max(np.abs(p[:,ii].sum(axis=1)-1))>2e-5:
            raise RouterError('HAFIZA_INVALID_NORMALIZED_PROBABILITIES')
    if any(not re.fullmatch(r'\d{4}-\d{2}-\d{2}',x) for x in dates):
        raise RouterError('INVALID_HISTORY_DATE')
    h,a=score[:,0],score[:,1]
    occurred=np.stack((h>a,h==a,h<a,h+a>=3,h+a<=2,(h>0)&(a>0),(h==0)|(a==0)),axis=1).astype('uint8')
    return {'p':p,'y':occurred,'dates':dates,'sha256':sha,'historical_rows':len(hist),'all_rows':len(data['matches'])}


def query_memory(hist,partial_prob,asof_date=None):
    available=[i for i,k in enumerate(KEYS) if partial_prob.get(k) is not None]
    if not available:
        return None
    # Whole families only; reconstruct only from what the source truly supplies.
    if any((k in partial_prob and partial_prob[k] is not None) for k in KEYS):
        for ks in FAMILIES.values():
            if any(partial_prob.get(k) is not None for k in ks) and not all(partial_prob.get(k) is not None for k in ks):
                raise RouterError('PARTIAL_MARKET_PROBABILITY_FAMILY_INVALID')
    q=np.asarray([partial_prob[KEYS[i]] for i in available],dtype=float)
    # A historical retrospective must NOT consult observations from the
    # future or the same match day. Current future matches use all GECMIS.
    valid=np.flatnonzero(hist['dates']<asof_date) if asof_date else np.arange(len(hist['p']))
    if len(valid)==0:return None
    diff=np.max(np.abs(hist['p'][valid][:,available]-q),axis=1)
    idx=None;radius=None
    for radius in RADII:
        idx=valid[np.flatnonzero(diff<=radius+1e-12)]
        if len(idx)>=100:break
    if idx is None or not len(idx):return None
    counts=np.sum(hist['y'][idx],axis=0)
    p=counts/len(idx)
    return {'seven':{k:float(p[i]) for i,k in enumerate(KEYS)},'similar_n':int(len(idx)),
        'radius_pp':radius*100,'counts':{k:int(counts[i]) for i,k in enumerate(KEYS)},
        'historical_rows':hist['historical_rows'],'historical_asof_rows':int(len(valid)),
        'basis':('FULL_SEVEN_MARKET_PROFILE' if len(available)==7 else
                 'PARTIAL_PROFILE_WEAKER_CONDITIONAL_REFERENCE'),
        'matched_probability_dimensions':len(available)}


def decide(experts,weights):
    sources={s:v for s,v in experts.items() if v is not None and any(v.get(k) is not None for k in KEYS)}
    if not sources:return None
    parsed={}
    for s,v in sources.items():
        if set(v)!=set(KEYS):raise RouterError('EXPERT_MUST_PROVIDE_ALL_SEVEN_EVENT_KEYS_NULL_IF_MISSING')
        if all(v[k] is not None for k in KEYS):parsed[s]=validate(v)
        else:
            parsed[s]={k:(None if v[k] is None else float(v[k])) for k in KEYS}
            for f,ks in FAMILIES.items():
                group=[parsed[s][k] for k in ks]
                if any(x is not None for x in group) and (any(x is None for x in group) or abs(sum(group)-1)>2e-5):
                    raise RouterError('INVALID_PARTIAL_EXPERT_FAMILY')
    if len(parsed)==3 and all(all(v[k] is not None for k in KEYS) for v in parsed.values()):
        return {**choose(parsed,weights),'classification':'THREE_SOURCE_FROZEN_HAKEM_V1',
                'sources_used':list(SOURCES)}
    joined={};components={}
    for fam,keys in FAMILIES.items():
        eligible=[s for s in SOURCES if s in parsed and all(parsed[s][k] is not None for k in keys)]
        if not eligible:continue
        denom=sum(weights[fam][SOURCES.index(s)] for s in eligible)
        for k in keys:
            joined[k]=sum(parsed[s][k]*weights[fam][SOURCES.index(s)] for s in eligible)/denom
        components[fam]=eligible
    if not joined:return None
    order=sorted(joined,key=lambda k:(-joined[k],KEYS.index(k)))
    main=order[0];fam=next(f for f,ks in FAMILIES.items() if main in ks)
    alt=next((k for k in order if k not in FAMILIES[fam]),None)
    return {'ana_tercih':main,'ana_tercih_tr':NAMES[main],
       'hakem_arastirma_yuzdesi':round(joined[main]*100,2),
       'alternatif_tercih':alt,'alternatif_tr':NAMES[alt] if alt else None,
       'alternatif_yuzdesi':round(joined[alt]*100,2) if alt else None,
       'tum_7_hakem_yuzdeleri':{k:round(joined[k]*100,2) if k in joined else None for k in KEYS},
       'classification':('ONE_SOURCE_DIRECT_CHOICE' if len(parsed)==1 else
                 'INCOMPLETE_SOURCES_CONDITIONAL_FROZEN_WEIGHT_RENORMALIZATION_UNVALIDATED'),
       'sources_used':list(parsed),'family_sources_used':components,
       'warning':'When fewer than 3 complete sources are available, these weights were NOT trained or independently validated for this combination.'}


def name_identity(x):
    s=str(x).replace('ı','i').replace('İ','I')
    s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c))
    s=s.lower()
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',s)).strip()


def registry_team(registry,league,user_name,league_rows):
    aliases=registry.get('aliases',{})
    key=name_identity(user_name)
    # Identity index normalizes somewhat differently; compare normalized aliases,
    # require a single stable UUID in the selected league training history.
    target={v for k,v in aliases.items() if name_identity(k)==key}
    league_ids={r['home_id'] for r in league_rows}|{r['away_id'] for r in league_rows}
    hits=target & league_ids
    if len(hits)!=1:
        raise RouterError('TEAM_REGISTRY_NOT_UNIQUELY_MATCHED:'+league+':'+user_name)
    return next(iter(hits))


def _calibrate_bin(p,base,positive):
    co={'BTTS_YES':(.120946,.2643173,.5012377),
        'OVER_2.5':(.1100003,.2639998,.2514675)}[positive]
    def lg(x):
        z=max(0.0001,min(.9999,float(x)))
        return math.log(z/(1-z))
    z=co[0]+co[1]*lg(p)+co[2]*lg(base)
    return (1/(1+math.exp(-z))) if z>=0 else (math.exp(z)/(1+math.exp(z)))


def recompute_m4_v4_named(engine_root,history_path,registry_file,league,home,away,asof_date):
    """Runs original locked functional M4/C3 math, NOT a signed fixture/gateway.

    Same-day and future results are excluded. Strict registry UUID mapping.
    Version assumptions are stated; not a substitute for the original forward
    signed official input / accepted append audit.
    """
    if league not in TEN_LEAGUES:raise RouterError('NAMED_FOOTBALL_ONLY_FOR_TEN_LEAGUES')
    root=Path(engine_root).resolve()
    sd=root/'experiments'/'263'
    if not (sd/'m4_integrated.py').is_file() or not (sd/'exp_263_batch.py').is_file():
        raise RouterError('ORIGINAL_M4_C3_ENGINE_FILES_MISSING')
    sys.path.insert(0,str(sd))
    from m4_integrated import Settings,fit_m4,predict_m4,score_markets
    from exp_263_batch import clean_rows,fit_c3,predict_c3
    rows=clean_rows(history_path)
    # Match-date exclusive - never peek at test match, its result, or same-day results.
    past=[r for r in rows if r['league']==league and r['match_date']<asof_date]
    if len(past)<60:raise RouterError('INSUFFICIENT_LEAGUE_PAST_MATCHES')
    index=json.loads(Path(registry_file).read_text(encoding='utf-8'))
    home_id=registry_team(index,league,home,past)
    away_id=registry_team(index,league,away,past)
    if home_id==away_id:raise RouterError('HOME_AWAY_SAME_UUID')
    model_fit=fit_m4(rows,league,asof_date,Settings(half_life_days=360,ridge_shared=4,ridge_venue=48))
    c3_fit=fit_c3(past)
    if model_fit is None or c3_fit is None:raise RouterError('M4_OR_C3_FIT_FAILED')
    lh_la=predict_m4(model_fit,home_id,away_id)
    c3_lh_la=predict_c3(c3_fit,home_id,away_id)
    if lh_la is None or c3_lh_la is None:raise RouterError('MODEL_EXPECTED_GOALS_UNAVAILABLE')
    # Frozen normal policy MS M4 Aug joint coefficients; calibrated C3 KG/O25
    theta=(.05206617557187415,.10909064506028164,1.0154151566181202)
    lh=math.exp(theta[0]+theta[2]*math.log(lh_la[0]))
    la=math.exp(theta[1]+theta[2]*math.log(lh_la[1]))
    market_m4=score_markets(lh,la)['markets']
    market_c3=score_markets(*c3_lh_la)['markets']
    prev_kg=sum(int(int(r['home_goals'])>0 and int(r['away_goals'])>0) for r in past)/len(past)
    prev_o=sum(int(int(r['home_goals'])+int(r['away_goals'])>=3) for r in past)/len(past)
    yes=_calibrate_bin(market_c3['BTTS_YES'],prev_kg,'BTTS_YES')
    over=_calibrate_bin(market_c3['OVER_2.5'],prev_o,'OVER_2.5')
    p={'MS1':market_m4['1X2']['H'],'MSX':market_m4['1X2']['D'],
       'MS2':market_m4['1X2']['A'],'OVER_2.5':over,'UNDER_2.5':1-over,
       'BTTS_YES':yes,'BTTS_NO':1-yes}
    return {'seven':validate(p),
        'model_origin':'ORIGINAL_FORMULAS_RECOMPUTED_ASOF_NOT_SIGNED_OR_OFFICIALLY_GATE_VERIFIED',
        'league_history_matches':len(past),'training_cutoff_exclusive':asof_date,
        'history_file_sha256':hashlib.sha256(Path(history_path).read_bytes()).hexdigest(),
        'engine_versions':'M4_360_4_48_M4_AUG_MS_C3_RIDGE6_V4_CAL_BINARY'}


def _models(model_index,repo_root):
    if model_index and repo_root:raise RouterError('CHOOSE_SINGLE_MODEL_SOURCE')
    if model_index:return read_model_index(model_index)
    if repo_root:return read_model_repo(repo_root)
    return []


def _optional_existing_model(match,time,league,date,models):
    if not models:return None
    r={'match_name_pdf':match,'kickoff_local_time_user_label':time,
       'league_code_user_label':league}
    if time is None:
        # PDF-free named request: unique date + league + exact curated home/away
        h,a=split_match(match)
        hits=[m for m in models if m['league']==league
            and normal_team(m['home'])==normal_team(h)
            and normal_team(m['away'])==normal_team(a)
            and (not date or datetime.fromisoformat(m['kickoff_utc'].replace('Z','+00:00')).astimezone(TR).date().isoformat()==date)]
        if len(hits)>1:raise RouterError('NAMED_MODEL_MATCH_AMBIGUOUS')
        if not hits:return None
        m=hits[0]
    else:
        try:
            m=identify(r,models,date,{tuple(map(int,(date[8:10],date[5:7])))} if date else set())
        except BridgeError as e:
            if str(e).startswith('M4_FIXTURE_NOT_FOUND_OR_ALIAS_REVIEW_REQUIRED'):
                return None
            raise
    return {'seven':validate(m['predicted']),'model_origin':m['model_source'],
       'forecast_sha256':m['forecast_sha256'],'decision_sha256':m['decision_sha256'],
       'league':m['league'],'kickoff_utc':m['kickoff_utc']}


def _outcome(record,raw_row,models,weights,archive,date,league,engine_root=None,history=None,registry=None):
    if raw_row is not None and raw_row.get('error'):
        record.update({'status':'PDF_READER_UNVERIFIED','reason':raw_row['error']});return record
    experts={};evidence={};notes=[]
    if raw_row is not None:
        effective=raw_row['effective_odds']
        p=market_probabilities(effective)
        if any(v is not None for v in p.values()):
            experts['P0']=p
            evidence['P0']={'source':'ORIGINAL_PDF_FOR_AVAILABLE_MARKETS',
                'quotes_missing':list(raw_row['estimated_quotes']),
                'partial_market_families':[f for f,ks in FAMILIES.items() if any(p[k] is None for k in ks)],
                'estimated_prices_are_not_offered':bool(raw_row['estimated_quotes'])}
        if archive is not None:
            mem=query_memory(archive,p,date)
            if mem is not None:
                experts['HAFIZA']=mem['seven'];evidence['HAFIZA']=mem
        record['piyasa']={'real_odds':raw_row['real_odds'],
            'estimated_quotes':raw_row['estimated_quotes'],
            'market_status':raw_row['market_status'],
            'p0_probabilities':p}
    name=record['match']
    found=_optional_existing_model(name,record.get('time'),league,date,models)
    if found is not None:
        experts['M4_C3_V4']=found['seven'];evidence['M4_C3_V4']={k:v for k,v in found.items() if k!='seven'}
        record['league']=found['league']
    elif engine_root and history and registry and league in TEN_LEAGUES and date:
        h,a=split_match(name)
        try:
            calc=recompute_m4_v4_named(engine_root,history,registry,league,h,a,date)
            experts['M4_C3_V4']=calc['seven'];evidence['M4_C3_V4']={k:v for k,v in calc.items() if k!='seven'}
        except (RouterError,KeyError,ValueError) as e:
            notes.append('M4_CALC_NOT_AVAILABLE:'+str(e))
    else:
        notes.append('M4_NOT_SUPPLIED_OR_NOT_AVAILABLE_THIS_MATCH')
    record['experts']=experts;record['evidence']=evidence;record['notes']=notes
    if not experts:
        record['status']='NO_SOURCE_AVAILABLE';record['decision']=None
    else:
        record['status']='ANALYSIS_AVAILABLE'
        record['decision']=decide(experts,weights)
        reconstructed=bool(raw_row is not None and raw_row.get('estimated_quotes'))
        if reconstructed and record['decision'] is not None:
            record['decision']['classification']+='__INPUT_HAS_THEORETICAL_PRICE_UNVALIDATED'
            record['decision']['estimated_prices_used']=True
        record['full_three_source']=(set(experts)==set(SOURCES) and
             all(v is not None for v in experts['P0'].values()) and not reconstructed)
    return record


def run_pdf(pdf,archive_path,weights,model_index=None,repo_root=None,date=None,
            league=None,engine_root=None,history=None,registry=None):
    full=read_iddaa_pdf(pdf)
    rows=complete_quote_rows(full['rows'])
    archive=true_archive(archive_path) if archive_path else None
    models=_models(model_index,repo_root)
    if date:datetime.strptime(date,'%Y-%m-%d')
    result=[]
    for r in rows:
        item={'match':r['match'],'time':r['time'],'date_user_supplied':date,
              'status':'PENDING','pdf_sha256':full['pdf_sha256']}
        result.append(_outcome(item,r,models,weights,archive,date,league,engine_root,history,registry))
    return {'schema':'SERBEST_ANALIZ_MODULER_V1','mode':'PDF_MARKET_OPTIONAL_FOOTBALL',
        'scope':'PDF_ANY_LEAGUE_P0_HAFIZA_M4_ONLY_TEN_LEAGUES','source_sha256':full['pdf_sha256'],
        'count':len(result),'matches':result,
        'memory_archive_sha256':archive['sha256'] if archive else None,
        'memory_history_rows':archive['historical_rows'] if archive else None,
        'warning':'Partial/estimated quotes are NOT bookmaker offers; original 3-source referee weights are not validated with absent sources. Without --date a retrospective as-of memory cut is NOT verified.'}


def run_named(league,home,away,date,weights,model_index=None,repo_root=None,
              engine_root=None,history=None,registry=None):
    if league not in TEN_LEAGUES:raise RouterError('NAMED_FOOTBALL_ONLY_FOR_TEN_LEAGUES')
    datetime.strptime(date,'%Y-%m-%d')
    models=_models(model_index,repo_root)
    label=home+' - '+away
    match=_optional_existing_model(label,None,league,date,models)
    if match is None and engine_root and history and registry:
        m=recompute_m4_v4_named(engine_root,history,registry,league,home,away,date)
    elif match is not None:
        m=match
    else:
        m=None
    item={'match':label,'league':league,'date_user_supplied':date,'time':None,
          'status':'ANALYSIS_AVAILABLE' if m else 'FOOTBALL_MODEL_SOURCE_MISSING',
          'experts':{'M4_C3_V4':m['seven']} if m else {},
          'evidence':{'M4_C3_V4':{k:v for k,v in m.items() if k!='seven'}} if m else {},
          'notes':['PDF_NOT_REQUIRED_FOR_FOOTBALL_MODEL'],
          'decision':decide({'M4_C3_V4':m['seven']},weights) if m else None}
    return {'schema':'SERBEST_ANALIZ_MODULER_V1','mode':'NAMED_TEN_LEAGUE_FOOTBALL_NO_PDF',
       'count':1,'matches':[item],
       'warning':'As-of date is not authenticated official kickoff. This is research, not an original sealed forecast.'}


def format_md(result):
    lines=['# Serbest Analiz - Bagimsiz motorlar / Hakem V1','',
      f"Mod: **{result['mode']}** · Mac: **{result['count']}**",'',
      '| Mac | Kaynaklar | Ana tercih | Alternatif | Kayıt durumu |',
      '|---|---|---|---|---|']
    for r in result['matches']:
        d=r.get('decision') or {}
        main=(f"{d['ana_tercih_tr']} %{d['hakem_arastirma_yuzdesi']:.2f}" if d else 'Üretilemedi')
        alt=(f"{d['alternatif_tr']} %{d['alternatif_yuzdesi']:.2f}" if d.get('alternatif_tr') else '-')
        lines.append('| '+r['match'].replace('|','/')+' | '+', '.join(r.get('experts',{}))+' | '+main+' | '+alt+' | '+r['status']+' |')
    lines+=['','## Sınırlar','- Her mevcut motor tek başına analiz üretebilir.',
            '- Üç kaynak tam olduğunda yalnız dondurulmuş Hakem V1 uygulanır; daha az kaynakta koşullu yeniden ölçekleme deneysel bir yedektir.',
            '- Eksik piyasa oranı diğer fiyatlar ve marjdan teorik olarak hesaplanabilir; **iddaa tarafından sunulduğu anlamına gelmez**.',
            '- Futbol modelinin mevcut olmaması P0/Hafıza analizini engellemez; PDF olmaması da futbol analizini engellemez.',
            '- Hiçbir analiz gerçek doğrulanmış başlangıç ve bağımsız saatli Git commit olmadan yeni maç önü mühürü sayılmaz.',
            '- Bu araştırma kazanç, kalibrasyon veya bahis avantajı garantisi değildir.','']
    for i,r in enumerate(result['matches'],1):
        if r.get('piyasa',{}).get('estimated_quotes'):
            lines.append(f"### {i}. {r['match']} - teorik oranlar")
            for k,val in r['piyasa']['estimated_quotes'].items():
                lines.append(f"- {NAMES[k]}: **{val['theoretical_odds']}** (hesap, teklif degil; {val['overround_source']})")
            lines.append('')
    return '\n'.join(lines)


def save_run(result,out_dir):
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    result['recorded_at_utc']=datetime.now(timezone.utc).isoformat()
    result['record_status']='LOCAL_RESEARCH_APPEND_ONLY_NOT_GITHUB_PREKICKOFF_SEAL'
    result['payload_sha256']=digest_object(result)
    name='SERBEST_ANALIZ_'+result['recorded_at_utc'].replace(':','').replace('.','_').replace('+','_')+'_'+result['payload_sha256'][:12]
    p=out/(name+'.json');m=out/(name+'.md')
    with p.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    with m.open('x',encoding='utf-8') as f:f.write(format_md(result))
    return p,m


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--pdf',type=Path)
    mode.add_argument('--league')
    p.add_argument('--home');p.add_argument('--away');p.add_argument('--date',help='Local YYYY-MM-DD; required for named M4')
    p.add_argument('--pdf-league',help='Optional single-league PDF metadata, e.g. GER1, TUR1')
    p.add_argument('--archive',type=Path,help='Full private odds history; never uploaded')
    p.add_argument('--rule',required=True,type=Path)
    p.add_argument('--model-index',type=Path)
    p.add_argument('--repo-root',type=Path)
    p.add_argument('--engine-root',type=Path)
    p.add_argument('--history',type=Path)
    p.add_argument('--registry',type=Path)
    p.add_argument('--out-dir',type=Path,required=True)
    a=p.parse_args()
    try:
        weights,_=load_weights(a.rule)
        if a.pdf:
            if a.pdf_league and a.pdf_league not in TEN_LEAGUES:
                raise RouterError('INVALID_PDF_LEAGUE_FOR_NAMED_FOOTBALL')
            result=run_pdf(a.pdf,a.archive,weights,a.model_index,a.repo_root,a.date,
                          league=a.pdf_league,
                          engine_root=a.engine_root,history=a.history,registry=a.registry)
        else:
            if not all((a.home,a.away,a.date)):
                raise RouterError('NAMED_MODE_REQUIRES_LEAGUE_HOME_AWAY_DATE')
            result=run_named(a.league,a.home,a.away,a.date,weights,a.model_index,a.repo_root,
                  a.engine_root,a.history,a.registry)
        jf,mf=save_run(result,a.out_dir)
        print(json.dumps({'mode':result['mode'],'matches':result['count'],
            'analysed':sum(x['decision'] is not None for x in result['matches']),
            'json':str(jf),'report':str(mf),'sources':[
              {'match':x['match'],'sources':list(x.get('experts',{})),
               'choice':x['decision']['ana_tercih_tr'] if x.get('decision') else None} for x in result['matches']]},ensure_ascii=False,indent=2))
    except (RouterError,OddsAuditError,BridgeError,ValueError,KeyError,OSError,ImportError) as e:
        p.exit(2,'BLOCKED: '+str(e)+'\n')
if __name__=='__main__':main()
