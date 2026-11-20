"""Empirical reliability of PREMATCH model probabilities, not score-only baselines.

A record must carry the original pre-kickoff model forecast, its immutable
model-prediction SHA, final match result, and result timestamp. This module
does not create backfilled predictions and never uses bookmaker prices.

Research-only until an independently audited historical evidence archive is
available and a walk-forward holdout validates selection.
"""
from __future__ import annotations
import math
from collections import defaultdict
from datetime import datetime, timezone

FAMILIES={"MS1":"MS","MSX":"MS","MS2":"MS",
          "BTTS_YES":"KG","BTTS_NO":"KG",
          "OVER_2.5":"O25","UNDER_2.5":"O25"}

def _time(s):
    t=datetime.fromisoformat(str(s).replace("Z","+00:00"))
    if t.tzinfo is None:raise ValueError("AWARE_TIMESTAMP_REQUIRED")
    return t.astimezone(timezone.utc)

def _okprob(p):
    if isinstance(p,bool) or not isinstance(p,(float,int)) or not math.isfinite(p) or not 0<=p<=1:
        raise ValueError("INVALID_PROBABILITY")
    return float(p)

def validate(records, *, asof):
    """No same-match duplicates, no post-kickoff predictions or future results."""
    cutoff=_time(asof)
    seen=set();out=[]
    for r in records:
        market=r["market"]
        if market not in FAMILIES:raise ValueError("UNKNOWN_MARKET")
        fixture=str(r["fixture_id"]);league=str(r["league"])
        key=(fixture,market)
        if key in seen:raise ValueError("DUPLICATE_FIXTURE_MARKET")
        seen.add(key)
        forecast=_time(r["forecast_created_at_utc"])
        kickoff=_time(r["kickoff_utc"])
        finished=_time(r["result_known_at_utc"])
        if not forecast<kickoff<=finished<cutoff:raise ValueError("FUTURE_OR_RETROACTIVE_EVIDENCE")
        if not isinstance(r.get("forecast_sha256"),str) or len(r["forecast_sha256"])!=64:
            raise ValueError("PREMATCH_FORECAST_SHA_REQUIRED")
        if r.get("forecast_origin")!="SEALED_BEFORE_KICKOFF":
            raise ValueError("NOT_GENUINE_PREMATCH_FORECAST")
        p=_okprob(r["model_probability"])
        actual=r["occurred"]
        if type(actual) is not bool:raise ValueError("ACTUAL_MUST_BE_BOOLEAN")
        out.append({**r,"model_probability":p})
    return out

def similar(records, *, league, market, probability, asof, half_width=.05, min_samples=20):
    """Historical outcomes for the same market and probability neighborhood.

    An empty or sparse group is UNKNOWN, not zero accuracy and not a PAS
    justified by an arbitrary probability floor. The 20 observations are a
    sample-size guard, not a 60% probability gate.
    """
    if market not in FAMILIES:raise ValueError("UNKNOWN_MARKET")
    p=_okprob(probability)
    if not 0<half_width<=.15:raise ValueError("BAD_WINDOW")
    if min_samples<1:raise ValueError("BAD_SAMPLE_MINIMUM")
    rows=validate(records,asof=asof)
    matched=[r for r in rows if r["market"]==market and r["league"]==league
             and abs(r["model_probability"]-p)<=half_width]
    n=len(matched);wins=sum(r["occurred"] for r in matched)
    if n<min_samples:
        return {"status":"INSUFFICIENT_HISTORICAL_PREMATCH_EVIDENCE",
                "market":market,"league":league,"n":n,"wins":wins,
                "window":[round(max(0,p-half_width),5),round(min(1,p+half_width),5)],
                "observed_hit_rate":None,"wilson_lower95":None}
    hit=wins/n
    z=1.959963984540054
    denom=1+z*z/n
    center=(hit+z*z/(2*n))/denom
    half=z*math.sqrt((hit*(1-hit)+z*z/(4*n))/n)/denom
    return {"status":"HISTORICAL_PREMATCH_REFERENCE_AVAILABLE",
            "market":market,"league":league,"n":n,"wins":wins,
            "window":[round(max(0,p-half_width),5),round(min(1,p+half_width),5)],
            "observed_hit_rate":round(hit,6),
            "wilson_lower95":round(max(0,center-half),6)}

def rank_candidates(candidates, records, *, league, asof, min_samples=20):
    """Rank the most likely realized outcome; evidence labels verified vs unverified.

    Do NOT silently equate raw C3 probabilities with calibrated hit rates.
    No fixed 60% or any other model-probability acceptance threshold.
    """
    ranked=[]
    for c in candidates:
        e=similar(records,league=league,market=c["market"],
                  probability=c["calibrated_probability"],asof=asof,
                  min_samples=min_samples)
        ranked.append({**c,"historical_reliability":e,
                       "decision_evidence_status":("HISTORICALLY_EVALUATED" if
                          e["status"]=="HISTORICAL_PREMATCH_REFERENCE_AVAILABLE"
                          else "PROVISIONAL_MODEL_DIRECTION")})
    # User's original objective is MAXIMUM ESTIMATED CHANCE OF OCCURRENCE.
    # Wilson lower bound is an uncertainty display, NOT a value/edge filter
    # or the primary rank target. Verified same-market historical success
    # estimates rank first; provisional raw probability ranks only when there
    # is not yet a validated similar-match sample.
    return sorted(ranked,key=lambda x:(
        x["historical_reliability"]["observed_hit_rate"] is None,
        -(x["historical_reliability"]["observed_hit_rate"]
          if x["historical_reliability"]["observed_hit_rate"] is not None
          else x["calibrated_probability"]),
        -x["historical_reliability"]["n"],
        -x["calibrated_probability"],x["market"]))
