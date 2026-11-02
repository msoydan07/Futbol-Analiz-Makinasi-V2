"""B/C2/C3/M4 pre-kickoff single-fixture pilot ledger, experimental ONLY.

Uses EXISTING live official named-match gate (no supplied JSON on CLI), and
existing frozen B/C2/C3 formula functions without editing them.
Legacy 0..10 Poisson tails are kept explicitly for B and C3.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from exp_263_batch import c1, clean_rows, fit_c3, predict_c3, scores
from analysis_math_core import canonical_c2_lambda, score_market
from forward_c3 import valid_gate, sha256_file, canonical_bytes, MAX_DATA_AGE_DAYS
from m4_integrated import Settings, fit_m4, predict_m4, score_markets, use_lock, FEATURE_VERSION

SCHEMA='quad_forward_263_v1'
FROZEN='35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1'
REQUIRED_BASE_COUNT=4413


def _legacy_joint(lh,la,original):
    """Preserve unchanged B/C3 0..10 normalized 1X2 while adding markets."""
    hh=np.array([math.exp(-lh)*lh**i/math.factorial(i) for i in range(11)])
    aa=np.array([math.exp(-la)*la**i/math.factorial(i) for i in range(11)])
    matrix=np.outer(hh,aa)
    tail=1-float(matrix.sum())
    if tail>0.001:raise ValueError('legacy_poisson_tail_invalid')
    matrix/=matrix.sum()
    h=np.arange(11)[:,None];a=np.arange(11)[None,:]
    p={'H':float(matrix[h>a].sum()),'D':float(matrix[h==a].sum()),'A':float(matrix[h<a].sum())}
    if max(abs(p[k]-original[i]) for i,k in enumerate(('H','D','A')))>1e-10:
        raise ValueError('legacy_formula_changed')
    m={'1X2':p,'BTTS_YES':float(matrix[(h>0)&(a>0)].sum())}
    m['BTTS_NO']=1-m['BTTS_YES']
    for l in (1.5,2.5,3.5):
        ov=float(matrix[h+a>l].sum());m[f'OVER_{l:g}']=ov;m[f'UNDER_{l:g}']=1-ov
    top=sorted(((float(matrix[i,j]),f'{i}-{j}') for i in range(11) for j in range(11)),reverse=True)[:5]
    return {'lambda_home':lh,'lambda_away':la,'markets':m,'top_scores':{name:p for p,name in top},
            'tail_mass':tail,'distribution':'legacy_truncated_poisson_0_to_10_normalized'}


def _b_lambdas(past,home,away):
    """Extract lambda from frozen C1 expression and VERIFY its legacy probabilities."""
    if len(past)<30:return None
    h=[r for r in past if r['home_id']==home][-20:]
    a=[r for r in past if r['away_id']==away][-20:]
    if min(len(h),len(a))<5:return None
    mh=sum(int(r['home_goals']) for r in past)/len(past)
    ma=sum(int(r['away_goals']) for r in past)/len(past)
    if min(mh,ma)<=0:return None
    def sm(rows,key,mu):return (sum(int(r[key]) for r in rows)+5*mu)/(len(rows)+5)/mu
    return (max(.05,min(5,mh*sm(h,'home_goals',mh)*sm(a,'home_goals',mh))),
            max(.05,min(5,ma*sm(a,'away_goals',ma)*sm(h,'away_goals',ma))))


def verify_snapshot(path,rows,now,base=None,source_audit=None):
    digest=sha256_file(path)
    if digest==FROZEN:
        if len(rows)!=REQUIRED_BASE_COUNT:raise ValueError('frozen_row_count_mismatch')
        return 'PINNED_FROZEN_HISTORICAL_ARCHIVE',digest
    if base is None or source_audit is None:
        raise ValueError('updated_history_requires_baseline_and_source_acceptance')
    if sha256_file(base)!=FROZEN:raise ValueError('baseline_sha_mismatch')
    original=clean_rows(base)
    if len(original)!=REQUIRED_BASE_COUNT:raise ValueError('baseline_row_count_mismatch')
    known={r['fixture_id']:r for r in rows}
    for old in original:
        new=known.get(old['fixture_id'])
        if new is None or any(str(new.get(k))!=str(v) for k,v in old.items()):
            raise ValueError('append_only_historical_archive_modified')
    if len(rows)<=len(original):raise ValueError('no_new_rows_in_updated_history')
    audit=json.loads(Path(source_audit).read_text(encoding='utf-8'))
    if audit.get('status')!='HUMAN_VERIFIED_SOURCE_ACCEPTANCE' or audit.get('snapshot_sha256')!=digest or audit.get('baseline_sha256')!=FROZEN:
        raise ValueError('source_provenance_not_accepted')
    if not audit.get('reviewer') or not audit.get('source_links') or not isinstance(audit['source_links'],list):
        raise ValueError('source_provenance_incomplete')
    from forward_c3 import read_aware
    reviewed=read_aware(audit['reviewed_at_utc'])
    if reviewed>now or (now-reviewed).total_seconds()>7*86400:
        raise ValueError('source_provenance_review_expired')
    # This is a disclosed HUMAN ATTESTATION, not independent network verification.
    return 'APPEND_ONLY_HUMAN_SOURCE_ATTESTED_NOT_INDEPENDENTLY_RECHECKED',digest


def predict_quad_from_verified_gate(gate,history_path,out_dir,lock_path,now=None,base=None,source_audit=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError('aware_current_time_required')
    now=now.astimezone(timezone.utc)
    league,home,away,kickoff,checked,local_date=valid_gate(gate,now)
    rows=clean_rows(history_path)
    source_status,source_sha=verify_snapshot(history_path,rows,now,base,source_audit)
    future_rows=[r for r in rows if r['match_date']>local_date and r['league']==league]
    if future_rows:raise ValueError('source_contains_same_day_or_future_results')
    league_rows=[r for r in rows if r['league']==league]
    if not league_rows:raise ValueError('missing_league_history')
    latest=max(r['match_date'] for r in league_rows)
    if (datetime.fromisoformat(local_date).date()-datetime.fromisoformat(latest).date()).days>MAX_DATA_AGE_DAYS:
        raise ValueError('stale_history_refresh_required')
    past=[r for r in league_rows if r['match_date']<local_date]
    if len(past)<60:raise ValueError('m4_minimum_historical_sample_missing')
    lock_path=Path(lock_path)
    lock=json.loads(lock_path.read_text(encoding='utf-8'))
    setting=use_lock(lock)
    if lock.get('m4_engine_sha256')!=sha256_file(Path(__file__).with_name('m4_integrated.py')):
        raise ValueError('m4_engine_changed_after_lock')
    if lock.get('frozen_source_sha256')!=FROZEN:
        raise ValueError('m4_lock_wrong_archive')

    outputs={}
    b=c1(past,home,away)
    bl=_b_lambdas(past,home,away)
    if (b is None)!=(bl is None):raise ValueError('frozen_b_compatibility_failed')
    outputs['B']={'status':'AVAILABLE','goals':_legacy_joint(*bl,b[0])} if b else {'status':'UNAVAILABLE_INSUFFICIENT_CONTEXT'}
    current=[r for r in past if r['season']=='2026-2027']
    previous=[r for r in past if r['season']=='2025-2026']
    c2,reason=canonical_c2_lambda(current,previous,home,away)
    outputs['C2']={'status':'AVAILABLE','goals':score_market(c2['lambda_home'],c2['lambda_away'])} if c2 else {'status':'UNAVAILABLE','reason':reason}
    fit3=fit_c3(past)
    lam3=predict_c3(fit3,home,away) if fit3 else None
    s3=scores(*lam3) if lam3 else None
    outputs['C3']={'status':'AVAILABLE','goals':_legacy_joint(*lam3,s3[0])} if s3 else {'status':'UNAVAILABLE_FIT_OR_TAIL'}
    mfit=fit_m4(past,league,local_date,setting)
    mlam=predict_m4(mfit,home,away)
    outputs['M4']={'status':'AVAILABLE','goals':score_markets(*mlam),'train_rows':mfit[3]} if mlam else {'status':'UNAVAILABLE_FIT_OR_RANGE'}

    data={'schema':SCHEMA,'status':'EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING',
          'created_at_utc':now.isoformat(),
          'fixture':{'league':league,'home_id':home,'away_id':away,'kickoff_utc':kickoff.isoformat(),
                     'match_local_date':local_date,'official_source':gate['source_url'],
                     'source_checked_at_utc':checked.isoformat(),
                     'fixture_verification':'VERIFIED_BY_LIVE_OFFICIAL_GATE'},
          'data':{'snapshot_sha256':source_sha,'snapshot_acceptance':source_status,
                  'league_history_rows':len(past),'league_latest_result_date':latest,
                  'cutoff_rule':'strictly_before_local_kickoff_date'},
          'code':{'B_C2_C3':'FROZEN_EXISTING_MODEL_FUNCTIONS',
                  'frozen_batch_sha256':sha256_file(Path(__file__).with_name('exp_263_batch.py')),
                  'frozen_c2_sha256':sha256_file(Path(__file__).with_name('analysis_math_core.py')),
                  'm4_engine_sha256':lock['m4_engine_sha256'],
                  'quad_forward_sha256':sha256_file(__file__),
                  'm4_lock_sha256':sha256_file(lock_path),'m4':FEATURE_VERSION},
          'm4_learned_settings':lock['settings'],'model_predictions':outputs,
          'pilot_restrictions':['No odds, EV, bet or production promotion','No first-half or corner estimates',
                                'C2 missing context is reported, never imputed','Human-attested updated data is not independently reverified by this code']}
    digest=hashlib.sha256(canonical_bytes(data)).hexdigest();data['payload_sha256']=digest
    fixture_id=hashlib.sha256(canonical_bytes([league,home,away,kickoff.isoformat()])).hexdigest()[:24]
    target=Path(out_dir)/local_date/(fixture_id+'.json')
    # Enforce exactly one immutable prediction per fixture and max 100 registrations.
    if len(list(Path(out_dir).glob('*/*.json')))>=100:raise ValueError('quad_pilot_100_record_limit')
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
        f.write('\n')
    return target,data


def main():
    parser=argparse.ArgumentParser(description='Four-model EXPERIMENTAL forward single-match pilot')
    for item in ('league','home','away'):parser.add_argument('--'+item,required=True)
    parser.add_argument('--history',required=True)
    parser.add_argument('--m4-lock',default='experiments/263/m4_lock.json')
    parser.add_argument('--out-dir',default='forward_quad_263')
    parser.add_argument('--baseline')
    parser.add_argument('--source-acceptance')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(root))
    from analyze_named_match_gate import run as live_gate
    try:
        gate=live_gate(args.league,args.home,args.away)
        target,record=predict_quad_from_verified_gate(gate,args.history,args.out_dir,args.m4_lock,base=args.baseline,source_audit=args.source_acceptance)
        print(json.dumps({'status':record['status'],'path':str(target),'sha256':record['payload_sha256']},ensure_ascii=False))
    except (ValueError,OSError,KeyError,AssertionError) as exc:
        raise SystemExit(f'BLOCKED_NO_PREDICTION_SAVED: {exc}') from exc

if __name__=='__main__':main()
