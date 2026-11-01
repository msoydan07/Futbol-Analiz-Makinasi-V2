"""2.6.3 C3 experimental PRE-MATCH forward journal. Not a betting engine.

The authoritative prediction must be generated before kickoff, from the verified
named-match gate, with strictly earlier dated match results, then committed as an
unmodified file to Git history. Model C3 is frozen from 2026-11-01 research.

Usage from the feature branch (after preparing historical_results.csv):
  python experiments/263/forward_c3.py --league TUR1 --home 'Team A' --away 'Team B' \
    --history data/historical_results.csv --out-dir forward_263
Never supply or infer fixture dates manually. No automatic match selection.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# Only the audit-locked code is importable. Any edit to this file or model
# changes the source hashes recorded with each prediction.
from exp_263_batch import c0, c1, clean_rows, fit_c3, predict_c3, scores, REG

SCHEMA = "c3_forward_263_v1"
MAX_FUTURE_DAYS = 7
MAX_SOURCE_AGE_HOURS = 24
MAX_DATA_AGE_DAYS = 10
TIMEZONES = {
    "ENG1": "Europe/London", "ENG2": "Europe/London",
    "GER1": "Europe/Berlin", "ESP1": "Europe/Madrid",
    "ITA1": "Europe/Rome", "FRA1": "Europe/Paris",
    "NED1": "Europe/Amsterdam", "TUR1": "Europe/Istanbul",
    "POR1": "Europe/Lisbon", "BEL1": "Europe/Brussels",
}


def canonical_bytes(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_aware(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone_required")
    return parsed.astimezone(timezone.utc)


def valid_gate(gate, now):
    """Only accepts the result of an INDEPENDENT live official named-match lookup.

    This structural check alone CANNOT prove a user-supplied dict is official;
    the public entrypoint calls analyze_named_match_gate.run itself.
    """
    if gate.get("status") != "VERIFIED":
        raise ValueError("fixture_not_officially_verified")
    league = gate.get("league")
    if league not in TIMEZONES:
        raise ValueError("unsupported_league")
    home, away = gate.get("home_id"), gate.get("away_id")
    if not home or not away or home == away:
        raise ValueError("bad_team_identity")
    if not gate.get("source_url") or not str(gate["source_url"]).startswith("https://"):
        raise ValueError("missing_official_source_url")
    kickoff = read_aware(gate["kickoff_utc"])
    checked = read_aware(gate["retrieved_at_utc"])
    if not now < kickoff <= now + timedelta(days=MAX_FUTURE_DAYS):
        raise ValueError("match_not_in_future_seven_days")
    if not checked <= now + timedelta(minutes=5) or now - checked > timedelta(hours=MAX_SOURCE_AGE_HOURS):
        raise ValueError("official_check_not_fresh")
    local_date = kickoff.astimezone(ZoneInfo(TIMEZONES[league])).date().isoformat()
    return league, home, away, kickoff, checked, local_date


def predict_from_verified_gate(gate, history_file, out_dir, now=None):
    """Pure experiment entry for gate output; real entry ALWAYS runs official lookup.

    Existence check is atomic on a normal local filesystem. Repository protection
    additionally requires non-rewritten Git commit history: hash is tamper-evident,
    not an unconditional guarantee against a repo admin force-push.
    """
    now = now if now is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("naive_now_not_allowed")
    now = now.astimezone(timezone.utc)
    league, home, away, kickoff, checked, local_date = valid_gate(gate, now)
    history_path = Path(history_file)
    rows = clean_rows(history_path)
    latest = max(r["match_date"] for r in rows if r["league"] == league)
    if latest > local_date:
        raise ValueError("source_contains_future_results")
    age = (datetime.fromisoformat(local_date).date() - datetime.fromisoformat(latest).date()).days
    if age > MAX_DATA_AGE_DAYS:
        raise ValueError("stale_history_refresh_required")

    # Source snapshot may contain non-target future results from other leagues.
    # The model only trains on rows strictly earlier than the local kickoff day.
    past = [r for r in rows if r["league"] == league and r["match_date"] < local_date]
    if len(past) < 30:
        raise ValueError("not_enough_historical_matches")
    fitted = fit_c3(past)
    if fitted is None:
        raise ValueError("c3_optimizer_did_not_converge")
    lambdas = predict_c3(fitted, home, away)
    if lambdas is None:
        raise ValueError("c3_lambda_out_of_bounds")
    s3 = scores(*lambdas)
    if s3 is None:
        raise ValueError("c3_poisson_tail_rejected")
    s1 = c1(past, home, away)
    s0 = c0(past)
    if s0 is None:
        raise ValueError("league_baseline_unavailable")
    prediction_payload = {
        "schema": SCHEMA,
        "status": "EXPERIMENTAL_PREMATCH_NOT_FOR_BETTING",
        "created_at_utc": now.isoformat(),
        "fixture": {
            "league": league, "home_id": home, "away_id": away,
            "kickoff_utc": kickoff.isoformat(), "match_local_date": local_date,
            "official_source": gate["source_url"],
            "source_checked_at_utc": checked.isoformat(),
            "fixture_verification": "VERIFIED_BY_LIVE_OFFICIAL_GATE",
        },
        "data": {
            "snapshot_sha256": sha256_file(history_path),
            "source_tag": "football-data-co-uk-linked-historical-results",
            "league_history_rows": len(past), "league_latest_match_date": latest,
            "league_fixtures_used_sha256": hashlib.sha256(canonical_bytes([
                {key: r[key] for key in ("fixture_id", "match_date", "home_id", "away_id", "home_goals", "away_goals")}
                for r in past
            ])).hexdigest(),
            "cutoff_rule": "match_date strictly before local fixture day",
        },
        "code": {
            "frozen_model": "C3_ridge_poisson_2026_11_01",
            "c3_ridge": REG,
            "model_file_sha256": sha256_file(Path(__file__).with_name("exp_263_batch.py")),
            "forward_file_sha256": sha256_file(__file__),
        },
        "probabilities": {
            "C0_league_reference": dict(zip(("H", "D", "A"), s0)),
            "C1_existing_model_b": dict(zip(("H", "D", "A"), s1[0])) if s1 else None,
            "C3_opponent_adjusted": dict(zip(("H", "D", "A"), s3[0])),
        },
        "c3_expected_goals": {"home": lambdas[0], "away": lambdas[1]},
        "c3_poisson_tail_mass": s3[1],
        "c1_unavailable_reason": "INSUFFICIENT_HISTORY_OR_TAIL" if s1 is None else None,
        "model_limitations": [
            "C3 is not the official 2.6.3 k=5/w=0.5 primary model",
            "No first XI, odds, xG, corners or halftime modeled",
            "No bet, EV, or confidence guarantees",
            "New teams without prior observed ratings are centered at league strength",
        ],
    }
    if abs(sum(prediction_payload["probabilities"]["C3_opponent_adjusted"].values()) - 1) > 1e-9:
        raise ValueError("probability_sum_invalid")
    digest = hashlib.sha256(canonical_bytes(prediction_payload)).hexdigest()
    prediction_payload["payload_sha256"] = digest
    # UUID-like unambiguous ID from independently verified fixture fields.
    fixture_id = hashlib.sha256(canonical_bytes([league, home, away, kickoff.isoformat()])).hexdigest()[:24]
    target = Path(out_dir) / local_date / f"{fixture_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    # A rerun must never silently overwrite its earlier registered prediction.
    with target.open("x", encoding="utf-8") as fp:
        json.dump(prediction_payload, fp, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        fp.write("\n")
    return target, prediction_payload


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--league", required=True, choices=sorted(TIMEZONES))
    cli.add_argument("--home", required=True)
    cli.add_argument("--away", required=True)
    cli.add_argument("--history", default="data/historical_results.csv")
    cli.add_argument("--out-dir", default="forward_263")
    a = cli.parse_args()
    # Do NOT accept a fabricated fixture JSON from the CLI.
    try:
        root = Path(__file__).resolve().parents[2]
        sys.path.insert(0, str(root))
        from analyze_named_match_gate import run as check_fixture_live
        gate = check_fixture_live(a.league, a.home, a.away)
        if gate.get("status") != "VERIFIED":
            raise ValueError(f"Official fixture lookup failed: {gate.get('reason', gate.get('status'))}")
        dest, record = predict_from_verified_gate(gate, a.history, a.out_dir)
        print(json.dumps({"status": "CREATED_EXPERIMENTAL_ONLY",
                          "path": str(dest), "payload_sha256": record["payload_sha256"],
                          "fixture": record["fixture"]}, ensure_ascii=False))
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"BLOCKED (no prediction saved): {exc}") from exc


if __name__ == "__main__":
    main()
