"""One offline batch of safety tests. All fixtures here are SYNTHETIC stubs.
No official source is queried; no real prematch prediction is created.
"""
import csv
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from forward_c3 import predict_from_verified_gate
from evaluate_forward import collect, report

SOURCE = Path(__file__).resolve().parents[1] / '263_toplu_deney' / 'historical_results.csv'
# When executed inside the repository checkout supply the source via env var.
if not SOURCE.is_file():
    SOURCE=Path(os.environ.get('C3_TEST_HISTORY','nonexistent.csv'))
NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def sample_gate(rows, now=NOW):
    teams = {r['home_id'] for r in rows if r['league']=='ENG1'}
    team_list=sorted(teams)
    assert len(team_list)>=2
    return {'status':'VERIFIED', 'league':'ENG1', 'home_id':team_list[0], 'away_id':team_list[1],
            'source_url':'https://example.org/SYNTHETIC_NOT_REAL',
            'kickoff_utc':(now+timedelta(days=2)).isoformat(),
            'retrieved_at_utc':now.isoformat()}

class ForwardFrozenContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SOURCE.is_file():
            raise unittest.SkipTest('Provide real locked snapshot via C3_TEST_HISTORY to run this acceptance test')
        with SOURCE.open(encoding='utf-8-sig',newline='') as f:
            cls.rows=list(csv.DictReader(f))
        cls.gate=sample_gate(cls.rows)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.path=self.root/'historical_results.csv'
        shutil.copyfile(SOURCE,self.path)
        self.out=self.root/'future_records'

    def create(self,gate=None):
        return predict_from_verified_gate(gate or self.gate,self.path,self.out,now=NOW)

    def test_probability_snapshot_hash_and_no_overwrite(self):
        path,record=self.create()
        self.assertTrue(path.exists())
        self.assertEqual(record['status'],'EXPERIMENTAL_PREMATCH_NOT_FOR_BETTING')
        self.assertEqual(record['fixture']['fixture_verification'],'VERIFIED_BY_LIVE_OFFICIAL_GATE')
        self.assertAlmostEqual(sum(record['probabilities']['C3_opponent_adjusted'].values()),1,places=10)
        self.assertEqual(len(record['data']['snapshot_sha256']),64)
        before=path.read_bytes()
        with self.assertRaises(FileExistsError):self.create()
        self.assertEqual(path.read_bytes(),before)

    def test_reject_unverified_and_started_matches(self):
        for updates in ({'status':'NOT_VERIFIED'},
                        {'kickoff_utc':(NOW-timedelta(minutes=2)).isoformat()},
                        {'retrieved_at_utc':(NOW-timedelta(hours=25)).isoformat()},
                        {'kickoff_utc':(NOW+timedelta(days=9)).isoformat()}):
            invalid={**self.gate,**updates}
            with self.subTest(updates=updates):
                with self.assertRaises(ValueError):self.create(invalid)
        self.assertFalse(self.out.exists())

    def test_no_future_or_same_day_leakage(self):
        _,baseline=self.create()
        target=(NOW+timedelta(days=2)).date().isoformat()
        new=dict(self.rows[0])
        new.update({'fixture_id':'SYNTH-9001','league':'ENG1','match_date':target,
                    'home_goals':'30','away_goals':'0','result':'H'})
        with self.path.open('a',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=self.rows[0]);w.writerow(new)
        second=self.out.parent/'second'
        _,changed=predict_from_verified_gate(self.gate,self.path,second,now=NOW)
        self.assertEqual(baseline['probabilities']['C3_opponent_adjusted'],changed['probabilities']['C3_opponent_adjusted'])
        self.assertEqual(baseline['data']['league_history_rows'],changed['data']['league_history_rows'])
        self.assertNotEqual(baseline['data']['snapshot_sha256'],changed['data']['snapshot_sha256'])

    def test_stale_data_blocks(self):
        later=NOW+timedelta(days=11)
        gate={**self.gate,'kickoff_utc':(later+timedelta(days=2)).isoformat(),
              'retrieved_at_utc':later.isoformat()}
        with self.assertRaisesRegex(ValueError,'stale_history'):
            predict_from_verified_gate(gate,self.path,self.out,now=later)

    def test_tamper_detection_and_forward_evaluation(self):
        path,record=self.create()
        fixture=record['fixture']
        with self.path.open(encoding='utf-8-sig',newline='') as f:
            fieldnames=next(csv.reader(f))
        actual=dict(self.rows[0]);actual.update({
            'fixture_id':'SYNTH-FUTURE-ACTUAL', 'league':fixture['league'],
            'home_id':fixture['home_id'],'away_id':fixture['away_id'],
            'match_date':fixture['match_local_date'],'home_goals':'1',
            'away_goals':'0','result':'H'})
        final=self.root/'later_result.csv'
        with final.open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fieldnames);w.writeheader();w.writerow(actual)
        self.assertEqual(collect(self.out,final,now=NOW)[0],[])
        after=NOW+timedelta(days=4)
        evaluation=report(self.out,final,now=after)
        self.assertEqual(evaluation['paired_all_three'],1)
        self.assertEqual(evaluation['outcome'],'NO_PROMOTION_EVIDENCE_YET')
        original=path.read_text(encoding='utf-8')
        changed=json.loads(original)
        changed['probabilities']['C3_opponent_adjusted']['H']=0.99
        path.write_text(json.dumps(changed),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'digest mismatch'):
            collect(self.out,final,now=after)

if __name__=='__main__':unittest.main()
