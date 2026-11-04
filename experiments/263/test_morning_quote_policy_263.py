"""Synthetic morning snapshot and T-60 1.90 -> 1.60 fallback contract."""
import json,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from test_four_model_value_policy_263 import fixture,odds,seal
from four_model_value_policy_263 import decide
from morning_quote_policy_263 import REQUEST,record_request,extract,identity,conditional,read_for_forecast,verify_conditional_precommit
NOW=datetime(2026,11,6,16,3,tzinfo=timezone.utc)
AM=datetime(2026,11,6,7,0,tzinfo=timezone.utc)
class MorningOddsAcceptance(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
    self.root=Path(self.tmp.name);self.f,self.b,self.lock=fixture()
    fx=self.f["fixture"]
    self.fx={k:fx[k] for k in ("league","home_id","away_id","match_local_date","kickoff_utc")}
    self.fx["official_fixture_url"]=fx.get("official_source","https://www.tff.org/synthetic-fixture")
    self.relative="experiments/263/morning_quote_requests/SYNTH.json"
    self.path=self.root/self.relative;self.path.parent.mkdir(parents=True)
    self.source={"schema":REQUEST,"fixture":self.fx,"source_domain":"nesine.com",
       "source_url":"https://www.nesine.com/synthetic-not-real",
       "reviewer":"SYNTHETIC_TESTER","reviewed_at_utc":"2026-11-06T06:59:00+00:00",
       "observed_at_utc":"2026-11-06T06:59:30+00:00",
       "visible_source_note":"SYNTHETIC TEST BOOKMAKER SNAPSHOT",
       "market_prices":{"MS":{"MS1":1.9,"MSX":3.65,"MS2":4.7},
         "GOALS_3.5":{"OVER_3.5":2.45,"UNDER_3.5":1.65}}}
    self.path.write_text(json.dumps(self.source))
 def snap(self):
    r=record_request(self.relative,self.root,self.root/"morning",AM)
    return json.loads(Path(r["path"]).read_text())
 def test_morning_is_sha_archived_not_current(self):
    s=self.snap()
    self.assertTrue(s["not_current_at_T60"])
    self.assertFalse(s["auto_scraped"])
    self.assertEqual(extract(s,self.f,NOW)["MS1"]["odds"],1.9)
 def test_morning_price_190_generates_conditional_candidate(self):
    d=decide(self.f,self.b,self.lock,morning_snapshot=self.snap(),now=NOW)
    self.assertEqual(d["status"],"RESEARCH_CONDITIONAL_MORNING_PRICE_NOT_CURRENT")
    self.assertEqual(d["main_candidate"]["market"],"MS1")
    self.assertEqual(d["main_candidate"]["price_age_class"],"MORNING_ARCHIVE_NOT_CURRENT")
    self.assertFalse(d["betting_authorized"])
 def test_new_price_160_always_replaces_190(self):
    m=self.snap();latest=odds(self.f,groups={"MS":{"MS1":1.60,"MSX":4.20,"MS2":5.80}})
    d=decide(self.f,self.b,self.lock,latest,morning_snapshot=m,now=NOW)
    row=next(x for x in d["all_market_diagnostics"] if x["market"]=="MS1")
    self.assertEqual(row["observed_odds"],1.60)
    self.assertEqual(row["price_age_class"],"CURRENT_T60")
    old=decide(self.f,self.b,self.lock,morning_snapshot=m,now=NOW)
    old_row=next(x for x in old["all_market_diagnostics"] if x["market"]=="MS1")
    # Whether 1.60 is still +EV depends on calibration; lower price must LOWER EV.
    self.assertLess(row["EV"],old_row["EV"])
    self.assertEqual(row["calibrated_probability"],old_row["calibrated_probability"])
 def test_new_other_group_keeps_old_market(self):
    m=self.snap();fresh=odds(self.f,groups={"KG":{"BTTS_YES":1.94,"BTTS_NO":1.88}})
    d=decide(self.f,self.b,self.lock,fresh,morning_snapshot=m,now=NOW)
    self.assertEqual(next(x for x in d["all_market_diagnostics"] if x["market"]=="MS1")["price_age_class"],"MORNING_ARCHIVE_NOT_CURRENT")
    self.assertEqual(next(x for x in d["all_market_diagnostics"] if x["market"]=="BTTS_YES")["price_age_class"],"CURRENT_T60")
 def test_tampered_morning_blocked(self):
    s=self.snap();s["quotes"]["MS"]["decimal_odds"]["MS1"]=4.0
    with self.assertRaisesRegex(ValueError,"TAMPERED"):extract(s,self.f,NOW)
 def test_wrong_kickoff_blocked(self):
    s=self.snap();s["fixture"]["kickoff_utc"]="2026-11-06T19:00:00+00:00";seal(s)
    with self.assertRaisesRegex(ValueError,"MORNING_WRONG_KICKOFF"):extract(s,self.f,NOW)
 def test_replay_duplicate_blocked(self):
    self.snap()
    with self.assertRaises(FileExistsError):self.snap()
 def test_no_price_pas(self):
    self.assertEqual(decide(self.f,self.b,self.lock,now=NOW)["status"],"RESEARCH_PAS")
 def prepare_forward_join(self,*,with_morning=True,create_conditional=True):
    snap=self.snap() if with_morning else None
    stem=identity(self.fx)
    fp=self.root/"forward_quad_263/2026-11-06"/(stem+".json")
    fp.parent.mkdir(parents=True);fp.write_text(json.dumps(self.f))
    bp=self.root/"experiments/263/quad_research_links/2026-11-06"/stem/"baseline.json"
    bp.parent.mkdir(parents=True);bp.write_text(json.dumps(self.b))
    mp=self.root/"experiments/263/morning_quotes_locked/2026-11-06"/(stem+".json")
    if with_morning:
        mp.parent.mkdir(parents=True);mp.write_text(json.dumps(snap))
    lp=self.root/"lock.json";lp.write_text(json.dumps(self.lock))
    rp=self.root/"batch.json";rp.write_text(json.dumps({"schema":"quad_named_match_batch_report_v1",
      "outcomes":[{"status":"REGISTERED_FOUR_MODELS_EXPERIMENTAL",
       "path":"forward_quad_263/2026-11-06/"+stem+".json",
       "payload_sha256":self.f["payload_sha256"]}]}))
    out=conditional(rp,lp,self.root,NOW) if create_conditional else []
    return fp,mp,rp,stem,out

 def test_real_shaped_quad_record_joins_without_rewriting(self):
    fp,mp,rp,stem,items=self.prepare_forward_join()
    self.assertEqual(items[0]["status"],"RESEARCH_CONDITIONAL_MORNING_PRICE_NOT_CURRENT")
    original=fp.read_bytes()
    self.assertEqual(verify_conditional_precommit(rp,self.root,NOW),1)
    self.assertEqual(fp.read_bytes(),original)
    self.assertEqual(read_for_forecast(self.f,self.root/"experiments/263/morning_quotes_locked")["payload_sha256"],
                     json.loads(mp.read_text())["payload_sha256"])

 def test_precommit_missing_required_conditional_blocks(self):
    _,_,rp,_,_=self.prepare_forward_join(create_conditional=False)
    with self.assertRaisesRegex(ValueError,"CONDITIONAL_RECORD_MISSING"):
        verify_conditional_precommit(rp,self.root,NOW)

 def test_precommit_revised_original_morning_request_blocks(self):
    _,_,rp,_,_=self.prepare_forward_join()
    self.path.write_text(json.dumps({"schema":"MUTATED_SOURCE"}))
    with self.assertRaisesRegex(ValueError,"ORIGINAL_REQUEST_REVISED"):
        verify_conditional_precommit(rp,self.root,NOW)

 def test_precommit_tampered_quote_or_decision_blocks(self):
    _,mp,rp,stem,_=self.prepare_forward_join()
    record=json.loads(mp.read_text())
    record["quotes"]["MS"]["decimal_odds"]["MS1"]=2.7
    mp.write_text(json.dumps(record))
    with self.assertRaisesRegex(ValueError,"TAMPERED"):
        verify_conditional_precommit(rp,self.root,NOW)

 def test_precommit_after_kickoff_blocks(self):
    _,_,rp,_,_=self.prepare_forward_join()
    with self.assertRaisesRegex(ValueError,"AFTER_KICKOFF"):
        verify_conditional_precommit(rp,self.root,datetime(2026,11,6,17,0,tzinfo=timezone.utc))

 def test_precommit_without_any_morning_archive_is_allowed(self):
    _,_,rp,_,items=self.prepare_forward_join(with_morning=False,create_conditional=False)
    self.assertEqual(items,[])
    self.assertEqual(verify_conditional_precommit(rp,self.root,NOW),0)

 def test_precommit_workflow_gate_is_after_rebase_and_before_push(self):
    wf=Path(".github/workflows/263-quad-forward-on-request.yml").read_text(encoding="utf-8")
    rebased=wf.rindex('git pull --rebase origin "$GITHUB_REF_NAME"')
    verification=wf.rindex('morning_quote_policy_263.py verify-conditional')
    push=wf.rindex('git push origin "HEAD:$GITHUB_REF_NAME"')
    self.assertLess(rebased,verification)
    self.assertLess(verification,push)

if __name__=="__main__":unittest.main()
