"""Fifth *reference* (bookmaker prices), NOT a fifth trained model or betting signal.

Read-only, post-result, paired scoring of a stored 4-model pre-kickoff forecast
against a manually attested full-market odds snapshot from the SAME fixture.
Live source retrieval and GitHub commit-time verification are NOT implemented.
The output is descriptive and never grants S2, A/B/C or model promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from classification_odds_263 import GROUPS, canonical_markets
from forward_c3 import canonical_bytes, read_aware
from forward_quad import SCHEMA as FORECAST_SCHEMA
from market_benchmark_263 import compare

SCHEMA = "263_fifth_market_baseline_postmatch_v1"
OBSERVATION_SCHEMA = "263_manual_market_snapshot_v1"
GROUP_ORDER = ("MS", "KG", "GOALS_1.5", "GOALS_2.5", "GOALS_3.5")
MODELS = ("B", "C2", "C3", "M4")
POSITIVE = {
    "KG": "BTTS_YES",
    "GOALS_1.5": "OVER_1.5",
    "GOALS_2.5": "OVER_2.5",
    "GOALS_3.5": "OVER_3.5",
}
GOAL_TOTAL_MINIMUM = {"GOALS_1.5": 2, "GOALS_2.5": 3, "GOALS_3.5": 4}


def sealed_payload(data: dict, expected_schema: str) -> str:
    if not isinstance(data, dict) or data.get("schema") != expected_schema:
        raise ValueError("SCHEMA_MISMATCH")
    original = dict(data)
    fingerprint = original.pop("payload_sha256", None)
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise ValueError("SEALED_SHA_MISSING")
    if hashlib.sha256(canonical_bytes(original)).hexdigest() != fingerprint:
        raise ValueError("SEALED_SHA_TAMPERED")
    return fingerprint


def fixture_key(fixture: dict) -> str:
    return ":".join((fixture["league"], fixture["home_id"], fixture["away_id"],
                     fixture["match_local_date"]))


def _score(prob: dict, group: str, selected: str) -> dict:
    keys = GROUPS[group]
    if set(prob) != set(keys):
        raise ValueError("PROBABILITY_MARKET_SHAPE")
    p = {k: float(prob[k]) for k in keys}
    if not all(math.isfinite(v) and 0 <= v <= 1 for v in p.values()):
        raise ValueError("INVALID_MARKET_PROBABILITY")
    if abs(sum(p.values()) - 1) > 1e-8:
        raise ValueError("UNNORMALIZED_PROBABILITY")
    if group == "MS":
        brier = sum((p[k] - int(k == selected)) ** 2 for k in keys)
    else:
        pos = POSITIVE[group]
        brier = (p[pos] - int(selected == pos)) ** 2
    best = max(keys, key=lambda k: p[k])
    return {"logloss": -math.log(max(0.001, p[selected])),
            "brier": brier, "top1_correct": int(best == selected)}


def _result_side(result: dict, group: str) -> str:
    a, b = result["home_goals"], result["away_goals"]
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in (a, b)):
        raise ValueError("INVALID_FINAL_SCORE")
    if group == "MS":
        return "MS1" if a > b else "MSX" if a == b else "MS2"
    if group == "KG":
        return "BTTS_YES" if a > 0 and b > 0 else "BTTS_NO"
    if group not in GOAL_TOTAL_MINIMUM:
        raise ValueError("UNSUPPORTED_GOALS_GROUP")
    line = group.removeprefix("GOALS_")
    return ("OVER_" if a + b >= GOAL_TOTAL_MINIMUM[group] else "UNDER_") + line


def _same_source_quote(q: dict, obs: dict) -> None:
    if not isinstance(q, dict):
        raise ValueError("MALFORMED_QUOTE")
    if q.get("source") != obs["source_domain"]:
        raise ValueError("BOOKMAKER_DOMAIN_MISMATCH")
    u = urlparse(str(q.get("source_url", "")))
    host = str(u.hostname or "").lower().removeprefix("www.")
    if u.scheme != "https" or host != obs["source_domain"] or u.username or u.password:
        raise ValueError("URL_SOURCE_DOMAIN_MISMATCH")


def evaluate_pair(*, forecast: dict, observation: dict, final: dict, asof: str) -> dict:
    forecast_sha = sealed_payload(forecast, FORECAST_SCHEMA)
    obs_sha = sealed_payload(observation, OBSERVATION_SCHEMA)
    fixture = forecast["fixture"]
    ko = read_aware(fixture["kickoff_utc"])
    created = read_aware(forecast["created_at_utc"])
    verified = read_aware(fixture["source_checked_at_utc"])
    now = read_aware(asof)
    if fixture.get("fixture_verification") != "VERIFIED_BY_LIVE_OFFICIAL_GATE":
        raise ValueError("OFFICIAL_FIXTURE_GATE_MISSING")
    if not verified <= created < ko < now:
        raise ValueError("FORECAST_NOT_BEFORE_KICKOFF_OR_RESULT_TOO_EARLY")
    if observation.get("forecast_payload_sha256") != forecast_sha:
        raise ValueError("ODDS_LINKED_TO_WRONG_FORECAST")
    key = fixture_key(fixture)
    if observation.get("fixture_key") != key:
        raise ValueError("ODDS_FIXTURE_IDENTITY_MISMATCH")
    review = observation.get("source_review")
    if (not isinstance(review, dict) or review.get("method") != "MANUAL_PUBLIC_PAGE"
            or not isinstance(review.get("reviewer"), str) or not review["reviewer"].strip()):
        raise ValueError("HUMAN_SOURCE_ATTESTATION_REQUIRED")
    if not isinstance(observation.get("source_domain"), str):
        raise ValueError("SOURCE_DOMAIN_REQUIRED")
    analysis = read_aware(observation["analysis_at_utc"])
    inspected = read_aware(review["reviewed_at_utc"])
    if not created <= inspected <= analysis < ko:
        raise ValueError("ODDS_SOURCE_INSPECTION_OUTSIDE_PREMATCH")
    finalized = read_aware(final["finalized_at_utc"])
    if not ko < finalized <= now:
        raise ValueError("RESULT_NOT_POSTMATCH")
    url = urlparse(str(final.get("source_url", "")))
    if url.scheme != "https" or not url.hostname:
        raise ValueError("FINAL_SCORE_SOURCE_MISSING")
    if set(forecast.get("model_predictions", {})) != set(MODELS):
        raise ValueError("FOUR_MODEL_FIELDS_REQUIRED")

    groups = {}
    for group in GROUP_ORDER:
        q = observation.get("quotes", {}).get(group)
        if q is None:
            groups[group] = {"status": "NO_SNAPSHOT_FOR_THIS_MARKET"}
            continue
        _same_source_quote(q, observation)
        if q.get("market_group") != group:
            raise ValueError("QUOTE_LINE_OR_GROUP_MISMATCH")
        benchmark = compare(models=forecast["model_predictions"], quote=q,
                            fixture_key=key, kickoff=ko.isoformat(), now=analysis.isoformat())
        if benchmark["status"] != "DESCRIPTIVE_ONLY_NOT_MODEL_SELECTION":
            groups[group] = {"status": "NO_COMPLETE_FRESH_QUOTE",
                             "reason": benchmark.get("reason")}
            continue
        selection = _result_side(final, group)
        market_p = benchmark["no_vig_probabilities"]
        rows = {"MARKET": _score(market_p, group, selection)}
        for name in MODELS:
            record = forecast["model_predictions"][name]
            if record["status"] != "AVAILABLE":
                continue
            allp = canonical_markets(record["goals"]["markets"])
            rows[name] = _score({k: allp[k] for k in GROUPS[group]}, group, selection)
        groups[group] = {
            "status": "DESCRIPTIVE_MATCHED_PAIR_NOT_LIVE_VERIFIED",
            "actual_selection": selection,
            "market_margin": benchmark["market_margin"],
            "no_vig": market_p,
            "observed_prices": benchmark["observed_prices"],
            "scores": rows,
            "source_url": benchmark["source_url"],
            "source_checked_at_utc": benchmark["checked_at_utc"],
        }
    return {
        "schema": "263_market_versus_quad_pair_v1",
        "status": "POSTMATCH_DESCRIPTIVE_ONLY",
        "fixture_key": key, "kickoff_utc": ko.isoformat(),
        "source_domain": observation["source_domain"],
        "forecast_sha256": forecast_sha, "observation_sha256": obs_sha,
        "groups": groups,
        "manual_observation_not_proof_of_bookmaker_quote": True,
        "git_commit_before_kickoff_not_verified_by_this_module": True,
        "official_result_url_not_independently_checked_by_this_module": True,
        "S1_S2_approved": False, "official_A_B_C": None,
        "betting_authorized": False, "model_promoted": None,
    }


def summarize(pairs: list[dict]) -> dict:
    result = {"schema": SCHEMA, "status": "DESCRIPTIVE_ONLY_NO_LIVE_GIT_PROOF",
              "pairs_evaluated": len(pairs), "markets": {}, "pair_details": pairs,
              "recommended": False, "betting_authorized": False, "model_promoted": None}
    for group in GROUP_ORDER:
        matched = [x["groups"][group] for x in pairs
                   if x["groups"][group]["status"] == "DESCRIPTIVE_MATCHED_PAIR_NOT_LIVE_VERIFIED"]
        stats = {}
        for name in ("MARKET",) + MODELS:
            rows = [x["scores"][name] for x in matched if name in x["scores"]]
            stats[name] = {
                "n": len(rows),
                "mean_logloss": sum(r["logloss"] for r in rows) / len(rows) if rows else None,
                "mean_brier": sum(r["brier"] for r in rows) / len(rows) if rows else None,
                "top1_accuracy": sum(r["top1_correct"] for r in rows) / len(rows) if rows else None,
            }
        comparison = {}
        for name in MODELS:
            available = [x for x in matched if name in x["scores"]]
            comparison[name] = {
                "matched_n": len(available),
                "market_minus_model_logloss": (
                    sum(x["scores"]["MARKET"]["logloss"]-x["scores"][name]["logloss"]
                        for x in available)/len(available) if available else None),
                "market_minus_model_brier": (
                    sum(x["scores"]["MARKET"]["brier"]-x["scores"][name]["brier"]
                        for x in available)/len(available) if available else None),
            }
        result["markets"][group] = {"quotes_complete_n": len(matched),
                                    "quotes_missing_or_blocked_n": len(pairs)-len(matched),
                                    "scores": stats, "same_match_comparison": comparison}
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, help="JSON with entries: forecast_path, observation_path, final")
    ap.add_argument("--out", required=True)
    ap.add_argument("--asof", default=datetime.now(timezone.utc).isoformat())
    a = ap.parse_args()
    manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    if manifest.get("schema") != "263_market_versus_quad_manifest_v1" or not isinstance(manifest.get("entries"), list):
        raise ValueError("INVALID_MANIFEST")
    result = []
    seen = set()
    for row in manifest["entries"]:
        f = json.loads(Path(row["forecast_path"]).read_text(encoding="utf-8"))
        o = json.loads(Path(row["observation_path"]).read_text(encoding="utf-8"))
        pair = evaluate_pair(forecast=f, observation=o, final=row["final"], asof=a.asof)
        if pair["fixture_key"] in seen:
            raise ValueError("DUPLICATE_MARKET_FIXTURE")
        seen.add(pair["fixture_key"])
        result.append(pair)
    output = summarize(result)
    with Path(a.out).open("x", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        file.write("\n")
    print(json.dumps({"status": output["status"], "n": output["pairs_evaluated"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
