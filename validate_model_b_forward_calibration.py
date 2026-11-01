"""Out-of-season temperature calibration test. No production model modification."""
import csv,json,math
from pathlib import Path
from experimental_poisson_baseline import estimate

def temper(ps,t):
 values=[max(1e-12,p)**(1/t) for p in ps]
 z=sum(values)
 return [v/z for v in values]

def score(records,t):
 n=len(records)
 if not n:return {"n":0,"brier":None,"logloss":None}
 brier=sum(sum((p-int(i==y))**2 for i,p in enumerate(temper(ps,t))) for ps,y in records)/n
 loss=sum(-math.log(max(1e-12,temper(ps,t)[y])) for ps,y in records)/n
 return {"n":n,"brier":brier,"logloss":loss}

def main():
 with Path("data/historical_results.csv").open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
 rows.sort(key=lambda r:(r["match_date"],r["fixture_id"]))
 if len({r["fixture_id"] for r in rows})!=len(rows):raise ValueError("Duplicate fixture IDs")
 train=[];test=[];leagues={}
 for r in rows:
  p=estimate(rows,r["league"],r["home_id"],r["away_id"],r["match_date"])
  if p is None:continue
  ps=[p["p_home"],p["p_draw"],p["p_away"]]
  z=sum(ps)
  if z<=0 or not math.isfinite(z):raise ValueError("Invalid probabilities")
  ps=[v/z for v in ps]
  y={"H":0,"D":1,"A":2}[r["result"]]
  item=(ps,y)
  if r["season"]=="2025-2026":train.append(item)
  elif r["season"]=="2026-2027":
   test.append(item)
   leagues.setdefault(r["league"],[]).append(item)
  else:raise ValueError("Unexpected season "+r["season"])
 if not train or not test:raise ValueError("Both seasons must have eligible predictions")
 # Single global parameter, fitted exclusively on earlier season.
 candidates=[round(0.7+i*0.025,3) for i in range(33)]
 selected=min(candidates,key=lambda t:(score(train,t)["logloss"],abs(t-1)))
 original=score(test,1.0)
 adjusted=score(test,selected)
 report={"version":"out_of_season_temperature_validation_v1","train_season":"2025-2026","test_season":"2026-2027","train_count":len(train),"test_count":len(test),"candidate_temperatures":candidates,"selected_temperature":selected,"train_original":score(train,1.0),"train_adjusted":score(train,selected),"test_original":original,"test_adjusted":adjusted,"test_improvement_positive_is_better":{metric:original[metric]-adjusted[metric] for metric in ("brier","logloss")},"test_by_league":{league:{"original":score(items,1.0),"adjusted":score(items,selected)} for league,items in sorted(leagues.items())},"rule":"Temperature fitted only on 2025-2026 predictions; tested on 2026-2027. Each prediction uses strictly earlier match dates.","limitations":["Single chronological season split; no rolling cross-validation","No production model modifications","No xG, Elo, odds or EV","Sample uncertainty not yet quantified"]}
 Path("data/model_b_forward_calibration.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":main()
