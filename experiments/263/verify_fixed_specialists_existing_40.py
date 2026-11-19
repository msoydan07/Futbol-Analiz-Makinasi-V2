"""Read-only real 40 immutable SHA Nov8 forecasts acceptance of next decision policy.
Recalculates hypothetical *new* decisions for compatibility ONLY, never writes
or relabels existing decisions, predictions, scores, source or odds evidence.
"""
import json
from datetime import datetime,timedelta
from pathlib import Path
from four_model_value_policy_263 import decide

ROOT=Path(__file__).resolve().parents[2]
def audit():
    forecasts=sorted((ROOT/"forward_morning_263/2026-11-08").glob("*.json"))
    if len(forecasts)!=40:raise ValueError("EXPECTED_40_PREVIOUSLY_SEALED_FORECASTS")
    counts={"n":0,"normalised_ms":0,"fixed_m4_ms":0,"fixed_c3_kg":0,"fixed_c3_goals":0,"pas_with_no_odds":0}
    lock=json.loads((ROOT/"experiments/263/forward_dev_calibration_lock_263.json").read_text())
    for path in forecasts:
        f=json.loads(path.read_text())
        base=ROOT/"experiments/263/sabah_research/new100/2026-11-08"/path.stem/"baseline.json"
        b=json.loads(base.read_text())
        original_decision=ROOT/"experiments/263/sabah_research/new100/2026-11-08"/path.stem/"decision.json"
        before=original_decision.read_bytes()
        now=max(datetime.fromisoformat(f["created_at_utc"]),datetime.fromisoformat(b["created_at_utc"]))+timedelta(seconds=1)
        if now>=datetime.fromisoformat(f["fixture"]["kickoff_utc"]):
            raise ValueError("NOT_REAL_PREKICKOFF_OBSERVATION")
        d=decide(f,b,lock,now=now)
        ex=d["fixed_market_specialists_research_only"]
        if d["status"]!="RESEARCH_PAS" or d["main_candidate"] is not None or d["betting_authorized"] is not False:
            raise ValueError("MISSING_ODDS_MUST_REMAIN_PAS")
        ms=ex["MS"]["dev_shrunken_probability_vector"]
        if ms is None or abs(sum(ms.values())-1)>1e-10:
            raise ValueError("DECISION_MS_100_PERCENT_FAILED")
        if ex["MS"]["model"]!="M4" or ex["KG"]["model"]!="C3" or ex["GOALS"]["model"]!="C3":
            raise ValueError("PREFERRED_SPECIALIST_NOT_USED")
        if original_decision.read_bytes()!=before:
            raise ValueError("ORIGINAL_SHA_SEAL_CHANGED")
        counts["n"]+=1;counts["normalised_ms"]+=1
        counts["fixed_m4_ms"]+=1;counts["fixed_c3_kg"]+=1;counts["fixed_c3_goals"]+=1
        counts["pas_with_no_odds"]+=1
    return counts
if __name__=="__main__":
    print("PREVIOUS_40_SHA_READONLY_REPLAY="+json.dumps(audit(),sort_keys=True))
