"""Research-only PDF-first bridge: original model SHA -> model decision -> MARKET reference.

Never calls four_model_value_policy_263.decide (EV/odds-driven legacy path).
Never refits B/C2/C3/M4. One original forecast SHA; second PDF only a review.
"""
from __future__ import annotations
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from iddaa_pdf_first_quote_263 import verify_original_pdf, build_snapshot
from iddaa_pdf_value_bridge_263 import _load
from model_first_decision_263 import select, market_reference, digest, verified, EvidenceError, SCHEMA

def calibrate_session(bulletin, session, *, original_pdf, repo_root=".",
                      dev_lock_path="experiments/263/model_first_selection_lock_20261120.json",
                      now=None, session_dir=None):
    sha=verify_original_pdf(original_pdf,bulletin)
    if session.get("pdf_sha256")!=sha or session.get("source_bookmaker")!="iddaa.com":
        raise ValueError("NOT_ORIGINAL_IDDAA_PDF_SESSION")
    lock_path=Path(repo_root)/dev_lock_path
    lock=json.loads(lock_path.read_text(encoding="utf-8"))
    if (lock.get("schema")!="263_MODEL_FIRST_RESEARCH_LOCK_V2"
        or lock.get("payload_sha256")!=digest({k:v for k,v in lock.items() if k!="payload_sha256"})
        or lock.get("officially_approved") is not False):
        raise ValueError("MODEL_FIRST_LOCK_NOT_ACCEPTED")
    out=copy.deepcopy(session)
    success=0;model_pas=0;technical=0
    for r in out.get("rows",[]):
        if r.get("status")!="FOUR_MODELS_FORECAST_SHA_CREATED":
            continue
        try:
            f=_load(repo_root,r["model_forecast_path"],session_dir=session_dir,
                record_kind="forecasts" if session_dir is not None else None)
            b=_load(repo_root,r["empirical_baseline_path"],session_dir=session_dir,
                record_kind="empirical_baselines" if session_dir is not None else None)
            if (r.get("model_forecast_sha256")!=f.get("payload_sha256")
                or r.get("empirical_baseline_sha256")!=b.get("payload_sha256")):
                raise EvidenceError("ROW_FORECAST_BASELINE_SHA_MISMATCH")
            clock=now or datetime.now(timezone.utc)
            if clock.tzinfo is None:raise EvidenceError("CLOCK_MUST_BE_AWARE")
            # MODEL FIRST: the SHA decision is completed before ANY prices
            # are read. Price failures cannot turn a model candidate into PAS,
            # nor a valid model PAS into a technical blockage.
            d=select(f,b,lock,now=clock)
            verified(d,SCHEMA)
            r["model_first_decision"]=d
            r["model_only_decision_status"]=d["status"]
            r["odds_affected_selection"]=False
            # Prices are the separate, signed descriptive fifth reference only.
            # The uploaded PDF SHA must be genuine, but a missing/incomplete
            # price group should never force a fresh model calculation.
            try:
                original_price_snapshot=build_snapshot(bulletin,session,
                    session["rows"][r["index"]],f,verified_pdf_sha=sha)
                trusted_groups={group:{"status":"FULL_MARKET_QUOTE_AVAILABLE",**payload}
                    for group,payload in original_price_snapshot["groups"].items()}
                ref=market_reference(d,trusted_groups,source_pdf_sha256=sha)
                r["pdf_first_price_snapshot"]=original_price_snapshot
            except (OSError,ValueError,KeyError,TypeError,AssertionError) as price_exc:
                ref=market_reference(d,{},source_pdf_sha256=sha)
                r["market_reference_status"]="PRICE_OBSERVATION_UNAVAILABLE_DECISION_UNCHANGED"
                r["market_reference_reason"]=(type(price_exc).__name__+":"+str(price_exc))[:140]
            if (ref["decision_sha256"]!=d["payload_sha256"]
                or ref["forecast_sha256"]!=f["payload_sha256"]):
                raise EvidenceError("MARKET_WRONG_MODEL_DECISION")
            r["market_fifth_reference"]=ref
            success+=1
            if d["main_candidate"] is None:model_pas+=1
        except (OSError,ValueError,KeyError,TypeError,AssertionError,ImportError,AttributeError) as e:
            r["model_only_decision_status"]="TECHNICAL_BLOCKED_NOT_PAS"
            r["model_only_technical_reason"]=(type(e).__name__+":"+str(e))[:180]
            technical+=1
    out["n_pdf_first_decisions"]=success
    out["n_pdf_first_pas_or_blocked"]=model_pas+technical
    out["n_technical_blocked_not_pas"]=technical
    out["iddaa_pdf_first_policy"]="D_MARKET_006_MODEL_FIRST_FIXED_EXPERT_FIFTH_REFERENCE_20261120"
    out["source_original_pdf_verified_once_locally"]=True
    out["pdf_captured_before_forecast_not_current_quote"]=True
    out["new_bookmaker_network_calls"]=0
    out["policy_dev_lock_sha256"]=lock["payload_sha256"]
    out["pilot_count_changed"]=False
    out["signed_research_session_sha256"]=digest(
        {k:v for k,v in out.items() if k!="signed_research_session_sha256"})
    return out
