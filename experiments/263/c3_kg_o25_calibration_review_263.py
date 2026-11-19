"""C3 KG and 2.5 goals calibration audit using ONLY frozen prior dev weights.

August/September 2026: 587 development matches (580 C3 coverage).
October: 293 retrospective as-of evaluations (previously researched).
Nov 8: 39 previously SHA-sealed prematch forecasts, one day, scored only
AFTER fixing historical weights; NOT an independent final blinded trial.

Never refit C3/M4, open bookmaker data, edit SHA, choose odds, or run pilots.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from chrono_goal_stage2_263 import load_predictions
from model_first_decision_263 import verified, EvidenceError

REPO=Path(__file__).resolve().parents[2]
LOCK_REL="experiments/263/forward_dev_calibration_lock_263.json"
NOV_REL="data/results_only_263/nov8_new100_terminal_archive_20261112.json"
NOV_BASE="experiments/263/sabah_research/new100/2026-11-08"
WANTED=("BTTS_YES","OVER_2.5")
DEV_BEFORE="2026-10-01"
OCT_END="2026-10-30"
NOV_DAY="2026-11-08"

def _prob(x):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or not 0<=x<=1:
        raise ValueError("INVALID_MARKET_PROBABILITY")
    return float(x)

def _record(day,league,market,p,b,y,source):
    # Input is a pair of complete binary events: the NO/UNDER complement is
    # implied, ensuring the calibrated results cannot violate 100% total.
    p,b=_prob(p),_prob(b)
    if y not in (0,1) or isinstance(y,bool):raise ValueError("INVALID_RESULT")
    if market not in WANTED:raise ValueError("INVALID_MARKET")
    return {"day":day,"league":league,"market":market,"raw":p,"base":b,
            "outcome":y,"source":source}

def _accepted_lock(path):
    d=json.loads(Path(path).read_text(encoding="utf-8"))
    from model_first_decision_263 import digest
    if (d.get("schema")!="263_forward_dev_calibration_lock_v1"
        or d.get("official_approval") is not False
        or d.get("development_period")!="2026-08-01/2026-09-30"
        or d.get("evaluation_period_not_used_for_weights")!="2026-10-01/2026-10-29"
        or digest({k:v for k,v in d.items() if k!="payload_sha256"})!=d.get("payload_sha256")):
        raise ValueError("FROZEN_DEV_LOCK_INVALID")
    pairs={"BTTS_YES":"BTTS_NO","OVER_2.5":"UNDER_2.5"}
    result={}
    for market,reverse in pairs.items():
        cell=d["calibration"]["C3"][market]
        reverse_cell=d["calibration"]["C3"][reverse]
        w=cell.get("weight")
        if (cell!=reverse_cell or cell.get("available") is not True
            or cell.get("n")!=580 or not isinstance(w,(int,float))
            or isinstance(w,bool) or not 0<w<1):
            raise ValueError("FROZEN_C3_PAIR_WEIGHT_INVALID")
        result[market]=float(w)
    return result,d["payload_sha256"]

def _score_one(row,weight):
    p,b,y=row["raw"],row["base"],row["outcome"]
    q=b+weight*(p-b)
    if not -1e-12 <= q <= 1+1e-12:raise ValueError("CALIBRATION_OUT_OF_BOUNDS")
    return _prob(min(1,max(0,q)))

def _brier(p,y):
    return (p-y)**2

def _logloss(p,y):
    p=min(1-1e-12,max(1e-12,p))
    return -math.log(p if y else 1-p)

def _rel_bins(rows,method,weight):
    bins=[]
    for i in range(10):
        xs=[x for x in rows if min(9,int(_score_one(x,weight) * 10
                 if method=="frozen" else (x["raw"] if method=="raw" else x["base"])*10))==i]
        if not xs:continue
        prob=[_score_one(x,weight) if method=="frozen"
              else x["raw"] if method=="raw" else x["base"] for x in xs]
        bins.append({"interval":f"{i*10}-{(i+1)*10}%",
                     "n":len(xs),
                     "avg_predicted":round(sum(prob)/len(xs),5),
                     "realized":round(sum(x["outcome"] for x in xs)/len(xs),5)})
    return bins

def summarize(records,market,weight):
    rows=[r for r in records if r["market"]==market]
    if not rows:return {"n":0}
    n=len(rows)
    output={"n":n,"distinct_days":len({x["day"] for x in rows}),
            "actual_yes_rate":round(sum(x["outcome"] for x in rows)/n,6),
            "methods":{}}
    for method in ("raw","frozen","baseline"):
        ps=[r["raw"] if method=="raw" else r["base"] if method=="baseline"
            else _score_one(r,weight) for r in rows]
        bs=sum(_brier(p,r["outcome"]) for p,r in zip(ps,rows))/n
        ll=sum(_logloss(p,r["outcome"]) for p,r in zip(ps,rows))/n
        bins=_rel_bins(rows,method,weight)
        ece=sum(x["n"]/n*abs(x["avg_predicted"]-x["realized"]) for x in bins)
        output["methods"][method]={"brier":round(bs,8),"logloss":round(ll,8),
             "ece10_descriptive":round(ece,6),
             "mean_prediction":round(sum(ps)/n,6),
             "reliability_bins":bins}
    output["raw_minus_frozen_brier"]=round(
        output["methods"]["raw"]["brier"]-output["methods"]["frozen"]["brier"],8)
    output["raw_minus_frozen_logloss"]=round(
        output["methods"]["raw"]["logloss"]-output["methods"]["frozen"]["logloss"],8)
    return output

def paired_date_bootstrap(rows,weight,*,reps=1600,seed=26320):
    # Paired, by match-day to avoid pseudo-confidence when league results
    # within one football weekend are correlated.
    if not rows:return None
    buckets=defaultdict(list)
    for r in rows:
        buckets[r["day"]].append(_brier(r["raw"],r["outcome"])-
                                _brier(_score_one(r,weight),r["outcome"]))
    days=sorted(buckets)
    if len(days)<4:
        return {"available":False,"reason":"FEWER_THAN_FOUR_DISTINCT_MATCH_DAYS"}
    rng=random.Random(seed)
    draws=[]
    for _ in range(reps):
        selected=[rng.choice(days) for __ in days]
        diffs=[v for day in selected for v in buckets[day]]
        draws.append(sum(diffs)/len(diffs))
    draws.sort()
    original=[v for day in days for v in buckets[day]]
    return {"available":True,"n":len(original),"days":len(days),
            "mean_raw_minus_frozen_brier":round(sum(original)/len(original),8),
            "ci95":[round(draws[int(.025*reps)],8),round(draws[int(.975*reps)],8)],
            "positive_ci_implies_frozen_better":draws[int(.025*reps)]>0}

def from_880(path):
    rows=load_predictions(path)
    if len(rows)!=880:raise ValueError("CHRONO_880_COUNT_CHANGED")
    dev=[];october=[]
    for r in rows:
        d=r["date"]
        if d>=OCT_END:raise ValueError("LATE_RETROSPECTIVE_DATE")
        if "C3" not in r["p"]:continue
        for market in WANTED:
            z=_record(d,r["league"],market,
                    r["p"]["C3"][market],r["base"][market],r["obs"][market],
                    "RETROSPECTIVE_STRICT_PREVIOUS_DATE")
            (dev if d<DEV_BEFORE else october).append(z)
    if len(dev)!=580*2 or len(october)!=293*2:
        raise ValueError("C3_ORIGINAL_RETRO_COVERAGE_CHANGED")
    return dev,october

def _nov8_source(root):
    archive=json.loads((root/NOV_REL).read_text(encoding="utf-8"))
    if (archive.get("schema")!="263_NOV8_NEW100_POSTMATCH_TERMINAL_ARCHIVE_V1"
        or archive.get("registered")!=40 or archive.get("completed")!=39
        or archive.get("postponed")!=1 or archive.get("human_attestation_count")!=0):
        raise ValueError("NOVEMBER_ARCHIVE_STATUS_CHANGED")
    out=[]
    grades=Counter()
    for row in archive["rows"]:
        if row.get("score") is None:continue
        src=root/row["forecast_path"]
        f=verified(json.loads(src.read_text(encoding="utf-8")),"quad_forward_263_v1")
        if f["payload_sha256"]!=row["forecast_sha256"]:
            raise ValueError("ORIGINAL_SHA_CHANGED")
        bpath=root/NOV_BASE/src.stem/"baseline.json"
        b=verified(json.loads(bpath.read_text(encoding="utf-8")),"263_asof_market_baseline_v2")
        if (b["forecast_sha256"]!=f["payload_sha256"] or b["league"]!=row["league"]
            or b["last_result_date"]>=NOV_DAY or
            f["fixture"]["match_local_date"]!=NOV_DAY or
            f["fixture"]["kickoff_utc"]!=row["kickoff_utc"] or
            datetime.fromisoformat(f["created_at_utc"])>=datetime.fromisoformat(row["kickoff_utc"])):
            raise ValueError("NOV_BASELINE_OR_FIXTURE_NOT_ASOF")
        c3=f["model_predictions"].get("C3",{})
        if c3.get("status")!="AVAILABLE":raise ValueError("NOV_C3_UNAVAILABLE")
        markets=c3["goals"]["markets"]
        score=row["score"]
        if (not isinstance(score,list) or len(score)!=2 or
            any(type(s)!=int or s<0 or s>30 for s in score)):
            raise ValueError("NOV_RESULT_INVALID")
        h,a=score
        grades[row["evidence_grade"]]+=1
        out.append(_record(NOV_DAY,row["league"],"BTTS_YES",
                           markets["BTTS_YES"],b["markets"]["BTTS_YES"],
                           int(h>0 and a>0),"ORIGINAL_PREMATCH_SHA"))
        out.append(_record(NOV_DAY,row["league"],"OVER_2.5",
                           markets["OVER_2.5"],b["markets"]["OVER_2.5"],
                           int(h+a>=3),"ORIGINAL_PREMATCH_SHA"))
    if len(out)!=39*2:raise ValueError("NOV_39_NOT_AVAILABLE")
    return out,dict(grades)

def evaluate(predictions,*,root=REPO):
    weights,lock_sha=_accepted_lock(root/LOCK_REL)
    dev,october=from_880(predictions)
    nov,grades=_nov8_source(root)
    aggregate={"schema":"263_C3_KG_O25_FROZEN_DEV_SHRINK_CROSS_PERIOD_V1",
        "frozen_lock_sha256":lock_sha,"source":"4413_HISTORICAL_SHA_PLUS_ORIGINAL_NOV8_SEALS",
        "validation":{"development_n":len(dev)//2,"october_n":len(october)//2,
                      "november_sha_n":len(nov)//2},
        "weights":{"KG":weights["BTTS_YES"],"OVER_2.5":weights["OVER_2.5"]},
        "source_grade_breakdown_nov8":grades,
        "periods":{},"confidence_october":{}}
    for period,records in (("development",dev),("october_previous_researched",october),
                           ("november8_SHA_previously_scored",nov)):
        aggregate["periods"][period]={m:summarize(records,m,weights[m]) for m in WANTED}
    for market in WANTED:
        aggregate["confidence_october"][market]=paired_date_bootstrap(
            [r for r in october if r["market"]==market],weights[market])
    # Pre-declared engineering gate: no post-hoc optimizing weights on Oct/Nov.
    def pass_period(period,market):
        s=aggregate["periods"][period][market]
        return s["raw_minus_frozen_brier"]>0 and s["raw_minus_frozen_logloss"]>=-0.002
    outcome={}
    for market in WANTED:
        oc=aggregate["confidence_october"][market]
        wins=pass_period("october_previous_researched",market) and pass_period(
            "november8_SHA_previously_scored",market)
        outcome[market]={
           "oct_and_nov_brier_improve_and_logloss_not_materially_worse":wins,
           "october_date_block_ci_excludes_zero":oc["available"] and
                 oc["positive_ci_implies_frozen_better"],
           "recommendation":"RESEARCH_ONLY_HOLD_OLD_C3" if not (wins and
                 oc["available"] and oc["positive_ci_implies_frozen_better"])
                 else "RESEARCH_VALIDATED_CANDIDATE_NEEDS_UNSEEN_FORWARD_CONFIRMATION"}
    aggregate.update({
        "recommendation":outcome,
        "not_independent_blind_final_holdout":True,
        "historical_october_previously_seen":True,
        "sealed_november_source_day_count":1,
        "odds_not_used":True,"no_new_pilot":True,
        "B_C2_C3_M4_model_formulas_changed":False,
        "main_M4_changed":False,"historical_seals_changed":False,
        "production_decision_changed":False,
        "no_closing_line_or_ev":True,
        "warnings":[
            "All calibrated probabilities are frozen-AUG/SEP shrinkage toward strictly as-of league baseline.",
            "No odds, match outcomes or future data used as inputs at match decision time.",
            "Oct retrospective outcomes have been explored before, thus not a clean final holdout.",
            "November8 outcomes only 39 completed matches, all from one match day; result grades vary.",
            "Do not train or adjust thresholds after looking at October or November scores.",
            "Check log-loss and Brier, not accuracy alone; goal Over and Under are complements.",
            "A lower Brier does not constitute reliable betting income."
        ]})
    return aggregate

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--predictions",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=evaluate(a.predictions)
    dest=Path(a.output)
    if dest.exists():raise ValueError("NEVER_OVERWRITE_RESEARCH")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,sort_keys=True,ensure_ascii=False,
                               indent=2,allow_nan=False)+"\n",encoding="utf-8")
    brief={"cohorts":report["validation"],"weights":report["weights"],
       "nov_source_grades":report["source_grade_breakdown_nov8"],
       "comparison":{period:{
           m:{"n":q["n"],"raw_brier":q["methods"]["raw"]["brier"],
              "shrink_brier":q["methods"]["frozen"]["brier"],
              "base_brier":q["methods"]["baseline"]["brier"],
              "raw_logloss":q["methods"]["raw"]["logloss"],
              "shrink_logloss":q["methods"]["frozen"]["logloss"],
              "raw_ece":q["methods"]["raw"]["ece10_descriptive"],
              "shrink_ece":q["methods"]["frozen"]["ece10_descriptive"]}
           for m,q in groups.items()} for period,groups in report["periods"].items()},
       "bootstrap":report["confidence_october"],
       "recommendation":report["recommendation"]}
    print("C3_KG_O25_CALIBRATION_RESULT="+json.dumps(brief,sort_keys=True,
                                                        allow_nan=False))

if __name__=="__main__":
    main()
