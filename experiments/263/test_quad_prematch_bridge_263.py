import json,tempfile,unittest,copy,hashlib
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
from test_four_model_value_policy_263 import fixture,odds,seal
from quad_prematch_bridge_263 import link_baseline,link_priced,precommit
NOW=datetime(2026,11,6,16,3,tzinfo=timezone.utc)
class TestProvenanceLink(unittest.TestCase):
 def setUp(self):
    self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)
    self.f,self.b,self.lock=fixture();self.id="a"*24
    self.path="forward_quad_263/2026-11-06/"+self.id+".json"
    self.put(self.path,self.f)
    self.lock_path=self.root/"lock.json";self.lock_path.write_text(json.dumps(self.lock))
    self.bases=self.root/"baselines";self.priced=self.root/"priced"
    self.report=self.root/"report.json"
    self.report.write_text(json.dumps({"schema":"quad_named_match_batch_report_v1",
        "outcomes":[{"status":"REGISTERED_FOUR_MODELS_EXPERIMENTAL","path":self.path,
                     "payload_sha256":self.f["payload_sha256"]}]}))
 def put(self,rel,obj):
    p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj));return p
 def base(self):
    with patch("quad_prematch_bridge_263.produce",return_value=self.b):
        return link_baseline(self.report,"fake-history",self.lock_path,self.root,self.bases,NOW)
 def quote(self):
    request="experiments/263/market_quote_requests/test.json"
    rq=self.put(request,{"schema":"263_manual_market_quote_request_v1","forecast_path":self.path})
    q=odds(self.f)
    q["source_review"]["request_path"]=request
    q["source_review"]["request_file_sha256"]=hashlib.sha256(rq.read_bytes()).hexdigest()
    seal(q)
    qp="experiments/263/market_quotes_locked/2026-11-06/"+self.id+".json"
    self.put(qp,q)
    report=self.root/"quotes.json"
    report.write_text(json.dumps({"schema":"263_manual_market_quote_batch_report_v1",
        "items":[{"status":"MANUAL_ATTESTATION_SEALED_LOCALLY_AWAIT_GITHUB_PREKO_COMMIT",
                  "path":qp,"payload_sha256":q["payload_sha256"]}]}))
    return report,q
 def test_one_initial_forecast_requires_baseline_and_no_odds_pas(self):
    self.assertEqual(len(self.base()),1)
    d=json.loads((self.bases/"2026-11-06"/self.id/"preprice_decision.json").read_text())
    self.assertEqual(d["status"],"RESEARCH_PAS")
    self.assertEqual(precommit(self.report,"baseline",self.root,self.bases,self.priced,NOW),1)
 def test_real_shaped_price_links_new_decision_without_rewriting_forecast(self):
    self.base();r,q=self.quote();original=(self.root/self.path).read_bytes()
    self.assertEqual(len(link_priced(r,self.lock_path,self.root,self.bases,self.priced,NOW)),1)
    d=json.loads((self.priced/"2026-11-06"/(self.id+".json")).read_text())
    self.assertEqual(d["main_candidate"]["market"],"MS1")
    self.assertEqual(d["alternative_candidate"]["market"],"UNDER_3.5")
    self.assertEqual(d["quote_sha256"],q["payload_sha256"])
    self.assertEqual(precommit(r,"priced",self.root,self.bases,self.priced,NOW),1)
    self.assertEqual((self.root/self.path).read_bytes(),original)
 def test_duplicates_block(self):
    self.base()
    with patch("quad_prematch_bridge_263.produce",return_value=self.b):
        with self.assertRaisesRegex(ValueError,"PRELIMINARY_ALREADY_WRITTEN"):
            link_baseline(self.report,"fake-history",self.lock_path,self.root,self.bases,NOW)
 def test_after_kickoff_blocks(self):
    with patch("quad_prematch_bridge_263.produce",return_value=self.b):
        with self.assertRaisesRegex(ValueError,"POST_KICKOFF_RECORD_FORBIDDEN"):
            link_baseline(self.report,"fake-history",self.lock_path,self.root,self.bases,
                datetime(2026,11,6,17,0,tzinfo=timezone.utc))
 def test_sha_tamper_blocks(self):
    f=copy.deepcopy(self.f);f["model_predictions"]["M4"]["goals"]["markets"]["OVER_1.5"]=.99
    self.put(self.path,f)
    with patch("quad_prematch_bridge_263.produce",return_value=self.b):
        with self.assertRaisesRegex(ValueError,"SHA_TAMPERED"):
            link_baseline(self.report,"fake-history",self.lock_path,self.root,self.bases,NOW)
 def test_price_without_forecast_baseline_blocks(self):
    r,q=self.quote()
    with self.assertRaisesRegex(ValueError,"MISSING_LOCKED_ASOF_BASELINE"):
        link_priced(r,self.lock_path,self.root,self.bases,self.priced,NOW)
 def test_report_sha_must_match(self):
    o=json.loads(self.report.read_text());o["outcomes"][0]["payload_sha256"]="0"*64
    self.report.write_text(json.dumps(o))
    with patch("quad_prematch_bridge_263.produce",return_value=self.b):
        with self.assertRaisesRegex(ValueError,"FORECAST_REPORT_SHA_MISMATCH"):
            link_baseline(self.report,"fake-history",self.lock_path,self.root,self.bases,NOW)
if __name__=="__main__":unittest.main()
