"""Source join safety with real 4518-score snapshot and synthetic fixture.
No synthetic fixture is ever treated as live official proof.
"""
import copy,json,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from trusted_263_snapshot_bridge import transform
from official_263_fixture_bridge import convert_observation,GateBlocked

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"data/quad_accepted_263/extended_history.csv"
ACCEPT=ROOT/"data/quad_accepted_263/source_acceptance.json"
NOW=datetime(2026,11,9,12,0,tzinfo=timezone.utc)

def prior_audit():
    rows,r=transform(SRC.read_bytes(),json.loads(ACCEPT.read_text()),asof=NOW)
    return rows,r

def fixture():
    return {"status":"VERIFIED","league":"ENG1",
            "home_id":"a"*36,"away_id":"b"*36,
            "kickoff_utc":(NOW+timedelta(days=2)).isoformat(),
            "source_url":"https://www.premierleague.com/example",
            "retrieved_at_utc":(NOW-timedelta(minutes=3)).isoformat()}

class RealHistoryAndSyntheticGate(unittest.TestCase):
    def test_research_snapshot_integrity_and_canonical_ids(self):
        rows,audit=prior_audit()
        self.assertEqual(len(rows),4518)
        self.assertEqual(len(audit["league_counts"]),10)
        self.assertEqual(audit["history_sha256"],
                         audit["owner_accepted_manifest_snapshot_sha"])
        self.assertFalse(audit["independent_result_verification"])

    def test_acceptance_sha_mutation_fails(self):
        data=json.loads(ACCEPT.read_text())
        data["snapshot_sha256"]="a"*64
        with self.assertRaisesRegex(ValueError,"SHA"):
            transform(SRC.read_bytes(),data,asof=NOW)

    def test_actual_263_id_fields_kept_in_manifest(self):
        _,audit=prior_audit()
        obs=fixture()
        result=convert_observation(obs,"ENG1",audit,now=NOW)
        self.assertEqual(result["home_name"],obs["home_id"])
        self.assertEqual(result["home_id"],obs["home_id"])
        self.assertEqual(result["fixture_verified_by"],"EXTERNAL_OFFICIAL_GATE")

    def test_reject_unverified_official_observation(self):
        _,audit=prior_audit()
        obs=fixture();obs["status"]="NOT_VERIFIED"
        with self.assertRaises(GateBlocked):
            convert_observation(obs,"ENG1",audit,now=NOW)

    def test_reject_future_or_late_source(self):
        _,audit=prior_audit()
        obs=fixture()
        obs["retrieved_at_utc"]=(NOW+timedelta(minutes=10)).isoformat()
        with self.assertRaises(GateBlocked):
            convert_observation(obs,"ENG1",audit,now=NOW)

if __name__=="__main__":
    unittest.main()
