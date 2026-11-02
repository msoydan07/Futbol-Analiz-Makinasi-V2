"""New M4 + four-model forward contract acceptance; never refits legacy trials."""
import csv
import hashlib
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from m4_integrated import CANDIDATES, fit_m4, predict_m4, score_markets, dev_select, use_lock
from forward_c3 import canonical_bytes
from forward_quad import predict_quad_from_verified_gate, SCHEMA, FROZEN
from evaluate_quad import report

HISTORY=Path(os.environ.get('M4_TEST_HISTORY','historical_results.csv'))
LOCK=Path(__file__).with_name('m4_lock.json')
NOW=datetime(2026,11,1,12,0,tzinfo=timezone.utc)

class M4Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not HISTORY.is_file():raise unittest.SkipTest('M4_TEST_HISTORY pinned source not supplied')
        if hashlib.sha256(HISTORY.read_bytes()).hexdigest()!=FROZEN:raise ValueError('source_sha_not_pinned')
        with HISTORY.open(encoding='utf-8-sig',newline='') as f:
            cls.data=list(csv.DictReader(f))
        cls.lock=json.loads(LOCK.read_text())
        cls.settings=use_lock(cls.lock)
        assert cls.lock['settings'] in [c.__dict__ for c in CANDIDATES]
        teams=sorted(set(r['home_id'] for r in cls.data if r['league']=='ENG1' and r['season']=='2026-2027'))
        cls.home,cls.away=teams[0],teams[1]
        cls.gate={'status':'VERIFIED','league':'ENG1','home_id':cls.home,'away_id':cls.away,
                  'source_url':'https://example.org/SYNTHETIC_TEST_ONLY',
                  'kickoff_utc':(NOW+timedelta(days=2)).isoformat(),
                  'retrieved_at_utc':NOW.isoformat()}

    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);self.path=self.root/'historical_results.csv'
        shutil.copyfile(HISTORY,self.path);self.out=self.root/'records'

    def create(self,gate=None):
        return predict_quad_from_verified_gate(gate or self.gate,self.path,self.out,LOCK,now=NOW)

    def test_exact_source_and_lock(self):
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),FROZEN)
        self.assertEqual(self.lock['evaluation_season_excluded'],'2026-2027')
        with self.assertRaises(ValueError):use_lock({**self.lock,'settings':{'half_life_days':1,'ridge_shared':4,'ridge_venue':48}})

    def test_coherent_probabilities(self):
        fit=fit_m4(self.data,'ENG1','2026-11-02',self.settings)
        mu=predict_m4(fit,self.home,self.away)
        self.assertTrue(mu is not None)
        s=score_markets(*mu)
        self.assertAlmostEqual(sum(s['markets']['1X2'].values()),1,places=10)
        self.assertAlmostEqual(s['markets']['BTTS_YES']+s['markets']['BTTS_NO'],1,places=10)
        for line in ('1.5','2.5','3.5'):
            self.assertAlmostEqual(s['markets']['OVER_'+line]+s['markets']['UNDER_'+line],1,places=10)
        self.assertLess(s['tail_mass'],1e-9)
        self.assertTrue(s['top_scores'])

    def test_same_day_outcome_not_used(self):
        cutoff='2026-11-02'
        base=fit_m4(self.data,'ENG1',cutoff,self.settings)
        pred=predict_m4(base,self.home,self.away)
        added={**self.data[0],'fixture_id':'SYNTHETIC_SAME_DAY','league':'ENG1','match_date':cutoff,
               'home_id':self.home,'away_id':self.away,'home_goals':'40','away_goals':'0','result':'H'}
        new=fit_m4(self.data+[added],'ENG1',cutoff,self.settings)
        self.assertEqual(pred,predict_m4(new,self.home,self.away))

    def test_future_season_cannot_tune_m4(self):
        # Learning selection reads only 2025/26. Deliberately poison later rows.
        corrupt=[{**r,'home_goals':'40','away_goals':'0','result':'H'} if r['season']=='2026-2027' else r for r in self.data]
        rebuilt=dev_select(corrupt)
        self.assertEqual(self.lock['settings'],rebuilt['settings'])
        self.assertEqual(self.lock['winner_dev']['n'],rebuilt['winner_dev']['n'])
        self.assertAlmostEqual(self.lock['winner_dev']['logloss'],rebuilt['winner_dev']['logloss'],places=12)

    def test_four_models_and_no_overwrite(self):
        name,data=self.create()
        self.assertEqual(data['schema'],SCHEMA)
        self.assertEqual(set(data['model_predictions']),{'B','C2','C3','M4'})
        self.assertEqual(data['status'],'EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING')
        self.assertEqual(data['model_predictions']['M4']['status'],'AVAILABLE')
        self.assertEqual(data['data']['snapshot_sha256'],FROZEN)
        self.assertEqual(name.read_bytes().count(b'payload_sha256'),1)
        before=name.read_bytes()
        with self.assertRaises(FileExistsError):self.create()
        self.assertEqual(name.read_bytes(),before)

    def test_invalid_gate_and_bad_history_do_not_register(self):
        for changes in ({'status':'UNVERIFIED'},
                        {'kickoff_utc':(NOW-timedelta(seconds=1)).isoformat()},
                        {'retrieved_at_utc':(NOW-timedelta(hours=26)).isoformat()},
                        {'kickoff_utc':(NOW+timedelta(days=9)).isoformat()}):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):self.create({**self.gate,**changes})
        self.assertFalse(self.out.exists())
        # Modified historical result cannot be passed as the pinned baseline.
        content=self.path.read_text(encoding='utf-8')
        self.path.write_text(content.replace('BEL1','ZEL1',1),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'updated_history_requires_baseline'):
            self.create()

    def test_sealed_evaluator_and_tamper_guard(self):
        file,data=self.create()
        self.assertEqual(report(self.out,self.path,now=NOW)['finished_matched'],0)
        with self.path.open(encoding='utf-8-sig',newline='') as f:
            fields=next(csv.reader(f))
        actual=dict(self.data[0]);actual.update({'fixture_id':'SYNTHETIC_NEW_RESULT',
                 'league':'ENG1','home_id':self.home,'away_id':self.away,
                 'match_date':data['fixture']['match_local_date'],'home_goals':'1','away_goals':'0','result':'H'})
        final=self.root/'later.csv'
        with final.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerow(actual)
        seen=report(self.out,final,now=NOW+timedelta(days=4))
        self.assertEqual(seen['finished_matched'],1)
        self.assertEqual(seen['model_scores']['M4']['n'],1)
        self.assertEqual(seen['four_way_common']['n'],int(all(data['model_predictions'][m]['status']=='AVAILABLE' for m in ('B','C2','C3','M4'))))
        tampered=json.loads(file.read_text())
        tampered['model_predictions']['M4']['goals']['markets']['1X2']['H']=.999
        file.write_text(json.dumps(tampered))
        with self.assertRaisesRegex(ValueError,'tampered_prediction'):
            report(self.out,final,now=NOW+timedelta(days=4))

if __name__=='__main__':unittest.main()
