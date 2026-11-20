"""Frozen 2025/26 calibration for C3 KG and O2.5, research-approved v4.

The two coefficients were trained on 2,898 *chronological retrospective*
C3-supported 2025/26 games in the independent math audit. They are frozen;
this module neither refits anything, reads game scores, nor uses prices/xG.

The surrounding SHA-signed model-first lock must activate this explicitly.
Original v3 model-first decision replay does not depend on this module.
"""
from __future__ import annotations
import math

POLICY = "C3_2025_26_TWO_BINARY_LOGIT_FROZEN_V1"
SUPPORTED = {
    "BTTS_YES": {"intercept": 0.120946,
                 "c3_logit": 0.2643173,
                 "previous_league_logit": 0.5012377},
    "OVER_2.5": {"intercept": 0.1100003,
                 "c3_logit": 0.2639998,
                 "previous_league_logit": 0.2514675},
}
TRAIN_N = 2898
TRAIN_SEASON = "2025-2026"

def bounded(p):
    if (isinstance(p, bool) or not isinstance(p,(float,int))
        or not math.isfinite(p) or not 0 <= p <= 1):
        raise ValueError("C3_CALIBRATION_PROBABILITY_INVALID")
    return float(p)

def _logit(p):
    p=max(.0001,min(.9999,bounded(p)))
    return math.log(p/(1-p))

def _sigmoid(z):
    if z>=0:
        return 1/(1+math.exp(-z))
    v=math.exp(z)
    return v/(1+v)

def verify_policy(policy):
    if (not isinstance(policy,dict)
        or policy.get("method")!=POLICY
        or policy.get("train_season")!=TRAIN_SEASON
        or policy.get("train_n")!=TRAIN_N
        or policy.get("only_kg_and_over25") is not True
        or policy.get("same_day_outcomes_forbidden") is not True
        or policy.get("odds_not_used") is not True
        or policy.get("xg_not_used") is not True
        or policy.get("version")!=4):
        raise ValueError("C3_FROZEN_POLICY_NOT_ACCEPTED")
    if policy.get("coefficients")!=SUPPORTED:
        raise ValueError("C3_COEFFICIENTS_CHANGED")
    return policy

def calibrated_binary_pair(p,base,positive,policy):
    """Return normalized positive and negative outcomes of ONE binary family.

    Input b is from the SHA-linked previous-day league-rate snapshot.
    No current result, same-date result, market price, or xG input exists.
    """
    verify_policy(policy)
    if positive not in SUPPORTED:raise ValueError("UNSUPPORTED_MARKET")
    c=SUPPORTED[positive]
    z=(c["intercept"]+c["c3_logit"]*_logit(p)
       +c["previous_league_logit"]*_logit(base))
    yes=_sigmoid(z)
    return yes,1-yes
