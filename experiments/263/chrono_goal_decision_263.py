"""ONE retrospective research cohort: 2026/27 880 games, goals/KG 4 models.

Aug-Sep 587 development and Oct 293 evaluation; October is NOT untouched
because earlier 1X2 studies already explored it. Does not promote S1/S2.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from collections import defaultdict,Counter
from exp_263_batch import clean_rows,c1,fit_c3,predict_c3,scores
from forward_quad import _b_lambdas,_legacy_joint
from analysis_math_core import canonical_c2_lambda,score_market
from m4_integrated import fit_m4,predict_m4,score_markets,use_lock
from classification_odds_263 import stress_low
SHA="35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1"
MODELS=("B","C2","C3","M4")
MARKETS=("MS1","MSX","MS2","OVER_1.5","UNDER_1.5","OVER_2.5","UNDER_2.5","OVER_3.5","UNDER_3.5","BTTS_YES","BTTS_NO")
PROFILES={"T0_original_75_70":(.75,.70),"T1_relaxed_70_65":(.70,.65),"T2_asof_calibrated_relative":(.63,.58)}
def family(m):
 return "GOALS" if m.startswith(("OVER_","UNDER_")) else "BTTS" if m.startswith("BTTS_") else "MS"
def outcome(r,m):
 h,a=int(r["home_goals"]),int(r["away_goals"])
 if m=="MS1":return int(h>a)
 if m=="MSX":return int(h==a)
 if m=="MS2":return int(h<a)
 if m=="BTTS_YES":return int(h>0 and a>0)
 if m=="BTTS_NO":return int(not(h>0 and a>0))
 over=(h+a)>float(m.split("_")[1])
 return int(over if m.startswith("OVER_") else not over)
def base(past):
 if len(past)<60:return None
 return {m:sum(outcome(r,m) for r in past)/len(past) for m in MARKETS}
def probs(goals):
 mk=goals["markets"];ms=mk["1X2"]
 p={"MS1":ms["H"],"MSX":ms["D"],"MS2":ms["A"]}
 p.update({m:mk[m] for m in MARKETS if m not in p})
 if abs(p["MS1"]+p["MSX"]+p["MS2"]-1)>1e-6:raise ValueError("MS_NOT_NORMALIZED")
 if any(not math.isfinite(v) or v<0 or v>1 for v in p.values()):raise ValueError("BAD_PROB")
 return p
def records_for_day(past,fixtures,league,day,setting):
 if any(r["match_date"]>=day for r in past):raise ValueError("SAME_DAY_LEAKAGE")
 histbase=base(past)
 now_season=[r for r in past if r["season"]=="2026-2027"]
 prev=[r for r in past if r["season"]=="2025-2026"]
 f3=fit_c3(past);f4=fit_m4(past,league,day,setting)
 result=[]
 for r in fixtures:
  h,a=r["home_id"],r["away_id"];mod={}
  b=c1(past,h,a);bl=_b_lambdas(past,h,a)
  if b and bl:mod["B"]=_legacy_joint(*bl,b[0])
  c,reason=canonical_c2_lambda(now_season,prev,h,a)
  if c:mod["C2"]=score_market(c["lambda_home"],c["lambda_away"])
  l3=predict_c3(f3,h,a) if f3 is not None else None
  if l3:
   s=scores(*l3)
   if s:mod["C3"]=_legacy_joint(*l3,s[0])
  l4=predict_m4(f4,h,a)
  if l4:mod["M4"]=score_markets(*l4)
  result.append({"id":r["fixture_id"],"league":league,"date":day,"base":histbase,
                 "y":{m:outcome(r,m) for m in MARKETS},
                 "p":{k:probs(v) for k,v in mod.items()},
                 "c2_lambdas":(c["lambda_home"],c["lambda_away"]) if c else None})
 return result
def reconstruct(path,lock):
 rows=clean_rows(path)
 if len(rows)!=4413 or hashlib.sha256(Path(path).read_bytes()).hexdigest()!=SHA:raise ValueError("BAD_FROZEN_SHA")
 if lock["frozen_source_sha256"]!=SHA:raise ValueError("LOCK_SOURCE_MISMATCH")
 setting=use_lock(lock)
 leagues=defaultdict(list)
 for r in rows:leagues[r["league"]].append(r)
 records=[];months=Counter()
 for league,rr in sorted(leagues.items()):
  past=[];i=0
  while i<len(rr):
   day=rr[i]["match_date"];j=i
   while j<len(rr) and rr[j]["match_date"]==day:j+=1
   matches=rr[i:j]
   if day.startswith(("2026-08","2026-09","2026-10")):
    records+=records_for_day(past,matches,league,day,setting)
    months[day[:7]]+=len(matches)
   past+=matches;i=j
 if dict(months)!={"2026-08":259,"2026-09":328,"2026-10":293}:raise ValueError("COHORT_CHANGED")
 return records,months
def shrink_weights(dev):
 weights={}
 for m in MARKETS:
  obs=[(r["p"]["C2"][m],r["base"][m],r["y"][m]) for r in dev if "C2" in r["p"] and r["base"]]
  n=len(obs)
  if n<60:weights[m]={"n":n,"w":0.,"available":False};continue
  den=sum((p-b)**2 for p,b,y in obs)
  raw=min(1.,max(0.,sum((p-b)*(y-b) for p,b,y in obs)/den)) if den>1e-12 else 0.
  weights[m]={"n":n,"w":round((n*raw+40)/(n+80),10),"available":True}
 return weights
def logloss(p,y):
 p=min(1-1e-7,max(1e-7,p))
 return -math.log(p if y else 1-p)
def model_scores(rows):
 out={}
 for model in MODELS:
  markets={}
  for m in MARKETS:
   a=[(r["p"][model][m],r["y"][m],r["base"][m]) for r in rows if model in r["p"] and r["base"]]
   n=len(a)
   if not n:markets[m]={"n":0};continue
   mse=sum((p-y)**2 for p,y,b in a)/n
   bse=sum((b-y)**2 for p,y,b in a)/n
   markets[m]={"n":n,"brier":round(mse,6),"logloss":round(sum(logloss(p,y) for p,y,b in a)/n,6),
               "brier_skill_vs_same_event_asof_base":round(1-mse/bse,6) if bse else None}
  out[model]={"fixture_coverage":sum(model in r["p"] for r in rows),"markets":markets}
 return out
def select(row,profile,weights):
 if "C2" not in row["p"] or row["base"] is None:
  return None,None,"C2_CONTEXT_MISSING"
 p=row["p"]["C2"];b=row["base"];lh,la=row["c2_lambdas"]
 picks=[]
 for m in MARKETS:
  cutoff,floor=PROFILES[profile]
  if profile=="T2_asof_calibrated_relative":
   if not weights[m]["available"]:continue
   q=b[m]+weights[m]["w"]*(p[m]-b[m])
   if q<cutoff or q-b[m]<.03:continue
   score=q-b[m]+.1*q
  else:
   q=p[m];score=q
   if q<cutoff:continue
  if stress_low(m,lh,la)<floor:continue
  picks.append({"market":m,"family":family(m),"p":q,"raw_p":p[m],"base":b[m],
                "y":row["y"][m],"priority":score})
 if not picks:return None,None,"NO_QUALIFIED_MARKET"
 picks.sort(key=lambda x:(-x["priority"],-x["p"],x["market"]))
 main=picks[0]
 alternative=next((x for x in picks[1:] if x["family"]!=main["family"]),None)
 return main,alternative,None
def summarize(rows,profile,weights):
 selected=[];alt=0;pas=Counter()
 for r in rows:
  a,b,why=select(r,profile,weights)
  if a is None:pas[why]+=1
  else:
   selected.append(a)
   if b is not None:alt+=1
 counts=Counter(x["market"] for x in selected);n=len(selected)
 mse=sum((x["p"]-x["y"])**2 for x in selected)/n if n else None
 bse=sum((x["base"]-x["y"])**2 for x in selected)/n if n else None
 return {"matches":len(rows),"would_select":n,"PAS":len(rows)-n,"coverage_pct":round(100*n/len(rows),2),
         "alternative_count":alt,"pas_reasons":dict(pas),"selection_distribution":dict(counts),
         "over15_selection_share_pct":round(100*counts.get("OVER_1.5",0)/n,2) if n else 0,
         "under35_selection_share_pct":round(100*counts.get("UNDER_3.5",0)/n,2) if n else 0,
         "observed_hit_pct":round(100*sum(x["y"] for x in selected)/n,2) if n else None,
         "selected_brier":round(mse,6) if n else None,
         "same_selected_event_asof_baseline_brier":round(bse,6) if n else None,
         "paired_brier_minus_baseline":round(mse-bse,6) if n else None,
         "S1_S2_approved":False,"EV_or_ROI":None}
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--source",required=True);ap.add_argument("--report",required=True)
 ap.add_argument("--predictions",required=True);args=ap.parse_args()
 lock=json.loads(Path("experiments/263/m4_lock.json").read_text(encoding="utf-8"))
 rec,months=reconstruct(args.source,lock)
 dev=[r for r in rec if r["date"]<"2026-10-01"]
 test=[r for r in rec if r["date"]>="2026-10-01"]
 if len(dev)!=587 or len(test)!=293:raise ValueError("WRONG_DEV_TEST_COUNTS")
 weights=shrink_weights(dev)
 result={"schema":"263_four_model_goals_pas_walkforward_research_v1",
         "status":"RECONSTRUCTED_HISTORICAL_OCTOBER_PREVIOUSLY_EXPLORED_NO_PROMOTION",
         "original_source_sha256":SHA,"source_matches":4413,
         "date_cutoffs":{"development":"2026-08-01_through_2026-09-30","evaluation":"2026-10-01_through_2026-10-29"},
         "development_n":len(dev),"evaluation_n":len(test),"months":dict(months),
         "models":["B","C2","C3","M4"],"market_list":list(MARKETS),
         "dev_only_market_shrinkage_weights":weights,
         "dev_quality":model_scores(dev),"test_quality":model_scores(test),
         "policy_comparison":{k:summarize(test,k,weights) for k in PROFILES},
         "policy_parameters":{"T0_original_75_70":"p>=.75, lambda-stress>=.70, rank by raw p",
           "T1_relaxed_70_65":"p>=.70, lambda-stress>=.65, rank by raw p",
           "T2_asof_calibrated_relative":"dev-only baseline shrinkage, p>=.63, asof league uplift>=.03, lambda-stress>=.58, rank uplift + 0.1*p"},
         "production_rules_changed":False,"human_source_review_claimed":False,
         "pilot_count_increment":0,"S1_S2_officially_approved":False,"historical_bookmaker_odds_available":False,
         "warnings":["Retrospective asof reconstruction is NOT a pre-kickoff GitHub sealed prediction",
          "October 2026/27 already inspected in earlier research: not an independent final holdout",
          "Same date results never used as features; season-specific C2 context may be missing",
          "A goal 1.5 and goal 2.5 decision are correlated and never independent alternatives",
          "Goal 1.5 baseline relative lift is a diagnostic, not proof of calibrated accuracy or value",
          "Lambda +/-10% stress is NOT statistical confidence interval",
          "No historical timed odds: no S2/EV/ROI and no actual betting advice",
          "Compare selected-market Brier to SAME chosen-event historical base, not raw across base rates"]}
 for path in (args.report,args.predictions):
  p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():raise ValueError("REPORT_OVERWRITE_FORBIDDEN")
 Path(args.report).write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 with Path(args.predictions).open("x",encoding="utf-8",newline="") as f:
  w=csv.writer(f);w.writerow(["fixture_id","league","date","model","market","probability","actual",
                             "asof_baseline","record_type"])
  for r in rec:
   for name,p in r["p"].items():
    for m,v in p.items():
     w.writerow([r["id"],r["league"],r["date"],name,m,format(v,".12g"),r["y"][m],
                 format(r["base"][m],".12g"),"RETROSPECTIVE_ASOF_NOT_SEALED"])
 print(json.dumps({"evaluation_n":len(test),
   "model_coverage":{k:v["fixture_coverage"] for k,v in result["test_quality"].items()},
   "policies":{k:{"select":v["would_select"],"PAS":v["PAS"],"over15_share":v["over15_selection_share_pct"],
                  "brier_vs_base":v["paired_brier_minus_baseline"]}
               for k,v in result["policy_comparison"].items()}},ensure_ascii=False))
if __name__=="__main__":main()
