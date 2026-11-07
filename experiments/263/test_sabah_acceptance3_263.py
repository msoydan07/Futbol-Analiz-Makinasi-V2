"""Offline end-to-end acceptance3 with synthetic fixtures; NEVER bookmaker."""
import hashlib,json,os,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import Mock
from sabah_batch_263 import run,save_new,sha,Blocked
from sabah_mobile_screens_263 import build
from sabah_acceptance_commit_guard_263 import verify,AcceptanceBlocked

NOW=datetime(2026,11,7,6,0,tzinfo=timezone.utc)
KO=NOW+timedelta(hours=8)
TEAMS=[("ESP1","Valencia","Real Madrid"),
       ("ENG1","Arsenal","Hull City"),
       ("TUR1","Samsunspor","Konyaspor")]
def gate(league,home,away):
    return {"status":"VERIFIED","league":league,
            "home_id":"H_"+home,"away_id":"A_"+away,
            "kickoff_utc":KO.isoformat(),"retrieved_at_utc":NOW.isoformat(),
            "source_url":"https://www.tff.org/synthetic-no-network"}
def fake_predict(g,history,out_dir,lock,now=None,base=None,source_audit=None):
    stem=hashlib.sha256(g["home_id"].encode()).hexdigest()[:24]
    p=Path(out_dir)/"2026-11-07"/(stem+".json")
    raw={"1X2":{"H":.50,"D":.28,"A":.22},"BTTS_YES":.57,"BTTS_NO":.43,
         "OVER_1.5":.78,"UNDER_1.5":.22,"OVER_2.5":.52,"UNDER_2.5":.48,
         "OVER_3.5":.32,"UNDER_3.5":.68}
    x={"schema":"quad_forward_263_v1","status":"EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING",
       "created_at_utc":now.isoformat(),
       "fixture":{"league":g["league"],"home_id":g["home_id"],"away_id":g["away_id"],
                  "kickoff_utc":g["kickoff_utc"],"match_local_date":"2026-11-07",
                  "official_source":g["source_url"],
                  "fixture_verification":"VERIFIED_BY_LIVE_OFFICIAL_GATE"},
       "data":{"snapshot_acceptance":"APPEND_ONLY_HUMAN_SOURCE_ATTESTED_NOT_INDEPENDENTLY_RECHECKED"},
       "model_predictions":{m:{"status":"AVAILABLE","goals":{"markets":raw}} for m in ("B","C2","C3","M4")}}
    # One diagnostic-only B model has insufficient historical context,
    # exactly as in the live Arsenal / Hull test. No imputation.
    if g["league"]=="ENG1":
        x["model_predictions"]["B"]={"status":"UNAVAILABLE_INSUFFICIENT_CONTEXT"}
    x["payload_sha256"]=sha(x);save_new(p,x)
    return p,x
def baseline(f,path,now=None):
    x={"schema":"synthetic_baseline","forecast_sha256":f["payload_sha256"],
       "created_at_utc":now.isoformat(),"markets":{}}
    x["payload_sha256"]=sha(x);return x
def decide(f,b,l,observation=None,now=None):
    x={"schema":"263_four_model_value_decision_research_v1",
       "status":"RESEARCH_PAS","forecast_sha256":f["payload_sha256"],
       "baseline_sha256":b["payload_sha256"],"created_at_utc":now.isoformat(),
       "quote_sha256":None,"main_candidate":None,"alternative_candidate":None,
       "betting_authorized":False,"all_market_diagnostics":[]}
    x["payload_sha256"]=sha(x);return x

