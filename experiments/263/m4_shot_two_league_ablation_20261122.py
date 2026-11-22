#!/usr/bin/env python3
"""Read-only 2-league M4 shot ablation, frozen M4 settings; no existing forecasts touched."""
from __future__ import annotations
import csv, json, math, random, sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "263"))
from m4_integrated import fit_m4, predict_m4, score_markets, Settings
from exp_263_batch import shot_signal

LEAGUES = ("ENG1", "GER1")
TRAIN = "2025-2026"
HOLDOUT = "2026-2027"
BETAS = (0., 0.1, 0.2, 0.3, 0.5)
DEV_FROM = "2026-01-01"
SEED = 20261122

def read_rows():
    path = ROOT / "data" / "quad_accepted_263" / "extended_history.csv"
    with path.open(encoding="utf-8", newline="") as fp:
        rows = [r for r in csv.DictReader(fp) if r["league"] in LEAGUES and r["season"] in (TRAIN, HOLDOUT)]
    assert len(rows) == len({r["fixture_id"] for r in rows}), "duplicated fixture ID"
    for r in rows:
        assert r["home_goals"] and r["away_goals"]
        assert r["result"] == ("H" if int(r["home_goals"]) > int(r["away_goals"]) else "A" if int(r["home_goals"]) < int(r["away_goals"]) else "D")
    return sorted(rows, key=lambda r:(r["league"],r["match_date"],r["fixture_id"]))

def evaluate(p,r):
    ms = p["markets"]["1X2"]
    y = r["result"]
    return {
        "ll": -math.log(max(ms[y],1e-12)),
        "br": sum((ms[k] - (k==y))**2 for k in ("H","D","A")),
        "hit": int(max(("H","D","A"), key=lambda k:ms[k])==y),
    }

def capped(base,delta,beta):
    h,a=base
    if beta == 0: return base
    hh=h*math.exp(beta*delta[0]);aa=a*math.exp(beta*delta[1])
    if not (.05<=hh<=5 and .05<=aa<=5):return None
    return hh,aa

def all_predictions(rows, settings):
    out=[]; stats=defaultdict(int)
    for league in LEAGUES:
        lr=[r for r in rows if r["league"]==league]
        days=defaultdict(list)
        for r in lr:days[r["match_date"]].append(r)
        for d,fixtures in sorted(days.items()):
            if d < DEV_FROM and fixtures[0]["season"]==TRAIN:
                continue
            past=[r for r in lr if r["match_date"] < d]
            if len(past)<60:continue
            model=fit_m4(past,league,d,settings)
            if model is None:
                stats["fit_failures"]+=len(fixtures);continue
            for r in fixtures:
                lam=predict_m4(model,r["home_id"],r["away_id"])
                if lam is None:
                    stats["prediction_failures"]+=1;continue
                signal=shot_signal(past,r["home_id"],r["away_id"],*lam)
                scores={}
                for beta in BETAS:
                    changed=capped(lam,signal,beta) if signal is not None else lam
                    if changed is None: changed=lam
                    scores[beta]=evaluate(score_markets(*changed),r)
                out.append({"league":league,"season":r["season"],"date":d,"fixture_id":r["fixture_id"],
                            "signal_available":signal is not None,"scores":scores})
    return out,dict(stats)

def summarize(records,beta,filter_signal=False):
    rr=[x for x in records if not filter_signal or x["signal_available"]]
    n=len(rr)
    if not n:return {"n":0}
    return {"n":n,"ll":round(sum(x["scores"][beta]["ll"] for x in rr)/n,8),
            "brier":round(sum(x["scores"][beta]["br"] for x in rr)/n,8),
            "hits":sum(x["scores"][beta]["hit"] for x in rr),
            "hit_rate":round(sum(x["scores"][beta]["hit"] for x in rr)/n,6),
            "signal_available":sum(x["signal_available"] for x in rr)}

def boots(records,beta):
    by_day=defaultdict(list)
    for r in records:
        z=r["scores"]
        by_day[r["date"]].append((z[0.]["ll"]-z[beta]["ll"],z[0.]["br"]-z[beta]["br"]))
    dates=sorted(by_day)
    if not dates:return None
    rng=random.Random(SEED)
    diffs=[[],[]]
    for _ in range(1200):
        sample=[rng.choice(dates) for __ in dates]
        ll=br=cnt=0
        for day in sample:
            for x,y in by_day[day]:ll+=x;br+=y;cnt+=1
        diffs[0].append(ll/cnt); diffs[1].append(br/cnt)
    for x in diffs:x.sort()
    return {"days":len(dates),
            "baseline_minus_shots_logloss_ci95":[round(diffs[0][30],8),round(diffs[0][1170],8)],
            "baseline_minus_shots_brier_ci95":[round(diffs[1][30],8),round(diffs[1][1170],8)]}

def run():
    rows=read_rows()
    lock=json.loads((ROOT/"experiments"/"263"/"m4_lock.json").read_text(encoding="utf-8"))
    assert lock["schema"]=="m4_dev_lock_263_v1" and lock["evaluation_season_excluded"]==HOLDOUT
    settings=Settings(**lock["settings"])
    calculated,failures=all_predictions(rows,settings)
    dev=[r for r in calculated if r["season"]==TRAIN and r["date"]>=DEV_FROM]
    test=[r for r in calculated if r["season"]==HOLDOUT]
    assert len(dev)>150 and len(test)>=150,(len(dev),len(test))
    table=[{"beta":b,**summarize(dev,b)} for b in BETAS]
    # freeze beta using ONLY 2025/26 validation; never reselect from 2026/27
    win=min(table,key=lambda x:(x["ll"],x["brier"],x["beta"]))["beta"]
    result={"schema":"m4_shot_ablation_readonly_20261122_v1",
            "source":"data/quad_accepted_263/extended_history.csv",
            "m4_settings":lock["settings"],"leagues":LEAGUES,"betas_preregistered":BETAS,
            "dev_selection":table,"selected_beta":win,"fit_errors":failures,
            "counts":{"source_matches":len(rows),"development":len(dev),"holdout":len(test),
                      "shots_histories":sum(x["signal_available"] for x in test)},
            "holdout":{"baseline":summarize(test,0.),
                       "shots":summarize(test,win),
                       "signal_only_baseline":summarize(test,0.,True),
                       "signal_only_shots":summarize(test,win,True),
                       "paired_ci":boots(test,win)},
            "by_league":{lg:{"baseline":summarize([x for x in test if x["league"]==lg],0.),
                             "shots":summarize([x for x in test if x["league"]==lg],win)}
                         for lg in LEAGUES},
            "interpretation":"M4 MS 1X2 only; existing C3 KG/OU untouched. Chronological, same-day excluded, holdout season excluded from coefficient choice.",
            "limit":"Holdout 2026/27 already explored historically; not a new blinded prospective cohort. Data coverage to early Nov 2026."}
    assert result["holdout"]["baseline"]["n"]==result["holdout"]["shots"]["n"]
    print("M4_SHOT_ABLATION_RESULT_START")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print("M4_SHOT_ABLATION_RESULT_END")
    return result
if __name__=="__main__":run()
