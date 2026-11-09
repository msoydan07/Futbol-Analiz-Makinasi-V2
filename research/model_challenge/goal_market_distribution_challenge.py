"""Research-only coherent goals/BTTS challenger experiment, 2.6.3.

ONE experiment, frozen candidate grid, chronology-safe weekly M4 prediction.
Original model: unchanged M4 lambda + independent Poisson.
Three challenger families, all internally coherent JOINT-SCORE distributions:
  - Shared-goal-rate scalar on lambda_home/lambda_away
  - Dixon-Coles low-score dependence correction (rho)
  - Bivariate Poisson common-goal covariance (covariance c)
Choose each family's hyperparameters using August/September 2026 ONLY;
test on October/November 2026 only once. This 2026/27 period has
already been inspected and is NOT a fresh held-out external validation.

The fixed objective on DEV is the average of four binary Brier scores:
BTTS_YES, OVER_1.5, OVER_2.5, OVER_3.5. 1X2 multiclass Brier
is a guardrail; trials exceeding incumbent DEV by +0.003 are ineligible.
No re-fitting M4 hyperparameters and no claims about ROI.
"""
from __future__ import annotations
import argparse,csv,json,math,sys,random,hashlib
from collections import defaultdict,Counter
from datetime import date,timedelta
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments"/"263"))
from m4_integrated import fit_m4,predict_m4,use_lock

SCHEMA="MC_263_GOALMARKET_CHALLENGE_V1"
N=40
BINARY=("BTTS_YES","OVER_1.5","OVER_2.5","OVER_3.5")
SCALES=(0.85,0.925,1.0,1.075,1.15)
RHOS=(-0.15,-0.075,0.0,0.075,0.15)
COVS=(0.0,0.10,0.20,0.30)
MARKETS=BINARY+("MS_H","MS_D","MS_A")

def monday(s):
    d=date.fromisoformat(s)
    return (d-timedelta(days=d.weekday())).isoformat()

def pois(mu):
    p=np.empty(N+1,dtype=float)
    p[0]=math.exp(-mu)
    for i in range(1,N+1):p[i]=p[i-1]*mu/i
    return p

def matrix(lh,la,*,kind="independent",scale=1.0,rho=0.0,cov=0.0):
    lh*=scale;la*=scale
    if not 0.01<lh<8 or not 0.01<la<8:
        raise ValueError("out of domain lambda")
    if kind not in ("independent","scaled","dc","bivar"):
        raise ValueError("not a preregistered family")
    if kind=="bivar":
        if cov<0 or cov>=min(lh,la):
            raise ValueError("covariance outside valid bivariate Poisson support")
        a=pois(lh-cov);b=pois(la-cov);shared=pois(cov)
        p=np.zeros((N+1,N+1),dtype=float)
        for k in range(min(N+1,16)):
            # x=I+k, y=J+k, I~Pois(lh-c), J~Pois(la-c), k~Pois(c)
            p[k:,k:]+=shared[k]*np.outer(a[:N+1-k],b[:N+1-k])
    else:
        p=np.outer(pois(lh),pois(la))
        if kind=="dc":
            # Standard Dixon-Coles correction on (0,0),(0,1),(1,0),(1,1).
            factors=(1-lh*la*rho,1+lh*rho,1+la*rho,1-rho)
            if min(factors)<=0:
                raise ValueError("invalid negative Dixon-Coles tau")
            p[0,0]*=factors[0];p[0,1]*=factors[1]
            p[1,0]*=factors[2];p[1,1]*=factors[3]
    mass=float(p.sum())
    if not .999999999<=mass<=1.000000001:
        raise ValueError("uncontrolled goal-score probability mass")
    p/=mass
    return p

def probs(p):
    i=np.arange(p.shape[0])[:,None];j=np.arange(p.shape[1])[None,:]
    total=i+j
    return {"BTTS_YES":float(p[(i>0)&(j>0)].sum()),
            "OVER_1.5":float(p[total>=2].sum()),
            "OVER_2.5":float(p[total>=3].sum()),
            "OVER_3.5":float(p[total>=4].sum()),
            "MS_H":float(p[i>j].sum()),
            "MS_D":float(p[i==j].sum()),
            "MS_A":float(p[i<j].sum())}

def actual(h,a):
    return {"BTTS_YES":int(h>0 and a>0),
            "OVER_1.5":int(h+a>=2),"OVER_2.5":int(h+a>=3),
            "OVER_3.5":int(h+a>=4),
            "MS_H":int(h>a),"MS_D":int(h==a),"MS_A":int(h<a)}

