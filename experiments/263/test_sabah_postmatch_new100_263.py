"""Synthetic outcomes: prove scoring NEVER invents source verification or rewrites pilot."""
import copy,hashlib,json,os,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from sabah_postmatch_new100_263 import (
    evaluate,mobile,checked_score,scores_for,ScoreBlocked,SCHEMA)
from sabah_batch_263 import sha

KO="2026-11-08T16:00:00+00:00"
MADE="2026-11-08T12:00:00+00:00"
CHECKED="2026-11-08T12:00:00+00:00"
RESULT_CHECKED="2026-11-08T18:10:00+00:00"
RESULT_REVIEWED="2026-11-08T18:15:00+00:00"
NOW=datetime(2026,11,10,13,0,tzinfo=timezone.utc)
MARKETS={"1X2":{"H":.62,"D":.23,"A":.15},"BTTS_YES":.55,
         "OVER_1.5":.75,"OVER_2.5":.60,"OVER_3.5":.30}
def sealed_forecast(home="HOME_ID_A",away="AWAY_ID_A",missing=None):
    models={m:{"status":"AVAILABLE","goals":{"markets":copy.deepcopy(MARKETS)}}
            for m in ("B","C2","C3","M4")}
    if missing:models[missing]={"status":"UNAVAILABLE_INSUFFICIENT_CONTEXT"}
    body={"schema":"quad_forward_263_v1","created_at_utc":MADE,
          "fixture":{"league":"ESP1","home_id":home,"away_id":away,
                     "kickoff_utc":KO,"match_local_date":"2026-11-08",
                     "source_checked_at_utc":CHECKED,
                     "fixture_verification":"VERIFIED_BY_LIVE_OFFICIAL_GATE"},
          "model_predictions":models}
    body["payload_sha256"]=sha(body)
    return body
def official_result(f,score=(2,1)):
    x={"schema":SCHEMA,"cohort":"new100",
       "forecast_sha256":f["payload_sha256"],
       "league":"ESP1","home_id":f["fixture"]["home_id"],
       "away_id":f["fixture"]["away_id"],"kickoff_utc":KO,
       "home_goals":score[0],"away_goals":score[1],
       "final_status":"FULL_TIME_HUMAN_REVIEWED",
       "source_url":"https://www.laliga.com/laliga-easports/resultados",
       "source_checked_at_utc":RESULT_CHECKED,
       "reviewed_at_utc":RESULT_REVIEWED,"reviewer":"Synthetic reviewer",
       "verification_scope":"HUMAN_ATTESTED_OFFICIAL_PAGE_NOT_NETWORK_REVERIFIED"}
    return x

