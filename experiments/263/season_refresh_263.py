"""Append-only ten-league *offline* Football-Data source CSV refresh for 2.6.3.

Never modifies the frozen 4,413-match experiment. Existing match identities,
results and statistics are immutable; new completed matches must be supported
by the supplied full-season provider CSV, unique pairing and reviewed team ID.
Provider-file existence is NOT online/independent verification. No bets or odds.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import uuid
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from mackolik_identity_gate_263 import _candidate_id, _memberships, _validate_identity_source
from analysis_math_core import load_history
from quality_gate_263 import HISTORICAL_SHA256

VERSION='263_append_only_provider_snapshot_v1'
LEAGUES={'ENG1':'E0','ENG2':'E1','GER1':'D1','ESP1':'SP1','ITA1':'I1',
         'FRA1':'F1','NED1':'N1','TUR1':'T1','POR1':'P1','BEL1':'B1'}
SEASON='2026-2027'
SOURCE_PREFIX='https://www.football-data.co.uk/mmz4281/2627/'
NAMESPACE=uuid.UUID('0c312c79-42d1-4ca9-8b1c-4c65b96ef6b2')
STAT_MAP={'half_time_home_goals':'HTHG','half_time_away_goals':'HTAG',
          'half_time_result':'HTR','home_shots':'HS','away_shots':'AS',
          'home_shots_on_target':'HST','away_shots_on_target':'AST',
          'home_corners':'HC','away_corners':'AC','home_fouls':'HF',
          'away_fouls':'AF','home_yellow_cards':'HY','away_yellow_cards':'AY',
          'home_red_cards':'HR','away_red_cards':'AR'}

class RefreshError(ValueError):pass

def parse_date(value):
    if not isinstance(value,str):raise RefreshError('Source date missing')
    for fmt in ('%d/%m/%Y','%d/%m/%y','%Y-%m-%d'):
        try:return datetime.strptime(value.strip(),fmt).date().isoformat()
        except ValueError:pass
    raise RefreshError('Source date not recognized')

def _count(value):
    t=str(value or '').strip()
    return int(t) if t.isascii() and t.isdigit() else None

def _csv(data):
    if isinstance(data,bytes):
        if len(data)>2_000_000:raise RefreshError('Provider source exceeds size limit')
        try:data=data.decode('utf-8-sig')
        except UnicodeError:raise RefreshError('CSV encoding invalid') from None
    if '\x00' in data:raise RefreshError('CSV contains invalid bytes')
    rdr=csv.DictReader(io.StringIO(data))
    if not rdr.fieldnames or not {'Date','HomeTeam','AwayTeam','FTHG','FTAG','FTR'} <= set(rdr.fieldnames):
        raise RefreshError('Missing completed-match source columns')
    rows=list(rdr)
    if len(rows)>1000 or not rows:raise RefreshError('Source has invalid season row count')
    return rows

def _resolve(index, membership, league, raw_name):
    tid=_candidate_id(index,raw_name,league,membership,{})
    if tid is None:raise RefreshError(f'Unreviewed source team for {league}: {raw_name}')
    return tid

def _source_row(row, league, line_no, index, membership, as_of):
    h=str(row.get('HomeTeam') or '').strip();a=str(row.get('AwayTeam') or '').strip()
    if not h and not a:return None, 'EMPTY'
    if not h or not a:raise RefreshError(f'{league} row {line_no}: team missing')
    hg=_count(row.get('FTHG'));ag=_count(row.get('FTAG'));res=str(row.get('FTR') or '').strip()
    if hg is None and ag is None and not res:return None,'UNPLAYED'
    if hg is None or ag is None or res not in ('H','D','A'):
        raise RefreshError(f'{league} row {line_no}: partial or invalid final result')
    if hg>40 or ag>40 or (('H' if hg>ag else 'A' if hg<ag else 'D')!=res):
        raise RefreshError(f'{league} row {line_no}: final score/result inconsistent')
    day=parse_date(row.get('Date',''))
    if day>=as_of:raise RefreshError(f'{league} row {line_no}: result not strictly before cutoff')
    hid=_resolve(index,membership,league,h);aid=_resolve(index,membership,league,a)
    if hid==aid:raise RefreshError('Source home and away have same ID')
    return {'league':league,'season':SEASON,'match_date':day,'home_id':hid,
            'away_id':aid,'home_goals':str(hg),'away_goals':str(ag),
            'result':res,'source_row':str(line_no),
            'source_url':f'{SOURCE_PREFIX}{LEAGUES[league]}.csv',
            '_raw':row},'COMPLETED'

def _statistics(record):
    r=record.pop('_raw')
    for out,src in STAT_MAP.items():
        val=str(r.get(src) or '').strip()
        if out=='half_time_result':
            record[out]=val if val in ('H','D','A') else ''
        else:
            parsed=_count(val)
            record[out]=str(parsed) if parsed is not None and parsed<=100 else ''
    hh=_count(record.get('half_time_home_goals'))
    ha=_count(record.get('half_time_away_goals'))
    if hh is None or ha is None or hh>int(record['home_goals']) or ha>int(record['away_goals']):
        for x in ('half_time_home_goals','half_time_away_goals','half_time_result'):record[x]=''
    else:
        expected='H' if hh>ha else 'A' if hh<ha else 'D'
        if record.get('half_time_result')!=expected:record['half_time_result']=''
    hs=_count(record.get('home_shots'));a=_count(record.get('away_shots'))
    hst=_count(record.get('home_shots_on_target'));ast=_count(record.get('away_shots_on_target'))
    if hs is None or a is None or hst is None or ast is None or hst>hs or ast>a:
        for x in ('home_shots','away_shots','home_shots_on_target','away_shots_on_target'):record[x]=''
    return record

def _append_id(row):
    # Match registry's established identity basis; never guess repeated encounter.
    key=json.dumps([row[x] for x in ('league','season','home_id','away_id')],ensure_ascii=False)
    return str(uuid.uuid5(NAMESPACE,'dated-league-fixture:'+key))

def prepare_refresh(base_rows,base_meta,index,provided:dict[str,bytes],as_of:str,
                    *,strict_all=True,locked=True):
    """No files are downloaded. All 10 season CSVs should be supplied in one batch.

    locked=False is reserved for synthetic software tests, never CLI.
    Existing provider rows are reconciled by immutable source row AND match
    identity. A reordered, corrected or incomplete source blocks publication.
    """
    if locked and base_meta.get('sha256')!=HISTORICAL_SHA256:
        raise RefreshError('Frozen historical base digest mismatch')
    if base_meta.get('rows')!=len(base_rows) or not base_rows:
        raise RefreshError('Frozen historical provenance invalid')
    _validate_identity_source(index)
    if not isinstance(provided,dict) or not provided:
        raise RefreshError('No provider CSV files supplied; cannot claim fresh data')
    if set(provided)-set(LEAGUES):raise RefreshError('Unsupported source league')
    if strict_all and set(provided)!=set(LEAGUES):
        raise RefreshError('Incomplete ten-league refresh: '+','.join(sorted(set(LEAGUES)-set(provided))))
    try:as_of=date.fromisoformat(as_of).isoformat()
    except (ValueError,TypeError):raise RefreshError('Invalid as-of date') from None
    if max(r['match_date'] for r in base_rows)>=as_of:
        raise RefreshError('Cutoff predates some already-frozen historical results')
    members=_memberships(index,SEASON)
    if not isinstance(members,dict):raise RefreshError('Current season membership missing')
    prev={(r['league'],r['source_row']):r for r in base_rows if r['season']==SEASON}
    all_pairs={(r['league'],r['season'],r['home_id'],r['away_id']) for r in base_rows}
    all_ids={r['fixture_id'] for r in base_rows}
    additions=[]; audits={};seen_pairs=set()
    for league in sorted(provided):
        raw_bytes=provided[league]
        parsed=_csv(raw_bytes)
        old_seen=set();new=0;upcoming=0;empty=0
        for line_no,raw in enumerate(parsed,2):
            record,kind=_source_row(raw,league,line_no,index,members,as_of)
            if kind=='EMPTY':empty+=1;continue
            if kind=='UNPLAYED':upcoming+=1;continue
            pair=(record['league'],record['season'],record['home_id'],record['away_id'])
            if pair in seen_pairs:raise RefreshError(f'{league} repeated same directed pairing requires review')
            seen_pairs.add(pair)
            old=prev.get((league,str(line_no)))
            if old is not None:
                match_keys=('league','season','match_date','home_id','away_id','home_goals','away_goals','result','source_url')
                if any(str(old.get(k,''))!=str(record.get(k,'')) for k in match_keys):
                    raise RefreshError(f'{league} source row {line_no} changed frozen match; manual reconciliation required')
                old_seen.add(str(line_no));continue
            if pair in all_pairs:
                raise RefreshError(f'{league} new match pair already exists; source reordered or playoff duplicate')
            if record['match_date']>=as_of:raise RefreshError('Non-historical source date')
            item=_statistics(record)
            item['fixture_id']=_append_id(item)
            if item['fixture_id'] in all_ids:
                raise RefreshError('New fixture UUID collided with existing registry')
            all_ids.add(item['fixture_id']);all_pairs.add(pair)
            additions.append(item);new+=1
        old_expected={src for lg,src in prev if lg==league}
        if old_seen!=old_expected:
            raise RefreshError(f'{league} full-season source incomplete: only {len(old_seen)}/{len(old_expected)} frozen rows matched')
        audits[league]={'frozen_rows_reconciled':len(old_seen),'new_completed':new,
                        'unplayed_ignored':upcoming,'empty_ignored':empty,
                        'provider_file_sha256':hashlib.sha256(raw_bytes).hexdigest(),
                        'provider_fetch_independently_verified':False,
                        'source':'USER_OR_OPERATOR_SUPPLIED_PROVIDER_CSV_NOT_LIVE_VERIFIED'}
    # All source files must validate before a single result can be published.
    additions.sort(key=lambda r:(r['match_date'],r['fixture_id']))
    output_rows=sorted(base_rows+additions,key=lambda r:(r['match_date'],r['fixture_id']))
    return output_rows, {'version':VERSION,'status':'STAGED_UNVERIFIED_SOURCE_FILES',
            'base_sha256':base_meta['sha256'],'base_rows':len(base_rows),
            'source_season':SEASON,'as_of_exclusive':as_of,
            'leagues_provided':len(provided),'leagues_expected':len(LEAGUES),
            'source_completeness':'TEN_LEAGUES' if len(provided)==len(LEAGUES) else 'PARTIAL_TEST_ONLY',
            'appended':len(additions),'total_rows':len(output_rows),
            'source_file_audit':audits,
            'independent_source_verification':False,
            'retrospective_model_acceptance_transferred':False,
            'probability_recommendations_authorized':False,
            'main_or_production_modified':False}

def export_snapshot(base_rows,extended,report,output:Path):
    if report['base_rows']!=len(base_rows) or report['total_rows']!=len(extended):
        raise RefreshError('Report and output count mismatch')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    fields=list(base_rows[0]);fields=[f for f in fields if not f.startswith('_')]
    for r in extended:
        if set(f for f in r if not f.startswith('_'))-set(fields):
            raise RefreshError('Unknown output column')
    buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=fields,lineterminator='\n')
    w.writeheader();w.writerows([{k:r.get(k,'') for k in fields} for r in extended])
    data=buf.getvalue().encode('utf-8')
    report={**report,'extended_history_sha256':hashlib.sha256(data).hexdigest()}
    # Validates the actual on-disk exported file below, not silently success.
    temp=output/'extended_history.csv.tmp';temp.write_bytes(data)
    r,src=load_history(temp)
    if len(r)!=len(extended) or src['sha256']!=report['extended_history_sha256']:
        temp.unlink(missing_ok=True);raise RefreshError('Export re-read validation failed')
    temp.replace(output/'extended_history.csv')
    (output/'refresh_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

def main(argv=None):
    p=argparse.ArgumentParser(description='OFFLINE 10-league full-season source refresh; not official validation')
    p.add_argument('--base',required=True)
    p.add_argument('--identity-index',required=True)
    inputs=p.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--sources-dir',help='All 10 original provider current-season CSV files')
    inputs.add_argument('--refreshed-history',help='Preferred: existing GitHub weekly job regenerated historical_results.csv')
    p.add_argument('--pipeline-audit',help='Required with --refreshed-history: historical_results_audit.json')
    p.add_argument('--source-audit',help='Required with --refreshed-history: source_audit.csv')
    p.add_argument('--as-of',required=True,help='ISO YYYY-MM-DD, no same-day results')
    p.add_argument('--output',required=True)
    args=p.parse_args(argv)
    base,meta=load_history(args.base)
    index=json.loads(Path(args.identity_index).read_text(encoding='utf-8'))
    if args.refreshed_history:
        if not args.pipeline_audit or not args.source_audit:
            raise RefreshError('Regenerated weekly data requires both pipeline/source audits')
        extended,new_meta=load_history(args.refreshed_history)
        pipeline=json.loads(Path(args.pipeline_audit).read_text(encoding='utf-8'))
        with Path(args.source_audit).open(encoding='utf-8-sig',newline='') as f:
            sources=list(csv.DictReader(f))
        audit=reconcile_existing_weekly_pipeline(base,meta,extended,new_meta,index,
                                                 pipeline,sources,args.as_of)
    else:
        source_dir=Path(args.sources_dir)
        if not source_dir.is_dir():raise RefreshError('Source directory missing')
        files={league:(source_dir/(league+'.csv')).read_bytes() for league in LEAGUES}
        extended,audit=prepare_refresh(base,meta,index,files,args.as_of)
    audit=export_snapshot(base,extended,audit,Path(args.output))
    print(json.dumps({'status':audit['status'],'appended':audit['appended'],
                      'leagues':audit['leagues_provided'],'independent_verification':False,
                      'extended_sha256':audit['extended_history_sha256']}))
def reconcile_existing_weekly_pipeline(base_rows,base_meta,new_rows,new_meta,index,
                                      pipeline_audit,source_audit,as_of):
    """Preferred path: existing weekly GitHub job's regenerated history+audits.

    No extra scraper. Output may only extend the protected base with completed
    same-season, known-club, unique-pair results. The old 4,413 rows must be
    byte-field identical after CSV parsing. GitHub workflow green alone is not
    independent proof that third-party results are factually correct.
    """
    if base_meta.get('sha256')!=HISTORICAL_SHA256 or len(base_rows)!=4413:
        raise RefreshError('Frozen historical base digest mismatch')
    _validate_identity_source(index)
    if new_meta.get('rows')!=len(new_rows) or not isinstance(new_meta.get('sha256'),str):
        raise RefreshError('Regenerated snapshot provenance inconsistent')
    if not isinstance(pipeline_audit,dict) or not isinstance(source_audit,list):
        raise RefreshError('Original pipeline audits required')
    if (pipeline_audit.get('errors')!=[] or pipeline_audit.get('linked')!=len(new_rows)
        or pipeline_audit.get('expected_rows')!=len(new_rows) or pipeline_audit.get('sources')!=20):
        raise RefreshError('Regenerated pipeline audit not accepted')
    source_keys={(x.get('league'),x.get('season')) for x in source_audit
                 if x.get('status')=='OK'}
    if (len(source_audit)!=20 or len(source_keys)!=20 or any((l,s) not in source_keys
           for l in LEAGUES for s in ('2025-2026','2026-2027')) or any(
            x.get('url') != ('https://www.football-data.co.uk/mmz4281/'
                 + ('2627' if x.get('season')=='2026-2027' else '2526')
                 + '/' + LEAGUES.get(x.get('league'),'INVALID') + '.csv')
            for x in source_audit)):
        raise RefreshError('Ten-league two-season source audit incomplete')
    try:cutoff=date.fromisoformat(as_of).isoformat()
    except (ValueError,TypeError):raise RefreshError('Invalid as-of date') from None
    if max(r['match_date'] for r in base_rows)>=cutoff:
        raise RefreshError('Cutoff predates the frozen baseline')
    old={r['fixture_id']:r for r in base_rows}
    new={r['fixture_id']:r for r in new_rows}
    if len(new)!=len(new_rows) or not set(old).issubset(new):
        raise RefreshError('Regenerated history removed or duplicated frozen match')
    expected_fields=[k for k in base_rows[0] if not k.startswith('_')]
    for fid,r in old.items():
        if any(str(r.get(k,''))!=str(new[fid].get(k,'')) for k in expected_fields):
            raise RefreshError('Regenerated pipeline altered a frozen match; reconcile, do not overwrite')
    memberships=_memberships(index,SEASON)
    known_pairs={(r['league'],r['season'],r['home_id'],r['away_id']) for r in base_rows}
    additions=[]
    for fid,r in new.items():
        if fid in old:continue
        if r.get('league') not in LEAGUES or r.get('season')!=SEASON:
            raise RefreshError('Added match outside current target season/leagues')
        if r['match_date']>=cutoff:raise RefreshError('New completed result is not before cutoff')
        if r['home_id'] not in memberships.get(r['league'],set()) or r['away_id'] not in memberships.get(r['league'],set()):
            raise RefreshError('New source team has no reviewed canonical membership')
        k=(r['league'],r['season'],r['home_id'],r['away_id'])
        if k in known_pairs:raise RefreshError('Repeated pairing requires explicit identity review')
        known_pairs.add(k)
        if fid!=_append_id(r):raise RefreshError('New fixture ID differs from canonical identity basis')
        if r.get('source_url')!=SOURCE_PREFIX+LEAGUES[r['league']]+'.csv':
            raise RefreshError('Unrecognized result source URL')
        additions.append(r)
    by_league=Counter(r['league'] for r in additions)
    return {'version':VERSION,'status':'STAGED_UNVERIFIED_SOURCE_FILES',
            'base_sha256':base_meta['sha256'],'base_rows':len(base_rows),
            'source_season':SEASON,'as_of_exclusive':cutoff,
            'leagues_provided':10,'leagues_expected':10,'source_completeness':'TEN_LEAGUES',
            'appended':len(additions),'total_rows':len(new_rows),
            'source_file_audit':{lg:{'new_completed':by_league[lg],
                'source':'EXISTING_GITHUB_WEEKLY_PIPELINE_REGENERATED_CSV',
                'provider_fetch_independently_verified':False} for lg in LEAGUES},
            'pipeline_audit_rechecked':True,
            'regenerated_input_sha256':new_meta['sha256'],
            'independent_source_verification':False,
            'retrospective_model_acceptance_transferred':False,
            'probability_recommendations_authorized':False,
            'main_or_production_modified':False}


if __name__=='__main__':main()
