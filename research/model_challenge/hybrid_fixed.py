"""PREDECLARED equal-weight probability pool for Elo / Poisson / XGBoost.

All three inputs are immutable archived diagnostic predictions. Weights are
exactly 1/3 each, defined prior to inspecting pooled results; there is no
tuning, league-specific weight selection, or market odds inference.
2025/26 evaluation period has already been viewed, so the output is
EXPLORATORY ONLY and cannot justify deployment or wagering.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from paired_audit import (
    LABELS, audit, block_interval, load_csv, match_key, probability,
    score, unique_index, lower_mean
)

WEIGHTS = {"Elo": 1 / 3, "Poisson": 1 / 3, "XGBoost": 1 / 3}

def pool(preds):
    if set(preds) != set(WEIGHTS):
        raise ValueError("three predeclared competitors required")
    result = tuple(sum(WEIGHTS[model] * preds[model][j] for model in WEIGHTS)
                   for j in range(3))
    if not all(math.isfinite(x) and 0 < x < 1 for x in result):
        raise ValueError("invalid pooled probability")
    total = sum(result)
    # XGBoost exports float32 probabilities; a ~1e-8 sum deviation
    # is expected and must not invalidate correctly paired predictions.
    if abs(total - 1) > 1e-5:
        raise ValueError("non-normalized pool")
    return tuple(x / total for x in result)

def run(elo_file, poisson_file, xgb_file, out_file):
    paths = {"Elo": elo_file, "Poisson": poisson_file, "XGBoost": xgb_file}
    tables = {m: unique_index(load_csv(path)) for m, path in paths.items()}
    keys = set(tables["XGBoost"])
    if not keys.issubset(tables["Elo"]) or not keys.issubset(tables["Poisson"]):
        raise ValueError("unpaired fixture keys")
    if len(keys) < 1000:
        raise ValueError("too few fixtures")
    data = []
    for k in sorted(keys):
        rows = {m: tables[m][k] for m in WEIGHTS}
        labels = [rows["Elo"]["result"], rows["Poisson"]["result"],
                  rows["XGBoost"]["actual"]]
        if len(set(labels)) != 1:
            raise ValueError("result mismatch")
        if any(rows[m]["valid_warmup"].lower() != "true" for m in ("Elo","Poisson")):
            raise ValueError("warmup mismatch")
        if k[1] < "2025-07-01" or k[1] > "2026-11-09":
            raise ValueError("bad evaluation date")
        probs = {m: probability(rows[m]) for m in WEIGHTS}
        blended = pool(probs)
        s = {m: score(p, labels[0]) for m,p in probs.items()}
        s["EqualWeightHybrid"] = score(blended, labels[0])
        row = {"date":k[1], "league":k[0], "home":k[2], "away":k[3],
               "result":labels[0], "p_home":blended[0],
               "p_draw":blended[1], "p_away":blended[2]}
        for m, (loss,brier) in s.items():
            row[m+"_logloss"] = loss
            row[m+"_brier"] = brier
        data.append(row)
    metrics = ("logloss","brier")
    overall = {m: {metric: lower_mean([row[m+"_"+metric] for row in data])
                   for metric in metrics}
               for m in (*WEIGHTS,"EqualWeightHybrid")}
    comparisons = {}
    for m in WEIGHTS:
        comparisons["EqualWeightHybrid_minus_"+m] = {}
        for metric in metrics:
            a="EqualWeightHybrid_"+metric;b=m+"_"+metric
            comparisons["EqualWeightHybrid_minus_"+m][metric] = {
                "delta": lower_mean([r[a]-r[b] for r in data]),
                "date_block_bootstrap_95pct": block_interval(data,a,b)
            }
    path = Path(out_file)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=("league","date","home","away","result",
                                      "p_home","p_draw","p_away"))
        w.writeheader()
        for r in data:
            w.writerow({k:r[k] for k in w.fieldnames})
    report = {
        "schema":"MC_FROZEN_EQUAL_WEIGHT_HYBRID_V1",
        "status":"EXPLORATORY_ALREADY_VIEWED_HOLDOUT",
        "weights":WEIGHTS, "fixture_count":len(data),
        "overall":overall,"paired":comparisons,
        "weight_tuning":"NONE",
        "m4_head_to_head":"NOT_COMPARABLE",
        "market_edge":"NOT_AVAILABLE",
        "promotion_eligible":False,"betting_authorized":False
    }
    path.with_suffix(".summary.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("elo","poisson","xgb","out"):p.add_argument("--"+name,required=True)
    args=p.parse_args()
    r=run(args.elo,args.poisson,args.xgb,args.out)
    print(json.dumps(r,indent=2,ensure_ascii=False))
