"""New §12/13 test only: no historical model or forward record is rerun."""
from unittest import TestCase,main
from datetime import datetime,timedelta,timezone
from classification_odds_263 import classify,poisson_market,explain,DecisionError
NOW=datetime(2026,11,2,7,0,tzinfo=timezone.utc)
KO=(NOW+timedelta(days=5)).isoformat()
QUOTE={'fixture_key':'SYNTHETIC','market_group':'MS','verification':'INDEPENDENTLY_CHECKED',
       'stage':'PREMATCH','source':'SYNTHETIC','source_url':'https://example.org/synthetic',
       'checked_at_utc':NOW.isoformat(),'decimal_odds':{'MS1':1.35,'MSX':5.,'MS2':9.}}
def get(selection='MS1',lh=2.8,la=.3,**overrides):
    opts=dict(model='C2',markets=poisson_market(lh,la),selection=selection,
              lambda_home=lh,lambda_away=la,fixture_key='SYNTHETIC',
              kickoff=KO,now=NOW,league='TUR1',model_level='BASIT',
              data_reliability='ORTA',context_ok=True,
              critical_unverified_effect=False,fixture_verified=True)
    opts.update(overrides)
    return classify(**opts)
class ABCContract(TestCase):
    def test_A_without_price(self):
        r=get()
        self.assertEqual(r['candidate_class'],'A_ADAYI')
        self.assertIsNone(r['EV']);self.assertIsNone(r['official_class'])
    def test_A_plus_B_with_complete_synthetic_price(self):
        r=get(quote=QUOTE)
        self.assertEqual(r['candidate_class'],'A+B_ADAYI')
        self.assertTrue(r['B_condition']);self.assertIn('başa baş',explain(r))
    def test_unverified_or_missing_competing_price_no_B(self):
        for q in ({**QUOTE,'verification':'USER_PROVIDED'},
                  {**QUOTE,'decimal_odds':{'MS1':1.35}}):
            self.assertIsNone(get(quote=q)['EV'])
    def test_wrong_match_and_market_fail(self):
        with self.assertRaises(DecisionError):get(quote={**QUOTE,'fixture_key':'WRONG'})
        with self.assertRaises(DecisionError):get(quote={**QUOTE,'market_group':'GOALS_2.5'})
    def test_low_quality_never_becomes_C(self):
        self.assertEqual(get(context_ok=False)['candidate_class'],'DEGERLENDIRILEMEDI')
    def test_nonexclusive_double_chance_no_value(self):
        self.assertIsNone(get(selection='1X',quote=QUOTE)['EV'])
    def test_prices_do_not_change_model_percent(self):
        self.assertEqual(get()['model_probability'],get(quote=QUOTE)['model_probability'])
    def test_no_0_5_high_filter(self):
        with self.assertRaises(DecisionError):get(selection='OVER_0.5')
if __name__=='__main__':main()
