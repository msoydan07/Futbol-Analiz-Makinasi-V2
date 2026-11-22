"""Permanent regression: official fixture parser failure must not kill M4/C3.

Uses actual frozen historical snapshot, original first-PDF quote layout,
canonical 215-club identity and exact frozen research calibration.
No real bookmaker, no actual official lookup, no backdated real betting seal.
"""
import copy
import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import fitz

from iddaa_pdf_source_fallback_263 import attach,verify_research_record
from iddaa_pdf_session_263 import market_no_vig,pdf_prices,SCHEMA as SESSION_SCHEMA
from iddaa_pdf_first_quote_263 import sha256
from iddaa_pdf_approved_layout_263 import render_batch
from iddaa_pdf_team_alias_preflight_263 import index_registry,resolve_label

ROOT=Path(__file__).resolve().parents[2]
HISTORY=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
BASE=ROOT/"m4_quad_base/historical_results.csv"
AUDIT=ROOT/"data/results_only_263/4617_research_input_provenance.json"
M4=ROOT/"experiments/263/m4_lock.json"
LOCK=ROOT/"experiments/263/model_first_selection_lock_20261121_v4.json"
NOW=datetime(2026,11,22,10,32,tzinfo=timezone.utc)
SHA="d"*64


def fixtures():
    return [
        ("Go Ahead Eagles","Fortuna Sittard","18:45",
         {"MS1":1.67,"MSX":3.56,"MS2":3.61,"O25_UNDER":2.21,
          "O25_OVER":1.42,"BTTS_YES":1.41,"BTTS_NO":2.23}),
        ("Twente","Willem II","14:15",
         {"MS1":None,"MSX":10.60,"MS2":17.80,"O25_UNDER":3.89,
          "O25_OVER":1.11,"BTTS_YES":1.83,"BTTS_NO":1.63}),
    ]


def make():
    raw=[];rows=[]
    for i,(home,away,time,odds) in enumerate(fixtures()):
        source={"status":"PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK",
                "league":"NED1","home_label":home,"away_label":away,
                "match_date_tr":"2026-11-22","kickoff_time_tr":time,
                "page":1,"odds":odds}
        raw.append(source)
        rows.append({
            "index":i,"status":"ONE_ROW_OFFICIAL_FIXTURE_NOT_VERIFIED",
            "model_forecast_created":False,
            "league":"NED1","pdf_home":home,"pdf_away":away,
            "match_date_tr":"2026-11-22","kickoff_time_tr":time,
            "pdf_page":1,"prices":pdf_prices(source),
            "market_no_vig":market_no_vig(source),
            "price_capture_utc":"2026-11-22T08:20:00+00:00",
            "official_lookup_attempts":1,
        })
    bulletin={"pdf_sha256":SHA,"rows":raw,"source_domain":"iddaa.com",
              "pdf_capture_utc":"2026-11-22T08:20:00+00:00"}
    session={"schema":SESSION_SCHEMA,"source_bookmaker":"iddaa.com",
             "pdf_sha256":SHA,"source_rows":2,
             "pdf_capture_utc":"2026-11-22T08:20:00+00:00",
             "session_created_utc":"2026-11-22T10:31:00+00:00",
             "policy_dev_lock_sha256":"dummy-unused-for-pdf-only",
             "rows":rows}
    session["signed_research_session_sha256"]=sha256(session)
    return bulletin,session


def run(b,s):
    return attach(b,s,history=HISTORY,source_baseline=BASE,
                  source_acceptance=AUDIT,m4_lock=M4,dev_lock=LOCK,now=NOW)


