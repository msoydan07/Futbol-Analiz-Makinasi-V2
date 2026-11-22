"""Regression against exact Nov20 approved visual specification, no live fixtures."""
import copy
import tempfile
import unittest
from pathlib import Path

from iddaa_pdf_approved_layout_263 import render_batch,render_singles
from iddaa_pdf_session_263 import SCHEMA as MORNING_SCHEMA
from iddaa_pdf_last_review_263 import build as review_build
from test_iddaa_pdf_last_review_263 import make, NOW

class UserApprovedReports(unittest.TestCase):
    def _row(self,n):
        prices={"MS1":1.40,"MSX":4.20,"MS2":6.50,
                "UNDER_2.5":2.30,"OVER_2.5":1.61,
                "BTTS_YES":1.90,"BTTS_NO":1.82}
        return {"index":n,"league":"GER1","pdf_home":"Ev Takımı "+str(n),
                "pdf_away":"Deplasman Takımı "+str(n),
                "match_date_tr":"2026-11-21","kickoff_time_tr":"17:30",
                "status":"ONE_ROW_OFFICIAL_ADAPTER_ERROR","prices":prices}
    def test_six_one_page_not_synthetic_predictions(self):
        import fitz
        session={"schema":MORNING_SCHEMA,"pdf_sha256":"a"*64,
                 "rows":[self._row(i) for i in range(6)]}
        with tempfile.TemporaryDirectory() as d:
            p=render_batch(session,Path(d)/"toplu.pdf")
            with fitz.open(p) as doc:
                self.assertEqual(len(doc),1)
                t=doc[0].get_text()
                for label in ("BUNDESLIGA","ANA MAKİNE","P0",
                              "P2:","Alternatif:"):
                    self.assertIn(label,t)
                self.assertIn("TEKNİK ENGEL",t)
                self.assertNotIn("MODEL ÖZETİ",t)
                for i in range(6):self.assertIn("Ev Takımı "+str(i),t)
            with self.assertRaises(FileExistsError):render_batch(session,p)
    def test_seven_matches_paginate_without_overwriting(self):
        import fitz
        s={"schema":MORNING_SCHEMA,"rows":[self._row(i) for i in range(7)]}
        with tempfile.TemporaryDirectory() as d:
            with fitz.open(render_batch(s,Path(d)/"toplu.pdf")) as pdf:
                self.assertEqual(len(pdf),2)
    def test_single_three_cards_seven_strip_and_no_invented_xi(self):
        import fitz
        morning,first,last,resolver=make()
        review=review_build(morning,first,last,[],NOW,resolver=resolver)
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/"tekli"
            made=render_singles(review,output)
            self.assertEqual(len(made),5)
            with fitz.open(made[0]) as doc:
                self.assertEqual(len(doc),1)
                page=doc[0]
                txt=page.get_text()
                for part in ("TEKLİ MAÇ RAPORU","ANA TERCİH","ALTERNATİF",
                             "P0 PİYASA","İlk oran","Son oran","Fark",
                             "Tercihler","Yüzdeler","Oranlar","MAÇ YORUMU"):
                    self.assertIn(part,txt)
                self.assertNotIn("MODEL ÖZETİ",txt)
                self.assertNotIn("Şart 1",txt)
                self.assertNotIn("ORAN KARŞILAŞTIRMASI",txt)
                self.assertIn("İlk 11",txt)
                drawings=page.get_drawings()
                boxes=[x["rect"] for x in drawings
                       if 150 < x["rect"].width < 185 and x["rect"].height>180]
                self.assertGreaterEqual(len(boxes),3)
                self.assertAlmostEqual(boxes[0].y0,boxes[1].y0,places=1)
                self.assertAlmostEqual(boxes[1].y0,boxes[2].y0,places=1)
                self.assertAlmostEqual(boxes[0].width,boxes[2].width,places=1)
            with self.assertRaises(FileExistsError):render_singles(review,output)

    def test_second_pdf_unmatched_match_has_no_single_report(self):
        morning,first,last,resolver=make()
        last["rows"][0]["home_label"]="Wrong team"
        review=review_build(morning,first,last,[],NOW,resolver=resolver)
        self.assertEqual(review["rows"][0]["status"],"GUNCEL_PDF_MAC_ESLESMEDI")
        with tempfile.TemporaryDirectory() as d:
            outputs=render_singles(review,Path(d)/"tekli")
            self.assertEqual(len(outputs),4)
            import fitz
            all_text=""
            for path in outputs:
                with fitz.open(path) as pdf:all_text+=pdf[0].get_text()
            self.assertNotIn("Ev Takimi 0 - Dep Takimi 0",all_text)
    def test_second_pdf_no_match_is_fail_closed_not_an_empty_report(self):
        morning,first,last,resolver=make()
        last["rows"]=[]
        review=review_build(morning,first,last,[],NOW,resolver=resolver)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"NO_VERIFIED_SECOND_PDF"):
                render_singles(review,Path(d)/"tekli")

    def test_unsigned_choice_does_not_become_real_pick(self):
        # A market price alone can never manufacture a main prediction.
        s={"schema":MORNING_SCHEMA,"rows":[self._row(0)]}
        with tempfile.TemporaryDirectory() as d:
            import fitz
            with fitz.open(render_batch(s,Path(d)/"r.pdf")) as pdf:
                t=pdf[0].get_text()
                self.assertIn("TEKNİK ENGEL",t)
                self.assertIn("PAS DEĞİL",t)
                self.assertNotIn("MS 1   %",t)
if __name__=="__main__":
    unittest.main()
