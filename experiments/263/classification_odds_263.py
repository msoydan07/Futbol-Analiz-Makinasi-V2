"""2.6.3 §12–14: read-only A/B/C candidate + verified odds explanation.

No official class, no model promotion, no prediction recording. The caller must
INDEPENDENTLY check the price source: a caller flag alone is not source proof.
"""
from __future__ import annotations
from datetime import datetime, timezone
from math import exp, factorial, isfinite

MARKETS=('MS1','MSX','MS2','1X','X2','12','BTTS_YES','BTTS_NO','OVER_1.5',
         'UNDER_1.5','OVER_2.5','UNDER_2.5','OVER_3.5','UNDER_3.5')
GROUPS={'MS':('MS1','MSX','MS2'),'KG':('BTTS_YES','BTTS_NO'),
        'GOALS_1.5':('OVER_1.5','UNDER_1.5'),
        'GOALS_2.5':('OVER_2.5','UNDER_2.5'),
        'GOALS_3.5':('OVER_3.5','UNDER_3.5')}
GROUP={selection:k for k,values in GROUPS.items() for selection in values}
class DecisionError(ValueError): pass

def numeric(x,low=0.,high=1.):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not isfinite(x) or not low<=x<=high:
        raise DecisionError('INVALID_NUMBER')
    return float(x)

def aware(s):
    try:
        x=datetime.fromisoformat(str(s).replace('Z','+00:00'))
        if x.tzinfo is None:raise ValueError('timezone')
        return x.astimezone(timezone.utc)
    except (ValueError,TypeError) as ex:
        raise DecisionError('INVALID_AWARE_TIME') from ex

def canonical_markets(raw):
    if not isinstance(raw,dict):raise DecisionError('MARKETS_MISSING')
    ms=raw.get('1X2')
    p={}
    for k,alias in (('MS1','H'),('MSX','D'),('MS2','A')):
        p[k]=numeric(raw[k] if k in raw else ms[alias] if isinstance(ms,dict) else None)
    if abs(sum(p.values())-1)>1e-7:raise DecisionError('1X2_NOT_NORMALIZED')
    p.update({'1X':p['MS1']+p['MSX'],'X2':p['MSX']+p['MS2'],'12':p['MS1']+p['MS2']})
    for k in ('1X','X2','12'):
        if k in raw and abs(numeric(raw[k])-p[k])>1e-7:raise DecisionError('DOUBLE_CHANCE_MISMATCH')
    for x,y in (('BTTS_YES','BTTS_NO'),('OVER_1.5','UNDER_1.5'),
                ('OVER_2.5','UNDER_2.5'),('OVER_3.5','UNDER_3.5')):
        if x not in raw and y not in raw:raise DecisionError('MISSING_BINARY_MARKET')
        v=numeric(raw[x] if x in raw else 1-numeric(raw[y]))
        w=numeric(raw[y] if y in raw else 1-v)
        if abs(v+w-1)>1e-7:raise DecisionError('BINARY_MARKET_NOT_NORMALIZED')
        p[x]=v;p[y]=w
    return p

def poisson_market(lh,la):
    lh=numeric(lh,.05,5);la=numeric(la,.05,5)
    a=[exp(-lh)*lh**j/factorial(j) for j in range(26)]
    b=[exp(-la)*la**j/factorial(j) for j in range(26)]
    mass=sum(a)*sum(b)
    if 1-mass>1e-9:raise DecisionError('POISSON_TAIL')
    p={'MS1':0.,'MSX':0.,'MS2':0.,'BTTS_YES':0.,
       'OVER_1.5':0.,'OVER_2.5':0.,'OVER_3.5':0.}
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            w=x*y/mass
            p['MS1' if i>j else 'MSX' if i==j else 'MS2']+=w
            if i>0 and j>0:p['BTTS_YES']+=w
            for z in (1.5,2.5,3.5):
                if i+j>z:p['OVER_'+str(z)]+=w
    p.update({'1X':p['MS1']+p['MSX'],'X2':p['MSX']+p['MS2'],
              '12':p['MS1']+p['MS2'],'BTTS_NO':1-p['BTTS_YES']})
    for z in (1.5,2.5,3.5):p['UNDER_'+str(z)]=1-p['OVER_'+str(z)]
    return p

def stress_low(selection,lh,la):
    return min(poisson_market(lh*x,la*y)[selection]
               for x in (.9,1.,1.1) for y in (.9,1.,1.1))

