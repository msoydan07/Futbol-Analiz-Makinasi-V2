"""2.6.3 sections 12-14: deterministic, non-promoting, offline decision preflight.

This is NOT a model, odds lookup, actual selection, or pilot. It distinguishes:
 - highest calculated probability (descriptive)
 - section 12.1 >=75% WATCH list (never PASS without real-world validation)
 - section 12.2 A/B/C status (not evaluated offline)
 - section 12.4 same-league/season base rate (not a model probability)
 - section 13 EV (unavailable without independently verified prematch prices).
No prospective or retrospective model performance tests are run here.
"""
from __future__ import annotations
from datetime import date
import math

VERSION = '263_decision_preflight_nonpromoting_v1'
MIN_PROB = 0.75    # Canonical template 12.1 fixed experimental threshold
STRESS_FLOOR = 0.70
SIDE = ('MS1','MSX','MS2')
DOUBLE_CHANCE = ('1X','X2','12')
GENERAL = ('BTTS_YES','BTTS_NO','OVER_1.5','UNDER_1.5',
           'OVER_2.5','UNDER_2.5','OVER_3.5','UNDER_3.5')
WATCH_MARKETS = SIDE + DOUBLE_CHANCE + GENERAL

class DecisionPreflightError(ValueError):
    pass

def _check_probability(p, name):
    if (isinstance(p,bool) or not isinstance(p,(float,int)) or
            not math.isfinite(p) or not 0 <= p <= 1):
        raise DecisionPreflightError('invalid probability: '+name)
    return float(p)

def _reference_rate(rows, league, season, day, market):
    """Observed same-season base rate, strictly before target date, never a forecast."""
    past=[r for r in rows if r['league']==league and r['season']==season
          and r['match_date']<day]
    wins=0
    for r in past:
        try:
            h=int(r['home_goals']);a=int(r['away_goals'])
        except (ValueError,KeyError,TypeError) as exc:
            raise DecisionPreflightError('invalid mandatory historical score') from exc
        if h<0 or a<0:
            raise DecisionPreflightError('negative historical score')
        if market=='MS1':wins+=h>a
        elif market=='MSX':wins+=h==a
        elif market=='MS2':wins+=h<a
        elif market=='1X':wins+=h>=a
        elif market=='X2':wins+=h<=a
        elif market=='12':wins+=h!=a
        elif market=='BTTS_YES':wins+=h>0 and a>0
        elif market=='BTTS_NO':wins+=not(h>0 and a>0)
        elif market.startswith(('OVER_','UNDER_')):
            direction, line=market.split('_')
            boundary=float(line)
            wins+=(h+a>boundary) if direction=='OVER' else (h+a<boundary)
        else:
            raise DecisionPreflightError('not a supported reference market: '+market)
    return {'source':'FROZEN_RESULTS_SAME_LEAGUE_SEASON_BEFORE_TARGET',
            'sample_size':len(past),'observed_probability':wins/len(past) if past else None,
            'prediction_model_input':False,'changes_filter':False}

def _stress_range(model, market):
    sensitivity=model.get('sensitivity') or {}
    if sensitivity.get('status')!='HEURISTIC_NOT_CONFIDENCE_INTERVAL' or sensitivity.get('input_variation')!=.1:
        return None
    ranges=sensitivity.get('ranges') or {}
    invert={'BTTS_NO':'BTTS_YES','UNDER_2.5':'OVER_2.5'}
    key=invert.get(market,market)
    v=ranges.get(key)
    if not isinstance(v,list) or len(v)!=2:return None
    low,high=_check_probability(v[0],key+' stress lower'),_check_probability(v[1],key+' stress upper')
    if low>high:raise DecisionPreflightError('invalid stress interval')
    return [1-high,1-low] if market in invert else [low,high]

