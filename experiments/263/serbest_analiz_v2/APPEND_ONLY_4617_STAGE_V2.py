#!/usr/bin/env python3
"""Research-only append preview: immutable SHA-pinned 4617 base plus 10 public score feeds.

Never promote this output into main M4 or old seals. Scores and club identities
must be independently accepted before this can be used for official pre-KO.
"""
import argparse,csv,hashlib,io,json,sys
from datetime import date
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from season_refresh_263 import (LEAGUES,SEASON,SOURCE_PREFIX,_csv,_source_row,
                                _statistics,_append_id,parse_date,RefreshError)
from mackolik_identity_gate_263 import _memberships,_validate_identity_source

PIN='637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89'
EXPECTED_N=4617

def read_base(path):
    b=Path(path).read_bytes()
    if hashlib.sha256(b).hexdigest()!=PIN:raise RefreshError('BASE_4617_SHA_CHANGED')
    rows=list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))))
    if len(rows)!=EXPECTED_N or len({r['fixture_id'] for r in rows})!=EXPECTED_N:
        raise RefreshError('BASE_4617_ROWS_OR_IDS_INVALID')
    return rows

def create(base,index,raw_files,cutoff):
    if set(raw_files)!=set(LEAGUES):raise RefreshError('TEN_LEAGUE_SOURCES_REQUIRED')
    _validate_identity_source(index)
    members=_memberships(index,SEASON)
    fields=list(base[0])
    bykey={};by_pair={};all_ids=set()
    for r in base:
        key=tuple(r[k] for k in ('league','season','match_date','home_id','away_id'))
        pair=tuple(r[k] for k in ('league','season','home_id','away_id'))
        if key in bykey or pair in by_pair or r['fixture_id'] in all_ids:
            raise RefreshError('BASE_DUPLICATE_MATCH_IDENTITY')
        bykey[key]=r;by_pair[pair]=r;all_ids.add(r['fixture_id'])
    new=[];audit={};seen=set()
    for league in sorted(LEAGUES):
        content=raw_files[league]
        records=_csv(content)
        old_verified=0;added=0;future_skipped=0;unplayed=0;latest=None
        for lineno,raw in enumerate(records,2):
            if not (str(raw.get('HomeTeam') or '').strip() or str(raw.get('AwayTeam') or '').strip()):
                continue
            if (raw.get('FTR') or '').strip() in ('H','D','A') and parse_date(raw.get('Date',''))>=cutoff:
                future_skipped+=1;continue
            r,kind=_source_row(raw,league,lineno,index,members,cutoff)
            if kind=='UNPLAYED':unplayed+=1;continue
            if kind=='EMPTY':continue
            key=tuple(r[k] for k in ('league','season','match_date','home_id','away_id'))
            pair=tuple(r[k] for k in ('league','season','home_id','away_id'))
            if key in seen:raise RefreshError('PROVIDER_DUPLICATE_SAME_GAME:'+league)
            seen.add(key)
            latest=max(latest or r['match_date'],r['match_date'])
            if key in bykey:
                old=bykey[key]
                if any(str(old[k])!=str(r[k]) for k in ('home_goals','away_goals','result')):
                    raise RefreshError('PROVIDER_CONFLICTS_WITH_ACCEPTED_SCORE:'+league+':'+r['match_date'])
                old_verified+=1
                continue
            if pair in by_pair:raise RefreshError('PROVIDER_REVISED_ACCEPTED_MATCH_DATE:'+league)
            newrow=_statistics(r)
            fid=_append_id(newrow)
            if fid in all_ids:raise RefreshError('NEW_MATCH_FIXTURE_ID_COLLISION')
            newrow['fixture_id']=fid
            bykey[key]=newrow;by_pair[pair]=newrow;all_ids.add(fid)
            new.append(newrow);added+=1
        required=[r for r in base if r['league']==league and r['season']==SEASON
                  and r.get('source_url','').startswith(SOURCE_PREFIX) and r['match_date']<cutoff]
        audit[league]={'new_completed':added,'accepted_provider_matches_rescored':old_verified,
             'existing_provider_rows_expected':len(required),'latest_public_completed_date':latest,
             'source_sha256':hashlib.sha256(content).hexdigest(),
             'source_grade':'PUBLIC_SECONDARY_NOT_OFFICIAL','today_or_future_ignored':future_skipped,
             'unplayed_ignored':unplayed}
        if old_verified < len(required):
            raise RefreshError('PROVIDER_MISSING_PREVIOUSLY_ACCEPTED_MATCHES:'+league+':'+str(old_verified)+'/'+str(len(required)))
    new.sort(key=lambda r:(r['match_date'],r['fixture_id']))
    result=sorted(base+new,key=lambda r:(r['match_date'],r['fixture_id']))
    if len(result)!=len(base)+len(new):raise RefreshError('UNEXPECTED_COUNT')
    buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=fields,lineterminator='\n',extrasaction='ignore')
    writer.writeheader();writer.writerows(result)
    bytes_=buf.getvalue().encode('utf-8')
    check=list(csv.DictReader(io.StringIO(bytes_.decode('utf-8'))))
    lookup={r['fixture_id']:r for r in check}
    if len(lookup)!=len(check):raise RefreshError('STAGED_DUPLICATE_FIXTURE_ID')
    for r in base:
        existing=lookup.get(r['fixture_id'])
        if not existing or any(existing.get(k,'')!=r.get(k,'') for k in fields):
            raise RefreshError('APPEND_ONLY_BASE_CHANGED')
    return bytes_,{'schema':'263_4617_PLUS_PROVIDER_RESEARCH_STAGE_V2',
        'status':'STAGED_UNVERIFIED_NOT_PERMITTED_FOR_OFFICIAL_PREKO_SEALS',
        'cutoff_exclusive':cutoff,'base_rows':len(base),'added_rows':len(new),'staged_rows':len(check),
        'source_sha256':PIN,'staged_sha256':hashlib.sha256(bytes_).hexdigest(),
        'per_league':audit,'not_officially_score_verified':True,
        'forecast_seals_changed':False,'original_model_changed':False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base',required=True);p.add_argument('--registry',required=True)
    p.add_argument('--sources-dir',required=True);p.add_argument('--asof',required=True)
    p.add_argument('--out-dir',required=True)
    a=p.parse_args()
    base=read_base(a.base)
    index=json.loads(Path(a.registry).read_text(encoding='utf-8'))
    supplied={league:(Path(a.sources_dir)/(league+'.csv')).read_bytes() for league in LEAGUES}
    result,audit=create(base,index,supplied,date.fromisoformat(a.asof).isoformat())
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/'research_appended_history_4617.csv').write_bytes(result)
    (out/'append_preview_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    print('RESEARCH_APPEND_PREVIEW',json.dumps({'total':audit['staged_rows'], 'new':audit['added_rows'],
          'per_league':{k:v['new_completed'] for k,v in audit['per_league'].items()},
          'staged_sha256':audit['staged_sha256']},ensure_ascii=False))
if __name__=='__main__': main()
