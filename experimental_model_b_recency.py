"""Leakage-safe paired time-decay experiment for the existing Model B.

Keeps the baseline intact. Candidate changes ONLY recency weighting.
No parameter is accepted without out-of-sample paired improvement.
Usage: python experimental_model_b_recency.py [historical_results.csv]
"""
import csv
import json
import math
import sys
from datetime import date
from pathlib import Path
from experimental_poisson_baseline import estimate, poisson

HALF_LIVES = (60, 120, 180, 270)

def weighted_mean(rows, goal_key, cutoff, half_life):
    weights = [2 ** (-(date.fromisoformat(cutoff)-date.fromisoformat(r["match_date"])).days / half_life) for r in rows]
    return sum(w * int(r[goal_key]) for w,r in zip(weights,rows)) / sum(weights) if weights else None

def candidate(rows, league, home_id, away_id, cutoff, half_life, window=20, shrink=5):
    past = sorted((r for r in rows if r["league"] == league and r["match_date"] < cutoff),
                  key=lambda r: (r["match_date"], r["fixture_id"]))
    home = [r for r in past if r["home_id"] == home_id][-window:]
    away = [r for r in past if r["away_id"] == away_id][-window:]
    if len(past) < 30 or len(home) < 5 or len(away) < 5:
        return None
    mh = weighted_mean(past, "home_goals", cutoff, half_life)
    ma = weighted_mean(past, "away_goals", cutoff, half_life)
    if min(mh, ma) <= 0:
        return None
    def factor(team_rows, field, prior):
        # Prior weight is relative to the effective weighted sample size;
        # this preserves the existing five-match shrinkage interpretation.
        weights = [2 ** (-(date.fromisoformat(cutoff)-date.fromisoformat(r["match_date"])).days / half_life) for r in team_rows]
        # Normalize recency weights to the original match count so that
        # shrink=5 retains the same effective prior strength as baseline.
        # Only relative recency, not the absolute age of the season, changes.
        scale = len(weights) / sum(weights)
        weights = [w * scale for w in weights]
        effective = sum(weights)
        observed = sum(w * int(r[field]) for w,r in zip(weights,team_rows))
        return ((observed + shrink*prior)/(effective+shrink))/prior
    lh = max(.05, min(5., mh*factor(home,"home_goals",mh)*factor(away,"home_goals",mh)))
    la = max(.05, min(5., ma*factor(away,"away_goals",ma)*factor(home,"away_goals",ma)))
    ph = [poisson(lh,k) for k in range(11)]
    pa = [poisson(la,k) for k in range(11)]
    out = [0.,0.,0.]
    for i in range(11):
        for j in range(11):
            out[0 if i>j else 1 if i==j else 2] += ph[i]*pa[j]
    total = sum(out)
    return [v/total for v in out]

def evaluate(rows):
    rows = sorted(rows, key=lambda r:(r["match_date"],r["fixture_id"]))
    assert len({r["fixture_id"] for r in rows}) == len(rows), "Duplicate fixture_id"
    results = {}
    for half_life in HALF_LIVES:
        n=0
        base_ll=alt_ll=base_brier=alt_brier=0.
        for r in rows:
            baseline = estimate(rows,r["league"],r["home_id"],r["away_id"],r["match_date"])
            alt = candidate(rows,r["league"],r["home_id"],r["away_id"],r["match_date"],half_life)
            if baseline is None or alt is None:
                continue
            actual = ("H","D","A").index(r["result"])
            original = [baseline["p_home"],baseline["p_draw"],baseline["p_away"]]
            total = sum(original)
            original = [v/total for v in original]
            base_ll -= math.log(max(original[actual],1e-12))
            alt_ll -= math.log(max(alt[actual],1e-12))
            base_brier += sum((p-int(i==actual))**2 for i,p in enumerate(original))
            alt_brier += sum((p-int(i==actual))**2 for i,p in enumerate(alt))
            n+=1
        results[str(half_life)] = {
            "paired_matches":n,
            "baseline_log_loss":base_ll/n if n else None,
            "candidate_log_loss":alt_ll/n if n else None,
            "baseline_brier":base_brier/n if n else None,
            "candidate_brier":alt_brier/n if n else None,
            "log_loss_delta_candidate_minus_baseline":(alt_ll-base_ll)/n if n else None,
            "brier_delta_candidate_minus_baseline":(alt_brier-base_brier)/n if n else None,
        }
    return {"experiment":"model_b_recency_only_v1","half_lives_days":list(HALF_LIVES),
            "selection_rule":"lower log loss and Brier are better; do not adopt without chronological holdout",
            "caveat":"Exploratory same-history comparison; select half-life on validation, verify on later untouched test period",
            "results":results}

if __name__=="__main__":
    path=Path(sys.argv[1]) if len(sys.argv)>1 else Path("data/historical_results.csv")
    with path.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    report=evaluate(rows)
    Path("data").mkdir(exist_ok=True)
    Path("data/model_b_recency_experiment.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
