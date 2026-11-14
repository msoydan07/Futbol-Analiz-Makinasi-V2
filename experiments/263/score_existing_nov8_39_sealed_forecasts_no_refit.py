#!/usr/bin/env python3
"""Score ONLY already sealed 2026-11-08 new100 pre-match forecasts vs archived results.

Research diagnosis, NOT fresh independent verification, model fitting, strategy or
betting analysis. No network and no old-result re-query. Forecast SHA verified.
All 39 results reported by existing archive remain qualified by source grade.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from collections import Counter,defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
# Inline the audit-locked canonical JSON and aware-time contracts for a pure
# stdlib scoring step. Importing model-fit modules pulls numerical dependencies
# and would be unnecessary for read-only outcomes.
def read_aware(value):
 parsed=datetime.fromisoformat(str(value).replace("Z","+00:00"))
 if parsed.tzinfo is None:raise ValueError("TIMEZONE_REQUIRED")
 return parsed.astimezone(timezone.utc)
def sealed_payload(obj, expected_schema):
 if obj.get("schema")!=expected_schema:raise ValueError("FORECAST_SCHEMA_WRONG")
 fingerprint=obj.get("payload_sha256")
 if not isinstance(fingerprint,str) or len(fingerprint)!=64:raise ValueError("FORECAST_SHA_MISSING")
 rest=dict(obj);rest.pop("payload_sha256",None)
 canonical=json.dumps(rest,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")
 if hashlib.sha256(canonical).hexdigest()!=fingerprint:raise ValueError("FORECAST_SHA_TAMPERED")
 return fingerprint

ROOT=Path(".")
ARCH=ROOT/"data/results_only_263/nov8_new100_terminal_archive_20261112.json"
OUT=ROOT/"experiments/263/league_expansion/NOV8_39_OLD_SEALS_MODEL_OUTCOME_PROVISIONAL_ONLY_20261114.json"
MODELS=("B","C2","C3","M4")
MARKETS=("BTTS_YES","OVER_1.5","OVER_2.5","OVER_3.5")
ALL_LABELS=("H","D","A")
ALLOWED_EVIDENCE={"TFF_NETWORK_VERIFIED","OFFICIAL_CLUB_WEB_RESEARCH",
"OFFICIAL_LEAGUE_WEB_RESEARCH","EXTERNAL_FEDERATION_WEB_RESEARCH"}

def read(path):return json.loads(path.read_text(encoding="utf-8"))
def score(model,h,a):
 if model.get("status")!="AVAILABLE":return None
 m=model["goals"]["markets"]
 p3=m["1X2"]
 if set(p3)!={"H","D","A"}:raise ValueError("INVALID_THREE_WAY_MARKET_SHAPE")
 vals=[float(p3[k]) for k in ALL_LABELS]
 if not all(0<=v<=1 and math.isfinite(v) for v in vals):raise ValueError("NONFINITE_1X2")
 if abs(sum(vals)-1)>1e-7:raise ValueError("NOT_NORMALIZED_1X2")
 outcome="H" if h>a else "D" if h==a else "A"
 cat={"accuracy":int(max(ALL_LABELS,key=lambda x:p3[x])==outcome),
      "brier":sum((p3[k]-int(outcome==k))**2 for k in ALL_LABELS),
      "logloss":-math.log(max(float(p3[outcome]),1e-15))}
 actual={
  "BTTS_YES":int(h>0 and a>0),
  "OVER_1.5":int(h+a>=2),
  "OVER_2.5":int(h+a>=3),
  "OVER_3.5":int(h+a>=4)
 }
 goal={}
 for market in MARKETS:
  prob=float(m[market])
  if not (math.isfinite(prob) and 0<=prob<=1):raise ValueError("INVALID_BINARY_PROB")
  y=actual[market]
  goal[market]={"accuracy":int((prob>=0.5)==bool(y)),
    "brier":(prob-y)**2,
    "logloss":-(y*math.log(max(prob,1e-15))+(1-y)*math.log(max(1-prob,1e-15)))}
 return {"1X2":cat,**goal}
def metrics(values):
 if not values:return None
 return {k:round(sum(x[k] for x in values)/len(values),6) for k in ("accuracy","brier","logloss")}
def calculate():
 archive=read(ARCH)
 assert (archive["registered"],archive["completed"],archive["postponed"])==(40,39,1)
 assert archive["human_attestation_count"]==0
 assert archive["daily_repeat_source_calls_allowed"] is False
 assert archive["model_or_original_seals_modified"] is False
 records=archive["rows"]
 assert len(records)==40
 counts=Counter();good=[];per_sha=set();provisional=defaultdict(list)
 signatures={}
 for row in records:
  state=row["match_state"]
  if state!="FINISHED_ARCHIVED":
   assert state.startswith("POSTPONED") and row.get("score") is None
   counts["postponed_no_scoring"]+=1
   continue
  source=row["evidence_grade"]
  if source not in ALLOWED_EVIDENCE:raise ValueError("UNKNOWN_ARCHIVAL_EVIDENCE_GRADE")
  if not isinstance(row.get("score"),list) or len(row["score"])!=2:raise ValueError("MISSING_RESULT")
  h,a=row["score"]
  if any(type(v)!=int or not 0<=v<=20 for v in (h,a)):raise ValueError("INVALID_RESULT")
  target=ROOT/row["forecast_path"]
  if not target.is_file():raise ValueError("FORECAST_FILE_NOT_IN_GITHUB_ARCHIVE "+str(target))
  f=read(target)
  seal=sealed_payload(f,"quad_forward_263_v1")
  if seal!=row["forecast_sha256"] or seal in per_sha:raise ValueError("SHA_OR_DUPLICATE")
  per_sha.add(seal)
  x=f["fixture"]
  if x.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE":raise ValueError("OFFICIAL_GATE_MISSING")
  if (x["league"],x["kickoff_utc"],x["match_local_date"])!=(row["league"],row["kickoff_utc"],row["match_date"]):
   raise ValueError("FORECAST_RESULT_FIXTURE_MISMATCH")
  created=read_aware(f["created_at_utc"])
  ko=read_aware(x["kickoff_utc"])
  checked=read_aware(x["source_checked_at_utc"])
  if not (created<ko and checked<ko and checked<=created+timedelta(seconds=60)):
   raise ValueError("PREMATCH_SEAL_TIME_INVALID")
  if row["official_network_verified"] is not (source=="TFF_NETWORK_VERIFIED"):
   raise ValueError("NETWORK_SOURCE_GRADE_FALSIFIED")
  if row["human_attestation"] is not False:raise ValueError("ATTESTATION_MISMATCH")
  if len(f.get("model_predictions",{}))!=4:raise ValueError("NOT_FOUR_MODELS")
  bymodel={}
  for name in MODELS:
   calculated=score(f["model_predictions"][name],h,a)
   if calculated is not None:bymodel[name]=calculated
  if not bymodel:raise ValueError("NO_MODEL_FOR_MATCH")
  counts[source]+=1
  counts["scored"]+=1
  if len(bymodel)==4:counts["all_four_available"]+=1
  row_out={"sha":seal,"grade":source,"league":row["league"],"bymodel":bymodel}
  good.append(row_out)
  provisional[source].append(row_out)
  signatures[seal]=x["kickoff_utc"]
 if counts["scored"]!=39 or counts["postponed_no_scoring"]!=1:
  raise ValueError("ARCHIVE_COUNTS_MISMATCH")
 if counts["TFF_NETWORK_VERIFIED"]!=3:raise ValueError("NOT_THREE_DIRECT_NETWORK_VERIFICATIONS")
 def evaluate(subset):
  per_model={}
  for model in MODELS:
   v=[r["bymodel"][model] for r in subset if model in r["bymodel"]]
   per_model[model]={
    "n":len(v),"markets":{k:metrics([entry[k] for entry in v]) for k in ("1X2",*MARKETS)}}
  common=[r for r in subset if all(m in r["bymodel"] for m in MODELS)]
  paired={model:{"n":len(common),
    "markets":{k:metrics([r["bymodel"][model][k] for r in common]) for k in ("1X2",*MARKETS)}}
    for model in MODELS}
  return {"match_count":len(subset),"model_own_coverage":per_model,
          "same_all_four_match_coverage":len(common),"four_way_paired":paired}
 return {
  "status":"READONLY_ARCHIVED_NEW100_39_SEALS_RESEARCH_OUTCOMES_NOT_FULLY_OFFICIALLY_VERIFIED",
  "model_or_forecasts_changed":False,
  "retrained":False,
  "future_pilot_created":False,
  "new_training_admissions":0,
  "bookmaker_EV_or_betting_accuracy_claims":False,
  "last_scored_event":"2026-11-08",
  "score_archive_cutoff":"2026-11-12",
  "archive_sha256":hashlib.sha256(ARCH.read_bytes()).hexdigest(),
  "source_grade_counts":dict(counts),
  "all_39_provisional_inference":evaluate(good),
  "direct_network_3_only":evaluate(provisional["TFF_NETWORK_VERIFIED"]),
  "other_36_web_research_only":evaluate([r for r in good if r["grade"]!="TFF_NETWORK_VERIFIED"]),
  "evaluation_limitations":[
   "The non-network 36 results are previously archived web research and NOT newly human-attested or live-network verified",
   "N=39 is small; comparing these metrics does not certify forecasting superiority or expected betting returns",
   "No after-kickoff forecast computed, no model selection or coefficient changes",
   "No claim these 39 are the legacy96 cohort; 40 are independent new100 existing seals",
   "This is score-only analysis, not permission to train on 4218 new research source matches"
  ],
  "no_repeat":"This report is built offline from existing SHA-locked pre-match JSONs and frozen postmatch archive; same old score sites were not re-queried."
 }
def selftest():
 p={"status":"AVAILABLE","goals":{"markets":{
  "1X2":{"H":0.5,"D":0.3,"A":0.2},
  "BTTS_YES":0.5,"OVER_1.5":0.8,"OVER_2.5":0.45,"OVER_3.5":0.2}}}
 s=score(p,2,1)
 assert s["1X2"]["accuracy"]==1 and s["OVER_2.5"]["accuracy"]==0
 assert score({"status":"UNAVAILABLE"},0,0) is None
 print("PASS no re-fit, binary thresholds, 3-way probabilities and missing models")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--run",action="store_true")
 a=p.parse_args()
 if a.self_test:selftest()
 if a.run:
  report=calculate()
  OUT.parent.mkdir(parents=True,exist_ok=True)
  OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
  print(json.dumps({"status":report["status"],
    "scored":report["all_39_provisional_inference"]["match_count"],
    "common":report["all_39_provisional_inference"]["same_all_four_match_coverage"],
    "official_network_only":report["direct_network_3_only"]["match_count"],
    "new_training":0},ensure_ascii=False))
