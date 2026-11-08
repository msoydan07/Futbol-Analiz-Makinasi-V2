"""Independent XGBoost 1X2 challenger: date-causal results-only features.
No outcome from date D enters any date-D feature. This run is EXPLORATORY,
because the same 2025+ holdout was already viewed in other model reports.
"""
import argparse,csv,json
from collections import defaultdict,deque
from datetime import date
from pathlib import Path
import numpy as np
from xgboost import XGBClassifier

TRAIN_END="2024-07-01"; DEV_END="2025-07-01"
PARAMS=[
 dict(max_depth=2,n_estimators=160,learning_rate=.035,min_child_weight=15),
 dict(max_depth=3,n_estimators=210,learning_rate=.025,min_child_weight=20),
 dict(max_depth=4,n_estimators=140,learning_rate=.025,min_child_weight=30)]
LABEL={"H":0,"D":1,"A":2}

class Team:
 def __init__(self):
  self.form=deque(maxlen=10);self.venue={"H":deque(maxlen=5),"A":deque(maxlen=5)}
  self.last=None;self.games=0;self.points=0
 def stats(self,n):
  v=list(self.form)[-n:]
  return [sum(x[j] for x in v)/len(v) if v else base
          for j,base in enumerate((1.3,1.35,1.35))]
 def rest(self,now):
  return float(max(0,min(30,(now-self.last).days))) if self.last else 7.0
 def venue_pts(self,v):
  return sum(self.venue[v])/len(self.venue[v]) if self.venue[v] else 1.3
 def add(self,now,venue,gf,ga):
  pts=3 if gf>ga else 1 if gf==ga else 0
  self.form.append((pts,gf,ga));self.venue[venue].append(pts)
  self.last=now;self.games+=1;self.points+=pts

def fixture_key(r):return (r["league"],r["date"],r["home"],r["away"])

def make_features(rows):
 byday=defaultdict(list)
 for r in rows:byday[r["date"]].append(r)
 teams=defaultdict(Team);leagues=defaultdict(lambda:[0,0,0,0])
 lid={x:i for i,x in enumerate(sorted({r["league"] for r in rows}))}
 out=[]
 for day in sorted(byday):
  now=date.fromisoformat(day);pending=[]
  for r in sorted(byday[day],key=fixture_key):
   key=r["league"];h=teams[key,r["home"]];a=teams[key,r["away"]]
   h5,h10,a5,a10=h.stats(5),h.stats(10),a.stats(5),a.stats(10)
   hr,ar=h.rest(now),a.rest(now);n,hg,ag,draw=leagues[key]
   features=[lid[key],h.games,a.games,*h5,*a5,*h10,*a10,
     h.venue_pts("H"),a.venue_pts("A"),hr,ar,hr-ar,
     (h.points+5.2)/(h.games+4),(a.points+5.2)/(a.games+4),
     (hg+1.45*35)/(n+35),(ag+1.15*35)/(n+35),
     (draw+.265*35)/(n+35)]
   gh,ga=int(r["home_goals"]),int(r["away_goals"])
   label="H" if gh>ga else "D" if gh==ga else "A"
   out.append((r,features,label,n))
   pending.append((r,gh,ga))
  # Delayed batch update prevents today's score leaking to another today's fixture.
  for r,gh,ga in pending:
   k=r["league"];teams[k,r["home"]].add(now,"H",gh,ga)
   teams[k,r["away"]].add(now,"A",ga,gh)
   counts=leagues[k];counts[0]+=1;counts[1]+=gh;counts[2]+=ga;counts[3]+=int(gh==ga)
 return out

def metrics(rows,prob):
 y=np.array([LABEL[r[2]] for r in rows])
 p=np.clip(np.asarray(prob,dtype=float),1e-12,1)
 p=p/p.sum(axis=1,keepdims=True)
 return {"n":len(rows),"logloss":float(-np.log(p[np.arange(len(y)),y]).mean()),
         "brier":float(((p-np.eye(3)[y])**2).sum(axis=1).mean())}

def fit(rows,params):
 model=XGBClassifier(objective="multi:softprob",num_class=3,eval_metric="mlogloss",
      tree_method="hist",n_jobs=2,random_state=263,reg_lambda=10.0,
      reg_alpha=1.0,subsample=.85,colsample_bytree=.9,**params)
 x=np.asarray([r[1] for r in rows],dtype=np.float32)
 y=np.asarray([LABEL[r[2]] for r in rows])
 model.fit(x,y)
 return model

def probabilities(model,rows):
 return model.predict_proba(np.asarray([r[1] for r in rows],dtype=np.float32))

def pair(rows,prob,path):
 with open(path,encoding="utf8",newline="") as f:base=list(csv.DictReader(f))
 b={fixture_key(x):x for x in base}
 if len(b)!=len(base):raise ValueError("duplicate baseline")
 deltas=[]
 for row,p in zip(rows,prob):
  k=fixture_key(row[0]);actual=row[2];reference=b.get(k)
  if not reference or reference["valid_warmup"].lower()!="true" or reference["result"]!=actual:
   raise ValueError("unpaired record: "+str(k))
  loss=-np.log(max(float(p[LABEL[actual]]),1e-12))
  deltas.append(loss-float(reference["logloss"]))
 return {"n":len(deltas),"mean_logloss_difference":float(np.mean(deltas))}

def run(src,elo,poisson,outpath):
 with open(src,encoding="utf8",newline="") as f:source=list(csv.DictReader(f))
 if any(x["date"]>"2026-11-09" for x in source):raise ValueError("future scores")
 rows=[r for r in make_features(source) if r[3]>=40]
 train=[r for r in rows if r[0]["date"]<TRAIN_END]
 dev=[r for r in rows if TRAIN_END<=r[0]["date"]<DEV_END]
 hold=[r for r in rows if r[0]["date"]>=DEV_END]
 if min(len(train),len(dev),len(hold))<100:raise ValueError("insufficient historical data")
 trials=[metrics(dev,probabilities(fit(train,par),dev)) for par in PARAMS]
 choice=min(range(len(PARAMS)),key=lambda i:(trials[i]["logloss"],i))
 # Fit on training+dev ONLY; no 2025-26 labels used for parameter fitting.
 model=fit(train+dev,PARAMS[choice]);p=probabilities(model,hold)
 out=Path(outpath);out.parent.mkdir(parents=True,exist_ok=True)
 with out.open("w",encoding="utf8",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=("league","date","home","away","actual","p_home","p_draw","p_away"))
  writer.writeheader()
  for row,q in zip(hold,p):
   r=row[0];writer.writerow(dict(league=r["league"],date=r["date"],home=r["home"],
     away=r["away"],actual=row[2],p_home=q[0],p_draw=q[1],p_away=q[2]))
 report={"schema":"MC_XGBOOST_EXPLORATORY_V1",
    "train_n":len(train),"dev_n":len(dev),"holdout_n":len(hold),
    "parameters_selected_on_dev":PARAMS[choice],"dev_trials":trials,
    "holdout":metrics(hold,p),
    "paired_logloss":{"elo":pair(hold,p,elo),"poisson":pair(hold,p,poisson)},
    "warning":"Exploratory: other models already inspected this holdout; not independent promotion evidence",
    "no_market_odds":True,"incumbent_comparison_done":False,"betting_authorized":False}
 out.with_suffix(".summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
 return report

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 for field in ("input","elo","poisson","out"):parser.add_argument("--"+field,required=True)
 args=parser.parse_args()
 print(json.dumps(run(args.input,args.elo,args.poisson,args.out),indent=2))
