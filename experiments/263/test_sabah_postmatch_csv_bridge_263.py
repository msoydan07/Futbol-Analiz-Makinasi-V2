"""Deterministic, offline checks of real new100 SHA -> free CSV bridge."""
import csv,io,json,sys,unittest
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sabah_postmatch_csv_bridge_263 import report,ROOT,Aliases,parse_source,CODES,safe_csv_target
NOW=datetime(2026,11,10,16,tzinfo=timezone.utc)
def feed(url,score=(2,0),bad=False):
    code=url.split("/")[-1].split(".")[0]
    b=io.StringIO();w=csv.writer(b);w.writerow(["Div","Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"])
    if code=="E0":
        h,a=score
        w.writerow([code,"08/11/2026","Brighton","Brentford",h,a,"D" if bad else ("H" if h>a else "A" if h<a else "D")])
    return b.getvalue().encode("utf-8")
class Bridge(unittest.TestCase):
    def test_one_real_seal_matches_and_does_not_become_official(self):
        r=report(ROOT,now=NOW,fetcher=lambda url:feed(url))
        self.assertEqual(r["registered"],40)
        self.assertEqual(r["official_result_count"],0)
        self.assertFalse(r["human_attestation_generated"])
        self.assertGreaterEqual(r["provisional_completed"],1)
        x=[z for z in r["scored"] if z["home"]=="Brighton" and z["away"]=="Brentford"]
        self.assertEqual(len(x),1)
        self.assertEqual(x[0]["score"],[2,0])
        self.assertEqual(x[0]["status"],"CSV_AND_WEB_REVIEW_AGREE_NOT_OFFICIAL")
        self.assertIn("M4",x[0]["models"])
        self.assertEqual(len(r["scored"])+len(r["not_scored"]),40)
    def test_contradiction_is_pending_not_scored(self):
        r=report(ROOT,now=NOW,fetcher=lambda url:feed(url,score=(1,2)))
        self.assertFalse(any(z["home"]=="Brighton" for z in r["scored"]))
        self.assertTrue(any(z["home"]=="Brighton" and z["status"]=="CONFLICT_RESEARCH_AND_CSV" for z in r["not_scored"]))
    def test_corrupt_score_source_fails_closed(self):
        r=report(ROOT,now=NOW,fetcher=lambda url:feed(url,bad=True))
        self.assertEqual(r["source_status"]["ENG1"]["status"],"SOURCE_UNAVAILABLE_OR_REJECTED")
        self.assertFalse(any(z["home"]=="Brighton" for z in r["scored"]))
    def test_safe_csv_redirect_only_same_exact_source_file(self):
        src="https://www.football-data.co.uk/mmz4281/2627/E0.csv"
        self.assertTrue(safe_csv_target(src,src))
        self.assertTrue(safe_csv_target("https://football-data.co.uk/mmz4281/2627/E0.csv",src))
        self.assertFalse(safe_csv_target("http://www.football-data.co.uk/mmz4281/2627/E0.csv",src))
        self.assertFalse(safe_csv_target("https://evil.example/mmz4281/2627/E0.csv",src))
        self.assertFalse(safe_csv_target("https://www.football-data.co.uk/mmz4281/2627/D1.csv",src))
    def test_bad_date_and_names_never_fuzzy_merge(self):
        aliases=Aliases(ROOT)
        entries=parse_source("Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n08/11/2026,Imaginary Club,Brentford,2,0,H\n","ENG1",aliases)
        self.assertFalse(any(key[1]==aliases.key("ENG1","Brighton") for key in entries))
if __name__=="__main__":unittest.main()
