"""Read-only 7 Nov research: 3 SHA-sealed acceptance3 forecasts and observed scores.

Kept separate from 8 Nov's pre-existing 39-match report and the new100
pilot. No network source attestation is performed in CI, no refits or writes
to source history, odds, official result records, or forward predictions.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = "research/opponent_goals/nov7_primary_score_evidence_20261110.json"
BATCH = "experiments/263/sabah_batch_reports/acceptance3_42358492713.json"
PREVIOUS = "research/opponent_goals/reports/sealed_nov8_goal_error_and_strength_20261110.json"
DAY = "2026-11-07"
MARKETS = ("BTTS_YES", "OVER_1.5", "OVER_2.5", "OVER_3.5")
PRIMARY_HOSTS = {"ESP1": {"www.laliga.com"}, "ENG1": {"www.premierleague.com"},
                 "TUR1": {"konyaspor.org.tr"}}

class Blocked(ValueError):
    pass

def load(root, relative):
    return json.loads((Path(root) / relative).read_text(encoding="utf-8"))

def sha256_object(obj):
    b = json.dumps(obj, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def aware(ts):
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise Blocked("TIMESTAMP_WITHOUT_TIMEZONE")
    return dt.astimezone(timezone.utc)

def proper_probability(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not 0 <= x <= 1:
        raise Blocked("INVALID_PROBABILITY")
    return float(x)

def bin_metrics(prob, y):
    p = proper_probability(prob)
    return {"p": p, "y": y, "brier": (p - y) ** 2,
            "logloss": -(y * math.log(max(p, 1e-15)) +
                         (1 - y) * math.log(max(1 - p, 1e-15))),
            "correct_0_5": int((p >= 0.5) == bool(y))}

def summarize(values):
    n = len(values)
    return {
        "n": n,
        "mean_forecast": round(sum(x["p"] for x in values) / n, 6) if n else None,
        "observed_rate": round(sum(x["y"] for x in values) / n, 6) if n else None,
        "brier": round(sum(x["brier"] for x in values) / n, 6) if n else None,
        "logloss": round(sum(x["logloss"] for x in values) / n, 6) if n else None,
        "correct_0_5": sum(x["correct_0_5"] for x in values),
    }

def evaluate(root=ROOT, *, evidence_override=None):
    root = Path(root)
    evidence = evidence_override if evidence_override is not None else load(root, EVIDENCE)
    batch = load(root, BATCH)
    if (evidence.get("schema") != "263_NOV7_PUBLIC_PRIMARY_SCORE_RESEARCH_ONLY_V1"
            or evidence.get("cohort") != "acceptance3_NOT_new100"
            or evidence.get("day") != DAY
            or evidence.get("source_checks_in_github_ci") is not False
            or evidence.get("production_result_attestation") is not False):
        raise Blocked("EVIDENCE_CONTRACT_NOT_RESEARCH_ONLY")
    if (batch.get("schema") != "SABAH_TOPLU_KAYIT_V1"
            or batch.get("cohort") != "acceptance3"
            or batch.get("day_turkey") != DAY
            or len(batch.get("outcomes", [])) != 3
            or len(evidence.get("observations", [])) != 3):
        raise Blocked("ACCEPTANCE3_BATCH_OR_EVIDENCE_COUNT_INVALID")
    if batch.get("payload_sha256") != sha256_object(
        {k: v for k, v in batch.items() if k != "payload_sha256"}
    ):
        raise Blocked("ORIGINAL_BATCH_SHA_TAMPERED")
    registered = {}
    for row in batch["outcomes"]:
        key = (row["league"], row["home"], row["away"])
        if key in registered or row.get("status") != "REGISTERED_FOUR_MODELS_EXPERIMENTAL":
            raise Blocked("NONUNIQUE_OR_UNREGISTERED_BATCH")
        registered[key] = row

    recorded = set()
    per_market = {name: [] for name in MARKETS}
    rows = []
    for row in evidence["observations"]:
        key = (row["league"], row["home"], row["away"])
        if key in recorded or key not in registered:
            raise Blocked("DUPLICATE_OR_UNMATCHED_OUTCOME")
        recorded.add(key)
        if (type(row["home_goals"]) is not int or type(row["away_goals"]) is not int or
                not 0 <= row["home_goals"] <= 20 or not 0 <= row["away_goals"] <= 20):
            raise Blocked("UNSAFE_FULL_TIME_SCORE")
        parsed = urlsplit(row["source_url"])
        if (parsed.scheme != "https" or parsed.hostname not in PRIMARY_HOSTS.get(row["league"], set())
                or parsed.username or parsed.password or parsed.port or not parsed.path):
            raise Blocked("INVALID_OR_NONPRIMARY_RESULT_SOURCE")
        if row.get("source_type") not in ("OFFICIAL_LEAGUE", "OFFICIAL_CLUB"):
            raise Blocked("UNSUPPORTED_SOURCE_CLASS")
        batch_row = registered[key]
        path = batch_row.get("forecast_path", "")
        if not re.fullmatch(r"forward_acceptance_263/2026-11-07/[0-9a-f]{24}\\.json", path):
            raise Blocked("NOT_ORIGINAL_NOV7_ACCEPTANCE3_SEAL_PATH")
        seal = load(root, path)
        digest = sha256_object({k: v for k, v in seal.items() if k != "payload_sha256"})
        if (seal.get("schema") != "quad_forward_263_v1"
                or seal.get("payload_sha256") != digest
                or batch_row.get("forecast_sha256") != digest):
            raise Blocked("ORIGINAL_FORECAST_SHA_TAMPERED")
        fixture = seal["fixture"]
        if (fixture["match_local_date"] != DAY or fixture["league"] != row["league"]
                or fixture["kickoff_utc"] != batch_row["kickoff_utc"]
                or fixture["fixture_verification"] != "VERIFIED_BY_LIVE_OFFICIAL_GATE"):
            raise Blocked("MATCH_IDENTITY_OR_PREKICKOFF_FIXTURE_INVALID")
        created = aware(seal["created_at_utc"])
        checked = aware(fixture["source_checked_at_utc"])
        kickoff = aware(fixture["kickoff_utc"])
        if not (created < kickoff and checked < kickoff and checked <= created + timedelta(seconds=60)):
            raise Blocked("NOT_GENUINE_PREMATCH_FORECAST")
        if (seal["data"]["research_shadow_unverified_source"] is not False or
                seal["data"]["snapshot_sha256"] != "1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9"):
            raise Blocked("FROZEN_TRAINING_HISTORY_MISMATCH")
        prediction = seal["model_predictions"].get("M4", {})
        if prediction.get("status") != "AVAILABLE":
            raise Blocked("M4_MISSING_NO_FALLBACK")
        p = prediction["goals"]["markets"]
        ms = p["1X2"]
        if set(ms) != {"H", "D", "A"} or abs(sum(proper_probability(v) for v in ms.values()) - 1) > 1e-5:
            raise Blocked("INVALID_M4_MS1X2_GUARD")
        home, away = row["home_goals"], row["away_goals"]
        outcomes = {"BTTS_YES": int(home > 0 and away > 0),
                    "OVER_1.5": int(home + away >= 2),
                    "OVER_2.5": int(home + away >= 3),
                    "OVER_3.5": int(home + away >= 4)}
        values = {}
        for market in MARKETS:
            obs = bin_metrics(p[market], outcomes[market])
            per_market[market].append(obs)
            values[market] = {"forecast": round(obs["p"], 6), "occurred": obs["y"]}
        rows.append({"fixture": f"{row['home']} - {row['away']}",
                     "league": row["league"], "score": [home, away],
                     "forecast_sha256": digest, "original_forecast_path": path,
                     "primary_result_url": row["source_url"],
                     "market_events": values})
    if recorded != set(registered):
        raise Blocked("MISSING_OFFICIAL_SCORE_REVIEW")
    old = load(root, PREVIOUS)
    if (old.get("schema") != "263_NOV8_SEALED_M4_GOAL_MATCHUP_ERROR_DIAG_V1"
            or old.get("scored_m4") != 39 or old.get("postponed_excluded") != 1
            or old.get("whole", {}).get("n") != 39
            or old.get("model_changed") is not False):
        raise Blocked("OLD_NOV8_REPORT_MUTATED")
    prior = old["whole"]["goals_by_market"]
    previous = {k: {"n": prior[k]["n"],
                    "mean_forecast": prior[k]["predicted_event_rate"],
                    "observed_rate": prior[k]["observed_event_rate"],
                    "brier": prior[k]["m4_brier"]} for k in MARKETS}
    return {
        "schema": "263_SEPARATE_DATE_BLOCK_7_AND_EXISTING_8_NOV_RESEARCH_V1",
        "nov7": {"cohort": "acceptance3", "n": 3, "provenance": "PUBLIC_PRIMARY_PAGES_REVIEWED_CI_NOT_INDEPENDENT",
                 "markets": {k: summarize(v) for k, v in per_market.items()}, "matches": rows},
        "nov8_reference_only": {"cohort": "new100_research_unaccepted", "n": 39,
                                "source": PREVIOUS, "markets": previous,
                                "scored_again": False},
        "distinct_match_days": 2,
        "total_visible_research_events_unpooled": 42,
        "model_refit": False,
        "official_postmatch_inputs_modified": False,
        "new100_accepted_results_from_nov7": 0,
        "production_probability_recalibration": False,
        "candidate_promoted": False,
        "decision": "HOLD_UNTIL_MULTIPLE_NEW_INDEPENDENT_DATES",
        "limitations": [
            "7 Nov acceptance3 and 8 Nov new100 are different cohorts: separate reporting only",
            "7 Nov results were reviewed from public league/club pages in this research; CI does not fetch/recheck sources",
            "The previously reported 8 Nov 39 results are referenced unchanged, not rescored or certified here",
            "2 independent dates and 3+39 matches cannot certify 60-70 pct bins or establish superiority",
            "Original 4518 training archive, sealed forward files, M4 and 99 staged candidates untouched"]
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="")
    opts = parser.parse_args()
    report = evaluate()
    result = json.dumps(report, ensure_ascii=False, indent=2)
    if opts.output:
        Path(opts.output).write_text(result + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k in
                      ("schema", "distinct_match_days", "total_visible_research_events_unpooled",
                       "decision", "candidate_promoted")}, ensure_ascii=False))
    print(json.dumps(report["nov7"]["markets"], ensure_ascii=False))
