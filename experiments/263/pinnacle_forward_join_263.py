"""Read-only Pinnacle market reference inside a NEW four-model forecast job.

One bookmaker h2h API call per unique league/day, never per match. No source,
price, or normal S1/S2 decision is invented. Only time-aligned new forecasts.
"""
from __future__ import annotations
import argparse, hashlib, json, os
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from free_bulk_odds_263 import collect, canonical, utc, QuoteUnavailable
from market_fifth_baseline_263 import sealed_payload
from pinnacle_market_benchmark_263 import compare, BenchmarkBlocked

SCHEMA = "263_pinnacle_same_job_research_v1"
FORECAST_STATUS = "REGISTERED_FOUR_MODELS_EXPERIMENTAL"

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save_new(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x", encoding="utf-8") as fp:
        json.dump(obj, fp, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        fp.write("\n")

def seal(obj):
    obj = dict(obj)
    obj.pop("payload_sha256", None)
    obj["payload_sha256"] = hashlib.sha256(canonical(obj)).hexdigest()
    return obj

def join(report_path, *, root=Path("."), out_base=Path("experiments/263"),
         now=None, key=None, getter=None):
    """Collect only required leagues; stage independent evidence without revising forecasts."""
    root = Path(root).resolve()
    out_base = Path(out_base)
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    batch = read(root / report_path)
    if batch.get("schema") != "quad_named_match_batch_report_v1":
        raise ValueError("INVALID_FORWARD_BATCH_SCHEMA")
    eligible = defaultdict(list)
    items = []
    seen = set()
    for item in batch.get("outcomes", []):
        if item.get("status") != FORECAST_STATUS:
            continue
        relative = item.get("path")
        if not isinstance(relative, str) or not relative.startswith("forward_quad_263/"):
            raise ValueError("UNSAFE_FORECAST_PATH")
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("MISSING_FORWARD_FORECAST_FILE")
        f = read(path)
        sealed_payload(f, "quad_forward_263_v1")
        if f["payload_sha256"] != item.get("payload_sha256"):
            raise ValueError("FORECAST_BATCH_SHA_DISAGREEMENT")
        if relative in seen:
            raise ValueError("DUPLICATE_FORWARD_RECORD")
        seen.add(relative)
        fixture = f["fixture"]
        created = utc(f["created_at_utc"])
        kickoff = utc(fixture["kickoff_utc"])
        age = (now - created).total_seconds() / 60
        minutes_to_ko = (kickoff - now).total_seconds() / 60
        current = {
            "forecast_path": relative,
            "forecast_sha256": f["payload_sha256"],
            "league": fixture["league"],
            "kickoff_utc": kickoff.isoformat(),
            "status": "NO_PINNACLE_COMPARISON",
            "reason": None,
        }
        if not key:
            current["reason"] = "NO_FREE_THE_ODDS_API_KEY_CONFIGURED"
        elif not 0 <= age <= 10:
            current["reason"] = "FORECAST_OUTSIDE_SAME_TIME_WINDOW"
        elif not 20 <= minutes_to_ko <= 90:
            current["reason"] = "NOT_IN_T60_KICKOFF_WINDOW"
        else:
            eligible[(fixture["match_local_date"], fixture["league"])].append((f, current))
        items.append(current)
    by_day = defaultdict(set)
    for day, league in eligible:
        by_day[day].add(league)
    snaps = []
    maximum_requested_credits = 0
    for day in sorted(by_day):
        leagues = sorted(by_day[day])
        maximum_requested_credits += len(leagues)  # one market x one bookmaker
        try:
            kw = dict(bookmaker_filter="pinnacle", leagues=leagues, markets=("h2h",))
            if getter is not None:
                kw["getter"] = getter
            bulk = collect(date.fromisoformat(day), now, key, **kw)
            snap_rel = out_base / "pinnacle_samejob_bulk" / (
                Path(report_path).stem + "_" + day + ".json")
            save_new(root / snap_rel, bulk)
            snaps.append({"path": snap_rel.as_posix(), "sha256": bulk["payload_sha256"],
                          "leagues": leagues, "blocked": bulk.get("blocked", {})})
        except (QuoteUnavailable, ValueError) as exc:
            for league in leagues:
                for _, row in eligible[(day, league)]:
                    row["reason"] = str(exc)[:120]
            continue
        for league in leagues:
            for f, row in eligible[(day, league)]:
                try:
                    outcome = compare(f, bulk)
                except (BenchmarkBlocked, ValueError, TypeError, KeyError) as exc:
                    row["reason"] = "BENCHMARK_VALIDATION_ERROR:" + str(exc)[:80]
                    continue
                if outcome["status"] != "READ_ONLY_SAME_TIME_BENCHMARK":
                    row["reason"] = outcome.get("reason", "PRICE_NOT_ACCEPTED")
                    continue
                dest = (out_base / "pinnacle_samejob_comparisons" / day /
                        (Path(row["forecast_path"]).stem + ".json"))
                save_new(root / dest, outcome)
                row.update(status="PINNACLE_READ_ONLY_COMPARISON_STORED", reason=None,
                           comparison_path=dest.as_posix(),
                           comparison_sha256=outcome["payload_sha256"])
    return seal({
        "schema": SCHEMA, "observed_at_utc": now.isoformat(),
        "status": "READ_ONLY_PINNACLE_RESEARCH_AUDITED",
        "provider": "Pinnacle via The Odds API (not direct site verified)",
        "max_requested_credits": maximum_requested_credits,
        "original_predictions_modified": False,
        "official_S1_S2_modified": False, "betting_authorized": False,
        "items": items, "snapshots": snaps
    })

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--report", required=True)
    p.add_argument("--audit-out", required=True)
    args = p.parse_args()
    report = join(args.report, key=os.environ.get("THE_ODDS_API_KEY"))
    save_new(args.audit_out, report)
    print(json.dumps({
        "status": report["status"], "max_requested_credits": report["max_requested_credits"],
        "per_match": [{"league": x["league"], "status": x["status"],
                       "reason": x["reason"]} for x in report["items"]],
        "models_and_decisions_untouched": True,
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
