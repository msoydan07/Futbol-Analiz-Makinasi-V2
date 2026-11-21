"""No network, no bookmaker, no model fitting: append-only second review proof."""
from pathlib import Path
from tempfile import TemporaryDirectory
import copy
import json
import sys
import types

import second_pdf_commentary_archive_263 as a

sys.modules['iddaa_pdf_approved_layout_263']=types.SimpleNamespace(
    _single_commentary=lambda row,market,old,new:
       'SABAH_KARARI_DEGISMEDI; main %s fiyat %.2f -> %.2f; kadro nedeni kesin degil.'%(market,old,new)
)

D='2026-11-21'
P={'MS1':.6,'MSX':.25,'MS2':.15}
base={'MS':{'status':'FULL_MARKET_QUOTE_AVAILABLE','no_vig':P}}
raw={'MS1':1.45,'MSX':4.2,'MS2':6.0}
last={'MS1':1.51,'MSX':4.0,'MS2':5.8}
row={'league':'ENG1','home':'Alpha','away':'Beta','home_id':'a'*32,'away_id':'b'*32,
     'match_date_tr':D,'kickoff_time_tr':'15:30','kickoff_utc':'2026-11-21T12:30:00+00:00',
     'status':'GUNCEL_ORAN_KAYDI_VE_KADRO_DURUMU_HAZIR',
     'morning_model_sha256':'a'*64,'morning_decision_sha256':'b'*64,
     'morning_main_choice':{'market':'MS1','calibrated_probability':.66},
     'morning_alternative_choice':{'market':'BTTS_YES','calibrated_probability':.54},
     'morning_odds':raw,'latest_odds':last,'morning_market_no_vig':base,
     'latest_market_no_vig':{'MS':{'status':'FULL_MARKET_QUOTE_AVAILABLE','no_vig':{'MS1':.55,'MSX':.27,'MS2':.18}}},
     'lineups':{'status':'KADRO_KANITI_YOK','comments':[]}}
review={'schema':a.REVIEW_SCHEMA,'morning_pdf_sha256':'1'*64,
        'second_pdf_sha256':'2'*64,'morning_session_sha256':'3'*64,
        'math_refitted':False,'forecast_shas_replaced':False,'second_model_seal_created':False,
        'last_odds_observed_utc':'2026-11-21T12:10:00+00:00',
        'reviewed_at_utc':'2026-11-21T12:11:00+00:00','rows':[row]}
with TemporaryDirectory() as root:
    r=a.append_review_archive(review,root)
    assert r['count']==1 and 'GITHUB_COMMIT_REQUIRED' in r['status']
    b=a.append_review_archive(review,root)
    assert b==r
    p=Path(root)/r['files'][0]
    saved=json.loads(p.read_text(encoding='utf-8'))
    assert saved['record_sha256']==a.sha({k:v for k,v in saved.items() if k!='record_sha256'})
    assert saved['commentary']['text_verbatim'].startswith('SABAH_KARARI_DEGISMEDI')
    altered=copy.deepcopy(review);altered['rows'][0]['latest_odds']['MS1']=1.50
    try:a.append_review_archive(altered,root)
    except a.ArchiveRejected as e:assert 'ALREADY_EXISTS_DIFFERENT' in str(e)
    else:raise AssertionError('overwrite should have been prevented')
    late=copy.deepcopy(review);late['reviewed_at_utc']='2026-11-21T12:31:00+00:00'
    try:a.append_review_archive(late,root)
    except a.ArchiveRejected as e:assert 'NOT_VALID_SECOND_PDF_PRE_KO' in str(e)
    else:raise AssertionError('postkickoff must fail')
print('PASS: write, idempotence, integrity, conflict lock, prematch clock gate')