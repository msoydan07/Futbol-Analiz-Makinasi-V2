"""One-time independent score concordance for 83 Nov 20–22 league matches.

Cross-check Football-Data with ESPN's distinct public scoreboard. Fuzzy team
names are only a discovery convenience: each match must be uniquely paired
within the same league + local date, separated from the runner-up, and the
independent final home/away score MUST agree. No official federation claim.
Never overwrites the protected 4,617 source or historical prematch records.
"""
from __future__ import annotations
import csv, hashlib, io, json, unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from rapidfuzz import fuzz
from scipy.optimize import linear_sum_assignment

STAGE_SHA='37bf74e820df85325213c2e0ef8ce9a88a16c1f452edf5bd2a41814f10f261bd'
OLD_SHA='637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89'
CODES={'ENG1':'E0','ENG2':'E1','GER1':'D1','ESP1':'SP1','ITA1':'I1',
       'FRA1':'F1','NED1':'N1','TUR1':'T1','POR1':'P1','BEL1':'B1'}
# Reviewed one-to-one team name aliases, NEVER inferred from a matching score.
REVIEWED={('ESP1','La Coruna'):'Deportivo'}
PUB_A='https://www.football-data.co.uk/mmz4281/2627/'
PUB_B='https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates=202611'

def fail(reason):
    raise ValueError('SCORE_SOURCE_NOT_ACCEPTED:'+reason)

def norm(x):
    x=unicodedata.normalize('NFKD',str(x).casefold())
    return ''.join(ch for ch in x if not unicodedata.combining(ch) and (ch.isalnum() or ch.isspace())).strip()

def score_name(league,source,other):
    source=REVIEWED.get((league,source),source)
    return fuzz.WRatio(norm(source),norm(other))

