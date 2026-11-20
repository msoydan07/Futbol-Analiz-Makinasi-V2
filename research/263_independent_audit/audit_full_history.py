"""2025/26 full archive strictly previous-day walk-forward sensitivity analysis.

Independent research only. The season informed M4 tuning and is NOT a blind holdout.
Does not rerun already archived 2026/27 880 or rewrite SHA-sealed forecasts.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments/263"))
sys.path.insert(0,str(ROOT/"research/263_independent_audit"))
from exp_263_batch import clean_rows
from chrono_goal_decision_263 import records_for_day
from m4_integrated import use_lock
from audit import add_alternatives, score_all, block_interval, decisions

EXPECTED_SHA="35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1"
NAMES=("ASOF_LEAGUE_RATE","B","C2","C3","M4","ENSEMBLE_50_50",
       "DC_MINUS_0.1","DC_PLUS_0.1","BIVARIATE_0.15","NB_K3","NB_K8")
DEV_WINDOWS=(("2025-11-15","2025-12-06"),("2026-01-15","2026-02-05"),("2026-03-15","2026-04-05"))
FAMILIES=("MS","KG","O25")

def dev_block(r):
    return any(start<=r["date"]<end for start,end in DEV_WINDOWS)

def safe_metric(rows,name,family):
    return score_all(rows,name,family)

def summarize(rows):
    return {name:{family:safe_metric(rows,name,family) for family in FAMILIES}
            for name in NAMES}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--history",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    raw=Path(args.history).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_SHA:
        raise ValueError("FROZEN_ORIGINAL_SHA_DIFFERENT")
    rows=clean_rows(args.history)
    if len(rows)!=4413:
        raise ValueError("FROZEN_SOURCE_COUNT_DIFFERENT")
    season=[r for r in rows if r["season"]=="2025-2026"]
    if len(season)!=3533:
        raise ValueError("ORIGINAL_2025_SEASON_COUNT_CHANGED")
    leagues=collections.defaultdict(list)
    for r in season:
        leagues[r["league"]].append(r)
    if len(leagues)!=10:raise ValueError("TEN_LEAGUES_REQUIRED")
    lock=json.loads((ROOT/"experiments/263/m4_lock.json").read_text())
    setting=use_lock(lock)
    obs=[]
    excluded=collections.Counter()
    asof_days=collections.Counter()
    for league in sorted(leagues):
        rr=sorted(leagues[league],key=lambda z:(z["match_date"],z["fixture_id"]))
        past=[]
        i=0
        while i<len(rr):
            day=rr[i]["match_date"]
            j=i
            while j<len(rr) and rr[j]["match_date"]==day:
                j+=1
            today=rr[i:j]
            # A match cannot be evaluated using itself, same-date teammates, or future results.
            if len(past)>=60:
                forecast=records_for_day(past,today,league,day,setting)
                if len(forecast)!=len(today):
                    raise ValueError("ONE_FORECAST_PER_ELIGIBLE_FIXTURE")
                for f in forecast:
                    f["obs"]=f.pop("y")
                    if f["base"] is None:raise ValueError("MISSING_PREVIOUS_DAY_BASE")
                    for k,m in f["p"].items():
                        if len(m)!=11:raise ValueError("INVALID_MARKET_COVERAGE")
                    obs.append(f)
                asof_days[league]+=1
            else:
                excluded[league]+=len(today)
            past.extend(today)
            i=j
    if len(obs)<2500:
        raise ValueError("UNEXPECTEDLY_SMALL_FULL_HISTORY_ELIGIBLE_COHORT")
    if len({r["id"] for r in obs})!=len(obs):
        raise ValueError("DUPLICATE_CANONICAL_FIXTURE")
    if len(obs)+sum(excluded.values())!=len(season):
        raise ValueError("SOURCE_ACCOUNTING_MISMATCH")
    failures=add_alternatives(obs)
    no_dev=[r for r in obs if not dev_block(r)]
    dev=[r for r in obs if dev_block(r)]
    months=collections.Counter(r["date"][:7] for r in obs)
    coverage=collections.Counter(r["league"] for r in obs)
    periods={
        "2025_26_ALL_EXPLORATORY":obs,
        "EXCLUDING_ORIGINAL_M4_DEV_FOLDS":no_dev,
        "ORIGINAL_M4_DEV_FOLDS_ONLY":dev
    }
    data={
        "schema":"263_INDEPENDENT_FULL_2025_26_CHRONO_WALKFORWARD_V1",
        "source_sha256":EXPECTED_SHA,
        "source_total":len(rows),
        "season_source_total":len(season),
        "eligible_scored":len(obs),
        "excluded_initial_training_rows":sum(excluded.values()),
        "excluded_initial_by_league":dict(sorted(excluded.items())),
        "eligible_by_league":dict(sorted(coverage.items())),
        "prediction_days_by_league":dict(sorted(asof_days.items())),
        "eligible_by_month":dict(sorted(months.items())),
        "dev_fold_dates":[list(p) for p in DEV_WINDOWS],
        "n_original_dev_fold_rows":len(dev),
        "n_without_original_dev_folds":len(no_dev),
        "model_hyperparameters":lock["settings"],
        "coverage_failures":failures,
        "status":"RETROSPECTIVE_ASOF_ONLY_2025_26_HYPERPARAMETER_SELECTION_CONTAMINATION",
        "test_independence":"NO__M4_TUNED_ON_2025_26__MODEL_CANDIDATES_PREVIOUSLY_RESEARCHED",
        "does_not_recompute_880":"YES__2026_27_ALREADY_ARCHIVED_IN_PREVIOUS_RESEARCH",
        "no_live_rewrite":True,
        "blind_test_claimed":False,
        "pinnacle_or_iddaa_value_test":False,
        "periods":{},
        "markets_single_decision":{},
        "per_league":{},
        "paired_block_intervals":{}
    }
    for pname,p in periods.items():
        data["periods"][pname]=summarize(p)
        data["markets_single_decision"][pname]={
            name:decisions(p,name) for name in ("ASOF_LEAGUE_RATE","B","C3","M4","ENSEMBLE_50_50")
        }
    for league in sorted(leagues):
        sample=[r for r in obs if r["league"]==league]
        data["per_league"][league]=summarize(sample)
    # Pair both models on exactly the same match in each target-market family.
    for pname,p in (("all",obs),("excluding_m4_dev_folds",no_dev)):
        data["paired_block_intervals"][pname]={
            name:{
                family:block_interval(p,name,{"MS":"M4","KG":"C3","O25":"C3"}[family],family,nboot=800)
                for family in FAMILIES
            }
            for name in ("ASOF_LEAGUE_RATE","B","C3","M4","ENSEMBLE_50_50",
                         "DC_MINUS_0.1","DC_PLUS_0.1","BIVARIATE_0.15","NB_K3","NB_K8")
        }
    outpath=Path(args.output)
    outpath.parent.mkdir(parents=True,exist_ok=True)
    outpath.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    summary={
        "eligible":len(obs),
        "excluded_initial":sum(excluded.values()),
        "dev_folds":len(dev),
        "not_dev_folds":len(no_dev),
        "overall":{name:{family:data["periods"]["2025_26_ALL_EXPLORATORY"][name][family].get("brier")
                         for family in FAMILIES} for name in ("ASOF_LEAGUE_RATE","B","C3","M4","ENSEMBLE_50_50")},
        "nondev":{name:{family:data["periods"]["EXCLUDING_ORIGINAL_M4_DEV_FOLDS"][name][family].get("brier")
                         for family in FAMILIES} for name in ("ASOF_LEAGUE_RATE","B","C3","M4","ENSEMBLE_50_50")}
    }
    print("FULL_HISTORY_AUDIT="+json.dumps(summary,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
