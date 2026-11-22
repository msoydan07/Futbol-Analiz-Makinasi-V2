"""P2 — read-only P0 vs frozen M4/C3 *agreement auditor*, never an ensemble.

P0: proportional no-vig in EACH complete market. P1 remains a separate
market-price re-expression. P2 creates NO new event probability, refuses
future/post-kickoff odds for live analysis, and never alters the signed decision.

The 5 percentage-point window is observational and NOT outcome-calibrated.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path

from p1_market import MARKETS, MarketDataError, _sha_json, archive_record_to_input, \
    best_choices, no_vig, analyze_prices

SCHEMA = "P2_MARKET_MODEL_AGREEMENT_RESEARCH_V1"
DECISION_SCHEMA = "263_MODEL_FIRST_FOUR_MODEL_DECISION_RESEARCH_V2"
PDF_SCHEMA = "263_iddaa_pdf_first_sha_price_v1"
GROUP_NAMES = {"MS": "MS", "GOALS_2.5": "OU25", "KG": "KG"}
CHOICE_FAMILIES = {choice: g for g, names in MARKETS.items() for choice in names}
PROVISIONAL_WINDOWS_PP = (3.0, 5.0, 7.0)


class AlignmentError(ValueError):
    pass


def _checked_sha(obj: dict, sha_key: str, error: str) -> None:
    if not isinstance(obj, dict):
        raise AlignmentError(error)
    sha = obj.get(sha_key)
    if not isinstance(sha, str) or sha != _sha_json({
            k: v for k, v in obj.items() if k != sha_key}):
        raise AlignmentError(error)


def _aware(s: str) -> datetime:
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("timezone absent")
        return dt
    except (TypeError, ValueError) as exc:
        raise AlignmentError("BAD_SOURCE_TIMESTAMP") from exc


def _validate_decision(decision: dict) -> tuple[str, float]:
    _checked_sha(decision, "payload_sha256", "DECISION_SHA_INVALID")
    if (decision.get("schema") != DECISION_SCHEMA
        or decision.get("price_used_in_decision") is not False
        or decision.get("odds_affected_selection") is not False
        or decision.get("market_prices_not_required_for_model_decision") is not True
        or decision.get("production_modified") is not False
        or decision.get("betting_authorized") is not False
        or decision.get("forecast_unchanged") is not True):
        raise AlignmentError("NOT_INDEPENDENT_FROZEN_MODEL_DECISION")
    fixture = decision.get("fixture", {})
    if fixture.get("fixture_verification") != "VERIFIED_BY_LIVE_OFFICIAL_GATE":
        raise AlignmentError("NOT_OFFICIALLY_VERIFIED_FIXTURE")
    main = decision.get("main_candidate")
    if main is None:
        raise AlignmentError("NO_MODEL_MAIN_CHOICE")
    key = main.get("market")
    value = main.get("calibrated_probability")
    if (key not in CHOICE_FAMILIES or isinstance(value, bool)
        or not isinstance(value, (int, float)) or not math.isfinite(value)
        or not 0 <= value <= 1 or main.get("family") not in
            (CHOICE_FAMILIES[key], "O25" if CHOICE_FAMILIES[key] == "OU25" else CHOICE_FAMILIES[key])):
        raise AlignmentError("INVALID_MODEL_TOP_CHOICE")
    candidates = decision.get("model_market_diagnostics")
    if not isinstance(candidates, list) or len(candidates) != 7:
        raise AlignmentError("INCOMPLETE_MODEL_SEVEN_CHOICES")
    if {x.get("market") for x in candidates} != set(CHOICE_FAMILIES):
        raise AlignmentError("INVALID_MODEL_CHOICE_SET")
    if any((not isinstance(x.get("calibrated_probability"), (float, int))
            or isinstance(x.get("calibrated_probability"), bool)
            or not math.isfinite(x["calibrated_probability"])
            or not 0 <= x["calibrated_probability"] <= 1)
           for x in candidates):
        raise AlignmentError("INVALID_MODEL_DIAGNOSTICS")
    top = max(x["calibrated_probability"] for x in candidates)
    same_event = [x for x in candidates if x["market"] == key]
    if (len(same_event) != 1 or abs(same_event[0]["calibrated_probability"] - value) > 1e-8
        or value < top - 1e-8):
        raise AlignmentError("MODEL_TOP_CHOICE_NOT_FROZEN_MAXIMUM")
    return key, float(value)


def _p0_from_prices(prices: dict) -> dict:
    if not isinstance(prices, dict) or not prices:
        raise AlignmentError("NO_COMPLETE_MARKET")
    p0 = {}
    for group, values in prices.items():
        if group not in MARKETS or not isinstance(values, dict) or set(values) != set(MARKETS[group]):
            raise AlignmentError("INCOMPLETE_OR_WRONG_MARKET_" + str(group))
        result = no_vig(values, "proportional")
        # First-PDF bookmaker odds must have positive, plausible margin.
        if not 0 < result["book_margin"] < .30:
            raise AlignmentError("ODDS_MARGIN_OUT_OF_SCOPE_" + group)
        p0[group] = result["probabilities"]
    return p0


def _align(decision: dict, prices: dict, *, source: dict) -> dict:
    selected, model_prob = _validate_decision(decision)
    p0 = _p0_from_prices(prices)
    family = CHOICE_FAMILIES[selected]
    p0_top = best_choices(p0)["main"] if set(p0) == set(MARKETS) else (
        sorted(((prob, market) for group in p0.values()
                for market, prob in group.items()), reverse=True)[0])
    if isinstance(p0_top, tuple):
        p0_top = {"choice": p0_top[1], "probability": p0_top[0]}
    if family not in p0:
        return {
            "schema": SCHEMA, "source": source, "model_decision_sha256": decision["payload_sha256"],
            "p0_probabilities": p0,
            "forecast_sha256": decision["forecast_sha256"], "model_choice": selected,
            "model_probability": model_prob, "p0_same_choice_probability": None,
            "signed_gap_pp": None, "absolute_gap_pp": None,
            "p0_highest_choice": p0_top["choice"], "p0_highest_probability": p0_top["probability"],
            "p0_highest_is_global": False,
            "p0_main_choice_matches": False, "status": "P0_SAME_MARKET_UNAVAILABLE",
            "window_sensitivity": {}, "no_new_probability": True,
            "main_decision_changed": False, "threshold_validated": False,
        }
    implied = p0[family][selected]
    gap = 100 * (model_prob - implied)
    # A missing OTHER group also makes the seven-event P0 peak unknowable.
    # Display the same-event comparison, but never infer full top-choice agreement.
    if set(p0) != set(MARKETS):
        return {
            "schema": SCHEMA, "source": source, "model_decision_sha256": decision["payload_sha256"],
            "p0_probabilities": p0,
            "forecast_sha256": decision["forecast_sha256"], "model_choice": selected,
            "model_probability": model_prob, "p0_same_choice_probability": implied,
            "signed_gap_pp": gap, "absolute_gap_pp": abs(gap),
            "p0_highest_choice": p0_top["choice"], "p0_highest_probability": p0_top["probability"],
            "p0_highest_is_global": False, "p0_main_choice_matches": False,
            "status": "P0_SEVEN_MARKETS_INCOMPLETE", "window_sensitivity": {},
            "no_new_probability": True, "main_decision_changed": False,
            "threshold_validated": False,
        }
    same_top = p0_top["choice"] == selected
    sensitivity = {
        str(int(w)): "UYUMLU" if same_top and abs(gap) <= w else "UYUMLU_TAHMIN_BULUNAMADI"
        for w in PROVISIONAL_WINDOWS_PP
    }
    return {
        "schema": SCHEMA, "source": source, "model_decision_sha256": decision["payload_sha256"],
        "p0_probabilities": p0,
        "forecast_sha256": decision["forecast_sha256"], "model_choice": selected,
        "model_probability": model_prob, "p0_same_choice_probability": implied,
        "signed_gap_pp": gap, "absolute_gap_pp": abs(gap),
        "p0_highest_choice": p0_top["choice"], "p0_highest_probability": p0_top["probability"],
        "p0_highest_is_global": True,
        "p0_main_choice_matches": same_top,
        "status": sensitivity["5"], "window_sensitivity": sensitivity,
        "threshold_validated": False,
        "no_new_probability": True, "main_decision_changed": False,
        "meaning": "DESCRIPTIVE_AGREEMENT_NOT_HIGHER_ACCURACY_OR_BETTING_EDGE",
    }


def align_first_pdf_snapshot(decision: dict, snapshot: dict) -> dict:
    """Only the SHA-linked iddaa first-PDF snapshot, never later price movements."""
    _validate_decision(decision)
    _checked_sha(snapshot, "payload_sha256", "PDF_SNAPSHOT_SHA_INVALID")
    fx = decision["fixture"]
    expected_key = ":".join((fx["league"], fx["home_id"], fx["away_id"], fx["match_local_date"]))
    if (snapshot.get("schema") != PDF_SCHEMA
        or snapshot.get("source_domain") != "iddaa.com"
        or snapshot.get("human_source_type") != "ORIGINAL_USER_CHROME_PRINT_TO_PDF"
        or snapshot.get("price_age_class") != "ARCHIVED_PDF_PRE_FORECAST"
        or snapshot.get("is_current_live_quote") is not False
        or snapshot.get("network_bookmaker_reverified") is not False
        or snapshot.get("bookmaker_api_calls") != 0
        or snapshot.get("forecast_sha256") != decision["forecast_sha256"]
        or snapshot.get("fixture_key") != expected_key
        or _aware(snapshot.get("kickoff_utc")) != _aware(fx["kickoff_utc"])):
        raise AlignmentError("PDF_FIRST_SOURCE_OR_FIXTURE_JOIN_MISMATCH")
    observed = _aware(snapshot.get("observed_at_utc"))
    created = _aware(snapshot.get("created_after_pdf_forecast_utc"))
    ko = _aware(fx["kickoff_utc"])
    if not observed <= created < ko:
        raise AlignmentError("PRICE_NOT_BEFORE_MODEL_AND_KICKOFF")
    pdf_sha = snapshot.get("source_pdf_sha256")
    if not isinstance(pdf_sha, str) or len(pdf_sha) != 64 or any(c not in "0123456789abcdef" for c in pdf_sha):
        raise AlignmentError("SOURCE_PDF_SHA_MISSING")
    groups = snapshot.get("groups", {})
    if not isinstance(groups, dict) or not set(groups).issubset(GROUP_NAMES):
        raise AlignmentError("INVALID_PDF_MARKET_GROUPS")
    prices = {}
    for group, payload in groups.items():
        category = GROUP_NAMES[group]
        if not isinstance(payload, dict) or not isinstance(payload.get("prices"), dict):
            raise AlignmentError("PDF_MARKET_PRICES_MISSING")
        odds = payload["prices"]
        fair = payload.get("no_vig")
        if not isinstance(fair, dict) or set(fair) != set(odds):
            raise AlignmentError("PDF_FAIR_PROBABILITY_MISSING")
        check = no_vig(odds)["probabilities"]
        if any(isinstance(fair[k], bool) or not isinstance(fair[k], (int, float))
               or not math.isfinite(fair[k]) or abs(fair[k]-check[k]) > 1e-9
               for k in check):
            raise AlignmentError("PDF_FAIR_VALUES_DO_NOT_MATCH_PRICES")
        prices[category] = odds
    return _align(decision, prices, source={
        "kind": "SHA_LINKED_ORIGINAL_USER_IDDAA_FIRST_PDF",
        "source_pdf_sha256": pdf_sha, "snapshot_sha256": snapshot["payload_sha256"],
        "independently_download_verified": False,
        "first_pdf_observed_at_utc": observed.isoformat(),
    })


def align_legacy_archive(decision: dict, archived: dict, archive_name: str) -> dict:
    """Historic descriptive audit ONLY. Transcription is not proof of original PDF."""
    source = archive_record_to_input(archived, archive_name)
    main = archived.get("original_seal", {})
    fx = decision["fixture"]
    if (archived.get("match", {}).get("league") != fx.get("league")
        or archived.get("match", {}).get("date_tr") != fx.get("match_local_date")
        or main.get("decision_sha256") != decision.get("payload_sha256")
        or main.get("forecast_sha256") != decision.get("forecast_sha256")
        or main.get("main_market") != decision.get("main_candidate", {}).get("market")
        or abs(main.get("main_probability", -9) -
               decision.get("main_candidate", {}).get("calibrated_probability", -8)) > 1e-8):
        raise AlignmentError("LEGACY_ARCHIVE_ORIGINAL_SEAL_JOIN_INVALID")
    return _align(decision, source["prices"], source={
        "kind": "RESEARCH_BACKFILL_USER_PDF_TRANSCRIPTION_NOT_LIVE",
        "archive_file": archive_name, "first_pdf_sha256": source["first_pdf_sha256"],
        "original_pdf_bytes_rechecked": False, "cannot_claim_forward_accuracy": True,
    })


def run_archive(repo_root: Path, archive_dir: Path) -> dict:
    """Read only legitimate recorded paths under root; never append or reseal."""
    root = repo_root.resolve()
    results, excluded = [], []
    for file in sorted(archive_dir.glob("*.json")):
        if file.name == "index.json":
            continue
        try:
            archived = json.loads(file.read_text(encoding="utf-8"))
            decision_path = archived.get("original_seal", {}).get("decision_path")
            if not isinstance(decision_path, str):
                raise AlignmentError("DECISION_PATH_MISSING")
            path = (root / decision_path).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise AlignmentError("DECISION_PATH_NOT_FOUND_OR_ESCAPED")
            decision = json.loads(path.read_text(encoding="utf-8"))
            result = align_legacy_archive(decision, archived, file.name)
            results.append({"match": archived["match"], "alignment": result})
        except (ValueError, KeyError, TypeError, OSError, ZeroDivisionError) as exc:
            excluded.append({"file": file.name, "reason": str(exc)})
    return {
        "schema": "P2_ARCHIVE_DESCRIPTIVE_AUDIT_V1",
        "total_records": len(results)+len(excluded),
        "analyzed": len(results), "excluded": excluded, "records": results,
        "threshold_pp": 5.0, "threshold_validated": False,
        "is_readonly_research": True, "no_betting_or_forward_accuracy_claim": True,
    }


def run_signed_session(session: dict, *, include_p1_research: bool = False) -> dict:
    """Observe the existing PDF-first signed session, without changing it.

    Only decision rows already independently built and verified by the 2.6.3
    workflow can be joined. This never generates fresh model decisions.
    """
    _checked_sha(session, "signed_research_session_sha256", "SESSION_SHA_INVALID")
    if (session.get("source_original_pdf_verified_once_locally") is not True
        or session.get("new_bookmaker_network_calls") != 0
        or session.get("pilot_count_changed") is not False
        or session.get("source_bookmaker") != "iddaa.com"):
        raise AlignmentError("NOT_ORIGINAL_SIGNED_IDDAA_FIRST_SESSION")
    records, excluded = [], []
    rows = session.get("rows")
    if not isinstance(rows, list):
        raise AlignmentError("INVALID_SESSION_ROWS")
    for row in rows:
        if not isinstance(row, dict) or (
            "model_first_decision" not in row and "pdf_first_price_snapshot" not in row
        ):
            continue
        try:
            d = row["model_first_decision"]
            snap = row["pdf_first_price_snapshot"]
            alignment = align_first_pdf_snapshot(d, snap)
            if include_p1_research:
                groups = snap.get("groups", {})
                if set(groups) == set(GROUP_NAMES):
                    prices = {GROUP_NAMES[k]: v["prices"] for k, v in groups.items()}
                    p1 = analyze_prices(prices)
                    alignment["p1_price_reexpression_research_only"] = {
                        "probabilities": p1["p1"]["p1_probabilities"],
                        "top_choice": p1["p1_select"]["main"],
                        "not_independent_evidence": True,
                    }
                else:
                    alignment["p1_price_reexpression_research_only"] = {
                        "status": "SEVEN_PRICES_REQUIRED_FOR_P1",
                    }
            records.append({"row_index": row.get("index"), "alignment": alignment})
        except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
            excluded.append({"row_index": row.get("index"), "reason": str(exc)})
    return {
        "schema": "P2_SIGNED_FIRST_PDF_SESSION_RESEARCH_V1",
        "analyzed": len(records), "excluded": excluded, "records": records,
        "threshold_pp": 5.0, "threshold_validated": False,
        "no_new_seals": True, "no_model_selection_changes": True,
        "not_an_accuracy_or_profitability_claim": True,
    }


def cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--archive-dir", type=Path)
    sources.add_argument("--session-file", type=Path)
    parser.add_argument("--include-p1-research", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.archive_dir is not None:
        result = run_archive(args.repo_root, args.archive_dir)
    else:
        session = json.loads(args.session_file.read_text(encoding="utf-8"))
        result = run_signed_session(session, include_p1_research=args.include_p1_research)
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    cli()
