"""One bundled *software correctness* suite; NOT an out-of-sample performance test."""
import csv
import copy
import math
import tempfile
import unittest
from datetime import date,timedelta
from pathlib import Path

from analysis_math_core import (
    _shrink,_negative_binomial_pmf,_poisson_pmf,_count_lambdas,
    canonical_c2_lambda,load_history,build_analysis,score_market,sensitivity,InvalidHistory
)

FIELDS=('fixture_id','league','season','match_date','home_id','away_id','home_goals','away_goals','result',
        'half_time_home_goals','half_time_away_goals','home_corners','away_corners')


def synthetic_rows(n=110):
    """Entirely artificial, invented teams T0..T5; never real-match forecasting."""
    teams=[f'T{i}' for i in range(6)]
    rows=[]
    for i in range(n):
        t=teams[i%6]; u=teams[(i+1+i//6)%6]
        if t==u: u=teams[(i+3)%6]
        hg=(i*17)%4;ag=(i*11)%3
        d=(date(2025,8,1)+timedelta(days=i)).isoformat()
        rows.append({'fixture_id':f'fake-{i}','league':'SYN','season':'S1' if i<35 else 'S2',
                     'match_date':d,'home_id':t,'away_id':u,
                     'home_goals':str(hg),'away_goals':str(ag),'result':'H' if hg>ag else 'A' if hg<ag else 'D',
                     'half_time_home_goals':str(min(hg,i%2)),'half_time_away_goals':str(min(ag,(i+1)%2)),
                     'home_corners':str((i%7)+4),'away_corners':str((i%8)+2),
                     '_ht_usable':True,'_corner_usable':True})
    return rows


class Math263Suite(unittest.TestCase):
    def test_total_probabilities_coherent_and_analytical(self):
        m=score_market(1.7,1.1)
        p=m['markets']
        self.assertAlmostEqual(m['probability_sum'],1.,places=10)
        self.assertAlmostEqual(p['1X'],p['MS1']+p['MSX'],places=12)
        self.assertAlmostEqual(p['X2'],p['MSX']+p['MS2'],places=12)
        self.assertAlmostEqual(p['OVER_0.5'],1-math.exp(-2.8),places=10)
        self.assertAlmostEqual(p['BTTS_YES'],(1-math.exp(-1.7))*(1-math.exp(-1.1)),places=10)
        self.assertAlmostEqual(p['BTTS_YES']+p['BTTS_NO'],1.,places=12)
        for line in (0.5,1.5,2.5,3.5,4.5):
            self.assertAlmostEqual(p[f'OVER_{line:g}']+p[f'UNDER_{line:g}'],1.,places=12)
        self.assertLess(m['truncation_tail'],1e-9)

    def test_263_exact_shrink_prior(self):
        # Explicit template example: current 5 scored 9, old rho=1.2
        current=[{'home_id':'H','home_goals':str(x)} for x in (1,2,1,3,2)]
        prev=[{'home_id':'H','home_goals':'18'}] # mean18 / prev_ref15 =1.2
        d=_shrink(current,prev,'H','home','home_goals',1.5,15.)
        self.assertEqual(d['n'],5)
        self.assertAlmostEqual(d['rho'],1.2)
        self.assertAlmostEqual(d['prior_mean'],1.65)
        self.assertAlmostEqual(d['adjusted_mean'],1.725)
        # Promoted team: prior rho=1, no fabricated previous-season match
        x=_shrink(current,[],'H','home','home_goals',1.5,15.)
        self.assertEqual(x['rho'],1.0)
        self.assertAlmostEqual(x['prior_mean'],1.5)

    def test_c2_exact_four_context_rule_not_an_extra_thirty_games(self):
        rows=synthetic_rows()
        current=[r for r in rows if r['season']=='S2']
        previous=[r for r in rows if r['season']=='S1']
        cand,reason=canonical_c2_lambda(current[:12],previous,'T0','T1')
        self.assertIsNone(cand)
        self.assertIn('LT_4',reason)
        # 2.6.3 has no arbitrary minimum of 30 *league* matches for C2.
        mini=[]
        for i in range(4):
            mini.append({'home_id':'H','away_id':'Z'+str(i),'home_goals':'1','away_goals':'1'})
            mini.append({'home_id':'Z'+str(i),'away_id':'A','home_goals':'1','away_goals':'1'})
        c2,problem=canonical_c2_lambda(mini,[],'H','A')
        self.assertIsNone(problem)
        self.assertEqual(c2['current_sample'],8)
        cand,reason=canonical_c2_lambda(current,previous,'T0','T1')
        if cand is not None:
            self.assertEqual(cand['k'],5)
            self.assertEqual(cand['w'],.5)
            self.assertEqual(cand['current_sample'],len(current))

    def test_foot_and_corner_distributions_are_independent(self):
        po,tail=_poisson_pmf(5.)
        self.assertLess(tail,1e-9)
        self.assertAlmostEqual(sum(po),1.,places=10)
        nbt,tail=_negative_binomial_pmf(8.,.35)
        self.assertLess(tail,1e-9)
        self.assertAlmostEqual(sum(nbt),1.,places=10)
        self.assertAlmostEqual(sum(i*v for i,v in enumerate(nbt)),8.,places=7)
        self.assertRaises(ValueError,_negative_binomial_pmf,-1.,.5)

    def test_no_same_day_leak_c2_c3_ht_corners(self):
        rows=synthetic_rows()
        target=rows[-1]['match_date'];src={'sha256':'synthetic'}
        def query(data):
            return build_analysis(data,src,'SYN','S2','S1',target,'T0','T1')
        a=query(rows)
        mutated=copy.deepcopy(rows)
        for row in mutated:
            if row['match_date']>=target:
                row.update(home_goals='77',away_goals='0',half_time_home_goals='77',
                           half_time_away_goals='0',home_corners='88',away_corners='0')
        b=query(mutated)
        self.assertEqual(a,b)
        self.assertFalse(a['fixture_verified'])
        self.assertFalse(a['is_real_match_forecast'])
        self.assertNotIn('first_half_corners',a['other_markets'])

    def test_market_failure_preserves_ft_and_labels_data(self):
        rows=synthetic_rows()
        for r in rows:r['_ht_usable']=False;r['_corner_usable']=False
        res=build_analysis(rows,{},'SYN','S2','S1','2025-12-22','T0','T1')
        self.assertEqual(res['other_markets']['first_half']['status'],'INSUFFICIENT_MARKET_DATA')
        self.assertEqual(res['other_markets']['full_time_corners']['status'],'INSUFFICIENT_MARKET_DATA')

    def test_parse_quarantine_and_score_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            fp=Path(tmp)/'source.csv'
            row=synthetic_rows(1)[0].copy();row['half_time_home_goals']='99';row['home_corners']=''
            with fp.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerow({k:row[k] for k in FIELDS})
            rs,meta=load_history(fp)
            self.assertEqual(meta['rows'],1)
            self.assertEqual(meta['market_quarantine'],{'first_half':1,'corners':1})
            self.assertFalse(rs[0]['_ht_usable']);self.assertFalse(rs[0]['_corner_usable'])
            row['result']='A' if row['result']!='A' else 'H'
            with fp.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerow({k:row[k] for k in FIELDS})
            self.assertRaises(InvalidHistory,load_history,fp)

    def test_sensitivity_discloses_heuristic_and_does_not_force_clips(self):
        s=sensitivity(1.5,1.1)
        self.assertEqual(s['status'],'HEURISTIC_NOT_CONFIDENCE_INTERVAL')
        self.assertAlmostEqual(s['ranges']['OVER_2.5'][0],score_market(1.35,.99)['markets']['OVER_2.5'])
        self.assertEqual(sensitivity(5.,4.)['status'],'NOT_CALCULATED_OUT_OF_RANGE')

if __name__=='__main__':unittest.main()