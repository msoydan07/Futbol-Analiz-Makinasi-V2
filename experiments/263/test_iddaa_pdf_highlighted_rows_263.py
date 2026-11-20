"""User's 20 November mobile IDDAA layout faithfully mocked at PDF block-level.
All markets are from source columns, not model probabilities. No future info.
"""
from __future__ import annotations
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from iddaa_pdf_bulletin_263 import parse_pdf
from iddaa_pdf_team_alias_preflight_263 import index_registry,resolve_label

PRICES={
 "Troyes": ["2.00","3.12","2.96","2.59","2.04","3.57","0:1","3.73","3.69","1.49","1.73","1.73","1.58","1.90"],
 "Athletic Bilbao": ["1.34","4.11","5.99","1.82","2.26","6.12","0:1","2.06","3.28","2.36","1.82","1.65","1.82","1.65"],
 "Iğdır FK": ["1.64","3.18","3.60","2.17","2.00","4.14","0:1","2.80","3.29","1.67","1.66","1.66","1.59","1.74"],
 "Arminia Bielefeld": ["2.02","3.21","2.84","2.56","2.13","3.36","0:1","3.67","3.84","1.47","1.92","1.58","1.47","2.10"],
 "Darmstadt 98": ["3.06","3.47","1.84","3.45","2.31","2.31","1:0","1.58","3.89","3.08","2.32","1.38","1.34","2.41"],
}
ROWS=(
 ("TÜRKİYE 1. LİG","20:00","Iğdır FK","Ümraniyespor",213.4),
 ("ALMANYA 2. BUNDESLİGA","20:30","Arminia Bielefeld","Magdeburg",248.9),
 ("ALMANYA 2. BUNDESLİGA","20:30","Darmstadt 98","Heidenheim",269.9),
 ("FRANSA LİGUE 1","22:45","Troyes","Le Havre",305.4),
 ("İSPANYA LA LİGA","23:00","Athletic Bilbao","Espanyol",340.9),
)
XS=(208,224,238,253,268,283,300,313,328,343,359,374,389,404)

class FakePage:
    def __init__(self,corrupt=False):
        self.blocks=[];self.words=[]
        self.blocks.append((70,120,160,130,"Bülten\n",0,0))
        for i,(title,time,home,away,teambase) in enumerate(ROWS):
            # Real first-page order is not the same as visual order; code
            # must match layout by coordinates instead of stream ordering.
            if i in (0,1,3,4):
                self.blocks.append((82.5,teambase-15,410,teambase-7,
                                    title+"\n1\n0\n2\n",0,0))
            self.blocks.append((104,teambase+.7,122,teambase+13,
                                "Bugün\n"+time+"\n",0,0))
            self.blocks.append((129,teambase,202,teambase+13,
                                home+"\n"+away+"\n",0,0))
            # For two German fixtures, a shared heading appears above the
            # first; one is still eligible for the same previous section.
            if i==2:pass
            prices=PRICES[home]
            if corrupt and home=="Troyes":prices=prices[:13]
            for j,token in enumerate(prices):
                self.words.append((XS[j],teambase+3,XS[j]+8,teambase+8,
                                   token,i,j,0))
            # Several layout fragments after the price row: no guessed heading.
            self.blocks.append((89,teambase+3,410,teambase+10,
                                "1\nCANLI\n"+"\n".join(prices)+"\n",0,0))
    def get_text(self,form=None):
        if form=="blocks":return self.blocks
        if form=="words":return self.words
        return "Bülten"

class FakeDoc:
    metadata={"title":"iddaa Programı - iddaa Bülteni | iddaa.com",
              "creationDate":"D:20261120071846+00'00'"}
    def __init__(self,page):self.pages=[page]
    def __iter__(self):return iter(self.pages)

class FeaturedMobilePdf(unittest.TestCase):
    def read(self,corrupt=False):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"iddaa.pdf"
            path.write_bytes(b"%PDF-BLOCK-LEVEL-SYNTHETIC-TEST-ONLY")
            with patch("fitz.open",return_value=FakeDoc(FakePage(corrupt))):
                return parse_pdf(path)
    def test_full_user_mobile_layout_five_rows_exactly_two_ten_leagues(self):
        result=self.read()
        self.assertEqual(result["total_visible_fixtures"],5)
        self.assertEqual(result["potential_ten_league_rows"],2)
        target={r["home_label"]:r for r in result["rows"]}
        self.assertEqual(target["Troyes"]["league"],"FRA1")
        self.assertEqual(target["Athletic Bilbao"]["league"],"ESP1")
        self.assertIsNone(target["Iğdır FK"]["league"])
        self.assertIsNone(target["Arminia Bielefeld"]["league"])
        self.assertIsNone(target["Darmstadt 98"]["league"])
        self.assertEqual(target["Troyes"]["match_date_tr"],"2026-11-20")
        self.assertEqual(target["Athletic Bilbao"]["kickoff_time_tr"],"23:00")
        self.assertEqual(target["Troyes"]["odds"]["MS1"],2.0)
        self.assertEqual(target["Troyes"]["odds"]["O25_OVER"],1.73)
        self.assertEqual(target["Troyes"]["odds"]["BTTS_YES"],1.58)
        self.assertEqual(target["Athletic Bilbao"]["odds"]["MS1"],1.34)
        self.assertEqual(target["Athletic Bilbao"]["odds"]["O25_UNDER"],1.82)
        self.assertEqual(target["Athletic Bilbao"]["odds"]["BTTS_NO"],1.65)
        for home in ("Troyes","Athletic Bilbao"):
            self.assertEqual(target[home]["price_parse"]["found_slots"],14)
            self.assertEqual(target[home]["status"],
                "PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK")
    def test_missing_a_single_price_column_does_not_shift_other_markets(self):
        result=self.read(corrupt=True)
        row=next(r for r in result["rows"] if r["home_label"]=="Troyes")
        self.assertIsNone(row["odds"])
        self.assertEqual(row["price_parse"]["status"],"PRICE_COLUMN_ALIGNMENT_UNRESOLVED")
        self.assertEqual(row["price_parse"]["found_slots"],13)
    def test_missing_stale_data_is_technical_block_not_model_pas(self):
        from iddaa_pdf_report_263 import _render_pick
        blocked={"status":"ONE_ROW_FOUR_MODEL_EVIDENCE_BLOCKED",
                 "model_reason":"GAP_EXCEEDS_LIMIT_REQUIRES_REFRESH",
                 "model_error_type":"StaleLeagueData"}
        output=_render_pick(blocked,{"pdf_sha256":"a"*64})
        self.assertIn("TEKNIK ENGEL (PAS DEGIL)",output)
        self.assertIn("GAP_EXCEEDS_LIMIT_REQUIRES_REFRESH",output)
        no_official=_render_pick({"status":"ONE_ROW_OFFICIAL_TIME_INVALID"},{})
        self.assertIn("TEKNIK ENGEL (PAS DEGIL)",no_official)

    def test_only_existing_espanol_and_athletic_identity_ids(self):
        lookup,names,membership=index_registry()
        for league,label in (("FRA1","Troyes"),("FRA1","Le Havre"),
                             ("ESP1","Athletic Bilbao"),("ESP1","Espanyol")):
            got=resolve_label(league,label,lookup)
            self.assertEqual(got["status"],"MAPPED")
            self.assertIn(got["team_id"],membership[league])
        self.assertEqual(names[resolve_label("ESP1","Espanyol",lookup)["team_id"]],
                         "RCD Espanyol de Barcelona")

if __name__=="__main__":unittest.main()
