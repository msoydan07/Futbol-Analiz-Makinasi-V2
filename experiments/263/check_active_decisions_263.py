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
    "fixed_market_experts":"D-EXPERT-20261121",
    "model_selection":"D-MARKET-007",
    "pdf_sequence":"D-ODDS-001",
    "exclusive_odds_source":"D-ODDS-SOURCE-20261120",
    "c3_calibration":"D-C3-CAL-011",
    "reporting_and_seals":"D-OPER-006",
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
    # The original highest-realization objective is in the normal selector,
    # never in a separate ninth policy topic.
    _require(len(active)==8,"ORIGINAL_EIGHT_POLICY_TOPICS_REQUIRED")
    _require("gerceklesme ihtimali en yuksek tahmini" in by_topic["model_selection"]["rule"],
             "ORIGINAL_MACHINE_OBJECTIVE_MISSING")
    _require((root/"experiments/263/historical_probability_reliability_263.py").is_file()
             and (root/"experiments/263/normal_historical_reference_263.py").is_file(),
             "NORMAL_PREMATCH_HISTORY_MODULES_MISSING")
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
    active_lock_rel="experiments/263/model_first_selection_lock_20261121_v4.json"
    _require(paths.get("model_selection_lock")==active_lock_rel,
             "NORMAL_SELECTION_LOCK_NOT_ACTIVE")
    lock=json.loads((root/active_lock_rel).read_text(encoding="utf-8"))
    _require("min_probability" not in lock and "min_lift" not in lock,
             "ARBITRARY_PROBABILITY_OR_LIFT_GATE_RETURNED")
    _require(lock.get("historical_reference",{}).get("ranking")=="DIAGNOSTIC_ONLY_NOT_USED_FOR_V4_CALIBRATED_MARKET_SELECTION"
             and lock.get("historical_reference",{}).get("price_influence") is False,
             "V4_MUST_NOT_MIX_RAW_39_SHA_INTO_CALIBRATED_RANKING")
    # The research-selected C3 transformation is a new versioned decision
    # policy, never a silent mutation of the original v3 lock.
    from model_first_decision_263 import digest
    _require(lock.get("payload_sha256")==digest({k:v for k,v in lock.items() if k!="payload_sha256"}),
             "V4_MODEL_LOCK_SHA_INVALID")
    _require((root/"experiments/263/model_first_selection_lock_20261120_normal_v3.json").is_file(),
             "V3_REPLAY_LOCK_REMOVED")
    calibration=lock.get("calibration_v4")
    # Read source from this root rather than importing active installation,
    # so temporary-copy negative tests also fail closed.
    calibration_path=paths.get("c3_binary_calibrator")
    _require(calibration_path=="experiments/263/model_first_frozen_c3_calibration_263.py",
             "V4_CALIBRATION_ROUTE_CHANGED")
    module_source=(root/calibration_path).read_text(encoding="utf-8")
    _require("def calibrated_binary_pair(" in module_source and "TRAIN_N = 2898" in module_source,
             "V4_C3_CALIBRATION_IMPLEMENTATION_MISSING")
    _require(isinstance(calibration,dict) and calibration.get("train_n")==2898
             and calibration.get("method")=="C3_2025_26_TWO_BINARY_LOGIT_FROZEN_V1"
             and calibration.get("train_season")=="2025-2026"
             and calibration.get("odds_not_used") is True,
             "V4_BINARY_CALIBRATION_LOCK_MISSING")
    _require(calibration.get("coefficients")=={
        "BTTS_YES":{"intercept":0.120946,"c3_logit":0.2643173,
                    "previous_league_logit":0.5012377},
        "OVER_2.5":{"intercept":0.1100003,"c3_logit":0.2639998,
                    "previous_league_logit":0.2514675}},
        "V4_COEFFICIENTS_UNEXPECTED")
    _require(active_lock_rel in one and active_lock_rel in bridge,
             "V4_PDF_ROUTE_NOT_ACTIVE")
    morning=(root/"experiments/263/sabah_batch_263.py").read_text(encoding="utf-8")
    _require(active_lock_rel in morning,"V4_MORNING_ROUTE_NOT_ACTIVE")

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
    # The user-approved 21-Nov card report is canonical for BOTH first-iddaa
    # and new100-model-only output; no silent fallback to old batch tables.
    approved="experiments/263/iddaa_pdf_approved_layout_263.py"
    new100_batch="experiments/263/sabah_mobile_model_only_263.py"
    spec="docs/263_TOPLU_RAPOR_KALICI_KART_SABLONU_20261121.md"
    _require(paths.get("approved_batch_card_pdf")==approved
             and paths.get("approved_model_only_batch_route")==new100_batch
             and paths.get("approved_batch_spec")==spec,
             "USER_APPROVED_BATCH_CARD_ROUTE_MISSING")
    _require("KALICI TOPLU RAPOR" in by_topic["reporting_and_seals"]["rule"],
             "USER_APPROVED_LAYOUT_DECISION_MISSING")
    layout=(root/approved).read_text(encoding="utf-8")
    model_only=(root/new100_batch).read_text(encoding="utf-8")
    _require((root/spec).is_file() and
             "def _draw_grouped_cards(" in layout and
             "def render_model_only_batch(" in layout and
             "return _draw_grouped_cards(grouped,target,model_only=True)" in layout and
             "render_model_only_batch(report[\"day_turkey\"],rows,folder/\"toplu.pdf\")" in model_only and
             "batch_pdf(folder/\"toplu.pdf\"" not in model_only,
             "USER_APPROVED_BATCH_RENDERER_NOT_ACTIVE")
    # Second user PDF MUST return the same four-box single design, bundled
    # one full page per match. The old review.pdf is audit-only.
    single_spec="docs/263_IKINCI_PDF_TEKLI_RAPOR_KALICI_SABLON_20261121.md"
    single_renderer="experiments/263/iddaa_pdf_approved_layout_263.py"
    second_route="experiments/263/iddaa_pdf_last_review_263.py"
    _require(paths.get("approved_single_review_pdf")==single_renderer and
             paths.get("approved_single_review_spec")==single_spec and
             paths.get("second_pdf_only_review")==second_route and
             (root/single_spec).is_file(),
             "USER_APPROVED_SECOND_PDF_SINGLE_SPEC_MISSING")
    _require("İKİNCİ İDDAA PDF RAPORU KALICI" in by_topic["reporting_and_seals"]["rule"],
             "SECOND_PDF_LAYOUT_POLICY_NOT_LOCKED")
    second=(root/second_route).read_text(encoding="utf-8")
    _require("from iddaa_pdf_approved_layout_263 import render_singles as approved_single_pdfs" in second and
             'singles=approved_single_pdfs(review,target/"tekli",bundle_pdf=target/"tekli_rapor.pdf")' in second and
             '"pdf_report":str(target/"tekli_rapor.pdf")' in second and
             '"pdf_report":str(target/"review.pdf")' not in second,
             "SECOND_PDF_MUST_RETURN_APPROVED_SINGLE_BUNDLE")
    _require("def _draw_approved_single_page(" in layout and
             "def render_singles(review,target_dir,bundle_pdf=None):" in layout and
             "combined.save()" in layout and
             "_draw_approved_single_page(combined,r,i,len(ready))" in layout,
             "SECOND_PDF_APPROVED_RENDERER_BUNDLE_MISSING")
    # Append-only after-second-PDF historical research records are mandatory;
    # raw user PDFs remain outside the public GitHub repository.
    arc="experiments/263/second_pdf_commentary_archive_263.py"
    arc_spec="docs/263_IKINCI_PDF_ORAN_YORUM_ARSIV_KARARI_20261121.md"
    _require(paths.get("second_pdf_archive")==arc and
             paths.get("second_pdf_archive_spec")==arc_spec and
             (root/arc_spec).is_file(),
             "SECOND_PDF_ARCHIVE_POLICY_FILES_MISSING")
    archive_source=(root/arc).read_text(encoding="utf-8")
    _require("D-SECOND-ARCHIVE-001" in by_topic["pdf_sequence"]["rule"] and
             "def append_review_archive(" in archive_source and
             "SECOND_PDF_ARCHIVE_ALREADY_EXISTS_DIFFERENT" in archive_source and
             "raw_pdfs_committed_to_github" in archive_source,
             "SECOND_PDF_IMMUTABLE_ARCHIVE_NOT_ENFORCED")
    _require("from second_pdf_commentary_archive_263 import append_review_archive" in second and
             "archived=append_review_archive(report," in second and
             "archived=append_review_archive(review," in second and
             '"second_pdf_archive_files":archived["files"]' in second,
             "SECOND_PDF_ARCHIVE_NOT_ATTACHED_TO_BOTH_REVIEW_ROUTES")
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
