"""2.6.3 operational OFFLINE evidence report built on frozen existing models.

Purpose: produce an actual mathematical output from the existing C1 (Model B),
canonical C2, experimental C3, market evidence, historical context and all 17
section states in one callable chain. Does NOT certify a live match, generate
bets, execute a pilot, collect odds, or edit production. No maths parameters
are learned or adjusted from this report's target outcomes.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from datetime import date

from analysis_math_core import load_history, score_market, sensitivity
from experimental_poisson_baseline import estimate as frozen_model_b
from integrated_offline_report import build_offline_bundle, render_bundle_markdown
from quality_gate_263 import HISTORICAL_SHA256, locked_evidence
from mackolik_identity_gate_263 import (
    _validate_identity_source, _reviewed, resolve_requested_match,
)

VERSION='263_operational_offline_comparison_v1'

class OperationalError(ValueError):
    pass


def _safe_probability(p: float) -> float:
    if isinstance(p,bool) or not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<=p<=1:
        raise OperationalError('Nonfinite or out-of-range probability')
    return float(p)


def _reference_model_b(rows: list[dict], case: dict) -> dict:
    """Existing unmodified C1 window=20, shrink=5; no C2 parameter substitution."""
    p=frozen_model_b(rows,case['league'],case['home_id'],case['away_id'],case['target_date'])
    if p is None:
        return {'status':'NOT_AVAILABLE_INSUFFICIENT_HISTORY', 'role':'EXISTING_C1_COMPARATOR_NOT_263_CANONICAL',
                'recommended':False, 'probabilities':None}
    lh,la=p['lambda_home'],p['lambda_away']
    if p['matrix_mass']<.999 or p['matrix_mass']>1.000001 or p['tail_mass']<-.000001:
        raise OperationalError('Model B score-matrix tail outside permitted bound')
    z=p['p_home']+p['p_draw']+p['p_away']
    if z<=0:raise OperationalError('Model B empty 1X2 mass')
    original={'MS1':_safe_probability(p['p_home']/z),'MSX':_safe_probability(p['p_draw']/z),
              'MS2':_safe_probability(p['p_away']/z),
              'OVER_2.5':_safe_probability(p['p_over25']/p['matrix_mass']),
              'BTTS_YES':_safe_probability(p['p_btts']/p['matrix_mass'])}
    if abs(sum(original[k] for k in ('MS1','MSX','MS2'))-1)>1e-8:
        raise OperationalError('Model B probabilities inconsistent')
    # Same lambdas + score_matrix from C2 library for descriptive extra lines;
    # not a retrospective validation of these extra C1 markets.
    full=score_market(lh,la)
    for k in original:
        if abs(full['markets'][k]-original[k])>max(0.000002,2*p['tail_mass']+0.0000001):
            raise OperationalError('Frozen Model B vs full Poisson score-matrix mismatch')
    return {'status':'CALCULATED_EXISTING_B_NOT_263_CANONICAL',
            'role':'EXISTING_C1_COMPARATOR_NOT_263_CANONICAL',
            'method':p['method'],'lambda_home':lh,'lambda_away':la,
            'parameters':{'window':20,'shrink':5},
            'samples':{'league':p['league_samples'],'home_venue':p['home_samples'],'away_venue':p['away_samples']},
            'probabilities':original,'top_scores':full['correct_scores'],
            'extra_markets_descriptive_only':{k:full['markets'][k] for k in ('OVER_1.5','OVER_3.5','UNDER_2.5','BTTS_NO','1X','X2','12')},
            'sensitivity':sensitivity(lh,la),
            'source_cutoff_exclusive':p['data_cutoff_exclusive'],
            'calibration':'HISTORICAL_COMPARISON_ONLY_NOT_FORWARD_VALIDATED',
            'recommended':False, 'model_promoted':False}


def _scenarios(rows:list[dict], case:dict) -> dict:
    """Descriptive recent form, not score multiplier or causal team-strength claim."""
    league=case['league'];day=case['target_date'];season=case['season']
    records=[r for r in rows if r['league']==league and r['season']==season and r['match_date']<day]
    answer={}
    for role,tid in [('home',case['home_id']),('away',case['away_id'])]:
        played=[r for r in records if r['home_id']==tid or r['away_id']==tid]
        played=sorted(played,key=lambda r:(r['match_date'],r['fixture_id']))[-5:]
        goals_for=sum(int(r['home_goals'] if r['home_id']==tid else r['away_goals']) for r in played)
        goals_against=sum(int(r['away_goals'] if r['home_id']==tid else r['home_goals']) for r in played)
        w=sum(int(r['home_goals'] if r['home_id']==tid else r['away_goals'])>
              int(r['away_goals'] if r['home_id']==tid else r['home_goals']) for r in played)
        d=sum(int(r['home_goals'])==int(r['away_goals']) for r in played)
        answer[role]={'last_5_current_season_matches':len(played),'wins':w,'draws':d,
                      'losses':len(played)-w-d,'goals_for':goals_for,'goals_against':goals_against,
                      'source':'RESULTS_CSV_DESCRIPTIVE_NOT_ADJUSTED_FOR_OPPONENT',
                      'used_as_lambda_multiplier':False}
    return answer


def _ranking(c2:dict, model_b:dict) -> dict:
    """Mathematical highest-probability fact, not A/B/C selection or recommendation."""
    if c2:
        source='C2_CANONICAL'
        p=c2['goals']['markets']
        keys=['MS1','MSX','MS2','OVER_2.5','UNDER_2.5','BTTS_YES','BTTS_NO','1X','X2','12']
    elif model_b['probabilities'] is not None:
        source='C1_EXPLORATORY_ONLY_C2_MISSING'
        p={**model_b['probabilities'],**model_b['extra_markets_descriptive_only']}
        keys=['MS1','MSX','MS2','OVER_2.5','UNDER_2.5','BTTS_YES','BTTS_NO','1X','X2','12']
    else:
        return {'status':'NOT_CALCULABLE','model':None,'rows':[],'recommended':False}
    data=sorted(({'market':k,'probability':_safe_probability(p[k])} for k in keys),
                key=lambda item:(-item['probability'],item['market']))
    return {'status':'DESCRIPTIVE_MAX_PROBABILITY_NOT_RECOMMENDATION',
            'model':source,'rows':data[:5],
            'note':'Double chance and correlated markets are displayed for descriptive comparison only. No A/B/C trust level or EV.',
            'recommended':False}


def build_operational_offline_bundle(rows:list[dict],source:dict,evidence:dict,
                                      cases:list[dict],*,require_locked_source=True,
                                      identity_audit:dict|None=None) -> dict:
    """Frozen 2.6.3 math/explanation/report path; never certify a real fixture."""
    if require_locked_source and source.get('sha256')!=HISTORICAL_SHA256:
        raise OperationalError('Historical snapshot changed; refuse to run')
    base=build_offline_bundle(rows,source,evidence,cases,require_locked_source=require_locked_source,identity_audit=identity_audit)
    for entry in base['cases']:
        case=entry['identity'];c2=entry['analysis']['model_outputs'].get('C2')
        b=_reference_model_b(rows,case)
        entry['model_b_existing']=b
        entry['model_arbitration']={
            'canonical_primary':'C2' if c2 else None,
            'canonical_status':'CALCULATED_NOT_FORWARD_VALIDATED' if c2 else 'YOK_INSUFFICIENT_CONTEXT',
            'existing_b_comparison':'AVAILABLE' if b['probabilities'] else 'NOT_AVAILABLE',
            'c3_status':'SEPARATE_EXPERIMENT_ONLY',
            'automatic_fallback_promoted':False,
            'reason':'Template 6.2 cannot be bypassed merely to make predictions appear complete',
        }
        entry['descriptive_form']=_scenarios(rows,case)
        entry['probability_ranking']=_ranking(c2,b)
        entry['external_factors']={'xg':'SEPARATE_JOIN_NOT_VERIFIED',
                                  'elo':'AUXILIARY_NOT_APPLIED','lineups':'NOT_CHECKED',
                                  'injuries_suspensions':'NOT_CHECKED',
                                  'tactics':'NOT_CHECKED',
                                  'weather':'NOT_CHECKED',
                                  'verified_external_lambda_adjustments':0}
        if b['probabilities'] and b['source_cutoff_exclusive']!=case['target_date']:
            raise OperationalError('Model B data cutoff mismatch')
        if entry['quality']['recommendations'] or entry['probability_ranking']['recommended']:
            raise OperationalError('Offline recommendation safety violation')
    base.update({'operational_version':VERSION,
                 'primary_model_is_experimentally_evaluated_not_validated':True,
                 'does_not_claim_live_readiness':True,
                 'model_b_parameters_modified':False,
                 'c2_parameters_modified':False,
                 'odds_EV':None,'recommendations':[], 'production_changed':False})
    return base


def named_cases(index_path:str|Path,alias_path:str|Path,requests:list[dict]) -> list[dict]:
    """Names are user-provided; identity matching alone NEVER verifies the fixture."""
    registry=json.loads(Path(index_path).read_text(encoding='utf-8'))
    _validate_identity_source(registry)
    reviewed=_reviewed(Path(alias_path),registry)
    cases=[]
    if not isinstance(requests,list) or not 1<=len(requests)<=20:
        raise OperationalError('Exactly 1..20 user-supplied offline fixtures required')
    for req in requests:
        if not isinstance(req,dict) or not {'home','away','target_date'} <= set(req):
            raise OperationalError('Invalid named case')
        if not isinstance(req['home'],str) or not isinstance(req['away'],str) or not req['home'].strip() or not req['away'].strip():
            raise OperationalError('Missing named team')
        try:
            target=date.fromisoformat(req['target_date'])
            if target.isoformat()!=req['target_date']:raise ValueError
        except (ValueError,TypeError):raise OperationalError('Invalid target date') from None
        season=req.get('season','2026-2027')
        if season!='2026-2027':raise OperationalError('Only fixed snapshot season is supported')
        identity=resolve_requested_match(registry,req['home'],req['away'],req.get('league'),season,reviewed)
        if identity.get('status')!='RESOLVED_IDENTITY':
            raise OperationalError('Identity unresolved: '+str(identity.get('reason')))
        cases.append({'league':identity['league'],'season':season,
                      'previous_season':'2025-2026','target_date':req['target_date'],
                      'home_id':identity['home_id'],'away_id':identity['away_id']})
    return cases


def render_operational_markdown(bundle:dict) -> str:
    md=render_bundle_markdown(bundle)
    lines=['# 2.6.3 — ÇALIŞAN MATEMATİK + FUTBOL VERİSİ OFFLINE RAPORU','',
           '**Gerçek maç doğrulaması veya tahmin kaydı değildir.** Kullanıcı maçı söylediğinde resmî kontrol ayrı ve anlık yapılacak.',
           'Bu çalışmada eski C1 (Model B) ile şablona uygun C2 ayrı hesaplandı; C3 ana motor yapılmadı.',
           'Veri kesimi hedef günün **öncesidir**. Yüksek yüzde, doğrulanmış yüksek güven değildir.', '',
           '## Özet — hesaplanan/gösterilen modeller','',
           '| Örnek | Kanonik C2 | Mevcut B karşılaştırması | C3 | İY ve korner |',
           '|---|---|---|---|---|']
    for i,entry in enumerate(bundle['cases'],1):
        s=entry['model_arbitration'];b=entry['model_b_existing']
        c3='Deneysel' if entry['analysis']['model_outputs'].get('C3') else 'Yetersiz'
        other=entry['analysis']['other_markets']
        hc='Hesaplandı / deneysel' if other.get('first_half',{}).get('status')=='EXPERIMENTAL_NOT_VALIDATED' else 'Eksik bağlam'
        lines.append(f'| {i}. {entry["identity"]["league"]} | {s["canonical_status"]} | {b["status"]} | {c3} | {hc} |')
    lines+=['', '## Futbol bağlamı ve en olası sonuçlar — öneri değil','']
    for i,entry in enumerate(bundle['cases'],1):
        case=entry['identity'];b=entry['model_b_existing']; c2=entry['analysis']['model_outputs'].get('C2')
        lines.append(f'### {i}. {case["league"]} — {case["home_id"]} / {case["away_id"]}')
        if c2:
            d=c2['details']; vals=d['team_contexts']
            lines.append(f'C2 kanonik λ: ev **{d["lambda_home"]:.3f}**, deplasman **{d["lambda_away"]:.3f}**; k=5, w=0,5. Cari ev/deplasman maçları: {vals["home_scored"]["n"]}/{vals["away_scored"]["n"]}.')
            sens=c2['sensitivity']
            if sens['status']=='HEURISTIC_NOT_CONFIDENCE_INTERVAL':
                lines.append('±%10 λ duyarlılığı **sezgisel senaryodur**, istatistiksel güven aralığı değildir.')
        else:
            lines.append('**C2: VERİ YETERSİZ.** Şablonun en az dört cari ev/deplasman maçı şartı sağlanmadı; sessiz model değişimi yapılmadı.')
        if b['probabilities']:
            p=b['probabilities']
            lines.append(f'Mevcut B (ayrı): λ {b["lambda_home"]:.3f}/{b["lambda_away"]:.3f}; MS 1/X/2 = **%{100*p["MS1"]:.1f} / %{100*p["MSX"]:.1f} / %{100*p["MS2"]:.1f}**; 2,5 Üst **%{100*p["OVER_2.5"]:.1f}**, KG Var **%{100*p["BTTS_YES"]:.1f}**. Kanonik C2 yerine atanmadı.')
        else:
            lines.append('Mevcut Model B de en az beş ev/deplasman örneği bulamadı; hesap yapılmadı.')
        form=entry['descriptive_form']
        for role in ('home','away'):
            f=form[role]
            lines.append(f'**{("Ev" if role=="home" else "Dep")}:** son {f["last_5_current_season_matches"]} cari sezon maçı = {f["wins"]}G-{f["draws"]}B-{f["losses"]}M, atılan/yenen {f["goals_for"]}/{f["goals_against"]}. **Rakip gücüne göre düzeltilmemiştir.**')
        ranking=entry['probability_ranking']
        if ranking['rows']:
            lines.append('En yüksek **hesaplanmış** olasılıklar ('+ranking['model']+', **öneri değil**): '+', '.join(f'{x["market"]} %{100*x["probability"]:.1f}' for x in ranking['rows'][:3])+'.')
        lines.append('xG ayrı kaynaktan henüz güvenle eşleştirilmedi; Elo, kadro, hava/tempo çarpanı uygulanmadı. İlk 11 henüz yoksa analize engel değildir. Oran/EV ve pilot yok.')
        lines.append('')
    lines+=['---','','## Orijinal kalite ve 17 bölüm uygunluk denetimi','','Bu ek, önceki kanıt sınıflandırmasını değiştirmez.','',md]
    return '\n'.join(lines)


def main(argv=None):
    parser=argparse.ArgumentParser(description='Only hypothetical offline math readiness, not a live fixture prediction')
    parser.add_argument('--history',required=True)
    parser.add_argument('--evidence',required=True)
    parser.add_argument('--index',required=True)
    parser.add_argument('--aliases',required=True)
    parser.add_argument('--named',required=True,help='JSON array of user-supplied named hypothetical cases')
    parser.add_argument('--out',required=True)
    args=parser.parse_args(argv)
    rows,source=load_history(args.history)
    evidence=locked_evidence(args.evidence)
    req=json.loads(Path(args.named).read_text(encoding='utf-8'))
    cases=named_cases(args.index,args.aliases,req)
    bundle=build_operational_offline_bundle(rows,source,evidence,cases)
    path=Path(args.out)
    path.mkdir(parents=True,exist_ok=True)
    (path/'operational_report.json').write_text(json.dumps(bundle,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (path/'operational_report.md').write_text(render_operational_markdown(bundle)+'\n',encoding='utf-8')
    print(json.dumps({'status':'OFFLINE_MATH_COMPLETED','cases':len(bundle['cases']),
                      'not_live_forecast':True,'recommendations':0,'output':str(path)},ensure_ascii=False))

if __name__=='__main__':main()
