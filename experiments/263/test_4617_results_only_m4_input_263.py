"""4617 pre-match research input acceptance: real SHAs, mathematical smoke, no live fixture.

Fake fixture gates are used ONLY in an isolated temporary directory to test
the existing four-model code; no fake fixtures are ever committed or announced.
"""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp_263_batch import clean_rows
from forward_quad import predict_quad_from_verified_gate, verify_snapshot
from forward_empirical_baseline_263 import produce
from four_model_value_policy_263 import decide
from m4_integrated import fit_m4, predict_m4, Settings
from verify_completed99_results_archive import build

ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/"data/quad_accepted_263/extended_history.csv"
NEW=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
PROVENANCE=ROOT/"data/results_only_263/4617_research_input_provenance.json"
BASE=ROOT/"m4_quad_base/historical_results.csv"
M4LOCK=ROOT/"experiments/263/m4_lock.json"
DEVLOCK=ROOT/"experiments/263/forward_dev_calibration_lock_263.json"
RESEARCH_GRADE="APPEND_ONLY_4617_PUBLIC_RESULTS_ONLY_RESEARCH_NOT_OFFICIAL_ID_VERIFIED"

class Active4617Input(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=clean_rows(OLD)
        cls.new=clean_rows(NEW)
        cls.original_ids=set(x["fixture_id"] for x in cls.old)
        cls.cutoff=datetime(2026,11,11,9,0,0,tzinfo=timezone.utc)
        if not BASE.is_file():
            raise RuntimeError("PINNED_4413_BASELINE_NOT_DOWNLOADED_IN_ISOLATED_CI")

    def test_archive_real_sha_originals_and_99_goals_only(self):
        self.assertEqual(len(self.old),4518)
        self.assertEqual(len(self.new),4617)
        audit=build()
        self.assertEqual(audit["new_result_records"],99)
        self.assertEqual(audit["old_ENG2_changed_stage_rows_ignored"],9)
        self.assertEqual(audit["new_99_advanced_fields_admitted"],0)
        self.assertFalse(audit["base_accepted_csv_modified"])
        for x in self.new:
            if x["fixture_id"] not in self.original_ids:
                self.assertFalse(x["home_corners"])
                self.assertFalse(x["home_shots"])

    def test_m4_active_source_explicitly_downgrades_verification_grade(self):
        grade,sha=verify_snapshot(NEW,self.new,self.cutoff,BASE,PROVENANCE)
        self.assertEqual(grade,RESEARCH_GRADE)
        self.assertEqual(sha,"637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89")

    def test_4518_human_legacy_source_still_accepted_without_rewrite(self):
        source=ROOT/"data/quad_accepted_263/source_acceptance.json"
        self.assertEqual(verify_snapshot(OLD,self.old,self.cutoff,BASE,source)[0],
                         "APPEND_ONLY_HUMAN_SOURCE_ATTESTED_NOT_INDEPENDENTLY_RECHECKED")

    def test_falsified_manifest_blocks_promoted_history(self):
        source=json.loads(PROVENANCE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"false_research_gate.json"
            source["official_unique_match_id_verified"]=True
            p.write_text(json.dumps(source),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"results_only_4617_provenance_not_accepted_for_research"):
                verify_snapshot(NEW,self.new,self.cutoff,BASE,p)
            source["official_unique_match_id_verified"]=False
            source["source_snapshot_sha256"]="0"*64
            p.write_text(json.dumps(source),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"results_only_4617_provenance_not_accepted_for_research"):
                verify_snapshot(NEW,self.new,self.cutoff,BASE,p)

    def test_m4_train_rows_genuinely_use_new_scores_but_nothing_after_asof(self):
        opts=Settings(half_life_days=360,ridge_shared=4,ridge_venue=48)
        cutoff="2026-11-11"
        for league,n_added in (("ENG1",10),("TUR1",9)):
            old=[r for r in self.old if r["league"]==league and r["match_date"]<cutoff]
            new=[r for r in self.new if r["league"]==league and r["match_date"]<cutoff]
            self.assertEqual(len(new)-len(old),n_added)
            old_fit=fit_m4(old,league,cutoff,opts)
            new_fit=fit_m4(new,league,cutoff,opts)
            self.assertIsNotNone(old_fit)
            self.assertIsNotNone(new_fit)
            self.assertEqual(new_fit[3]-old_fit[3],n_added)
            teams=sorted({r["home_id"] for r in new})
            m=predict_m4(new_fit,teams[0],teams[1])
            self.assertIsNotNone(m)
            self.assertTrue(all(0.05<=v<=5 for v in m))
        # A future date cannot leak into an earlier as-of fit.
        self.assertTrue(all(r["match_date"]<"2026-11-07"
                            for r in self.new if r["match_date"]<"2026-11-07"))

    def test_full_4model_asof_decision_research_only_with_no_real_fixture_created(self):
        # Structural fixture test, deliberately NOT a real official game lookup.
        # The only output directory is the temporary workspace, never forward_morning_263.
        names={r["home_id"] for r in self.new if r["league"]=="ENG1"}
        home,away=sorted(names)[:2]
        now=self.cutoff
        gate={"status":"VERIFIED","league":"ENG1","home_id":home,"away_id":away,
              "kickoff_utc":"2026-11-11T17:00:00+00:00",
              "retrieved_at_utc":now.isoformat(),
              "source_url":"https://www.premierleague.com/en/fixtures"}
        with tempfile.TemporaryDirectory() as d:
            path,forecast=predict_quad_from_verified_gate(
               gate,NEW,Path(d),M4LOCK,now=now,base=BASE,source_audit=PROVENANCE)
            self.assertTrue(path.is_file())
            self.assertEqual(forecast["data"]["snapshot_acceptance"],RESEARCH_GRADE)
            self.assertFalse(forecast["data"]["human_source_acceptance"])
            self.assertEqual(forecast["data"]["snapshot_sha256"],
                             "637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89")
            self.assertEqual(forecast["model_predictions"]["M4"]["status"],"AVAILABLE")
            self.assertEqual(set(forecast["model_predictions"]),{"B","C2","C3","M4"})
            old_count=sum(r["league"]=="ENG1" and r["match_date"]<"2026-11-11" for r in self.old)
            self.assertEqual(forecast["model_predictions"]["M4"]["train_rows"],old_count+10)
            baseline=produce(forecast,NEW,now=now)
            lock=json.loads(DEVLOCK.read_text(encoding="utf-8"))
            decision=decide(forecast,baseline,lock,observation=None,now=now)
            self.assertEqual(decision["status"],"RESEARCH_PAS")
            self.assertFalse(decision["betting_authorized"])
            self.assertIsNone(decision["main_candidate"])
            self.assertEqual(decision["forecast_sha256"],forecast["payload_sha256"])


    def test_complete_new100_morning_mobile_receipt_mock_only_not_real_fixture(self):
        """Exercise the normal 4-model morning route with a test-only fake gate.

        The dummy 'official' gate is never submitted as a user fixture and
        its temporary predictions are deleted after this unit test.
        """
        import os
        from sabah_batch_263 import run as morning_batch, sha as sealed_hash
        from sabah_mobile_screens_263 import build as make_mobile
        from sabah_new100_commit_guard_263 import verify as verify_receipt
        now=self.cutoff
        ids=sorted({r["home_id"] for r in self.new if r["league"]=="ENG1"})
        home,away=ids[:2]
        fake_gate={"status":"VERIFIED","league":"ENG1","home_id":home,"away_id":away,
                   "kickoff_utc":"2026-11-11T17:00:00+00:00",
                   "retrieved_at_utc":now.isoformat(),
                   "source_url":"https://www.premierleague.com/en/fixtures"}
        def test_only_lookup(league,h,a):
            self.assertEqual(league,"ENG1")
            self.assertEqual(h,"Test Home")
            self.assertEqual(a,"Test Away")
            return fake_gate
        original_cwd=Path.cwd()
        with tempfile.TemporaryDirectory() as temp:
            try:
                os.chdir(temp)
                req=Path("new100_technical_mock.json")
                req.write_text(json.dumps({
                    "schema":"SABAH_TOPLU_V1","day_turkey":"2026-11-11",
                    "matches":[{"league":"ENG1","home":"Test Home","away":"Test Away"}]
                }),encoding="utf-8")
                report=morning_batch(
                    "new100","2026-11-11",req,NEW,BASE,PROVENANCE,M4LOCK,
                    root=".",now=now,lookup=test_only_lookup,
                    dev_lock_path=DEVLOCK)
                self.assertEqual(report["new_forecasts"],1,report)
                self.assertEqual(report["blocked"],0,report)
                self.assertEqual(report["outcomes"][0]["decision_status"],"RESEARCH_PAS")
                Path("experiments/263/sabah_batch_reports").mkdir(parents=True,exist_ok=True)
                rp=Path("experiments/263/sabah_batch_reports/mock_only.json")
                rp.write_text(json.dumps(report),encoding="utf-8")
                md=Path("experiments/263/sabah_mobile_reports/test_mock")
                (md/"matches").mkdir(parents=True,exist_ok=True)
                summary,singles=make_mobile(Path("."),report)
                (md/"summary.md").write_text(summary,encoding="utf-8")
                for stem,panel in singles.items():
                    (md/"matches"/(stem+".md")).write_text(panel,encoding="utf-8")
                receipt=verify_receipt(rp,md,root=".",now=now)
                self.assertEqual(receipt["new_count"],1)
                self.assertTrue(receipt["mobile_sha_equal_to_seal"])
                self.assertFalse(receipt["betting_authorized"])
            finally:
                os.chdir(original_cwd)

if __name__=="__main__":
    unittest.main()
