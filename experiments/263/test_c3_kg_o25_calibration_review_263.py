"""Tests for research-only frozen C3 KG/O25 calibrator, no odds or refitting."""
from __future__ import annotations
import copy
import tempfile
import unittest
from pathlib import Path
from c3_kg_o25_calibration_review_263 import (_record,_score_one,_accepted_lock,
                 summarize,paired_date_bootstrap,REPO,WANTED)

class C3CalibrationUnit(unittest.TestCase):
    def rows(self,market,n=24):
        # Deterministic dates, no external historical results.
        return [_record("2026-10-%02d"%(1+i//2),"ENG1",market,
                       0.75 if i%3 else 0.22,0.51 if market=="BTTS_YES" else .54,
                       int(i%4 in (0,1)),"SYNTHETIC_ONLY")
                for i in range(n)]

    def test_frozen_580_dev_lock_and_complements(self):
        weights,sha=_accepted_lock(REPO/"experiments/263/forward_dev_calibration_lock_263.json")
        self.assertEqual(set(weights),set(WANTED))
        self.assertAlmostEqual(weights["BTTS_YES"],.5083407177)
        self.assertAlmostEqual(weights["OVER_2.5"],.3113038451)
        self.assertEqual(len(sha),64)
        for key in WANTED:
            r=_record("2026-10-01","ENG1",key,.73,.46,1,"SYNTHETIC_ONLY")
            q=_score_one(r,weights[key])
            self.assertAlmostEqual(q+(1-q),1)
            self.assertGreaterEqual(q,0)
            self.assertLessEqual(q,1)

    def test_only_existing_earlier_dev_weights(self):
        weights,_=_accepted_lock(REPO/"experiments/263/forward_dev_calibration_lock_263.json")
        for key in WANTED:
            r=_record("2026-10-01","ENG1",key,.70,.41,0,"SYNTHETIC_ONLY")
            q=_score_one(r,weights[key])
            self.assertAlmostEqual(q,.41+weights[key]*(.70-.41))
            # A radically different outcome cannot be treated as a feature:
            z=copy.deepcopy(r);z["outcome"]=1
            self.assertEqual(q,_score_one(z,weights[key]))

    def test_nonfinite_probability_blocks(self):
        for p in (float("nan"),float("inf"),-0.01,1.01,True):
            with self.assertRaises(ValueError):
                _record("2026-10-01","ENG1","BTTS_YES",p,.5,0,"SYNTHETIC")

    def test_unavailable_early_season_weight_cannot_be_forged(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"tampered.json"
            src=REPO/"experiments/263/forward_dev_calibration_lock_263.json"
            text=src.read_text(encoding="utf-8").replace(
                '"weight": 0.5083407177','"weight": 0.9000000000')
            path.write_text(text,encoding="utf-8")
            with self.assertRaises(ValueError):
                _accepted_lock(path)

    def test_score_and_calibration_bins_consistent(self):
        rows=self.rows("OVER_2.5",n=24)
        s=summarize(rows,"OVER_2.5",.31)
        self.assertEqual(s["n"],24)
        for method in ("raw","frozen","baseline"):
            self.assertEqual(sum(x["n"] for x in
                 s["methods"][method]["reliability_bins"]),24)

    def test_bootstrap_keeps_matchday_groups_together(self):
        rows=self.rows("BTTS_YES",n=24)
        r=paired_date_bootstrap(rows,.51,reps=100,seed=20)
        self.assertTrue(r["available"])
        self.assertEqual(r["days"],12)
        self.assertEqual(r["n"],24)
        self.assertEqual(len(r["ci95"]),2)

    def test_one_date_nov_seal_cannot_claim_bootstrap_confidence(self):
        rows=[_record("2026-11-08","TUR1","BTTS_YES",.5,.48,i%2,
                     "SYNTHETIC_ONLY") for i in range(39)]
        ci=paired_date_bootstrap(rows,.5)
        self.assertFalse(ci["available"])

if __name__=="__main__":
    unittest.main()
