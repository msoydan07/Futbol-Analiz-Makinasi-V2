"""Real SHA integration: once archived, the old scoring bridge never fetches CSV."""
import json,tempfile,unittest
from datetime import datetime,timezone
from unittest.mock import patch
from pathlib import Path
from postmatch_csv_bridge_263 import ROOT,evaluate
from postmatch_once_accept_263 import archive_once,OBS

class BridgeIntegration(unittest.TestCase):
 def test_real_original_sha_and_four_models_read_onepass_no_network(self):
  f=json.loads((ROOT/"forward_morning_263/2026-11-08/00156b675f1e2d1a941fba4c.json").read_text())
  x=f["fixture"]
  self.assertEqual(x["league"],"NED1")
  obs={"schema":OBS,"capture_mode":"LIVE_PARSED_SCORE_ADAPTER",
       "forecast_sha256":f["payload_sha256"],"league":x["league"],
       "home_id":x["home_id"],"away_id":x["away_id"],
       "kickoff_utc":x["kickoff_utc"],"checked_at_utc":"2026-11-12T10:00:00+00:00",
       "source_kind":"OFFICIAL_LEAGUE",
       "source_url":"https://eredivisie.nl/matches/result/fixture-123",
       "response_sha256":"c"*64,"source_event_id":"fixture-123",
       "upstream_owner":"eredivisie","match_state":"FULL_TIME",
       "score":[2,0],"score_scope":"90MIN_FT"}
  now=datetime(2026,11,12,13,tzinfo=timezone.utc)
  with tempfile.TemporaryDirectory() as directory:
   record=archive_once(directory,f,[obs],now=now)
   self.assertEqual(record["status"],"ACCEPTED_FULL_TIME")
   # No source fetches whatsoever are permitted when the new outcome is
   # already terminal; Names is not used unless a live CSV is requested.
   with patch("postmatch_csv_bridge_263.sealed",return_value={f["payload_sha256"]:f}),\
        patch("postmatch_csv_bridge_263.registered_names",
              return_value={f["payload_sha256"]:{"league":"NED1"}}),\
        patch("postmatch_csv_bridge_263.Names",return_value=None),\
        patch("postmatch_csv_bridge_263.sources_for") as fetch:
    fetch.return_value=({}, {})
    result=evaluate(root=directory,now=now)
    fetch.assert_called_once()
    self.assertEqual(fetch.call_args.args[2],set())
   self.assertEqual((result["registered"],result["provisional_scored"],result["pending"]),(1,1,0))
   self.assertEqual(result["daily_external_csv_calls"],0)
   self.assertEqual(result["archived_new_once"],1)
   self.assertEqual(result["per_model"]["ALL_PROVISIONAL"]["M4"]["MS"]["n"],1)
   self.assertEqual(result["status_counts"],{"ARCHIVED_OFFICIAL_LEAGUE_OR_CLUB":1})
   self.assertFalse(result["forecast_modified"])
if __name__=="__main__":unittest.main()
