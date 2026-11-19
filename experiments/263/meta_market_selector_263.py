"""Read-only market-family meta selector over pinned retrospective B/C2/C3/M4 snapshots.

Comparison is exploratory: October 2026 outcomes were seen by earlier research.
NO forecast re-writes, xG, live API, odds, model refit or production promotion.
A market family uses ONE coherent base model. Decisions have strict pre-day history.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from chrono_goal_stage2_263 import load_predictions

FAMILIES = {
    "MS": ("MS1", "MSX", "MS2"),
    "KG": ("BTTS_YES", "BTTS_NO"),
    "GOALS": ("OVER_1.5", "UNDER_1.5", "OVER_2.5", "UNDER_2.5",
              "OVER_3.5", "UNDER_3.5"),
}
BASE = {"MS": "M4", "KG": "C3", "GOALS": "C3"}
OTHER = {"M4": "C3", "C3": "M4"}
TRIAL_START = "2026-10-01"
MIN_PAIRED = 120
MIN_DAYS = 10
SWITCH_MARGIN = 0.005

def _prob(x):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) or not 0 <= x <= 1:
        raise ValueError("INVALID_PROBABILITY")
    return x

def valid(row, model, family):
    p = row.get("p", {}).get(model, {})
    try:
        for market in FAMILIES[family]:
            _prob(p[market])
        if family == "MS":
            if abs(sum(p[k] for k in FAMILIES["MS"]) - 1) > 1e-7:
                return False
        elif family == "KG":
            if abs(p["BTTS_YES"] + p["BTTS_NO"] - 1) > 1e-7:
                return False
        else:
            for n in ("1.5", "2.5", "3.5"):
                if abs(p["OVER_" + n] + p["UNDER_" + n] - 1) > 1e-7:
                    return False
            if not (p["OVER_1.5"] >= p["OVER_2.5"] >= p["OVER_3.5"]):
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False

def loss(row, model, family):
    if not valid(row, model, family):
        raise ValueError("INCOMPLETE_MODEL_FAMILY")
    p = row["p"][model]
    y = row["obs"]
    if family == "MS":
        return sum((p[k] - y[k]) ** 2 for k in FAMILIES["MS"])
    if family == "KG":
        return (p["BTTS_YES"] - y["BTTS_YES"]) ** 2
    return sum((p["OVER_" + n] - y["OVER_" + n]) ** 2 for n in ("1.5", "2.5", "3.5")) / 3

def choose(row, prior, family):
    """Return decision made using ONLY earlier match DATES (never same-day)."""
    preferred = BASE[family]
    alternative = OTHER[preferred]
    paired = [r for r in prior if r["date"] < row["date"]
              and valid(r, preferred, family) and valid(r, alternative, family)]
    evidence = {"prior_paired": len(paired),
                "prior_distinct_dates": len({r["date"] for r in paired}),
                "latest_training_date": max((r["date"] for r in paired), default=None),
                "base_model": preferred,
                "switch_margin": SWITCH_MARGIN}
    if not valid(row, preferred, family):
        if valid(row, alternative, family):
            return alternative, {**evidence, "reason": "BASE_MODEL_UNAVAILABLE"}
        return None, {**evidence, "reason": "BOTH_MODELS_UNAVAILABLE_PAS"}
    if len(paired) < MIN_PAIRED or evidence["prior_distinct_dates"] < MIN_DAYS:
        return preferred, {**evidence, "reason": "NOT_ENOUGH_PAST_USE_DEFAULT"}
    diffs = [(loss(r, preferred, family) - loss(r, alternative, family), r["league"]) for r in paired]
    global_edge = sum(d for d, _ in diffs) / len(diffs)
    local = [d for d, league in diffs if league == row["league"]]
    # Shrink league-specific evidence toward global evidence; never train on target-day scores.
    league_weight = min(0.5, len(local) / (len(local) + 120))
    edge = (1 - league_weight) * global_edge + league_weight * (sum(local)/len(local) if local else global_edge)
    evidence.update(global_edge_brier=global_edge, league_n=len(local),
                    league_weight=league_weight, shrunk_edge_brier=edge)
    if edge > SWITCH_MARGIN and valid(row, alternative, family):
        return alternative, {**evidence, "reason": "PAST_BRIER_SUPPORTS_SWITCH"}
    return preferred, {**evidence, "reason": "DEFAULT_NOT_BEATEN"}

def select_static(row, family, strategy):
    if strategy == "fixed":
        candidates = (BASE[family], OTHER[BASE[family]])
    elif strategy == "all_m4":
        candidates = ("M4", "C3")
    elif strategy == "all_c3":
        candidates = ("C3", "M4")
    else:
        raise ValueError("UNKNOWN_STRATEGY")
    return next((m for m in candidates if valid(row, m, family)), None)

def score(row, selections):
    output = {}
    for family, model in selections.items():
        if model is None:
            output[family] = None
            continue
        p, y = row["p"][model], row["obs"]
        if family == "MS":
            truth = next(k for k in ("MS1", "MSX", "MS2") if y[k] == 1)
            top = max(("MS1", "MSX", "MS2"), key=lambda k: p[k])
            output["MS"] = {"model": model, "brier": loss(row, model, "MS"),
                            "logloss": -math.log(max(1e-12, p[truth])),
                            "hit": int(top == truth),
                            "confidence": p[top], "top_observed": int(top == truth)}
        elif family == "KG":
            output["KG"] = _binary(p["BTTS_YES"], y["BTTS_YES"], model)
        else:
            output["GOALS"] = {n: _binary(p["OVER_" + n], y["OVER_" + n], model)
                               for n in ("1.5", "2.5", "3.5")}
    return output

def _binary(p, y, model):
    return {"model": model, "brier": (p-y)**2,
            "logloss": -math.log(max(1e-12, p if y else 1-p)),
            "hit": int((p >= 0.5) == bool(y)),
            "confidence": p, "top_observed": y}

def _ece(items):
    # Descriptive ten-bin reliability error. Do not call a post-hoc recalibrator.
    if not items:
        return None
    result = 0.0
    for i in range(10):
        group = [z for z in items if min(9, int(z["confidence"] * 10)) == i]
        if group:
            result += (len(group) / len(items)) * abs(
                sum(z["confidence"] for z in group)/len(group) -
                sum(z["top_observed"] for z in group)/len(group))
    return result

def summary(records):
    result = {}
    for key in ("MS", "KG", "GOALS_1.5", "GOALS_2.5", "GOALS_3.5"):
        f, line = ("GOALS", key.split("_")[1]) if key.startswith("GOALS_") else (key, None)
        entries = [r["values"][f][line] if line else r["values"][f]
                   for r in records if r["values"][f] is not None]
        n = len(entries)
        result[key] = {"n": n,
             "brier": sum(x["brier"] for x in entries)/n if n else None,
             "logloss": sum(x["logloss"] for x in entries)/n if n else None,
             "accuracy": sum(x["hit"] for x in entries)/n if n else None,
             "ece10": _ece(entries),
             "model_counts": dict(Counter(x["model"] for x in entries))}
    return result

def _confidence_days(recs, key="MS", reps=800, seed=263):
    """Paired date-block confidence bounds for fixed minus dynamic Brier."""
    buckets = defaultdict(list)
    for r in recs:
        base = r["fixed"]["values"]
        other = r["dynamic"]["values"]
        f, line = ("GOALS", key.split("_")[1]) if key.startswith("GOALS_") else (key, None)
        a, b = base[f], other[f]
        if line and a is not None and b is not None:
            a,b = a[line],b[line]
        if a is not None and b is not None:
            buckets[r["date"]].append(a["brier"]-b["brier"])
    days = sorted(buckets)
    if not days: return {"n": 0, "mean_fixed_minus_dynamic": None}
    values = [x for d in days for x in buckets[d]]
    rng = random.Random(seed)
    boot = []
    for _ in range(reps):
        sample = [rng.choice(days) for __ in days]
        obs = [x for d in sample for x in buckets[d]]
        boot.append(sum(obs)/len(obs))
    boot.sort()
    return {"n":len(values),"distinct_days":len(days),
            "mean_fixed_minus_dynamic":sum(values)/len(values),
            "ci95":[boot[int(.025*reps)],boot[int(.975*reps)]]}

def evaluate(predictions):
    if len(predictions) != 880:
        raise ValueError("REQUIRES_PINNED_880_RETROSPECTIVE_MATCHES")
    history = []
    evaluated = []
    grouped = defaultdict(list)
    for row in predictions:
        grouped[row["date"]].append(row)
    for day in sorted(grouped):
        decisions = []
        for r in grouped[day]:
            fixed = {f:select_static(r,f,"fixed") for f in FAMILIES}
            dynamic_detail = {f:choose(r,history,f) for f in FAMILIES}
            dynamic = {f: dynamic_detail[f][0] for f in FAMILIES}
            all_m4 = {f:select_static(r,f,"all_m4") for f in FAMILIES}
            all_c3 = {f:select_static(r,f,"all_c3") for f in FAMILIES}
            # An entire mutually exclusive MS probability triple comes from ONE model.
            for choice in (fixed, dynamic, all_m4, all_c3):
                assert choice["MS"] is None or valid(r, choice["MS"], "MS")
            if day >= TRIAL_START:
                decisions.append({"day": day, "date": day, "league":r["league"],
                    "fixed":{"choices":fixed,"values":score(r,fixed)},
                    "dynamic":{"choices":dynamic,"values":score(r,dynamic)},
                    "all_m4":{"choices":all_m4,"values":score(r,all_m4)},
                    "all_c3":{"choices":all_c3,"values":score(r,all_c3)},
                    "evidence":{f:dynamic_detail[f][1] for f in FAMILIES}})
        evaluated.extend(decisions)
        history.extend(grouped[day])  # critical: only AFTER ALL same-day choices!
    if len(evaluated) != 293:
        raise ValueError("EXACT_OCTOBER_293_EXPECTED")
    comparisons = {k:summary([{"values":x[k]["values"]} for x in evaluated])
                   for k in ("fixed","dynamic","all_m4","all_c3")}
    switches = {f:sum(x["dynamic"]["choices"][f] != x["fixed"]["choices"][f]
                      for x in evaluated) for f in FAMILIES}
    blocked = {f:sum(x["dynamic"]["choices"][f] is None for x in evaluated) for f in FAMILIES}
    training = {f: {"min_history": min(x["evidence"][f]["prior_paired"] for x in evaluated),
                    "max_history": max(x["evidence"][f]["prior_paired"] for x in evaluated)}
                for f in FAMILIES}
    if any(x["evidence"][f]["latest_training_date"] is not None and
           x["evidence"][f]["latest_training_date"] >= x["date"]
           for x in evaluated for f in FAMILIES):
        raise ValueError("TRAINING_RESULT_LEAKAGE")
    ci = {k:_confidence_days(evaluated,k) for k in
          ("MS","KG","GOALS_1.5","GOALS_2.5","GOALS_3.5")}
    return {"schema":"263_meta_market_family_research_v1",
       "data":"4413_SHA_PINNED_RECONSTRUCTED_ASOF_880",
       "development":"2026-08-01/2026-09-30",
       "evaluation":"2026-10-01/2026-10-29",
       "n_development":587,"n_evaluation":293,
       "read_only":True,"independent_untouched_final_test":False,
       "past_results_same_day_leakage":False,
       "no_xg":True,"no_odds_or_ev":True,"no_new_pilot":True,
       "production_changed":False,"model_parameters_changed":False,
       "old_sha_forecasts_changed":False,
       "calibration_method":"none_exploratory_reliability_bins_only",
       "policy":"fixed MS:M4 KG:C3 GOALS:C3; dynamic strictly earlier history, league-shrunk Brier",
       "switch_rule":{"min_prior_paired":MIN_PAIRED,
                      "min_prior_dates":MIN_DAYS,
                      "min_brier_advantage":SWITCH_MARGIN},
       "switches":switches,"missing_models":blocked,
       "history_size":training,"metrics":comparisons,
       "paired_date_block_fixed_minus_dynamic":ci,
       "observed_days":len({r["date"] for r in evaluated}),
       "decisions_preview": [
            {"date":r["date"],"league":r["league"],
             "fixed":r["fixed"]["choices"],"dynamic":r["dynamic"]["choices"],
             "reason":{f:r["evidence"][f]["reason"] for f in FAMILIES}}
            for r in evaluated[:12]],
       "promotion":"HOLD_UNTIL_INDEPENDENT_FORWARD_EVIDENCE",
       "warnings":["October retrospective data was previously explored: no clean final holdout",
          "Brier is a proper probability score; win-rate alone is not sufficient",
          "No timestamped price evidence; no ROI/EV claim",
          "Do not tune thresholds to October results or re-open historical forecast seals"]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--predictions",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    d=evaluate(load_predictions(args.predictions))
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():raise ValueError("NEVER_OVERWRITE_RESEARCH")
    target.write_text(json.dumps(d,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("META_MARKET_COMPARISON="+json.dumps({
        "n":d["n_evaluation"],"switches":d["switches"],
        "metrics":{s:{market:{"n":v["n"],"brier":v["brier"],"logloss":v["logloss"],
                         "ece10":v["ece10"],"model_counts":v["model_counts"]}
                      for market,v in d["metrics"][s].items()}
                   for s in d["metrics"]},
        "bootstrap":d["paired_date_block_fixed_minus_dynamic"]},sort_keys=True,allow_nan=False))

if __name__=="__main__":
    main()
