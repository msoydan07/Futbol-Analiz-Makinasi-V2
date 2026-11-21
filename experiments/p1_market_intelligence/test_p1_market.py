"""Deterministic standard-library unit checks; no impact on 2.6.3."""
import math
import tempfile
import json
from pathlib import Path
import unittest
from p1_market import (no_vig, poisson_markets, fit_inverse_poisson,
                       analyze_prices, best_choices, score_observed,
                       archive_record_to_input, run_archive, _sha_json, MarketDataError)

class TestP1(unittest.TestCase):
    def setUp(self):
        # Real morning prices transcribed from 21.11.2026 Amed-Rizespor
        # archived user iddaa PDF references; NOT a verified historical backtest.
        self.amed = {'MS': {'MS1':1.70,'MSX':3.51,'MS2':3.52},
                     'OU25': {'UNDER_2.5':2.15, 'OVER_2.5':1.44},
                     'KG': {'BTTS_YES':1.42,'BTTS_NO':2.21}}

    def test_marketwise_normalization(self):
        for method in ('proportional','additive','power'):
            for group in self.amed.values():
                r = no_vig(group,method)
                self.assertAlmostEqual(sum(r['probabilities'].values()),1,places=10)
                self.assertGreater(min(r['probabilities'].values()),0)
                self.assertGreater(r['book_margin'],0)

    def test_market_outcomes_poisson(self):
        p=poisson_markets(2.0,1.0)
        for d in p.values():self.assertAlmostEqual(sum(d.values()),1,places=10)
        self.assertAlmostEqual(p['KG']['BTTS_YES'],(1-math.exp(-2))*(1-math.exp(-1)),places=11)
        self.assertAlmostEqual(p['OU25']['UNDER_2.5'],math.exp(-3)*(1+3+4.5),places=11)

    def test_inverse_recovers_coherent_poisson(self):
        original=poisson_markets(1.82,0.95)
        recovered=fit_inverse_poisson(original)
        self.assertAlmostEqual(recovered['lambda_home'],1.82,delta=0.0008)
        self.assertAlmostEqual(recovered['lambda_away'],0.95,delta=0.0008)
        self.assertLess(recovered['max_residual_pp'],0.03)

    def test_real_archived_price_first_only(self):
        a=analyze_prices(self.amed)
        self.assertAlmostEqual(a['p0']['MS']['MS1'],(1/1.7)/(1/1.7+1/3.51+1/3.52),places=10)
        self.assertGreater(a['p1']['lambda_home'],0)
        self.assertGreater(a['p1']['lambda_away'],0)
        self.assertEqual(len([k for d in a['p1']['p1_probabilities'].values() for k in d]),7)

    def test_no_missing_opposites_fabrication(self):
        incomplete={**self.amed,'OU25':{'UNDER_2.5':2.15}}
        with self.assertRaises(MarketDataError):analyze_prices(incomplete)
        with self.assertRaises(MarketDataError):no_vig({'MS1':True,'MS2':2.0})
        with self.assertRaises(MarketDataError):archive_record_to_input({},'invalid.json')

    def test_alternative_other_family(self):
        a=analyze_prices(self.amed)
        for route in ('p0_select','p1_select'):
            self.assertNotEqual(a[route]['main']['family'],a[route]['alternative_different_family']['family'])

    def test_readonly_archived_record_and_missing_group(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            base = {
                'schema': '263_SECOND_PDF_COMMENTARY_APPEND_ONLY_V1',
                'match': {'home':'Amed', 'away':'Rizespor', 'league':'TUR1', 'date_tr':'2026-11-21'},
                'record_kind': 'SYNTHETIC_TEST_ONLY',
                'source_pdf_fingerprints': {'first_pdf_sha256':'f' * 64},
                'second_pdf_observation': {'quoted_families': {
                    'MS_1_X_2':{'before':[1.70,3.51,3.52]},
                    'OVER_UNDER_2_5':{'before':[2.15,1.44]},
                    'BTTS_YES_NO':{'before':[1.42,2.21]}}}}
            base['record_sha256'] = _sha_json(base)
            (path/'full.json').write_text(json.dumps(base))
            partial = json.loads(json.dumps(base))
            del partial['second_pdf_observation']['quoted_families']['OVER_UNDER_2_5']
            partial['record_sha256'] = _sha_json({k:v for k,v in partial.items() if k!='record_sha256'})
            (path/'partial.json').write_text(json.dumps(partial))
            rep=run_archive(path)
            self.assertEqual(rep['full_quotes_analyzed'],1)
            self.assertEqual(len(rep['excluded']),1)
            self.assertIn('INCOMPLETE_FIRST_PDF_GROUP',rep['excluded'][0]['reason'])
            # Same record cannot be silently edited while keeping its old checksum.
            base['match']['home']='Changed'
            with self.assertRaises(MarketDataError):archive_record_to_input(base,'edited.json')

    def test_scoring_does_not_count_seven_independent_matches(self):
        p=poisson_markets(1.7,1.2)
        got=score_observed(p,1,0)
        self.assertEqual(len(got['brier_by_market']),3)
        self.assertEqual(got['truth'],{'MS':'MS1','OU25':'UNDER_2.5','KG':'BTTS_NO'})
        with self.assertRaises(MarketDataError):score_observed(p,True,0)

if __name__=='__main__':
    unittest.main()
