import unittest
from elo_baseline import predict_stream, probs, score

class EloTests(unittest.TestCase):
    def sample(self, day, home, away, hg, ag):
        return {"date": day, "league": "ENG1", "home": home, "away": away,
                "home_goals": str(hg), "away_goals": str(ag)}

    def test_probabilities_sum_to_one(self):
        for h, a in [(1500, 1500), (1100, 1700), (1900, 1200)]:
            p = probs(h, a, 12, 50)
            self.assertAlmostEqual(sum(p), 1.0)
            self.assertTrue(all(0 < x < 1 for x in p))

    def test_same_date_match_reordering_does_not_leak(self):
        # Teams appear twice on the same date; neither result may affect
        # their other match's day-D pre-match probability.
        first = self.sample("2025-08-01", "A", "B", 8, 0)
        second = self.sample("2025-08-01", "A", "C", 0, 1)
        p1 = list(predict_stream([first, second]))
        first["home_goals"], first["away_goals"] = "0", "8"
        p2 = list(predict_stream([first, second]))
        for a, b in zip(p1, p2):
            self.assertAlmostEqual(a["p_home"], b["p_home"])
            self.assertAlmostEqual(a["p_draw"], b["p_draw"])

    def test_next_date_consumes_previous_result(self):
        rows = [self.sample("2025-08-01", "A", "B", 3, 0),
                self.sample("2025-08-02", "A", "C", 1, 0)]
        out = list(predict_stream(rows))
        self.assertGreater(out[1]["p_home"], out[0]["p_home"])
        self.assertEqual(out[1]["prior_matches_in_league"], 1)

    def test_scoring_is_proper_three_class(self):
        a, b = score((.6, .25, .15), "H")
        self.assertGreater(a, 0)
        self.assertGreater(b, 0)

if __name__ == "__main__":
    unittest.main()