def evaluate_case(entry:dict, rows:list[dict]) -> dict:
    """Read-only 12/13/14 decision readiness, never calls Models B/C2/C3."""
    ident=entry['identity'];day=ident['target_date'];date.fromisoformat(day)
    if (entry['analysis']['provenance']['cutoff_exclusive_date']!=day or
            entry['data_context']['cutoff_exclusive']!=day):
        raise DecisionPreflightError('historical cutoff mismatch')
    if entry['analysis'].get('fixture_verified') is not False or entry['analysis'].get('is_real_match_forecast') is not False:
        raise DecisionPreflightError('unexpected live status in offline preflight')
    if entry['quality'].get('recommendations') or entry['quality'].get('best_pick') is not None:
        raise DecisionPreflightError('quality layer already recommended a bet')
    model=entry['analysis']['model_outputs'].get('C2')
    out={'version':VERSION,'status':'OFFLINE_DECISION_PREFLIGHT_ONLY',
         'league':ident['league'],'season':ident['season'],'cutoff_exclusive':day,
         'canonical_model':'C2' if model else None,
         'model_status':'CALCULATED_NOT_FORWARD_VALIDATED' if model else 'INSUFFICIENT_CONTEXT',
         'main_side_descriptive':None,'main_general_descriptive':None,
         'double_chance_descriptive':[], 'high_probability_filter':[],
         'passed_filter':[], 'A_B_C_official_candidates':[],
         'value_selections':[], 'odds_or_EV':None,
         'value_status':'NOT_EVALUATED_NO_VERIFIED_PREMATCH_ODDS',
         'A_B_C_status':'DEGERLENDIRILEMEDI_OFFLINE_GUVEN_KANITI_YOK',
         'lineups_not_published_blocks_math':False,
         'recommendation_eligible':False,'pilot_record_eligible':False,
         'independent_forward_validation':False,
         'reference_rates_change_probability':False}
    if model is None:
        out['filter_status']='DEGERLENDIRILEMEDI_C2_YOK'
        out['reason']='Existing Model B and C3 cannot silently replace 2.6.3 C2; no A/B/C evaluation.'
        return out
    p=model['goals']['markets']
    if abs(sum(_check_probability(p[k],k) for k in SIDE)-1)>1e-7:
        raise DecisionPreflightError('C2 1X2 not normalized')
    for market, formula in (('1X',p['MS1']+p['MSX']),('X2',p['MSX']+p['MS2']),('12',p['MS1']+p['MS2'])):
        if abs(_check_probability(p[market],market)-formula)>1e-7:
            raise DecisionPreflightError('C2 double chance inconsistent')
    for m,n in [('BTTS_YES','BTTS_NO'),('OVER_2.5','UNDER_2.5')]:
        if abs(_check_probability(p[m],m)+_check_probability(p[n],n)-1)>1e-7:
            raise DecisionPreflightError('C2 complementary markets inconsistent')
    choices=[]
    for k in WATCH_MARKETS:
        prob=_check_probability(p[k],k)
        baseline=_reference_rate(rows,ident['league'],ident['season'],day,k)
        stress=_stress_range(model,k)
        if prob>=MIN_PROB:
            # Even a robust probability remains unapproved without independent
            # forward model reliability and real-match data quality verification.
            state='IZLEME'
            reason=('No independent forward model calibration or live data quality confirmation. '
                    '±10% lambda stress is not a confidence interval.')
        else:
            state='ELENDI_ESIK_ALTI'
            reason='Below fixed 75% experimental high-probability screen; not a model quality verdict.'
        choices.append({'market':k,'p_model':prob,'probability_source':'C2_CANONICAL_UNCALIBRATED',
                        'base_rate':baseline,'lambda_stress_range':stress,
                        'lambda_stress_floor_passed':stress is not None and stress[0]>=STRESS_FLOOR,
                        'filter_state':state,'reason':reason,
                        'A_B_C':'DEGERLENDIRILEMEDI','recommended':False})
    by_market={r['market']:r for r in choices}
    side=sorted((by_market[k] for k in SIDE),key=lambda r:(-r['p_model'],r['market']))
    general=sorted((by_market[k] for k in GENERAL),key=lambda r:(-r['p_model'],r['market']))
    doubles=sorted((by_market[k] for k in DOUBLE_CHANCE),key=lambda r:(-r['p_model'],r['market']))
    out['main_side_descriptive']={'market':side[0]['market'],'probability':side[0]['p_model'],
                                  'second_market':side[1]['market'],
                                  'percentage_point_gap':100*(side[0]['p_model']-side[1]['p_model']),
                                  'base_rate':side[0]['base_rate'],'approved':False}
    out['main_general_descriptive']={'market':general[0]['market'],
                                     'probability':general[0]['p_model'],
                                     'base_rate':general[0]['base_rate'],'approved':False}
    out['double_chance_descriptive']=[{'market':r['market'],'probability':r['p_model']} for r in doubles]
    out['high_probability_filter']=choices
    out['filter_status']='IZLEME_VAR_ONAY_YOK' if any(r['filter_state']=='IZLEME' for r in choices) else 'ESIK_GECEN_ADAY_YOK'
    out['reason']='Descriptive math only. Real fixture, verified lineups/risks, model reliability and pre-match prices are not certified.'
    out['excluded_markets']=['OVER_0.5','UNDER_0.5','OVER_4.5','UNDER_4.5',
                              'HALF_1X2_UNVALIDATED','HALF_GOALS_UNVALIDATED','CORNERS_UNVALIDATED',
                              'FIRST_HALF_CORNERS_REMOVED']
    return out

