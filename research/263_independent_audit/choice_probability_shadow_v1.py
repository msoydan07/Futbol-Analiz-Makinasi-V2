"""Candidate-only 2.6.3 main choice selector.

Inputs are pre-match predictions, previously-known match scores, and a frozen
model-version family. No odds, xG, betting stake, or post-match information.
"""
from __future__ import annotations
import bisect
import collections
import math

GROUPS={"MS":("MS1","MSX","MS2"),
        "KG":("BTTS_YES","BTTS_NO"),
        "O25":("OVER_2.5","UNDER_2.5")}
SEVEN=GROUPS["MS"]+GROUPS["KG"]+GROUPS["O25"]
POS=("BTTS_YES","OVER_2.5")

def assert_vector(p):
    if set(p)!=set(SEVEN):raise ValueError("MISSING_OR_EXTRA_EVENT")
    if any(not isinstance(v,(int,float)) or not math.isfinite(v)
           or not 0<=v<=1 for v in p.values()):raise ValueError("BAD_PROB")
    for keys in GROUPS.values():
        if abs(sum(p[k] for k in keys)-1)>1e-5:raise ValueError("NOT_A_FAMILY_DISTRIBUTION")

def c3_family_vector(ms,c3_yes,c3_over):
    p=dict(ms)
    p.update({"BTTS_YES":c3_yes,"BTTS_NO":1-c3_yes,
              "OVER_2.5":c3_over,"UNDER_2.5":1-c3_over})
    assert_vector(p)
    return p

def with_adjusted_binary(p,kg,over):
    return c3_family_vector({k:p[k] for k in GROUPS["MS"]},kg,over)

def shrink_binary(p,base,w):
    if not 0<=w<=1:raise ValueError("WEIGHT")
    return with_adjusted_binary(p,w*p["BTTS_YES"]+(1-w)*base["BTTS_YES"],
                               w*p["OVER_2.5"]+(1-w)*base["OVER_2.5"])

def mix_binary(a,b,w):
    if not 0<=w<=1:raise ValueError("WEIGHT")
    assert_vector(a);assert_vector(b)
    return with_adjusted_binary(a,
        w*a["BTTS_YES"]+(1-w)*b["BTTS_YES"],
        w*a["OVER_2.5"]+(1-w)*b["OVER_2.5"])

class HistoricalC3Index:
    """Date-gated same-model C3 actuals: no MS use, no same-day data."""
    def __init__(self):
        self.arr={key:[] for key in POS}
        self.latest_day=None
        self.count=0
    def add_batch(self,rows):
        if not rows:return
        day=rows[0]["date"]
        if any(r["date"]!=day for r in rows):raise ValueError("MULTIDAY_BATCH")
        if self.latest_day is not None and not self.latest_day<day:
            raise ValueError("DATE_LEAKAGE_OR_OUT_OF_ORDER")
        for r in rows:
            c3=r["p"].get("C3")
            if c3 is None:continue
            for key in POS:
                bisect.insort(self.arr[key],(float(c3[key]),int(r["obs"][key])))
            self.count+=1
        self.latest_day=day
    def estimate(self,key,p,prior=80,min_n=30):
        if key not in POS or not 0<=p<=1:raise ValueError("BAD_QUERY")
        if prior<=0 or min_n<0:raise ValueError("BAD_SMOOTHING")
        arr=self.arr[key]
        lo=bisect.bisect_left(arr,(p-.05,-1))
        hi=bisect.bisect_right(arr,(p+.05,2))
        n=hi-lo
        if n<min_n:return p,n
        wins=sum(y for _,y in arr[lo:hi])
        return (prior*p+wins)/(prior+n),n

def choose(p,probability_source="UNRATED"):
    assert_vector(p)
    keys=sorted(SEVEN,key=lambda k:(-p[k],k))
    main,runner=keys[:2]
    family=next(f for f,k in GROUPS.items() if main in k)
    alternate=next((k for k in keys[1:] if k not in GROUPS[family]),None)
    return {
        "main":main,"main_probability":round(p[main],9),
        "alternative":alternate,
        "alternative_probability":round(p[alternate],9) if alternate else None,
        "runner_up":runner,"runner_up_probability":round(p[runner],9),
        "gap_pp":round((p[main]-p[runner])*100,4),
        "near_tie":(p[main]-p[runner])<=.02,
        "near_tie_is_not_automatic_pas":True,
        "probability_method":probability_source,
        "price_used":False,"no_guaranteed_hit":True,
    }
