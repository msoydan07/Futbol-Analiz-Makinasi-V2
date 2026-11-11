"""A real-calculation, NO-LIVE-QUOTE PDF-first acceptance rehearsal.

Actual PyMuPDF-generated printable PDF bytes -> production PDF parser ->
actual 2026/27 TFF week-12 parser fed a fixed fixture HTML test double ->
real accepted 4617 results, frozen B/C2/C3/M4/empirical baseline ->
real frozen value policy -> final readable PDF + immutable duplicate receipt.

The PDF/odds and official page fixture are TEST DATA, not a real user iddaa
bulletin or independently re-fetched live kickoff. This test NEVER saves a
live/pilot forecast, never makes a network request, and never authorizes bets.
"""
from __future__ import annotations
import hashlib
import json
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch

import fitz

from iddaa_pdf_bulletin_263 import parse_pdf
from iddaa_pdf_one_step_263 import one_step
from iddaa_pdf_live_official_263 import lookup as source_lookup
from iddaa_pdf_team_alias_preflight_263 import index_registry
from full_match_eligibility_263 import full_match_rows
from exp_263_batch import clean_rows

ROOT=Path(__file__).resolve().parents[2]
HISTORY=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
BASE=ROOT/"m4_quad_base/historical_results.csv"
MANIFEST=ROOT/"data/results_only_263/4617_research_input_provenance.json"
LOCK=ROOT/"experiments/263/m4_lock.json"
TRUSTED_AT=datetime(2026,11,21,12,45,tzinfo=timezone.utc)
SOURCE="https://www.tff.org/Default.aspx?hafta=12&pageId=198"
EXPECTED=("GALATASARAY A.Ş.","SAMSUNSPOR A.Ş.")
EVENTS=[
    ("21.11.2026 13:30","GENÇLERBİRLİĞİ","GAZİANTEP FUTBOL KULÜBÜ A.Ş."),
    ("21.11.2026 16:00","AMED SPORTİF FAALİYETLER","ÇAYKUR RİZESPOR A.Ş."),
    ("21.11.2026 16:00","GALATASARAY A.Ş.","SAMSUNSPOR A.Ş."),
    ("21.11.2026 19:00","KOCAELİSPOR","FENERBAHÇE A.Ş."),
    ("22.11.2026 13:30","ERZURUMSPOR FK","GÖZTEPE A.Ş."),
    ("22.11.2026 16:00","KASIMPAŞA A.Ş.","CORENDON ALANYASPOR"),
    ("22.11.2026 16:00","TÜMOSAN KONYASPOR","BEŞİKTAŞ A.Ş."),
    ("22.11.2026 19:00","TRABZONSPOR A.Ş.","EYÜPSPOR"),
    ("23.11.2026 20:00","İSTANBUL BAŞAKŞEHİR FK","ARCA ÇORUM FK"),
]
PDF_PRICES=("1.88","3.60","3.90","2.11","3.22","2.22","1:0",
            "1.55","4.20","3.20","1.91","1.81","1.91","1.85")

def fake_official_html():
    # Exact 9 publicly observed TFF rows, reconstructed HTML; NOT a live fetch.
    return ("<html><h1>Trendyol Süper Lig 2026-2027 Sezonu Fikstürü</h1>"
        "<p>12.Hafta</p><table>"
        + "".join("<tr><td>"+time+"</td><td>"+home+"</td><td>-</td><td>"
                  +away+"</td><td>Detaylar</td></tr>" for time,home,away in EVENTS)
        +"</table></html>")

def synthetic_print_pdf(path):
    font=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if not font.is_file():
        raise RuntimeError("TEST_ONLY_UNICODE_FONT_UNAVAILABLE")
    doc=fitz.open()
    # Second row deliberately shows a wrong time: it must be rejected without
    # blocking the real-model calculation of the good first test row.
    for home,away,shown in (
        ("Galatasaray","Samsunspor","16:00"),
        ("Kocaelispor","Fenerbahce","18:30"),
    ):
        page=doc.new_page(width=595,height=842)
        page.insert_font(fontname="dev",fontfile=str(font))
        page.insert_text((18,50),"iddaa Bülten",fontname="dev",fontsize=12)
        page.insert_text((83,290),"TÜRKİYE SÜPER LİG\nBugün",
                         fontname="dev",fontsize=8)
        page.insert_text((104,318),shown+"\n"+home+" - "+away+"\n+\n1",
                         fontsize=9,fontname="helv")
        for i,value in enumerate(PDF_PRICES):
            page.insert_text((209+i*15,319),value,fontsize=7)
    doc.set_metadata({
        "title":"iddaa Programı - iddaa Bülteni | iddaa.com",
        "creationDate":"D:20261121153000+03'00'",
    })
    doc.save(path)
    doc.close()

