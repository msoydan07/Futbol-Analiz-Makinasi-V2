"""ONE synthetic gate, real locked inputs, TEMPORARY output only.

Checks that 10-day gap evidence threads all the way through B/C2/C3/M4:
No real fixture is asserted, no new Git SHA seal or pilot is committed.
"""
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
from exp_263_batch import clean_rows
from forward_quad import predict_quad_from_verified_gate

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
BASE=ROOT/"m4_quad_base/historical_results.csv"
AUDIT=ROOT/"data/results_only_263/4617_research_input_provenance.json"
LOCK=ROOT/"experiments/263/m4_lock.json"

def main():
    rows=clean_rows(SRC)
    if len(rows)!=4617:raise ValueError("WRONG_SOURCE_COUNT")
    clubs=list(dict.fromkeys(r["home_id"] for r in rows
                             if r["league"]=="ENG1" and r["season"]=="2026-2027"))
    if len(clubs)<2:raise ValueError("UNREALISTIC_SYNTHETIC_IDS")
    now=datetime.now(timezone.utc)
    gate={"status":"VERIFIED","league":"ENG1","home_id":clubs[0],"away_id":clubs[1],
          "source_url":"https://example.invalid/SYNTHETIC_TEST_ONLY_NOT_AN_OFFICIAL_FIXTURE",
          "kickoff_utc":(now+timedelta(hours=2)).isoformat(),
          "retrieved_at_utc":now.isoformat()}
    original_sha=hashlib.sha256(SRC.read_bytes()).hexdigest()
    with TemporaryDirectory(prefix="263_gap_synthetic_quads_") as folder:
        path,pred=predict_quad_from_verified_gate(
            gate,SRC,folder,LOCK,now=now,base=BASE,source_audit=AUDIT)
        if not path.is_file():raise ValueError("NO_TEMPORARY_SAMPLE")
        if set(pred["model_predictions"])!={"B","C2","C3","M4"}:
            raise ValueError("FOUR_MODELS_NOT_IN_RECORD")
        evidence=pred["data"].get("current_season_gap_check",{})
        if evidence.get("status")!="BOUNDED_GAP_NO_MISSING_RESULTS_IN_PUBLIC_FEED_RESEARCH_ONLY":
            raise ValueError("NO_VERIFIED_GAP_METADATA")
        if evidence.get("league")!="ENG1" or evidence.get("age_days")<=10:
            raise ValueError("NO_GAP_AGE_PROOF")
        if pred["status"]!="EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING":
            raise ValueError("NOT_SYNTHETIC_RESEARCH_STATUS")
        if pred["payload_sha256"]!=json.loads(path.read_text())["payload_sha256"]:
            raise ValueError("TEMPORARY_RECORD_TAMPER")
        if hashlib.sha256(SRC.read_bytes()).hexdigest()!=original_sha:
            raise ValueError("HISTORY_MODIFIED")
    print("REAL_MODEL_TEMPORARY_GAP_ACCEPTANCE="+json.dumps({
        "schema":"263_SYNTHETIC_FIXTURE_REAL_MODELS_TEMP_ONLY",
        "same_snapshot_sha":original_sha,
        "four_model_status":{m:pred["model_predictions"][m]["status"]
                             for m in ("B","C2","C3","M4")},
        "source_gap":{k:evidence.get(k) for k in ("age_days","provider_last_result_date",
                    "historical_overlap_matches_verified","status")},
        "file_persisted":False,"official_fixture_verified":False,
        "historical_pilot_increment":0,"live_prediction_created":False,
        "odds_queried":False,"xg_used":False},sort_keys=True))

if __name__=="__main__":main()
