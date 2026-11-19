"""Forty previous SHA-sealed real forecast RECORDS, read-only decision replay.

No new forecast generated, no result read, no model refit, no price needed.
Original decision.json files are never modified or re-classified.
"""
from pathlib import Path
import json
from datetime import datetime,timedelta,timezone
from model_first_decision_263 import select,market_reference,verified,SCHEMA,REF_SCHEMA
ROOT=Path(__file__).resolve().parents[2]

def run():
    lock=json.loads((ROOT/"experiments/263/model_first_selection_lock_20261120.json").read_text())
    paths=sorted((ROOT/"forward_morning_263/2026-11-08").glob("*.json"))
    if len(paths)!=40:raise ValueError("EXPECTED_EXACTLY_40_EXISTING_SEALED_RECORDS")
    n=0; main=0; pas=0; fallback=0
    for path in paths:
        f=json.loads(path.read_text())
        bpath=ROOT/"experiments/263/sabah_research/new100/2026-11-08"/path.stem/"baseline.json"
        b=json.loads(bpath.read_text())
        orig=ROOT/"experiments/263/sabah_research/new100/2026-11-08"/path.stem/"decision.json"
        before=orig.read_bytes()
        now=max(datetime.fromisoformat(f["created_at_utc"]),
                datetime.fromisoformat(b["created_at_utc"]))+timedelta(seconds=1)
        if now>=datetime.fromisoformat(f["fixture"]["kickoff_utc"]):
            raise ValueError("NOT_BEFORE_KICKOFF")
        d=select(f,b,lock,now=now)
        verified(d,SCHEMA)
        ref=market_reference(d,{},source_pdf_sha256="a"*64)
        verified(ref,REF_SCHEMA)
        if ref["decision_sha256"]!=d["payload_sha256"]:
            raise ValueError("FIFTH_REFERENCE_CHANGED_MODEL_DECISION")
        if d["price_used_in_decision"] is not False or d["betting_authorized"] is not False:
            raise ValueError("PRICE_INFLUENCE_OR_BETTING_AUTHORIZED")
        prob={z["market"]:z for z in d["model_market_diagnostics"]}
        ms=[prob[k] for k in ("MS1","MSX","MS2")]
        if any(r["anchor_model"]!="M4" for r in ms):
            raise ValueError("SPLIT_MS_MODELS")
        if abs(sum(z["calibrated_probability"] for z in ms)-1)>1e-8:
            raise ValueError("MS_SUM_NOT_ONE")
        for key in ("BTTS_YES","BTTS_NO","OVER_2.5","UNDER_2.5"):
            if prob[key]["anchor_model"] not in ("C3","M4"):
                raise ValueError("WRONG_SPECIALIST")
        if d["used_fallback_families"]: fallback+=1
        if orig.read_bytes()!=before:
            raise ValueError("HISTORIC_DECISION_REWRITTEN")
        n+=1
        main+=bool(d["main_candidate"])
        pas+=d["main_candidate"] is None
    return {"existing_sha_forecasts":n,"research_model_candidates":main,
            "research_model_pas":pas,"c3_unavailable_fallbacks":fallback,
            "historical_file_updates":0,"new_real_pilot":0,
            "price_required_for_decision":False,"model_math_changed":False}
if __name__=="__main__":
    print("MODEL_ONLY_EXISTING_40_SHA_REPLAY="+json.dumps(run(),sort_keys=True))
