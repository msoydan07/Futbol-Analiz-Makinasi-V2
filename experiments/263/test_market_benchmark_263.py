"""Only new observational benchmark checks. Never re-run historical model tests."""
import unittest
from datetime import datetime,timedelta,timezone
from copy import deepcopy
from classification_odds_263 import poisson_market
from market_benchmark_263 import compare,render,MarketReferenceError

NOW=datetime(2026,11,2,12,0,tzinfo=timezone.utc)
KO=(NOW+timedelta(days=5)).isoformat()
def model(p):
    m=poisson_market(1.6,.6)
    m["MS1"]=p;m["MSX"]=(1-p)*.65;m["MS2"]=(1-p)*.35
    m["1X"]=m["MS1"]+m["MSX"];m["X2"]=m["MSX"]+m["MS2"];m["12"]=m["MS1"]+m["MS2"]
    return {"status":"AVAILABLE","goals":{"markets":m}}
def four():return {"B":model(.64),"C2":model(.79),"C3":model(.65),"M4":model(.66)}
def quote(**kw):
    q={"fixture_key":"TEST","market_group":"MS","stage":"PREMATCH",
       "verification":"INDEPENDENTLY_CHECKED","source":"SYNTHETIC_NOT_REAL",
       "source_url":"https://example.org/test-only",
       "checked_at_utc":NOW.isoformat(),
       "decimal_odds":{"MS1":1.50,"MSX":4.50,"MS2":7.00}}
    q.update(kw);return q
def run(m=None,q=None):
    return compare(models=m if m is not None else four(),
                   quote=q if q is not None else quote(),
                   fixture_key="TEST",kickoff=KO,now=NOW)

class DescriptiveOnlyTests(unittest.TestCase):
    def test_no_vig_is_normalized_from_all_three_bookmaker_prices(self):
        x=run()
        expected=(1/1.5)/(1/1.5+1/4.5+1/7)
        self.assertAlmostEqual(x["no_vig_probabilities"]["MS1"],expected)
        self.assertAlmostEqual(sum(x["no_vig_probabilities"].values()),1)
    def test_example_C3_closest_to_MS1_without_becoming_primary(self):
        x=run()
        self.assertEqual(x["closest_per_selection"]["MS1"],["C3"])
        self.assertFalse(x["model_selected"]);self.assertFalse(x["A_B_C_approved"])
        self.assertFalse(x["pilot_recorded"])
    def test_model_with_high_ev_is_not_automatically_best(self):
        x=run()
        c2=next(r for r in x["model_comparison"] if r["model"]=="C2")
        self.assertAlmostEqual(c2["selections"][0]["arithmetic_ev_not_a_value_approval"],.185)
        self.assertTrue(x["closest_does_not_mean_best_model"])
        self.assertIn("Kayıt yok",render(x))
    def test_missing_counter_prices_prevents_comparison(self):
        self.assertEqual(run(q=quote(decimal_odds={"MS1":1.5}))["status"],
                         "NO_VERIFIED_COMPLETE_ANALYSIS_TIME_ODDS")
    def test_outdated_quote_prevents_comparison(self):
        stale=quote(checked_at_utc=(NOW-timedelta(minutes=11)).isoformat())
        self.assertEqual(run(q=stale)["status"],"NO_VERIFIED_COMPLETE_ANALYSIS_TIME_ODDS")
    def test_wrong_match_cannot_be_comparable(self):
        with self.assertRaisesRegex(ValueError,"WRONG_MATCH_ODDS"):
            run(q=quote(fixture_key="OTHER"))
    def test_missing_model_is_unavailable_not_zero(self):
        m=four();m["C2"]={"status":"UNAVAILABLE","reason":"not_enough_data"}
        x=run(m=m)
        self.assertEqual(next(r for r in x["model_comparison"] if r["model"]=="C2")["status"],"UNAVAILABLE")
    def test_comparison_does_not_mutate_original_predictions(self):
        m=four();orig=deepcopy(m);run(m=m);self.assertEqual(m,orig)
    def test_no_quote_stops(self):
        x=compare(models=four(),quote=None,fixture_key="TEST",kickoff=KO,now=NOW)
        self.assertEqual(x["status"],"NO_VERIFIED_COMPLETE_ANALYSIS_TIME_ODDS")
    def test_nonexclusive_double_chance_cannot_be_normalized_as_MS(self):
        with self.assertRaisesRegex(MarketReferenceError,"EXCLUSIVE"):
            run(q=quote(market_group="DOUBLE_CHANCE",decimal_odds={"1X":1.2}))
    def test_two_sided_KG_and_over_under_supported(self):
        for group,prices in [("KG",{"BTTS_YES":1.9,"BTTS_NO":1.9}),
                             ("GOALS_2.5",{"OVER_2.5":1.9,"UNDER_2.5":1.9})]:
            x=run(q=quote(market_group=group,decimal_odds=prices))
            self.assertEqual(x["status"],"DESCRIPTIVE_ONLY_NOT_MODEL_SELECTION")

if __name__=="__main__":unittest.main()
