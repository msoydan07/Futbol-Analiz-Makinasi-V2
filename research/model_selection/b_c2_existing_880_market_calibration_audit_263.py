"""B/C2 KG & 2.5 Alt/Ust & MS market calibration using the EXACT 880 as-of archive.

NO model retraining, no new pilot, no guessed 96 seals. Reuse November 4
historical original 880 predictions generated before this market experiment.
Fixed cohort: 587 Aug-Sep 2026 DEV; 293 Oct 2026 *already inspected* TEST.
The already published frozen DEV C3/M4 calibration lock must be identical to
recomputing its provenance. Do not backfill absent C2 Aug-Sep forecasts.

Estimates B's DEV-only historical market skill/shrinkage using the original
stage2 function and measures B/C2/C3/M4 on identical matched occasions.
For categorical MS use proper 3-way Brier/logloss and never normalize or
present separately-calibrated MS1/X/2 as a coherent 3-way distribution.
Never write main model, frozen calibration lock or mobile decisions.

Any Oct result is an EXPLORATORY historical replay, not a fresh validation
set or a legitimate prospective model-routing promotion.
"""
from __future__ import annotations
import argparse,hashlib,json,math,random,sys
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments/263"))
from chrono_goal_stage2_263 import (
  EXPECTED_SOURCE,EXPECTED_SCHEMA,MARKETS,load_predictions,calibration
)
from forward_calibration_bridge_263 import CAL_SCHEMA,_digest

ORIGINAL_ARTIFACT_RUN=41836437930
ARCHIVE_SHA="dc674e2d05641eca27a8655eacfe6457e4140fb2adbdb0d9002b45e38cca1b3d"
PRIOR_STAGE2_REPORT_SHA="f01dfe8c10fdda1d9958b7f592f5cfd72a61f48f14f9b35e8342188acda26e00"
LOCK_PATH=ROOT/"experiments/263/forward_dev_calibration_lock_263.json"
DEV_MAX_EXCLUSIVE="2026-10-01"
MODELS=("B","C2","C3","M4")
FIELDS=("KG","OVER25","MS")
MAPPINGS={
  "KG":("BTTS_YES","BTTS_NO"),
  "OVER25":("OVER_2.5","UNDER_2.5"),
  "MS":("MS1","MSX","MS2")
}
METRICS=("brier","logloss","top1")
class AuditBlocked(ValueError):pass
def need(x,msg):
    if not x:raise AuditBlocked(msg)
def file_sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mean(x):return sum(x)/len(x) if x else None
def metrics(p,y,market):
    if market=="MS":
        states=MAPPINGS["MS"]
        need(set(p)==set(states),"MISSING_MS_VECTOR")
        need(all(math.isfinite(p[s]) and 0<=p[s]<=1 for s in states) and
             abs(sum(p.values())-1)<1e-7,"INVALID_3WAY_PROBABILITY")
        actual=next(s for s in states if y[s]==1)
        return {
         "brier":sum((p[s]-y[s])**2 for s in states),
         "logloss":-math.log(max(1e-12,p[actual])),
         "top1":int(max(states,key=lambda k:p[k])==actual)}
    yes=MAPPINGS[market][0]
    q=float(p[yes])
    need(math.isfinite(q) and 0<=q<=1 and y[yes] in (0,1),"INVALID_BINARY_PROBABILITY")
    v=int(y[yes])
    return {"brier":(q-v)**2,
            "logloss":-math.log(max(1e-12,q if v else 1-q)),
            "top1":int((q>=.5)==bool(v))}

def per_event(row,model,market):
    fields=MAPPINGS[market]
    need(model in row["p"],"UNAVAILABLE_MODEL_CANNOT_BE_SCORED")
    p={f:row["p"][model][f] for f in fields}
    y={f:row["obs"][f] for f in fields}
    base={f:row["base"][f] for f in fields}
    need(all(f in row["base"] and f in row["obs"] for f in fields),
         "MISSING_ASOF_BASE")
    if market in ("KG","OVER25"):
        y0,y1=fields
        need(abs((p[y0]+p[y1])-1)<1e-7 and
             abs((base[y0]+base[y1])-1)<1e-7 and
             y[y0]+y[y1]==1,"INVALID_BINARY_COMPLEMENT")
    return {"model":metrics(p,y,market),"base":metrics(base,y,market)}

