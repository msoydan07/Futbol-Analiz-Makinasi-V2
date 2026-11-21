"""Append-only, sanitized derived archive for the 2.6.3 second user iddaa PDF.

Never store raw PDFs, API keys, private user data, new predictions or final scores.
An export is a local pending git file until a separate Git commit is verified.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re

SCHEMA = '263_SECOND_PDF_COMMENTARY_APPEND_ONLY_V1'
REVIEW_SCHEMA = '263_SINGLE_MORNING_SEAL_ONE_PREKO_REVIEW_V1'
CORE_MARKETS = ('MS1','MSX','MS2','OVER_2.5','UNDER_2.5','BTTS_YES','BTTS_NO')
ARCHIVE_ROOT = Path('experiments/263/second_pdf_commentary_archive_263')
GROUP = {'MS1':'MS','MSX':'MS','MS2':'MS',
         'OVER_2.5':'GOALS_2.5','UNDER_2.5':'GOALS_2.5',
         'BTTS_YES':'KG','BTTS_NO':'KG'}

class ArchiveRejected(ValueError):
    pass

def canon(o):
    return json.dumps(o,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')

def sha(o):
    return hashlib.sha256(canon(o)).hexdigest()

def _clock(s):
    d=datetime.fromisoformat(str(s).replace('Z','+00:00'))
    if d.tzinfo is None:raise ArchiveRejected('AWARE_UTC_REQUIRED')
    return d.astimezone(timezone.utc)

def _valid_sha(v):
    return isinstance(v,str) and bool(re.fullmatch(r'[a-f0-9]{64}',v))

def _slug(s):
    s=re.sub(r'[^a-z0-9]+','_',str(s).casefold()).strip('_')
    if not s or len(s)>100:raise ArchiveRejected('UNSAFE_SLUG')
    return s

def _numbers(src):
    if not isinstance(src,dict):return {}
    out={}
    for k in CORE_MARKETS:
        v=src.get(k)
        if v is None:continue
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not 1<v<500:
            raise ArchiveRejected('BAD_ODDS_VALUE:'+k)
        out[k]=float(v)
    return out

def _fair(src):
    if not isinstance(src,dict):return {}
    out={}
    for name in ('MS','GOALS_2.5','KG'):
        group=src.get(name) or {}
        if group.get('status')!='FULL_MARKET_QUOTE_AVAILABLE':continue
        p=group.get('no_vig') or {}
        if not isinstance(p,dict):raise ArchiveRejected('INVALID_NO_VIG')
        numeric={k:float(v) for k,v in p.items()
                 if k in CORE_MARKETS and isinstance(v,(int,float)) and not isinstance(v,bool)}
        if not numeric or not all(0<=v<=1 for v in numeric.values()):
            raise ArchiveRejected('INVALID_NO_VIG_PROBS')
        out[name]=numeric
    return out

def row_to_record(review,row):
    """Only a completed, original-seal-linked, strictly pre-KO row qualifies."""
    if review.get('schema')!=REVIEW_SCHEMA or review.get('math_refitted') is not False \
       or review.get('forecast_shas_replaced') is not False or review.get('second_model_seal_created') is not False:
        raise ArchiveRejected('NOT_ORIGINAL_SINGLE_PREMATCH_REVIEW')
    if row.get('status')!='GUNCEL_ORAN_KAYDI_VE_KADRO_DURUMU_HAZIR':
        raise ArchiveRejected('ROW_NOT_PREMATCH_REVIEWED')
    for key in ('morning_pdf_sha256','second_pdf_sha256','morning_session_sha256'):
        if not _valid_sha(review.get(key)):raise ArchiveRejected('MISSING_SOURCE_SHA:'+key)
    for key in ('morning_model_sha256','morning_decision_sha256'):
        if not _valid_sha(row.get(key)):raise ArchiveRejected('MISSING_SEAL_SHA:'+key)
    observed=_clock(review.get('last_odds_observed_utc'))
    reviewed=_clock(review.get('reviewed_at_utc'))
    ko=_clock(row.get('kickoff_utc'))
    if not observed<=reviewed<ko:
        raise ArchiveRejected('NOT_VALID_SECOND_PDF_PRE_KO')
    choice=row.get('morning_main_choice') or {}
    alternative=row.get('morning_alternative_choice') or {}
    main=choice.get('market')
    if main not in CORE_MARKETS or alternative.get('market') not in CORE_MARKETS:
        raise ArchiveRejected('MISSING_FROZEN_MARKET')
    p=choice.get('calibrated_probability')
    if isinstance(p,bool) or not isinstance(p,(int,float)) or not 0<=p<=1:
        raise ArchiveRejected('BAD_FROZEN_PROB')
    start=_numbers(row.get('morning_odds'))
    end=_numbers(row.get('latest_odds'))
    if not start or not end:raise ArchiveRejected('SECOND_ODDS_MISSING')
    def pct(data):return (_fair(data).get(GROUP[main]) or {}).get(main)
    p0=pct(row.get('morning_market_no_vig'))
    p1=pct(row.get('latest_market_no_vig'))
    if p0 is None or p1 is None:raise ArchiveRejected('MAIN_MARKET_NO_VIG_UNAVAILABLE')
    from iddaa_pdf_approved_layout_263 import _single_commentary
    msg=_single_commentary(row,main,start.get(main),end.get(main))
    if not msg:raise ArchiveRejected('COMMENTARY_MISSING')
    facts=((row.get('lineups') or {}).get('comments') or [])
    # A source assertion is not automatically an independently verified XI.
    facts=[{'fact':str(c.get('fact','')),'football_reason':str(c.get('football_reason','')),
            'source_url':str(c.get('source_url','')),
            'source_verified_by_program':False} for c in facts if isinstance(c,dict)]
    record={
      'schema':SCHEMA,
      'record_kind':'PREMATCH_SECOND_PDF_LOCAL_EXPORT_PENDING_SEPARATE_GIT_COMMIT',
      'match':{'league':str(row['league']),'date_tr':str(row['match_date_tr']),
               'time_tr':str(row['kickoff_time_tr']),'home':str(row['home']),
               'away':str(row['away']),'home_id':str(row['home_id']),'away_id':str(row['away_id']),
               'kickoff_utc':ko.isoformat()},
      'original_seal':{'forecast_sha256':row['morning_model_sha256'],
                       'decision_sha256':row['morning_decision_sha256'],
                       'main_market':main,'main_probability':p,
                       'alternative_market':alternative['market'],
                       'alternative_probability':alternative.get('calibrated_probability')},
      'source_pdf_fingerprints':{
             'first_pdf_sha256':review['morning_pdf_sha256'],
             'second_pdf_sha256':review['second_pdf_sha256'],
             'morning_session_sha256':review['morning_session_sha256'],
             'second_pdf_observed_utc':observed.isoformat(),
             'reviewed_at_utc':reviewed.isoformat(),
             'raw_pdfs_committed_to_github':False},
      'second_pdf_observation':{
             'first_odds':start,'second_odds':end,
             'first_market_no_vig':_fair(row.get('morning_market_no_vig')),
             'second_market_no_vig':_fair(row.get('latest_market_no_vig')),
             'main_price_first':start.get(main), 'main_price_second':end.get(main),
             'main_price_delta':round(end[main]-start[main],5) if main in start and main in end else None,
             'main_market_probability_change_pp':round(100*(p1-p0),6),
             'our_probability_minus_second_market_pp':round(100*(p-p1),6)},
      'commentary':{'author':'ChatGPT assistant','text_verbatim':msg,
                    'sourced_football_claims':facts,
                    'lineup_verification_status':(row.get('lineups') or {}).get('status'),
                    'movement_cause_independently_proven':False},
      'archive_safety':{
             'original_model_and_decision_unchanged':True,
             'no_new_model_fit_or_forecast':True,
             'no_match_result_in_commentary':True,
             'git_commit_before_kickoff_not_claimed':True,
             'user_pdf_bytes_excluded':True}
    }
    record['record_sha256']=sha(record)
    return record

def append_review_archive(review,repo_root='.'):
    """Prepare immutable files in checkout; a separate Git commit is required.

    Re-running an identical review is idempotent. Any conflicting second PDF or
    altered commentary for the same match is blocked rather than overwritten.
    """
    root=Path(repo_root).resolve()
    payloads=[];keys=set()
    for row in review.get('rows',[]):
        if row.get('status')!='GUNCEL_ORAN_KAYDI_VE_KADRO_DURUMU_HAZIR':continue
        record=row_to_record(review,row)
        m=record['match']
        if not re.fullmatch(r'20\d\d-\d\d-\d\d',m['date_tr']):raise ArchiveRejected('BAD_DATE')
        name=f"{m['league']}_{_slug(m['home_id'])}_{_slug(m['away_id'])}.json"
        path=root/ARCHIVE_ROOT/m['date_tr']/name
        if path in keys:raise ArchiveRejected('DUPLICATE_REVIEW_MATCH')
        keys.add(path);payloads.append((path,record))
    if not payloads:raise ArchiveRejected('NO_REVIEW_ROWS_TO_ARCHIVE')
    # precheck all conflicts before opening any new file
    for p,v in payloads:
        if p.exists():
            old=json.loads(p.read_text(encoding='utf-8'))
            if old!=v:raise ArchiveRejected('SECOND_PDF_ARCHIVE_ALREADY_EXISTS_DIFFERENT:'+p.name)
    saved=[]
    for p,v in payloads:
        p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():
            with p.open('x',encoding='utf-8') as f:
                json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
                f.write('\n')
        saved.append(str(p.relative_to(root)))
    return {'status':'LOCAL_APPEND_ONLY_FILES_READY_GITHUB_COMMIT_REQUIRED',
            'files':saved,'count':len(saved),'original_forecasts_untouched':True}