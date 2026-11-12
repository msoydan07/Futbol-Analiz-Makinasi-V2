"""Deterministic onepass acceptance + immutable archive tests, no network."""
import copy, tempfile, unittest
from pathlib import Path
from datetime import datetime,timezone
from postmatch_once_accept_263 import (
 OBS,Reject,fingerprint,decide,archive_once,read_once,path_for)

NOW=datetime(2026,11,12,13,0,tzinfo=timezone.utc)
PRE="2026-11-08T10:00:00+00:00"
CHECKED="2026-11-08T13:30:00+00:00"
KICK="2026-11-08T11:00:00+00:00"
HOME="aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa"
AWAY="bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"
HASH="a"*64

def forecast():
 d={"schema":"quad_forward_263_v1","created_at_utc":PRE,
  "fixture":{"league":"ENG1","match_local_date":"2026-11-08",
             "home_id":HOME,"away_id":AWAY,"kickoff_utc":KICK,
             "source_checked_at_utc":"2026-11-08T10:00:05+00:00",
             "fixture_verification":"VERIFIED_BY_LIVE_OFFICIAL_GATE"}}
 d["payload_sha256"]=fingerprint(d)
 return d

def observation(f,*,kind="OFFICIAL_LEAGUE",url="https://www.premierleague.com/en/match/12345",
                score=None,event="match-12345",checked=CHECKED,upstream="web-primary",
                state="FULL_TIME",method="LIVE_PARSED_SCORE_ADAPTER"):
 return {"schema":OBS,"capture_mode":method,"forecast_sha256":f["payload_sha256"],
         "league":f["fixture"]["league"],"home_id":HOME,"away_id":AWAY,
         "kickoff_utc":KICK,"checked_at_utc":checked,"source_kind":kind,
         "source_url":url,"response_sha256":HASH,"source_event_id":event,
         "upstream_owner":upstream,"match_state":state,
         "score":[2,1] if score is None and state=="FULL_TIME" else score,
         "score_scope":"90MIN_FT"}

