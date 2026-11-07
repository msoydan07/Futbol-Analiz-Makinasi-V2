"""14.00 request, 14.xx GitHub completion grace and 15.00 fail-closed."""
import unittest
from datetime import datetime,timezone,timedelta
from sabah_manual_window_263 import in_manual_window,DISPLAY_WINDOW

class ManualWindowTests(unittest.TestCase):
    def test_istanbul_morning_open_and_14_is_accepted(self):
        for hour,minute,second in [(5,0,0),(11,30,0),(13,59,59),(14,0,0),(14,59,59)]:
            local=datetime(2026,11,8,hour,minute,second,tzinfo=timezone(timedelta(hours=3)))
            self.assertTrue(in_manual_window(local),str(local))
        self.assertEqual(DISPLAY_WINDOW,"05:00–14:59 TSİ")
    def test_before_05_or_at_15_blocked(self):
        for hour,minute,second in [(0,0,0),(4,59,59),(15,0,0),(23,59,59)]:
            local=datetime(2026,11,8,hour,minute,second,tzinfo=timezone(timedelta(hours=3)))
            self.assertFalse(in_manual_window(local),str(local))
    def test_utc_is_also_interpreted_as_turkey(self):
        self.assertTrue(in_manual_window(datetime(2026,11,8,11,59,59,tzinfo=timezone.utc)))
        self.assertFalse(in_manual_window(datetime(2026,11,8,12,0,0,tzinfo=timezone.utc)))
    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            in_manual_window(datetime(2026,11,8,14,0))
if __name__=="__main__":unittest.main()
