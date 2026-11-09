"""Leakage-safe meta selector for paired, timestamped OOF base predictions.

Deliberately imports NO base model fitting routines. Input rows must carry
three-class forecasts from both experts, match result (training only),
and verified generation cutoffs. A fixture's predictions must be generated
before its result and not trained on that outcome.

This prototype fits one feature-only gating rule on train OOF rows:
  p = w*p_M4 + (1-w)*p_XGB, w = sigmoid(theta . features)
Uses only pre-match information: each expert's probability confidence,
entropy, disagreement, strength of favorite, league-specific categorical
features deliberately OMITTED to prevent fragile league-level memorization.
One *global* gate; regularized optimization; no results provided at inference.
No 2.6.3 promotion without an independent same-match chronology test.
"""
from __future__ import annotations
import json
import math
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

LABELS=("H","D","A")

def norm(p):
    if isinstance(p,dict):
        if set(p)!=set(LABELS):
            raise ValueError("probability keys must be H/D/A")
        v=np.array([p[k] for k in LABELS],dtype=float)
    else:
        v=np.asarray(p,dtype=float)
    if v.shape!=(3,) or not np.isfinite(v).all() or (v<=0).any() or abs(v.sum()-1)>1e-5:
        raise ValueError("invalid three-way probability")
    return v/v.sum()

def features(m4,xgb):
    a,b=norm(m4),norm(xgb)
    h=lambda p: -float((p*np.log(p)).sum())/math.log(3)
    return np.array([1.,max(a)-max(b),h(a)-h(b),float(np.abs(a-b).sum()),
                     a[1]-b[1]],dtype=float)

def sigmoid(v):
    v=np.clip(v,-25,25)
    return 1.0/(1.0+np.exp(-v))

def mix(m4,xgb,theta):
    if np.asarray(theta).shape!=(5,) or not np.isfinite(theta).all():
        raise ValueError("invalid gate parameters")
    a,b=norm(m4),norm(xgb)
    w=float(sigmoid(features(a,b)@theta))
    return dict(zip(LABELS,(w*a+(1-w)*b).tolist())),w

@dataclass(frozen=True)
class TrainedGate:
    theta:tuple
    train_rows:int
    source_sha:str

def fit_oof(rows,*,regularization=10.0):
    """Only historical base forecasts that were out-of-fold as-of predictions."""
    if len(rows)<100:
        raise ValueError("not enough paired out-of-fold rows")
    x=[];a=[];b=[];y=[];seen=set()
    for r in rows:
        key=(r["league"],r["date"],r["home_id"],r["away_id"])
        if key in seen:raise ValueError("duplicate training fixture")
        seen.add(key)
        if r.get("forecast_provenance")!="OUT_OF_FOLD_BEFORE_MATCH":
            raise ValueError("in-sample expert forecast cannot train gate")
        if r["trained_history_cutoff"]>=r["date"]:
            raise ValueError("future-trained expert")
        left=norm(r["m4"]);right=norm(r["xgboost"])
        if r["result"] not in LABELS:raise ValueError("unknown label")
        x.append(features(left,right));a.append(left);b.append(right)
        y.append(LABELS.index(r["result"]))
    x=np.stack(x);a=np.stack(a);b=np.stack(b);y=np.array(y)
    def loss(theta):
        w=sigmoid(x@theta)[:,None]
        p=w*a+(1-w)*b
        # Regularize except intercept; fixed strength before holdout.
        return -np.log(np.maximum(1e-12,p[np.arange(len(y)),y])).mean()+(
            regularization*float(np.dot(theta[1:],theta[1:]))/len(y))
    opt=minimize(loss,np.zeros(5),method="L-BFGS-B",options={"maxiter":250})
    if not opt.success:raise ValueError("gate optimization failed")
    return tuple(float(t) for t in opt.x)

def frozen_predict(m4,xgb,theta):
    return mix(m4,xgb,theta)

if __name__=="__main__":
    raise SystemExit("Library module only. Use future fixture gate with verified OOF records.")
