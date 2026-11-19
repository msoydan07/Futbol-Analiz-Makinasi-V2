"""Optional read-only public results witness for 2.6.3's locked 4,618 snapshot.

The 10 Football-Data CSVs are SECONDARY provider evidence, not official result
confirmation. No bookmaker calls, no model decisions, no raw private data upload.
Checks missing completed-match dates after each league's last frozen date.
"""
from __future__ import annotations
import csv,hashlib,io,json,urllib.request
from datetime import date,datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit

SOURCES={'ENG1':'E0','ENG2':'E1','GER1':'D1','ESP1':'SP1','ITA1':'I1',
         'FRA1':'F1','NED1':'N1','TUR1':'T1','POR1':'P1','BEL1':'B1'}
BASE='https://www.football-data.co.uk/mmz4281/2627/'
MIN_FT_BY_NOV8={'ENG1':100,'ENG2':180,'GER1':81,'ESP1':119,'ITA1':110,
                'FRA1':90,'NED1':108,'TUR1':99,'POR1':98,'BEL1':99}
COLUMNS={'Date','HomeTeam','AwayTeam','FTHG','FTAG','FTR'}
class ProviderBlocked(ValueError): pass

def parse_day(s):
    for fmt in ('%d/%m/%Y','%d/%m/%y','%Y-%m-%d'):
        try:return datetime.strptime(str(s).strip(),fmt).date()
        except ValueError:pass
    raise ProviderBlocked('INVALID_SOURCE_DATE')

def witness_source(league,raw,last_frozen,target_day):
    """Compare complete FT season counts, then inspect strictly intervening days."""
    if league not in SOURCES: raise ProviderBlocked('UNSUPPORTED_LEAGUE')
    if not isinstance(raw,(bytes,bytearray)) or not 400 <= len(raw)<=2_000_000:
        raise ProviderBlocked('PROVIDER_SOURCE_EMPTY_OR_OVERSIZE')
    try:s=raw.decode('utf-8-sig')
    except UnicodeDecodeError as e:raise ProviderBlocked('PROVIDER_ENCODING_INVALID') from e
    r=csv.DictReader(io.StringIO(s))
    if not r.fieldnames or not COLUMNS.issubset(r.fieldnames):raise ProviderBlocked('MISSING_SOURCE_COLUMNS')
    rows=list(r)
    if not 50<=len(rows)<=1100:raise ProviderBlocked('PROVIDER_SEASON_COVERAGE_TOO_SMALL_OR_LARGE')
    last=parse_day(last_frozen);day=parse_day(target_day)
    if not last<day:raise ProviderBlocked('TARGET_NOT_AFTER_FROZEN_DATE')
    seen=set();completed=0;new=[];before=0;no_result=0
    for idx,x in enumerate(rows,2):
        h=(x.get('HomeTeam') or '').strip();a=(x.get('AwayTeam') or '').strip()
        if not h and not a:continue
        if not h or not a or h.casefold()==a.casefold():raise ProviderBlocked('PROVIDER_INVALID_TEAMS')
        d=parse_day(x.get('Date'))
        hg,ag=(x.get('FTHG') or '').strip(),(x.get('FTAG') or '').strip()
        rt=(x.get('FTR') or '').strip()
        if not hg and not ag and not rt: no_result+=1;continue
        if not hg.isascii() or not ag.isascii() or not hg.isdigit() or not ag.isdigit() or rt not in ('H','D','A'):
            raise ProviderBlocked('PROVIDER_INCOMPLETE_RESULT')
        hi,ai=int(hg),int(ag)
        if max(hi,ai)>30 or rt!=('H' if hi>ai else 'D' if hi==ai else 'A'):
            raise ProviderBlocked('PROVIDER_SCORE_RESULT_MISMATCH')
        if d>=day: raise ProviderBlocked('PROVIDER_FUTURE_SCORE_LEAK')
        key=(h.casefold(),a.casefold())
        if key in seen:raise ProviderBlocked('DUPLICATE_DIRECTED_FIXTURE')
        seen.add(key);completed+=1
        if d<=last:before+=1
        if last<d<day:
            new.append({'day':d.isoformat(),'home':h,'away':a,'home_goals':hi,'away_goals':ai,'source_csv_line':idx})
    if before<MIN_FT_BY_NOV8[league]:
        raise ProviderBlocked('PROVIDER_BEHIND_FROZEN_SNAPSHOT')
    return {'schema':'263_SECONDARY_FOOTBALL_DATA_2627_GAP_WITNESS_V1','league':league,
            'provider':'football-data.co.uk','source_url':BASE+SOURCES[league]+'.csv',
            'source_sha256':hashlib.sha256(raw).hexdigest(),
            'full_time_source_rows':completed,'prior_or_equal_frozen_rows':before,
            'unplayed_rows':no_result,'new_full_time_in_gap':new,
            'status':'PROVIDER_REPORTS_UNARCHIVED_COMPLETED_RESULTS' if new else 'PROVIDER_OBSERVED_NO_NEW_RESULTS',
            'official_federation_results_verified':False,'provider_completeness_independently_verified':False,
            'forecast_source_admitted':False,'M4_or_seals_modified':False}

def fetch_source(league,*,fetcher=None):
    if league not in SOURCES:raise ProviderBlocked('UNSUPPORTED_LEAGUE')
    url=BASE+SOURCES[league]+'.csv'
    if fetcher is not None:return witness_only_fetch(url,fetcher)
    req=urllib.request.Request(url,headers={'User-Agent':'2.6.3-private-research-gap-audit/1.0'})
    with urllib.request.urlopen(req,timeout=25) as response:
        actual=response.geturl();u=urlsplit(actual)
        if u.scheme!='https' or (u.hostname or '').lower() not in ('www.football-data.co.uk','football-data.co.uk'):
            raise ProviderBlocked('UNTRUSTED_PROVIDER_REDIRECT')
        if response.status!=200:raise ProviderBlocked('PROVIDER_HTTP_ERROR')
        raw=response.read(2_000_001)
    if len(raw)>2_000_000:raise ProviderBlocked('PROVIDER_DOWNLOAD_OVERLIMIT')
    return raw

def witness_only_fetch(url,fn):
    observed_url,raw=fn(url)
    if observed_url!=url:raise ProviderBlocked('INJECTED_REDIRECT_NOT_EXPECTED')
    return raw

def audit_ten(latest_by_league,target_day,*,fetcher=None):
    if set(latest_by_league)!=set(SOURCES):raise ProviderBlocked('LATEST_10_LEAGUES_REQUIRED')
    out={}
    for league in sorted(SOURCES):
        out[league]=witness_source(league,fetch_source(league,fetcher=fetcher),
                                  latest_by_league[league],target_day)
    return {'schema':'263_PUBLIC_PROVIDER_10_LEAGUE_GAP_WITNESS_V1',
            'target_day':target_day,'provider_reports':out,
            'unarchived_completed_rows':sum(len(x['new_full_time_in_gap']) for x in out.values()),
            'source_note':'SECONDARY_PROVIDER_NOT_OFFICIAL_FEDERATION_NOT_A_LIVE_MODEL_GATE',
            'production_forecast_allowed':False}

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--latest-by-league-json',required=True);a.add_argument('--target-day',required=True);a.add_argument('--out',required=True)
    p=a.parse_args()
    latest=json.loads(Path(p.latest_by_league_json).read_text(encoding='utf-8'))
    obj=audit_ten(latest,p.target_day)
    Path(p.out).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'target_day':p.target_day,'unarchived_completed_rows':obj['unarchived_completed_rows'],'production_forecast_allowed':False}))
