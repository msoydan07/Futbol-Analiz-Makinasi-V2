import unittest,datetime as dt,json,tempfile,subprocess
from pathlib import Path
from P0_HAFIZA_MUHUR_SONUC_ZINCIRI_V1 import hash_obj,RECEIPT_SCHEMA,RECEIPT_STATUS,OddsForwardError
from PREKO_ORAN_KAYIT_GUARD_V1 import verify_added_in_push
UTC=dt.timezone.utc
START=dt.datetime(2026,11,24,14,0,tzinfo=UTC)
NOW=dt.datetime(2026,11,24,11,0,tzinfo=UTC)
def git(root,*args):subprocess.run(["git",*args],cwd=root,check=True,stdout=subprocess.DEVNULL)
class GuardTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);git(self.root,"init","-q")
        git(self.root,"config","user.email","ci@example.invalid");git(self.root,"config","user.name","ci")
        (self.root/"base.txt").write_text("base")
        git(self.root,"add","base.txt");git(self.root,"commit","-qm","base")
        self.before=subprocess.check_output(["git","rev-parse","HEAD"],cwd=self.root,text=True).strip()
        self.folder=self.root/"experiments/263/serbest_analiz_v2/odds_receipts"
        self.folder.mkdir(parents=True)
    def add(self):
        a={"schema":RECEIPT_SCHEMA,"status":RECEIPT_STATUS,"match":"A-B",
           "fixture_key":"K","kickoff_utc":START.isoformat(),"observed_at_utc":NOW.isoformat(),
           "official_verification":"OFFICIAL_FIXTURE_GATEWAY_LOOKUP",
           "official_source_url":"https://example.org/","source_pdf_sha256":"f"*64}
        a["payload_sha256"]=hash_obj(a)
        p=self.folder/(START.date().isoformat()+"_"+a["payload_sha256"][:24]+".json")
        p.write_text(json.dumps(a))
        git(self.root,"add",str(p.relative_to(self.root)));git(self.root,"commit","-qm","new")
        return p
    def test_accept(self):
        self.add()
        self.assertEqual(verify_added_in_push(self.root,before=self.before,now=NOW)["new_receipts"],1)
    def test_kickoff_block(self):
        self.add()
        with self.assertRaises(OddsForwardError):
            verify_added_in_push(self.root,before=self.before,now=START+dt.timedelta(seconds=1))
    def test_stale_block(self):
        self.add()
        with self.assertRaises(OddsForwardError):
            verify_added_in_push(self.root,before=self.before,now=NOW+dt.timedelta(hours=1))
    def test_tamper_block(self):
        p=self.add();a=json.loads(p.read_text());a["match"]="changed";p.write_text(json.dumps(a))
        with self.assertRaises(OddsForwardError):
            verify_added_in_push(self.root,before=self.before,now=NOW)
    def test_other_file_change_block(self):
        self.add();(self.root/"base.txt").write_text("changed")
        git(self.root,"add","base.txt");git(self.root,"commit","-qm","change")
        with self.assertRaises(OddsForwardError):
            verify_added_in_push(self.root,before=self.before,now=NOW)
if __name__=="__main__":unittest.main()
