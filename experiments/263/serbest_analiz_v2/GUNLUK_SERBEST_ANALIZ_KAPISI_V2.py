#!/usr/bin/env python3
# coding: utf-8
"""Daily dispatch for the *existing* modular engines, with authoritative
fixture/KO preflight for new named 10-league games. No fixed morning window.

No fixture gate -> research calculation only, never a pre-match seal.
Verified fixture gate -> first ensure kickoff future & history fresh,
then use existing M4/C3 model mathematics and save the immutable local receipt.
GitHub pre-kickoff proof requires a real subsequent Git commit before kickoff.
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,sys
from pathlib import Path
from zoneinfo import ZoneInfo
from SERBEST_ANALIZ_YONLENDIRICI_V1 import (TEN_LEAGUES,RouterError,load_weights,
       recompute_m4_v4_named,run_named,run_pdf,save_run,decide)

TZ={'ENG1':'Europe/London','ENG2':'Europe/London','GER1':'Europe/Berlin',
    'ESP1':'Europe/Madrid','ITA1':'Europe/Rome','FRA1':'Europe/Paris',
    'NED1':'Europe/Amsterdam','TUR1':'Europe/Istanbul',
    'POR1':'Europe/Lisbon','BEL1':'Europe/Brussels'}

class GateError(ValueError):pass

def now_utc():return dt.datetime.now(dt.timezone.utc)

def gate_result(gate,league,now):
    """Structure/time checks after *an independently invoked official gateway*.
    Not proof that a hand-crafted dict was fetched from an official source.
    """
    if gate.get('status')!='VERIFIED' or gate.get('league')!=league:
        raise GateError('OFFICIAL_NAMED_FIXTURE_NOT_VERIFIED')
    if not all(gate.get(x) for x in ('home_id','away_id','kickoff_utc','retrieved_at_utc','source_url')):
        raise GateError('OFFICIAL_GATE_INCOMPLETE')
    if gate['home_id']==gate['away_id'] or not str(gate['source_url']).startswith('https://'):
        raise GateError('OFFICIAL_GATE_TEAM_OR_SOURCE_INVALID')
    ko=dt.datetime.fromisoformat(str(gate['kickoff_utc']).replace('Z','+00:00'))
    checked=dt.datetime.fromisoformat(str(gate['retrieved_at_utc']).replace('Z','+00:00'))
    if ko.tzinfo is None or checked.tzinfo is None or now.tzinfo is None:
        raise GateError('NAIVE_KO_OR_CHECK_TIME')
    ko=ko.astimezone(dt.timezone.utc);checked=checked.astimezone(dt.timezone.utc)
    if not now<ko:raise GateError('KICKOFF_NOT_IN_FUTURE')
    if checked>now+dt.timedelta(minutes=5) or now-checked>dt.timedelta(hours=24):
        raise GateError('STALE_OFFICIAL_OBSERVATION')
    local=ko.astimezone(ZoneInfo(TZ[league])).date().isoformat()
    return {'local_date':local,'kickoff_utc':ko.isoformat(),
       'official_check_utc':checked.isoformat(),'source_url':gate['source_url'],
       'home_id':gate['home_id'],'away_id':gate['away_id']}

def latest_result_age(history,league,date):
    import csv
    with Path(history).open(encoding='utf-8-sig',newline='') as f:
        rows=[r for r in csv.DictReader(f) if r.get('league')==league and r.get('match_date','')<date]
    if not rows:raise GateError('NO_PREMATCH_LEAGUE_RESULTS')
    latest=max(r['match_date'] for r in rows)
    age=(dt.date.fromisoformat(date)-dt.date.fromisoformat(latest)).days
    return age,latest

def validate_source_locks(engine_root,history):
    """Only SHA-pinned original 4,617 OR separately accepted 4,700 research data.

    Research 4,700 has 83 results cross-checked against a SECOND public source.
    It is not a federation-certified score archive and never rewrites the 4,617
    input or original prematch seals. A file alone cannot self-authorize.
    """
    root=Path(engine_root).resolve()
    lock=root/'experiments/263/m4_lock.json'
    eng=root/'experiments/263/m4_integrated.py'
    old_prov=root/'data/results_only_263/4617_research_input_provenance.json'
    new_file=root/'data/research_263/2026-11-23_4700_two_source_research.csv'
    new_prov=root/'data/research_263/2026-11-23_4700_two_source_provenance.json'
    new_ledger=root/'data/research_263/2026-11-23_83_two_source_match_ledger.json'
    if not all(x.is_file() for x in (lock,eng,old_prov)):
        raise GateError('M4_LOCK_OR_SOURCE_PROVENANCE_UNAVAILABLE')
    a=json.loads(lock.read_text(encoding='utf-8'))
    digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    if a.get('m4_engine_sha256')!=digest(eng):
        raise GateError('M4_MATH_UNEXPECTED_SHA')
    h=Path(history).resolve();live_sha=digest(h)
    old=json.loads(old_prov.read_text(encoding='utf-8'))
    if (h==(root/old['source_snapshot_path']).resolve() and
          old.get('source_snapshot_sha256')==live_sha and
          old.get('usable_total_rows')==4617):
        return {'engine_sha256':digest(eng),'history_sha256':live_sha,
                'provenance_schema':old['schema'],'research_rows':4617,
                'score_evidence':'LEGACY_RESEARCH'}
    if h!=new_file.resolve() or not all(x.is_file() for x in (new_prov,new_ledger)):
        raise GateError('FOOTBALL_HISTORY_NOT_ON_WHITELIST')
    b=json.loads(new_prov.read_text(encoding='utf-8'))
    ledger=json.loads(new_ledger.read_text(encoding='utf-8'))
    if (b.get('schema')!='263_RESEARCH_HISTORY_4700_TWO_SECONDARY_SOURCES_PIN_V1'
        or b.get('status')!='RESEARCH_APPROVED_SECONDARY_SCORE_AGREEMENT_NOT_FEDERATION_VERIFIED'
        or b.get('source_snapshot_sha256')!=live_sha
        or live_sha!='37bf74e820df85325213c2e0ef8ce9a88a16c1f452edf5bd2a41814f10f261bd'
        or b.get('source_snapshot_path')!='data/research_263/2026-11-23_4700_two_source_research.csv'
        or b.get('score_ledger_path')!='data/research_263/2026-11-23_83_two_source_match_ledger.json'
        or b.get('usable_total_rows')!=4700
        or b.get('accepted_legacy_rows')!=4617
        or b.get('new_concordant_results')!=83
        or b.get('asof_exclusive')!='2026-11-23'
        or b.get('independent_federation_evidence') is not False
        or ledger.get('source_snapshot_sha256')!=live_sha
        or len(ledger.get('matches',[]))!=83
        or not all(row.get('score_agrees') is True for row in ledger['matches'])):
        raise GateError('RESEARCH_4700_PROVENANCE_OR_SECOND_SOURCE_AUDIT_INVALID')
    # A true current research calculation requires accepted provenance; no
    # retroactive prematch seal or claim of official independent score review.
    return {'engine_sha256':digest(eng),'history_sha256':live_sha,
            'provenance_schema':b['schema'],'research_rows':4700,
            'score_evidence':'83_TWO_PUBLIC_SECONDARY_SOURCES_NOT_FEDERATIONS'}


def official_named(league,home,away,weights,engine_root,history,registry,
                   *,gateway_factory=None,clock=None,max_gap_days=10):
    if league not in TEN_LEAGUES:raise GateError('OUTSIDE_TEN_LEAGUE_NAMED_SCOPE')
    now=clock or now_utc()
    if gateway_factory is None:
        sys.path.insert(0,str(Path(engine_root).resolve()/'experiments/263'))
        sys.path.insert(0,str(Path(engine_root).resolve()))
        from sabah_official_fixture_gateway_263 import OfficialFixtureGateway
        gateway_factory=OfficialFixtureGateway
    gateway=gateway_factory()
    actual=gateway.lookup(league,home,away) # Independent named-match lookup.
    checked=gate_result(actual,league,now)
    date=checked['local_date']
    age,latest=latest_result_age(history,league,date)
    lock=validate_source_locks(engine_root,history)
    gap_evidence={'status':'WITHIN_NORMAL_TEN_DAY_LIMIT','age_days':age}
    if age>max_gap_days:
        # The original main machine already has a verified no-games-during-break
        # exemption. Reuse its strict exact-league, same-snapshot source check.
        # Never treat a calendar gap as proof there were no missing games.
        import csv
        sd=Path(engine_root).resolve()/'experiments/263'
        sys.path.insert(0,str(sd))
        sys.path.insert(0,str(Path(engine_root).resolve()))
        from freshness_gap_guard_263 import review_gap
        with Path(history).open(encoding='utf-8-sig',newline='') as f:
            accepted_rows=list(csv.DictReader(f))
        try:
            gap_evidence=review_gap(accepted_rows,league,date,now=now)
        except Exception as exc:
            raise GateError('FRESHNESS_GAP_NOT_VERIFIED:'+str(exc)) from exc
        if gap_evidence.get('status')!='BOUNDED_GAP_NO_MISSING_RESULTS_IN_PUBLIC_FEED_RESEARCH_ONLY':
            raise GateError('FRESHNESS_GAP_NOT_ACCEPTED')
    m=recompute_m4_v4_named(engine_root,history,registry,league,home,away,date)
    model=m['seven']
    main=decide({'M4_C3_V4':model},weights)
    receipt={'schema':'SERBEST_NAMED_OFFICIAL_PREKO_RESEARCH_V2',
             'match':home+' - '+away,'league':league,
             'kickoff_utc':checked['kickoff_utc'],
             'observed_at_utc':now.isoformat(),
             'official_source_url':checked['source_url'],
             'official_check_utc':checked['official_check_utc'],
             'home_id':checked['home_id'],'away_id':checked['away_id'],
             'football_history_latest':latest,'football_history_age_days':age,
             'engine_acceptance':lock,'freshness_gap_review':gap_evidence,
             'predictions':{'M4_C3_V4':model},
             'decision':main,'status':'OFFICIAL_FIXTURE_VERIFIED_MODEL_RESEARCH_RECEIPT_NOT_GIT_SEALED',
             'note':'KO verified independently from gateway. Git SHA pre-KO commit is separately required to call this a sealed record.'}
    return receipt

def save_official_receipt(obj,out_dir):
    p=Path(out_dir);p.mkdir(parents=True,exist_ok=True)
    body=json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    sha=hashlib.sha256(body.encode()).hexdigest()
    # Content-addressed creation only; repeated identical calls never rewrite.
    file=p/(obj['kickoff_utc'][:10]+'_'+sha[:24]+'.json')
    with file.open('x',encoding='utf-8') as f:
        f.write(json.dumps({**obj,'payload_sha256':sha},ensure_ascii=False,indent=2)+'\n')
    return file

def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--pdf',type=Path)
    mode.add_argument('--league',choices=sorted(TEN_LEAGUES))
    p.add_argument('--home');p.add_argument('--away');p.add_argument('--date')
    p.add_argument('--archive',type=Path)
    p.add_argument('--rule',required=True,type=Path)
    p.add_argument('--hakem2-rule',type=Path,help='Optional frozen Hakem2 selector; no blend on missing expert')
    p.add_argument('--model-index',type=Path)
    p.add_argument('--engine-root',type=Path)
    p.add_argument('--history',type=Path)
    p.add_argument('--registry',type=Path)
    p.add_argument('--research-only',action='store_true',help='Explicitly no fixture/KO authentication, never sealed')
    p.add_argument('--out-dir',required=True,type=Path)
    a=p.parse_args()
    weights,_=load_weights(a.rule)
    if a.pdf:
        d=run_pdf(a.pdf,a.archive,weights,model_index=a.model_index, date=a.date,
                  engine_root=a.engine_root, history=a.history,registry=a.registry)
        if a.hakem2_rule:
            from HAKEM2_GUNLUK_SECICI_V1 import load_h2_rule,apply_hakem2
            d=apply_hakem2(d,load_h2_rule(a.hakem2_rule))
        out,md=save_run(d,a.out_dir)
        print(json.dumps({'type':'PDF_INDEPENDENT','count':d['count'],'json':str(out),'report':str(md),
               'researched':sum(bool(r['decision']) for r in d['matches'])},ensure_ascii=False))
        return
    if not (a.home and a.away):p.error('Named mode requires --home and --away')
    if a.research_only:
        if not a.date:p.error('--date is required for unverified research')
        d=run_named(a.league,a.home,a.away,a.date,weights,model_index=a.model_index,
                    engine_root=a.engine_root,history=a.history,registry=a.registry)
        if a.hakem2_rule:
            from HAKEM2_GUNLUK_SECICI_V1 import load_h2_rule,apply_hakem2
            d=apply_hakem2(d,load_h2_rule(a.hakem2_rule))
        out,md=save_run(d,a.out_dir)
        print(json.dumps({'type':'NAMED_RESEARCH_NO_SEAL','json':str(out),'report':str(md)},ensure_ascii=False));return
    if not all((a.engine_root,a.history,a.registry)):
        p.error('Verified named mode requires --engine-root, --history, --registry')
    r=official_named(a.league,a.home,a.away,weights,a.engine_root,a.history,a.registry)
    file=save_official_receipt(r,a.out_dir)
    print(json.dumps({'type':'OFFICIAL_PREKO_RESEARCH_RECEIPT_NEEDS_GIT_COMMIT','file':str(file)},ensure_ascii=False))
if __name__=='__main__':main()
