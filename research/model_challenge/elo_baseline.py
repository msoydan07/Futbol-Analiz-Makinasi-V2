"""Deterministic, leakage-conservative Elo research baseline for 1X2.

Date-batched updates: no match on date D can use *any* results from date D.
No odds, xG or results from the scored match appear in prediction inputs.
Fixed parameters are hypotheses, NOT tuned or promoted models.

Run: python research/model_challenge/elo_baseline.py \
  --input /tmp/football-research/normalized_matches.csv \
  --out /tmp/football-research/elo_predictions.csv

All rows include a pre-update prediction; evaluation windows are deliberately
reported separately and not silently treated as untouched if previously seen.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path

K = 20.0
HOME_ELO_BONUS = 65.0
DRAW_PRIOR = 0.265
DRAW_PRIOR_N = 60
MIN_PRIOR_MATCHES = 40

def expectation(home, away, home_adv=HOME_ELO_BONUS):
    return 1.0 / (1.0 + 10.0 ** ((away - home - home_adv) / 400.0))

def probs(home, away, prior_draw_count, prior_count):
    draw = (DRAW_PRIOR * DRAW_PRIOR_N + prior_draw_count) / (DRAW_PRIOR_N + prior_count)
    win = expectation(home, away)
    return (1.0 - draw) * win, draw, (1.0 - draw) * (1.0 - win)

def outcome(h, a):
    return "H" if h > a else "D" if h == a else "A"

def score(p, label):
    y = [int(label == x) for x in ("H", "D", "A")]
    return -math.log(max(1e-12, p[("H", "D", "A").index(label)])), sum(
        (z - t) ** 2 for z, t in zip(p, y))

def predict_stream(rows):
    """Rows sorted by (date, league); update all ratings *after* the date is scored."""
    leagues = defaultdict(lambda: {"ratings": defaultdict(lambda: 1500.0),
                                   "draws": 0, "n": 0})
    by_date = defaultdict(list)
    for item in rows:
        by_date[item["date"]].append(item)
    for day in sorted(by_date):
        updates = []
        for row in sorted(by_date[day], key=lambda r: (r["league"], r["home"], r["away"])):
            s = leagues[row["league"]]
            home, away = row["home"], row["away"]
            h, a = s["ratings"][home], s["ratings"][away]
            p = probs(h, a, s["draws"], s["n"])
            label = outcome(int(row["home_goals"]), int(row["away_goals"]))
            logloss, brier = score(p, label)
            yield {
                "league": row["league"], "date": day, "home": home, "away": away,
                "result": label, "p_home": p[0], "p_draw": p[1], "p_away": p[2],
                "logloss": logloss, "brier": brier,
                "prior_matches_in_league": s["n"], "valid_warmup": s["n"] >= MIN_PRIOR_MATCHES,
            }
            # Buffer changes. Date-D results cannot enter any date-D probability.
            actual = 1.0 if label == "H" else 0.5 if label == "D" else 0.0
            predicted = expectation(h, a)
            margin = abs(int(row["home_goals"]) - int(row["away_goals"]))
            delta = K * (actual - predicted)  # no goal-margin tuning
            updates.append((row["league"], home, away, delta, label == "D"))
        for league, home, away, delta, draw in updates:
            s = leagues[league]
            s["ratings"][home] += delta
            s["ratings"][away] -= delta
            s["n"] += 1
            s["draws"] += int(draw)

FIELDS = ("league","date","home","away","result","p_home","p_draw","p_away",
          "logloss","brier","prior_matches_in_league","valid_warmup")

def run(input_path, output_path):
    with open(input_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        if date.fromisoformat(row["date"]) > date(2026, 11, 9):
            raise ValueError("future record forbidden")
        if any(not row.get(k) for k in ("league","home","away","home_goals","away_goals")):
            raise ValueError("missing value")
    out = list(predict_stream(rows))
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    # Fixed windows are declared only as diagnostics; NOT unexposed holdouts.
    windows = {
        "train_pre_2024_07_01": [],
        "dev_2024_07_01_to_2025_06_30": [],
        "holdout_2025_07_01_onward": [],
    }
    for x in out:
        if not x["valid_warmup"]:
            continue
        target = ("train_pre_2024_07_01" if x["date"] < "2024-07-01" else
                  "dev_2024_07_01_to_2025_06_30" if x["date"] < "2025-07-01" else
                  "holdout_2025_07_01_onward")
        windows[target].append(x)
    result = {}
    for name, items in windows.items():
        result[name] = {
            "n": len(items),
            "mean_logloss": sum(z["logloss"] for z in items) / len(items) if items else None,
            "mean_brier": sum(z["brier"] for z in items) / len(items) if items else None,
            "note": "diagnostic, not an as-yet untouched holdout"
        }
    summary = {"schema": "MC_ELO_DIAGNOSTIC_V1", "parameters": {
        "K": K, "home_elo_bonus": HOME_ELO_BONUS,
        "draw_prior": DRAW_PRIOR, "draw_prior_n": DRAW_PRIOR_N,
        "min_prior_matches": MIN_PRIOR_MATCHES,
    }, "results": result,
       "betting_authorized": False, "incumbent_comparison_done": False}
    p.with_suffix(".summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    print(json.dumps(run(a.input, a.out), indent=2))
