"""One targeted batch: real staged exception, training and baseline alignment."""
import csv
import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from full_match_eligibility_263 import full_match_rows, POLICY_PATH
from forward_empirical_baseline_263 import produce
from forward_calibration_bridge_263 import _digest
from test_forward_baseline_provenance_263 import forecast
from forward_quad import predict_quad_from_verified_gate

ROOT=Path(__file__).resolve().parents[2]
EXCEPTION_ID="e775098b-7465-52ab-92e6-534adabea6bf"
NOW=datetime(2026,11,6,16,0,tzinfo=timezone.utc)

class FullMatchEligibilityAcceptance(unittest.TestCase):
    def make_history(self,root):
        path=root/"sample.csv"
        fields=["fixture_id","league","season","match_date","home_id","away_id","home_goals","away_goals","result"]
        entries=[]
        for i in range(150):
            h=i%4;away=(i+1)%3
            entries.append({"fixture_id":f"normal-{i}","league":"NED1",
                 "season":"2026-2027","match_date":"2026-11-05",
                 "home_id":f"H{i}","away_id":f"A{i}","home_goals":str(h),
                 "away_goals":str(away),"result":"H" if h>away else "D" if h==away else "A"})
        entries.append({"fixture_id":EXCEPTION_ID,"league":"NED1",
            "season":"2026-2027","match_date":"2026-10-31",
            "home_id":"CAM","away_id":"GAE","home_goals":"4","away_goals":"0","result":"H"})
        with path.open("w",newline="",encoding="utf-8") as handle:
            writer=csv.DictWriter(handle,fieldnames=fields)
            writer.writeheader();writer.writerows(entries)
        return path,entries

    def test_existing_staged_4501_retains_awarded_score_but_excludes_training(self):
        with (ROOT/"data/staged_263/extended_history.csv").open(encoding="utf-8-sig",newline="") as handle:
            source=list(csv.DictReader(handle))
        self.assertEqual(len(source),4501)
        original=[r for r in source if r["fixture_id"]==EXCEPTION_ID]
        self.assertEqual(len(original),1)
        self.assertEqual((original[0]["home_goals"],original[0]["away_goals"]),("4","0"))
        subset=[r for r in source if r["league"]=="NED1"]
        eligible,excluded,digest=full_match_rows(subset)
        self.assertEqual(excluded,[EXCEPTION_ID])
        self.assertEqual(len(eligible),len(subset)-1)
        self.assertEqual(digest,hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest())
        self.assertEqual(len(source),4501)

    def test_tampered_exception_score_blocks(self):
        row={"fixture_id":EXCEPTION_ID,"league":"NED1","match_date":"2026-10-31",
             "home_goals":"3","away_goals":"0","result":"H"}
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_MATCH_SOURCE_MISMATCH"):
            full_match_rows([row])

    def test_empirical_baseline_omits_incomplete_match_and_seals_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            path,entries=self.make_history(Path(folder))
            f=forecast()
            f["fixture"]["league"]="NED1"
            f["data"]["snapshot_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
            f["data"]["league_history_rows"]=150
            f["data"]["league_latest_result_date"]="2026-11-05"
            f["data"]["training_excluded_partial_match_ids"]=[EXCEPTION_ID]
            f["data"]["full_match_policy_sha256"]=hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()
            f["payload_sha256"]=_digest({k:v for k,v in f.items() if k!="payload_sha256"})
            b=produce(f,path,now=NOW)
            self.assertEqual(b["historical_match_count"],150)
            self.assertEqual(b["last_result_date"],"2026-11-05")
            f["data"]["training_excluded_partial_match_ids"]=[]
            f["payload_sha256"]=_digest({k:v for k,v in f.items() if k!="payload_sha256"})
            with self.assertRaisesRegex(ValueError,"EXCLUSION_MISMATCH"):
                produce(f,path,now=NOW)
            f["data"]["training_excluded_partial_match_ids"]=[EXCEPTION_ID]
            f["data"]["full_match_policy_sha256"]="0"*64
            f["payload_sha256"]=_digest({k:v for k,v in f.items() if k!="payload_sha256"})
            with self.assertRaisesRegex(ValueError,"POLICY_HASH_MISMATCH"):
                produce(f,path,now=NOW)

    def test_quad_training_never_sees_partial_match(self):
        with tempfile.TemporaryDirectory() as folder:
            path,rows=self.make_history(Path(folder))
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            gate={"source_url":"https://example.com/synthetic-only"}
            kickoff=datetime(2026,11,6,18,0,tzinfo=timezone.utc)
            observed=[]
            def c1_checked(past,*args):
                observed.append({r["fixture_id"] for r in past})
                return None
            def c3_checked(past):
                observed.append({r["fixture_id"] for r in past})
                return None
            def m4_checked(past,*args):
                observed.append({r["fixture_id"] for r in past})
                return (None,None,None,len(past))
            with (patch("forward_quad.valid_gate",return_value=("NED1","NEW_H","NEW_A",kickoff,NOW,"2026-11-06")),
                  patch("forward_quad.clean_rows",return_value=rows),
                  patch("forward_quad.verify_snapshot",return_value=("APPEND_ONLY_HUMAN_SOURCE_ATTESTED_NOT_INDEPENDENTLY_RECHECKED",digest)),
                  patch("forward_quad.c1",side_effect=c1_checked),
                  patch("forward_quad.fit_c3",side_effect=c3_checked),
                  patch("forward_quad.canonical_c2_lambda",return_value=(None,"SYNTHETIC_NO_COVERAGE")),
                  patch("forward_quad.fit_m4",side_effect=m4_checked),
                  patch("forward_quad.predict_m4",return_value=None)):
                target,record=predict_quad_from_verified_gate(
                    gate,path,Path(folder)/"record",
                    ROOT/"experiments/263/m4_lock.json",now=NOW)
            self.assertTrue(target.exists())
            self.assertEqual(len(observed),3)
            self.assertTrue(all(EXCEPTION_ID not in each for each in observed))
            self.assertEqual(record["data"]["league_history_rows"],150)
            self.assertEqual(record["data"]["training_excluded_partial_match_ids"],[EXCEPTION_ID])
            self.assertEqual(record["data"]["full_match_policy_sha256"],
                             hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest())
            self.assertFalse(record.get("betting_authorized",False))

if __name__=="__main__":unittest.main()
