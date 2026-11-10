"""Exploratory 2026/27 opponent-strength-segmented GOAL market challenge.

Same original frozen M4 fit & weekly past-only information.
Two PREDECLARED static alternatives:
- DC rho=-0.08 adjusts scorelines 0-0,0-1,1-0,1-1 only.
- BV common-shock max covariance .12, bounded by 25% of weaker lambda,
  preserves separate team goal means and changes BTTS/2.5-over too.

All results are from already VIEWED matches: no production promotion.
No tuning or data downloads, no 2.6.3 seals touched.
"""
from __future__ import annotations
import argparse,json,math,random,sys
from collections import Counter,defaultdict
from datetime import date,timedelta
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/"experiments"/"263"))
from m4_integrated import fit_m4,predict_m4,score_markets,use_lock
from data_opponent_goal_audit import read_rows,strength_band

EVENTS=("BTTS","OVER_1.5","OVER_2.5","OVER_3.5")
METHODS=("M4","DC_FIXED_RHO_NEG008","BIVARIATE_FIXED_SHARED012")

class ModelAuditBlocked(ValueError):pass

def monday(s):
    d=date.fromisoformat(s)
    return (d-timedelta(days=d.weekday())).isoformat()

def poisson(mu,n):
    if mu<0:raise ModelAuditBlocked("POISSON_NEGATIVE_RATE")
    probs=np.zeros(n)
    probs[0]=math.exp(-mu)
    for j in range(1,n):probs[j]=probs[j-1]*mu/j
    if 1-float(probs.sum())>1e-10:raise ModelAuditBlocked("TRUNCATED_POISSON_TAIL")
    return probs

def markets_from_matrix(mat):
    if not isinstance(mat,np.ndarray) or mat.ndim!=2 or mat.shape[0]!=mat.shape[1]:
        raise ModelAuditBlocked("MATRIX_SCHEMA")
    if not np.isfinite(mat).all() or (mat<0).any() or mat.sum()<=0:
        raise ModelAuditBlocked("UNUSABLE_JOINT_SCORES")
    mat=mat/float(mat.sum());n=mat.shape[0]
    h=np.arange(n)[:,None];a=np.arange(n)[None,:]
    ms={"H":float(mat[h>a].sum()),"D":float(mat[h==a].sum()),"A":float(mat[h<a].sum())}
    res={"1X2":ms,"BTTS_YES":float(mat[(h>0)&(a>0)].sum())}
    for line in (1.5,2.5,3.5):res[f"OVER_{line}"]=float(mat[h+a>line].sum())
    if abs(sum(ms.values())-1)>1e-9:raise ModelAuditBlocked("1X2_NOT_COHERENT")
    if not 0<=res["BTTS_YES"]<=res["OVER_1.5"]+1e-10:raise ModelAuditBlocked("IMPOSSIBLE_BTTS")
    if not res["OVER_1.5"]+1e-9>=res["OVER_2.5"]>=res["OVER_3.5"]-1e-9:
        raise ModelAuditBlocked("GOALS_NOT_MONOTONE")
    return res

def dc_fixed(lh,la,rho=-.08,n=32):
    ph,pa=poisson(lh,n),poisson(la,n)
    mat=np.outer(ph,pa)
    mat[0,0]*=(1-lh*la*rho)
    mat[0,1]*=(1+lh*rho)
    mat[1,0]*=(1+la*rho)
    mat[1,1]*=(1-rho)
    return markets_from_matrix(mat)

def bivar_fixed(lh,la,n=32):
    shared=min(.12,.25*min(lh,la))
    pu,pv,ps=poisson(lh-shared,n),poisson(la-shared,n),poisson(shared,n)
    mat=np.zeros((n,n))
    for k in range(n):
        if ps[k]<1e-16:break
        mat[k:,k:]+=ps[k]*np.outer(pu[:n-k],pv[:n-k])
    p=markets_from_matrix(mat)
    p["common_shock_rate"]=shared
    return p

def outcome(h,a):
    return "H" if h>a else "D" if h==a else "A"

def scalar_scores(p,y):
    if not math.isfinite(p) or not 0<=p<=1:raise ModelAuditBlocked("NON_FINITE_PROBABILITY")
    return ((p-y)**2,-y*math.log(max(1e-15,p))-(1-y)*math.log(max(1e-15,1-p)))

