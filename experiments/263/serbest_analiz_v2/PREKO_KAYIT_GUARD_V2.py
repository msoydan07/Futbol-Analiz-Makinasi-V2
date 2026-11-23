#!/usr/bin/env python3
# coding: utf-8
"""Fail-closed verification of exactly one *new* pre-kickoff research receipt.

Existing tracked receipts must NOT cause a second/new analysis to fail. The
new file must be an untracked, genuine output from the independent official
research gate, intact SHA-signed, and kickoff must still be in the future.
This checks integrity & clock, NOT independent authenticity of the official
source and NOT proof of a GitHub push accepted before kickoff.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

RECEIPT_DIR = 'experiments/263/serbest_analiz_v2/official_receipts/'
SCHEMA = 'SERBEST_NAMED_OFFICIAL_PREKO_RESEARCH_V2'
STATUS = 'OFFICIAL_FIXTURE_VERIFIED_MODEL_RESEARCH_RECEIPT_NOT_GIT_SEALED'

class ReceiptError(ValueError):
    pass


def _git(root: Path, *args: str) -> str:
    p = subprocess.run(['git', *args], cwd=root, capture_output=True, text=True)
    if p.returncode:
        raise ReceiptError('GIT_COMMAND_FAILED:' + p.stderr.strip()[:160])
    return p.stdout


def newly_created(root: Path) -> str:
    names = _git(root, 'ls-files', '--others', '--exclude-standard', '--', RECEIPT_DIR).splitlines()
    if len(names) != 1:
        raise ReceiptError(f'EXACTLY_ONE_NEW_UNTRACKED_RECEIPT_REQUIRED:{len(names)}')
    name = names[0]
    if not re.fullmatch(r'experiments/263/serbest_analiz_v2/official_receipts/\d{4}-\d\d-\d\d_[0-9a-f]{24}\.json', name):
        raise ReceiptError('RECEIPT_PATH_NOT_CONTENT_ADDRESSED')
    p=(root/name).resolve()
    if not p.is_relative_to((root/RECEIPT_DIR).resolve()) or not p.is_file() or p.is_symlink():
        raise ReceiptError('RECEIPT_PATH_INVALID')
    return name


def check_payload(name: str, raw: bytes, now: dt.datetime) -> dict:
    if now.tzinfo is None:
        raise ReceiptError('CURRENT_CLOCK_MUST_BE_AWARE')
    try:
        doc=json.loads(raw)
    except (ValueError,UnicodeDecodeError) as exc:
        raise ReceiptError('RECEIPT_INVALID_JSON') from exc
    if not isinstance(doc,dict) or doc.get('schema')!=SCHEMA or doc.get('status')!=STATUS:
        raise ReceiptError('RECEIPT_SCHEMA_OR_STATUS_INVALID')
    signed=doc.get('payload_sha256')
    original={k:v for k,v in doc.items() if k!='payload_sha256'}
    check=hashlib.sha256(json.dumps(original,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
    if signed!=check:
        raise ReceiptError('RECEIPT_SHA256_MISMATCH')
    if not name.endswith('_'+check[:24]+'.json'):
        raise ReceiptError('RECEIPT_FILENAME_NOT_SHA_MATCHED')
    for key in ('league','match','home_id','away_id','official_source_url','kickoff_utc','observed_at_utc'):
        if not isinstance(doc.get(key),str) or not doc[key].strip():
            raise ReceiptError('RECEIPT_MISSING_FIELD:'+key)
    if not doc['official_source_url'].startswith('https://') or doc['home_id']==doc['away_id']:
        raise ReceiptError('RECEIPT_INVALID_SOURCE_OR_TEAMS')
    try:
        ko=dt.datetime.fromisoformat(doc['kickoff_utc'].replace('Z','+00:00'))
        observed=dt.datetime.fromisoformat(doc['observed_at_utc'].replace('Z','+00:00'))
    except ValueError as exc:
        raise ReceiptError('RECEIPT_INVALID_DATE') from exc
    if ko.tzinfo is None or observed.tzinfo is None:
        raise ReceiptError('RECEIPT_UNAWARE_TIMES')
    now=now.astimezone(dt.timezone.utc)
    ko=ko.astimezone(dt.timezone.utc)
    observed=observed.astimezone(dt.timezone.utc)
    if not observed < ko or not now < ko:
        raise ReceiptError('KICKOFF_NOT_IN_FUTURE_OR_RESULT_BACKFILLED')
    if observed > now + dt.timedelta(minutes=2):
        raise ReceiptError('RECEIPT_OBSERVATION_IN_FUTURE')
    if (now-observed)>dt.timedelta(minutes=30):
        raise ReceiptError('STALE_PREKO_RECEIPT_NOT_SAFELY_COMMITTABLE')
    return doc


def check_new(root: Path, now: dt.datetime | None=None) -> str:
    name=newly_created(root)
    check_payload(name, (root/name).read_bytes(), now or dt.datetime.now(dt.timezone.utc))
    return name


def check_staged(root: Path, name: str, now: dt.datetime | None=None) -> str:
    changed=_git(root,'diff','--cached','--name-only').splitlines()
    added=_git(root,'diff','--cached','--name-only','--diff-filter=A').splitlines()
    if changed!=[name] or added!=[name]:
        raise ReceiptError('STAGED_CHANGE_IS_NOT_ONE_NEW_RECEIPT')
    blob=_git(root,'show',':'+name).encode('utf-8')
    check_payload(name,blob,now or dt.datetime.now(dt.timezone.utc))
    if blob!=(root/name).read_bytes():
        raise ReceiptError('STAGED_RECEIPT_DIFFERS_FROM_WORKING_COPY')
    return name


def main() -> None:
    a=argparse.ArgumentParser()
    a.add_argument('--path',action='store_true',help='Print only the one newly created receipt path')
    a.add_argument('--staged',metavar='PATH',help='Validate exactly one staged addition and recheck KO')
    args=a.parse_args()
    root=Path.cwd().resolve()
    if args.staged:
        selected=check_staged(root,args.staged)
    else:
        selected=check_new(root)
    print(selected if args.path or args.staged else 'SAFE_PREKO_RECEIPT '+selected)

if __name__=='__main__':
    main()
