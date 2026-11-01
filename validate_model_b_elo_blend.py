"""Forward-season evaluation of an Elo and Model B blend, without modifying production."""
import csv,json,math
from collections import defaultdict
from pathlib import Path
from experimental_poisson_baseline import estimate
from audit_elo_auxiliary import probabilities

def scores(rows,w):
 n=len(rows)
 if not n:return {"n":0}
 b=l=0
 for base,elo,y in rows:
  p=[(1-w)*a+w*e for a,e in zip(base,elo)]
  b+=sum((v-(i==y))**2 for i,v in enumerate(p))
  l-=math.log(max(p[y],1e-12))
 return {"n":n,"brier":b/n,"logloss":l/n}

def main():
 with open("data/historical_results.csv",encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
 rows.sort(key=lambda r:(r["match_date"],r["fixture_id"]))
 ratings=defaultdict(lambda:1500.)
 seasons=defaultdict(list)
 for day in sorted({r["match_date"] for r in rows}):
  changes=defaultdict(float)
  for r in (r for r in rows if r["match_date"]==day):
   h=(r["league"],r["home_id"]);a=(r["league"],r["away_id"])
   q=1/(1+10**(-((ratings[h]+55-ratings[a])/400)))
   delta=20*({"H":1,"D":.5,"A":0}[r["result"]]-q)
   changes[h]+=delta;changes[a]-=delta
   pred=estimate(rows,r["league"],r["home_id"],r["away_id"],day)
   if pred:
    base=[pred["p_home"],pred["p_draw"],pred["p_away"]]
    total=sum(base)
    seasons[r["season"]].append(([v/total for v in base],probabilities(ratings[h],ratings[a]),("H","D","A").index(r["result"])))
  for team,change in changes.items():ratings[team]+=change
 train=seasons["2025-2026"];test=seasons["2026-2027"]
 if not train or not test:raise ValueError("Missing seasons")
 candidates=[0,.05,.1,.15,.2,.25,.3,.4,.5]
 chosen=min(candidates,key=lambda w:(scores(train,w)["logloss"],w))
 original=scores(test,0);adjusted=scores(test,chosen)
 report={"version":"model_b_elo_forward_blend_v1","train_n":len(train),"test_n":len(test),"candidate_weights":candidates,"selected_weight":chosen,"train_scores":{str(w):scores(train,w) for w in candidates},"test_model_b":original,"test_blend":adjusted,"test_improvement":{k:original[k]-adjusted[k] for k in ("brier","logloss")},"rule":"train weight on 2025-2026 only; test 2026-2027; no same-day leakage; production unchanged"}
 Path("data/model_b_elo_forward_blend.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps(report))
if __name__=="__main__":main()