def score_market(rows,model,market):
    relevant=[r for r in rows if model in r["p"]]
    if not relevant:return {"n":0,"brier":None,"logloss":None,"top1_correct":None,
                             "baseline_brier":None,"skill_vs_asof_base":None}
    ev=[per_event(r,model,market) for r in relevant]
    mse=mean([x["model"]["brier"] for x in ev])
    bse=mean([x["base"]["brier"] for x in ev])
    return {"n":len(ev),"brier":mse,
      "logloss":mean([x["model"]["logloss"] for x in ev]),
      "top1_correct":sum(x["model"]["top1"] for x in ev),
      "baseline_brier":bse,
      "skill_vs_asof_base":1-mse/bse if bse else None}

def pair_metric(rows,model,reference,market):
    # Exact matched fixtures and exactly same targets/baselines.
    paired=[r for r in rows if model in r["p"] and reference in r["p"]]
    if not paired:return {"n":0}
    d=[]
    for r in paired:
        a=per_event(r,model,market)["model"]
        b=per_event(r,reference,market)["model"]
        d.append({"date":r["date"],**{
            k:a[k]-b[k] for k in METRICS}})
    return {
     "n":len(d),"days":len({r["date"] for r in d}),
     "candidate_minus_reference_negative_Brier_improves":{
        k:mean([r[k] for r in d]) for k in ("brier","logloss")},
     "candidate_minus_reference_top1_count":sum(r["top1"] for r in d),
     "calendar_day_resampling_interval":day_ci(d,"brier")
    }

def day_ci(vals,field,draws=500,seed=20261111):
    groups=defaultdict(list)
    for x in vals:groups[x["date"]].append(x[field])
    if len(vals)<70 or len(groups)<10:return None
    days=sorted(groups);rnd=random.Random(seed)
    values=[]
    for _ in range(draws):
        pool=[v for __ in days for v in groups[days[rnd.randrange(len(days))]]]
        values.append(mean(pool))
    values.sort()
    return {
      "lower":values[int(.025*draws)],
      "upper":values[int(.975*draws)-1],
      "n_days":len(groups),
      "method":"EXPLORATORY_WHOLE_CALENDAR_DATES_NO_UNTOUCHED_HOLDOUT"
    }

def binary_shadow_calibration(rows,model,dev_cal,market):
    """Uses ONLY frozen Aug-Sep DEV weight. Do NOT calibrate MS category vectors."""
    need(market in ("KG","OVER25"),"MS_NOT_INDEPENDENT_BINARY_EVENT")
    fields=MAPPINGS[market]
    c=dev_cal[fields[0]]
    if c["available"] is not True or c["development_brier_skill"] is None:
        return {"status":"NO_DEVELOPMENT_SUPPORT","n":0}
    w=c["weight"]
    sample=[r for r in rows if model in r["p"]]
    out=[]
    for r in sample:
        p=r["p"][model][fields[0]]
        b=r["base"][fields[0]]
        y=r["obs"][fields[0]]
        q=b+w*(p-b)
        need(0<=q<=1,"SHADOW_WEIGHT_WRONG")
        out.append({"raw":(p-y)**2,"shrunk":(q-y)**2,
                    "asof_base":(b-y)**2,"logloss":-math.log(max(1e-12,q if y else 1-q))})
    if not out:return {"status":"NO_EVALUATION_COVERAGE","n":0}
    skill=mean([z["shrunk"] for z in out]);bse=mean([z["asof_base"] for z in out])
    return {
      "status":"OCTOBER_EXPLORATORY_ONLY_NOT_FUTURE_APPROVAL",
      "n":len(out),"frozen_dev_weight":w,
      "development_unshrunk_skill":c["development_brier_skill"],
      "raw_Brier":mean([z["raw"] for z in out]),
      "shrunk_Brier":skill,
      "asof_baseline_Brier":bse,
      "shrunk_skill_vs_asof_baseline":1-skill/bse if bse else None,
      "shrunk_logloss":mean([z["logloss"] for z in out]),
      "lock_applied_to_actual_live_picks":False
    }