class New100PostmatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.records=self.root/"forward_morning_263/2026-11-08"
        self.records.mkdir(parents=True)
        self.inputs=self.root/"experiments/263/sabah_postmatch_inputs/2026-11-08"
        self.inputs.mkdir(parents=True)
    def forecast(self,home="HOME_ID_A",away="AWAY_ID_A",missing=None,stem="a"*24):
        f=sealed_forecast(home,away,missing)
        p=self.records/(stem+".json")
        p.write_text(json.dumps(f),encoding="utf-8")
        return f,p
    def result(self,f,goals=(2,1),stem="result"):
        r=official_result(f,goals)
        p=self.inputs/(stem+".json")
        p.write_text(json.dumps(r),encoding="utf-8")
        return r,p
    def eval(self,**kwargs):
        return evaluate(self.root,now=kwargs.pop("now",NOW),**kwargs)
    def test_empty_pilot_is_zero_results_not_fake_100(self):
        out=self.eval()
        self.assertEqual(out["registered"],0)
        self.assertEqual(out["human_attested_official_result_count"],0)
        self.assertEqual(out["per_model_MS"]["M4"]["n"],0)
        self.assertIsNone(out["per_model_MS"]["M4"]["top1_accuracy_pct"])
        self.assertIn("0/100",mobile(out))
    def test_two_realistic_sealed_results_MS_KG_three_overlines(self):
        fa,_=self.forecast()
        self.result(fa,(2,1))
        fb,_=self.forecast("HOME_ID_B","AWAY_ID_B",missing="B",stem="b"*24)
        self.result(fb,(0,1),stem="next")
        out=self.eval()
        self.assertEqual(out["registered"],2)
        self.assertEqual(out["human_attested_official_result_count"],2)
        self.assertEqual(out["independently_network_verified_result_count"],0)
        self.assertEqual(out["per_model_MS"]["B"]["n"],1)
        self.assertEqual(out["per_model_MS"]["M4"]["n"],2)
        self.assertEqual(out["four_model_common_n"],1)
        first=next(r for r in out["outcomes"] if r["forecast_sha256"]==fa["payload_sha256"])
        self.assertEqual({m:first["market_scores"]["M4"][m]["y"] for m in
                         ("BTTS","OVER_1.5","OVER_2.5","OVER_3.5")},
                         {"BTTS":1,"OVER_1.5":1,"OVER_2.5":1,"OVER_3.5":0})
        self.assertAlmostEqual(first["model_scores"]["M4"]["brier"],(.62-1)**2+.23**2+.15**2)
        self.assertEqual(out["same_match_M4_comparisons"]["B_minus_M4"]["n"],1)
        self.assertTrue(all(x["schema"]=="quad_forward_263_v1" for x in (fa,fb)))
    def test_existing_prematch_microsecond_clock_order_is_accepted(self):
        f,p=self.forecast()
        f["fixture"]["source_checked_at_utc"]="2026-11-08T12:00:00.000018+00:00"
        f["payload_sha256"]=sha({k:v for k,v in f.items() if k!="payload_sha256"})
        p.write_text(json.dumps(f),encoding="utf-8")
        self.result(f)
        self.assertEqual(self.eval()["human_attested_official_result_count"],1)

    def test_source_check_beyond_small_drift_or_postkickoff_is_rejected(self):
        f,p=self.forecast()
        for stamp in ("2026-11-08T12:01:00.000001+00:00",KO):
            f["fixture"]["source_checked_at_utc"]=stamp
            f["payload_sha256"]=sha({k:v for k,v in f.items() if k!="payload_sha256"})
            p.write_text(json.dumps(f),encoding="utf-8")
            r,rp=self.result(f)
            with self.assertRaises(ScoreBlocked):self.eval()

    def test_forecast_bytes_immutable_after_evaluation(self):
        f,path=self.forecast();self.result(f)
        raw=path.read_bytes();self.eval()
        self.assertEqual(raw,path.read_bytes())
    def test_missing_official_result_remains_pending(self):
        f,_=self.forecast()
        out=self.eval()
        self.assertEqual(out["human_attested_official_result_count"],0)
        self.assertEqual(len(out["pending"]),1)
        self.assertEqual(out["pending"][0]["forecast_sha256"],f["payload_sha256"])
    def test_result_from_96_or_acceptance3_refused(self):
        f=sealed_forecast()
        self.result(f)
        with self.assertRaises(ScoreBlocked):self.eval()
    def test_same_result_twice_blocks(self):
        f,_=self.forecast();self.result(f)
        self.result(f,stem="second")
        with self.assertRaises(ScoreBlocked):self.eval()
    def test_wrong_team_pair_and_kickoff_blocks(self):
        f,_=self.forecast();r,p=self.result(f)
        r["away_id"]="OTHER_ID";p.write_text(json.dumps(r))
        with self.assertRaises(ScoreBlocked):self.eval()
        r["away_id"]=f["fixture"]["away_id"]
        r["kickoff_utc"]="2026-11-08T17:00:00+00:00";p.write_text(json.dumps(r))
        with self.assertRaises(ScoreBlocked):self.eval()
    def test_modified_forecast_sha_rejected(self):
        f,p=self.forecast();self.result(f)
        x=json.loads(p.read_text());x["model_predictions"]["M4"]["status"]="UNAVAILABLE"
        p.write_text(json.dumps(x))
        with self.assertRaises(ValueError):self.eval()
    def test_fake_unofficial_url_rejected(self):
        f,_=self.forecast();r,p=self.result(f)
        r["source_url"]="https://www.laliga.com.evil.example/fake"
        p.write_text(json.dumps(r))
        with self.assertRaises(ScoreBlocked):self.eval()
    def test_full_time_cannot_be_attested_before_90_minutes(self):
        f,_=self.forecast();r,p=self.result(f)
        r["source_checked_at_utc"]="2026-11-08T17:00:00+00:00"
        p.write_text(json.dumps(r))
        with self.assertRaises(ScoreBlocked):self.eval()
    def test_unreviewed_result_is_not_verified(self):
        f,_=self.forecast();r,p=self.result(f)
        r["final_status"]="FULL_TIME_AUTOMATED_GUESS"
        p.write_text(json.dumps(r))
        with self.assertRaises(ScoreBlocked):self.eval()
    def test_no_future_attestation(self):
        f,_=self.forecast();self.result(f)
        with self.assertRaises(ScoreBlocked):
            self.eval(now=datetime(2026,11,8,17,0,tzinfo=timezone.utc))
    def test_false_goals_bool_or_negative_rejected(self):
        f,_=self.forecast();r,p=self.result(f)
        r["home_goals"]=True;p.write_text(json.dumps(r))
        with self.assertRaises(ScoreBlocked):self.eval()
        r["home_goals"]=-1;p.write_text(json.dumps(r))
        with self.assertRaises(ScoreBlocked):self.eval()
    def test_calibrated_markets_scored_as_separate_binary_diagnostics(self):
        f,p=self.forecast();self.result(f)
        stem=p.stem
        folder=self.root/"experiments/263/sabah_research/new100/2026-11-08"/stem
        folder.mkdir(parents=True)
        d={"schema":"263_four_model_value_decision_research_v1",
           "forecast_sha256":f["payload_sha256"],"status":"RESEARCH_PAS",
           "betting_authorized":False,
           "all_market_diagnostics":[
               {"market":"MS1","calibrated_probability":.58,"anchor_model":"C3",
                "dev_brier_skill":.12,"support_count":4},
               {"market":"OVER_2.5","calibrated_probability":.65,"anchor_model":"M4",
                "dev_brier_skill":.03,"support_count":3},
               {"market":"MSX","calibrated_probability":None,"anchor_model":None,
                "support_count":0,"dev_brier_skill":None}]}
        d["payload_sha256"]=sha(d)
        (folder/"decision.json").write_text(json.dumps(d))
        out=self.eval()
        self.assertEqual(out["calibrated_DEV_diagnostics"]["MS1"]["n"],1)
        self.assertEqual(out["calibrated_DEV_diagnostics"]["OVER_2.5"]["n"],1)
        self.assertEqual(out["calibrated_DEV_diagnostics"]["MSX"]["n"],0)
    def test_wrong_decision_forecast_sha_fails(self):
        f,p=self.forecast();self.result(f)
        folder=self.root/"experiments/263/sabah_research/new100/2026-11-08"/p.stem
        folder.mkdir(parents=True)
        d={"schema":"263_four_model_value_decision_research_v1","status":"RESEARCH_PAS",
           "betting_authorized":False,"forecast_sha256":"0"*64,
           "all_market_diagnostics":[]}
        d["payload_sha256"]=sha(d);(folder/"decision.json").write_text(json.dumps(d))
        with self.assertRaises(ScoreBlocked):self.eval()
if __name__=="__main__":unittest.main()
