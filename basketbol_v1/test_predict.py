"""Safety: no backdated pregame computer output; missing official fixture marked."""
import sys,unittest
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from predict import calculate
class Tests(unittest.TestCase):
    def test_retroactive_scenario_request_denied_before_any_network(self):
        with self.assertRaises(ValueError):
            calculate(league="NBA",day="2026-11-01",home="DEN",away="LAL",
                      clock=datetime(2026,11,9,15,tzinfo=timezone.utc))
if __name__=="__main__":unittest.main()
