"""22 Nov 2026: ONE research-only real-fixture M4/C3 -> P0/P1 -> P2 probe.

Input prices are manually transcribed from the locally inspected user iddaa PDF.
The original PDF bytes are NOT on this GitHub runner, so this is NOT the
canonical original-PDF-verified release workflow. No existing seals change.
Run only before kickoff. Never substitute past results for an unrun forecast.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "experiments/263"),
                str(ROOT / "experiments/p1_market_intelligence")]

from analyze_named_match_gate import run as live_gate
from forward_quad import predict_quad_from_verified_gate
from forward_empirical_baseline_263 import produce
from model_first_decision_263 import select, verified, SCHEMA as DECISION_SCHEMA
from p1_market import no_vig, analyze_prices, MARKETS
from p2_market_alignment import _align
from check_active_decisions_263 import verify_active_policy

SOURCE_PDF_SHA = "76af6d9e98d2a9c93ce9cd95eff46ae6ea696454305b2b238f4741b5f60435c8"
PDF_CAPTURED_UTC = "2026-11-22T08:28:29+00:00"
HISTORY = ROOT / "data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
BASELINE = ROOT / "m4_quad_base/historical_results.csv"
AUDIT = ROOT / "data/results_only_263/4617_research_input_provenance.json"
M4_LOCK = ROOT / "experiments/263/m4_lock.json"
V4_LOCK = ROOT / "experiments/263/model_first_selection_lock_20261121_v4.json"

# Each value reproduced from the uploaded 1.pdf (NOT from another bookmaker).
CASES = [
    ("Erzurumspor FK", "Göztepe", "13:30",
     {"MS": {"MS1": 2.33, "MSX": 2.98, "MS2": 2.55},
      "OU25": {"UNDER_2.5": 1.56, "OVER_2.5": 1.93},
      "KG": {"BTTS_YES": 1.70, "BTTS_NO": 1.75}}),
    ("Konyaspor", "Beşiktaş", "16:00",
     {"MS": {"MS1": 4.95, "MSX": 3.87, "MS2": 1.43},
      "OU25": {"UNDER_2.5": 1.95, "OVER_2.5": 1.55},
      "KG": {"BTTS_YES": 1.63, "BTTS_NO": 1.84}}),
    ("Kasımpaşa", "Alanyaspor", "16:00",
     {"MS": {"MS1": 1.74, "MSX": 3.29, "MS2": 3.60},
      "OU25": {"UNDER_2.5": 1.73, "OVER_2.5": 1.73},
      "KG": {"BTTS_YES": 1.64, "BTTS_NO": 1.83}}),
    ("Trabzonspor", "Eyüpspor", "19:00",
     {"OU25": {"UNDER_2.5": 2.79, "OVER_2.5": 1.25},
      "KG": {"BTTS_YES": 2.01, "BTTS_NO": 1.51}}),
]


def entry(home, away, hour, prices):
    out = {
        "fixture": f"{home} - {away}", "league": "TUR1",
        "date": "2026-11-22", "pdf_local_kickoff": hour,
        "pdf_sha256": SOURCE_PDF_SHA, "pdf_observed_utc": PDF_CAPTURED_UTC,
        "pdf_quote_origin": "MANUAL_TRANSCRIPTION_OF_USER_UPLOAD_NOT_ORIGINAL_PDF_REPARSED_ON_RUNNER",
        "execution_utc": datetime.now(timezone.utc).isoformat(),
        "status": "NOT_STARTED", "model_forecast_persisted": False,
        "official_prediction_authorized": False,
        "legacy_seals_modified": False, "new_2006_11_22_main_sha_record": False,
    }
    norm = {g: no_vig(odds) for g, odds in prices.items()}
    out["p0"] = {
        "probabilities": {g: v["probabilities"] for g, v in norm.items()},
        "complete_seven_quotes": set(prices) == set(MARKETS),
        "margins": {g: v["book_margin"] for g, v in norm.items()},
    }
    if set(prices) == set(MARKETS):
        p1 = analyze_prices(prices)
        out["p1"] = {
            "top": p1["p1_select"]["main"],
            "p1_probabilities": p1["p1"]["p1_probabilities"],
            "price_reexpression_not_independent_evidence": True,
        }
    else:
        out["p1"] = {"status": "NOT_RUN_INCOMPLETE_SEVEN_QUOTES"}
    expected = datetime.fromisoformat(f"2026-11-22T{hour}:00").replace(
        tzinfo=ZoneInfo("Europe/Istanbul")).astimezone(timezone.utc)
    now = datetime.now(timezone.utc)
    if not datetime.fromisoformat(PDF_CAPTURED_UTC) < now < expected:
        out.update(status="NO_PREKICKOFF_WINDOW", block_reason="TODAY_MATCH_ALREADY_STARTED")
        return out
    try:
        gate = live_gate("TUR1", home, away)
        out["official_gate"] = gate
        if gate.get("status") != "VERIFIED":
            out.update(status="OFFICIAL_GATE_BLOCKED", block_reason=gate.get("reason"))
            return out
        if datetime.fromisoformat(gate["kickoff_utc"]) != expected:
            out.update(status="OFFICIAL_PDF_KICKOFF_MISMATCH")
            return out
    except Exception as exc:
        out.update(status="OFFICIAL_GATE_EXCEPTION", block_reason=f"{type(exc).__name__}:{exc}"[:240])
        return out
    try:
        now = datetime.now(timezone.utc)
        _, forecast = predict_quad_from_verified_gate(
            gate, str(HISTORY), str(ROOT / "tmp_live_probe" / "forecasts"),
            str(M4_LOCK), now=now, base=str(BASELINE), source_audit=str(AUDIT)
        )
        out["model_forecast_sha256"] = forecast["payload_sha256"]
        out["model"] = {
            "status": forecast["status"],
            "data_status": forecast["data"]["snapshot_acceptance"],
            "historical_rows": forecast["data"]["league_history_rows"],
            "last_recorded_match": forecast["data"]["league_latest_result_date"],
            "model_availability": {k: v["status"] for k, v in forecast["model_predictions"].items()},
        }
        # Core routine signs the research forecast in a TEMPORARY GitHub runner,
        # but we do not transfer it to or relabel it as an official PDF seal.
        out["temporary_research_model_sha_created"] = True
    except Exception as exc:
        out.update(status="MODEL_DATA_OR_FRESHNESS_GATE_BLOCKED",
                   block_reason=f"{type(exc).__name__}:{exc}"[:260])
        return out
    try:
        baseline = produce(forecast, HISTORY, now=datetime.now(timezone.utc))
        lock = json.loads(V4_LOCK.read_text(encoding="utf-8"))
        decision = select(forecast, baseline, lock, now=datetime.now(timezone.utc))
        verified(decision, DECISION_SCHEMA)
        main, alt = decision["main_candidate"], decision["alternative_candidate"]
        out["model_decision"] = {
            "decision_sha256": decision["payload_sha256"], "status": decision["status"],
            "main": {
                "market": main["market"],
                "probability": main["calibrated_probability"],
                "expert": main["anchor_model"],
            } if main else None,
            "alternative": {
                "market": alt["market"],
                "probability": alt["calibrated_probability"],
                "expert": alt["anchor_model"],
            } if alt else None,
        }
    except Exception as exc:
        out.update(status="MODEL_DECISION_GATE_BLOCKED",
                   block_reason=f"{type(exc).__name__}:{exc}"[:260])
        return out
    try:
        result = _align(
            decision, prices,
            source={
                "kind": "HUMAN_USER_PDF_TRANSCRIPTION_RESEARCH_ONLY",
                "pdf_sha256": SOURCE_PDF_SHA, "time": PDF_CAPTURED_UTC,
                "not_canonical_pdf_first_snapshot": True,
            })
        out["p2"] = result
        out["status"] = "RESEARCH_THREE_ENGINE_COMPARISON_COMPLETE_NOT_CANONICAL_PDF_SEAL"
        out["warning"] = "P2 descriptive only: original user PDF bytes are not on runner"
    except Exception as exc:
        out.update(status="P2_COMPARISON_BLOCKED",
                   block_reason=f"{type(exc).__name__}:{exc}"[:260])
    return out


def main():
    verify_active_policy(ROOT)
    for src, correct in ((HISTORY,
                         "637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89"),
                         (BASELINE,
                         "35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1")):
        got = hashlib.sha256(src.read_bytes()).hexdigest()
        if got != correct:
            raise RuntimeError("HISTORICAL_SHA_MISMATCH:" + str(src))
    report = {
        "schema": "NOV22_REAL_TFF_MODEL_P0_P1_P2_RESEARCH_PROBE_V1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_user_pdf_sha256": SOURCE_PDF_SHA,
        "source_pdf_bytes_accessible_on_runner": False,
        "not_an_approved_first_pdf_seal": True,
        "results": [],
    }
    try:
        for home, away, hour, odds in CASES:
            result = entry(home, away, hour, odds)
            report["results"].append(result)
            print("THREE_MACHINE_ROW", json.dumps({
                "fixture": result["fixture"],
                "status": result["status"],
                "reason": result.get("block_reason"),
                "model": result.get("model_decision"),
                "p2": result.get("p2", {}).get("status"),
            }, ensure_ascii=False), flush=True)
    finally:
        path = Path("/tmp/nov22_three_machine_probe.json")
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        print("FULL_REPORT_JSON", str(path), flush=True)
        print("FINAL_COUNT", json.dumps({
            "attempted": len(report["results"]),
            "three_model_complete": sum("COMPARISON_COMPLETE" in r["status"] for r in report["results"]),
            "blocked": [r["fixture"] + ":" + r["status"] for r in report["results"] if "COMPARISON_COMPLETE" not in r["status"]],
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
