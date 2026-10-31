"""Experimental leakage-safe independent Poisson baseline. Not a betting recommendation."""
import csv,json,math,sys
from collections import defaultdict
from datetime import date
from pathlib import Path

def poisson(lam, k):
 return math.exp(-lam)*lam**k/math.factorial(k)

def estimate(rows, league, home_id, away_id, target_date, window=20, shrink=5):
 past=[r for r in rows if r["league"]==league and r["match_date"]<target_date]
 past.sort(key=lambda r:(r["match_date"],r["fixture_id"]))
 home=[r for r in past if r["home_id"]==home_id][-window:]
 away=[r for r in past if r["away_id"]==away_id][-window:]
 if len(past)<30 or len(home)<5 or len(away)<5:return None
 mean_h=sum(int(r["home_goals"]) for r in past)/len(past)
 mean_a=sum(int(r["away_goals"]) for r in past)/len(past)
 if min(mean_h,mean_a)<=0:return None
 h_attack=(sum(int(r["home_goals"]) for r in home)+shrink*mean_h)/(len(home)+shrink)/mean_h
 h_def=(sum(int(r["away_goals"]) for r in home)+shrink*mean_a)/(len(home)+shrink)/mean_a
 a_attack=(sum(int(r["away_goals"]) for r in away)+shrink*mean_a)/(len(away)+shrink)/mean_a
 a_def=(sum(int(r["home_goals"]) for r in away)+shrink*mean_h)/(len(away)+shrink)/mean_h
 lh=max(.05,min(5.,mean_h*h_attack*a_def))
 la=max(.05,min(5.,mean_a*a_attack*h_def))
 # Explicitly include 0..10 goals, with residual mass outside matrix reported.
 n=11
 ph=[poisson(lh,i) for i in range(n)]
 pa=[poisson(la,i) for i in range(n)]
 win=draw=loss=over=both=0.
 for i in range(n):
  for j in range(n):
   p=ph[i]*pa[j]
   if i>j:win+=p
   elif i==j:draw+=p
   else:loss+=p
   if i+j>=3:over+=p
   if i>0 and j>0:both+=p
 mass=sum(ph)*sum(pa)
 return {"lambda_home":lh,"lambda_away":la,"p_home":win,"p_draw":draw,"p_away":loss,"p_over25":over,"p_btts":both,"matrix_mass":mass,"tail_mass":1-mass,"home_samples":len(home),"away_samples":len(away),"league_samples":len(past),"method":"historical_goals_shrunk_home_away_poisson_v0_experimental","data_cutoff_exclusive":target_date}

def main():
 path=Path(sys.argv[1]) if len(sys.argv)>1 else Path("data/historical_results.csv")
 with path.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
 rows.sort(key=lambda r:(r["match_date"],r["fixture_id"]))
 assert len({r["fixture_id"] for r in rows})==len(rows),"Duplicate fixture_id"
 checked=0;skipped=0;brier=0.;logloss=0.;tail=0.\n baseline_brier=0.;baseline_logloss=0.;model_wins=0;baseline_wins=0;ties=0
 for r in rows:
  p=estimate(rows,r["league"],r["home_id"],r["away_id"],r["match_date"])
  if p is None:skipped+=1;continue
  # Same historical cutoff, same scored fixtures, and Laplace smoothing.\n  prior=[x for x in rows if x["league"]==r["league"] and x["match_date"]<r["match_date"]]\n  counts=[sum(x["result"]==v for x in prior) for v in ("H","D","A")]\n  baseline=[(n+1)/(len(prior)+3) for n in counts]\n  probs=[p["p_home"],p["p_draw"],p["p_away"]]
  truth=[int(r["result"]==v) for v in ("H","D","A")]
  # Residual tail is explicit; normalize only for scoring 1X2.
  s=sum(probs);probs=[x/s for x in probs]
  brier+=sum((x-y)**2 for x,y in zip(probs,truth))
  logloss-=math.log(max(1e-12,probs[truth.index(1)]))
  tail=max(tail,p["tail_mass"])
  checked+=1
 report={"version":"poisson_goals_baseline_v0_experimental","historical_rows":len(rows),"scored":checked,"skipped":skipped,"mean_multiclass_brier":brier/checked if checked else None,"mean_log_loss":logloss/checked if checked else None,"baseline_mean_multiclass_brier":baseline_brier/checked if checked else None,"baseline_mean_log_loss":baseline_logloss/checked if checked else None,"brier_improvement_vs_baseline":(baseline_brier-brier)/checked if checked else None,"logloss_improvement_vs_baseline":(baseline_logloss-logloss)/checked if checked else None,"per_match_brier_wins":{"poisson":model_wins,"league_baseline":baseline_wins,"ties":ties},"baseline_method":"league_historical_1x2_frequencies_laplace_one_same_cutoff","max_matrix_tail_mass":tail,"leakage_rule":"Only match_date strictly before target date","warnings":["Not xG model","No Dixon-Coles calibration","No Elo","No odds or EV","No first-half corners","Not validated for betting"]}
 Path("data").mkdir(exist_ok=True)
 Path("data/poisson_baseline_backtest.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":main()
