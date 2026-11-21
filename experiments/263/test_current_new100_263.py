"""Active new100 contract: one real code path, synthetic fixture/no outside APIs.

The forecast and baseline are already SHA-signed, then actual model-first
new100 code must create its own decision and repeatable mobile / price
reference. No real kickoff, no credentials, and no historical record mutation.
"""
import copy
import json
import os
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path

from test_model_first_decision_263 import scenario,seal
from sabah_batch_263 import run,save_new,sha
from sabah_mobile_screens_263 import build
from sabah_new100_commit_guard_263 import verify as verify_receipt
from sabah_pinnacle_new100_bridge_263 import render as price_render
from sabah_mobile_approved_pdf_263 import row_data

NOW=datetime(2026,11,21,10,5,tzinfo=timezone.utc)
KO=datetime(2026,11,21,17,0,tzinfo=timezone.utc)
DAY="2026-11-21"

def named_fixture(league,home,away):
    return {"status":"VERIFIED","league":league,"home_id":"synthetic-home",
            "away_id":"synthetic-away","kickoff_utc":KO.isoformat(),
            "retrieved_at_utc":NOW.isoformat(),
            "source_url":"https://www.tff.org/synthetic-no-network"}

def predictor(g,history,out_dir,lock,now=None,base=None,source_audit=None):
    f,_=scenario()
    # The production forecast includes all full-time market lines.
    # Fill the synthetic auxiliary lines without changing the core MS/KG/O25.
    import math
    mu=3.4
    over15=1-math.exp(-mu)*(1+mu)
    over35=1-math.exp(-mu)*(1+mu+mu*mu/2+mu**3/6)
    for m in f["model_predictions"].values():
        if m.get("status")=="AVAILABLE":
            marks=m["goals"]["markets"]
            marks.update({"OVER_1.5":over15,"UNDER_1.5":1-over15,
                          "OVER_3.5":over35,"UNDER_3.5":1-over35})
    f["fixture"]["official_source"]=g["source_url"]
    f["fixture"]["source_checked_at_utc"]=NOW.isoformat()
    f["data"].update(snapshot_acceptance="APPEND_ONLY_4617_PUBLIC_RESULTS_ONLY_RESEARCH_NOT_OFFICIAL_ID_VERIFIED",
                     human_source_acceptance=False,research_shadow_unverified_source=False)
    seal(f)
    path=Path(out_dir)/DAY/("a"*24+".json")
    save_new(path,f)
    return path,f

def baseline(f,history,now=None):
    _,b=scenario()
    b["forecast_sha256"]=f["payload_sha256"]
    seal(b)
    return b