def load_inputs(prediction_path,report_path,lock_path=LOCK_PATH):
    need(file_sha(prediction_path)==ARCHIVE_SHA,"ASOF_880_PREDICTION_FILE_CHANGED")
    lock=json.loads(Path(lock_path).read_text(encoding="utf-8"))
    need(lock.get("schema")==CAL_SCHEMA and
         lock.get("official_approval") is False and
         lock.get("development_period")=="2026-08-01/2026-09-30" and
         lock.get("evaluation_period_not_used_for_weights")=="2026-10-01/2026-10-29" and
         lock.get("source_predictions_sha256")==ARCHIVE_SHA and
         lock.get("source_stage2_sha256")==PRIOR_STAGE2_REPORT_SHA and
         lock.get("payload_sha256")==_digest({k:v for k,v in lock.items() if k!="payload_sha256"}),
         "PUBLISHED_C3_M4_DEV_LOCK_CHANGED")
    prior=json.loads(Path(report_path).read_text(encoding="utf-8"))
    need(prior.get("schema")==EXPECTED_SCHEMA and
         prior.get("original_source_sha256")==EXPECTED_SOURCE and
         prior.get("development_n")==587 and prior.get("evaluation_n")==293 and
         prior.get("production_rules_changed") is False and
         prior.get("S1_S2_officially_approved") is False,
         "OLD_880_HISTORY_REPORT_CHANGED")
    rows=load_predictions(prediction_path)
    need(len(rows)==880 and len({r["date"] for r in rows})>=30,
         "CANNOT_REUSE_ORIGINAL_880")
    dev=[r for r in rows if r["date"]<DEV_MAX_EXCLUSIVE]
    oct_=[r for r in rows if r["date"]>=DEV_MAX_EXCLUSIVE]
    need(len(dev)==587 and len(oct_)==293,"DEV_OCTOBER_FROZEN_SPLIT_CHANGED")
    need(len({r["league"] for r in rows})==10,"NOT_ALL_TEN_LEAGUES")
    for model in ("C3","M4"):
        calculated=calibration(dev,model)
        pinned=lock["calibration"][model]
        need(set(calculated)==set(pinned)==set(MARKETS),"LOCK_MARKET_MISMATCH")
        for market in MARKETS:
            for attr in ("n","available","weight","development_brier_skill"):
                need(calculated[market][attr]==pinned[market][attr],
                     "OLD_CALIBRATION_MATH_VS_LOCK_DISAGREES_"+model+"_"+market+"_"+attr)
    return dev,oct_,lock

