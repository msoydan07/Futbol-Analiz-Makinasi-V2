"""Connect existing *single requested* official fixture gate to existing 2.6.3 math.

No match discovery, no odds, no new model fitting. Output is an audited
mathematical preview, never a live betting approval or prediction ledger.

There are two mutually exclusive modes:
  frozen: pinned 4,413-match history, full existing offline 17-section audit.
  staged: append-only Tuesday refresh, existing updated_preview_263 (NOT 17-section certified).

Do not accept user-created verification JSON: the real CLI invokes the existing
on-demand source adapter. Tests can inject a trusted fake gateway in-process.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo
import json
from pathlib import Path
from typing import Callable
from on_demand_context_263 import prepare_named_match
from analysis_math_core import load_history
from operational_report_263 import (named_cases, build_operational_offline_bundle,
                                    render_operational_markdown)
from quality_gate_263 import locked_evidence, HISTORICAL_SHA256
from section_acceptance_263 import audit as audit_sections, render as render_sections
from updated_preview_263 import preview as staged_preview
from analysis_time_decision_bridge_263 import offline_appendix, render_appendix

VERSION = '263_requested_match_single_path_v1'
class RequestedMatchError(ValueError): pass


def _file_sha_matches(base_rows,base_meta):
    if base_meta.get('sha256') != HISTORICAL_SHA256 or len(base_rows) != 4413:
        raise RequestedMatchError('frozen baseline not independently pinned')


def requested_match(*, league,home,away,index_path,alias_path,history_path,
                    evidence_path=None,refresh_audit_path=None,base_path=None,
                    fixture_gate:Callable|None=None,quote_provider:Callable|None=None,now:datetime|None=None,
                    registry_path='data/match_registry.json'):
    """One invocation. Fixture gate must fetch/parse official source; no supplied flags.

    If fixture unverified, DO NOT calculate. Verified fixture is metadata;
    math remains unapproved offline preview, with distinct provenance labels.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise RequestedMatchError('timezone-aware current time required')
    if bool(base_path) != bool(refresh_audit_path):
        raise RequestedMatchError('staged snapshot requires base and refresh audit together')
    mode='STAGED' if refresh_audit_path else 'FROZEN'
    if mode=='FROZEN' and not evidence_path:
        raise RequestedMatchError('frozen acceptance evidence required')
    # Real CLI always uses default official verification, never user-supplied JSON.
    gate_kwargs={'now':now,'registry_path':registry_path}
    if fixture_gate is not None:gate_kwargs['fixture_gate']=fixture_gate
    verification=prepare_named_match(league,home,away,**gate_kwargs)
    envelope={'version':VERSION,'status':'OFFICIAL_FIXTURE_NOT_VERIFIED',
              'mode':mode,'requested':{'league':league,'home':home,'away':away},
              'fixture_check':verification,'model_not_promoted':True,
              'A_B_C_approved':False,'recommendations':[],'odds_EV':None,
              'pilot_recorded':False,'production_modified':False,
              'tuesday_policy':{'day':'TUESDAY','timezone':'Europe/Istanbul',
                                'automation_verified':False},
              'live_analysis_accepted':False}
    if verification.get('status')!='READY_FOR_DATA_AUDIT':
        return envelope,{}
    fixture=verification['fixture']
    local_date=fixture['local_date']
    cases=named_cases(index_path,alias_path,[{'league':league,'home':home,'away':away,
                                               'target_date':local_date}])
    c=cases[0]
    if (c['league'],c['home_id'],c['away_id']) != (
            fixture['league'],fixture['home_id'],fixture['away_id']):
        raise RequestedMatchError('OFFICIAL_VS_REVIEWED_IDENTITY_MISMATCH')
    rows,meta=load_history(history_path)
    latest=max(r['match_date'] for r in rows)
    now_turkey=now.astimezone(ZoneInfo('Europe/Istanbul')).date().isoformat()
    if latest>now_turkey:
        raise RequestedMatchError('future result detected in historical snapshot')
    envelope['historical_snapshot']={'sha256':meta['sha256'],'rows':len(rows),
                                     'last_result_date':latest,'target_date_exclusive':local_date}
    if mode=='FROZEN':
        _file_sha_matches(rows,meta)
        evidence=locked_evidence(evidence_path)
        bundle=build_operational_offline_bundle(rows,meta,evidence,cases)
        # The 17-section audit expects the pinned historical sample and explicitly
        # does NOT certify a real fixture; keep that contract unchanged.
        bundle['weekly_update_policy']={'day':'TUESDAY','timezone':'Europe/Istanbul',
                                         'automation_verified':False,'historical_base_immutable':True}
        contract=audit_sections(bundle)
        if contract.get('status')!='PASS_OFFLINE_INTEGRATION_ONLY':
            raise RequestedMatchError('17-section offline contract not satisfied')
        if bundle['cases'][0]['identity']!=c or bundle['cases'][0]['analysis']['fixture_verified'] is not False:
            raise RequestedMatchError('offline bundle identity or safety mismatch')
        envelope['status']='OFFICIAL_FIXTURE_CHECKED_FROZEN_MATH_PREVIEW_ONLY'
        envelope['live_analysis_accepted']=False
        envelope['model_readiness']='FROZEN_4413_ONLY_NOT_CURRENT_DATA_VERIFIED'
        decision_appendix=offline_appendix(verification,bundle,now,quote_provider=quote_provider)
        return envelope,{
            'model_preview.json':bundle,
            'model_preview.md':render_operational_markdown(bundle)+'\n\n'+render_appendix(decision_appendix),
            'analysis_time_odds_abc_appendix.json':decision_appendix,
            'section_acceptance_263.json':contract,
            'section_acceptance_263.md':render_sections(contract),
        }
    base_rows,base_meta=load_history(base_path)
    _file_sha_matches(base_rows,base_meta)
    refresh=json.loads(Path(refresh_audit_path).read_text(encoding='utf-8'))
    if not isinstance(refresh.get('as_of_exclusive'),str) or refresh['as_of_exclusive']>now_turkey:
        raise RequestedMatchError('staged provider snapshot dated in the future')
    p=staged_preview(rows,meta,refresh,cases,base_rows,base_meta)
    if p['status']!='OFFLINE_STAGED_SOURCE_PREVIEW_NOT_ACCEPTED' or p['recommendations']:
        raise RequestedMatchError('staged preview safety mismatch')
    envelope['status']='OFFICIAL_FIXTURE_CHECKED_STAGED_MATH_PREVIEW_ONLY'
    envelope['live_analysis_accepted']=False
    envelope['model_readiness']='STAGED_SOURCE_UNVERIFIED_NOT_ACCEPTED'
    # No 17-section certificate on newly updated data; that certificate is
    # cryptographically tied to the immutable 4,413-match baseline.
    envelope['section_17_acceptance']='NOT_TRANSFERRED_TO_STAGED_DATA'
    return envelope,{'staged_math_preview.json':p}