class OnePass(unittest.TestCase):
 def setUp(self):self.f=forecast()
 def test_single_official_league_source_accepted_and_sha(self):
  r=decide(self.f,[observation(self.f)],now=NOW)
  self.assertEqual((r["status"],r["score"],r["source_grade"]),
                   ("ACCEPTED_FULL_TIME",[2,1],"OFFICIAL_LEAGUE_OR_CLUB"))
  self.assertFalse(r["human_attestation"])
 def test_single_official_club_must_be_curated_for_fixture(self):
  club=observation(self.f,kind="OFFICIAL_CLUB",
     url="https://www.club-example.org/match/12345")
  with self.assertRaisesRegex(Reject,"CLUB_HOST_NOT_CURATED"):
   decide(self.f,[club],now=NOW)
  r=decide(self.f,[club],now=NOW,
    club_hosts={("ENG1","club-example.org"):HOME})
  self.assertEqual(r["status"],"ACCEPTED_FULL_TIME")
 def test_secondary_one_source_not_enough(self):
  a=observation(self.f,kind="SECONDARY",
    url="https://www.football-data.co.uk/mmz4281/2627/E0.csv",
    upstream="FOOTBALL_DATA",event="fd-123")
  self.assertEqual(decide(self.f,[a],now=NOW)["status"],
                   "HOLD_NEED_INDEPENDENT_SECOND_SOURCE")
 def test_two_separate_secondary_publishers_accepted(self):
  a=observation(self.f,kind="SECONDARY",
    url="https://www.football-data.co.uk/mmz4281/2627/E0.csv",
    upstream="FD",event="fd123")
  b=observation(self.f,kind="SECONDARY",
    url="https://www.espn.com/soccer/match/_/gameId/123",
    upstream="ESPN",event="espn123")
  r=decide(self.f,[a,b],now=NOW)
  self.assertEqual(r["source_grade"],"TWO_INDEPENDENT_PUBLISHER_SOURCES")
  self.assertEqual(len(r["source_evidence"]),2)
 def test_shared_upstream_same_feed_mirrors_rejected(self):
  a=observation(self.f,kind="SECONDARY",
    url="https://www.football-data.co.uk/mmz4281/2627/E0.csv",
    upstream="SHARED",event="a")
  b=observation(self.f,kind="SECONDARY",
    url="https://www.espn.com/soccer/match/_/gameId/123",
    upstream="SHARED",event="b")
  self.assertEqual(decide(self.f,[a,b],now=NOW)["status"],
                   "HOLD_NEED_INDEPENDENT_SECOND_SOURCE")
 def test_conflicting_scores_block_even_if_official(self):
  a=observation(self.f)
  b=observation(self.f,kind="SECONDARY",
    url="https://www.espn.com/soccer/match/_/gameId/123",
    score=[0,1],event="other")
  self.assertEqual(decide(self.f,[a,b],now=NOW)["status"],
                   "HOLD_SCORE_OR_STATUS_CONFLICT")
 def test_wrong_team_sha_and_time_block(self):
  wrong=observation(self.f);wrong["away_id"]="not-the-registered-club"
  with self.assertRaisesRegex(Reject,"IDENTITY"):
   decide(self.f,[wrong],now=NOW)
  wrong=observation(self.f);wrong["forecast_sha256"]="0"*64
  with self.assertRaisesRegex(Reject,"IDENTITY"):
   decide(self.f,[wrong],now=NOW)
  wrong=observation(self.f,checked="2026-11-08T11:15:00+00:00")
  with self.assertRaisesRegex(Reject,"NOT_FINAL"):
   decide(self.f,[wrong],now=NOW)
  wrong=observation(self.f);wrong["score_scope"]="PENALTY_WINNER"
  with self.assertRaisesRegex(Reject,"REGULATION"):
   decide(self.f,[wrong],now=NOW)
 def test_url_and_source_claim_not_sufficient(self):
  fake=observation(self.f,method="RESEARCH_WEB_LINK_ONLY")
  with self.assertRaisesRegex(Reject,"WEB_LINK_CLAIM"):
   decide(self.f,[fake],now=NOW)
  bad=observation(self.f,url="http://premierleague.com/en/match/123")
  with self.assertRaisesRegex(Reject,"UNTRUSTED_SOURCE_URL"):
   decide(self.f,[bad],now=NOW)
  fake=observation(self.f,url="https://bad.source.example/123")
  with self.assertRaisesRegex(Reject,"WRONG_OFFICIAL_LEAGUE_HOST"):
   decide(self.f,[fake],now=NOW)
 def test_postponed_record_has_no_score_never_scored(self):
  a=observation(self.f,state="POSTPONED")
  self.assertEqual(decide(self.f,[a],now=NOW)["status"],
                   "ACCEPTED_POSTPONED_NO_SCORE")
  fake=observation(self.f,state="POSTPONED",score=[0,0])
  with self.assertRaisesRegex(Reject,"POSTPONED"):
   decide(self.f,[fake],now=NOW)
 def test_research_only_cannot_archive(self):
  with tempfile.TemporaryDirectory() as directory:
   o=observation(self.f,method="RESEARCH_WEB_LINK_ONLY")
   with self.assertRaises(Reject):archive_once(directory,self.f,[o],now=NOW)
   self.assertFalse(path_for(directory,self.f).exists())
 def test_archive_once_twice_same_sha_zero_new_sources(self):
  with tempfile.TemporaryDirectory() as directory:
   a=archive_once(directory,self.f,[observation(self.f)],now=NOW)
   path=path_for(directory,self.f);before=path.read_bytes()
   b=archive_once(directory,self.f,[],now=NOW)
   self.assertEqual(a,b)
   self.assertEqual(before,path.read_bytes())
   self.assertEqual(a["archive_sha256"],fingerprint(
    {k:v for k,v in a.items() if k!="archive_sha256"}))
 def test_archive_tamper_rejected_and_no_rewrite(self):
  import json
  with tempfile.TemporaryDirectory() as directory:
   archive_once(directory,self.f,[observation(self.f)],now=NOW)
   path=path_for(directory,self.f)
   data=json.loads(path.read_text());data["score"]=[10,0]
   path.write_text(json.dumps(data))
   with self.assertRaisesRegex(Reject,"ARCHIVED_RECORD_SHA_TAMPERED"):
    read_once(directory,self.f)
   with self.assertRaises(Reject):
    archive_once(directory,self.f,[observation(self.f)],now=NOW)
 def test_forecast_tampering_blocked(self):
  fake=copy.deepcopy(self.f);fake["fixture"]["away_id"]="changed"
  with self.assertRaisesRegex(Reject,"FORECAST_SHA_TAMPERED"):
   decide(fake,[observation(self.f)],now=NOW)
 def test_unverified_state_no_archive(self):
  with tempfile.TemporaryDirectory() as directory:
   state=archive_once(directory,self.f,[],now=NOW)
   self.assertEqual(state["status"],"HOLD_NO_FINAL_SOURCE")
   self.assertFalse(path_for(directory,self.f).exists())
if __name__=="__main__":unittest.main()
