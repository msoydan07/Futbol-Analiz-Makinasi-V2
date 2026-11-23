import unittest,tempfile,datetime as dt,json
from pathlib import Path
from GUNLUK_SERBEST_ANALIZ_KAPISI_V2 import GateError,gate_result,save_official_receipt

class GateTests(unittest.TestCase):
    def setUp(self):
        self.now=dt.datetime(2026,11,23,13,0,tzinfo=dt.timezone.utc)
        self.g={'status':'VERIFIED','league':'TUR1','home_id':'a','away_id':'b',
            'kickoff_utc':'2026-11-23T17:00:00+00:00',
            'retrieved_at_utc':'2026-11-23T12:59:00+00:00','source_url':'https://www.tff.org/fixture'}
    def test_valid_ko_no_fixed_morning_time(self):
        self.assertEqual(gate_result(self.g,'TUR1',self.now)['local_date'],'2026-11-23')
    def test_10_minute_preko_valid(self):
        n=dt.datetime(2026,11,23,16,50,tzinfo=dt.timezone.utc)
        self.g['retrieved_at_utc']='2026-11-23T16:48:00+00:00'
        self.assertEqual(gate_result(self.g,'TUR1',n)['kickoff_utc'],'2026-11-23T17:00:00+00:00')
    def test_begun_match_blocked(self):
        with self.assertRaisesRegex(GateError,'KICKOFF_NOT_IN_FUTURE'):
            gate_result(self.g,'TUR1',dt.datetime(2026,11,23,17,1,tzinfo=dt.timezone.utc))
    def test_wrong_league_blocked(self):
        with self.assertRaisesRegex(GateError,'NOT_VERIFIED'):
            gate_result(self.g,'GER1',self.now)
    def test_old_check_blocked(self):
        self.g['retrieved_at_utc']='2026-11-21T13:00:00+00:00'
        with self.assertRaisesRegex(GateError,'STALE_OFFICIAL'):
            gate_result(self.g,'TUR1',self.now)
    def test_timestamp_without_timezone_blocked(self):
        self.g['kickoff_utc']='2026-11-23T17:00:00'
        with self.assertRaisesRegex(GateError,'NAIVE_KO'):
            gate_result(self.g,'TUR1',self.now)
    def test_untrusted_link_blocked(self):
        self.g['source_url']='http://example.com'
        with self.assertRaisesRegex(GateError,'SOURCE_INVALID'):
            gate_result(self.g,'TUR1',self.now)
    def test_write_once_append_only(self):
        r={'kickoff_utc':self.g['kickoff_utc'],'test_only':True}
        with tempfile.TemporaryDirectory() as d:
            p=save_official_receipt(r,d)
            self.assertTrue(p.exists())
            with self.assertRaises(FileExistsError):save_official_receipt(r,d)
    def test_no_ko_blocked(self):
        self.g['kickoff_utc']=None
        with self.assertRaisesRegex(GateError,'INCOMPLETE'):
            gate_result(self.g,'TUR1',self.now)
if __name__=='__main__':unittest.main(verbosity=2)