def metrics(predictions,groundtruth):
    n=len(predictions)
    if n!=len(groundtruth) or not n:
        raise ValueError("missing matched sample")
    result={}
    for m in BINARY:
        pp=np.array([x[m] for x in predictions])
        y=np.array([x[m] for x in groundtruth])
        result[m]={"n":n,"brier":float(np.mean((pp-y)**2)),
            "logloss":float(np.mean(-y*np.log(np.clip(pp,1e-12,1))
                       -(1-y)*np.log(np.clip(1-pp,1e-12,1)))),
            "mean_predicted":float(pp.mean()),"observed":float(y.mean())}
    px=np.array([[x[m] for m in ("MS_H","MS_D","MS_A")] for x in predictions])
    yy=np.array([[x[m] for m in ("MS_H","MS_D","MS_A")] for x in groundtruth])
    result["MS"]={"n":n,"brier":float(np.mean(((px-yy)**2).sum(axis=1))),
       "logloss":float(np.mean(-(yy*np.log(np.clip(px,1e-12,1))).sum(axis=1))),
       "accuracy":float(np.mean(px.argmax(axis=1)==yy.argmax(axis=1)))}
    result["mean_goal_market_brier"]=float(np.mean([result[m]["brier"] for m in BINARY]))
    return result

def candidates():
    return {
        "independent":[{"kind":"independent","scale":1.0}],
        "scaled":[{"kind":"scaled","scale":scale} for scale in SCALES],
        "dc":[{"kind":"dc","scale":scale,"rho":rho}
            for scale in SCALES for rho in RHOS],
        "bivar":[{"kind":"bivar","scale":scale,"cov":c}
            for scale in SCALES for c in COVS],
    }

def predictions(rows,candidate):
    result=[]
    for r in rows:
        try: p=matrix(r["lambda_h"],r["lambda_a"],**candidate)
        except ValueError:
            return None
        result.append(probs(p))
    return result

def sample(history,lock):
    # History is valid as-of past, but never claim actual historical
    # predictions were previously SHA-sealed.
    rows=[]
    for r in history:
        h,a=int(r["home_goals"]),int(r["away_goals"])
        if r["date"]!="2026-11-09" and date.fromisoformat(r["date"])>=date(2026,11,9):
            raise ValueError("future observed score in historical dataset")
        rows.append({"league":r["league"],"match_date":r["date"],
                     "season":r["season"],"fixture_id":"|".join(
                        (r["league"],r["date"],r["home"],r["away"])),
                     "home_id":r["home"],"away_id":r["away"],
                     "home_goals":h,"away_goals":a,
                     "result":"H" if h>a else "A" if a>h else "D"})
    grouped=defaultdict(list)
    for r in history:
        if r["date"]>="2026-08-01":
            grouped[(r["league"],monday(r["date"]))].append(r)
    outputs=[];failures=[]
    for (league,week),batch in sorted(grouped.items()):
        fit=fit_m4(rows,league,week,lock)
        for r in batch:
            lam=predict_m4(fit,r["home"],r["away"]) if fit else None
            if lam is None:
                failures.append({"league":league,"week":week,"reason":"NO_M4_LAMBDA"})
                continue
            h,a=int(r["home_goals"]),int(r["away_goals"])
            outputs.append({"league":league,"date":r["date"],"week":week,
                "lambda_h":float(lam[0]),"lambda_a":float(lam[1]),
                "h":h,"a":a})
    return outputs,failures

def diagnostic(records):
    """Descriptive mean-goal and probability-bin audit; no model tuning."""
    truth=[actual(x["h"],x["a"]) for x in records]
    predictions0=predictions(records,{"kind":"independent","scale":1.0})
    if predictions0 is None:raise ValueError("missing diagnostic probabilities")
    result={"n":len(records),
       "mean_home_lambda":float(np.mean([r["lambda_h"] for r in records])),
       "mean_away_lambda":float(np.mean([r["lambda_a"] for r in records])),
       "mean_observed_home_goals":float(np.mean([r["h"] for r in records])),
       "mean_observed_away_goals":float(np.mean([r["a"] for r in records])),
       "market_bins":{}}
    for market in BINARY:
        bs=[]
        for i in range(5):
            matched=[(p[market],y[market]) for p,y in zip(predictions0,truth)
                if i*.2<=p[market]<(i+1)*.2 or i==4 and i*.2<=p[market]<=1.]
            if matched:
                bs.append({"bin":[round(.2*i,1),round(.2*(i+1),1)],
                    "n":len(matched),
                    "mean_model":float(np.mean([z[0] for z in matched])),
                    "observed":float(np.mean([z[1] for z in matched]))})
        result["market_bins"][market]=bs
    return result

