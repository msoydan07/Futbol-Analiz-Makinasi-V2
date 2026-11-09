"""Train a bounded dynamic gate on 2025/26 OOF predictions and compare
against M4, XGBoost and a simple equal blend on 2026/27 *retrospectively*.

The 2026/27 evaluation period has already been inspected. This is an
EXPLORATORY decision diagnostic, not a fresh blind test and not a release.
"""
from __future__ import annotations
import argparse,json,math,random
from pathlib import Path
from collections import defaultdict
from meta_gate import fit_oof,mix,norm
from paired_audit import LABELS

def score(p,label):
    p=norm(p)
    ix=LABELS.index(label)
    return -math.log(float(p[ix])),sum(
        (float(p[j])-int(j==ix))**2 for j in range(3))

def analyze(train_file,evaluation_file,out_file):
    training=json.loads(Path(train_file).read_text(encoding="utf8"))
    ev=json.loads(Path(evaluation_file).read_text(encoding="utf8"))
    if training.get("schema")!="MC_META_GATE_OOF_TRAIN_V1":
        raise ValueError("untrusted OOF schema")
    if ev.get("schema")!="MC_M4_XGB_RETRO_PAIR_V1":
        raise ValueError("untrusted evaluation schema")
    raw=training["pairs"];future=ev["pairs"]
    if any(r["date"]>="2026-07-01" for r in raw):
        raise ValueError("gate sees evaluation future")
    if any(r["date"]<"2026-07-01" for r in future):
        raise ValueError("evaluation overlaps gate training")
    if len(raw)<100 or len(future)<100:
        raise ValueError("too few samples")
    theta=fit_oof(raw,regularization=10.0)
    outcomes=[]
    for row in future:
        m4=row["m4"];xgb=row["xgboost"];y=row["result"]
        dynamic,weight=mix(m4,xgb,theta)
        simple={k:(m4[k]+xgb[k])/2 for k in LABELS}
        outputs={"M4":m4,"XGBoost":xgb,"Fixed50":simple,"DynamicGate":dynamic}
        result={"date":row["date"],"league":row["league"],
                "weight_on_m4":weight}
        for k,p in outputs.items():
            ll,b=score(p,y)
            result[k+"_logloss"]=ll
            result[k+"_brier"]=b
        outcomes.append(result)
    names=("M4","XGBoost","Fixed50","DynamicGate")
    metrics=("logloss","brier")
    means={name:{metric:sum(r[name+"_"+metric] for r in outcomes)/len(outcomes)
                 for metric in metrics} for name in names}
    differences={}
    for base in ("M4","XGBoost","Fixed50"):
        differences["DynamicGate_minus_"+base]={}
        for metric in metrics:
            z=[r["DynamicGate_"+metric]-r[base+"_"+metric] for r in outcomes]
            byday=defaultdict(list)
            for r,d in zip(outcomes,z):byday[r["date"]].append(d)
            days=sorted(byday);rng=random.Random(263);boots=[]
            for _ in range(1200):
                selected=[byday[days[rng.randrange(len(days))]] for _ in days]
                boots.append(sum(sum(v) for v in selected)/sum(len(v) for v in selected))
            boots.sort()
            differences["DynamicGate_minus_"+base][metric]={
                "mean":sum(z)/len(z),
                "date_cluster_95pct":[boots[29],boots[1169]]}
    report={"schema":"MC_DYNAMIC_GATE_EXPLORATORY_V1",
       "status":"HISTORICAL_RETROSPECTIVE_NOT_PROSPECTIVE",
       "trained_on_2025_26_oof_count":len(raw),
       "evaluated_on_2026_27_count":len(future),
       "gate_theta":list(theta),
       "mean_weight_on_M4":sum(x["weight_on_m4"] for x in outcomes)/len(outcomes),
       "weight_on_M4_range":[min(x["weight_on_m4"] for x in outcomes),
                             max(x["weight_on_m4"] for x in outcomes)],
       "models":means,"paired":differences,
       "M4_original_sealed_forecasts_used":False,
       "holdout_previously_viewed":True,
       "production_promotion":False,
       "claim_of_betting_edge":False}
    dest=Path(out_file);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                    encoding="utf8")
    print(json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--train",required=True)
    p.add_argument("--eval",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    analyze(args.train,args.eval,args.out)
