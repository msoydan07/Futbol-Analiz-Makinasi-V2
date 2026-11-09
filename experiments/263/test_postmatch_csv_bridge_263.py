"""Read-only CSV result intake and SHA-gated score matching."""
from __future__ import annotations
import unittest,sys
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parent))
from postmatch_csv_bridge_263 import ROOT,Names,feed_rows,evaluate,Blocked
NOW=datetime(2026,11,9,12,0,tzinfo=timezone.utc)
HEAD=b"Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
class Tests(unittest.TestCase):
    def test_exact_named_alias_from_verified_mappings(self):
        g=Names(ROOT)
        self.assertEqual(g.key("ENG1","Man United"),g.key("ENG1","Manchester United"))
        self.assertEqual(g.key("GER1","Leverkusen"),g.key("GER1","Bayer Leverkusen"))
        self.assertNotEqual(g.key("ENG1","Manchester City"),g.key("ENG1","Manchester United"))
    def test_real_sha_and_one_independently_matching_csv_research(self):
        data=HEAD+b"E0,08/11/2026,Brighton,Brentford,2,0,H\n"
        before=(ROOT/"forward_morning_263/2026-11-08/00156b675f1e2d1a941fba4c.json").read_bytes()
        r=evaluate(ROOT,now=NOW,fetcher=lambda url:data if url.endswith("E0.csv") else HEAD)
        self.assertEqual(r["registered"],40)
        self.assertEqual(r["provisional_scored"],1)
        self.assertEqual(r["rows"][0]["status"],"TWO_SOURCE_RESEARCH_CONCORDANT_NOT_OFFICIAL")
        self.assertEqual(r["per_model"]["ALL_PROVISIONAL"]["M4"]["n"],1)
        self.assertEqual(r["independent_federation_verified"],0)
        self.assertEqual(r["human_attestations_written"],0)
        self.assertEqual(before,(ROOT/"forward_morning_263/2026-11-08/00156b675f1e2d1a941fba4c.json").read_bytes())
    def test_conflicting_score_rejected_not_scored(self):
        data=HEAD+b"E0,08/11/2026,Brighton,Brentford,1,1,D\n"
        r=evaluate(ROOT,now=NOW,fetcher=lambda url:data if url.endswith("E0.csv") else HEAD)
        self.assertEqual(r["provisional_scored"],0)
        self.assertEqual(r["status_counts"]["WEB_REVIEW_CONFLICT"],1)
    def test_wrong_date_skipped_missing_teams_not_guessed(self):
        data=HEAD+b"E0,09/11/2026,Brighton,Brentford,2,0,H\n"
        r=evaluate(ROOT,now=NOW,fetcher=lambda url:data if url.endswith("E0.csv") else HEAD)
        self.assertEqual(r["provisional_scored"],0)
    def test_source_FTR_mismatch_blocks_league_not_model(self):
        data=HEAD+b"E0,08/11/2026,Brighton,Brentford,2,0,A\n"
        r=evaluate(ROOT,now=NOW,fetcher=lambda url:data if url.endswith("E0.csv") else HEAD)
        self.assertEqual(r["provisional_scored"],0)
        self.assertEqual(r["sources"]["ENG1"]["status"],"SOURCE_UNAVAILABLE")
    def test_duplicate_source_match_does_not_score(self):
        line=b"E0,08/11/2026,Brighton,Brentford,2,0,H\n"
        r=evaluate(ROOT,now=NOW,fetcher=lambda url:HEAD+line+line if url.endswith("E0.csv") else HEAD)
        self.assertEqual(r["provisional_scored"],0)
        self.assertEqual(r["status_counts"]["DUPLICATE_SOURCE_MATCH"],1)
if __name__=="__main__":unittest.main()
