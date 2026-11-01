"""2.6.3 OFFLINE quality gate: evidence labels, no market selection, no odds.

Never interpret a model probability as calibration / a betting recommendation.
Sources: locked 2026-11-01 acceptance result + as-of-date historical records.
No fixture/first-XI checks; cannot be used as a live-match reporter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

VERSION = '263_quality_gate_v1_offline'
EVIDENCE_SHA256 = '68f7cc5ff1918d70324b56f5182fa7c922b7c7d5dfb1fc40a300f34a28c51fef'
HISTORICAL_SHA256 = '35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1'
MIN_BASELINE = 40

STATUSES = ('KANONIK_HESAPLANDI_AMA_DOGRULANMADI', 'DENEYSEL_RETROSPEKTIF_SINYAL',
            'LIG_REFERANSI_TEK_BASINA', 'VERI_YETERSIZ', 'KARANTINA')

# Label only what the historical comparison actually tested. Fixed before generating reports.
EXPECTED_DECISIONS = {
    ('FT_1X2','C2','C0'):'INSUFFICIENT_COVERAGE',
    ('FT_1X2','C2','C1'):'INSUFFICIENT_COVERAGE',
    ('FT_1X2','C2','C3'):'INSUFFICIENT_COVERAGE',
    ('FT_1X2','C3','C1'):'RETROSPECTIVE_SIGNAL_NOT_APPROVED',
    ('FT_BTTS','C2','LEAGUE'):'INSUFFICIENT_COVERAGE',
    **{('FT_OVER_'+v,'C2','LEAGUE'):'INSUFFICIENT_COVERAGE' for v in ('1.5','2.5','3.5')},
    ('HALF_1X2','RIDGE_HALF','LEAGUE'):'RETROSPECTIVE_SIGNAL_NOT_APPROVED',
    **{('HALF_OVER_'+v,'RIDGE_HALF','LEAGUE'):'NO_ESTABLISHED_GAIN' for v in ('0.5','1.5','2.5')},
    **{('CORN_OVER_'+v,'RIDGE_CORNERS','LEAGUE'):'NO_ESTABLISHED_GAIN' for v in ('7.5','8.5','9.5','10.5')},
}

class QualityGateError(ValueError):
    pass


def _digest(path:str|Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def locked_evidence(path:str|Path) -> dict:
    if _digest(path) != EVIDENCE_SHA256:
        raise QualityGateError('Acceptance evidence SHA-256 mismatch: FAIL CLOSED')
    evidence = json.loads(Path(path).read_text(encoding='utf-8'))
    if (evidence.get('status')!='RETROSPECTIVE_REUSED_2026_27_NOT_UNTOUCHED'
            or evidence.get('source',{}).get('sha256')!=HISTORICAL_SHA256
            or evidence.get('coverage',{}).get('target_matches')!=880
            or evidence.get('production_changes') is not False):
        raise QualityGateError('Evidence identity or provenance mismatch')
    decisions = {}
    for c in evidence.get('comparisons', []):
        key = (c.get('market'),c.get('candidate'),c.get('reference'))
        if key in decisions: raise QualityGateError('Duplicate evidence comparison')
        decisions[key] = c.get('decision')
    if decisions != EXPECTED_DECISIONS:
        raise QualityGateError('Evidence decisions missing, changed or unreviewed')
    return evidence


def _prob(v:Any) -> float:
    if isinstance(v,bool): raise QualityGateError('Invalid boolean probability')
    try: f=float(v)
    except (ValueError,TypeError): raise QualityGateError('Non-numeric probability') from None
    if not math.isfinite(f) or f<0 or f>1:
        raise QualityGateError('Probability outside [0,1]')
    return f


def _market_prob(markets:dict, key:str) -> float:
    if not isinstance(markets,dict) or key not in markets:
        raise QualityGateError('Expected model probability absent')
    return _prob(markets[key])


def _check_1x2(markets:dict) -> None:
    p = [_market_prob(markets,k) for k in ('MS1','MSX','MS2')]
    if abs(sum(p)-1)>1e-7: raise QualityGateError('1X2 probabilities not normalized')
    for a,b,c in [('1X','MS1','MSX'),('X2','MSX','MS2'),('12','MS1','MS2')]:
        if abs(_market_prob(markets,a)-_market_prob(markets,b)-_market_prob(markets,c))>1e-7:
            raise QualityGateError('Double-chance / 1X2 mismatch')
    for name,val in markets.items():
        p=_prob(val)
        if name.startswith('OVER_'):
            opposite='UNDER_'+name.removeprefix('OVER_')
            if opposite in markets and abs(p+_prob(markets[opposite])-1)>1e-7:
                raise QualityGateError('Over/under complement mismatch')
    if 'BTTS_YES' in markets and abs(_prob(markets['BTTS_YES'])+_prob(markets['BTTS_NO'])-1)>1e-7:
        raise QualityGateError('BTTS complement mismatch')


def _row(market:str,status:str,probability:float|None,origin:str,
         reason:str,reference_n:int|None=None,evidence_id:str|None=None) -> dict:
    if status not in STATUSES: raise QualityGateError('Unrecognized quality status')
    if probability is not None: probability=_prob(probability)
    return {'market':market,'status':status,'probability':probability,
            'probability_type':origin,'reference_sample':reference_n,
            'evidence_key':evidence_id,'can_recommend':False,'calibrated':False,
            'reason':reason}


def _baselines(rows:list[dict],league:str,target_date:str,field:str,thresholds:tuple[float,...],
               validity_field:str) -> tuple[dict[float,float],int]:
    past = [r for r in rows if r.get('league')==league and r.get('match_date','')<target_date
            and r.get(validity_field) is True]
    if len(past)<MIN_BASELINE: return {},len(past)
    counts=[]
    for r in past:
        if field=='_half_total':
            v=int(r['half_time_home_goals'])+int(r['half_time_away_goals'])
        elif field=='_corners_total':
            v=int(r['home_corners'])+int(r['away_corners'])
        else: raise QualityGateError('Unsupported reference field')
        if v<0: raise QualityGateError('Negative reference count')
        counts.append(v)
    return {t:(sum(x>t for x in counts)+1)/(len(counts)+2) for t in thresholds},len(counts)


def build_quality_report(analysis:dict,rows:list[dict],history_meta:dict,evidence:dict) -> dict:
    """Offline quality labeling. All selections disabled; evidence immutable and historical."""
    if analysis.get('fixture_verified') is not False or analysis.get('is_real_match_forecast') is not False:
        raise QualityGateError('Not a live fixture reporter: refuse verified/published predictions')
    fixture=analysis.get('fixture',{});provenance=analysis.get('provenance',{})
    day=fixture.get('target_date','');league=fixture.get('league','')
    try:
        if date.fromisoformat(day).isoformat()!=day: raise ValueError
    except (ValueError,TypeError): raise QualityGateError('Invalid target date') from None
    if not league or provenance.get('cutoff_exclusive_date')!=day:
        raise QualityGateError('Missing/external data cutoff')
    if not isinstance(history_meta,dict) or provenance.get('sha256')!=history_meta.get('sha256'):
        raise QualityGateError('Analysis source and history provenance mismatch')
    if not isinstance(evidence,dict) or evidence.get('coverage',{}).get('target_matches')!=880:
        raise QualityGateError('Unverified acceptance evidence')
    subset=[r for r in rows if r.get('league')==league and r.get('match_date','')<day]
    if len(subset)!=provenance.get('historical_games'):
        raise QualityGateError('Historical count/cutoff mismatch')
    for season,key in [(fixture.get('season'),'current_season_games'),(fixture.get('previous_season'),'previous_season_games')]:
        if sum(r.get('season')==season for r in subset)!=provenance.get(key):
            raise QualityGateError('Season/cutoff mismatch')
    out={'version':VERSION,'scope':'OFFLINE_QUALITY_AUDIT_NO_REAL_FIXTURE',
         'fixture_verified':False,'is_real_match_forecast':False,'odds_or_EV':None,
         'recommendations':[],'best_pick':None,'high_probability_alert':None,
         'fixture':fixture,'provenance':provenance,
         'evidence':{'source':'2026-11-01 locked retrospective comparison','sha256':EVIDENCE_SHA256,
                     'independent_forward_validation':False,'target_matches':880},
         'model_coverage':{}, 'markets':[],'experimental_audit':[],
         'omitted':[], 'not_implemented':['fixture verification','first-XI/roster','xG alternative',
               'Dixon-Coles','Elo','odds/EV','market-driven selections','25-match pilot','real-match ledger']}
    models=analysis.get('model_outputs',{})
    # A numerical value might exist without being well tested. Never promote it.
    for model,model_status in (('C2','KANONIK_HESAPLANDI_AMA_DOGRULANMADI'),
                               ('C3','DENEYSEL_RETROSPEKTIF_SINYAL')):
        m=models.get(model)
        if m is None:
            out['model_coverage'][model]='VERI_YETERSIZ'
            if model=='C2':
                for market in ('FT_MS1','FT_MSX','FT_MS2','FT_1X','FT_X2','FT_12',
                               'FT_BTTS_YES','FT_BTTS_NO','FT_OVER_0.5','FT_OVER_1.5',
                               'FT_OVER_2.5','FT_OVER_3.5','FT_OVER_4.5','FT_CORRECT_SCORE'):
                    out['markets'].append(_row(market,'VERI_YETERSIZ',None,'NONE','C2 model unavailable'))
            continue
        try:
            p=m['goals']['markets'];_check_1x2(p)
            if m['goals'].get('truncation_tail',0)>1e-8: raise QualityGateError('Unnormalized score mass')
            for key in ('lambda_home','lambda_away'):
                v=float(m['details'][key])
                if not math.isfinite(v) or not .05<=v<=5: raise QualityGateError('Unsafe goal expectation')
        except (KeyError,TypeError,ValueError,QualityGateError) as ex:
            if model=='C2':
                out['model_coverage'][model]='KARANTINA'
                out['markets'].append(_row('FT_ALL','KARANTINA',None,'NONE',f'Invalid C2 score distribution: {ex}'))
            else:
                out['model_coverage'][model]='KARANTINA'
                out['experimental_audit'].append(_row('FT_C3','KARANTINA',None,'NONE',str(ex)))
            continue
        out['model_coverage'][model]=model_status
        destination=out['markets'] if model=='C2' else out['experimental_audit']
        for label,key in [('FT_MS1','MS1'),('FT_MSX','MSX'),('FT_MS2','MS2'),
                          ('FT_1X','1X'),('FT_X2','X2'),('FT_12','12'),
                          ('FT_BTTS_YES','BTTS_YES'),('FT_BTTS_NO','BTTS_NO')]:
            destination.append(_row(label,model_status,_market_prob(p,key),f'{model}_POISSON',
                  'Calculated not calibrated; no selection',evidence_id='FT_1X2 C2/C1' if model=='C2' else 'FT_1X2 C3/C1'))
        for v in ('0.5','1.5','2.5','3.5','4.5'):
            for name in ('OVER','UNDER'):
                key=f'{name}_{v}'
                destination.append(_row(f'FT_{key}',model_status,_market_prob(p,key),f'{model}_POISSON',
                        'No sufficient independent outcome validation for this line'))
        scores=m['goals'].get('correct_scores',[])
        for ix,s in enumerate(scores):
            destination.append(_row(f'FT_CORRECT_SCORE_{ix+1}_{s["score"]}',model_status,
                s['probability'],f'{model}_POISSON','Most likely score is not a guaranteed outcome or recommendation'))
    other=analysis.get('other_markets',{})
    half=other.get('first_half',{})
    half_ok=half.get('status')=='EXPERIMENTAL_NOT_VALIDATED' and isinstance(half.get('estimate'),dict)
    if half_ok:
        try:
            hp=half['estimate']['markets'];_check_1x2(hp)
            for name in ('MS1','MSX','MS2'):
                out['markets'].append(_row('HALF_'+name,'DENEYSEL_RETROSPEKTIF_SINYAL',
                    _market_prob(hp,name),'RIDGE_HALF_POISSON',
                    '649 retrospectively matched; no untouched forward confirmation',649,'HALF_1X2 RIDGE_HALF/LEAGUE'))
        except (KeyError,TypeError,QualityGateError) as ex:
            out['markets'].append(_row('HALF_1X2','KARANTINA',None,'NONE',f'Invalid halftime distribution: {ex}'))
            half_ok=False
    else:
        out['markets'].append(_row('HALF_1X2','VERI_YETERSIZ',None,'NONE',str(half.get('status','HALF_DATA_MISSING'))))
    h_bases,n_h=_baselines(rows,league,day,'_half_total',(.5,1.5,2.5),'_ht_usable')
    for line in (.5,1.5,2.5):
        for direction in ('OVER','UNDER'):
            market=f'HALF_{direction}_{line:g}'
            if line in h_bases:
                value=h_bases[line] if direction=='OVER' else 1-h_bases[line]
                out['markets'].append(_row(market,'LIG_REFERANSI_TEK_BASINA',value,'LEAGUE_HISTORICAL_FREQUENCY_LAPLACE',
                       'Team half-goal ridge did not outperform league reference; not a team-specific prediction',n_h,
                       f'HALF_OVER_{line:g} RIDGE_HALF/LEAGUE'))
            else:
                out['markets'].append(_row(market,'VERI_YETERSIZ',None,'NONE',
                                          f'Only {n_h} usable historical half-time matches'))
    out['omitted'].extend(['HALF_BTTS','HALF_CORRECT_SCORE'])
    c_bases,n_c=_baselines(rows,league,day,'_corners_total',(7.5,8.5,9.5,10.5),'_corner_usable')
    for line in (7.5,8.5,9.5,10.5):
        for direction in ('OVER','UNDER'):
            market=f'CORN_{direction}_{line:g}'
            if line in c_bases:
                value=c_bases[line] if direction=='OVER' else 1-c_bases[line]
                out['markets'].append(_row(market,'LIG_REFERANSI_TEK_BASINA',value,
                       'LEAGUE_HISTORICAL_FREQUENCY_LAPLACE',
                       'Ridge corners did not outperform league reference; not team-specific',n_c,
                       f'CORN_OVER_{line:g} RIDGE_CORNERS/LEAGUE'))
            else:
                out['markets'].append(_row(market,'VERI_YETERSIZ',None,'NONE',
                                          f'Only {n_c} usable historical corner matches'))
    out['omitted'].extend(['HOME_TEAM_CORNERS','AWAY_TEAM_CORNERS','MORE_CORNERS_TEAM','FIRST_HALF_CORNERS_EXCLUDED'])
    return out


def render_markdown(report:dict) -> str:
    if report.get('scope')!='OFFLINE_QUALITY_AUDIT_NO_REAL_FIXTURE':
        raise QualityGateError('This renderer only accepts offline quality audits')
    lines=['# Futbol Makinası 2.6.3 — Offline pazar kalite denetimi',
           '', '**Bu bir maç tahmini veya bahis önerisi değildir.** Resmî fikstür ve ilk 11 doğrulanmadı.',
           'Geçmiş kabul verileri 2026/27 döneminde daha önce incelendi; bağımsız ileri test yok.',
           '', '## Matematiksel hesap ile tahmin güvenilirliği farklıdır',
           '', '| Pazar | Kaynak | Olasılık | Kanıt sınıfı | Önerilebilir mi? |',
           '|---|---|---:|---|---|']
    for m in report['markets']:
        p='—' if m['probability'] is None else f"{100*m['probability']:.1f}%"
        lines.append(f"| {m['market']} | {m['probability_type']} | {p} | {m['status']} | HAYIR |")
    lines.extend(['','## Deneysel alternatif — ayrı araştırma kaydı',
         'C3 alternatiflerinin aşağıdaki sayıları doğrulanmış ana model veya öneri değildir.'])
    for m in report['experimental_audit'][:6]:
        p='—' if m['probability'] is None else f"{100*m['probability']:.1f}%"
        lines.append(f"- {m['market']}: {p} — {m['status']}")
    lines += ['', '## Uygulama sınırları',
              '- En yüksek olasılık ve yüksek güven eşanlamlı değildir.',
              '- Lig frekansları takımın o maça özgü olasılığı değildir.',
              '- Otomatik en olası seçim, yüksek olasılık filtresi, oran/EV, pilot ve kayıt **kapalıdır**.',
              '- Eksik ilk yarı ve korner bilgisi sıfır olarak doldurulmaz.',
              '- İlk yarı korner pazarı 2.6.3 kapsamında değildir.',
              '- Geçmişte umut verici görünen C3 ve ilk yarı MS henüz terfi etmedi.',
              '', '## Bekleyen bağımsız kontroller',
              ', '.join(report['not_implemented']), '']
    return '\n'.join(lines)


def main() -> None:
    from analysis_math_core import load_history
    p=argparse.ArgumentParser(description='OFFLINE report, NEVER live prediction')
    p.add_argument('--history',required=True)
    p.add_argument('--analysis',required=True)
    p.add_argument('--evidence',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--markdown',required=True)
    args=p.parse_args()
    analysis=json.loads(Path(args.analysis).read_text(encoding='utf-8'))
    rows,source=load_history(args.history)
    evidence=locked_evidence(args.evidence)
    out=build_quality_report(analysis,rows,source,evidence)
    Path(args.out).write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    Path(args.markdown).write_text(render_markdown(out),encoding='utf-8')
    print(json.dumps({'status':out['scope'],'market_rows':len(out['markets']),
                      'actual_recommendations':len(out['recommendations'])}))

if __name__=='__main__': main()
