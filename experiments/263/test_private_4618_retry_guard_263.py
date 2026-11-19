"""Six safety cases for immutable first PDF retries after transient failure."""
import json,tempfile,unittest
from pathlib import Path
from private_4618_retry_guard_263 import select_attempt,UnsafeRetry
SHA='a'*64
class Tests(unittest.TestCase):
    def verify(self,folder,sha):
        return {'signed_four_model_forecasts':int((folder/'forecasts'/'day'/'one.json').is_file())}
    def test_initial_attempt(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(select_attempt(d,SHA,verify_completed=self.verify)['attempt'],1)
    def test_unsealed_failure_retry_without_overwriting(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/SHA[:20];root.mkdir()
            (root/'bulletin.json').write_text('{}')
            x=select_attempt(d,SHA,verify_completed=self.verify)
            self.assertEqual(x['attempt'],2)
            self.assertTrue((root/'bulletin.json').exists())
    def test_partial_seal_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/SHA[:20];(root/'forecasts'/'day').mkdir(parents=True)
            (root/'forecasts'/'day'/'one.json').write_text('{}')
            with self.assertRaisesRegex(UnsafeRetry,'INCOMPLETE_SEALED'):
                select_attempt(d,SHA,verify_completed=self.verify)
    def test_verified_completed_seal_is_reused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/SHA[:20];(root/'forecasts'/'day').mkdir(parents=True)
            (root/'forecasts'/'day'/'one.json').write_text('{}')
            (root/'completed_receipt.json').write_text('{}')
            self.assertEqual(select_attempt(d,SHA,verify_completed=self.verify)['action'],'REUSE_SEALED')
    def test_receipt_claimed_missing_model_files(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/SHA[:20];root.mkdir()
            (root/'completed_receipt.json').write_text('{}')
            with self.assertRaisesRegex(UnsafeRetry,'SEALED_RECEIPT'):
                select_attempt(d,SHA,verify_completed=lambda a,b:{'signed_four_model_forecasts':1})
    def test_unreadable_previous_session_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/SHA[:20];root.mkdir()
            (root/'source_session.json').write_text('{broken')
            with self.assertRaisesRegex(UnsafeRetry,'UNREADABLE_PREVIOUS'):
                select_attempt(d,SHA,verify_completed=self.verify)
if __name__=='__main__':unittest.main(verbosity=2)
