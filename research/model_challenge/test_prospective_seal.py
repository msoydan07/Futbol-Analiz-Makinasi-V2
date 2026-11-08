"""Tests use synthetic fixtures only; no historical pilot is touched."""
from datetime import datetime,timedelta,timezone
import tempfile,unittest,json
from pathlib import Path
from prospective_seal import validate, seal,Rejected,digest

NOW=datetime(2026,11,16,10,0,tzinfo=timezone.utc)
P={"H":.48,"D":.25,"A":.27}
def candidate():
    return {
      "schema":"MC_PROSPECTIVE_SHADOW_INPUT_V1",
      "fixture":{"fixture_id":"fixture-100","league":"ENG1","home_id":"club-a",
        "away_id":"club-b","kickoff_utc":(NOW+timedelta(hours=3)).isoformat()},
      "source":{"official_fixture_url":"https://www.premierleague.com/",
        "source_verified_at_utc":(NOW-timedelta(minutes=7)).isoformat(),
        "history_asof_utc":(NOW-timedelta(hours=2)).isoformat(),
        "model_code_sha":"a"*40,"history_sha":"b"*64},
      "created_at_utc":(NOW-timedelta(minutes=2)).isoformat(),
      "models":{name:{"status":"AVAILABLE","probabilities":dict(P)}
                for name in ("Elo","Poisson","XGBoost","EqualWeightHybrid")}}

class SealTests(unittest.TestCase):
 def test_success_and_immutable_write(self):
  with tempfile.TemporaryDirectory() as root:
   path,sha=seal(candidate(),root,now=NOW)
   self.assertTrue(path.is_file())
   self.assertEqual(json.loads(path.read_text())["payload_sha256"],sha)
   with self.assertRaises(Rejected):seal(candidate(),root,now=NOW)
 def test_reject_post_kickoff(self):
  c=candidate();c["fixture"]["kickoff_utc"]=(NOW-timedelta(minutes=1)).isoformat()
  with self.assertRaises(Rejected):validate(c,NOW)
 def test_reject_backdating(self):
  c=candidate();c["created_at_utc"]=(NOW-timedelta(days=1)).isoformat()
  with self.assertRaises(Rejected):validate(c,NOW)
 def test_reject_missing_timezone(self):
  c=candidate();c["created_at_utc"]="2026-11-16T09:58:00"
  with self.assertRaises(Rejected):validate(c,NOW)
 def test_reject_invalid_probability(self):
  c=candidate();c["models"]["Elo"]["probabilities"]["H"]=.61
  with self.assertRaises(Rejected):validate(c,NOW)
 def test_reject_disagreeing_hybrid(self):
  c=candidate();c["models"]["EqualWeightHybrid"]["probabilities"]={"H":.5,"D":.25,"A":.25}
  with self.assertRaises(Rejected):validate(c,NOW)
 def test_pas_propagation(self):
  c=candidate();c["models"]["XGBoost"]={"status":"PAS","probabilities":None}
  c["models"]["EqualWeightHybrid"]={"status":"PAS","probabilities":None}
  validate(c,NOW)
  c["models"]["EqualWeightHybrid"]={"status":"AVAILABLE","probabilities":dict(P)}
  with self.assertRaises(Rejected):validate(c,NOW)
 def test_bad_source_hash(self):
  c=candidate();c["source"]["history_sha"]="madeup"
  with self.assertRaises(Rejected):validate(c,NOW)
 def test_digest_determinism(self):
  self.assertEqual(digest({"a":1,"b":2}),digest({"b":2,"a":1}))

if __name__=="__main__":unittest.main()
