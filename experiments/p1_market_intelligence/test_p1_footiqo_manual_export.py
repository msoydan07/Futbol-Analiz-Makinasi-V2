import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).parent))
from p1_footiqo_manual_export import inspect

ODD=['id','matchDate','Country','League','Season','homeTeam','awayTeam','H','D','A','O25','U25','BTTSY','BTTSN']
SCORE=['id','matchDate','Country','League','Season','homeTeam','awayTeam','FTHG','FTAG','FTR']

def sample(id='155072',date='08-11-26 21:00'):
    identity={'id':id,'matchDate':date,'Country':'Spain','League':'LaLiga','Season':'2026/2027','homeTeam':'Atletico','awayTeam':'Barcelona'}
    return (dict(identity,H='3.84',D='4.56',A='1.78',O25='1.29',U25='3.62',BTTSY='1.35',BTTSN='3.20'),
            dict(identity,FTHG='1',FTAG='2',FTR='A'))

class FootiqoAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
        self.odds,self.scores=sample()
    def write(self,odds=None,scores=None):
        o=self.folder/'odds.csv'; s=self.folder/'scores.csv'
        for path,keys,items in ((o,ODD,odds or [self.odds]),(s,SCORE,scores or [self.scores])):
            with path.open('w',newline='',encoding='utf-8') as out:
                w=csv.DictWriter(out,fieldnames=keys);w.writeheader();w.writerows(items)
        return o,s
    def runcheck(self,odds=None,scores=None,authorized=True):
        a,b=self.write(odds,scores)
        return inspect(a,b,official_manual_export=authorized,private_noncommercial_research=authorized)
    def test_valid_fixture(self):
        r=self.runcheck();self.assertEqual(r['accepted'],1);self.assertEqual(r['excluded'],0)
        self.assertEqual(r['bookmaker'],'1xBet (publisher attribution, not separately verified)')
        self.assertIn('p0_brier',r['p0_p1_descriptive'])
    def test_missing_kg_rejected(self):
        z=dict(self.odds,BTTSN='');r=self.runcheck([z]);self.assertEqual(r['accepted'],0)
        self.assertEqual(r['reject_reasons'].get('INCOMPLETE_SEVEN_ODDS'),1)
    def test_future_match_rejected(self):
        z=dict(self.odds,matchDate='22-11-26 21:00');r=self.runcheck([z]);self.assertEqual(r['accepted'],0)
    def test_duplicate_odds_rejected(self):
        r=self.runcheck([self.odds,self.odds]);self.assertEqual(r['accepted'],1)
        self.assertEqual(r['reject_reasons'].get('DUPLICATE_ODDS_ID'),1)
    def test_different_name_rejected(self):
        z=dict(self.scores,awayTeam='Different');r=self.runcheck(scores=[z]);self.assertEqual(r['accepted'],0)
        self.assertEqual(r['reject_reasons'].get('SCORE_ODDS_IDENTITY_CONFLICT'),1)
    def test_no_manual_permission_fails(self):
        with self.assertRaisesRegex(ValueError,'ATTESTATION'):
            self.runcheck(authorized=False)
    def test_duplicate_scores_abort(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_SCORE_ID'):
            self.runcheck(scores=[self.scores,self.scores])
    def test_multiple_csvs_supported(self):
        a,b=self.write()
        r=inspect([a],[b],official_manual_export=True,private_noncommercial_research=True)
        self.assertEqual(r['accepted'],1)
        self.assertEqual(len(r['odds_files_sha256']),1)
    def test_wrong_result_letter_rejected(self):
        z=dict(self.scores,FTR='H')
        r=self.runcheck(scores=[z]);self.assertEqual(r['accepted'],0)
        self.assertEqual(r['unusable_score_rows'].get('INCONSISTENT_FINAL_RESULT'),1)
    def test_semicolon_separated(self):
        a,b=self.write();
        for path in (a,b):
            txt=path.read_text();path.write_text(txt.replace(',', ';'))
        r=inspect(a,b,official_manual_export=True,private_noncommercial_research=True)
        self.assertEqual(r['accepted'],1)
    def test_unsound_market_rejected(self):
        z=dict(self.odds,H='1.01',D='1.01',A='1.01')
        r=self.runcheck(odds=[z]);self.assertEqual(r['accepted'],0)
        self.assertEqual(r['reject_reasons'].get('UNUSUAL_MARKET_OVERROUND'),1)

if __name__=='__main__':unittest.main()
