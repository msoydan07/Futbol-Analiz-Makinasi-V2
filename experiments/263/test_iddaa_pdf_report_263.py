"""Mobile-friendly PDF report generator; no forbidden market rows/picks."""
import tempfile,unittest
from pathlib import Path
from iddaa_pdf_session_263 import SCHEMA
from iddaa_pdf_report_263 import build,_render_pick

class PdfReportTests(unittest.TestCase):
    def setUp(self):
        self.row={"index":0,"league":"TUR1",
          "pdf_home":"Beşiktaş","pdf_away":"Gençlerbirliği",
          "status":"FOUR_MODELS_FORECAST_SHA_CREATED",
          "match_date_tr":"2026-11-22","kickoff_time_tr":"20:00",
          "prices":{"MS1":2.18,"MSX":3.30,"MS2":3.60,
                    "UNDER_2.5":1.78,"OVER_2.5":2.04,
                    "BTTS_YES":1.86,"BTTS_NO":1.93},
          "market_no_vig":{
             "MS":{"status":"FULL_MARKET_QUOTE_AVAILABLE",
                   "no_vig":{"MS1":0.45,"MSX":0.29,"MS2":0.26}},
             "GOALS_2.5":{"status":"FULL_MARKET_QUOTE_AVAILABLE",
                   "no_vig":{"OVER_2.5":0.47,"UNDER_2.5":0.53}},
             "KG":{"status":"FULL_MARKET_QUOTE_AVAILABLE",
                   "no_vig":{"BTTS_YES":0.51,"BTTS_NO":0.49}}
          },
          "model_forecast_sha256":"b"*64,
          "model_1x2_and_core_markets":{
            "M4":{"MS1":0.52,"MSX":0.25,"MS2":0.23,
                  "OVER_2.5":0.56,"UNDER_2.5":0.44,
                  "BTTS_YES":0.59,"BTTS_NO":0.41},
            "C3":{"MS1":0.51,"OVER_2.5":0.54,"BTTS_YES":0.60}
          }}
        self.session={"schema":SCHEMA,"n_rows":1,"rows":[self.row],
          "pdf_capture_utc":"2026-11-22T10:25:00+00:00",
          "pdf_sha256":"a"*64}

    def test_pdf_is_text_selectable_contains_all_seven_markets_no_forbidden(self):
        import fitz
        with tempfile.TemporaryDirectory() as d:
            p=build(self.session,Path(d)/"report.pdf")
            self.assertTrue(p.is_file())
            doc=fitz.open(p)
            self.assertGreaterEqual(len(doc),1)
            text=" ".join(x.get_text() for x in doc)
            for phrase in ("Beşiktaş","Gençlerbirliği","MS 1",
                           "MS X","MS 2","2.5 Alt","2.5 Üst",
                           "KG Var","KG Yok","PAS",
                           "2,18","2,04","1,86"):
                self.assertIn(phrase,text)
            self.assertNotIn("1.5 Üst",text)
            self.assertNotIn("3.5 Alt",text)
            self.assertNotIn("1.5 Alt",text)
            self.assertNotIn("3.5 Üst",text)
            self.assertIn("Fark",text)

    def test_no_unverified_main_pick(self):
        text=_render_pick(self.row,self.session)
        self.assertIn("PAS",text)
        self.assertNotIn("ANA: MS",text)
        self.row["pdf_linked_policy_decision"]={
           "pdf_sha256":"notmatching","forecast_sha256":"b"*64,
           "frozen_policy_verified":True,
           "main_market":"OVER_2.5"}
        self.assertIn("PAS",_render_pick(self.row,self.session))

    def test_even_linked_decision_may_not_show_1_5_or_3_5(self):
        self.row["pdf_linked_policy_decision"]={
           "pdf_sha256":"a"*64,"forecast_sha256":"b"*64,
           "frozen_policy_verified":True,"main_market":"OVER_1.5"}
        self.assertIn("PAS",_render_pick(self.row,self.session))
        self.row["pdf_linked_policy_decision"]["main_market"]="MS1"
        self.row["pdf_linked_policy_decision"]["alternative_market"]="BTTS_YES"
        text=_render_pick(self.row,self.session)
        self.assertIn("ANA: MS 1",text)
        self.assertIn("KG Var",text)

    def test_pdf_never_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"report.pdf"
            build(self.session,out)
            with self.assertRaises(FileExistsError):
                build(self.session,out)

if __name__=="__main__":unittest.main()
