"""User-approved permanent v3 first and second PDF renderers, fully offline.

No invented bookmaker prices, no model retraining, no changes to old seals.
"""
import json
import tempfile
import unittest
from pathlib import Path

import fitz
from iddaa_pdf_approved_layout_263 import render_batch,render_singles
from iddaa_pdf_session_263 import SCHEMA as MORNING_SCHEMA
from iddaa_pdf_first_quote_263 import sha256
from model_first_decision_263 import select,market_reference
from test_model_first_decision_263 import scenario,LOCK,NOW
from test_iddaa_pdf_last_review_263 import make,NOW as REVIEW_NOW
from iddaa_pdf_last_review_263 import build as review_build
from experiments.p1_market_intelligence.p1_market import no_vig
from experiments.p1_market_intelligence.p2_market_alignment import align_first_pdf_snapshot
from experiments.p1_market_intelligence.test_p2_market_alignment import snapshot,ODDS


def sample_immutable_first_pdf():
    f,b=scenario()
    d=select(f,b,LOCK,now=NOW)
    source_sha="a"*64
    snap=snapshot(ODDS)
    snap.update({
        "fixture_key":"TUR1:synthetic-home:synthetic-away:2026-11-21",
        "kickoff_utc":"2026-11-21T17:00:00+00:00",
        "forecast_sha256":d["forecast_sha256"],
        "source_pdf_sha256":source_sha,
        "observed_at_utc":"2026-11-21T09:00:00+00:00",
        "created_after_pdf_forecast_utc":"2026-11-21T10:00:00+00:00",
    })
    snap["payload_sha256"]=sha256({k:v for k,v in snap.items() if k!="payload_sha256"})
    p2=align_first_pdf_snapshot(d,snap)
    source_groups={"MS":"MS","OU25":"GOALS_2.5","KG":"KG"}
    groups={}
    for g,odds in ODDS.items():
        n=no_vig(odds)
        groups[source_groups[g]]={
            "status":"FULL_MARKET_QUOTE_AVAILABLE",
            "prices":odds,"no_vig":n["probabilities"],
        }
    reference=market_reference(d,groups,source_pdf_sha256=source_sha)
    flat={k:v for vals in ODDS.values() for k,v in vals.items()}
    row={
        "index":0,"league":"TUR1","pdf_home":"Sentetik Ev","pdf_away":"Sentetik Dep",
        "match_date_tr":"2026-11-21","kickoff_time_tr":"20:00",
        "status":"FOUR_MODELS_FORECAST_SHA_CREATED",
        "model_forecast_sha256":d["forecast_sha256"],
        "empirical_baseline_sha256":d["baseline_sha256"],
        "model_first_decision":d,
        "market_fifth_reference":reference,
        "pdf_first_price_snapshot":snap,
        "p2_agreement":p2,
        "prices":flat,
    }
    s={"schema":MORNING_SCHEMA,"pdf_sha256":source_sha,
       "policy_dev_lock_sha256":d["model_policy_sha256"],
       "rows":[row]}
    s["signed_research_session_sha256"]=sha256(s)
    return s,d,p2


class TestThreeMachinePermanentPDFs(unittest.TestCase):
    def test_first_uses_model_p0_independent_tops_and_p2_verdict(self):
        first,decision,p2=sample_immutable_first_pdf()
        with tempfile.TemporaryDirectory() as temp:
            path=render_batch(first,Path(temp)/"toplu_analiz_onayli.pdf")
            with fitz.open(path) as pdf:
                self.assertEqual(len(pdf),1)
                text=pdf[0].get_text()
                self.assertIn("ANA MAKİNE",text)
                self.assertIn("P0",text)
                self.assertIn("P2:",text)
                self.assertIn("Alternatif:",text)
                self.assertIn("Oran:",text)
                self.assertIn("Fark:",text)
                self.assertNotIn("Şart 1",text)
                self.assertNotIn("BİZİM %",text)
                self.assertIn("Sentetik Ev - Sentetik Dep",text)
            self.assertEqual(first["rows"][0]["model_first_decision"],decision)
            self.assertEqual(first["rows"][0]["p2_agreement"],p2)
            with self.assertRaises(FileExistsError):render_batch(first,path)

    def test_second_preserves_same_morning_model_and_p0_with_seven_strip(self):
        morning,d,p2=sample_immutable_first_pdf()
        base,first,last,resolver=make()
        review=review_build(base,first,last,[],REVIEW_NOW,resolver=resolver)
        target=review["rows"][0]
        target.update({
            "morning_main_choice":d["main_candidate"],
            "morning_alternative_choice":d["alternative_candidate"],
            "morning_decision_sha256":d["payload_sha256"],
            "morning_model_sha256":d["forecast_sha256"],
            "morning_p2_agreement":p2,
            "morning_odds":{k:v for vals in ODDS.values() for k,v in vals.items()},
        })
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/"tekli"
            bundle=Path(temp)/"tekli_rapor.pdf"
            out=render_singles(review,folder,bundle_pdf=bundle)
            self.assertEqual(len(out),5)
            with fitz.open(out[0]) as pdf:
                self.assertEqual(len(pdf),1)
                text=pdf[0].get_text()
                for s in ("ANA TERCİH","ALTERNATİF","P0 PİYASA","Tercihler",
                          "Yüzdeler","Oranlar","İlk oran","Son oran",
                          "Fark","MAÇ YORUMU"):
                    self.assertIn(s,text)
                self.assertNotIn("Şart 1",text)
                self.assertNotIn("ORAN KARŞILAŞTIRMASI",text)
                self.assertNotIn("MODEL ÖZETİ",text)
                self.assertIn("İlk 11",text)
                self.assertIn("MS 1",text)
            with fitz.open(bundle) as merged:self.assertEqual(len(merged),5)
            self.assertEqual(target["morning_p2_agreement"],p2)
            self.assertEqual(target["morning_main_choice"],d["main_candidate"])

    def test_second_wrong_p0_decision_sha_fails_closed(self):
        base,first,last,resolver=make()
        review=review_build(base,first,last,[],REVIEW_NOW,resolver=resolver)
        review["rows"][0]["morning_p2_agreement"]={
            "model_decision_sha256":"a"*64,
            "p0_highest_is_global":True,
            "p0_highest_choice":"MS1","p0_highest_probability":.55,
        }
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,"P0_ORIGINAL_MORNING_SHA"):
                render_singles(review,Path(temp)/"tekli")

if __name__=="__main__":
    unittest.main(verbosity=2)
