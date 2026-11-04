"""Stage-2 learning on EXACT already-reconstructed 880-match GOALS/KG artifact.

Never refit B/C2/C3/M4 or re-download history. The first T2 policy produced
293 PAS because C2 had ZERO Aug-Sep development predictions. Compare C3 and
M4 early-season calibration separately, without promoting either to C2.
"""
import argparse,csv,json,math,hashlib
from pathlib import Path
from collections import defaultdict,Counter

EXPECTED_SCHEMA="263_four_model_goals_pas_walkforward_research_v1"
EXPECTED_SOURCE="35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1"
MARKETS=("MS1","MSX","MS2","OVER_1.5","UNDER_1.5","OVER_2.5",
         "UNDER_2.5","OVER_3.5","UNDER_3.5","BTTS_YES","BTTS_NO")
OPTIONS={"M4":{"min_prob":.60,"min_lift":.025},"C3":{"min_prob":.60,"min_lift":.025}}
REQUIRED_FIELDS=("fixture_id","league","date","model","market","probability","actual","asof_baseline","record_type")

def group(m):
 return "GOALS" if m.startswith(("OVER_","UNDER_")) else "BTTS" if m.startswith("BTTS_") else "MS"

def load_predictions(path):
 fixtures={}
 with Path(path).open(encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  if set(reader.fieldnames or ())!=set(REQUIRED_FIELDS):raise ValueError("BAD_INPUT_SCHEMA")
  for row in reader:
   fid=row["fixture_id"];market=row["market"];model=row["model"]
   if market not in MARKETS or model not in ("B","C2","C3","M4"):raise ValueError("INVALID_MODEL_OR_MARKET")
   if row["record_type"]!="RETROSPECTIVE_ASOF_NOT_SEALED":raise ValueError("WRONG_RECONSTRUCTION_KIND")
   if row["date"]<"2026-08-01" or row["date"]>"2026-10-29":raise ValueError("OUT_OF_SCOPE_DAY")
   p=float(row["probability"]);b=float(row["asof_baseline"]);y=int(row["actual"])
   if not all(math.isfinite(v) and 0<=v<=1 for v in (p,b)) or y not in (0,1):raise ValueError("BAD_P_OR_LABEL")
   r=fixtures.setdefault(fid,{"league":row["league"],"date":row["date"],"obs":{},"base":{},"p":defaultdict(dict)})
   if (r["date"],r["league"])!=(row["date"],row["league"]):raise ValueError("FIXTURE_ID_COLLISION")
   if model in r["p"] and market in r["p"][model]:raise ValueError("DUPLICATE_MODEL_MARKET")
   if market in r["obs"] and (r["obs"][market]!=y or abs(r["base"][market]-b)>1e-9):
    raise ValueError("MODEL_ROWS_DISAGREE_ON_SCORE_OR_HISTORY")
   r["obs"][market]=y;r["base"][market]=b;r["p"][model][market]=p
 if len(fixtures)!=880:raise ValueError("EXPECTED_EXACT_880_MATCHES")
 result=list(fixtures.values())
 if sum(r["date"]<"2026-10-01" for r in result)!=587:raise ValueError("NO_587_DEVELOPMENT")
 if sum(r["date"]>="2026-10-01" for r in result)!=293:raise ValueError("NO_293_OCTOBER")
 for r in result:
  for name,ps in r["p"].items():
   if set(ps)!=set(MARKETS):raise ValueError("INCOMPLETE_MODEL_MARKETS")
 return result

def calibration(dev,model):
 result={}
 for market in MARKETS:
  a=[(r["p"][model][market],r["base"][market],r["obs"][market])
     for r in dev if model in r["p"]]
  n=len(a)
  if n<120:
   result[market]={"n":n,"available":False,"weight":None,"development_brier_skill":None}
   continue
  den=sum((p-b)**2 for p,b,y in a)
  raw=max(0,min(1,sum((p-b)*(y-b) for p,b,y in a)/den)) if den>1e-12 else 0
  weight=(n*raw+80*.5)/(n+80)
  forecast_mse=sum((p-y)**2 for p,b,y in a)/n
  base_mse=sum((b-y)**2 for p,b,y in a)/n
  result[market]={"n":n,"available":True,"weight":round(weight,10),
     "development_brier_skill":round(1-forecast_mse/base_mse,6) if base_mse else None,
     "unshrunk_weight":round(raw,6)}
 return result

def choose(r,model,cals,require_skill):
 if model not in r["p"]:return None,None,"MODEL_MISSING"
 candidates=[]
 for m in MARKETS:
  c=cals[m]
  if not c["available"]:continue
  if require_skill and (c["development_brier_skill"] is None or c["development_brier_skill"]<=0):
   continue
  b=r["base"][m];p=r["p"][model][m]
  q=b+c["weight"]*(p-b)
  lift=q-b
  if q<OPTIONS[model]["min_prob"] or lift<OPTIONS[model]["min_lift"]:
   continue
  candidates.append({"market":m,"family":group(m),"p":q,"b":b,"y":r["obs"][m],
                     "priority":lift+.1*q})
 if not candidates:return None,None,"NO_RELIABLE_CANDIDATE"
 candidates.sort(key=lambda x:(-x["priority"],-x["p"],x["market"]))
 main=candidates[0]
 alt=next((x for x in candidates[1:] if x["family"]!=main["family"]),None)
 return main,alt,None

def summarize(test,model,cals,require_skill):
 picks=[];alternatives=0;pas=Counter()
 for r in test:
  main,alt,why=choose(r,model,cals,require_skill)
  if main is None:pas[why]+=1
  else:
   picks.append(main)
   if alt is not None:alternatives+=1
 n=len(picks);dist=Counter(x["market"] for x in picks)
 mse=sum((x["p"]-x["y"])**2 for x in picks)/n if n else None
 base_mse=sum((x["b"]-x["y"])**2 for x in picks)/n if n else None
 return {"model":model,"skill_gate_from_development":require_skill,
     "evaluation_match_count":len(test),"would_select_n":n,"PAS_n":len(test)-n,
     "coverage_pct":round(n/len(test)*100,2),
     "alternative_n":alternatives,
     "selection_counts":dict(sorted(dist.items())),
     "over15_share_pct":round(dist.get("OVER_1.5",0)*100/n,2) if n else 0,
     "under35_share_pct":round(dist.get("UNDER_3.5",0)*100/n,2) if n else 0,
     "selected_event_hit_rate_pct":round(sum(x["y"] for x in picks)*100/n,2) if n else None,
     "selected_event_brier":round(mse,6) if n else None,
     "same_selected_event_baseline_brier":round(base_mse,6) if n else None,
     "paired_selected_event_brier_minus_baseline":round(mse-base_mse,6) if n else None,
     "PAS_reasons":dict(sorted(pas.items())),
     "betting_authorized":False}
def evaluate(predictions,prior_report):
 if prior_report.get("schema")!=EXPECTED_SCHEMA or prior_report.get("original_source_sha256")!=EXPECTED_SOURCE:
  raise ValueError("NOT_EXACT_PRIOR_ONE_SHOT_REPORT")
 if prior_report.get("development_n")!=587 or prior_report.get("evaluation_n")!=293:
  raise ValueError("PRIOR_REPORT_COHORT_MISMATCH")
 if prior_report.get("production_rules_changed") is not False or prior_report.get("S1_S2_officially_approved") is not False:
  raise ValueError("PRIOR_REPORT_WRONGLY_PROMOTED")
 dev=[r for r in predictions if r["date"]<"2026-10-01"]
 test=[r for r in predictions if r["date"]>="2026-10-01"]
 cal={name:calibration(dev,name) for name in OPTIONS}
 variants={}
 for name in OPTIONS:
  for gate in (False,True):
   key=name+("_development_skill_gate" if gate else "_candidate_without_skill_gate")
   variants[key]=summarize(test,name,cal[name],gate)
 return {"schema":"263_reuse_first_880_asof_C3_M4_calibration_research_v1",
         "status":"EXPLORATORY_ONLY_DO_NOT_REPLACE_CANONICAL_C2",
         "prior_880_source_sha256":EXPECTED_SOURCE,
         "prior_880_report_status":prior_report["status"],
         "C2_early_development_matches":prior_report["dev_quality"]["C2"]["fixture_coverage"],
         "C2_october_evaluation_matches":prior_report["test_quality"]["C2"]["fixture_coverage"],
         "purpose":"Determine if model coverage (rather than arbitrary PAS thresholds) blocks early-season model learning",
         "dev_n":len(dev),"oct_test_n":len(test),
         "model_calibration":cal,
         "oct_test_experimental_decisions":variants,
         "applied_strategy":None,"S1_approved":False,"S2_approved":False,
         "main_or_alternative_picks_recorded":False,"pilot_increment":0,
         "historical_odds_available":False,"past_predictions_are_sealed_live":False,
         "model_promoted":False,"betting_authorized":False,
         "warnings":["Reuses the SAME already explored October outcomes, so NOT a truly new final holdout",
          "C3/M4 were experimental model rivals; this does NOT auto-fallback when C2 is absent",
          "A market with development brier skill <=0 can be considered research only; do not approve bets",
          "Pooled shrinkage learned only on Aug-Sep, no October outcome used to set weights",
          "A low PAS rate is not a win by itself; compare same selected-event baseline Brier",
          "Family of markets not statistically independent even with separate names",
          "No timestamped prices; EV, ROI, value-based S2 unsupported"]}
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--predictions",required=True);ap.add_argument("--prior-report",required=True)
 ap.add_argument("--out",required=True)
 args=ap.parse_args()
 p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():raise SystemExit("NO_OVERWRITE_REPORT")
 old=json.loads(Path(args.prior_report).read_text(encoding="utf-8"))
 r=evaluate(load_predictions(args.predictions),old)
 p.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":r["status"],
   "C2_dev":r["C2_early_development_matches"],
   "C2_oct":r["C2_october_evaluation_matches"],
   "experiments":{k:{"main":v["would_select_n"],"pas":v["PAS_n"],
      "over15_share":v["over15_share_pct"],"paired_brier_vs_base":v["paired_selected_event_brier_minus_baseline"]}
        for k,v in r["oct_test_experimental_decisions"].items()}},ensure_ascii=False))
if __name__=="__main__":main()
