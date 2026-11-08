import unittest
from poisson_challenger import estimate, league_factory, outcome_probs, predict, period, CANDIDATES

class PoissonTests(unittest.TestCase):
    def row(self, day, h, a, hg, ag):
        return {"date": day, "league": "ENG1", "home": h, "away": a,
                "home_goals": str(hg), "away_goals": str(ag)}

    def test_probs_are_valid(self):
        for x, y in [(0.2, 0.9), (1.3, 1.4), (3.0, 0.8), (4.5, 4.5)]:
            z = outcome_probs(x, y)
            self.assertAlmostEqual(sum(z), 1.0, places=9)
            self.assertTrue(all(0 <= p <= 1 for p in z))

    def test_no_same_date_result_leakage(self):
        rows = [self.row("2025-01-01", "A", "B", 9, 0),
                self.row("2025-01-01", "A", "C", 1, 1),
                self.row("2025-01-02", "A", "D", 0, 1)]
        before = list(predict(rows, 120, 6.0))
        rows[0]["home_goals"], rows[0]["away_goals"] = "0", "9"
        after = list(predict(rows, 120, 6.0))
        for i in range(2):
            self.assertAlmostEqual(before[i]["p_home"], after[i]["p_home"])
            self.assertAlmostEqual(before[i]["p_draw"], after[i]["p_draw"])
        self.assertNotAlmostEqual(before[2]["p_home"], after[2]["p_home"])

    def test_smaller_parameter_grid_predeclared(self):
        self.assertEqual(len(CANDIDATES), 6)
        self.assertEqual(period({"date": "2024-10-01"}), "dev")
        self.assertEqual(period({"date": "2025-09-01"}), "holdout")

    def test_league_priors_are_finite(self):
        state = league_factory()
        pred = estimate(state, "X", "Y", __import__("datetime").date(2025, 1, 1), 120, 12)
        self.assertAlmostEqual(sum(pred), 1.0)

if __name__ == "__main__":
    unittest.main()
