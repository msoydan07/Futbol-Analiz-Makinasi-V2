"""Readiness for PRIVATE xG and conservative 2.5 market promotion gate.

This checks *only* a private locally mounted xG file and emits metadata.
It cannot copy ChatGPT Library bytes into GitHub Actions or create secrets.
Existing signed M4 forecasts, odds, and decision engine remain unchanged.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

EXPECTED_SHA = "3b13921daafab70aa121fe807fea0a74e0c72f0fc2381366b183f621edea762c"
TEN = frozenset(("ENG1", "ENG2", "GER1", "ESP1", "ITA1",
                 "FRA1", "NED1", "TUR1", "POR1", "BEL1"))
REQUIRED = frozenset(("fixture_id", "league", "date", "home_id", "away_id",
                      "home_goals", "away_goals", "home_xg", "away_xg",
                      "xg_source", "source_status"))
SCHEMA = "263_PRIVATE_XG_LOCAL_READINESS_V1"


def _hash_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def private_data_preflight(path, checkout, expected_sha=EXPECTED_SHA, expected_n=4618):
    """Never emit individual provider values or raw rows to logs or public JSON."""
    source = Path(path).resolve()
    public_root = Path(checkout).resolve()
    if source.is_relative_to(public_root):
        raise ValueError("XG_INSIDE_PUBLIC_CHECKOUT_FORBIDDEN")
    if not source.is_file():
        return {"schema": SCHEMA, "status": "PRIVATE_XG_NOT_AVAILABLE",
                "m4_unchanged": True, "github_actions_ready": False}
    if _hash_file(source) != expected_sha:
        return {"schema": SCHEMA, "status": "PRIVATE_XG_SHA_MISMATCH",
                "m4_unchanged": True, "github_actions_ready": False}
    league_count = {}
    seen = set()
    with source.open(encoding="utf-8-sig", newline="") as f:
        rdr = csv.DictReader(f)
        if not REQUIRED.issubset(rdr.fieldnames or ()):
            raise ValueError("PRIVATE_XG_COLUMNS_MISSING")
        for r in rdr:
            fid = r["fixture_id"]
            if not fid or fid in seen:
                raise ValueError("PRIVATE_XG_DUPLICATE_FIXTURE")
            seen.add(fid)
            league = r["league"]
            if league not in TEN:
                raise ValueError("PRIVATE_XG_OUTSIDE_TEN_LEAGUES")
            league_count[league] = league_count.get(league, 0) + 1
            if not r["date"] or not r["home_id"] or not r["away_id"]:
                raise ValueError("PRIVATE_XG_MISSING_IDENTITY")
            for key in ("home_xg", "away_xg"):
                try:
                    v = float(r[key])
                except (TypeError, ValueError) as exc:
                    raise ValueError("PRIVATE_XG_INVALID_NUMBER") from exc
                if not math.isfinite(v) or not 0 <= v <= 9:
                    raise ValueError("PRIVATE_XG_OUT_OF_RANGE")
    if len(seen) != expected_n or set(league_count) != TEN:
        return {"schema": SCHEMA, "status": "PRIVATE_XG_SCOPE_MISMATCH",
                "m4_unchanged": True, "github_actions_ready": False,
                "record_count": len(seen), "league_count": len(league_count)}
    return {"schema": SCHEMA, "status": "PRIVATE_XG_READABLE_IN_CHATGPT_ENVIRONMENT",
            "dataset_sha256": expected_sha, "record_count": len(seen),
            "league_count": len(league_count),
            "raw_xg_values_in_report": False, "m4_unchanged": True,
            "github_actions_ready": False,
            "reason": "GitHub Actions cannot access ChatGPT Library; separate authorized secure transfer required."}


def promotion_gate(calibration, *, historical_score_source_independently_verified=False,
                   provider_vintage_asof_verified=False, rights_verified=False,
                   new_unseen_prematch_evaluation=False):
    """An explicit fail-closed quality/rights gate, never modifies M4.

    Thresholds are conservative operational criteria, not tuned post-hoc for
    the selected dataset: <3 percentage-point global mean bias and <5 pp ECE.
    """
    if calibration.get("schema") != "263_xg_1083_calibration_audit_v1":
        raise ValueError("CALIBRATION_PROVENANCE_INVALID")
    a = calibration["details"]["M4_PLUS_XG"]
    n = int(calibration["n"])
    reasons = []
    if n != 1083 or calibration.get("source_sha256") != EXPECTED_SHA:
        reasons.append("AUDIT_DATA_MISMATCH")
    mean_bias = abs(a["actual_rate"] - a["mean_p"])
    if mean_bias > .03:
        reasons.append("GOAL_2_5_MEAN_CALIBRATION_BIAS_TOO_LARGE")
    if a["ece_10"] > .05:
        reasons.append("GOAL_2_5_BUCKET_RELIABILITY_NOT_YET_STRONG")
    checks = {
        "independent_score_source": historical_score_source_independently_verified,
        "provider_pre_match_vintage": provider_vintage_asof_verified,
        "provider_usage_rights": rights_verified,
        "genuinely_unseen_prematch_evaluation": new_unseen_prematch_evaluation,
    }
    for key, ok in checks.items():
        if not ok:
            reasons.append("NOT_VERIFIED_" + key.upper())
    return {
        "schema": "263_M4_XG_PRODUCTION_PROMOTION_GATE_V1",
        "status": "HOLD_KEEP_M4_OFFICIAL_UNCHANGED" if reasons else "ALL_GATES_PASSED_REVIEW_REQUIRED",
        "reasons": reasons,
        "over25_brier_m4": calibration["details"]["M4"]["brier"],
        "over25_brier_xg": a["brier"],
        "over25_ece_xg": a["ece_10"],
        "over25_mean_probability": a["mean_p"],
        "over25_realized_frequency": a["actual_rate"],
        "official_m4_modified": False,
        "existing_sha_predictions_modified": False,
        "betting_authorized": False,
    }


def main():
    p = argparse.ArgumentParser(description="PRIVATE local xG preflight / independent M4 promotion decision")
    p.add_argument("--xg", required=True, help="Private file path, outside GitHub checkout")
    p.add_argument("--public-repo", default=".")
    p.add_argument("--calibration-json", help="Optional audited 1083-game calibration report")
    args = p.parse_args()
    out = {"private_input": private_data_preflight(args.xg, args.public_repo)}
    if args.calibration_json:
        out["production_gate"] = promotion_gate(json.loads(
            Path(args.calibration_json).read_text(encoding="utf-8")))
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
