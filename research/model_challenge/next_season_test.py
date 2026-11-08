"""Predeclared next-season check: all competitors evaluated on identical
new 2026/27 fixtures from the ALREADY PINNED OpenFootball commit.

This is NOT a new post-2026-09-22 result feed. Only eight league files
exist at that pinned commit; missing league-seasons are explicit.
Parameters are frozen: Elo default, Poisson half-life=365/prior=6,
XGBoost depth3/210 trees/0.025 eta/weight20; hybrid equal weights.
XGBoost refits on all previous-season records ONLY, with no 2026/27
labels used in fitting/tuning. Date-batched features prevent same-day leak.
"""
from __future__ import annotations
import argparse,csv,json,math
from collections import defaultdict
from datetime import date
from pathlib import Path
from ingest_openfootball import BASE, get_json, normalize_one, Reject
from elo_baseline import predict_stream
from poisson_challenger import predict as poisson_predict
from xgb_challenger import make_features, fit, probabilities, LABEL
from frozen_stress_audit import scoring

AVAILABLE={"GER1":"de.1","ENG1":"en.1","ENG2":"en.2",
           "ESP1":"es.1","FRA1":"fr.1","ITA1":"it.1",
           "NED1":"nl.1","POR1":"pt.1"}
PARAMS={"max_depth":3,"n_estimators":210,"learning_rate":.025,
        "min_child_weight":20}
NEW_START="2026-07-01"
FIELDS=("league","season","date","home","away","home_goals","away_goals",
        "source_file","source_sha256")
def key(r):
    return tuple(r[x] for x in ("league","date","home","away"))
def load_archive(path):
    with open(path,encoding="utf8",newline="") as f:rows=list(csv.DictReader(f))
    if any(r["date"] >= NEW_START for r in rows):
        raise ValueError("prior archive overlaps prospective period")
    return rows

def load_next(fetch=get_json):
    rows=[];qa=[]
    for league,code in AVAILABLE.items():
        source="2026-27/"+code+".json"
        doc,dig=fetch(BASE+"/"+source)
        if doc is None:
            qa.append({"league":league,"status":"SOURCE_MISSING","n":0})
            continue
        try:
            rr,missing=normalize_one(doc,league,"2026-27",source,dig,
                                      cutoff=date(2026,9,22))
            rows.extend(x for x in rr if x["date"]>=NEW_START)
            qa.append({"league":league,"status":"ACCEPTED","n":len(rr),
                       "missing":missing,"digest":dig})
        except Reject as e:
            qa.append({"league":league,"status":"REJECTED_QA","n":0,
                       "reason":str(e)})
    return rows,qa

def run(input_path,out_path,fetch=get_json):
    old=load_archive(input_path)
    new,qa=load_next(fetch)
    if not new:raise ValueError("no accepted fresh-season fixtures")
    combined=sorted(old+new,key=lambda r:(r["date"],r["league"],
                                          r["home"],r["away"]))
    known=set()
    for row in combined:
        k=key(row)
        if k in known:raise ValueError("duplicate "+str(k))
        known.add(k)
    needed={key(r) for r in new}
    if len(needed)!=len(new):raise ValueError("duplicate new fixture")
    oldx=[r for r in make_features(combined) if r[3]>=40 and
           r[0]["date"]<NEW_START]
    allx=[r for r in make_features(combined) if key(r[0]) in needed and r[3]>=40]
    if len(oldx)<1000 or not allx:raise ValueError("insufficient warmup")
    # Fit only with labels that existed before any fresh-season fixture.
    model=fit(oldx,PARAMS)
    xgb=dict(zip((key(r[0]) for r in allx),probabilities(model,allx)))
    elo={key(r):r for r in predict_stream(combined) if key(r) in needed}
    poisson={key(r):r for r in poisson_predict(combined,365,6.0)
             if key(r) in needed}
    records=[]
    for row in new:
        k=key(row);a=elo.get(k);b=poisson.get(k);c=xgb.get(k)
        if a is None or b is None or c is None:
            continue
        if not a["valid_warmup"] or not b["valid_warmup"]:
            continue
        label=a["result"]
        if label!=b["result"] or LABEL[label]!=(
            0 if int(row["home_goals"])>int(row["away_goals"]) else
            1 if int(row["home_goals"])==int(row["away_goals"]) else 2):
            raise ValueError("label mismatch")
        probs={"Elo":[a["p_home"],a["p_draw"],a["p_away"]],
               "Poisson":[b["p_home"],b["p_draw"],b["p_away"]],
               "XGBoost":[float(v) for v in c]}
        probs["Hybrid"]=[sum(probs[m][j] for m in ("Elo","Poisson","XGBoost"))/3
                         for j in range(3)]
        r={"league":k[0],"date":k[1],"result":label}
        for name,p in probs.items():
            ll,bs=scoring(p,label)
            r[name+"_logloss"]=ll;r[name+"_brier"]=bs
        records.append(r)
    if len(records)<40:raise ValueError("too few newer scored fixtures")
    def scores(rows):
        return {name:{"logloss":sum(r[name+"_logloss"] for r in rows)/len(rows),
                      "brier":sum(r[name+"_brier"] for r in rows)/len(rows)}
                for name in ("Elo","Poisson","XGBoost","Hybrid")}
    by_league=defaultdict(list)
    for row in records:by_league[row["league"]].append(row)
    result={"schema":"MC_2026_27_NEXT_SEASON_V1",
            "period":"2026-07-01 through 2026-09-22 (pinned source only)",
            "status":"EXPLORATORY_NEXT_SEASON_NOT_CONTEMPORANEOUS",
            "num_fixtures":len(records),"num_leagues":len(by_league),
            "matched_scores":scores(records),
            "league_scores":{k:{"n":len(v),"models":scores(v)}
                             for k,v in sorted(by_league.items())},
            "data_quality":qa,
            "trained_on_previous_seasons_only":True,
            "hyperparams_frozen":PARAMS,
            "market_odds":"NOT_AVAILABLE",
            "2.6.3_head_to_head":"NOT_COMPARABLE",
            "betting_authorized":False}
    out=Path(out_path);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"num_fixtures":result["num_fixtures"],
                      "num_leagues":result["num_leagues"],
                      "matched_scores":result["matched_scores"]},indent=2))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True);p.add_argument("--out",required=True)
    a=p.parse_args();run(a.input,a.out)
