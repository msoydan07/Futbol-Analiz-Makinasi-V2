"""Strict matched-fixture retrospective diagnostics for M4 vs XGBoost.

Not a model selection or learned gate training run; predictions reconstructed
as of each old match, not the actual immutable 2.6.3 forecast cohort.
"""
from __future__ import annotations
import argparse,json,math,random
from pathlib import Path
from collections import defaultdict
from paired_audit import LABELS

def metrics(pairs,model):
    ll=br=acc=0.
    for item in pairs:
        p=item[model];y=item["result"]
        if y not in LABELS:raise ValueError("unknown result")
        v=[float(p[k]) for k in LABELS]
        if abs(sum(v)-1)>1e-5:raise ValueError("bad probabilities")
        ll-=math.log(max(1e-12,float(p[y])))
        br+=sum((v[i]-int(LABELS[i]==y))**2 for i in range(3))
        acc+=int(LABELS[v.index(max(v))]==y)
    return {"n":len(pairs),"logloss":ll/len(pairs),
            "brier":br/len(pairs),"accuracy":acc/len(pairs)}

def run(path,dest):
    data=json.loads(Path(path).read_text(encoding="utf8"))
    if data.get("schema")!="MC_M4_XGB_RETRO_PAIR_V1":
        raise ValueError("unrecognized provenance")
    pairs=data["pairs"]
    if len(pairs)<100 or data["missing_count"]:
        raise ValueError("unpaired results not accepted")
    if len({(x["league"],x["date"],x["home_id"],x["away_id"]) for x in pairs})!=len(pairs):
        raise ValueError("duplicate match")
    by_league=defaultdict(list);by_day=defaultdict(list)
    for r in pairs:
        by_league[r["league"]].append(r)
        by_day[r["date"]].append(r)
    overall={k:metrics(pairs,k) for k in ("m4","xgboost")}
    slices={k:{model:metrics(xs,model) for model in ("m4","xgboost")}
            for k,xs in sorted(by_league.items())}
    # Date-cluster paired bootstrap, not a promotion significance claim.
    deltas=defaultdict(list)
    for r in pairs:
        deltas[r["date"]].append(
            math.log(r["m4"][r["result"]]/r["xgboost"][r["result"]]))
    days=sorted(deltas);rng=random.Random(263);samples=[]
    for _ in range(1200):
        vals=[deltas[days[rng.randrange(len(days))]] for _ in days]
        samples.append(sum(sum(v) for v in vals)/sum(len(v) for v in vals))
    samples.sort()
    result={"schema":"MC_M4_XGB_MATCHED_2026_27_AUDIT_V1",
       "status":"RETROSPECTIVE_ALREADY_VIEWED_NOT_INDEPENDENT",
       "n":len(pairs),
       "overall":overall,"league_slices":slices,
       "xgb_minus_m4_logloss":overall["xgboost"]["logloss"]-overall["m4"]["logloss"],
       "xgb_minus_m4_95pct_date_bootstrap":[samples[29],samples[1169]],
       "meta_training_allowed":False,
       "reason":"441 2026/27 outcomes already inspected; requires earlier out-of-fold pairs, with subsequent untouched evaluation",
       "original_263_sealed_predictions_used":False,
       "incumbent_production_replace":False}
    Path(dest).parent.mkdir(parents=True,exist_ok=True)
    Path(dest).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:result[k] for k in ("n","overall","xgb_minus_m4_logloss",
          "xgb_minus_m4_95pct_date_bootstrap")},indent=2))
    return result

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--input",required=True);a.add_argument("--out",required=True)
    args=a.parse_args();run(args.input,args.out)