def check(source_dir,espn_file,stage_file,preview_audit_file):
    stage_bytes=Path(stage_file).read_bytes()
    if hashlib.sha256(stage_bytes).hexdigest()!=STAGE_SHA:fail('STAGED_SNAPSHOT_SHA')
    stage=list(csv.DictReader(io.StringIO(stage_bytes.decode('utf-8-sig'))))
    if len(stage)!=4700 or len(set(r['fixture_id'] for r in stage))!=4700:fail('STAGE_COUNT_OR_IDS')
    prior=[r for r in stage if not(r['season']=='2026-2027' and r['match_date']>='2026-11-09')]
    appended=[r for r in stage if (r['season']=='2026-2027' and r['match_date']>='2026-11-09')]
    if len(prior)!=4617 or len(appended)!=83:fail('OLD_OR_NEW_COHORT_COUNT')
    if any(r['match_date']>'2026-11-22' for r in appended):fail('TOO_RECENT_OR_SAME_DAY_RESULT')
    source_audit=json.loads(Path(preview_audit_file).read_text(encoding='utf-8'))
    if (source_audit.get('staged_sha256')!=STAGE_SHA
        or source_audit.get('source_sha256')!=OLD_SHA
        or source_audit.get('base_rows')!=4617
        or source_audit.get('added_rows')!=83
        or source_audit.get('staged_rows')!=4700):
        fail('UPSTREAM_APPEND_AUDIT_INVALID')
    data=json.loads(Path(espn_file).read_text(encoding='utf-8'))
    if set(data.get('leagues',{}))!=set(CODES):fail('ESPN_TEN_LEAGUES_REQUIRED')
    ledger=[];fetched_sha={}
    for lg in sorted(CODES):
        provider_file=Path(source_dir)/(lg+'.csv')
        content=provider_file.read_bytes()
        expected=source_audit['per_league'][lg]['source_sha256']
        sha=hashlib.sha256(content).hexdigest()
        if sha!=expected:fail('PROVIDER_SHA_CHANGED_'+lg)
        fetched_sha[lg]=sha
        provider=list(csv.DictReader(io.StringIO(content.decode('utf-8-sig'))))
        public_a=defaultdict(list)
        for row in provider:
            if row.get('FTR') not in ('H','D','A'):continue
            day=datetime.strptime(row['Date'],'%d/%m/%Y').date().isoformat()
            if not('2026-11-20'<=day<='2026-11-22'):continue
            h,a=int(row['FTHG']),int(row['FTAG'])
            if row['FTR']!=('H' if h>a else 'A' if h<a else 'D'):
                fail('PROVIDER_RESULT_FIELD_CONFLICT_'+lg)
            public_a[day].append({'home':row['HomeTeam'],'away':row['AwayTeam'],'h':h,'a':a})
        src=data['leagues'][lg]
        if src.get('status')!='FETCHED':fail('ESPN_SOURCE_NOT_FETCHED_'+lg)
        public_b=defaultdict(list)
        for e in src.get('matches_in_window',[]):
            day=str(e.get('date',''))[:10]
            if not('2026-11-20'<=day<='2026-11-22') or not e.get('completed'):
                continue
            sides={s['side']:s for s in e['sides']}
            if set(sides)!={'home','away'}:fail('ESPN_HOME_AWAY_MISSING_'+lg)
            if not all(x.get('score') not in (None,'') for x in sides.values()):
                fail('ESPN_COMPLETED_SCORE_MISSING_'+lg)
            public_b[day].append({'home':sides['home']['name'],'away':sides['away']['name'],
                    'h':int(sides['home']['score']),'a':int(sides['away']['score']),
                    'id':e['event_id']})
        if set(public_a)!=set(public_b):fail('LEAGUE_MATCH_DAYS_NOT_EQUAL_'+lg)
        expected_added=source_audit['per_league'][lg]['new_completed']
        if sum(len(v) for v in public_a.values())!=expected_added:
            fail('PROVIDER_AND_STAGE_NEW_MATCH_COUNT_CONFLICT_'+lg)
        for day in sorted(public_a):
            a,b=public_a[day],public_b[day]
            if len(a)!=len(b):fail('DAY_MATCH_COUNTS_DIFFER_'+lg+'_'+day)
            matrix=[[(score_name(lg,x['home'],y['home'])+
                      score_name(lg,x['away'],y['away']))/2 for y in b] for x in a]
            ai,bi=linear_sum_assignment([[-v for v in row] for row in matrix])
            for i,j in zip(ai,bi):
                row=a[i];other=b[j];similar=matrix[i][j]
                alternatives=sorted(matrix[i],reverse=True)
                margin=similar-(alternatives[1] if len(alternatives)>1 else 0)
                if similar<70 or margin<12:fail('AMBIGUOUS_TEAM_MATCH_'+lg+'_'+day)
                if (row['h'],row['a'])!=(other['h'],other['a']):
                    fail('INDEPENDENT_SCORE_CONFLICT_'+lg+'_'+day)
                ledger.append({'league':lg,'match_date':day,
                    'football_data_home':row['home'],'football_data_away':row['away'],
                    'espn_home':other['home'],'espn_away':other['away'],
                    'home_goals':row['h'],'away_goals':row['a'],
                    'espn_event_id':other['id'],'name_confidence':round(similar,2),
                    'name_margin':round(margin,2),'score_agrees':True})
    if len(ledger)!=83 or len({(x['league'],x['match_date'],x['football_data_home'],x['football_data_away']) for x in ledger})!=83:
        fail('NOT_83_UNIQUE_MATCHES')
    by=Counter(x['league'] for x in ledger)
    return {'schema':'263_PUBLIC_SECONDARY_TWO_SOURCE_SCORE_CONCORDANCE_20261123_V1',
      'status':'RESEARCH_APPROVED_SECONDARY_SCORE_AGREEMENT_NOT_FEDERATION_VERIFIED',
      'asof_exclusive':'2026-11-23','source_snapshot_sha256':STAGE_SHA,
      'accepted_legacy_rows':4617,'new_concordant_results':83,'usable_total_rows':4700,
      'new_results_by_league':dict(sorted(by.items())),
      'football_data_provider_sha256':fetched_sha,
      'score_source_1':PUB_A,'score_source_2':PUB_B,
      'all_source_scores_identical':True,'team_names_unique_pairing_verified':True,
      'manually_reviewed_name_aliases':[{'league':k[0],'original':k[1],'espn_name':v} for k,v in REVIEWED.items()],
      'independent_federation_evidence':False,
      'original_4617_modified':False,'previous_prematch_seals_rewritten':False,
      'production_model_modified':False,
      'scope':'RESEARCH_M4C3_INPUT_NOT_PRODUCTION_OR_ORIGINAL_SEALED_MATCH',
      'matches':sorted(ledger,key=lambda v:(v['league'],v['match_date'],v['football_data_home']))}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    for key in ('source-dir','espn-file','stage-file','preview-audit-file','out-file'):
        parser.add_argument('--'+key,required=True)
    args=parser.parse_args()
    audit=check(args.source_dir,args.espn_file,args.stage_file,args.preview_audit_file)
    Path(args.out_file).write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('RESEARCH_TWO_SOURCE_ACCEPTED',audit['usable_total_rows'],
          'NEW',audit['new_concordant_results'],'MATCH_SCORE',audit['all_source_scores_identical'],
          'not federation evidence')
