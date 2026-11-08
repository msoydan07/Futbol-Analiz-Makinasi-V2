"""Causal independent Poisson challenger with predeclared development-only tuning.

Uses only full-time scores from strictly earlier calendar dates. League goals
baselines and home/away offense/defense are exponentially decayed and shrunk.
Not Dixon-Coles (the low-score dependence model is a separate candidate).
This initial evaluation is diagnostic; it cannot validate betting ROI.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import random
from collections import defaultdict
from datetime import date
from pathlib import Path
from elo_baseline import score

GOAL_MAX = 12
WARMUP = 40
TRAIN_END = "2024-07-01"
DEV_END = "2025-07-01"
CANDIDATES = [(h, prior) for h in (120, 365) for prior in (6.0, 12.0, 24.0)]
MIN_RATE, MAX_RATE = 0.18, 4.5

def key(row):
    return (row["league"], row["date"], row["home"], row["away"])

def keep_count(value, stamp, current, half_life):
    if stamp is None:
        return value
    age = max(0, (current - stamp).days)
    return value * math.exp(-math.log(2) * age / half_life)

class DecayStat:
    def __init__(self):
        self.last = None
        self.w = 0.0
        self.goals = 0.0

    def peek(self, day, halflife):
        factor = keep_count(1.0, self.last, day, halflife)
        return self.w * factor, self.goals * factor

    def add(self, day, halflife, goals):
        self.w, self.goals = self.peek(day, halflife)
        self.w += 1
        self.goals += goals
        self.last = day

def pmf(lam):
    vals = [math.exp(-lam)]
    for k in range(1, GOAL_MAX + 1):
        vals.append(vals[-1] * lam / k)
    # Reallocate tiny tail to final bin so outcomes sum to 1.
    vals[-1] += max(0.0, 1.0 - sum(vals))
    return vals

def outcome_probs(lam_h, lam_a):
    hp, ap = pmf(lam_h), pmf(lam_a)
    out = [0.0, 0.0, 0.0]
    for h, ph in enumerate(hp):
        for a, pa in enumerate(ap):
            out[0 if h > a else 1 if h == a else 2] += ph * pa
    normalizer = sum(out)
    return tuple(p / normalizer for p in out)

def history_rating(stats, day, halflife, prior, baseline, kind):
    w, g = stats.peek(day, halflife)
    return max(0.15, (g + prior * baseline) / (w + prior))

def estimate(league_state, home, away, day, halflife, prior):
    s = league_state
    wh, gh = s["league_home"].peek(day, halflife)
    wa, ga = s["league_away"].peek(day, halflife)
    mu_h = (gh + 60 * 1.45) / (wh + 60)
    mu_a = (ga + 60 * 1.15) / (wa + 60)
    h_att = history_rating(s["home_scored"][home], day, halflife, prior, mu_h, "h_att")
    a_con = history_rating(s["away_conceded"][away], day, halflife, prior, mu_h, "a_con")
    a_att = history_rating(s["away_scored"][away], day, halflife, prior, mu_a, "a_att")
    h_con = history_rating(s["home_conceded"][home], day, halflife, prior, mu_a, "h_con")
    lambda_h = max(MIN_RATE, min(MAX_RATE, h_att * a_con / mu_h))
    lambda_a = max(MIN_RATE, min(MAX_RATE, a_att * h_con / mu_a))
    return outcome_probs(lambda_h, lambda_a)

def league_factory():
    return {"league_home": DecayStat(), "league_away": DecayStat(),
            "home_scored": defaultdict(DecayStat),
            "home_conceded": defaultdict(DecayStat),
            "away_scored": defaultdict(DecayStat),
            "away_conceded": defaultdict(DecayStat), "n": 0}

def predict(rows, halflife, prior):
    states = defaultdict(league_factory)
    batches = defaultdict(list)
    for row in rows:
        batches[row["date"]].append(row)
    outputs = []
    for string_day in sorted(batches):
        day = date.fromisoformat(string_day)
        pending = []
        for row in sorted(batches[string_day], key=key):
            state = states[row["league"]]
            p = estimate(state, row["home"], row["away"], day, halflife, prior)
            label = ("H" if int(row["home_goals"]) > int(row["away_goals"]) else
                     "D" if int(row["home_goals"]) == int(row["away_goals"]) else "A")
            logloss, brier = score(p, label)
            outputs.append({**{k: row[k] for k in ("league", "date", "home", "away")},
                            "result": label, "p_home": p[0], "p_draw": p[1],
                            "p_away": p[2], "logloss": logloss, "brier": brier,
                            "prior_matches_in_league": state["n"],
                            "valid_warmup": state["n"] >= WARMUP})
            pending.append((row, day))
        # A match on the same date cannot affect another prediction that day.
        for row, d in pending:
            state = states[row["league"]]
            h, a = int(row["home_goals"]), int(row["away_goals"])
            state["league_home"].add(d, halflife, h)
            state["league_away"].add(d, halflife, a)
            for name, team, goals in (
                ("home_scored", row["home"], h),
                ("home_conceded", row["home"], a),
                ("away_scored", row["away"], a),
                ("away_conceded", row["away"], h)
            ):
                state[name][team].add(d, halflife, goals)
            state["n"] += 1
    return outputs

def period(row):
    return "train" if row["date"] < TRAIN_END else (
        "dev" if row["date"] < DEV_END else "holdout")

def mean(items, field):
    return sum(float(x[field]) for x in items) / len(items) if items else None

def ci_date_block(paired, seed=263, iterations=400):
    # delta = challenger - Elo, lower is better.
    by_day = defaultdict(list)
    for item in paired:
        by_day[item["date"]].append(item["delta"])
    days = sorted(by_day)
    if len(days) < 2:
        return [None, None]
    rng = random.Random(seed)
    output = []
    for _ in range(iterations):
        sampled = [days[rng.randrange(len(days))] for _ in days]
        total, count = 0.0, 0
        for day in sampled:
            values = by_day[day]
            total += sum(values)
            count += len(values)
        output.append(total / count)
    output.sort()
    return [output[int(.025 * (iterations - 1))],
            output[int(.975 * (iterations - 1))]]

def run(input_path, elo_path, output_path):
    with open(input_path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if any(row["date"] > "2026-11-09" for row in rows):
        raise ValueError("future match")
    with open(elo_path, encoding="utf-8", newline="") as f:
        elo_rows = list(csv.DictReader(f))
    elo = {key(r): r for r in elo_rows}
    if len(elo) != len(elo_rows) or len(elo) != len(rows):
        raise ValueError("unpaired input / duplicate Elo keys")
    trials = {}
    for half_life, prior in CANDIDATES:
        predictions = predict(rows, half_life, prior)
        dev = [r for r in predictions if period(r) == "dev" and r["valid_warmup"]]
        trials[(half_life, prior)] = {"dev_logloss": mean(dev, "logloss"),
                                     "n_dev": len(dev)}
    selected = min(trials, key=lambda k: (
        float("inf") if trials[k]["dev_logloss"] is None else trials[k]["dev_logloss"],
        k[0], k[1]))
    predictions = predict(rows, *selected)
    result = {}
    for phase in ("train", "dev", "holdout"):
        applicable = [r for r in predictions if period(r) == phase and r["valid_warmup"]]
        same = []
        for p in applicable:
            e = elo.get(key(p))
            if (e is None or e.get("valid_warmup", "").lower() != "true"
                    or p["result"] != e["result"]):
                raise ValueError("paired Elo records disagree")
            same.append((p, e))
        comparisons = {}
        for metric in ("logloss", "brier"):
            paired = [{"date": p["date"], "delta": p[metric] - float(e[metric])}
                      for p, e in same]
            comparisons[metric] = {
                "poisson_mean": mean(applicable, metric),
                "elo_mean": sum(float(e[metric]) for _, e in same) / len(same)
                if same else None,
                "poisson_minus_elo": sum(t["delta"] for t in paired) / len(paired)
                if paired else None,
                "date_block_bootstrap_95pct": ci_date_block(paired)}
        result[phase] = {"n_paired": len(same), "metrics": comparisons}
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(predictions[0]))
        writer.writeheader()
        writer.writerows(predictions)
    report = {
        "schema": "MC_POISSON_V1", "selection": {
            "basis": "development_only_multiclass_logloss",
            "half_life_days": selected[0], "smoothing_matches": selected[1],
            "dev_trials": [{"half_life": a, "prior": b, **trials[a, b]}
                           for a, b in CANDIDATES]},
        "paired": result, "no_market_benchmark": True,
        "incumbent_comparison_done": False,
        "forecast_policy": "pre_date_only",
        "caveat": "Experimental archive diagnostic, holdout not reusable for tuning; no betting claim",
    }
    p.with_suffix(".summary.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--elo", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.elo, args.out), indent=2))
