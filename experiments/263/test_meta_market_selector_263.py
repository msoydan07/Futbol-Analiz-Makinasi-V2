"""Synthetic no-leak and coherent-family contracts for read-only meta selector."""
import unittest
from meta_market_selector_263 import BASE, FAMILIES, valid, loss, choose, score, select_static

def sample(day="2026-09-01",league="ENG1", winner="M4"):
    good={"MS1":.8,"MSX":.1,"MS2":.1,"BTTS_YES":.8,"BTTS_NO":.2,
          "OVER_1.5":.85,"UNDER_1.5":.15,
          "OVER_2.5":.75,"UNDER_2.5":.25,
          "OVER_3.5":.65,"UNDER_3.5":.35}
    bad={"MS1":.1,"MSX":.45,"MS2":.45,"BTTS_YES":.2,"BTTS_NO":.8,
          "OVER_1.5":.5,"UNDER_1.5":.5,
          "OVER_2.5":.3,"UNDER_2.5":.7,
          "OVER_3.5":.1,"UNDER_3.5":.9}
    obs={"MS1":1,"MSX":0,"MS2":0,"BTTS_YES":1,"BTTS_NO":0,
         "OVER_1.5":1,"UNDER_1.5":0,
         "OVER_2.5":1,"UNDER_2.5":0,
         "OVER_3.5":1,"UNDER_3.5":0}
    return {"date":day,"league":league,"p":{winner:good, ("C3" if winner=="M4" else "M4"):bad},"obs":obs}

class MetaTests(unittest.TestCase):
    def test_families_whole(self):
        r=sample()
        for f in FAMILIES:self.assertTrue(valid(r,"M4",f))
        self.assertEqual(select_static(r,"MS","fixed"),"M4")
        self.assertEqual(select_static(r,"KG","fixed"),"C3")
        self.assertEqual(select_static(r,"GOALS","fixed"),"C3")
        o=score(r, {f:BASE[f] for f in FAMILIES})
        self.assertEqual(o["MS"]["model"],"M4")
        self.assertEqual(o["KG"]["model"],"C3")

    def test_probability_sum_and_consistency(self):
        r=sample()
        r["p"]["M4"]["MS2"]=.2
        self.assertFalse(valid(r,"M4","MS"))
        r=sample()
        r["p"]["C3"]["OVER_1.5"]=.2
        r["p"]["C3"]["UNDER_1.5"]=.8
        self.assertFalse(valid(r,"C3","GOALS"))

    def test_never_read_same_day_results(self):
        r=sample("2026-10-01")
        same=[sample("2026-10-01") for _ in range(400)]
        chosen,meta=choose(r,same,"MS")
        self.assertEqual(chosen,"M4")
        self.assertEqual(meta["prior_paired"],0)

    def test_sufficient_prior_switch_can_learn(self):
        from datetime import date,timedelta
        prior=[sample((date(2026,8,1)+timedelta(days=i//8)).isoformat(),winner="C3")
               for i in range(160)]
        current=sample("2026-10-01")
        chosen,why=choose(current,prior,"MS")
        self.assertEqual(chosen,"C3")
        self.assertEqual(why["reason"],"PAST_BRIER_SUPPORTS_SWITCH")
        self.assertTrue(why["latest_training_date"]<current["date"])

    def test_default_prior_too_small(self):
        prior=[sample("2026-08-01",winner="C3") for _ in range(150)]
        chosen,why=choose(sample("2026-10-01"),prior,"MS")
        self.assertEqual(chosen,"M4")
        self.assertEqual(why["reason"],"NOT_ENOUGH_PAST_USE_DEFAULT")

    def test_bad_confidence_fails_closed(self):
        r=sample()
        r["p"]["M4"]["BTTS_YES"]=float("nan")
        self.assertFalse(valid(r,"M4","KG"))
        with self.assertRaises(ValueError):loss(r,"M4","KG")

if __name__=="__main__":
    unittest.main()
