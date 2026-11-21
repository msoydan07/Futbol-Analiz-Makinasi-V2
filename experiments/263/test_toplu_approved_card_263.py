"""User-approved 21-Nov compact A4 card contract, never fabricated real picks."""
import tempfile
import unittest
from pathlib import Path
import fitz
from iddaa_pdf_approved_layout_263 import render_model_only_batch

def sample(i,day="2026-11-21"):
    return {"league":"TUR1",
            "approved_card":{
                "home":"Sentetik ev "+str(i),
                "away":"Sentetik dep "+str(i),
                "league":"TUR1","date":day,"time":"16:00",
                "main":"MS 1" if i%2 else "KG VAR",
                "ours":"68,0%","fair":"VERİ YOK",
                "diff":"—","alternative":"2.5 ÜST 63,0%",
                "main_odds":"—","forecast_sha":"a"*64,
                "decision_sha":"b"*64}}

class ApprovedCardContract(unittest.TestCase):
    def test_four_matches_one_page_and_fields(self):
        with tempfile.TemporaryDirectory() as root:
            out=Path(root)/"toplu.pdf"
            render_model_only_batch("2026-11-21",
                                    [sample(i) for i in range(4)],out)
            with fitz.open(out) as pdf:
                self.assertEqual(len(pdf),1)
                page=pdf[0]
                txt=page.get_text()
                for phrase in ("TÜRKİYE SÜPER LİG","21 KASIM 2026",
                               "CUMARTESİ","4 MAÇ","ANA TERCİH",
                               "BİZİM %","PİYASA %","FARK (PUAN)",
                               "Alternatif:", "Ana iddaa oranı:",
                               "VERİ YOK","SABAH / MODEL-ONLY",
                               "01/04","04/04"):
                    self.assertIn(phrase,txt)
                self.assertNotIn("SABAH / İLK ORAN PDF",txt)
                self.assertNotIn("Pinnacle",txt)
                boxes=[d["rect"] for d in page.get_drawings()
                       if d["rect"].width>500 and 90<=d["rect"].height<=105]
                self.assertEqual(len(boxes),4)
                for box in boxes:
                    self.assertAlmostEqual(box.x0,boxes[0].x0,places=1)
                    self.assertAlmostEqual(box.x1,boxes[0].x1,places=1)
            with self.assertRaises(FileExistsError):
                render_model_only_batch("2026-11-21",
                                        [sample(i) for i in range(4)],out)
    def test_seven_matches_paginates_six_per_page(self):
        with tempfile.TemporaryDirectory() as root:
            p=render_model_only_batch("2026-11-21",
                   [sample(i) for i in range(7)],Path(root)/"x.pdf")
            with fitz.open(p) as pdf:
                self.assertEqual(len(pdf),2)
                self.assertIn("07/07",pdf[1].get_text())
    def test_reject_forged_market_data_in_model_only(self):
        for key,v in (("fair","61,0%"),("main_odds","1,44"),
                      ("diff","+4,0")):
            r=sample(0)
            r["approved_card"][key]=v
            with tempfile.TemporaryDirectory() as root:
                with self.assertRaisesRegex(ValueError,"MODEL_ONLY_CARD_INVALID"):
                    render_model_only_batch("2026-11-21",[r],Path(root)/"x.pdf")
    def test_unverified_or_wrong_day_blocks(self):
        r=sample(0)
        del r["approved_card"]["decision_sha"]
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                render_model_only_batch("2026-11-21",[r],Path(root)/"x.pdf")
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError,"DATE_LEAGUE"):
                render_model_only_batch("2026-11-22",[sample(0)],Path(root)/"x.pdf")

if __name__=="__main__":unittest.main(verbosity=2)