class FullModelRehearsal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BASE.is_file():
            raise RuntimeError("MISSING_PINNED_4413_BASELINE_DOWNLOAD_CI_REQUIRED")
        if hashlib.sha256(BASE.read_bytes()).hexdigest()!=(
             "35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1"):
            raise ValueError("FROZEN_BASE_SHA_CHANGED")
        if hashlib.sha256(HISTORY.read_bytes()).hexdigest()!=(
             "637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89"):
            raise ValueError("RESEARCH_4617_SHA_CHANGED")

    def test_real_four_models_and_report_from_actual_rendered_pdf(self):
        index,_,_=index_registry()
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            pdf=folder/"SIMULATED_IDDAA_NOT_USER_SOURCE.pdf"
            synthetic_print_pdf(pdf)
            parsed=parse_pdf(pdf)
            self.assertEqual(parsed["source_domain"],"iddaa.com")
            self.assertEqual(parsed["total_visible_fixtures"],2)
            self.assertEqual(parsed["potential_ten_league_rows"],2)
            self.assertTrue(all(row["odds"] is not None for row in parsed["rows"]),parsed["rows"])
            self.assertEqual([row["league"] for row in parsed["rows"]],["TUR1","TUR1"])
            self.assertEqual(parsed["pdf_capture_utc"],"2026-11-21T12:30:00+00:00")

            calls=[]
            document=fake_official_html()
            def lookup(home,away):
                calls.append((home,away))
                return source_lookup("TUR1",home,away,now=TRUSTED_AT,
                    fetcher=lambda url:(url,document))
            # Simulated official site uses controlled HTML, not a fake JSON
            # marked "VERIFIED"; live parser must prove names/date/time.
            with patch("iddaa_pdf_live_official_263._default_fetch",
                       side_effect=AssertionError("OFFICIAL_NETWORK_FORBIDDEN")):
                result=one_step(pdf,history=HISTORY,output_root=folder/"private",
                    source_baseline=BASE,source_acceptance=MANIFEST,
                    now=TRUSTED_AT,repo_root=ROOT,
                    m4_lock=LOCK,official_lookup=lookup)
            self.assertEqual(len(calls),2)
            self.assertEqual(result["source_rows"],2)
            self.assertEqual(result["official_confirmed_rows"],1,result)
            self.assertEqual(result["signed_four_model_forecasts"],1,result)
            self.assertEqual(result["calibrated_price_decisions"],1,result)
            self.assertTrue(result["no_bookmaker_api_calls"])
            self.assertTrue(result["no_old_pilot_changes"])
            session_dir=Path(result["processing_folder"])
            session=json.loads((session_dir/"source_session.json").read_text())
            by_status={x["status"]:x for x in session["rows"]}
            self.assertIn("FOUR_MODELS_FORECAST_SHA_CREATED",by_status)
            self.assertIn("ONE_ROW_OFFICIAL_PDF_TIME_OR_DATE_DIFFER",by_status)
            passed=by_status["FOUR_MODELS_FORECAST_SHA_CREATED"]
            self.assertEqual(passed["official_lookup_attempts"],1)
            self.assertEqual(passed["rotation_7day"]["status"],
                             "VERIFIED_SAME_PAGE_LEAGUE_PARTIAL")
            self.assertFalse(passed["rotation_7day"]["model_probabilities_changed"])
            self.assertFalse(passed["rotation_7day"]["uefa_and_cup_schedule_complete"])
            self.assertEqual(passed["home_id"],index["TUR1"]["galatasaray"])
            self.assertEqual(passed["away_id"],index["TUR1"]["samsunspor"])
            self.assertEqual(set(passed["model_1x2_and_core_markets"]),
                             {"B","C2","C3","M4"})
            forecast=json.loads(Path(passed["model_forecast_path"]).read_text())
            baseline=json.loads(Path(passed["empirical_baseline_path"]).read_text())
            self.assertEqual(forecast["data"]["snapshot_acceptance"],
                             "APPEND_ONLY_4617_PUBLIC_RESULTS_ONLY_RESEARCH_NOT_OFFICIAL_ID_VERIFIED")
            self.assertEqual(forecast["data"]["history_freshness_verification"]["status"],
                             "REVIEWED_FIRST_POST_BREAK_SCHEDULE_ONLY")
            self.assertEqual(forecast["fixture"]["match_local_date"],"2026-11-21")
            self.assertEqual(forecast["model_predictions"]["M4"]["status"],"AVAILABLE")
            self.assertEqual(baseline["forecast_sha256"],forecast["payload_sha256"])
            self.assertFalse(forecast["data"]["human_source_acceptance"])
            calibrated=json.loads((session_dir/"calibrated_session.json").read_text())
            self.assertFalse(calibrated["pilot_count_changed"])
            self.assertEqual(calibrated["n_pdf_first_decisions"],1)
            self.assertTrue(Path(result["pdf_report_path"]).is_file())
            with fitz.open(result["pdf_report_path"]) as report:
                contents=" ".join(page.get_text() for page in report)
            self.assertIn("Galatasaray",contents)
            self.assertIn("Kocaelispor",contents)
            self.assertIn("KG Var",contents)
            self.assertIn("7 günlük maç yoğunluğu",contents)
            self.assertIn("Avrupa/kupa",contents)
            self.assertNotIn("1.5 Üst",contents)
            self.assertNotIn("3.5 Alt",contents)
            self.assertIn("PAS",contents)
            self.assertGreater(Path(result["pdf_report_path"]).stat().st_size,1000)
            self.assertTrue((session_dir/"completed_receipt.json").exists())

            # Duplicate PDF cannot write another pilot, refetch fixture or reprice.
            second=one_step(pdf,history=HISTORY,output_root=folder/"private",
                        now=TRUSTED_AT,official_lookup=lambda *_:self.fail("REQUERY"))
            self.assertTrue(second["already_processed_same_pdf_sha"])
            self.assertEqual(second["pdf_report_path"],result["pdf_report_path"])
            print("REAL_ENGINE_FAKE_BULLETIN_ACCEPTANCE="+json.dumps({
                "synthetic_pdf":True,"controlled_official_html":True,
                "live_iddaa_pdf_accepted":False,
                "real_4617_history_sha":forecast["data"]["snapshot_sha256"],
                "four_models":{k:v["status"] for k,v in forecast["model_predictions"].items()},
                "official_rows":1,"time_mismatch_rows":1,
                "policy_decisions":calibrated["n_pdf_first_decisions"],
                "pdf_page_count":len(fitz.open(result["pdf_report_path"])),
                "no_bet_or_live_claim":True},ensure_ascii=False),flush=True)

