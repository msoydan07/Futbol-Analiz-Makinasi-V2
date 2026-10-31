"""Independent Model B probability and chronological-safety audit.

Run: python -m unittest test_model_b_math_audit.py
No external data, odds, network, or GitHub Actions required.
"""
import math
import unittest
from datetime import date, timedelta
from experimental_poisson_baseline import estimate, poisson


def fixture(i, day, home, away, hg, ag):
    return {
        "fixture_id": str(i), "league": "ENG1",
        "match_date": day.isoformat(), "home_id": home, "away_id": away,
        "home_goals": str(hg), "away_goals": str(ag),
        "result": "H" if hg > ag else "D" if hg == ag else "A",
    }


class ModelBMathAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        start = date(2025, 8, 1)
        cls.rows = [
            fixture(i, start + timedelta(days=i), "A" if i % 2 else "B",
                    "B" if i % 2 else "A", (i % 4), ((i + 1) % 3))
            for i in range(1, 101)
        ]
        cls.cutoff = date(2026, 2, 1).isoformat()

    def test_poisson_normalization(self):
        for lam in (0.05, 0.7, 1.5, 3.0, 5.0):
            self.assertAlmostEqual(sum(poisson(lam, k) for k in range(60)), 1, places=10)

    def test_model_probability_identities(self):
        p = estimate(self.rows, "ENG1", "A", "B", self.cutoff)
        self.assertIsNotNone(p)
        lh, la = p["lambda_home"], p["lambda_away"]
        mass = p["matrix_mass"]
        self.assertAlmostEqual(p["p_home"] + p["p_draw"] + p["p_away"], mass, places=12)
        self.assertAlmostEqual(mass + p["tail_mass"], 1, places=12)
        # Compare matrix-limited outputs against exact independent-Poisson identities.
        exact_over25 = 1 - math.exp(-(lh + la)) * (1 + lh + la + (lh + la)**2 / 2)
        exact_btts = (1 - math.exp(-lh)) * (1 - math.exp(-la))
        self.assertLessEqual(abs(p["p_over25"] - exact_over25), p["tail_mass"] + 1e-12)
        self.assertLessEqual(abs(p["p_btts"] - exact_btts), p["tail_mass"] + 1e-12)

    def test_no_same_day_or_future_information(self):
        base = estimate(self.rows, "ENG1", "A", "B", self.cutoff)
        contaminated = self.rows + [
            fixture(900, date(2026, 2, 1), "A", "B", 20, 0),
            fixture(901, date(2026, 2, 2), "B", "A", 0, 20),
        ]
        self.assertEqual(base, estimate(contaminated, "ENG1", "A", "B", self.cutoff))

    def test_prior_match_changes_prediction(self):
        base = estimate(self.rows, "ENG1", "A", "B", self.cutoff)
        altered = [dict(r) for r in self.rows]
        altered[-1]["home_goals"] = "9"
        altered[-1]["result"] = "H"
        updated = estimate(altered, "ENG1", "A", "B", self.cutoff)
        self.assertNotEqual(base["lambda_home"], updated["lambda_home"])


if __name__ == "__main__":
    unittest.main()
