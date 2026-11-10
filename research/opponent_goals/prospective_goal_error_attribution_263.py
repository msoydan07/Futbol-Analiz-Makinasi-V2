"""NEW days only: distinguish marginal goal-fit signals from score-dependence signals.

A read-only observer of the EXISTING new100 SHA-sealed forward forecasts and
human-reviewed full-time results. No new trial/pilot, training, new model,
coefficient change, odds, or replay of the Nov 6-8 completed experiments.

A low mean goal error and a nonzero conditional cross-residual is suggestive,
not proof, of a dependence problem: latent team/context misfit can cause both.
Never grant confidence or auto-promote from this diagnostic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from random import Random
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments/263"))
from forward_c3 import read_aware
from market_fifth_baseline_263 import sealed_payload
from sabah_postmatch_new100_263 import checked_score, scores_for

START=date(2026,11,9)  # Explicit: none of original Nov 6, 7, 8 forward pilot.
MODELS=("B","C2","C3","M4")
MIN_DISTINCT_DAYS=10  # Date-block uncertainty is unavailable below this.
MIN_MATCHES=80         # Prospective descriptive scores are always available.
METRICS=("home_goal_residual","away_goal_residual","total_goal_residual",
         "total_poisson_dispersion_residual","goal_cross_residual",
         "home_zero_residual","away_zero_residual","both_zero_residual",
         "btts_residual","over25_residual")
CANONICAL="263_NEW_DAY_GOAL_ERROR_ATTRIBUTION_READONLY_V1"
class Blocked(ValueError):
    pass

def require(ok,message):
    if not ok:raise Blocked(message)

def _is_new_day(name):
    try:return date.fromisoformat(name)>=START
    except (ValueError,TypeError):return False

def _source_files(root,base):
    folder=root/base
    if not folder.exists():return []
    # Ignore old Nov 6-8 files *before opening their bytes*.
    return sorted(p for p in folder.glob("*/*.json")
                  if _is_new_day(p.parent.name))

def _checked_forecasts(root):
    found={};identities=set()
    for path in _source_files(root,"forward_morning_263"):
        require(re.fullmatch(r"[0-9a-f]{24}",path.stem) is not None,
                "INVALID_SEALED_FORECAST_FILE_NAME")
        f=json.loads(path.read_text(encoding="utf-8"))
        sealed_payload(f,"quad_forward_263_v1")
        fixture=f.get("fixture",{})
        require(fixture.get("match_local_date")==path.parent.name,
                "FORECAST_DATE_PATH_NOT_MATCHING")
        require(fixture.get("fixture_verification")=="VERIFIED_BY_LIVE_OFFICIAL_GATE",
                "NON_OFFICIAL_PREMATCH_FIXTURE")
        made=read_aware(f["created_at_utc"])
        checked=read_aware(fixture["source_checked_at_utc"])
        kickoff=read_aware(fixture["kickoff_utc"])
        require(made<kickoff and checked<kickoff and checked<=made+timedelta(seconds=60),
                "FORECAST_AFTER_KICKOFF_OR_UNTRUSTED_CLOCK")
        require(made.date()>=START and kickoff.date()>=START,
                "PREVIOUS_WEEKEND_FORECAST_CANNOT_ENTER_NEW_DAYS")
        key=(fixture["league"],fixture["home_id"],fixture["away_id"],
             fixture["match_local_date"],fixture["kickoff_utc"])
        require(key not in identities,"DUPLICATE_FIXTURE_OR_NEW_DAY_FORECAST")
        identities.add(key)
        sha=f["payload_sha256"]
        require(sha not in found,"DUPLICATE_PREMATCH_SHA")
        require(set(f.get("model_predictions",{}))==set(MODELS),
                "B_C2_C3_M4_REQUIRED")
        found[sha]=f
    return found

def _checked_scores(root,forecasts,now):
    observations={}
    for path in _source_files(root,"experiments/263/sabah_postmatch_inputs"):
        raw=json.loads(path.read_text(encoding="utf-8"))
        s=checked_score(raw,now)
        require(s["forecast_sha256"] in forecasts,
                "RESULT_NOT_FOR_NEW_DAY_SEALED_FORECAST")
        require(s["forecast_sha256"] not in observations,
                "DUPLICATE_RESULT_ATTESTATION")
        f=forecasts[s["forecast_sha256"]]
        require(path.parent.name==f["fixture"]["match_local_date"],
                "RESULT_FILE_DAY_NOT_MATCHING_SEAL")
        # Existing production-safe scorer enforces SHA, both team IDs, league,
        # exact kickoff, reviewed result and pre-kickoff evidence chronology.
        scores_for(f,s)
        observations[s["forecast_sha256"]]=s
    return observations

def independent_m4_probabilities(lh,la):
    require(all(type(v) in (int,float) and math.isfinite(v) and .05<=v<=5
                for v in (lh,la)),"M4_LAMBDAS_OUT_OF_FROZEN_RANGE")
    total=lh+la
    return {
        "BTTS_YES":(-math.expm1(-lh))*(-math.expm1(-la)),
        "OVER_2.5":-math.expm1(-total)-math.exp(-total)*(total+total*total/2),
        "home_zero":math.exp(-lh),
        "away_zero":math.exp(-la),
        "both_zero":math.exp(-total),
    }

def _metrics(f,observation):
    fg=f["fixture"]
    scored=scores_for(f,observation)
    model=f["model_predictions"]["M4"]
    require(model.get("status")=="AVAILABLE","M4_UNAVAILABLE_NO_LAMBDA_ATTRIBUTION")
    goals=model["goals"]
    lh,la=goals["lambda_home"],goals["lambda_away"]
    independent=independent_m4_probabilities(lh,la)
    published=goals["markets"]
    for market in ("BTTS_YES","OVER_2.5"):
        value=published.get(market)
        require(type(value) in (int,float) and math.isfinite(value)
                and abs(value-independent[market])<1e-9,
                "MARKET_NOT_DERIVED_FROM_SAME_M4_LAMBDAS_"+market)
    h,a=observation["home_goals"],observation["away_goals"]
    expected=lh+la
    actual=h+a
    outcomes={"btts":int(h>0 and a>0),"over25":int(actual>=3)}
    diag={
        "home_goal_residual":h-lh,
        "away_goal_residual":a-la,
        "total_goal_residual":actual-expected,
        # Mean of (Y - lambda)^2 - lambda should be 0 for a correct
        # conditional Poisson total; mean bias also influences this metric.
        "total_poisson_dispersion_residual":(actual-expected)**2-expected,
        "goal_cross_residual":(h-lh)*(a-la),
        "home_zero_residual":int(h==0)-independent["home_zero"],
        "away_zero_residual":int(a==0)-independent["away_zero"],
        "both_zero_residual":int(h==0 and a==0)-independent["both_zero"],
        "btts_residual":outcomes["btts"]-independent["BTTS_YES"],
        "over25_residual":outcomes["over25"]-independent["OVER_2.5"],
    }
    comparisons={}
    for other in ("B","C2","C3"):
        if other not in scored["market_scores"] or "M4" not in scored["market_scores"]:
            continue
        for market in ("BTTS","OVER_2.5"):
            p=scored["market_scores"]
            comparisons[f"{other}_minus_M4_{market}_brier"]=(p[other][market]["brier"]
                                                              -p["M4"][market]["brier"])
    return {
        "forecast_sha256":f["payload_sha256"],
        "league":fg["league"],
        "date":fg["match_local_date"],
        "score":[h,a],
        "m4_lambda_home":lh,
        "m4_lambda_away":la,
        "m4_btts_probability":independent["BTTS_YES"],
        "m4_over25_probability":independent["OVER_2.5"],
        "m4_btts_brier":(outcomes["btts"]-independent["BTTS_YES"])**2,
        "m4_over25_brier":(outcomes["over25"]-independent["OVER_2.5"])**2,
        "diagnostics":diag,
        "paired_comparisons":comparisons,
        "result_provenance":observation["verification_scope"],
    }

def _mean(items):
    return sum(items)/len(items) if items else None

def _day_ci(rows,field,*,samples=600,seed=20261111):
    """Resample DAYS, never games; no CI on a tiny number of independent dates."""
    if len(rows)<MIN_MATCHES:return None
    groups=defaultdict(list)
    for r in rows:groups[r["date"]].append(r[field])
    if len(groups)<MIN_DISTINCT_DAYS:return None
    dates=sorted(groups);rng=Random(seed)
    drawn=[]
    for _ in range(samples):
        blocks=[groups[dates[rng.randrange(len(dates))]] for _ in dates]
        numbers=[x for block in blocks for x in block]
        drawn.append(_mean(numbers))
    drawn.sort()
    return {"low":drawn[int(.025*samples)],
            "high":drawn[int(.975*samples)-1],
            "method":"day_block_bootstrap",
            "resamples":samples,"distinct_days":len(dates)}

def _in_interval(ci):
    return ci is not None and not (ci["low"]<=0<=ci["high"])

def attribution_report(root=ROOT,now=None):
    root=Path(root)
    now=now or datetime.now(timezone.utc)
    require(now.tzinfo is not None,"AWARE_CLOCK_REQUIRED")
    now=now.astimezone(timezone.utc)
    forecasts=_checked_forecasts(root)
    observations=_checked_scores(root,forecasts,now)
    completed=[];pending=[];missing_m4=[]
    for sha,f in sorted(forecasts.items()):
        if sha not in observations:
            pending.append(sha)
            continue
        if f["model_predictions"]["M4"].get("status")!="AVAILABLE":
            missing_m4.append(sha)
            continue
        completed.append(_metrics(f,observations[sha]))
    days=sorted({r["date"] for r in completed})
    aggregate={}
    for name in METRICS:
        samples=[{"date":r["date"],"value":r["diagnostics"][name]} for r in completed]
        aggregate[name]={
            "n":len(samples),
            "mean":_mean([r["value"] for r in samples]),
            "date_block_95pct_interval":_day_ci(samples,"value")
        }
    summaries={}
    for m in ("m4_btts_brier","m4_over25_brier"):
        summaries[m]=_mean([r[m] for r in completed])
    for other in ("B","C2","C3"):
        for market in ("BTTS","OVER_2.5"):
            key=f"{other}_minus_M4_{market}_brier"
            matched=[{"date":r["date"],"value":r["paired_comparisons"][key]}
                     for r in completed if key in r["paired_comparisons"]]
            summaries[key]={
                "n_same_matches":len(matched),
                "other_minus_M4_positive_favors_M4":_mean([x["value"] for x in matched]),
                "date_block_95pct_interval":_day_ci(matched,"value")
            }
    enough=len(completed)>=MIN_MATCHES and len(days)>=MIN_DISTINCT_DAYS
    lambda_bias=any(_in_interval(aggregate[name]["date_block_95pct_interval"])
                    for name in ("home_goal_residual","away_goal_residual",
                                 "total_goal_residual"))
    dependence_flag=_in_interval(aggregate["goal_cross_residual"]["date_block_95pct_interval"])
    dispersion_flag=_in_interval(
        aggregate["total_poisson_dispersion_residual"]["date_block_95pct_interval"])
    if enough:
        if lambda_bias:
            triage="GOAL_LAMBDA_BIAS_SIGNAL_CHECK_FIRST_NO_AUTO_FIX"
        elif dependence_flag or dispersion_flag:
            triage="RESIDUAL_DEPENDENCE_OR_DISPERSION_SIGNAL_NOT_CAUSAL_PROOF"
        else:
            triage="NO_DECISIVE_DIAGNOSTIC_SIGNAL_NO_AUTO_FIX"
    else:
        triage="NEW_INDEPENDENT_DATES_INSUFFICIENT_FOR_DIAGNOSTIC_CI"
    return {
        "schema":CANONICAL,
        "status":"PROSPECTIVE_OBSERVER_ONLY_NO_MODEL_CHANGE",
        "eligible_created_and_fixture_date_from":"2026-11-09",
        "registered_new_day_sealed_forecasts":len(forecasts),
        "eligible_finished_reviewed_results":len(completed),
        "finished_missing_M4":len(missing_m4),
        "pending_results":len(pending),
        "distinct_new_match_dates":len(days),
        "observed_match_dates":days,
        "evidence_grade":"HUMAN_ATTESTED_OFFICIAL_PAGE_NOT_NETWORK_REVERIFIED",
        "source_outcomes_from_existing_postmatch_contract":True,
        "no_nov6_7_8_reevaluation":True,
        "day_block_interval_minimum_distinct_dates":MIN_DISTINCT_DAYS,
        "day_block_interval_minimum_matches":MIN_MATCHES,
        "diagnostics":aggregate,
        "mean_market_brier_and_paired_models":summaries,
        "triage_hypothesis_not_model_decision":triage,
        "causal_lambda_vs_dependence_identification_proven":False,
        "forecasts_or_model_modified":False,
        "new_pilot_registered":False,
        "automatic_model_promotion":False,
        "betting_authorized":False,
        "per_match":completed,
        "limitations":[
            "All source results are existing human-attested postmatch observations; no live source network verification by this job.",
            "No Nov 6-8 seals or outcomes are scored: old pilot comparisons are not repeated.",
            "Even a near-zero aggregate goal residual does NOT establish individual lambda calibration.",
            "Cross-goal and zero-goal residuals can reflect omitted context or lambda errors, not uniquely goal dependence.",
            "Date-block CIs only begin at 10 distinct dates and 80 matched games; they do not authorize promotion or betting.",
            "Four-model market Brier is compared ONLY on same eligible matches; a missing model remains missing."]
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    p.add_argument("--root",default=".")
    args=p.parse_args()
    report=attribution_report(Path(args.root))
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,indent=2,allow_nan=False)
        f.write("\n")
    print(json.dumps({
        "status":report["status"],
        "new_day_seals":report["registered_new_day_sealed_forecasts"],
        "new_day_reviewed_results":report["eligible_finished_reviewed_results"],
        "distinct_days":report["distinct_new_match_dates"],
        "diagnostic":report["triage_hypothesis_not_model_decision"],
        "model_changed":False,
    },ensure_ascii=False))

if __name__=="__main__":
    main()
