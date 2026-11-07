"""New100 sealed SHA/mobile tests with synthetic named matches, NO real API."""
import json,os,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from sabah_batch_263 import run,save_new,sha,Blocked
from sabah_mobile_screens_263 import build
from sabah_new100_commit_guard_263 import verify,PilotBlocked
from test_sabah_acceptance3_263 import fake_predict,gate,baseline,decide,TEAMS,NOW,KO

class New100Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=os.getcwd()
        os.chdir(self.tmp.name)
        Path("experiments/263").mkdir(parents=True)
        self.manifest=Path("experiments/263/user_named_request.json")
        self.manifest.write_text(json.dumps({
            "schema":"SABAH_TOPLU_V1","day_turkey":"2026-11-07",
            "matches":[{"league":l,"home":h,"away":a} for l,h,a in TEAMS]}),encoding="utf-8")
        for path in ("history.csv","baseline.csv","approval.json","m4.json","dev.json"):
            Path(path).write_text("{}",encoding="utf-8")
    def tearDown(self):os.chdir(self.old);self.tmp.cleanup()
    def batch(self,**overrides):
        args={"cohort":"new100","day":"2026-11-07","src":self.manifest,
              "history":"history.csv","baseline":"baseline.csv",
              "acceptance":"approval.json","lock_path":"m4.json",
              "now":NOW,"lookup":gate,"predictor":fake_predict,
              "baseline_fn":baseline,"decision_fn":decide,
              "dev_lock_path":"dev.json"}
        args.update(overrides)
        return run(**args)
    def bundle(self):
        r=self.batch()
        rep=Path("experiments/263/sabah_batch_reports/test.json")
        save_new(rep,r)
        summary,pages=build(".",r)
        mobile=Path("experiments/263/sabah_mobile_reports/test")
        (mobile/"matches").mkdir(parents=True)
        (mobile/"summary.md").write_text(summary,encoding="utf-8")
        for stem,txt in pages.items():
            (mobile/"matches"/(stem+".md")).write_text(txt,encoding="utf-8")
        return r,rep,mobile
    def test_3_realistic_mocks_new100_seal_mobile(self):
        r,rep,mobile=self.bundle()
        receipt=verify(rep,mobile,now=NOW+timedelta(minutes=1))
        self.assertEqual(receipt["new_count"],3)
        self.assertEqual([x["available_models"] for x in receipt["records"]],[4,3,4])
        self.assertEqual(receipt["bookmaker_api_calls"],0)
        self.assertFalse(Path("forward_quad_263").exists())
        self.assertFalse(Path("forward_acceptance_263").exists())
    def test_no_mobile_mutation(self):
        r,rep,mobile=self.bundle()
        (mobile/"summary.md").write_text("unproven sure-win forecast",encoding="utf-8")
        with self.assertRaises(PilotBlocked):verify(rep,mobile,now=NOW)
    def test_no_mobile_single_removal(self):
        r,rep,mobile=self.bundle()
        next((mobile/"matches").glob("*.md")).unlink()
        with self.assertRaises(PilotBlocked):verify(rep,mobile,now=NOW)
    def test_cannot_commit_after_ko(self):
        r,rep,mobile=self.bundle()
        with self.assertRaises((PilotBlocked,Blocked)):verify(rep,mobile,now=KO)
    def test_missing_decision_research_gated_and_rollback(self):
        def fail(*args,**kwargs):raise ValueError("synthetic unavailable")
        r=self.batch(decision_fn=fail)
        self.assertEqual(r["new_forecasts"],0)
        self.assertEqual(r["blocked"],3)
        self.assertFalse(list(Path("forward_morning_263").glob("*/*.json")))
    def test_m4_missing_blocks_unready_match_without_imputation(self):
        def p(*args,**kwargs):
            path,f=fake_predict(*args,**kwargs)
            if f["fixture"]["league"]=="TUR1":
                f["model_predictions"]["M4"]={"status":"UNAVAILABLE_FIT_OR_RANGE"}
                f["payload_sha256"]=sha({k:v for k,v in f.items() if k!="payload_sha256"})
                Path(path).write_text(json.dumps(f),encoding="utf-8")
            return path,f
        r=self.batch(predictor=p)
        self.assertEqual(r["new_forecasts"],2)
        self.assertEqual(r["blocked"],1)
        self.assertFalse(list(Path("forward_morning_263/2026-11-07").glob("5b643*.json")))
    def test_acceptance3_same_fixture_does_not_become_new100(self):
        old=run("acceptance3","2026-11-07",self.manifest,
                "history.csv","baseline.csv","approval.json","m4.json",
                now=NOW,lookup=gate,predictor=fake_predict,
                baseline_fn=baseline,decision_fn=decide,dev_lock_path="dev.json")
        self.assertEqual(old["new_forecasts"],3)
        r=self.batch()
        self.assertEqual(r["new_forecasts"],0)
        self.assertEqual(r["blocked"],3)
        self.assertEqual(r["already_sealed"],0)
        self.assertTrue(all("FIXTURE_SEALED_IN_OTHER_COHORT" in x.get("reason","") for x in r["outcomes"]))
        self.assertFalse(list(Path("forward_morning_263").glob("*/*.json")))
    def test_same_cohort_existing_is_read_only(self):
        r=self.batch()
        again=self.batch()
        self.assertEqual(again["new_forecasts"],0)
        self.assertEqual(again["already_sealed"],3)
    def test_garbage_forecast_receipt_rejected(self):
        r,rep,mobile=self.bundle()
        raw=json.loads(rep.read_text())
        raw["cohort"]="legacy96"
        rep.write_text(json.dumps(raw),encoding="utf-8")
        with self.assertRaises(PilotBlocked):verify(rep,mobile,now=NOW)
    def test_no_unverified_bets_from_decision(self):
        r,rep,mobile=self.bundle()
        p=Path("experiments/263/sabah_research/new100/2026-11-07")/Path(r["outcomes"][0]["forecast_path"]).stem/"decision.json"
        obj=json.loads(p.read_text(encoding="utf-8"));obj["main_candidate"]={"market":"MS1"}
        obj["payload_sha256"]=sha({k:v for k,v in obj.items() if k!="payload_sha256"})
        p.write_text(json.dumps(obj),encoding="utf-8")
        with self.assertRaises((PilotBlocked,ValueError)):verify(rep,mobile,now=NOW)
    def test_101_names_cannot_enter_new100(self):
        rows=[{"league":"ESP1","home":"Home "+str(i),"away":"Away "+str(i)} for i in range(101)]
        self.manifest.write_text(json.dumps({"schema":"SABAH_TOPLU_V1",
             "day_turkey":"2026-11-07","matches":rows}),encoding="utf-8")
        with self.assertRaises(Blocked):self.batch()
if __name__=="__main__":unittest.main()
