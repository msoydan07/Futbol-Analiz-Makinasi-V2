"""Only new interleague graph/past UEFA completeness gates."""
import unittest
from uefa_xg_free_graph_m2_feasibility_263 import round_number,GraphError,ROUNDS
class FoldsAndRoundTest(unittest.TestCase):
 def test_cl_round_map(self):
    self.assertEqual(round_number("UEFA_CL","2025-09-16"),1)
    self.assertEqual(round_number("UEFA_CL","2025-11-26"),5)
    self.assertEqual(round_number("UEFA_CL","2026-01-28"),8)
 def test_el_round_map(self):
    self.assertEqual(round_number("UEFA_EL","2025-09-24"),1)
    self.assertEqual(round_number("UEFA_EL","2025-12-11"),6)
    self.assertEqual(round_number("UEFA_EL","2026-01-29"),8)
 def test_non_round_does_not_get_fake_previous_match_count(self):
    with self.assertRaisesRegex(GraphError,"UNKNOWN_HISTORICAL"):
        round_number("UEFA_CL","2025-09-25")
 def test_out_of_scope_competition_fails_closed(self):
    with self.assertRaisesRegex(GraphError,"UNKNOWN_COMPETITION"):
        round_number("UEFA_CONF","2025-09-24")
 def test_all_eight_rounds_fixed_both_competitions(self):
    self.assertEqual(len(ROUNDS["UEFA_CL"]),8)
    self.assertEqual(len(ROUNDS["UEFA_EL"]),8)
if __name__=="__main__":unittest.main()