class TestRealFrozenPDFResearchFallback(unittest.TestCase):
    def test_exact_reused_model_math_and_missing_favorite(self):
        b,s=make()
        before=copy.deepcopy(s)
        out=run(b,s)
        self.assertEqual(out["pdf_source_model_math_count"],2)
        self.assertEqual(out["pdf_source_research_blocked_count"],0)
        self.assertEqual(s,before)
        self.assertEqual(out["signed_research_session_sha256"],sha256({
            k:v for k,v in out.items() if k!="signed_research_session_sha256"}))
        a=out["rows"][0]["pdf_source_research"]
        t=out["rows"][1]["pdf_source_research"]
        self.assertEqual(a["main"]["market"],"BTTS_YES")
        self.assertAlmostEqual(a["main"]["calibrated_probability"],.6440030254,places=9)
        self.assertEqual(a["p0"]["choice"],"BTTS_YES")
        self.assertEqual(a["p2_status"],"UYUMLU")
        self.assertEqual(t["main"]["market"],"MS1")
        self.assertAlmostEqual(t["main"]["calibrated_probability"],.8995465007,places=9)
        self.assertIsNone(t["p0"])
        self.assertEqual(t["p2_status"],"ORAN_EKSIK")
        for i,r in enumerate(out["rows"]):
            self.assertNotIn("model_first_decision",r)
            self.assertFalse(r["model_forecast_created"])
            self.assertFalse(r["pdf_source_research"]["official_fixture_verified"])
            verify_research_record(r["pdf_source_research"],SHA,r)
        with tempfile.TemporaryDirectory() as d:
            p=render_batch(out,Path(d)/"toplu_analiz_onayli.pdf")
            with fitz.open(p) as doc:
                txt="\n".join(page.get_text() for page in doc)
                for t in ("ANA MAKİNE","P0","P2: UYUMLU",
                          "P2: ORAN EKSİK","PDF KAYNAKLI",
                          "RESMÎ ONAY YOK","Alternatif:"):
                    self.assertIn(t,txt)
                self.assertNotIn("Şart 1",txt)

    def test_second_pdf_preserves_pdf_only_morning_choices_with_source_grade(self):
        from iddaa_pdf_bulletin_263 import SCHEMA as BULLETIN_SCHEMA
        from iddaa_pdf_last_review_263 import build as build_review
        from iddaa_pdf_approved_layout_263 import render_singles
        b,s=make()
        original=run(b,s)
        original["bookmaker_reverification_calls"]=0
        original["signed_research_session_sha256"]=sha256({
            k:v for k,v in original.items() if k!="signed_research_session_sha256"})
        first={**b,"schema":BULLETIN_SCHEMA}
        last=copy.deepcopy(first)
        last["pdf_sha256"]="e"*64
        last["pdf_capture_utc"]="2026-11-22T14:50:00+00:00"
        last["rows"][0]["odds"]["BTTS_YES"]=1.43
        idx,_,_=index_registry()
        def resolve(lg,name):
            result=resolve_label(lg,name,idx)
            return result["team_id"] if result["status"]=="MAPPED" else None
        review=build_review(original,first,last,[],
                datetime(2026,11,22,15,0,tzinfo=timezone.utc),resolver=resolve)
        self.assertEqual(review["matches_reviewed"],2)
        go=next(x for x in review["rows"] if x["home"]=="Go Ahead Eagles")
        self.assertEqual(go["morning_source_grade"],
                         "PDF_ONLY_NOT_FEDERATION_VERIFIED")
        self.assertEqual(go["morning_main_choice"]["market"],"BTTS_YES")
        self.assertAlmostEqual(go["morning_p2_agreement"] or 0,0)
        self.assertEqual(go["latest_odds"]["BTTS_YES"],1.43)
        with tempfile.TemporaryDirectory() as d:
            outputs=render_singles(review,Path(d)/"singles")
            self.assertEqual(len(outputs),1)
            with fitz.open(outputs[0]) as doc:
                text=doc[0].get_text()
                for word in ("ANA TERCİH","ALTERNATİF","P0 PİYASA",
                             "Tercihler","Yüzdeler","Oranlar","MAÇ YORUMU",
                             "PDF KAYNAKLI","RESMÎ ONAY YOK"):
                    self.assertIn(word,text)

    def test_bad_row_cannot_reuse_other_pdf_research_record(self):
        b,s=make();out=run(b,s)
        one=out["rows"][0];rec=copy.deepcopy(one["pdf_source_research"])
        rec["main"]["calibrated_probability"]+=.1
        with self.assertRaisesRegex(ValueError,"PDF_RESEARCH_RECORD"):
            verify_research_record(rec,SHA,one)
        with self.assertRaisesRegex(ValueError,"PDF_RESEARCH_RECORD"):
            verify_research_record(one["pdf_source_research"],"a"*64,one)

    def test_kickoff_past_stays_blocked_without_postmatch_model(self):
        b,s=make()
        b["rows"][0]["kickoff_time_tr"]="10:00"
        s["rows"][0]["kickoff_time_tr"]="10:00"
        s["signed_research_session_sha256"]=sha256({
            k:v for k,v in s.items() if k!="signed_research_session_sha256"})
        out=run(b,s)
        self.assertEqual(out["pdf_source_model_math_count"],1)
        self.assertEqual(out["rows"][0]["pdf_source_research_status"],
                         "PDF_CAPTURE_OR_RUN_AFTER_KICKOFF")
        self.assertNotIn("pdf_source_research",out["rows"][0])

    def test_missing_history_provenance_never_bypasses_data_gate(self):
        b,s=make()
        self.assertEqual(attach(b,s,history=HISTORY,source_baseline=None,
            source_acceptance=None,m4_lock=M4,dev_lock=LOCK,now=NOW),s)

    def test_canonical_alias_review_is_exact_not_fuzzy(self):
        index,_,_=index_registry()
        for lg,label in (("ESP1","Racing Santander"),("ITA1","AC Milan"),
                         ("BEL1","Standard Liege")):
            self.assertEqual(resolve_label(lg,label,index)["status"],"MAPPED")
            self.assertEqual(resolve_label(lg,label+" random",index)["status"],
                             "UNMAPPED_NAME_SINGLE_MATCH_ONLY")


if __name__=="__main__":unittest.main()
