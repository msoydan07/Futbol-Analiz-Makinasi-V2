"""Leakage-safe Elo-only auxiliary benchmark. Model B remains untouched."""
import csv,json,math
from collections import defaultdict
from pathlib import Path
from experimental_poisson_baseline import estimate

def probabilities(home,away,home_adv=55,draw=0.26):
 q=1/(1+10**(-((home+home_adv)-away)/400))
 return [(1-draw)*q,draw,(1-draw)*(1-q)]

def score(records,key):
 n=len(records)
 if not n:return {"n":0}
 return {"n":n,"brier":sum(sum((p-int(i==y))**2 for i,p in enumerate(item[key])) for item,y in records)/n,"logloss":sum(-math.log(max(1e-12,item[key][y])) for item,y in records)/n}

def main():
 with Path("data/historical_results.csv").open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
 rows.sort(key=lambda r:(r["match_date"],r["fixture_id"]))
 if len({r["fixture_id"] for r in rows})!=len(rows):raise ValueError("duplicate fixtures")
 ratings=defaultdict(lambda:1500.0)
 paired=[];i=0
 while i<len(rows):
  day=rows[i]["match_date"];j=i
  while j<len(rows) and rows[j]["match_date"]==day:j+=1
  updates=defaultdict(float)
  for r in rows[i:j]:
   league=r["league"];home=(league,r["home_id"]);away=(league,r["away_id"])
   eh=1/(1+10**(-((ratings[home]+55)-ratings[away])/400))
   actual={"H":1.0,"D":0.5,"A":0.0}[r["result"]]
   delta=20*(actual-eh)
   updates[home]+=delta;updates[away]-=delta
   base=estimate(rows,league,r["home_id"],r["away_id"],day)
   if base is None:continue
   bp=[base["p_home"],base["p_draw"],base["p_away"]]
   z=sum(bp);bp=[p/z for p in bp]
   ep=probabilities(ratings[home],ratings[away])
   paired.append(({"model_b":bp,"elo_only":ep,"league":league,"season":r["season"]},("H","D","A").index(r["result"])))
  for team,change in updates.items():ratings[team]+=change
  i=j
 def metrics(items):
  return {"n":len(items),"model_b":score(items,"model_b"),"elo_only":score(items,"elo_only"),"elo_minus_model_b_logloss":score(items,"elo_only").get("logloss",0)-score(items,"model_b").get("logloss",0)}
 report={"version":"elo_only_auxiliary_v1","all":metrics(paired),"by_season":{s:metrics([(x,y) for x,y in paired if x["season"]==s]) for s in sorted({x["season"] for x,y in paired})},"by_league":{s:metrics([(x,y) for x,y in paired if x["league"]==s]) for s in sorted({x["league"] for x,y in paired})},"settings":{"initial_rating":1500,"k":20,"home_advantage_rating_points":55,"draw_probability":0.26},"leakage":"all same-date matches evaluated before same-date Elo updates","limitations":["Elo-only fixed draw assumption; not a calibrated hybrid","No tuning of Elo parameters","No model B modification","Not evidence of incremental Elo value"]}
 Path("data/elo_auxiliary_audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"version":report["version"],"all":report["all"],"by_season":report["by_season"]},ensure_ascii=False))
if __name__=="__main__":main()
