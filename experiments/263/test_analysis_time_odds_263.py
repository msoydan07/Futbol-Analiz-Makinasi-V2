"""2.6.3 instant-price policy only; NOT a historic backtest or prediction log."""
import unittest
from datetime import datetime,timedelta,timezone

from classification_odds_263 import classify,explain,odds_evidence,poisson_market,DecisionError

NOW=datetime(2026,11,2,12,0,tzinfo=timezone.utc)
KO=(NOW+timedelta(hours=1)).isoformat()
Q={'fixture_key':'TEST_FIXTURE','market_group':'MS',
   'verification':'INDEPENDENTLY_CHECKED','stage':'PREMATCH',
   'source':'TEST_BOOK','source_url':'https://example.org/test-only',
   'checked_at_utc':NOW.isoformat(),
   'decimal_odds':{'MS1':1.50,'MSX':4.40,'MS2':7.90}}


def classify_quote(quote,*,now=NOW,selection='MS1'):
    return classify(model='M4',markets=poisson_market(2.1,.7),
                    selection=selection,lambda_home=2.1,lambda_away=.7,
                    fixture_key='TEST_FIXTURE',kickoff=KO,now=now,league='TUR1',
                    model_level='BASIT',data_reliability='ORTA',context_ok=True,
                    critical_unverified_effect=False,fixture_verified=True,quote=quote)


class AnalysisTimeOddsPolicy(unittest.TestCase):
    def test_current_price_present_and_analysis_time_explained(self):
        result=classify_quote(Q)
        self.assertEqual(result['price']['decimal_odds'],1.5)
        self.assertEqual(result['price']['analysis_at_utc'],NOW.isoformat())
        self.assertEqual(result['price']['checked_at_utc'],NOW.isoformat())
        self.assertIn('Analiz anı oranı 1.50',explain(result))
        self.assertEqual(result['price_policy'],
                         'PRICE_CHECKED_WITHIN_10_MINUTES_OF_ANALYSIS; NO_AFTER_ANALYSIS_REFRESH')
        self.assertFalse(result['pilot_registered'])

    def test_price_old_eleven_minutes_is_rejected_even_though_before_kickoff(self):
        quote={**Q,'checked_at_utc':(NOW-timedelta(minutes=11)).isoformat()}
        result=classify_quote(quote)
        self.assertIsNone(result['price']['decimal_odds'])
        self.assertIsNone(result['EV'])
        self.assertEqual(result['price']['status'],'ODDS_STALE_FOR_ANALYSIS_OVER_10_MINUTES')

    def test_one_selected_verified_odds_is_displayed_but_cannot_be_B(self):
        quote={**Q,'decimal_odds':{'MS1':1.50}}
        result=classify_quote(quote)
        self.assertEqual(result['price']['decimal_odds'],1.5)
        self.assertIsNone(result['price']['no_vig'])
        self.assertIsNone(result['EV'])
        self.assertFalse(result['B_condition'])
        self.assertIn('EV/marjsız avantaj: HESAPLANAMADI',explain(result))

    def test_later_market_change_does_not_mutate_past_analysis(self):
        initial=classify_quote(Q)
        later={**Q,'decimal_odds':{'MS1':1.4,'MSX':4.7,'MS2':8.5}}
        new=classify_quote(later)
        self.assertEqual(initial['price']['decimal_odds'],1.5)
        self.assertNotEqual(new['price']['decimal_odds'],initial['price']['decimal_odds'])
        self.assertEqual(initial['analysis_time_utc'],new['analysis_time_utc'])

    def test_double_chance_price_visible_without_false_threeway_no_vig(self):
        quote={**Q,'market_group':'DOUBLE_CHANCE','decimal_odds':{'1X':1.22}}
        result=classify_quote(quote,selection='1X')
        self.assertEqual(result['price']['decimal_odds'],1.22)
        self.assertIsNone(result['EV'])
        self.assertIsNone(result['price']['no_vig'])
        self.assertEqual(result['price']['status'],
                         'DOUBLE_CHANCE_PRICE_OBSERVED_NO_COMPARABLE_NO_VIG')

    def test_no_fixture_or_live_price_source_cannot_count_as_observed(self):
        for quote in ({**Q,'verification':'USER_PROVIDED'},
                      {**Q,'fixture_key':'NOT_THE_MATCH'},
                      {**Q,'checked_at_utc':(NOW+timedelta(minutes=1)).isoformat()}):
            with self.subTest(quote=quote):
                if quote.get('fixture_key')!='TEST_FIXTURE':
                    with self.assertRaises(DecisionError):classify_quote(quote)
                else:
                    self.assertIsNone(classify_quote(quote)['price']['decimal_odds'])

    def test_after_kickoff_never_qualifies(self):
        with self.assertRaises(DecisionError):
            classify_quote(Q,now=NOW+timedelta(hours=2))


if __name__=='__main__':
    unittest.main()
