"""Synthetic read-only approved PDF screen, no API/production files rewritten."""
import json,unittest
from pathlib import Path
from pypdf import PdfReader
from test_sabah_pinnacle_new100_bridge_263 import New100PinnacleBridgeTests
from sabah_pinnacle_new100_bridge_263 import render
from sabah_mobile_approved_pdf_263 import row_data,batch_pdf,single_pdf,run,MobileBlocked
class ApprovedMobilePDF(unittest.TestCase):
    def setUp(self):
        self.fixture=New100PinnacleBridgeTests(methodName="test_missing_unchanged_secret_yields_explicit_PAS")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root=self.fixture.root
        self.day=self.fixture.report["day_turkey"]
    def data(self,with_snapshot=False):
        if with_snapshot:self.fixture.snapshot()
        p=render(self.fixture.report,self.fixture.receipt,self.root,self.fixture.snapshots)
        rows=row_data(self.fixture.report,p,self.root)
        self.assertEqual(len(rows),1)
        return p,rows[0]
    def test_original_approved_layout_fair_price_correct_side(self):
        price,r=self.data(True)
        self.assertEqual(r["direction"],"MS 1")
        self.assertAlmostEqual(r["model"],.53)
        self.assertIsNotNone(r["market"])
        self.assertAlmostEqual(r["delta"],100*(r["model"]-r["market"]))
        self.assertEqual(len(r["goals"]),4)
        self.assertEqual(r["forecast_sha"],self.fixture.f["payload_sha256"])
        self.assertEqual(r["status"],"PAS / ONAYSIZ")
        a=batch_pdf(self.root/"pdf"/"toplu.pdf",self.day,[r])
        b=single_pdf(self.root/"pdf"/"tekli.pdf",self.day,r)
        for f in (a,b):
            self.assertTrue(f.read_bytes().startswith(b"%PDF-"))
            self.assertEqual(len(PdfReader(str(f)).pages),1)
        s=PdfReader(str(a)).pages[0].extract_text()
        self.assertIn("BIZIM",s)
        self.assertIn("PIYASA",s)
        self.assertIn("KG Var",s)
        self.assertNotIn("1/X/2 oran",s)
        detail=PdfReader(str(b)).pages[0].extract_text()
        self.assertIn("DORT MODEL",detail)
        self.assertIn(r["forecast_sha"],detail)
    def test_missing_pinnacle_keeps_market_and_delta_blank(self):
        price,r=self.data()
        self.assertIsNone(r["market"])
        self.assertIsNone(r["delta"])
        p=batch_pdf(self.root/"no_price.pdf",self.day,[r])
        text=PdfReader(str(p)).pages[0].extract_text()
        self.assertIn("PIYASA",text)
        self.assertIn("—",text)
        self.assertIn("BIZIM",text)
    def test_wrong_day_sha_and_orphan_quote_fail_closed(self):
        price,r=self.data(True)
        fake=dict(price,day_turkey="2026-11-08")
        with self.assertRaisesRegex(MobileBlocked,"PRICE_DAY"):
            row_data(self.fixture.report,fake,self.root)
        bad=json.loads(json.dumps(price))
        bad["items"][0]["forecast_sha256"]="0"*64
        with self.assertRaisesRegex(MobileBlocked,"PRICE_FORECAST_SHA"):
            row_data(self.fixture.report,bad,self.root)
        bad=json.loads(json.dumps(price))
        bad["items"].append(dict(bad["items"][0]))
        with self.assertRaisesRegex(MobileBlocked,"DUPLICATE_PRICE"):
            row_data(self.fixture.report,bad,self.root)
    def test_price_report_must_be_reproducible_from_sealed_input(self):
        price,r=self.data(True)
        files=[]
        for label,obj in (("batch",self.fixture.report),("receipt",self.fixture.receipt),("price",price)):
            path=self.root/(label+".json");path.write_text(json.dumps(obj));files.append(path)
        count=run(*files,self.root,self.day,self.root/"generated")
        self.assertEqual(count,1)
        self.assertTrue((self.root/"generated"/"toplu.pdf").is_file())
        self.assertTrue((self.root/"generated"/"tekli"/(r["id"]+".pdf")).is_file())
        bad=json.loads(files[2].read_text())
        bad["items"][0]["status"]="FAKED_SUCCESS"
        files[2].write_text(json.dumps(bad))
        with self.assertRaisesRegex(MobileBlocked,"PRICE_REPORT_NOT_REPRODUCIBLE"):
            run(*files,self.root,self.day,self.root/"tampered")
    def test_forty_four_matches_paginate_and_remain_compact(self):
        _,r=self.data(True)
        rows=[]
        for n in range(44):
            x=dict(r)
            x["home"]="Very Long Official Home Club Name With District "+str(n)
            x["away"]="Very Long Official Away Club Name With District "+str(n)
            rows.append(x)
        p=batch_pdf(self.root/"44.pdf",self.day,rows)
        pdf=PdfReader(str(p))
        self.assertEqual(len(pdf.pages),5)
        self.assertEqual(sum(page.extract_text().count("FARK (yp)") for page in pdf.pages),44)
        self.assertTrue(all(float(page.mediabox.width)==420 for page in pdf.pages))
    def test_unavailable_models_are_not_filled_from_other_models(self):
        _,r=self.data(False)
        r["models"]={"B":{"status":"UNAVAILABLE"},"C2":{"status":"UNAVAILABLE"},
                     "C3":{"status":"UNAVAILABLE"},"M4":{"status":"UNAVAILABLE"}}
        r["goals"]=[None,None,None,None]
        pdf=single_pdf(self.root/"not_available.pdf",self.day,r)
        body=PdfReader(str(pdf)).pages[0].extract_text()
        self.assertIn("DORT MODEL",body)
        self.assertIn("—",body)
        self.assertIn("PAS",body)
    def test_raw_odds_values_are_not_rendered(self):
        price,r=self.data(True)
        path=single_pdf(self.root/"only.pdf",self.day,r)
        data=PdfReader(str(path)).pages[0].extract_text()
        self.assertNotIn("SYNTHETIC_NOT_REAL",data)
        self.assertNotIn("PINNACLE_DECIMAL",data)
        self.assertIn("PAS",data)
if __name__=="__main__":unittest.main()