def audit(prediction_path,report_path):
    dev,oct_,lock=load_inputs(prediction_path,report_path)
    devcal={m:calibration(dev,m) for m in MODELS}
    devcounts={m:sum(m in r["p"] for r in dev) for m in MODELS}
    octcounts={m:sum(m in r["p"] for r in oct_) for m in MODELS}
    need(devcounts["C2"]==0 and octcounts["C2"]==105,
         "EARLY_SEASON_C2_MISSINGNESS_CHANGED_NO_BACKFILL")
    need(all(devcounts[m]>=120 for m in ("B","C3","M4")),
         "NO_DEV_B_C3_M4_COVERAGE")
    need(octcounts["B"]==212 and octcounts["C3"]==293 and
         octcounts["M4"]==293,"OCTOBER_KNOWN_MODEL_COUNTS_CHANGED")
    result={}
    for name,subset in (("dev_aug_sep",dev),("explored_october",oct_)):
        score={
          m:{market:score_market(subset,m,market) for market in FIELDS}
          for m in MODELS
        }
        pair={
           candidate+"_vs_"+reference:{
               market:pair_metric(subset,candidate,reference,market)
               for market in FIELDS
           }
           for candidate,reference in [
               ("B","M4"),("B","C3"),("C2","M4"),("C2","C3"),("C3","M4")]
        }
        four=[r for r in subset if all(m in r["p"] for m in MODELS)]
        four_common={
           m:{market:score_market(four,m,market) for market in FIELDS}
           for m in MODELS
        }
        result[name]={
            "matches":len(subset),
            "model_coverage":{m:sum(m in r["p"] for r in subset) for m in MODELS},
            "unique_days":len({r["date"] for r in subset}),
            "market_error_by_model_unpaired_coverage":score,
            "paired_same_fixture_loss_differences":pair,
            "four_way_same_fixture_n":len(four),
            "four_way_same_fixture_market_scores":four_common
        }
    binary_shadow={
      model:{market:binary_shadow_calibration(oct_,model,devcal[model],market)
             for market in ("KG","OVER25")}
      for model in ("B","C3","M4")
    }
    c2cal=devcal["C2"]
    need(all(v["n"]==0 and v["available"] is False and
             v.get("weight") is None for v in c2cal.values()),
         "C2_DEV_NOT_ZERO_NO_AUTO_PROMOTION")
    return {
      "schema":"263_REUSED_ORIGINAL_880_B_C2_MARKET_CALIBRATION_DIAGNOSTIC_V1",
      "status":"RESEARCH_ONLY_NO_B_C2_CALIBRATION_PROMOTION",
      "exact_original_880_artifact_run":ORIGINAL_ARTIFACT_RUN,
      "exact_original_prediction_csv_sha256":ARCHIVE_SHA,
      "validated_existing_frozen_C3_M4_lock":True,
      "development_period":"2026-08-01/2026-09-30",
      "already_inspected_october_period":"2026-10-01/2026-10-29",
      "model_coverage_dev":devcounts,
      "model_coverage_oct":octcounts,
      "market_specific_development_calibration":{
        model:{m:devcal[model][m] for m in
               ("BTTS_YES","BTTS_NO","OVER_2.5","UNDER_2.5","MS1","MSX","MS2")}
        for model in MODELS
      },
      "dev_calibrated_binary_shadow_on_explored_october":binary_shadow,
      "same_match_scores":result,
      "C2_has_any_eligible_AugSep_calibration":False,
      "B_one_model_three_way_MS_calibration_candidate_approved":False,
      "B_binary_calibration_candidate_approved":False,
      "new_market_or_model_selector_approved":False,
      "new_pilot_opened":False,
      "old_fits_recomputed":False,
      "old_sha_forecasts_modified":False,
      "retrain_or_promote_main_engine":False,
      "market_picker_or_mobile_screen_modified":False,
      "betting_authorized":False,
      "decisions":[
        "C2 zero Aug-Sep DEV coverage blocks any estimate of market skill/weight there; October 105 cases do not retroactively create early DEV.",
        "B historical DEV calibration evaluated in detached report, not injected into old C3/M4 lock.",
        "Separate per-outcome MS1/X/2 shrinkage does not preserve a normalized categorical forecast; cannot silently use as a three-way MS decision.",
        "Compare model Brier only on same fixtures: per-model coverage averages are NOT head-to-head.",
        "Oct 2026 outcomes were inspected earlier, so October is not independent prospective evidence or model-selection authorization.",
        "Keep current M4 main reference, C3/M4 old dev policy and no-verified-odds PAS; do not choose a winner on the scored 39 Nov matches."
      ],
      "limitations":[
        "Historical 880 as-of reconstructions, NOT 880 actual immutable signed pre-match forecasts.",
        "Oct outcomes were reused in earlier model research and cannot verify a discovered market advantage independently.",
        "C2 October 105 matches are useful only for same-fixture descriptive comparison, not for tuning a DEV-selected C2 calibration.",
        "Market families KG and O25 are correlated, 1.5/2.5/3.5 lines must not be treated as independent evidence.",
        "No independently timestamped bookmaker odds, no EV, no ROI, no betting guarantees.",
        "No new model parameters should be selected by repeatedly searching these known 880 outcomes.",
      ]
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--predictions",required=True)
    p.add_argument("--prior-report",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    rep=audit(args.predictions,args.prior_report)
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as f:
        json.dump(rep,f,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False)
        f.write("\n")
    def small(m):
        return {p:{"n":v["n"],"skill":v["development_brier_skill"],
                   "weight":v["weight"]} for p,v in rep["market_specific_development_calibration"][m].items()
                if p in ("BTTS_YES","OVER_2.5","MS1","MSX","MS2")}
    print(json.dumps({
      "status":rep["status"],
      "dev_coverage":rep["model_coverage_dev"],
      "oct_coverage":rep["model_coverage_oct"],
      "B_early_dev_market_calibration":small("B"),
      "C2_early_dev_market_calibration":small("C2"),
      "oct_four_way_n":rep["same_match_scores"]["explored_october"]["four_way_same_fixture_n"],
      "oct_four_way_market_Brier":{
        m:{k:rep["same_match_scores"]["explored_october"]["four_way_same_fixture_market_scores"][m][k]["brier"]
           for k in FIELDS} for m in MODELS},
      "B_oct_shadow":rep["dev_calibrated_binary_shadow_on_explored_october"]["B"],
      "new_selector_approved":False
    },ensure_ascii=False))
if __name__=="__main__":main()
