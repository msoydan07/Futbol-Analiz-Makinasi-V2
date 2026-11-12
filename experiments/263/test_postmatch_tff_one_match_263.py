"""Frozen Nov 8 Corum-Fenerbahce official source missing CSV result regression."""
import unittest
from datetime import datetime,timezone
from postmatch_csv_bridge_263 import ROOT,evaluate,sealed,registered_names
from postmatch_tff_one_match_263 import verify_one,parse_tff,Blocked,FORECAST_SHA

NOW=datetime(2026,11,12,9,0,tzinfo=timezone.utc)
HEAD=b"Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
HTML="""<html><head><title>TFF Maç Detayları</title></head><body>
<a>ARCA ÇORUM FK</a><strong>0</strong><a>FENERBAHÇE A.Ş.</a><strong>5</strong>
<p>Trendyol Süper Lig Adnan Süvari Sezonu</p>
<p>8.11.2026 - 16:00</p></body></html>"""

class TFFSingleSourceTests(unittest.TestCase):
    def test_actual_sealed_sha_and_independent_page_evidence(self):
        f=sealed(ROOT)[FORECAST_SHA]
        b=registered_names(ROOT)[FORECAST_SHA]
        out=verify_one(f,b,now=NOW,fetcher=lambda _:HTML.encode("utf-8"))
        self.assertEqual(out["score"],[0,5])
        self.assertEqual(out["forecast_sha256"],FORECAST_SHA)
        self.assertFalse(out["human_attestation_written"])
        self.assertFalse(out["original_forecast_modified"])
    def test_csv_missing_one_exact_official_source_recovers_without_rewriting(self):
        prior=(ROOT/"forward_morning_263/2026-11-08/f0a7dd75ba79329ab6e1bff1.json").read_bytes()
        r=evaluate(ROOT,now=NOW,
           fetcher=lambda _:HEAD,official_tff_fetcher=lambda _:HTML.encode("utf-8"))
        self.assertEqual(r["registered"],40)
        self.assertEqual(r["provisional_scored"],1)
        self.assertEqual(r["independent_federation_verified"],1)
        self.assertEqual(r["human_attestations_written"],0)
        self.assertEqual(r["status_counts"]["OFFICIAL_TFF_NETWORK_READ_RESEARCH_NOT_HUMAN_ATTESTED"],1)
        score=next(x for x in r["rows"] if x["forecast_sha256"]==FORECAST_SHA)
        self.assertEqual(score["score"],[0,5])
        self.assertIsNone(score["csv_url"])
        self.assertEqual(score["official_network_evidence"]["source_url"],
                         "https://www.tff.org/Default.aspx?macId=317879&pageId=29")
        self.assertEqual(prior,(ROOT/"forward_morning_263/2026-11-08/f0a7dd75ba79329ab6e1bff1.json").read_bytes())
    def test_html_mismatch_and_ambiguity_are_blocked(self):
        for variant in (
           HTML.replace("ARCA ÇORUM FK","GÖZTEPE"),
           HTML.replace("8.11.2026 - 16:00","8.11.2026 - 20:00"),
           HTML.replace("Trendyol Süper Lig","Ziraat Kupası"),
           HTML.replace("<strong>5</strong>","<strong>5</strong><span>FENERBAHÇE A.Ş. 2</span>").replace(
                "<strong>0</strong><a>FENERBAHÇE", "<strong>1</strong><a>FENERBAHÇE"),
        ):
            with self.subTest(variant=variant[:32]):
                with self.assertRaises(Blocked):parse_tff(variant)
    def test_wrong_official_score_blocks_conflict(self):
        mismatch=HTML.replace("<strong>5</strong>","<strong>4</strong>")
        r=evaluate(ROOT,now=NOW,fetcher=lambda _:HEAD,
                   official_tff_fetcher=lambda _:mismatch.encode())
        self.assertEqual(r["independent_federation_verified"],0)
        self.assertEqual(r["provisional_scored"],0)
        self.assertEqual(r["status_counts"]["WEB_REVIEW_CONFLICT"],1)
    def test_unavailable_official_page_stays_pending(self):
        def offline(_):raise OSError("TFF blocked")
        r=evaluate(ROOT,now=NOW,fetcher=lambda _:HEAD,official_tff_fetcher=offline)
        self.assertEqual(r["provisional_scored"],0)
        self.assertEqual(r["independent_federation_verified"],0)
        item=next(x for x in r["pending_rows"] if x["forecast_sha256"]==FORECAST_SHA)
        self.assertEqual(item["status"],"NO_EXACT_RESULT")
        self.assertEqual(item["tff_source_status"],"NOT_INDEPENDENTLY_VERIFIED")
    def test_no_match_kickoff_future_blocks(self):
        f=sealed(ROOT)[FORECAST_SHA];b=registered_names(ROOT)[FORECAST_SHA]
        with self.assertRaises(Blocked):
            verify_one(f,b,now=datetime(2026,11,8,13,30,tzinfo=timezone.utc),
                       fetcher=lambda _:HTML)
if __name__=="__main__":unittest.main()