def evaluate_bundle(bundle:dict, rows:list[dict]) -> list[dict]:
    if bundle.get('scope')!='HYPOTHETICAL_OFFLINE_AUDIT' or bundle.get('real_fixture_verified') is not False:
        raise DecisionPreflightError('offline-only bundle required')
    if bundle.get('recommendations') or bundle.get('odds_EV') is not None:
        raise DecisionPreflightError('already recommended/EV bundle')
    return [evaluate_case(entry,rows) for entry in bundle['cases']]

def render_markdown(results:list[dict]) -> str:
    lines=['# 2.6.3 §12–14 — Güvenilir seçim hazırlığı (OFFLINE)',
           '', '**Bu çıktı bahis önerisi, gerçek maç tahmini, A/B/C onayı veya pilot kaydı değildir.**',
           'En olası sonuç ile A sınıfı, pozitif EV ve model güvenilirliği farklı kavramlardır.',
           'Şablonun pilot %75 ve ±%10 stres eşiği değiştirilmedi; bağımsız ileri kabul yok.',
           '']
    for i,part in enumerate(results,1):
        lines += [f'## {i}. {part["league"]} — {part["cutoff_exclusive"]}',
                  f'Kanonik model: {part["model_status"]}; filtre: {part["filter_status"]}',
                  f'A/B/C: {part["A_B_C_status"]}; value: {part["value_status"]}']
        if part['main_side_descriptive']:
            s=part['main_side_descriptive'];g=part['main_general_descriptive']
            lines += [f'MS ana sonuç (yalnız matematik): {s["market"]} %{100*s["probability"]:.1f}; en yakın alternatif {s["second_market"]}, fark {s["percentage_point_gap"]:.1f} puan.',
                      f'Genel pazar (yalnız matematik): {g["market"]} %{100*g["probability"]:.1f}.',
                      'Çifte şans ayrı tutulur. İY ve korner adaylarına doğrulanmamış model olasılığı verilmez.',
                      '| Pazar | Model p | 12.1 | Aynı lig/sezon taban çizgisi | ±%10 alt sınır |',
                      '|---|---:|---|---:|---:|']
            for c in part['high_probability_filter']:
                base=c['base_rate'];base_text=f'%{100*base["observed_probability"]:.1f} (n={base["sample_size"]})' if base['observed_probability'] is not None else 'DOĞRULANAMADI'
                stress=c['lambda_stress_range']; stress_text=f'%{100*stress[0]:.1f}' if stress else 'HESAPLANMADI'
                lines.append(f'| {c["market"]} | %{100*c["p_model"]:.1f} | {c["filter_state"]} | {base_text} | {stress_text} |')
        else:
            lines.append('C2 için örneklem yetersiz. B/C3 olasılıkları kanonik seçim yerine geçirilmedi.')
        lines.extend(['','**GEÇTİ / A / B / A+B / resmî C: YOK.** Oran/EV hesaplanmadı; pilot kaydı oluşturulmadı.',''])
    return '\n'.join(lines)
