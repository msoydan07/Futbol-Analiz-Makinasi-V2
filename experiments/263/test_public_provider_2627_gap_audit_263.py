import unittest,csv,io,copy
from public_provider_2627_gap_audit_263 import SOURCES,MIN_FT_BY_NOV8,ProviderBlocked,witness_source,audit_ten
F=['Date','HomeTeam','AwayTeam','FTHG','FTAG','FTR']
def fake(league,*,added=False):
    out=io.StringIO();w=csv.DictWriter(out,fieldnames=F,lineterminator='\n');w.writeheader()
    for i in range(MIN_FT_BY_NOV8[league]):
        w.writerow(dict(Date='08/11/2026',HomeTeam='Club%d'%i,AwayTeam='Other%d'%i,FTHG='1',FTAG='0',FTR='H'))
    if added:w.writerow(dict(Date='12/11/2026',HomeTeam='New A',AwayTeam='New B',FTHG='2',FTAG='2',FTR='D'))
    return out.getvalue().encode()
class ProviderTests(unittest.TestCase):
    def test_01_10_leagues_no_rare_games(self):
        for l in SOURCES:
            with self.subTest(l=l):
                r=witness_source(l,fake(l),'2026-11-08','2026-11-19')
                self.assertEqual(r['status'],'PROVIDER_OBSERVED_NO_NEW_RESULTS')
                self.assertFalse(r['forecast_source_admitted'])
    def test_02_new_completed_match_is_reported(self):
        r=witness_source('GER1',fake('GER1',added=True),'2026-11-08','2026-11-19')
        self.assertEqual(len(r['new_full_time_in_gap']),1)
    def test_03_source_below_frozen_count_block(self):
        raw=fake('ENG1').decode().splitlines()
        with self.assertRaisesRegex(ProviderBlocked,'BEHIND'):
            witness_source('ENG1',('\n'.join(raw[:-1])+'\n').encode(),'2026-11-08','2026-11-19')
    def test_04_incomplete_row_block(self):
        raw=fake('POR1')+b'14/11/2026,New A,New B,1,,H\n'
        with self.assertRaisesRegex(ProviderBlocked,'INCOMPLETE'):
            witness_source('POR1',raw,'2026-11-08','2026-11-19')
    def test_05_bad_score_block(self):
        raw=fake('BEL1')+b'14/11/2026,New A,New B,0,2,H\n'
        with self.assertRaisesRegex(ProviderBlocked,'MISMATCH'):
            witness_source('BEL1',raw,'2026-11-08','2026-11-19')
    def test_06_duplicate_pair_block(self):
        raw=fake('NED1')+b'12/11/2026,Club0,Other0,1,0,H\n'
        with self.assertRaisesRegex(ProviderBlocked,'DUPLICATE'):
            witness_source('NED1',raw,'2026-11-08','2026-11-19')
    def test_07_future_result_block(self):
        raw=fake('ESP1')+b'21/11/2026,New A,New B,1,0,H\n'
        with self.assertRaisesRegex(ProviderBlocked,'FUTURE_SCORE'):
            witness_source('ESP1',raw,'2026-11-08','2026-11-19')
    def test_08_10_league_combined_scan(self):
        latest={k:'2026-11-08' for k in SOURCES}
        r=audit_ten(latest,'2026-11-19',fetcher=lambda u:(u,fake(next(k for k,v in SOURCES.items() if v+'.csv' in u))))
        self.assertEqual(r['unarchived_completed_rows'],0)
        self.assertFalse(r['production_forecast_allowed'])
if __name__=='__main__':unittest.main(verbosity=2)