def score_markets_record(mark,h,a):
    y=outcome(h,a)
    ms=mark["1X2"]
    probs=[ms[k] for k in ("H","D","A")]
    if not all(math.isfinite(z) and 0<=z<=1 for z in probs) or abs(sum(probs)-1)>1e-7:
        raise ModelAuditBlocked("BAD_MS_MASS")
    out={"MS_brier":sum((ms[k]-int(y==k))**2 for k in ("H","D","A")),
         "MS_logloss":-math.log(max(ms[y],1e-15)),
         "MS_hit":int(max(("H","D","A"),key=lambda k:ms[k])==y)}
    for event in EVENTS:
        p=mark["BTTS_YES"] if event=="BTTS" else mark[event]
        actual=int(h>0 and a>0) if event=="BTTS" else int(h+a>float(event.split("_")[1]))
        b,log=scalar_scores(p,actual)
        out[event+"_brier"]=b;out[event+"_logloss"]=log
        out[event+"_p"]=p;out[event+"_y"]=actual
    return out

def score_summary(rows,method):
    if not rows:return {"n":0}
    fields=["MS_brier","MS_logloss","MS_hit"]
    for event in EVENTS:fields.extend((event+"_brier",event+"_logloss",event+"_p",event+"_y"))
    return {"n":len(rows),**{field:round(sum(r[method][field] for r in rows)/len(rows),6) for field in fields}}

def elo_by_week(rows):
    by_week=defaultdict(list)
    for r in rows:by_week[(r["league"],monday(r["match_date"]))].append(r)
    rating=defaultdict(lambda:1500.)
    prior=defaultdict(int)
    pre={}
    for (league,week),items in sorted(by_week.items(),key=lambda z:(z[0][1],z[0][0])):
        week_update=defaultdict(float)
        for r in items:
            kh,ka=(league,r["home_id"]),(league,r["away_id"])
            gap=rating[kh]-rating[ka]
            pre[r["fixture_id"]]={"gap":gap,"strength_band":strength_band(gap),
              "both_known":min(prior[kh],prior[ka])>=8}
            prob=1/(1+10**(-(gap+65)/400))
            delta=18*((1 if r["result"]=="H" else .5 if r["result"]=="D" else 0)-prob)
            week_update[kh]+=delta;week_update[ka]-=delta
        for k,delta in week_update.items():rating[k]+=delta
        for r in items:
            prior[(league,r["home_id"])]+=1
            prior[(league,r["away_id"])]+=1
    return pre

def grouped_metrics(items,field,model):
    groups=defaultdict(list)
    for r in items:groups[r[field]].append(r)
    return {k:{method:score_summary(v,method) for method in METHODS}
            for k,v in sorted(groups.items())}

def clustered_difference(rows,method,field,rep=500):
    """Block resample league-week, not independent matches. Descriptive only."""
    if len(rows)<50:return None
    bags=defaultdict(list)
    for r in rows:bags[(r["league"],r["week"])].append(
        r[method][field]-r["M4"][field])
    if len(bags)<8:return None
    keys=sorted(bags);n=len(keys);rng=random.Random(263)
    values=[]
    for _ in range(rep):
        samples=[bags[keys[rng.randrange(n)]] for _ in range(n)]
        vals=[v for batch in samples for v in batch]
        values.append(sum(vals)/len(vals))
    values.sort()
    return {"mean_candidate_minus_M4":round(sum(r[method][field]-r["M4"][field] for r in rows)/len(rows),6),
            "clustered_95pct_range":[round(values[int(rep*.025)],6),round(values[int(rep*.975)-1],6)],
            "n_league_week_clusters":n,
            "interpretation":"Exploratory, same outcomes previously inspected, not independent evidence of superiority"}