def run(archive,lock_path,dest):
    archive=Path(archive)
    content=archive.read_bytes()
    hist=list(csv.DictReader(content.decode("utf8").splitlines()))
    if len(hist)!=4518 or len({(r["league"],r["date"],r["home"],r["away"]) for r in hist})!=len(hist):
        raise ValueError("wrong accepted canonical-history cohort")
    lock=json.loads(Path(lock_path).read_text(encoding="utf8"))
    settings=use_lock(lock)
    observations,failed=sample(hist,settings)
    dev=[r for r in observations if r["date"]<"2026-10-01"]
    test=[r for r in observations if r["date"]>="2026-10-01"]
    if min(len(dev),len(test))<100:
        raise ValueError("too few chronological observations")
    label_dev=[actual(x["h"],x["a"]) for x in dev]
    label_test=[actual(x["h"],x["a"]) for x in test]
    baseline=metrics(predictions(dev,{"kind":"independent","scale":1.0}),label_dev)
    selection={}
    for family,grid in candidates().items():
        eligible=[]
        for idx,c in enumerate(grid):
            devpred=predictions(dev,c)
            if devpred is None:continue
            met=metrics(devpred,label_dev)
            diff=met["MS"]["brier"]-baseline["MS"]["brier"]
            if diff>0.003:continue
            eligible.append((met["mean_goal_market_brier"],idx,c,met))
        if not eligible:
            selection[family]={"status":"NO_ELIGIBLE_CANDIDATE"}
            continue
        _,index,chosen,met=min(eligible,key=lambda x:(x[0],x[1]))
        selection[family]={"status":"SELECTED_IN_DEV","parameter":chosen,
                           "development":met,"dev_ms_brier_delta":met["MS"]["brier"]-baseline["MS"]["brier"]}
    evaluation={}
    for family,s in selection.items():
        if s["status"]!="SELECTED_IN_DEV":continue
        p=predictions(test,s["parameter"])
        if p is None:
            evaluation[family]={"status":"INVALID_EVAL_PARAMETERS"};continue
        evaluation[family]={"status":"SCORED","metrics":metrics(p,label_test)}
    report={"schema":SCHEMA,
       "status":"HISTORICAL_EXPLORATORY_RESULTS_ALREADY_INSPECTED",
       "source_history_sha":hashlib.sha256(content).hexdigest(),
       "m4_settings":lock["settings"],
       "dev_period":"2026-08-01 to 2026-09-30",
       "test_period":"2026-10-01 to 2026-11-03",
       "same_week_outcomes_excluded":True,
       "development_n":len(dev),"evaluation_n":len(test),
       "unpaired":len(failed),"failure_reasons":dict(Counter(x["reason"] for x in failed)),
       "selection":selection,"evaluation":evaluation,
       "m4_diagnostic":{"development":diagnostic(dev),"evaluation":diagnostic(test)},
       "proper_score_target":"mean Brier of BTTS and 1.5/2.5/3.5 overs, same fixtures",
       "dev_ms_guardrail_brier_worsening_max":0.003,
       "original_m4_engine_unchanged":True,
       "scores_independently_verified":False,
       "previously_viewed_eval_period":True,
       "production_promotion":False,"betting_authorized":False}
    dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"development_n":len(dev),"evaluation_n":len(test),
      "unpaired":len(failed),
      "evaluation":{family: {"goal_brier":value.get("metrics",{}).get("mean_goal_market_brier"),
                          "MS_brier":value.get("metrics",{}).get("MS",{}).get("brier"),
                          "BTTS":value.get("metrics",{}).get("BTTS_YES",{}).get("brier"),
                          "OVER_2.5":value.get("metrics",{}).get("OVER_2.5",{}).get("brier")}
                     for family,value in evaluation.items()},
      "selected":{k:v.get("parameter") for k,v in selection.items()},
      "goal_expectations":{period:{field:report["m4_diagnostic"][period][field] for field in ("mean_home_lambda","mean_away_lambda","mean_observed_home_goals","mean_observed_away_goals")} for period in ("development","evaluation")}},
      ensure_ascii=False,indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("archive","lock","out"):p.add_argument("--"+name,required=True)
    a=p.parse_args();run(a.archive,a.lock,a.out)
