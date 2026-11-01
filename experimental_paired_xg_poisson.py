"""Paired, leakage-safe xG vs goals-only Poisson experiment.

Inputs are independently audited historical_results.csv and historical_verified_xg.csv.
No estimated xG is substituted for missing observations. Comparison uses identical
eligible fixtures for both models and only strictly earlier dates.
"""
import csv,json,math,random
from collections import defaultdict
from pathlib import Path
from experimental_poisson_baseline import estimate,poisson

ROOT=Path("data")
def read(path):
 with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def xg_estimate(rows, league, home_id, away_id, target_date, window=20, shrink=5):
 past=[r for r in rows if r["league"]==league and r["match_date"]<target_date]
 past.sort(key=lambda r:(r["match_date"],r["fixture_id"]))
 home=[r for r in past if r["home_id"]==home_id][-window:]
 away=[r for r in past if r["away_id"]==away_id][-window:]
 if len(past)<30 or len(home)<5 or len(away)<5:return None
 mh=sum(float(r["home_xg"]) for r in past)/len(past)
 ma=sum(float(r["away_xg"]) for r in past)/len(past)
 if min(mh,ma)<=0:return None
 ha=(sum(float(r["home_xg"]) for r in home)+shrink*mh)/(len(home)+shrink)/mh
 hd=(sum(float(r["away_xg"]) for r in home)+shrink*ma)/(len(home)+shrink)/ma
 aa=(sum(float(r["away_xg"]) for r in away)+shrink*ma)/(len(away)+shrink)/ma
 ad=(sum(float(r["home_xg"]) for r in away)+shrink*mh)/(len(away)+shrink)/mh
 lh=max(.05,min(5.,mh*ha*ad))
 la=max(.05,min(5.,ma*aa*hd))
 ph=[poisson(lh,i) for i in range(11)]
 pa=[poisson(la,j) for j in range(11)]
 probs=[0.,0.,0.]
 for i in range(11):
  for j in range(11):
   probs[0 if i>j else 1 if i==j else 2]+=ph[i]*pa[j]
 mass=sum(probs)
 return [v/mass for v in probs]

def main():
 historical=read(ROOT/"historical_results.csv")
 verified=read(ROOT/"historical_verified_xg.csv")
 by_id={r["fixture_id"]:r for r in historical}
 if len(by_id)!=len(historical):raise ValueError("Duplicate historical fixture ID")
 if len({r["fixture_id"] for r in verified})!=len(verified):raise ValueError("Duplicate verified xG fixture ID")
 for r in verified:
  h=by_id.get(r["fixture_id"])
  if h is None:raise ValueError("Unlinked verified xG")
  for k in ("league","season","match_date","home_id","away_id","home_goals","away_goals"):
   if str(h[k])!=str(r[k]):raise ValueError("xG identity mismatch: "+k)
  for k in ("home_xg","away_xg"):
   v=float(r[k])
   if not math.isfinite(v) or v<0:raise ValueError("Invalid xG")
 verified.sort(key=lambda r:(r["match_date"],r["fixture_id"]))
 score={"goals":{"brier":0.,"logloss":0.},"xg":{"brier":0.,"logloss":0.}}
 eligible=0;skipped=0
 league_counts=defaultdict(int)
 paired=[]
 for r in historical:
  goals=estimate(historical,r["league"],r["home_id"],r["away_id"],r["match_date"])
  xg=xg_estimate(verified,r["league"],r["home_id"],r["away_id"],r["match_date"])
  if goals is None or xg is None:
   skipped+=1
   continue
  g=[goals["p_home"],goals["p_draw"],goals["p_away"]]
  g=[v/sum(g) for v in g]
  idx={"H":0,"D":1,"A":2}[r["result"]]
  row_losses={}
  for name,prob in (("goals",g),("xg",xg)):
   score[name]["brier"]+=sum((p-int(i==idx))**2 for i,p in enumerate(prob))
   score[name]["logloss"]-=math.log(max(1e-12,prob[idx]))
   row_losses[name]={"brier":sum((p-int(i==idx))**2 for i,p in enumerate(prob)),"logloss":-math.log(max(1e-12,prob[idx]))}
  paired.append({"league":r["league"],"date":r["match_date"],"season":r["season"],"delta_brier":row_losses["goals"]["brier"]-row_losses["xg"]["brier"],"delta_logloss":row_losses["goals"]["logloss"]-row_losses["xg"]["logloss"]})
  eligible+=1
  league_counts[r["league"]]+=1
 result={"version":"paired_xg_vs_goals_poisson_v0_experimental","historical_matches":len(historical),"verified_xg_rows":len(verified),"paired_scored":eligible,"not_paired":skipped,"paired_by_league":dict(sorted(league_counts.items())),"goals_model":{k:v/eligible if eligible else None for k,v in score["goals"].items()},"xg_model":{k:v/eligible if eligible else None for k,v in score["xg"].items()},"xg_improvement_positive_is_better":{k:(score["goals"][k]-score["xg"][k])/eligible if eligible else None for k in ("brier","logloss")},"leakage":"strict match_date < prediction date; same-day excluded","limitations":["xG coverage only five leagues","Different historical sample sizes across models but paired evaluation on same matches","No Elo, odds, lineups or betting EV","Experimental, not calibrated"]}
 # Diagnostic slices: positive delta means xG is better.
 def summary(rows):
  return {"n":len(rows),"mean_delta_brier":sum(x["delta_brier"] for x in rows)/len(rows),"mean_delta_logloss":sum(x["delta_logloss"] for x in rows)/len(rows)} if rows else {"n":0}
 result["by_league"]={key:summary([x for x in paired if x["league"]==key]) for key in sorted({x["league"] for x in paired})}
 result["by_season"]={key:summary([x for x in paired if x["season"]==key]) for key in sorted({x["season"] for x in paired})}
 # Date-block bootstrap preserves within-day dependence, with fixed seed.
 blocks=defaultdict(list)
 for x in paired:blocks[x["date"]].append(x)
 dates=sorted(blocks)
 rng=random.Random(20261101)
 boot={"brier":[],"logloss":[]}
 if dates:
  for _ in range(1000):
   selected=[blocks[dates[rng.randrange(len(dates))]] for _ in dates]
   n=sum(len(group) for group in selected)
   for metric in boot:
    boot[metric].append(sum(x["delta_"+metric] for group in selected for x in group)/n)
 result["date_block_bootstrap"]={"replicates":1000,"seed":20261101,"interval_type":"percentile_95","by_metric":{}}
 for metric,values in boot.items():
  values.sort()
  result["date_block_bootstrap"]["by_metric"][metric]={"low":values[24],"high":values[974],"positive_fraction":sum(x>0 for x in values)/len(values)} if values else None
 result["decision_rule"]="Do not promote xG based only on small positive overall deltas; inspect league/season stability and uncertainty. Date bootstrap is descriptive, not prospective validation."
 (ROOT/"paired_xg_poisson_report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(result,ensure_ascii=False))
 if not eligible:raise SystemExit("No paired matches; no conclusion")
if __name__=="__main__":main()
