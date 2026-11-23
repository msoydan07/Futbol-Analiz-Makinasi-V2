#!/usr/bin/env python3
# coding: utf-8
"""Mobil V1.2 -> Hakem staging verifier (READ-ONLY).
Does not manufacture FUTBOL/M4/C3 forecasts, kickoff identity, match results,
server-side receipt, or HAKEM_PREMATCH_V1 records.

CLI: python MOBIL_HAKEM_STAGING_DOGRULAYICI_V1.py --staging mobil_hakem_aktarim_v1_2.json --pdf user_original_iddaa.pdf
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

EVENTS=('MS1','MSX','MS2','OVER_2.5','UNDER_2.5','BTTS_YES','BTTS_NO')
GROUPS=(EVENTS[:3],EVENTS[3:5],EVENTS[5:7])
class ValidationError(ValueError): pass

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,
        separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()

def numeric7(values, *, valid_odds=False):
    if not isinstance(values,dict) or tuple(values)!=EVENTS:
        raise ValidationError('SEVEN_ORDERED_EVENTS_REQUIRED')
    try: result={k:float(values[k]) for k in EVENTS}
    except (ValueError,TypeError,KeyError) as exc:raise ValidationError('INVALID_NUMERIC_VECTOR') from exc
    if not all(math.isfinite(x) for x in result.values()):raise ValidationError('NONFINITE_VECTOR')
    if valid_odds:
        if not all(1.0<x<=1000 for x in result.values()):raise ValidationError('INVALID_IDDAA_ODDS')
    else:
        if not all(0<=x<=1 for x in result.values()):raise ValidationError('INVALID_PROBABILITY')
        if any(abs(sum(result[k] for k in group)-1)>2e-8 for group in GROUPS):
            raise ValidationError('FAMILY_PROBABILITIES_NOT_NORMALIZED')
    return result

def no_vig(odds):
    x=numeric7(odds,valid_odds=True);p={}
    for group in GROUPS:
        inv={k:1/x[k] for k in group};total=sum(inv.values())
        p.update({k:inv[k]/total for k in group})
    return p

def validate(staging:dict, raw_pdf:bytes)->dict:
    if staging.get('schema')!='MOBIL_HAKEM_STAGING_V1':raise ValidationError('WRONG_STAGING_SCHEMA')
    if staging.get('status')!='RESEARCH_STAGING_NOT_PREMATCH_SEAL':raise ValidationError('UNSUPPORTED_STAGING_STATUS')
    seal=staging.get('staging_payload_sha256')
    if not isinstance(seal,str) or digest({k:v for k,v in staging.items() if k!='staging_payload_sha256'})!=seal:
        raise ValidationError('STAGING_PAYLOAD_SHA256_MISMATCH')
    actual_pdf_hash=hashlib.sha256(raw_pdf).hexdigest()
    if staging.get('source_pdf_sha256')!=actual_pdf_hash:raise ValidationError('ORIGINAL_USER_PDF_SHA256_MISMATCH')
    if staging.get('source_pdf_price_source')!='USER_UPLOADED_IDDAA_ORIGINAL_PDF':
        raise ValidationError('IDDAA_ORIGINAL_PDF_REQUIRED')
    if staging.get('archive_full_loaded') is not True or staging.get('source_pdf_not_included') is not True:
        raise ValidationError('FULL_ARCHIVE_OR_PDF_SOURCE_INVALID')
    rows=staging.get('records')
    if not isinstance(rows,list) or not rows or len(rows)!=staging.get('record_count') or len(rows)>250:
        raise ValidationError('INVALID_RECORD_COUNT')
    seen=set();audit=[]
    for n,r in enumerate(rows,1):
        if r.get('source_row')!=n:raise ValidationError('SOURCE_ORDER_CHANGED')
        key=(r.get('match_name_pdf'),r.get('kickoff_local_time_user_label'))
        if any(not isinstance(z,str) or not z for z in key) or key in seen:
            raise ValidationError('DUPLICATE_OR_MISSING_MATCH_LABEL')
        seen.add(key)
        if r.get('fixture_id') is not None or r.get('official_fixture_status')!='MISSING' or r.get('kickoff_utc') is not None:
            raise ValidationError('V12_STAGING_CANNOT_ATTEST_OFFICIAL_FIXTURE')
        if r.get('history_data_mode')!='FULL' or not isinstance(r.get('hafiza_similar_n'),int) or r['hafiza_similar_n']<=0:
            raise ValidationError('HAFIZA_FULL_HISTORY_REQUIRED')
        if r.get('source_pdf_sha256')!=actual_pdf_hash:
            raise ValidationError('RECORD_PDF_SHA_MISMATCH')
        odds=numeric7(r.get('seven_raw_odds'),valid_odds=True)
        market=numeric7(r.get('p0_seven_proportional'))
        historical=numeric7(r.get('hafiza_seven_realized'))
        computed=no_vig(odds)
        if max(abs(computed[k]-market[k]) for k in EVENTS)>3e-11:
            raise ValidationError('P0_MARKET_CALCULATION_MISMATCH')
        counts=r.get('hafiza_event_counts')
        if not isinstance(counts,dict) or tuple(counts)!=EVENTS or any(type(x)!=int or x<0 for x in counts.values()):
            raise ValidationError('HAFIZA_COUNTS_INVALID')
        for k in EVENTS:
            if abs(counts[k]/r['hafiza_similar_n']-historical[k])>3e-11:
                raise ValidationError('HAFIZA_COUNT_RATIO_MISMATCH')
        if any(sum(counts[k] for k in group)!=r['hafiza_similar_n'] for group in GROUPS):
            raise ValidationError('HAFIZA_FAMILY_COUNTS_MISMATCH')
        audit.append({'row':n,'match':r['match_name_pdf'],'p0_verified':True,'hafiza_fraction_verified':True,
            'model_m4_c3_v4_status':'UNVERIFIED_NO_SIGNED_FORECAST',
            'fixture_status':'UNVERIFIED_NO_OFFICIAL_ID_OR_KICKOFF',
            'prematch_receipt':'UNVERIFIED_CLIENT_CLOCK_NOT_INDEPENDENT'})
    return {'schema':'MOBIL_HAKEM_STAGING_READONLY_VERIFICATION_V1',
        'status':'SOURCE_AND_INTERNAL_MATH_VERIFIED_STAGING_ONLY',
        'source_pdf_sha256':actual_pdf_hash,'checked_records':len(audit),
        'HAFIZA_and_P0_share_odds_inputs':True,
        'history_test_included':bool(staging.get('history_test_included')),
        'valid_referee_training_records':0,
        'missing_next_steps':['OFFICIAL_FIXTURE_PROOF','SIGNED_FUTBOL_M4_C3_V4_FORECAST',
            'TRUSTED_PREKICKOFF_RECEIPT','SEPARATE_POSTMATCH_RESULT_AFTER_KICKOFF'],
        'records':audit}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staging',required=True,type=Path)
    parser.add_argument('--pdf',required=True,type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    try:result=validate(json.loads(args.staging.read_text(encoding='utf-8')),args.pdf.read_bytes())
    except (ValidationError,OSError,ValueError,KeyError,TypeError) as e:
        parser.exit(status=2,message='BLOCKED: '+str(e)+'\n')
    out=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:args.output.write_text(out,encoding='utf-8')
    else:print(out)
if __name__=='__main__':main()
