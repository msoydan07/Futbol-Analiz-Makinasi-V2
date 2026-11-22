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


def _align(decision: dict, prices: dict, *, source: dict,
           unquoted_market_keys: tuple[str, ...] = ()) -> dict:
    """Compare TWO INDEPENDENT seven-outcome winners; never select by the other.

    Gate 1: independently selected event codes identical?
    Gate 2: ONLY IF gate 1 passes, are their OWN highest percentages close?
    The provisional 5 percentage-point threshold is not result-calibrated.
    """
    model_top_choice, model_top_probability = _validate_decision(decision)
    p0 = _p0_from_prices(prices)
    if (len(set(unquoted_market_keys)) != len(unquoted_market_keys)
        or any(key not in CHOICE_FAMILIES for key in unquoted_market_keys)
        or any(key in p0.get(CHOICE_FAMILIES[key], {}) for key in unquoted_market_keys)):
        raise AlignmentError("UNQUOTED_MARKET_CONTRADICTS_COMPLETE_PRICES")

    all_seven_available = set(p0) == set(MARKETS)
    # This P0 selection is made from all P0 odds independently; it does NOT
    # accept the original model's pick as an input.
    market_top = best_choices(p0)["main"] if all_seven_available else None
    same_choice = (model_top_choice == market_top["choice"]
                   if market_top is not None else None)
    signed_gap = (100 * (model_top_probability - market_top["probability"])
                  if same_choice is True else None)
    absolute_gap = abs(signed_gap) if signed_gap is not None else None
    near = (absolute_gap <= 5.0 if absolute_gap is not None else None)
    sensitivity = ({
        str(int(w)): ("UYUMLU" if absolute_gap <= w else "YUZDELER_UZAK")
        for w in PROVISIONAL_WINDOWS_PP
    } if same_choice is True else {})

    if not all_seven_available:
        status = ("MODEL_TOP_CHOICE_NOT_OFFERED_IN_PDF"
                  if model_top_choice in unquoted_market_keys
                  else "P0_SEVEN_MARKETS_INCOMPLETE")
    elif same_choice is False:
        status = "TERCIHLER_FARKLI"
    elif near is False:
        status = "YUZDELER_UZAK"
    else:
        status = "UYUMLU"

    return {
        "schema": SCHEMA,
        "source": source,
        "model_decision_sha256": decision["payload_sha256"],
        "forecast_sha256": decision["forecast_sha256"],
        # Each engine has exactly ONE independently decided highest outcome.
        "model_choice": model_top_choice,
        "model_probability": model_top_probability,
        "p0_highest_choice": market_top["choice"] if market_top else None,
        "p0_highest_probability": market_top["probability"] if market_top else None,
        "p0_highest_is_global": all_seven_available,
        "p0_probabilities": p0,
        "missing_complete_market_groups": sorted(set(MARKETS) - set(p0)),
        "unquoted_pdf_selections": list(unquoted_market_keys),
        # Explicit two gates. None means NOT EVALUATED, not a negative vote.
        "condition_1_same_top_choice": same_choice,
        "condition_2_top_probabilities_close": near,
        "p0_main_choice_matches": same_choice,
        # A gap between DIFFERENT events is meaningless for agreement: NULL.
        "signed_gap_pp": signed_gap,
        "absolute_gap_pp": absolute_gap,
        "window_sensitivity": sensitivity,
        "threshold_pp": 5.0,
        "threshold_validated": False,
        "status": status,
        "no_new_probability": True,
        "main_decision_changed": False,
        "meaning": "TWO_INDEPENDENT_TOPS_AND_TWO_CONDITIONS_NOT_FORECAST_ACCURACY",
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
    unquoted = snapshot.get("not_offered_pdf_market_keys", [])
    raw_partial = snapshot.get("partial_quoted_prices_no_no_vig", {})
    if (not isinstance(unquoted, list) or
        any(not isinstance(x, str) for x in unquoted) or
        len(unquoted) != len(set(unquoted)) or
        any(x not in CHOICE_FAMILIES for x in unquoted)):
        raise AlignmentError("PDF_UNQUOTED_MARKET_KEYS_INVALID")
    if (not isinstance(raw_partial, dict) or
        not set(raw_partial).issubset(GROUP_NAMES)):
        raise AlignmentError("INVALID_PARTIAL_QUOTES")
    for label, pairs in raw_partial.items():
        canonical_group = GROUP_NAMES[label]
        if (label in groups or not isinstance(pairs, dict) or
            not set(pairs).issubset(MARKETS[canonical_group]) or
            len(pairs) == len(MARKETS[canonical_group]) or
            any(not isinstance(x, (float,int)) or isinstance(x,bool)
                or not math.isfinite(x) or x <= 1 for x in pairs.values()) or
            any(key in unquoted for key in pairs)):
            raise AlignmentError("PARTIAL_QUOTES_INCONSISTENT")
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
    if (any(choice in prices.get(CHOICE_FAMILIES[choice], {}) for choice in unquoted)
        or any(choice not in [key for g in raw_partial.values() for key in g]
               and CHOICE_FAMILIES[choice] in [GROUP_NAMES[k] for k in groups]
               for choice in unquoted)):
        raise AlignmentError("UNQUOTED_PDF_KEYS_CONTRADICT_COMPLETE_GROUP")
    result = _align(decision, prices, unquoted_market_keys=tuple(unquoted), source={
        "kind": "SHA_LINKED_ORIGINAL_USER_IDDAA_FIRST_PDF",
        "source_pdf_sha256": pdf_sha, "snapshot_sha256": snapshot["payload_sha256"],
        "independently_download_verified": False,
        "first_pdf_observed_at_utc": observed.isoformat(),
    })
    result["partially_quoted_unpriced_families"] = raw_partial
    return result


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
