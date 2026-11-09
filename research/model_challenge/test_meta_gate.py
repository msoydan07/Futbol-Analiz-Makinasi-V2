"""Gate tests use entirely synthetic expert forecasts, no real match labels."""
import unittest
try:
    from meta_gate import fit_oof, frozen_predict, features, norm
except ModuleNotFoundError:
    fit_oof = frozen_predict = features = norm = None

def rows(n=120):
    data=[]
    for i in range(n):
        a={"H":0.45+(i%3)*.04,"D":.25,"A":.30-(i%3)*.04}
        b={"H":.25+(i%5)*.05,"D":.30,"A":.45-(i%5)*.05}
        data.append({"league":"ENG1","date":f"2025-01-{i%28+1:02d}",
            "home_id":f"home-{i}","away_id":f"away-{i}",
            "trained_history_cutoff":"2024-12-31",
            "forecast_provenance":"OUT_OF_FOLD_BEFORE_MATCH",
            "m4":a,"xgboost":b,"result":"H" if i%3==0 else "A"})
    return data

@unittest.skipIf(fit_oof is None, 'Scientific Python dependencies installed in dedicated meta-gate workflow')
class GateTests(unittest.TestCase):
    def test_frozen_predict_is_valid(self):
        p,w=frozen_predict({"H":.6,"D":.2,"A":.2},
                           {"H":.4,"D":.3,"A":.3},(0,0,0,0,0))
        self.assertAlmostEqual(w,.5)
        self.assertAlmostEqual(sum(p.values()),1)
        self.assertAlmostEqual(p["H"],.5)
    def test_reject_in_sample_predictions(self):
        r=rows();r[0]["forecast_provenance"]="IN_SAMPLE"
        with self.assertRaises(ValueError):fit_oof(r)
    def test_reject_future_training_cutoff(self):
        r=rows();r[0]["trained_history_cutoff"]="2025-02-01"
        with self.assertRaises(ValueError):fit_oof(r)
    def test_reject_duplicates(self):
        r=rows();r[1]=dict(r[0])
        with self.assertRaises(ValueError):fit_oof(r)
    def test_only_predefined_gate_features(self):
        v=features({"H":.55,"D":.25,"A":.2},{"H":.3,"D":.3,"A":.4})
        self.assertEqual(len(v),5)
    def test_training_is_deterministic(self):
        a=fit_oof(rows());b=fit_oof(rows())
        self.assertEqual(a,b)
        p,w=frozen_predict({"H":.55,"D":.25,"A":.2},
                           {"H":.3,"D":.3,"A":.4},a)
        self.assertAlmostEqual(sum(p.values()),1)
        self.assertTrue(0<w<1)

if __name__=="__main__":
    unittest.main()