class Acceptance3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=os.getcwd();os.chdir(self.tmp.name)
        Path("experiments/263").mkdir(parents=True)
        self.manifest=Path("experiments/263/manifest.json")
        self.manifest.write_text(json.dumps({"schema":"SABAH_TOPLU_V1",
            "day_turkey":"2026-11-07",
            "matches":[{"league":l,"home":h,"away":a} for l,h,a in TEAMS]}),encoding="utf-8")
        for p in ("data.csv","base.csv","accepted.json","m4_lock.json","dev_lock.json"):
            Path(p).write_text("{}",encoding="utf-8")
    def tearDown(self):os.chdir(self.old);self.tmp.cleanup()
    def make(self):
        return run("acceptance3","2026-11-07",self.manifest,
                   "data.csv","base.csv","accepted.json","m4_lock.json",
                   now=NOW,lookup=gate,predictor=fake_predict,
                   baseline_fn=baseline,decision_fn=decide,dev_lock_path="dev_lock.json")
    def bundle(self):
        r=self.make()
        report=Path("experiments/263/sabah_batch_reports/b.json")
        save_new(report,r)
        summary,singles=build(".",r)
        mobile=Path("experiments/263/sabah_mobile_reports/m")
        (mobile/"matches").mkdir(parents=True)
        (mobile/"summary.md").write_text(summary,encoding="utf-8")
        for k,v in singles.items():
            (mobile/"matches"/(k+".md")).write_text(v,encoding="utf-8")
        return r,report,mobile
    def test_acceptance3_all_models_and_screens_reconcile(self):
        r,report,mobile=self.bundle()
        e=verify(report,mobile,now=NOW+timedelta(minutes=1))
        self.assertEqual(e["accepted_count"],3)
        self.assertEqual(len(e["records"]),3)
        self.assertTrue(e["all_mobile_pages_exactly_reproducible"])
        self.assertEqual(e["bookmaker_api_calls"],0)
        self.assertFalse(Path("forward_morning_263").exists())
        self.assertFalse(Path("forward_quad_263").exists())
    def test_B_context_unavailable_is_labelled_not_imputed(self):
        r,report,mobile=self.bundle()
        receipt=verify(report,mobile,now=NOW+timedelta(minutes=1))
        bstatus={x["league"]:x["model_statuses"]["B"] for x in receipt["records"]}
        self.assertEqual(bstatus["ENG1"],"UNAVAILABLE_INSUFFICIENT_CONTEXT")
        self.assertEqual([x["model_available_count"] for x in receipt["records"]],[4,3,4])
        pages=[p.read_text(encoding="utf-8") for p in (mobile/"matches").glob("*.md")]
        self.assertTrue(any("UNAVAILABLE_INSUFFICIENT_CONTEXT" in page for page in pages))
        self.assertIn("3/4 model", (mobile/"summary.md").read_text(encoding="utf-8"))
    def test_all_three_duplicate_entries_are_not_added_twice(self):
        r,report,mobile=self.bundle()
        again=self.make()
        self.assertEqual(again["new_forecasts"],0)
        self.assertEqual(again["already_sealed"],3)
    def test_one_changed_mobile_page_rejected(self):
        r,report,mobile=self.bundle()
        (mobile/"summary.md").write_text("fake 99% winning")
        with self.assertRaises(AcceptanceBlocked):verify(report,mobile,now=NOW)
    def test_model_missing_fail_closed(self):
        r,report,mobile=self.bundle()
        f=Path(r["outcomes"][0]["forecast_path"])
        d=json.loads(f.read_text());d["model_predictions"]["M4"]["status"]="UNAVAILABLE"
        d["payload_sha256"]=sha({k:v for k,v in d.items() if k!="payload_sha256"})
        f.write_text(json.dumps(d))
        with self.assertRaises((AcceptanceBlocked,ValueError)):verify(report,mobile,now=NOW)
    def test_after_kickoff_no_retroactive_commit(self):
        r,report,mobile=self.bundle()
        with self.assertRaises((AcceptanceBlocked,Blocked)):
            verify(report,mobile,now=KO)
    def test_decision_missing_rejected(self):
        r,report,mobile=self.bundle()
        p=Path(r["outcomes"][0]["forecast_path"])
        decision_path=Path("experiments/263/sabah_research/acceptance3/2026-11-07")/p.stem/"decision.json"
        decision_path.unlink()
        with self.assertRaises((AcceptanceBlocked,OSError,ValueError)):
            verify(report,mobile,now=NOW)
    def test_four_match_manifest_will_not_consume_pilot(self):
        m=json.loads(self.manifest.read_text())
        m["matches"].append({"league":"ITA1","home":"Roma","away":"Sassuolo"})
        self.manifest.write_text(json.dumps(m))
        with self.assertRaises(Blocked):self.make()
        self.assertFalse(Path("forward_acceptance_263").exists())
    def test_aborted_decision_marks_blocked_not_registered(self):
        def fail(*args,**kwargs):raise ValueError("synthetic decision failure")
        res=run("acceptance3","2026-11-07",self.manifest,
            "data.csv","base.csv","accepted.json","m4_lock.json",
            now=NOW,lookup=gate,predictor=fake_predict,
            baseline_fn=baseline,decision_fn=fail,dev_lock_path="dev_lock.json")
        self.assertEqual(res["new_forecasts"],0)
        self.assertEqual(res["blocked"],3)
        self.assertFalse(Path("forward_quad_263").exists())
if __name__=="__main__":unittest.main()
