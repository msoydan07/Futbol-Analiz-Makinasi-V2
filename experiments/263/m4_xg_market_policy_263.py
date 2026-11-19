"""Market-by-market M4+xG research selection, rooted in exact 1,083 paired forecasts.

Only the 2.5 goal family used xG under the Nov-19 research decision.
This output does NOT alter frozen M4, SHA-sealed forecasts or bookmaker policy.
"""
from __future__ import annotations
import math

EVIDENCE = {
    'window':'2026-08-01/2026-11-08',
    'n':1083,
    'xg_applied':810,
    'm4_source_sha256':'eac755e54086738f40d7f30a514b2c9bb789b2fd2b49bc45',
    'xg_data_sha256':'3b13921daafab70aa121fe807fea0a74e0c72f0fc2381366b183f621edea762c',
    'same_date_leakage_forbidden':True,
    'score_history_origin':'private xG/score research CSV; not independent score attestation',
    'blind_out_of_sample':False,
    'm4_minus_xg_brier':{'MS':-0.0012249176434495634,
                          'GOALS_2_5':0.003084994432350774,
                          'KG':0.0012324759913620864},
    'day_cluster_95pct_ci_goals_2_5':[0.0006125579165628919,0.0056600974028880919]
}


def _p(v):
    if not isinstance(v,(float,int)) or not math.isfinite(v) or not 0 <= v <= 1:
        raise ValueError('INVALID_MARKET_PROBABILITY')
    return float(v)


def _pair(a,b):
    x,y=_p(a),_p(b)
    if abs(x+y-1.0)>1e-8:
        raise ValueError('MARKET_FAMILY_NOT_NORMALIZED')
    return x,y


def choose_market_families(sidecar):
    """Select research probabilities, not decisions/bets, with conservative guards.

    Use original M4 for MS and KG. Use xG for 2.5 Over/Under only if
    source status is confirmed, and xG 2.5 probabilities respect the M4
    1.5 / 3.5 over bounds; otherwise revert the whole 2.5 market family.
    """
    if sidecar.get('schema')!='263_m4_xg_sidecar_v1' or sidecar.get('use')!='RESEARCH_SIDECAR_NOT_PRODUCTION':
        raise ValueError('RESEARCH_M4_XG_SIDECAR_REQUIRED')
    x=sidecar.get('xg') or {}
    active=x.get('status')=='XG_INCLUDED_IN_M4_RESEARCH_LAMBDA'
    if active:
        old=x['markets']['M4_original']
        new=x['markets']['M4_with_xg']
    else:
        return {'schema':'263_m4_xg_marketwise_research_policy_v1',
                'status':'BASELINE_ONLY_NO_XG_MARKET_SELECTION',
                'market_source':{'MS':'M4','KG':'M4','GOALS_2_5':'M4'},
                'selected_probability':None,
                'reason':x.get('reason','NO_VALID_PRIOR_XG'),
                'evidence':EVIDENCE,
                'official_m4_modified':False,'betting_authorized':False}
    ms=[_p(old['1X2'][k]) for k in ('H','D','A')]
    if abs(sum(ms)-1.0)>1e-8:raise ValueError('MS_NOT_NORMALIZED')
    kg_yes,kg_no=_pair(old['BTTS_YES'],old['BTTS_NO'])
    original_over,original_under=_pair(old['OVER_2.5'],old['UNDER_2.5'])
    updated_over,updated_under=_pair(new['OVER_2.5'],new['UNDER_2.5'])
    higher=_p(old['OVER_1.5'])
    lower=_p(old['OVER_3.5'])
    if not lower<=original_over<=higher:
        raise ValueError('ORIGINAL_GOAL_LINES_NOT_ORDERED')
    coherent=lower-1e-10<=updated_over<=higher+1e-10
    p25=(updated_over,updated_under) if coherent else (original_over,original_under)
    return {'schema':'263_m4_xg_marketwise_research_policy_v1',
            'status':('MARKETWISE_RESEARCH_SELECT_2_5_XG' if coherent
                      else 'MARKETWISE_RESEARCH_GOAL_COHERENCE_FALLBACK'),
            'market_source':{'MS':'M4','KG':'M4',
                             'GOALS_2_5':'M4_PLUS_PRIOR_XG' if coherent else 'M4'},
            'selected_probability':{'MS1':ms[0],'MSX':ms[1],'MS2':ms[2],
                                    'KG_VAR':kg_yes,'KG_YOK':kg_no,
                                    'UST_2_5':p25[0],'ALT_2_5':p25[1]},
            'evidence':EVIDENCE,
            'official_m4_modified':False,'betting_authorized':False,
            'disclaimer':'Research-only marginal selection; not a new joint score distribution or a validated market EV.'}
