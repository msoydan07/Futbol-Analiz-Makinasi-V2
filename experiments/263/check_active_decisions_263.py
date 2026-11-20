"""Fail-closed guard: 2.6.3 current PDF-first decisions, not an odds/model CI.

Reads the one ACTIVE decision index; checks its single-active-per-topic contract
and key imports/lock selection in the research branch. Does NOT certify live
official fixtures, odds, model accuracy or production readiness.
"""
from __future__ import annotations
import argparse
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/263_AKTIF_KARARLAR.json"
REQUIRED = {
    "league_scope":"D-SCOPE-002",
    "model_math":"D-MODEL-003",
    "fixed_market_experts":"D-EXPERT-20261120",
    "model_selection":"D-MARKET-006",
    "pdf_sequence":"D-ODDS-001",
    "exclusive_odds_source":"D-ODDS-SOURCE-20261120",
    "c3_calibration":"D-C3-CAL-010",
    "reporting_and_seals":"D-OPER-004",
    "historical_probability_reliability":"D-HIST-PROB-20261120",
}
EXPECTED = {"MS":"M4", "KG":"C3", "O25":"C3"}

class ActiveDecisionConflict(RuntimeError):
    pass

def _require(yes, why):
    if not yes:
        raise ActiveDecisionConflict(why)

def verify_active_policy(root=ROOT):
    root = Path(root).resolve()
    path = root / "docs/263_AKTIF_KARARLAR.json"
    p = json.loads(path.read_text(encoding="utf-8"))
    _require(p.get("schema") == "263_ACTIVE_DECISIONS_V1", "POLICY_SCHEMA_UNKNOWN")
    _require(p.get("owner_branch") == "experiment/263-toplu-karsilastirma", "WRONG_POLICY_BRANCH")
    _require(p.get("validation_status",{}).get("real_matchday_end_to_end") == "C_NOT_YET_VERIFIED",
             "UNSUPPORTED_LIVE_SUCCESS_CLAIM")
    active = p.get("active")
    _require(isinstance(active,list), "ACTIVE_DECISIONS_MISSING")
    _require(len(active)==len(REQUIRED),"ACTIVE_COUNT_MISMATCH")
    by_topic={}
    for item in active:
        topic=item.get("topic")
        _require(topic not in by_topic, "DOUBLE_ACTIVE_TOPIC:"+str(topic))
        _require(item.get("status")=="ACTIVE","HISTORICAL_DECISION_USED_AS_ACTIVE:"+str(topic))
        by_topic[topic]=item
    _require({k:v.get("decision_id") for k,v in by_topic.items()}==REQUIRED,
             "ACTIVE_DECISION_ID_CONFLICT")
    _require(by_topic["historical_probability_reliability"].get("implementation_status")==
             "RESEARCH_MODULE_ONLY_NOT_IN_LIVE_SELECTOR",
             "HISTORICAL_RELIABILITY_NOT_YET_LIVE_MUST_BE_EXPLICIT")
    _require((root/"experiments/263/historical_probability_reliability_263.py").is_file(),
             "HISTORICAL_REFERENCE_RESEARCH_MODULE_MISSING")
    paths=p.get("canonical_entrypoints",{})
    _require(paths.get("first_pdf")=="experiments/263/iddaa_pdf_one_step_263.py",
             "FIRST_PDF_ROUTE_CHANGED")
    _require(paths.get("model_first_bridge")=="experiments/263/model_first_iddaa_bridge_263.py",
             "DECISION_BRIDGE_CHANGED")
    _require(paths.get("model_first_selector")=="experiments/263/model_first_decision_263.py",
             "MODEL_SELECTOR_CHANGED")
    one=(root/paths["first_pdf"]).read_text(encoding="utf-8")
    bridge=(root/paths["model_first_bridge"]).read_text(encoding="utf-8")
    selector=(root/paths["model_first_selector"]).read_text(encoding="utf-8")
    _require("from model_first_iddaa_bridge_263 import calibrate_session" in one,
             "OLD_OR_MISSING_FIRST_PDF_DECIDER")
    _require("from iddaa_pdf_value_bridge_263 import calibrate_session" not in one,
             "HISTORICAL_PRICE_DECIDER_REACTIVATED")
    _require("from model_first_decision_263 import select" in bridge,
             "MODEL_FIRST_SELECTION_NOT_CONNECTED")
    mod=ast.parse(selector)
    named={node.name:node for node in mod.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
    _require("select" in named and "market_reference" in named,
             "MODEL_OR_MARKET_STAGE_MISSING")
    args=[arg.arg for arg in named["select"].args.args]
    _require(args==["forecast","baseline","lock"] and
             [arg.arg for arg in named["select"].args.kwonlyargs]==["now"],
             "ODDS_PASSED_TO_MODEL_SELECTION")
    lock=json.loads((root/"experiments/263/model_first_selection_lock_20261120.json").read_text(encoding="utf-8"))
    _require(lock.get("family_anchors")==EXPECTED and
             lock.get("no_odds_input_to_selection") is True and
             lock.get("market_reference_only") is True and
             lock.get("frozen_m4_calibration_only_applies_to_MS") is True,
             "ACTIVE_MARKET_EXPERT_LOCK_CONFLICT")
    m4=(root/paths["m4_engine"]).read_text(encoding="utf-8")
    _require("def predict_m4(" in m4 and "xg" not in m4.lower(),
             "M4_CORE_XG_POLICY_CONFLICT")
    _require(paths.get("new100_price_reference")==
             "experiments/263/iddaa_pdf_one_step_263.py",
             "NON_IDDAA_PRICE_REFERENCE_REACTIVATED")
    workflow=(root/".github/workflows/263-sabah-new100-on-request.yml").read_text(encoding="utf-8")
    # No upstream API quotation or calls on new forecasts. Historical
    # Pinnacle scripts are intentionally retained for audit only.
    for forbidden in ("THE_ODDS_API_KEY", "sabah_pinnacle_capture_263.py",
                      "sabah_pinnacle_new100_bridge_263.py",
                      "pinnacle_new100_research/", "pinnacle_daily_snapshots/"):
        _require(forbidden not in workflow,"AUTO_PRICE_FETCH_REACTIVATED:"+forbidden)
    _require("sabah_mobile_model_only_263.py" in workflow,
             "MODEL_ONLY_MOBILE_PATH_MISSING")
    _require("source_bookmaker" in bridge and "iddaa.com" in bridge,
             "PDF_BOOKMAKER_SOURCE_NOT_EXCLUSIVE")
    historical=p.get("superseded_for_pdf_first",[])
    _require(len(historical)>=2 and all(x.get("status")!="ACTIVE" for x in historical),
             "SUPERSEDED_POLICY_STILL_ACTIVE")
    return {"status":"ACTIVE_DECISIONS_OK", "active_topics":len(active),
            "first_pdf":"MODEL_FIRST", "market":"USER_IDDAA_PDF_ONLY_FIFTH_REFERENCE",
            "m4_xg":"NOT_IN_CORE", "live_acceptance":"NOT_YET_VERIFIED"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=str(ROOT))
    args=ap.parse_args()
    try:
        print(json.dumps(verify_active_policy(args.repo_root),sort_keys=True))
    except (ActiveDecisionConflict,FileNotFoundError,ValueError,KeyError,SyntaxError) as e:
        print(json.dumps({"status":"ACTIVE_DECISIONS_BLOCKED","reason":str(e)}))
        raise SystemExit(2)

if __name__=="__main__":
    main()