class CurrentNew100Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.prev=os.getcwd()
        os.chdir(self.tmp.name)
        self.addCleanup(lambda:os.chdir(self.prev))
        d=Path("experiments/263")
        d.mkdir(parents=True)
        self.manifest=d/"new100.json"
        self.manifest.write_text(json.dumps(
            {"schema":"SABAH_TOPLU_V1","day_turkey":DAY,
             "matches":[{"league":"TUR1","home":"A","away":"B"}]}),encoding="utf-8")
        for filename in ("history.csv","baseline.csv","accepted.json","m4_lock.json"):
            Path(filename).write_text("synthetic",encoding="utf-8")
        from test_model_first_decision_263 import HERE
        (d/"model_first_selection_lock_20261121_v4.json").write_bytes(
            (HERE/"model_first_selection_lock_20261121_v4.json").read_bytes())

    def get(self):
        report=run("new100",DAY,self.manifest,
                   "history.csv","baseline.csv","accepted.json","m4_lock.json",
                   now=NOW,lookup=named_fixture,predictor=predictor,
                   baseline_fn=baseline)
        self.assertEqual(report["new_forecasts"],1,report)
        self.assertEqual(report["blocked"],0,report)
        row=report["outcomes"][0]
        decision=json.loads((Path("experiments/263/sabah_research/new100")/DAY/
                             Path(row["forecast_path"]).stem/"decision.json").read_text())
        return report,row,decision

    def test_main_candidate_without_odds_is_not_forced_pas(self):
        r,row,d=self.get()
        self.assertEqual(d["schema"],"263_MODEL_FIRST_FOUR_MODEL_DECISION_RESEARCH_V2")
        self.assertEqual(d["status"],"RESEARCH_CANDIDATE_NOT_APPROVED")
        self.assertEqual(d["main_candidate"]["market"],"MS1")
        self.assertEqual(d["main_candidate"]["anchor_model"],"M4")
        self.assertFalse(d["price_used_in_decision"])
        self.assertFalse(d["odds_affected_selection"])
        self.assertEqual(row["decision_sha256"],d["payload_sha256"])
        self.assertEqual(r["xg_private_results"],0)

    def test_mobile_and_receipt_use_current_selection(self):
        report,row,d=self.get()
        source=Path("batch.json")
        save_new(source,report)
        summary,pages=build(".",report)
        self.assertIn("ortak M4",summary)
        self.assertIn("DENEYSEL MS1",summary)
        self.assertIn("Model-first ana:",next(iter(pages.values())))
        self.assertIn("MS=M4, KG/2.5=C3",next(iter(pages.values())))
        folder=Path("screens")
        (folder/"matches").mkdir(parents=True)
        (folder/"summary.md").write_text(summary,encoding="utf-8")
        for stem,body in pages.items():
            (folder/"matches"/(stem+".md")).write_text(body,encoding="utf-8")
        receipt=verify_receipt(source,folder,now=NOW+timedelta(minutes=1))
        self.assertEqual(receipt["decisions"],"MODEL_FIRST_M4_MS_C3_KG_O25")
        self.assertEqual(receipt["records"][0]["decision_sha256"],d["payload_sha256"])

    def test_pinnacle_price_reference_only_never_reselects(self):
        from sabah_pinnacle_new100_bridge_263 import calibrated_sidecar
        report,row,d=self.get()
        forecast=json.loads(Path(row["forecast_path"]).read_text(encoding="utf-8"))
        reference={"pinnacle_no_vig_probabilities":{"H":.53,"D":.25,"A":.22},
                   "odds":{"H":1.78,"D":3.8,"A":4.4}}
        q,source=calibrated_sidecar(Path("."),report,forecast,row,reference)
        self.assertEqual(source,d["payload_sha256"])
        self.assertEqual(set(q),{"MS1","MSX","MS2"})
        for k in ("MS1","MSX","MS2"):
            self.assertEqual(q[k]["anchor_model"],"M4")
            self.assertTrue(q[k]["not_model_selection_input"])
        original=json.loads((Path("experiments/263/sabah_research/new100")/DAY/
                            Path(row["forecast_path"]).stem/"decision.json").read_text())
        self.assertEqual(original["payload_sha256"],d["payload_sha256"])
        self.assertEqual(original["main_candidate"]["market"],"MS1")

    def test_named_without_user_pdf_has_zero_prices_and_generates_model_pdf(self):
        from sabah_mobile_model_only_263 import build_model_only,render
        report,row,d=self.get()
        source=Path("batch.json");save_new(source,report)
        result=build_model_only(report,Path("."))
        self.assertEqual(len(result),1)
        self.assertIsNone(result[0]["market"])
        self.assertIsNone(result[0]["delta"])
        self.assertIn("ANA: MS 1",result[0]["status"])
        created=render(source,Path("."),"out_pdf")
        self.assertEqual(created["status"],"MODEL_ONLY_MOBILE_PDF_NO_PRICE_SOURCE")
        self.assertEqual(created["odds_api_calls"],0)
        self.assertTrue((Path("out_pdf")/"toplu.pdf").read_bytes().startswith(b"%PDF-"))
        # The live new100 model-only batch MUST use the user's permanent
        # four-column approved cards, not the old monochrome summary table.
        import fitz
        with fitz.open(Path("out_pdf")/"toplu.pdf") as approved:
            pdf_text=approved[0].get_text()
            for label in ("TÜRKİYE SÜPER LİG","ANA TERCİH",
                          "BİZİM %","PİYASA %","FARK (PUAN)",
                          "VERİ YOK","Alternatif:","SABAH / MODEL-ONLY"):
                self.assertIn(label,pdf_text)
            self.assertIn("MS 1",pdf_text)
            self.assertNotIn("Ana iddaa oranı: 1,",pdf_text)

    def test_absent_pinnacle_price_cannot_change_model_pick(self):
        report,row,d=self.get()
        source=Path("batch.json");save_new(source,report)
        summary,pages=build(".",report)
        folder=Path("screens");(folder/"matches").mkdir(parents=True)
        (folder/"summary.md").write_text(summary,encoding="utf-8")
        for stem,body in pages.items():
            (folder/"matches"/(stem+".md")).write_text(body,encoding="utf-8")
        receipt=verify_receipt(source,folder,now=NOW+timedelta(minutes=1))
        price=price_render(report,receipt,Path("."),Path("no_price_snapshots"))
        self.assertEqual(price["items"][0]["status"],"NO_VALID_SAME_TIME_PINNACLE_REFERENCE")
        rr=row_data(report,price,Path("."))
        self.assertEqual(len(rr),1)
        self.assertIn("ANA: MS 1",rr[0]["status"])
        self.assertIsNone(rr[0]["market"])
        self.assertIsNone(rr[0]["delta"])
        self.assertEqual(rr[0]["decision_sha"],d["payload_sha256"])

if __name__=="__main__":
    unittest.main()
