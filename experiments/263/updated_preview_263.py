"""Preview only: consume a *staged* append-only 2.6.3 snapshot with strict lineage.

This is deliberately separate from old locked acceptance, so historical metrics
cannot be represented as a new snapshot's independent calibration evidence.
No live fixtures, selection, betting, odds, pilot, or automatic model promotion.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from analysis_math_core import build_analysis,load_history
from data_context_263 import build_data_context
from operational_report_263 import _reference_model_b,_scenarios,_ranking,named_cases
from quality_gate_263 import HISTORICAL_SHA256

VERSION='263_staged_current_history_preview_v1'
class PreviewError(ValueError):pass

def preview(rows,meta,audit,cases,base_rows,base_meta):
    if audit.get('version')!='263_append_only_provider_snapshot_v1':
        raise PreviewError('Staged refresh audit required')
    if audit.get('status')!='STAGED_UNVERIFIED_SOURCE_FILES' or audit.get('base_sha256')!=HISTORICAL_SHA256:
        raise PreviewError('Invalid frozen-history lineage')
    if (audit.get('total_rows')!=len(rows) or meta.get('rows')!=len(rows)
        or audit.get('extended_history_sha256')!=meta.get('sha256')
        or audit.get('base_rows')!=4413 or audit.get('appended')!=len(rows)-4413
        or audit.get('source_completeness')!='TEN_LEAGUES'
        or audit.get('independent_source_verification') is not False
        or audit.get('retrospective_model_acceptance_transferred') is not False):
        raise PreviewError('Snapshot or provenance mismatch')
    # A manifest alone cannot prove that the old 4,413 results were preserved.
    # Recompare every old fixture against a separately loaded SHA-pinned baseline.
    if base_meta.get('sha256')!=HISTORICAL_SHA256 or len(base_rows)!=4413:
        raise PreviewError('Independent frozen baseline required')
    old={r['fixture_id']:r for r in base_rows}
    new={r['fixture_id']:r for r in rows}
    if len(new)!=len(rows) or not set(old).issubset(new):
        raise PreviewError('Frozen fixtures absent in extended snapshot')
    for fid,r in old.items():
        if any(str(v)!=str(new[fid].get(k)) for k,v in r.items()):
            raise PreviewError('A frozen historical record was modified')
    if not isinstance(cases,list) or not 1<=len(cases)<=20:
        raise PreviewError('Expected 1..20 hypothetical named cases')
    result=[]
    for case in cases:
        # A later hypothetical match is allowed; no result dated on/after it is used.
        # Source freshness is reported as of the last supplied historical snapshot.
        out=build_analysis(rows,meta,league=case["league"],season=case["season"],
                           previous_season=case["previous_season"],target_date=case["target_date"],
                           home=case["home_id"],away=case["away_id"])
        c2=out['model_outputs'].get('C2')
        b=_reference_model_b(rows,case)
        form=_scenarios(rows,case)
        context=build_data_context(rows,meta,case)
        result.append({'identity':case,'canonical_c2':c2,'canonical_c2_status':out['model_status']['C2'],
            'existing_model_b':b,'experimental_c3':out['model_outputs'].get('C3'),
            'experimental_c3_status':out['model_status']['C3'],
            'experimental_other_markets':out['other_markets'],
            'model_probability_ranking_descriptive_only':_ranking(c2,b),
            'form_descriptive_only':form,'data_context':context,
            'market_calibration':'NOT_REEVALUATED_ON_EXTENDED_SNAPSHOT',
            'official_fixture_status':'NOT_CHECKED_OFFLINE',
            'recommended':False,'odds_EV':None})
    return {'version':VERSION,'status':'OFFLINE_STAGED_SOURCE_PREVIEW_NOT_ACCEPTED',
        'input_provenance':{'sha256':meta['sha256'],'rows':len(rows),'appended':audit['appended'],
                            'base_sha256':audit['base_sha256'],'provider_fetch_independently_verified':False},
        'retrospective_2026_27_model_acceptance_applies_to_updated_snapshot':False,
        'no_live_fixture_verification':True,'no_calibration_claim':True,
        'model_b_unchanged':True,'canonical_c2_unchanged':True,
        'provider_source_as_of_exclusive':audit['as_of_exclusive'],
        'c3_not_promoted':True,'recommendations':[],'odds_EV':None,'cases':result}

def main(argv=None):
    p=argparse.ArgumentParser(description='OFFLINE updated-data mathematical preview (not live analysis)')
    p.add_argument('--history',required=True)
    p.add_argument('--refresh-audit',required=True)
    p.add_argument('--base',required=True,help='Original immutable 4,413-match snapshot')
    p.add_argument('--identity-index',required=True)
    p.add_argument('--aliases',required=True)
    p.add_argument('--named',required=True)
    p.add_argument('--out',required=True)
    args=p.parse_args(argv)
    rows,meta=load_history(args.history)
    base_rows,base_meta=load_history(args.base)
    raw=Path(args.history).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=meta['sha256']:raise PreviewError('History bytes changed')
    audit=json.loads(Path(args.refresh_audit).read_text(encoding='utf-8'))
    requests=json.loads(Path(args.named).read_text(encoding='utf-8'))
    cases=named_cases(args.identity_index,args.aliases,requests)
    rep=preview(rows,meta,audit,cases,base_rows,base_meta)
    Path(args.out).write_text(json.dumps(rep,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':rep['status'],'cases':len(rep['cases']), 'recommendations':0},ensure_ascii=False))
if __name__=='__main__':main()
