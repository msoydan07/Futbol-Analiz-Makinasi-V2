"""Synthetic future-fixture full pipeline using *real accepted* 4518 results.

No real future match is asserted in this test. Fixture is explicitly
fabricated for unit testing only. The historical dataset is authentic
owner-accepted research material and must match its SHA256 acceptance.
"""
import csv,json,tempfile,unittest
from collections import Counter
from datetime import datetime,timezone,timedelta
from pathlib import Path
from trusted_263_snapshot_bridge import build
from official_263_fixture_bridge import convert_observation
from xgb_live_inference import inference
from prospective_seal import seal,Rejected

ROOT=Path(__file__).resolve().parents[2]
FIXED=datetime(2026,11,9,10,0,tzinfo=timezone.utc)

class ResearchIntegration(unittest.TestCase):
 def test_asof_xgb_from_4518_snapshot_and_synthetic_official_gate(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   report=build(ROOT/"data/quad_accepted_263/extended_history.csv",
       ROOT/"data/quad_accepted_263/source_acceptance.json",
       root,now=FIXED)
   rows=list(csv.DictReader((root/"normalized_263_research.csv").open()))
   ids=Counter()
   for r in rows:
    if r["league"]=="ENG1":
     ids[r["home"]]+=1
     ids[r["away"]]+=1
   home,away=[k for k,n in ids.most_common(2)]
   observation={"status":"VERIFIED","league":"ENG1",
     "home_id":home,"away_id":away,
     "kickoff_utc":(FIXED+timedelta(days=3,hours=3)).isoformat(),
     "source_url":"https://www.premierleague.com/fake-synthetic-only",
     "retrieved_at_utc":(FIXED-timedelta(minutes=2)).isoformat()}
   manifest=convert_observation(observation,"ENG1",report,now=FIXED)
   self.assertEqual(manifest["home_name"],home)
   self.assertNotIn("home_goals",manifest)
   p=root/"synthetic_fixture.json"
   p.write_text(json.dumps(manifest),encoding="utf8")
   output,details=inference(root/"normalized_263_research.csv",p,now=FIXED)
   self.assertEqual(details["training_matches"]>1000,True)
   self.assertEqual(output["models"]["XGBoost"]["status"],"AVAILABLE")
   self.assertEqual(output["fixture"]["home_id"],home)
   self.assertAlmostEqual(sum(output["models"]["XGBoost"]["probabilities"].values()),1.0)
   sealed,digest=seal(output,root,now=FIXED)
   self.assertTrue(sealed.is_file())
   with self.assertRaises(Rejected):
    seal(output,root,now=FIXED)

if __name__=="__main__":unittest.main()
