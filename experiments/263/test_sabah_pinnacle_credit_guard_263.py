import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
from sabah_pinnacle_credit_guard_263 import reserve,check_existing,AlreadyReserved
class CreditGuardTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.root=Path(self.tmp.name)
  self.now=datetime(2026,11,7,6,0,tzinfo=timezone.utc)
 def tearDown(self):self.tmp.cleanup()
 def test_one_call_per_league_day(self):
  reserve(self.root,"TUR1",self.now)
  with self.assertRaises(AlreadyReserved):reserve(self.root,"TUR1",self.now)
  self.assertFalse(check_existing(self.root,"TUR1",self.now)["retry_allowed_same_day"])
 def test_other_league_allowed(self):
  reserve(self.root,"TUR1",self.now)
  reserve(self.root,"ENG1",self.now)
 def test_next_day_allowed(self):
  reserve(self.root,"TUR1",self.now)
  reserve(self.root,"TUR1",datetime(2026,11,8,6,0,tzinfo=timezone.utc))
 def test_invalid_league(self):
  with self.assertRaises(ValueError):reserve(self.root,"UNKNOWN",self.now)
 def test_naive_clock(self):
  with self.assertRaises(ValueError):reserve(self.root,"TUR1",datetime(2026,11,7))
 def test_corrupt_ledger_blocks(self):
  p,_=reserve(self.root,"TUR1",self.now)
  p.write_text('{"schema":"INVALID"}',encoding="utf-8")
  with self.assertRaises(ValueError):check_existing(self.root,"TUR1",self.now)
  with self.assertRaises(AlreadyReserved):reserve(self.root,"TUR1",self.now)
if __name__=="__main__":unittest.main()