def audit(source,lock_path):
    rows,_,sha=read_rows(source)
    rows=sorted(rows,key=lambda r:(r["match_date"],r["league"],r["fixture_id"]))
    hist=[{"league":r["league"],"season":r["season"],"match_date":r["match_date"],
            "fixture_id":r["fixture_id"],"home_id":r["home_id"],"away_id":r["away_id"],
            "home_goals":int(r["home_goals"]),"away_goals":int(r["away_goals"]),"result":r["result"]}
            for r in rows]
    if not all(r["match_date"]<"2026-11-11" for r in rows):raise ModelAuditBlocked("FUTURE_TEST_LABEL")
    settings=use_lock(json.loads(Path(lock_path).read_text(encoding="utf8")))
    pre=elo_by_week(rows)
    groups=defaultdict(list)
    for r in rows:
        if r["season"]=="2026-2027":
            groups[(r["league"],monday(r["match_date"]))].append(r)
    scored=[];blocked=Counter();total=sum(len(x) for x in groups.values())
    for (league,week),fixtures in sorted(groups.items()):
        model=fit_m4(hist,league,week,settings)
        for r in fixtures:
            if model is None:
                blocked["M4_NO_FIT"]+=1;continue
            lam=predict_m4(model,r["home_id"],r["away_id"])
            if lam is None:
                blocked["M4_NO_LAMBDAS"]+=1;continue
            lh,la=lam
            markets=score_markets(lh,la)["markets"]
            candidate_dc=dc_fixed(lh,la)
            candidate_bv=bivar_fixed(lh,la)
            # Under exactly independent Poisson, expected score-market probs equal M4.
            expected=bivar_fixed(lh,la)["common_shock_rate"]
            if expected<=0 or not .05<=lh<=5 or not .05<=la<=5:
                raise ModelAuditBlocked("INVALID_FIXED_SHARED_LAMBDA")
            h,a=int(r["home_goals"]),int(r["away_goals"])
            rec={"league":league,"week":week,"date":r["match_date"],
                 "strength_band":pre[r["fixture_id"]]["strength_band"],
                 "both_teams_8plus_history":pre[r["fixture_id"]]["both_known"],
                 "M4":score_markets_record(markets,h,a),
                 "DC_FIXED_RHO_NEG008":score_markets_record(candidate_dc,h,a),
                 "BIVARIATE_FIXED_SHARED012":score_markets_record(candidate_bv,h,a)}
            # DC only alters scores with total <=2, so 2.5/3.5 should match to floating tolerance
            for event in ("OVER_2.5","OVER_3.5"):
                if abs(rec["M4"][event+"_p"]-rec["DC_FIXED_RHO_NEG008"][event+"_p"])>1e-9:
                    raise ModelAuditBlocked("DC_HIGH_GOAL_MARKET_UNEXPECTED_CHANGE")
            scored.append(rec)
    if total<600 or len(scored)<500:raise ModelAuditBlocked("INSUFFICIENT_HISTORICAL_COVERAGE")
    metrics={model:score_summary(scored,model) for model in METHODS}
    paired={candidate:{field:clustered_difference(scored,candidate,field)
      for field in ("MS_brier","BTTS_brier","OVER_1.5_brier","OVER_2.5_brier","OVER_3.5_brier")}
       for candidate in METHODS[1:]}
    source_stats={}
    for league in sorted({r["league"] for r in scored}):
        v=[r for r in scored if r["league"]==league]
        source_stats[league]={method:score_summary(v,method) for method in METHODS}
    return {"schema":"263_OPPONENT_GOALS_FROZEN_EXPLORATORY_COMP_V1",
      "status":"EXPLORATORY_ONLY_NO_MODEL_PROMOTION",
      "source_sha256":sha,"M4_original_lock_unchanged":True,
      "both_models_use_same_original_M4_lambdas":True,
      "control_M4_unchanged":True,
      "source_season_2026_27_total":total,"same_week_past_only_scored":len(scored),
      "unscored_reasons":dict(blocked),
      "predeclared_challengers":{
        "DC_FIXED_RHO_NEG008":"Dixon-Coles low-score rho=-0.08; adjusts MS, KG and 1.5 Over; 2.5/3.5 unchanged",
        "BIVARIATE_FIXED_SHARED012":"Shared Poisson shock min(0.12,0.25*min(lh,la)); team scoring means stay equal; market probabilities remain coherent"},
      "overall":metrics,"candidate_minus_M4_date_clusters":paired,
      "by_league":source_stats,
      "by_opponent_strength_band":grouped_metrics(scored,"strength_band","M4"),
      "by_team_prior_data_quality":grouped_metrics(scored,"both_teams_8plus_history","M4"),
      "not_a_tactical_style_measure":True,
      "provider_results_not_independently_verified":True,
      "original_forecasts_or_seals_recomputed":False,
      "do_not_promote_from_already_seen_2026_27":True,
      "limitations":["Historical data through latest accepted snapshot, not real-time updated",
          "2026/27 outcomes already studied in earlier analyses",
          "Only date-level weekly cutoff; historical exact kickoff timestamps unavailable",
          "Any positive score differences are hypothesis, NOT unseen statistical validation",
          "Elo opponent-strength bands are past-only but not actual pressing/formation labels",
          "Shot events do not encode tactics; separate xG/PPDA provider is not included",
          "True pre-match player absences and latest live fixtures cannot be reconstructed from score table",
          "No betting odds/EV or claims of live profitability"]}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",default="data/quad_accepted_263/extended_history.csv")
    parser.add_argument("--lock",default="experiments/263/m4_lock.json")
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    report=audit(args.source,args.lock)
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if json.loads(path.read_text(encoding="utf8"))!=report:
            raise ModelAuditBlocked("EXISTING_GOAL_RESEARCH_DIFFERENT")
    else:path.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({"scored":report["same_week_past_only_scored"],
      "blocked":report["unscored_reasons"],
      "overall":report["overall"],
      "paired":report["candidate_minus_M4_date_clusters"]},ensure_ascii=False))

if __name__=="__main__":main()