def write_outputs(envelope,outputs,out_dir):
    directory=Path(out_dir);directory.mkdir(parents=True,exist_ok=True)
    for name,payload in {'request_status.json':envelope,**outputs}.items():
        if '/' in name or '..' in name:raise RequestedMatchError('Unsafe artifact name')
        file=directory/name
        if name.endswith('.json'):
            file.write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        else:file.write_text(str(payload)+'\n',encoding='utf-8')
    return directory


def main(argv=None):
    p=argparse.ArgumentParser(description='One named match -> existing official gate -> safe 2.6.3 preview')
    for name in ('league','home','away','history','index','aliases','out'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--evidence',help='Required for pinned frozen-data mode')
    p.add_argument('--base',help='Pinned frozen data, required for staged-data mode')
    p.add_argument('--refresh-audit',help='Staged-data audit, required with --base')
    p.add_argument('--registry',default='data/match_registry.json',help='Existing team/match identity registry')
    a=p.parse_args(argv)
    envelope,outputs=requested_match(
        league=a.league,home=a.home,away=a.away,index_path=a.index,
        alias_path=a.aliases,history_path=a.history,evidence_path=a.evidence,
        base_path=a.base,refresh_audit_path=a.refresh_audit,
        registry_path=a.registry)
    write_outputs(envelope,outputs,a.out)
    print(json.dumps({'status':envelope['status'],'outputs':len(outputs)+1,
                       'live_analysis_accepted':False,'recommendations':0},ensure_ascii=False))
    return 0 if envelope['status'].startswith('OFFICIAL_FIXTURE_CHECKED_') else 2

if __name__=='__main__':raise SystemExit(main())