def odds_evidence(selection,quote,fixture_key,kickoff,now):
    fallback={'status':'PRICE_NOT_VERIFIED','decimal_odds':None,'no_vig':None,'break_even':None,
              'source':None,'market_margin':None}
    if quote is None:return fallback
    if selection not in GROUP:return {**fallback,'status':'DOUBLE_CHANCE_COUNTERMARKET_NOT_COMPARABLE'}
    if not isinstance(quote,dict):raise DecisionError('ODDS_INVALID')
    if quote.get('fixture_key')!=fixture_key:raise DecisionError('WRONG_MATCH_ODDS')
    if quote.get('market_group')!=GROUP[selection]:raise DecisionError('WRONG_MARKET_LINE')
    if quote.get('verification')!='INDEPENDENTLY_CHECKED' or quote.get('stage')!='PREMATCH':
        return {**fallback,'status':'SOURCE_OR_PRICE_NOT_CONFIRMED'}
    if not quote.get('source') or not str(quote.get('source_url','')).startswith('https://'):
        return {**fallback,'status':'ODDS_SOURCE_MISSING'}
    checked=aware(quote.get('checked_at_utc'));current=aware(now);ko=aware(kickoff)
    if not checked<=current<ko:return {**fallback,'status':'ODDS_WRONG_TIME'}
    if (current-checked).total_seconds()>7200:return {**fallback,'status':'ODDS_STALE'}
    v=quote.get('decimal_odds')
    if not isinstance(v,dict) or set(v)!=set(GROUPS[GROUP[selection]]):
        return {**fallback,'status':'NO_COMPLETE_OPPOSITE_PRICES'}
    odds={k:numeric(n,1.000001,1000.) for k,n in v.items()}
    inverse={k:1/x for k,x in odds.items()}
    margin=sum(inverse.values())-1
    if not -.001<=margin<=.5:return {**fallback,'status':'BAD_BOOKMAKER_MARGIN'}
    return {'status':'COMPLETE_PREMATCH_QUOTES_SOURCE_FLAGGED_AS_CHECKED',
            'decimal_odds':odds[selection],'break_even':inverse[selection],
            'no_vig':inverse[selection]/sum(inverse.values()),'source':quote['source'],
            'source_url':quote['source_url'],'checked_at_utc':checked.isoformat(),
            'market_margin':margin,'normalization':'proportional_no_vig'}

def classify(*,model,markets,selection,lambda_home,lambda_away,fixture_key,kickoff,now,
             league,model_level,data_reliability,context_ok,critical_unverified_effect,
             fixture_verified,quote=None):
    p=canonical_markets(markets)
    if selection not in MARKETS:raise DecisionError('SELECTION_NOT_IN_12_1')
    if model_level not in ('TAM','BASIT','YOK') or data_reliability not in ('YUKSEK','ORTA','DUSUK','DOGRULANAMADI'):
        raise DecisionError('BAD_DATA_OR_MODEL_LEVEL')
    if not all(isinstance(v,str) and v for v in (model,fixture_key,league)):
        raise DecisionError('BAD_FIXTURE_IDENTITY')
    if not aware(now)<aware(kickoff):raise DecisionError('NOT_PREMATCH')
    price=odds_evidence(selection,quote,fixture_key,kickoff,now)
    sufficient=bool(context_ok and model_level in ('TAM','BASIT') and
                    data_reliability in ('YUKSEK','ORTA') and not critical_unverified_effect)
    stress=stress_low(selection,lambda_home,lambda_away) if sufficient else None
    A=bool(sufficient and fixture_verified and p[selection]>=.75 and stress>=.70)
    ev=edge=None
    if price['status']=='COMPLETE_PREMATCH_QUOTES_SOURCE_FLAGGED_AS_CHECKED':
        ev=p[selection]*price['decimal_odds']-1
        edge=p[selection]-price['no_vig']
    B=bool(sufficient and fixture_verified and ev is not None and ev>=.05 and edge>=.03)
    if not sufficient or not fixture_verified:category='DEGERLENDIRILEMEDI'
    elif A and B:category='A+B_ADAYI'
    elif A:category='A_ADAYI'
    elif B:category='B_ADAYI'
    elif p[selection]>=.75:category='C_IZLEME'
    else:category='ADAY_YOK'
    return {'schema':'263_abc_and_odds_v1','status':'PRELIMINARY_NO_PRODUCTION_APPROVAL',
            'model':model,'league':league,'fixture_key':fixture_key,
            'selection':selection,'model_probability':p[selection],
            'model_level':model_level,'data_reliability':data_reliability,
            'probability_filter':'GECTI' if A else 'IZLEME' if p[selection]>=.75 else 'ESIK_ALTI',
            'stress_minimum':stress,'stress_method':'both lambdas +/-10pct: heuristic, not a CI',
            'A_condition':A,'B_condition':B,'candidate_class':category,
            'official_class':None,'price':price,'EV':ev,
            'no_vig_edge_percentage_points':edge*100 if edge is not None else None,
            'betting_authorized':False,'pilot_registered':False}

def explain(result):
    s=result['selection'];prob=result['model_probability'];e=result['price']
    line=f"{result['model']} {s}: %{prob*100:.1f}, {result['candidate_class']} (RESMİ ONAY YOK)."
    if result['EV'] is None:return line+" Oran/EV: HESAPLANAMADI ["+e['status']+"]."
    return (line+f" Oran {e['decimal_odds']:.2f} ({e['source']}); "
            f"başa baş %{e['break_even']*100:.1f}; marjsız piyasa %{e['no_vig']*100:.1f}; "
            f"avantaj {result['no_vig_edge_percentage_points']:+.1f} puan; "
            f"EV %{result['EV']*100:+.1f}.")
