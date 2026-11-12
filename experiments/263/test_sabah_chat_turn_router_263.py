"""One user chat command -> safe candidate manifest; never create a pilot here.

Source preflight is synthetic; the real official named-match gate still runs
inside the existing SHA new100 GitHub workflow, not in this test.
"""
import copy,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path

from sabah_10league_manifest_preflight_263 import inspect
from test_sabah_10league_manifest_preflight_263 import Fake,NOW,DAY
from sabah_chat_turn_router_263 import plan,from_repo,_identity
from sabah_manual_preflight_bridge_263 import review,BridgeBlocked

ROOT=Path(__file__).resolve().parents[2]
AT=NOW+timedelta(minutes=2)

class ChatMorningRoute(unittest.TestCase):
 def setUp(self):
  self.raw=inspect(DAY,gateway=Fake(),now=NOW)
 def route(self,**kwargs):
  return plan(self.raw,"Bugünün maçlarını getir",now=AT,seen=set(),used_count=40,**kwargs)
 def test_one_user_command_all_verified_candidates_exact_named_schema(self):
  p=self.route()
  self.assertEqual(p["status"],"SAFE_NAMED_REQUEST_READY_NOT_DISPATCHED")
  self.assertEqual(p["request"]["schema"],"SABAH_TOPLU_V1")
  self.assertEqual(p["request"]["day_turkey"],DAY)
  self.assertEqual(len(p["request"]["matches"]),2)
  self.assertEqual(set(p["request"]),{"schema","day_turkey","matches"})
  self.assertEqual((p["bookmaker_api_calls"],p["new_forecasts_written"]),(0,0))
  self.assertFalse(p["git_request_committed"])
  self.assertFalse(p["workflow_started"])
 def test_command_not_general_chit_chat_or_automation(self):
  for msg in ("Devam ortak","Haftasonu hepsini kendin oyna","",None):
   with self.subTest(msg=msg):
    with self.assertRaisesRegex(BridgeBlocked,"EXPLICIT_TODAY_ANALYSIS"):
     plan(self.raw,msg,now=AT,seen=set(),used_count=40)
 def test_common_chat_variant_authorizes_identical_set(self):
  a=self.route()["request"]
  b=plan(self.raw,"Bugünün maçlarını analiz et ortak!",now=AT,seen=set(),used_count=40)["request"]
  self.assertEqual(a,b)
 def test_existing_sealed_game_not_requested_again(self):
  preview=review(self.raw,now=AT)
  seen={_identity(preview["candidates"][0])}
  p=plan(self.raw,"Bugünün maçlarını getir",now=AT,seen=seen,used_count=40)
  self.assertEqual(p["previously_sealed_count"],1)
  self.assertEqual(p["fresh_unsealed_eligible_count"],1)
  self.assertEqual(len(p["request"]["matches"]),1)
 def test_neither_fresh_candidate_leads_to_no_request(self):
  preview=review(self.raw,now=AT)
  seen={_identity(r) for r in preview["candidates"]}
  p=plan(self.raw,"Bugünün maçlarını getir",now=AT,seen=seen,used_count=40)
  self.assertEqual(p["status"],"NO_NEW_SAFE_OFFICIAL_FIXTURE_NO_REQUEST")
  self.assertIsNone(p["request"])
 def test_never_silent_drop_when_current_new100_capacity_too_small(self):
  p=plan(self.raw,"Bugünün maçlarını getir",now=AT,seen=set(),used_count=99)
  self.assertEqual(p["status"],"INSUFFICIENT_EXISTING_NEW100_CAPACITY_NO_REQUEST")
  self.assertEqual(p["fresh_unsealed_eligible_count"],2)
  self.assertIsNone(p["request"])
 def test_user_does_not_get_new_pilot_after_existing_100_cap(self):
  p=plan(self.raw,"Bugünün maçlarını getir",now=AT,seen=set(),used_count=100)
  self.assertEqual(p["remaining_new100_capacity"],0)
  self.assertEqual(p["status"],"INSUFFICIENT_EXISTING_NEW100_CAPACITY_NO_REQUEST")
 def test_20_minute_git_margin_with_same_day_candidates(self):
  raw=copy.deepcopy(self.raw)
  raw["candidates"][0]["kickoff_utc"]=(AT+timedelta(minutes=10)).isoformat()
  p=plan(raw,"Bugünün maçlarını getir",now=AT,seen=set(),used_count=40)
  self.assertEqual(p["too_close_for_safe_prematch_git_count"],1)
  self.assertEqual(len(p["request"]["matches"]),1)
 def test_preflight_stale_wrong_day_and_untrusted_count_rejected(self):
  with self.assertRaisesRegex(BridgeBlocked,"OLDER_THAN_10MIN"):
   plan(self.raw,"Bugünün maçlarını getir",now=NOW+timedelta(minutes=11),
        seen=set(),used_count=40)
  raw=copy.deepcopy(self.raw);raw["day_turkey"]="2026-11-07"
  with self.assertRaisesRegex(BridgeBlocked,"NOT_SAME_TURKEY_DAY"):
   plan(raw,"Bugünün maçlarını getir",now=AT,seen=set(),used_count=40)
  with self.assertRaisesRegex(BridgeBlocked,"INVALID_NEW100_CAPACITY"):
   plan(self.raw,"Bugünün maçlarını getir",now=AT,seen=set(),used_count=101)
 def test_no_zero_fixture_assertion_from_partial_league_sources(self):
  p=self.route()
  self.assertFalse(p["league_coverage_complete"])
  self.assertIn("ENG2", {r["league"] for r in p["unresolved_source_leagues"]})
  self.assertTrue(p["candidate_list_not_live_named_gate"])
 def test_actual_registered_nov8_seals_stay_immutable_no_new_files(self):
  # Real 40 immutable Nov8 new100 forecasts, not mock counts.
  before={p:p.stat().st_size for p in (ROOT/"forward_morning_263").glob("*/*.json")}
  x=from_repo(ROOT,self.raw,"Bugünün maçlarını getir",now=AT)
  after={p:p.stat().st_size for p in (ROOT/"forward_morning_263").glob("*/*.json")}
  self.assertEqual(before,after)
  self.assertEqual(len(before),40)
  self.assertEqual(x["remaining_new100_capacity"],60)
  self.assertEqual(x["new_forecasts_written"],0)
  self.assertEqual(x["bookmaker_api_calls"],0)
 def test_github_preflight_receipt_is_not_a_user_request_or_pilot(self):
  text=(ROOT/".github/workflows/263-sabah-10lig-fixture-preflight.yml").read_text()
  self.assertIn("SAME_DAY_CHAT_PREFLIGHT_RECEIPT_VERIFIED_NO_NEW100_TRIGGER",text)
  self.assertIn('if: github.event_name == \'push\'',text)
  self.assertIn('git diff --cached',text)
  self.assertNotIn("git add -- experiments/263/sabah_requests",text)
  self.assertNotIn("git add -- forward_morning_263",text)

if __name__=="__main__":unittest.main()
