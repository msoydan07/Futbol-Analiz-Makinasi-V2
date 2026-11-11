"""Offline safety regression for real Android iddaa.com print layout (11 Nov 2026).

Contains extracted text/coordinates only, no uploaded personal PDF. The actual
sample was manually compared to a 3-page 30-row print. No online bookmaker calls.
"""
import tempfile,unittest
from datetime import timezone
from pathlib import Path
from unittest.mock import patch
from iddaa_pdf_bulletin_263 import (
    PRICE_NAMES,KEEP,_markets_from_words,_heading,capture_time,
    league_lookup,parse_pdf,normal,
)

class FakePage:
    def __init__(self,block,price_words,header,legend="Bülten"):
        self._blocks=[header,block]
        self._words=price_words
        self._legend=legend
    def get_text(self,kind=None):
        if kind=="blocks":return self._blocks
        if kind=="words":return self._words
        return self._legend

class FakeDoc:
    metadata={"title":"iddaa Programı - iddaa Bülteni | iddaa.com",
              "creationDate":"D:20261111144622+00'00'"}
    def __init__(self,pages):self._pages=pages
    def __iter__(self):return iter(self._pages)

def make_words(items,y=304.1,start=209):
    return [(start+i*15,y,start+i*15+10,y+5,x,0,0,i)
            for i,x in enumerate(items)]

class IddaaPdfTest(unittest.TestCase):
    def setUp(self):
        self.prices=["3.62","3.73","1.65","3.93","2.37","2.11",
                     "1:0","1.78","3.77","2.63","2.38","1.37","1.38","2.35"]
        self.row=(104.,301.1,430.,313.1,
                  "20:00\nTürkiye -Belçika\n+\n866\n",1,0)
        self.heading=(82.5,287.4,412.9,294.4,
                      "UEFA ULUSLAR LİGİ\nYarın\n1\n0\n2\n",0,0)

    def test_14_column_structure_real_observed_1x2_25_kg(self):
        pg=FakePage(self.row,make_words(self.prices),self.heading)
        values,status=_markets_from_words(pg,self.row)
        self.assertEqual(status["status"],"PRICE_COLUMNS_READ")
        self.assertEqual(values["MS1"],3.62)
        self.assertEqual(values["MSX"],3.73)
        self.assertEqual(values["MS2"],1.65)
        self.assertEqual(values["O25_UNDER"],2.38)
        self.assertEqual(values["O25_OVER"],1.37)
        self.assertEqual(values["BTTS_YES"],1.38)
        self.assertEqual(values["BTTS_NO"],2.35)
        self.assertEqual(set(values),set(KEEP))

    def test_hyphen_cells_do_not_shift_market_columns(self):
        values,status=_markets_from_words(FakePage(self.row,
            make_words(["1.08","6.09","8.99","1.41","2.80","7.64",
                        "0:2","2.16","3.62","1.95","-","-","1.62","1.73"]),
            self.heading),self.row)
        self.assertEqual(values["O25_UNDER"],None)
        self.assertEqual(values["O25_OVER"],None)
        self.assertEqual(values["BTTS_YES"],1.62)
        self.assertEqual(values["BTTS_NO"],1.73)

    def test_one_lost_column_must_not_be_interpreted_as_other_market(self):
        broken=self.prices[:11]+self.prices[12:]
        values,status=_markets_from_words(
            FakePage(self.row,make_words(broken),self.heading),self.row)
        self.assertIsNone(values)
        self.assertEqual(status["status"],"PRICE_COLUMN_ALIGNMENT_UNRESOLVED")

    def test_two_real_sample_13_slot_rows_stay_ambiguous(self):
        items=["2.25","2.85","2.51","2.89","1.87","3.17",
               "0:1","4.50","3.65","1.32","1.51","1.87","1.65"]
        values,status=_markets_from_words(FakePage(self.row,
            make_words(items),self.heading),self.row)
        self.assertIsNone(values)
        self.assertEqual(status["found_slots"],13)

    def test_fixture_league_do_not_infer_women_youth_cup_as_ten_leagues(self):
        self.assertIsNone(league_lookup("FRANSA 1.LİG, KADINLAR"))
        self.assertIsNone(league_lookup("İNGİLTERE FUTBOL LİGİ KUPASI, KUZEY GRUB"))
        self.assertIsNone(league_lookup("UEFA ULUSLAR LİGİ"))
        self.assertEqual(league_lookup("TÜRKİYE SÜPER LİG"),"TUR1")
        self.assertEqual(league_lookup("İNGİLTERE CHAMPIONSHIP"),"ENG2")
        self.assertEqual(league_lookup("FRANSA LİGUE 1"),"FRA1")

    def test_day_from_source_pdf_metadata_no_requery(self):
        t=capture_time(FakeDoc.metadata)
        self.assertEqual(t.isoformat(),"2026-11-11T14:46:22+00:00")
        self.assertEqual(t.astimezone(__import__("zoneinfo").ZoneInfo("Europe/Istanbul")).hour,17)
        self.assertRaises(ValueError,capture_time,{"creationDate":"D:20261111144622"})

    def test_actual_one_pdf_row_as_official_sample_scope_out(self):
        pg=FakePage(self.row,make_words(self.prices),self.heading,
                    legend="Bülten\niddaa")
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/"one.pdf"
            source.write_bytes(b"synthetic marker not an actual PDF")
            with patch("fitz.open",return_value=FakeDoc([pg])):
                report=parse_pdf(source)
        self.assertEqual(report["total_visible_fixtures"],1)
        self.assertEqual(report["potential_ten_league_rows"],0)
        self.assertEqual(report["rows"][0]["status"],
                         "OUT_OF_SCOPE_OR_UNMAPPED_LEAGUE")
        self.assertEqual(report["rows"][0]["match_date_tr"],"2026-11-12")
        self.assertEqual(report["rows"][0]["odds"]["BTTS_NO"],2.35)
        self.assertEqual(report["pdf_capture_tr"][:10],"2026-11-11")
        self.assertFalse(report["no_model_forecasts_created"] is False)

    def test_pregame_fixture_not_promoted_just_from_pdf_header(self):
        row=(104.,301.1,430.,313.1,
             "20:00\nBesiktas JK -Genclerbirligi SK\n+\n12\n",1,0)
        header=(82.5,287.4,412.9,294.4,
                "TÜRKİYE SÜPER LİG\nBugün\n1\n0\n2\n",0,0)
        pg=FakePage(row,make_words(self.prices),header,legend="Bülten")
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"test.pdf";p.write_bytes(b"not an actual PDF")
            with patch("fitz.open",return_value=FakeDoc([pg])):
                result=parse_pdf(p)
        self.assertEqual(result["potential_ten_league_rows"],1)
        self.assertEqual(result["rows"][0]["status"],
                         "PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK")
        self.assertTrue(result["no_model_forecasts_created"])
        self.assertTrue(result["no_bookmaker_api_calls"])
        self.assertEqual(result["rows"][0]["league"],"TUR1")
        self.assertEqual(result["rows"][0]["odds"]["MS1"],3.62)

if __name__=="__main__":unittest.main()
