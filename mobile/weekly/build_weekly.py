#!/usr/bin/env python3
"""Candidate replacement for research branch mobile/weekly/build_weekly.py.
Packaging gate only. Reviewed source claims are not independent authentication.
"""
import csv,datetime as dt,hashlib,io,json,re
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
L=set('ENG1 ENG2 GER1 ESP1 ITA1 FRA1 NED1 TUR1 POR1 BEL1'.split())
DOMAINS=dict(ENG1='premierleague.com',ENG2='efl.com',GER1='bundesliga.com',ESP1='laliga.com',ITA1='legaseriea.it',FRA1='ligue1.com',NED1='eredivisie.nl',TUR1='tff.org',POR1='ligaportugal.pt',BEL1='proleague.be')
TZ=ZoneInfo('Europe/Istanbul')
BASE=Path('mobile/weekly')
def require(ok,why):
    if not ok: raise ValueError(why)
def sha(b): return hashlib.sha256(b).hexdigest()
def utc(s):
    x=dt.datetime.fromisoformat(s.replace('Z','+00:00'))
    require(x.tzinfo is not None,'timezone missing')
    return x.astimezone(dt.timezone.utc)
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def official(u,l):
    if not isinstance(u,str) or l not in DOMAINS: return False
    x=urlsplit(u); h=x.hostname or ''; d=DOMAINS[l]
    return x.scheme=='https' and not x.username and not x.password and (h==d or h.endswith('.'+d))
def build(m,now):
    start=dt.date.fromisoformat(m['week_start']); end=start+dt.timedelta(days=6)
    require(start.weekday()==2 and start==now.astimezone(TZ).date(),'publish only on the actual Wednesday')
    require(m['schema']=='KAHIN_REVIEWED_WEEKLY_INPUT_V1','manifest schema')
    require(set(m['coverage'])==L and all(v in ('LISTED','NO_FIXTURES') for v in m['coverage'].values()),'all ten leagues must be reviewed')
    require(set(m['league_source_urls'])==L and all(official(u,l) for l,u in m['league_source_urls'].items()),'league source evidence')
    hp=m['history_path']; pp=m['provenance_path']
    require(re.fullmatch(r'data/research_263/[A-Za-z0-9_.-]+\.csv',hp) and re.fullmatch(r'data/research_263/[A-Za-z0-9_.-]+\.json',pp),'history scope')
    hist=Path(hp).read_bytes(); pv=read(pp)
    require(pv['source_snapshot_path']==hp and sha(hist)==pv['source_snapshot_sha256'] and pv['all_source_scores_identical'] is True,'history evidence mismatch')
    registry=read('experiments/263/evidence/identity_index_263.json')
    rows=list(csv.DictReader(io.StringIO(hist.decode('utf-8'))))
    require(len(rows)==pv['usable_total_rows'],'history count')
    seen=set(); counts={l:0 for l in L}; latest={}
    for r in rows:
        date=dt.date.fromisoformat(r['match_date']); h,a=int(r['home_goals']),int(r['away_goals'])
        require(r['fixture_id'] and r['fixture_id'] not in seen and r['league'] in L and date<start and min(h,a)>=0 and r['result']==('H' if h>a else 'A' if h<a else 'D') and r['home_id']!=r['away_id'] and all(i in registry['teams'] for i in (r['home_id'],r['away_id'])),'history row')
        seen.add(r['fixture_id']); counts[r['league']]+=1;latest[r['league']]=max(date,latest.get(r['league'],date))
    require(min(counts.values())>=60,'history coverage')
    reviews=m.get('results_reviews',{}); require(isinstance(reviews,dict) and set(reviews)<=L,'results review leagues')
    checked={}
    for l,r in reviews.items():
        require(isinstance(r,dict) and r.get('from_date')==str(latest[l]) and r.get('through_date')==str(start-dt.timedelta(days=1)) and type(r.get('missing_completed_matches')) is int and r['missing_completed_matches']==0 and r.get('full_window_reviewed') is True and official(r.get('source_url'),l),'results review evidence')
        stamp=utc(r['reviewed_at_utc']);require(stamp.astimezone(TZ).date()==start and stamp<=now,'results review time')
        checked[l]={**r,'reviewed_at_utc':stamp.isoformat().replace('+00:00','Z')}
    fs=m['fixtures']; require(isinstance(fs,list) and len(fs)<=300,'fixture count')
    keys=set(); fixtures=[]
    for f in fs:
        ko=utc(f['kickoff_utc']); day=ko.astimezone(TZ).date()
        require(f['league'] in L and f['fixture_id'] and f['fixture_id'] not in seen and start<=day<=end and ko>now and f['home_id']!=f['away_id'] and official(f['source_url'],f['league']),'fixture invalid')
        yr=day.year-(day.month<7); mem=registry['season_memberships'][f'{yr}-{yr+1}'][f['league']]
        require(all(i in mem and i in registry['teams'] for i in (f['home_id'],f['away_id'])) and ((day-latest[f['league']]).days<=10 or f['league'] in checked),'fixture team/freshness')
        k=(f['league'],ko,f['home_id'],f['away_id']);require(k not in keys,'duplicate fixture')
        seen.add(f['fixture_id']);keys.add(k);fixtures.append({**f,'kickoff_utc':ko.isoformat().replace('+00:00','Z')})
    for l in L:require((m['coverage'][l]=='LISTED')==any(f['league']==l for f in fixtures),'coverage conflict')
    source_note='Reviewed fixture and results manifest (source URLs retained); history: two public secondary score sources, not federation verification. '+json.dumps(m['league_source_urls'],ensure_ascii=False,sort_keys=True)
    p=dict(schema='KAHIN_WEEKLY_DATA_V1',week_start=start.isoformat(),week_end=end.isoformat(),created_at_utc=now.isoformat().replace('+00:00','Z'),source_note=source_note,history_csv=hist.decode('utf-8'),registry=registry,coverage=m['coverage'],fixtures=fixtures,results_reviews=checked)
    raw=json.dumps(p,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    return dict(schema='KAHIN_WEEKLY_ENVELOPE_V1',payload=raw,sha256=sha(raw.encode()))
def protect(old,new):
    require(old['sha256']==sha(old['payload'].encode()),'previous package digest')
    p=json.loads(old['payload']); n=json.loads(new['payload'])
    require(p['week_start']<n['week_start'],'same/older week must not overwrite published pack')
    prev={r['fixture_id']:r for r in csv.DictReader(io.StringIO(p['history_csv']))}
    nxt={r['fixture_id']:r for r in csv.DictReader(io.StringIO(n['history_csv']))}
    require(all(nxt.get(k)==v for k,v in prev.items()),'old history modified or lost')
if __name__=='__main__':
    pack=build(read(BASE/'input.json'),dt.datetime.now(dt.timezone.utc))
    out=BASE/'latest.json'
    if out.exists(): protect(read(out),pack)
    tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(pack,ensure_ascii=False),encoding='utf-8');tmp.replace(out)
    print('Kahin package created',pack['sha256'])
