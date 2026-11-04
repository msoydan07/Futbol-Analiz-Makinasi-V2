"""Synthetic presentation acceptance for sealed four-model pilot files.
No actual fixture, bookmaker odds, model retraining or pilot booking.
"""
import json
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
from test_four_model_value_policy_263 import fixture,odds,seal
from four_model_value_policy_263 import decide
from market_fifth_baseline_263 import fixture_key
from quad_user_report_263 import generate,execute,decision

NOW=datetime(2026,11,6,16,3,tzinfo=timezone.utc)
SHA="a"*40

class UserReportAcceptance(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.report=self.root/"experiments/263/quad_batch_reports"/(SHA+".json")
        self.report.parent.mkdir(parents=True)
        self.out_dir="experiments/263/quad_human_reports"

    def morning(self,f):
        fx=f["fixture"];key=fixture_key(fx)
        sf={x:fx[x] for x in ("league","home_id","away_id","match_local_date","kickoff_utc")}
        sf["official_fixture_url"]="https://www.tff.org/test-fake"
        quote={"fixture_key":key,"market_group":"MS","verification":"INDEPENDENTLY_CHECKED",
               "stage":"PREMATCH","source":"nesine.com","source_url":"https://www.nesine.com/synthetic",
               "checked_at_utc":"2026-11-06T06:59:30+00:00",
               "decimal_odds":{"MS1":1.90,"MSX":3.65,"MS2":4.70}}
        snap={"schema":"263_morning_market_snapshot_v1","fixture":sf,"fixture_key":key,
              "observed_at_utc":"2026-11-06T06:59:30+00:00",
              "captured_at_utc":"2026-11-06T07:00:00+00:00",
              "source_domain":"nesine.com",
              "source_review":{"method":"MANUAL_PUBLIC_PAGE","reviewer":"FAKE_TESTER",
                "visible_source_note":"SYNTHETIC TEST SNAPSHOT NOT LIVE"},
              "quotes":{"MS":quote},"not_current_at_T60":True,"research_only":True,
              "auto_scraped":False,"bookmaker_page_independently_rechecked_by_code":False}
        return seal(snap)

    def entry(self,i,stage,missing=False):
        f,b,lock=fixture()
        f["fixture"].update(home_id="SYNTH_HOME_"+str(i),away_id="SYNTH_AWAY_"+str(i))
        if missing:f["model_predictions"]["M4"]={"status":"UNAVAILABLE_NO_DATA"}
        seal(f)
        b["forecast_sha256"]=f["payload_sha256"];seal(b)
        day=f["fixture"]["match_local_date"];stem="%024x"%i
        fp=self.root/"forward_quad_263"/day/(stem+".json")
        fp.parent.mkdir(parents=True,exist_ok=True)
        fp.write_text(json.dumps(f,ensure_ascii=False),encoding="utf-8")
        bp=self.root/"experiments/263/quad_research_links"/day/stem/"preprice_decision.json"
        bp.parent.mkdir(parents=True,exist_ok=True)
        unpriced=decide(f,b,lock,now=NOW)
        bp.write_text(json.dumps(unpriced,ensure_ascii=False),encoding="utf-8")
        if stage=="fresh":
            d=decide(f,b,lock,odds(f),now=NOW)
            dest=self.root/"experiments/263/quad_priced_decisions"/day/(stem+".json")
        elif stage=="morning":
            d=decide(f,b,lock,morning_snapshot=self.morning(f),now=NOW)
            dest=self.root/"experiments/263/quad_conditional_morning_decisions"/day/(stem+".json")
        else:d=None
        if d is not None:
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(json.dumps(d,ensure_ascii=False),encoding="utf-8")
        return {"status":"REGISTERED_FOUR_MODELS_EXPERIMENTAL",
                "requested":{"league":"TUR1","home":"Demo-"+str(i),"away":"Rakip-"+str(i)},
                "path":"forward_quad_263/"+day+"/"+stem+".json",
                "payload_sha256":f["payload_sha256"]},fp

    def make_batch(self,which=("fresh","none","morning","none"),missing_fourth=False):
        outcomes=[];files=[]
        for i,stage in enumerate(which,1):
            r,p=self.entry(i,stage,missing=(missing_fourth and i==4))
            outcomes.append(r);files.append(p)
        outcomes.append({"status":"BLOCKED_NO_PREDICTION",
            "requested":{"league":"TUR1","home":"Engelli-Ev","away":"Engelli-Dep"},
            "reason":"LIVE_OFFICIAL_FIXTURE_NOT_VERIFIED"})
        self.report.write_text(json.dumps({"schema":"quad_named_match_batch_report_v1",
            "outcomes":outcomes},ensure_ascii=False),encoding="utf-8")
        return files

    def test_five_match_readable_summary_and_four_details(self):
        files=self.make_batch()
        original=[p.read_bytes() for p in files]
        summary,details=generate(self.root,self.report)
        self.assertEqual(len(details),4)
        self.assertIn("İstenen: 5",summary)
        self.assertIn("Tahminli: 4",summary)
        self.assertIn("Analizi engellenen: 1",summary)
        self.assertIn("PAS",summary)
        self.assertIn("KOŞULLU",summary)
        self.assertIn("ÜRETİLEMEDİ",summary)
        for p,content in details.items():
            self.assertIn("B / C2 / C3 / M4",content)
            self.assertIn("En olası 1X2",content)
            self.assertIn("ilk 11",content.lower())
            self.assertIn("BU DÖRTLÜ KAYITLA DOĞRULANAMADI",content)
            self.assertIn("Ana tercih / alternatif / PAS",content)
        self.assertTrue(all("B / C2 / C3 / M4" in v for v in details.values()))
        self.assertEqual([p.read_bytes() for p in files],original)

    def test_complete_current_price_displays_ev_and_source_time(self):
        self.make_batch()
        _,details=generate(self.root,self.report)
        current=details["matches/2026-11-06/"+("%024x"%1)+".md"]
        self.assertIn("T−60",current)
        self.assertIn("EV",current)
        self.assertIn("nesine.com",current)
        self.assertIn("Ana tercih:",current)
        self.assertIn("B / C2 / C3 / M4",current)

    def test_no_price_keeps_probabilities_and_pas(self):
        self.make_batch()
        _,details=generate(self.root,self.report)
        no_odds=details["matches/2026-11-06/"+("%024x"%2)+".md"]
        self.assertIn("PAS analiz yok demek değildir",no_odds)
        self.assertIn("2.5 Üst",no_odds)
        self.assertIn("Oran yok",no_odds)
        self.assertNotIn("oran 1,90",no_odds)

    def test_morning_market_is_clearly_conditional(self):
        self.make_batch()
        _,details=generate(self.root,self.report)
        conditional=details["matches/2026-11-06/"+("%024x"%3)+".md"]
        self.assertIn("sabah / KOŞULLU",conditional)
        self.assertIn("KOŞULLU",conditional)
        self.assertIn("T−60'da da alınabildiği doğrulanmadı",conditional)
        self.assertNotIn("oran 1,60",conditional)

    def test_write_verify_and_readonly_originals(self):
        files=self.make_batch()
        original=[p.read_bytes() for p in files]
        self.assertEqual(execute(self.root,self.report.relative_to(self.root),self.out_dir,"write")["details"],4)
        self.assertEqual(execute(self.root,self.report.relative_to(self.root),self.out_dir,"verify")["status"],"REPORT_VERIFIED")
        with self.assertRaises(FileExistsError):
            execute(self.root,self.report.relative_to(self.root),self.out_dir,"write")
        self.assertEqual([p.read_bytes() for p in files],original)

    def test_manipulated_rendered_report_is_detected(self):
        self.make_batch()
        execute(self.root,self.report.relative_to(self.root),self.out_dir,"write")
        p=self.root/self.out_dir/SHA/"summary.md"
        p.write_text("FALSIFIED",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"USER_REPORT_FILE_MISSING_OR_CHANGED"):
            execute(self.root,self.report.relative_to(self.root),self.out_dir,"verify")

    def test_tampered_forecast_sha_rejected(self):
        files=self.make_batch()
        x=json.loads(files[0].read_text(encoding="utf-8"))
        x["model_predictions"]["B"]["goals"]["lambda_home"]=4.97
        files[0].write_text(json.dumps(x),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"SEALED_SHA_TAMPERED"):
            generate(self.root,self.report)

    def test_missing_decision_not_silently_called_pas(self):
        self.make_batch()
        p=self.root/"experiments/263/quad_research_links"/"2026-11-06"/("%024x"%2)/"preprice_decision.json"
        p.unlink()
        with self.assertRaisesRegex(ValueError,"USER_REPORT_MISSING_BASELINE_PAS"):
            generate(self.root,self.report)

    def test_unsafe_forecast_path_refused(self):
        self.make_batch()
        obj=json.loads(self.report.read_text())
        obj["outcomes"][0]["path"]="../outside.json"
        self.report.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError,"USER_REPORT_FORECAST_PATH_INVALID"):
            generate(self.root,self.report)

    def test_only_blocked_batch_still_accurate(self):
        self.report.write_text(json.dumps({"schema":"quad_named_match_batch_report_v1",
           "outcomes":[{"status":"BLOCKED_NO_PREDICTION",
                         "requested":{"league":"ENG1","home":"A","away":"B"},
                         "reason":"NO_OFFICIAL_KICKOFF"}]}))
        summary,files=generate(self.root,self.report)
        self.assertEqual(files,{})
        self.assertIn("ÜRETİLEMEDİ",summary)
        self.assertIn("Tahminli: 0",summary)


    def test_model_unavailable_is_rejected_by_original_four_model_decision(self):
        # Never bypass the existing M4 lock to create a fake three-model decision.
        with self.assertRaisesRegex(ValueError,"M4_UNAVAILABLE_NO_SILENT_FALLBACK"):
            self.entry(99,"none",missing=True)


    def test_real_forecast_workflow_writes_then_verifies_user_reports(self):
        wf=Path(".github/workflows/263-quad-forward-on-request.yml").read_text(encoding="utf-8")
        self.assertIn("quad_user_report_263.py write",wf)
        self.assertIn("quad_user_report_263.py verify",wf)
        self.assertIn("HUMAN_REPORT_OUTCOME",wf)
        self.assertIn("experiments/263/quad_human_reports/*/summary.md",wf)
        self.assertIn("experiments/263/quad_human_reports/*/matches/*/*.md",wf)
        self.assertLess(wf.index("quad_prematch_bridge_263.py baseline"),
                        wf.index("quad_user_report_263.py write"))
        self.assertLess(wf.index("quad_user_report_263.py write"),
                        wf.index("git add -A -- experiments/263/quad_human_reports"))
        self.assertLess(wf.index('git pull --rebase origin "$GITHUB_REF_NAME"'),
                        wf.index("quad_user_report_263.py verify"))
        self.assertLess(wf.index("quad_user_report_263.py verify"),
                        wf.index('git push origin "HEAD:$GITHUB_REF_NAME"'))

if __name__=="__main__":unittest.main()
