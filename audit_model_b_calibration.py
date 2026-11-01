"""Read-only chronological Model B calibration audit."""
import csv,json,math
from collections import defaultdict
from pathlib import Path
from experimental_poisson_baseline import estimate

def summarize(rows):
 n=len(rows)
 return {"n":n,"brier":sum(sum((p-int(i==y))**2 for i,p in enumerate(ps)) for ps,y in rows)/n if n else None,"logloss":sum(-math.log(max(1e-12,ps[y])) for ps,y in rows)/n if n else None}

def bins(rows):
 out=[]
 for i in range(10):
  lo=i/10;hi=(i+1)/10
  subset=[(p,y) for p,y in rows if lo<=p<hi or (i==9 and p==1)]
  n=len(subset)
  out.append({"range":[lo,hi],"n":n,"predicted":sum(p for p,y in subset)/n if n else None,"observed":sum(y for p,y in subset)/n if n else None})
 return out

def main():
 with Path("data/historical_results.csv").open(encoding="utf-8-sig",newline="") as f:hist=list(csv.DictReader(f))
 hist.sort(key=lambda r:(r["match_date"],r["fixture_id"]))
 if len({r["fixture_id"] for r in hist})!=len(hist):raise ValueError("duplicate fixture IDs")
 records=[];by_league={};by_season={}
 for r in hist:
  p=estimate(hist,r["league"],r["home_id"],r["away_id"],r["match_date"])
  if p is None:continue
  ps=[p["p_home"],p["p_draw"],p["p_away"]]
  total=sum(ps)
  if total<=0 or not math.isfinite(total):raise ValueError("invalid probabilities")
  ps=[v/total for v in ps]
  y={"H":0,"D":1,"A":2}[r["result"]]
  records.append((ps,y,r["league"],r["season"]))
 overall=summarize([(ps,y) for ps,y,league,season in records])
 by_league={k:summarize([(ps,y) for ps,y,l,s in records if l==k]) for k in sorted({r[2] for r in records})}
 by_season={k:summarize([(ps,y) for ps,y,l,s in records if s==k]) for k in sorted({r[3] for r in records})}
 reliability={label:bins([(ps[i],int(y==i)) for ps,y,l,s in records]) for i,label in enumerate(("H","D","A"))}
 top=bins([(max(ps),int(ps.index(max(ps))==y)) for ps,y,l,s in records])
 report={"version":"model_b_calibration_v1_read_only","historical":len(hist),"scored":len(records),"overall":overall,"by_league":by_league,"by_season":by_season,"reliability":reliability,"top_choice":top,"rule":"strict earlier dates; no model changes; sparse bins descriptive only"}
 Path("data/model_b_calibration_audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,ensure_ascii=False))
 if not records:raise SystemExit("no scored rows")
if __name__=="__main__":main()
