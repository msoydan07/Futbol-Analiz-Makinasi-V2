"""Tests of GitHub commit guard; no real fixture or signed live forecast invented."""
import datetime as dt
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from PREKO_KAYIT_GUARD_V2 import check_new, check_staged, ReceiptError, RECEIPT_DIR

NOW=dt.datetime(2026,11,27,12,0,tzinfo=dt.timezone.utc)

def cli(repo,*a):
    subprocess.run(['git',*a],cwd=repo,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def make_doc(ko='2026-11-27T17:00:00+00:00',observed='2026-11-27T11:59:00+00:00'):
    d={'schema':'SERBEST_NAMED_OFFICIAL_PREKO_RESEARCH_V2',
       'status':'OFFICIAL_FIXTURE_VERIFIED_MODEL_RESEARCH_RECEIPT_NOT_GIT_SEALED',
       'league':'TUR1','match':'Team A - Team B','home_id':'a','away_id':'b',
       'official_source_url':'https://www.tff.org/fixture',
       'kickoff_utc':ko,'observed_at_utc':observed}
    h=hashlib.sha256(json.dumps(d,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    return {**d,'payload_sha256':h},ko[:10]+'_'+h[:24]+'.json'

class ReceiptGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.repo=Path(self.tmp.name)
        cli(self.repo,'init')
        cli(self.repo,'config','user.email','qa@example.org')
        cli(self.repo,'config','user.name','QA')
        self.dir=self.repo/RECEIPT_DIR
        self.dir.mkdir(parents=True)
        (self.repo/'README').write_text('clean')
        cli(self.repo,'add','README')
        cli(self.repo,'commit','-m','initialize')
    def tearDown(self):self.tmp.cleanup()
    def write(self,**kwargs):
        d,name=make_doc(**kwargs)
        p=self.dir/name
        p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
        return p
    def test_first_receipt_can_be_added(self):
        p=self.write()
        self.assertTrue(check_new(self.repo,NOW).endswith(p.name))
    def test_second_receipt_ignores_existing_tracked_first(self):
        first=self.write()
        cli(self.repo,'add',str(first.relative_to(self.repo)))
        cli(self.repo,'commit','-m','already sealed')
        second=self.write(ko='2026-11-28T17:00:00+00:00')
        found=check_new(self.repo,NOW)
        self.assertTrue(found.endswith(second.name))
        self.assertFalse(found.endswith(first.name))
    def test_no_new_receipt_rejected(self):
        with self.assertRaisesRegex(ReceiptError,'EXACTLY_ONE'):
            check_new(self.repo,NOW)
    def test_two_new_receipts_rejected(self):
        self.write()
        self.write(ko='2026-11-28T17:00:00+00:00')
        with self.assertRaisesRegex(ReceiptError,'EXACTLY_ONE'):
            check_new(self.repo,NOW)
    def test_tampered_receipt_rejected(self):
        p=self.write()
        x=json.loads(p.read_text());x['home_id']='tampered';p.write_text(json.dumps(x))
        with self.assertRaisesRegex(ReceiptError,'SHA256_MISMATCH'):
            check_new(self.repo,NOW)
    def test_kickoff_already_passed_rejected(self):
        self.write(ko='2026-11-27T11:00:00+00:00',observed='2026-11-27T10:59:00+00:00')
        with self.assertRaisesRegex(ReceiptError,'KICKOFF_NOT_IN_FUTURE'):
            check_new(self.repo,NOW)
    def test_observed_after_kickoff_rejected(self):
        self.write(ko='2026-11-27T11:00:00+00:00',observed='2026-11-27T11:01:00+00:00')
        with self.assertRaisesRegex(ReceiptError,'KICKOFF_NOT_IN_FUTURE'):
            check_new(self.repo,NOW)
    def test_stale_observation_rejected(self):
        self.write(observed='2026-11-27T10:00:00+00:00')
        with self.assertRaisesRegex(ReceiptError,'STALE_PREKO'):
            check_new(self.repo,NOW)
    def test_staged_single_addition_allowed(self):
        p=self.write();name=check_new(self.repo,NOW)
        cli(self.repo,'add',name)
        self.assertEqual(check_staged(self.repo,name,NOW),name)
    def test_staged_other_file_rejected(self):
        self.write();name=check_new(self.repo,NOW)
        cli(self.repo,'add',name)
        (self.repo/'unrelated').write_text('x')
        cli(self.repo,'add','unrelated')
        with self.assertRaisesRegex(ReceiptError,'STAGED_CHANGE'):
            check_staged(self.repo,name,NOW)
    def test_staged_content_modified_rejected(self):
        p=self.write();name=check_new(self.repo,NOW)
        cli(self.repo,'add',name)
        p.write_text(p.read_text()+'\n')
        with self.assertRaisesRegex(ReceiptError,'DIFFERS'):
            check_staged(self.repo,name,NOW)
if __name__=='__main__': unittest.main(verbosity=2)
