#!/usr/bin/env python3
# coding: utf-8
"""Fail-closed GitHub post-push acceptance check for new research odds receipts.

Only a GitHub run completed BEFORE official KO supports a pre-KO research
registration. The local receipt or client timestamp alone is NOT a Git seal.
"""
from __future__ import annotations
import argparse,datetime as dt,json,os,re,subprocess
from pathlib import Path
from P0_HAFIZA_MUHUR_SONUC_ZINCIRI_V1 import check_receipt,utc,OddsForwardError
PREFIX="experiments/263/serbest_analiz_v2/odds_receipts/"
NAME=re.compile(r"^\d{4}-\d\d-\d\d_[0-9a-f]{24}\.json$")
def git(root,*parts):
    p=subprocess.run(["git",*parts],cwd=root,capture_output=True,text=True)
    if p.returncode:raise OddsForwardError("GIT_ERROR:"+p.stderr[:180])
    return p.stdout.strip()
def verify_added_in_push(root,*,before,now=None):
    root=Path(root).resolve()
    now=utc(now or dt.datetime.now(dt.timezone.utc))
    if not re.fullmatch(r"[a-f0-9]{40}",before) or before=="0"*40:
        raise OddsForwardError("REAL_PREVIOUS_COMMIT_REQUIRED")
    added=git(root,"diff","--name-only","--diff-filter=A",before,"HEAD").splitlines()
    all_changed=git(root,"diff","--name-only",before,"HEAD").splitlines()
    if not added or added!=all_changed or len(added)>250:
        raise OddsForwardError("ONLY_NEW_APPEND_ONLY_RECEIPTS_ALLOWED")
    keys=set()
    for rel in added:
        if not rel.startswith(PREFIX) or not NAME.fullmatch(rel[len(PREFIX):]):
            raise OddsForwardError("UNEXPECTED_OR_BAD_RECEIPT_PATH")
        p=root/rel
        if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to((root/PREFIX).resolve()):
            raise OddsForwardError("INVALID_RECEIPT_FILE")
        doc=json.loads(p.read_text(encoding="utf-8"))
        check_receipt(doc,now)
        if p.name!=doc["kickoff_utc"][:10]+"_"+doc["payload_sha256"][:24]+".json":
            raise OddsForwardError("RECEIPT_FILENAME_SHA_MISMATCH")
        made=utc(doc["observed_at_utc"])
        if made>now+dt.timedelta(minutes=2) or now-made>dt.timedelta(minutes=30):
            raise OddsForwardError("STALE_OR_FUTURE_OBSERVATION")
        if doc["fixture_key"] in keys:raise OddsForwardError("DUPLICATE_NEW_FIXTURE")
        keys.add(doc["fixture_key"])
    for p in (root/PREFIX).glob("*.json"):
        if PREFIX+p.name in added:continue
        old=json.loads(p.read_text(encoding="utf-8"))
        check_receipt(old)
        if old["fixture_key"] in keys:raise OddsForwardError("DUPLICATE_OLD_FIXTURE")
    return {"status":"GITHUB_RUN_PREKO_RESEARCH_RECEIPT_VERIFIED","new_receipts":len(added),
            "warning":"Research receipt only. The GH server-side run must finish before kickoff."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path.cwd())
    p.add_argument("--before",default=os.environ.get("BEFORE_COMMIT"))
    a=p.parse_args()
    if not a.before:raise OddsForwardError("MISSING_PUSH_BEFORE_SHA")
    print(json.dumps(verify_added_in_push(a.root,before=a.before),ensure_ascii=False))
if __name__=="__main__":main()
