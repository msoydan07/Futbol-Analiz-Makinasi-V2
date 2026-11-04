"""One read-only actual TFF official fixture gate probe, no predictions."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from analyze_named_match_gate import run

def main():
    before=datetime.now(timezone.utc)
    result=run("TUR1","Gaziantep FK","Kasımpaşa")
    good=result.get("status")=="VERIFIED" and result.get("kickoff_utc")=="2026-11-06T17:00:00+00:00"
    report={"schema":"263_first_live_tff_fixture_gate_probe_v1","created_at_utc":before.isoformat(),
            "fixture_name":"Gaziantep FK - Kasımpaşa",
            "expected_kickoff_utc":"2026-11-06T17:00:00+00:00",
            "actual_kickoff_utc":result.get("kickoff_utc"),
            "actual_official_status":result.get("status"),
            "gate_ready":good,"returned_reason":result.get("reason"),
            "gate_checked_at":result.get("retrieved_at_utc"),
            "official_source_url":result.get("source_url"),
            "user_named_match_selection_done":False,
            "model_prediction_registered":False,
            "source_human_acceptance":False,
            "not_live_betting_authorized":True}
    out=Path("/tmp/263_first_real_fixture_gate_status.json")
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    if not good:raise SystemExit("LIVE_OFFICIAL_FIXTURE_GATE_BLOCKED")


if __name__=="__main__":main()
