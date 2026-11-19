"""Regression checks for xG input without touching frozen M4 or seals."""
import csv
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from m4_xg_support_263 import xg_adjustment,_accepted_past


def sample(n=80):
    score=[];xg=[]
    for i in range(n):
        h='H' if i%2==0 else 'A'
        a='A' if h=='H' else 'H'
        day=f'2026-01-{1+i//28:02d}' # early and old date, chronologically safe
        r=dict(fixture_id=f'id{i}',league='ENG1',match_date=day,
               home_id=h,away_id=a,home_goals='1',away_goals='0')
        score.append(r)
        xg.append(dict(fixture_id=r['fixture_id'],league='ENG1',date=day,
                       home_id=h,away_id=a,home_goals='1',away_goals='0',
                       home_xg='1.4',away_xg='.9',xg_source='Understat',
                       source_status='LEGACY_VERIFIED_2026_11_03'))
    return score,xg


def check():
    scores,xg=sample()
    result=xg_adjustment(scores,xg,'ENG1','H','A','2026-02-15',1.2,1.1)
    assert result['status']=='XG_INCLUDED_IN_M4_RESEARCH_LAMBDA',result
    assert result['used_matches']>0
    assert result['last_used_date']<'2026-02-15'
    # Forecast day and future information must never enter the calculated feature.
    future={**xg[0], 'fixture_id':'FUTURE','date':'2026-02-15',
            'home_xg':'8','away_xg':'8'}
    future_score={**scores[0],'fixture_id':'FUTURE','match_date':'2026-02-15'}
    result2=xg_adjustment(scores+[future_score],xg+[future],'ENG1','H','A','2026-02-15',1.2,1.1)
    assert result['adjusted_lambdas']==result2['adjusted_lambdas']
    assert result2['source_rejected']['future_or_same_day']==1
    # Never confuse opposite home/away identity or different goal scores.
    flipped={**xg[0],'home_id':'A','away_id':'H'}
    assert _accepted_past([flipped],scores,'ENG1','2026-02-15')[1]['identity_date_score_conflict']==1
    # Unchecked candidate source is explicitly excluded, not treated as verified.
    unconfirmed={**xg[0], 'source_status':'KAYNAK_TEKİL_KONTROL_BEKLİYOR'}
    assert _accepted_past([unconfirmed],scores,'ENG1','2026-02-15')[1]['unconfirmed_xg_source']==1
    # Understat xG must not be mixed into non-BIG5 league trained on xgEdge.
    mixed=[{**r,'league':'NED1'} for r in xg]
    accepted=[{**r,'league':'NED1'} for r in scores]
    assert xg_adjustment(accepted,mixed,'NED1','H','A','2026-02-15',1.2,1.1)['status']=='BASELINE_M4_FALLBACK'
    # With no clean prior xG, original lambdas are preserved exactly.
    assert xg_adjustment([],[], 'ENG1','H','A','2026-02-15',1.2,1.1)['adjusted_lambdas']==[1.2,1.1]
    try:
        _accepted_past(xg+[xg[0]],scores,'ENG1','2026-02-15')
    except ValueError as e: assert 'duplicate' in str(e)
    else: raise AssertionError('duplicate xg accepted')
    assert xg_adjustment(scores,xg,'ENG1','H','A','2026-02-15',1.2,1.1,alpha=0)['adjusted_lambdas']==[1.2,1.1]
    print('PASS: 8 groups: baseline, as-of, identity, source, fallback, provider, duplicate, alpha')

if __name__=='__main__':check()
