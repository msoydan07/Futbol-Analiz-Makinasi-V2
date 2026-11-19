"""Synthetic first-iddaa PDF safety tests; NO user PDF, odds or forecasts in CI."""
import copy,json,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from private_4618_first_pdf_day_guard_263 import (
    FirstPdfBlocked,verify_current_first_pdf,claim_single_first_pdf)

NOW=datetime(2026,11,21,9,30,tzinfo=timezone.utc)  # 12:30 in Istanbul
SHA1="a"*64
SHA2="b"*64

def bulletin(stamp="2026-11-21T09:20:00+00:00",sha=SHA1,league="ENG1",day="2026-11-21",
            status="PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK"):
    return {"schema":"263_iddaa_pdf_pregame_bulletin_v1",
            "source_domain":"iddaa.com","pdf_sha256":sha,
            "pdf_capture_utc":stamp,
            "rows":[{"league":league,"match_date_tr":day,
                     "status":status,"home_label":"Team H","away_label":"Team A"}]}

class GuardTests(unittest.TestCase):
    def test_01_valid_same_day_pdf_preflight(self):
        r=verify_current_first_pdf(bulletin(),now=NOW)
        self.assertEqual(r["current_ten_league_eligible_fixtures"],1)
        self.assertFalse(r["production_forecast_approved"])

    def test_02_previous_day_pdf_is_rejected(self):
        with self.assertRaisesRegex(FirstPdfBlocked,"STALE_OR_FUTURE"):
            verify_current_first_pdf(bulletin(stamp="2026-11-20T15:00:00+00:00"),now=NOW)

    def test_03_no_today_league_fixture_rejected(self):
        with self.assertRaisesRegex(FirstPdfBlocked,"NO_TODAY"):
            verify_current_first_pdf(bulletin(day="2026-11-22"),now=NOW)

    def test_04_out_of_scope_cup_pdf_rejected(self):
        with self.assertRaisesRegex(FirstPdfBlocked,"NO_TODAY"):
            verify_current_first_pdf(bulletin(league=None),now=NOW)

    def test_05_bad_quote_alignment_ignored_for_new_seal(self):
        with self.assertRaisesRegex(FirstPdfBlocked,"NO_TODAY"):
            verify_current_first_pdf(bulletin(status="PRICE_COLUMN_ALIGNMENT_UNRESOLVED"),now=NOW)

    def test_06_pdf_creation_in_future_rejected(self):
        with self.assertRaisesRegex(FirstPdfBlocked,"AFTER_ACTUAL"):
            verify_current_first_pdf(bulletin(stamp="2026-11-21T10:00:00+00:00"),now=NOW)

    def test_07_bad_source_rejected(self):
        b=bulletin();b["source_domain"]="otherbookie.example"
        with self.assertRaisesRegex(FirstPdfBlocked,"ONLY_USER"):
            verify_current_first_pdf(b,now=NOW)

    def test_08_duplicate_fixture_rejected(self):
        b=bulletin();b["rows"].append(copy.deepcopy(b["rows"][0]))
        with self.assertRaisesRegex(FirstPdfBlocked,"DUPLICATE"):
            verify_current_first_pdf(b,now=NOW)

    def test_09_lock_created_and_same_sha_retry(self):
        with tempfile.TemporaryDirectory() as d:
            p=verify_current_first_pdf(bulletin(),now=NOW)
            x=claim_single_first_pdf(d,p)
            self.assertEqual(x["status"],"FIRST_PDF_DAY_LOCK_CREATED")
            y=claim_single_first_pdf(d,p)
            self.assertEqual(y["status"],"SAME_FIRST_PDF_ONLY_ALLOW_EXISTING_SESSION_OR_SAFE_RETRY")
            self.assertEqual(x["first_pdf_day_lock"],y["first_pdf_day_lock"])

    def test_10_second_pdf_sha_cannot_reseal(self):
        with tempfile.TemporaryDirectory() as d:
            claim_single_first_pdf(d,verify_current_first_pdf(bulletin(),now=NOW))
            with self.assertRaisesRegex(FirstPdfBlocked,"SECOND_PDF_CANNOT"):
                claim_single_first_pdf(d,verify_current_first_pdf(bulletin(sha=SHA2),now=NOW))

    def test_11_tampered_daily_lock_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            p=claim_single_first_pdf(d,verify_current_first_pdf(bulletin(),now=NOW))
            fn=Path(p["first_pdf_day_lock"])
            obj=json.loads(fn.read_text())
            obj["pdf_sha256"]=SHA2
            fn.write_text(json.dumps(obj))
            with self.assertRaisesRegex(FirstPdfBlocked,"LOCK_TAMPERED"):
                claim_single_first_pdf(d,verify_current_first_pdf(bulletin(),now=NOW))

    def test_12_missing_timezone_refused(self):
        with self.assertRaisesRegex(FirstPdfBlocked,"MISSING_TIMEZONE"):
            verify_current_first_pdf(bulletin(stamp="2026-11-21T09:20:00"),now=NOW)

    def test_13_exact_old_pdf_date_guards_match_real_archive(self):
        # Actual user's Nov 11 PDF has D:20261111144622+00'00':
        # This test uses only the observed timestamp, not private PDF bytes.
        with self.assertRaisesRegex(FirstPdfBlocked,"STALE_OR_FUTURE"):
            verify_current_first_pdf(bulletin(stamp="2026-11-11T14:46:22+00:00"),now=NOW)

    def test_14_existing_day_lock_prevents_competing_same_day_sha(self):
        with tempfile.TemporaryDirectory() as d:
            p=verify_current_first_pdf(bulletin(),now=NOW)
            claim_single_first_pdf(d,p)
            for sha in ("c"*64,"d"*64):
                with self.assertRaisesRegex(FirstPdfBlocked,"SECOND_PDF_CANNOT"):
                    claim_single_first_pdf(d,verify_current_first_pdf(bulletin(sha=sha),now=NOW))

if __name__=="__main__":unittest.main(verbosity=2)
