"""Read-only NEW100 postmatch evaluation; SHA-locked results, no retroactive fitting.

Results are HUMAN-ATTESTED observations of official pages, never called
independently verified until a separate actual source validation exists.
No edit of forecasts, no market/odds requests, and no betting ROI claims.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re
from collections import defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit
from forward_c3 import read_aware
from market_fifth_baseline_263 import sealed_payload
from official_page_lookup_263 import is_approved_url
from evaluate_quad import _metrics,_binary
from sabah_batch_263 import sha

SCHEMA="263_NEW100_HUMAN_OFFICIAL_RESULT_ATTESTATION_V1"
REPORT="263_NEW100_POSTMATCH_RESEARCH_SCORE_V1"
MODELS=("B","C2","C3","M4")
MARKETS=("BTTS","OVER_1.5","OVER_2.5","OVER_3.5")
DIAG={"MS1":"H","MSX":"D","MS2":"A","BTTS_YES":"BTTS",
      "OVER_1.5":"OVER_1.5","OVER_2.5":"OVER_2.5","OVER_3.5":"OVER_3.5"}
TR=ZoneInfo("Europe/Istanbul")
class ScoreBlocked(ValueError):pass

def jsonread(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def ago(dt,now):return (now-dt).total_seconds()
def checked_score(x,now):
    if not isinstance(x,dict) or set(x)!={
      "schema","cohort","forecast_sha256","league","home_id","away_id",
      "kickoff_utc","home_goals","away_goals","final_status",
      "source_url","source_checked_at_utc","reviewed_at_utc","reviewer",
      "verification_scope"}:
        raise ScoreBlocked("RESULT_ATTESTATION_SCHEMA_INVALID")
    if (x["schema"]!=SCHEMA or x["cohort"]!="new100" or
        x["final_status"]!="FULL_TIME_HUMAN_REVIEWED" or
        x["verification_scope"]!="HUMAN_ATTESTED_OFFICIAL_PAGE_NOT_NETWORK_REVERIFIED"):
        raise ScoreBlocked("RESULT_UNVERIFIED_OR_NOT_FULL_TIME")
    if not isinstance(x["forecast_sha256"],str) or not re.fullmatch(r"[a-f0-9]{64}",x["forecast_sha256"]):
        raise ScoreBlocked("FORECAST_SHA_INVALID")
    if not isinstance(x["reviewer"],str) or not 3<=len(x["reviewer"].strip())<=120:
        raise ScoreBlocked("REVIEWER_REQUIRED")
    if any(not isinstance(x[k],int) or isinstance(x[k],bool) or not 0<=x[k]<=20
           for k in ("home_goals","away_goals")):
        raise ScoreBlocked("INVALID_FULL_TIME_SCORE")
    if not isinstance(x["league"],str) or not is_approved_url(x["source_url"],x["league"]):
        raise ScoreBlocked("SOURCE_URL_NOT_OFFICIAL_OR_HTTPS")
    ko=read_aware(x["kickoff_utc"])
    checked=read_aware(x["source_checked_at_utc"])
    reviewed=read_aware(x["reviewed_at_utc"])
    if not (ko+timedelta(minutes=90)<=checked<=reviewed<=now):
        raise ScoreBlocked("SOURCE_EVIDENCE_NOT_AFTER_MATCH_OR_IN_FUTURE")
    return x

def scores_for(f,observation):
    fg=f["fixture"]
    if f.get("schema")!="quad_forward_263_v1":
        raise ScoreBlocked("FORECAST_SCHEMA_WRONG")
    key=("league","home_id","away_id","kickoff_utc")
    if any(fg.get(k)!=observation[k] for k in key):
        raise ScoreBlocked("RESULT_WRONG_FIXTURE_IDENTITY_OR_KICKOFF")
    if f["payload_sha256"]!=observation["forecast_sha256"]:
        raise ScoreBlocked("RESULT_WRONG_SEALED_FORECAST")
    created=read_aware(f["created_at_utc"])
    checked=read_aware(fg["source_checked_at_utc"])
    ko=read_aware(fg["kickoff_utc"])
    # The start-of-request timestamp in real Nov 6/8 SHA seals can precede
    # the gateway's source-check timestamp by seconds. Both MUST remain
    # before kickoff. Accept up to 60 seconds of a live page fetch during the request;
    # never backdate or rewrite the immutable pre-match forecast.
    if not (created<ko and checked<ko and checked<=created+timedelta(seconds=60)):
        raise ScoreBlocked("NOT_AUTHENTIC_PREMATCH_FORECAST")
    if fg.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE":
        raise ScoreBlocked("FIXTURE_NOT_LIVE_OFFICIAL_VERIFIED")
    h,a=observation["home_goals"],observation["away_goals"]
    outcome="H" if h>a else "D" if h==a else "A"
    actual={"BTTS":int(h>0 and a>0),"OVER_1.5":int(h+a>=2),
            "OVER_2.5":int(h+a>=3),"OVER_3.5":int(h+a>=4)}
    out={"forecast_sha256":f["payload_sha256"],"league":fg["league"],
         "kickoff_utc":fg["kickoff_utc"],"score":[h,a],"outcome":outcome,
         "model_scores":{},"market_scores":{},
         "official_source":observation["source_url"],
         "result_evidence_scope":observation["verification_scope"],
         "calibrated_diagnostics":{}}
    for name in MODELS:
        model=f.get("model_predictions",{}).get(name,{})
        if model.get("status")!="AVAILABLE":continue
        markets=model["goals"]["markets"]
        ms=_metrics(markets["1X2"],outcome,("H","D","A"))
        out["model_scores"][name]=ms
        out["market_scores"][name]={
            market:_binary(markets["BTTS_YES"] if market=="BTTS"
                           else markets[market],actual[market])
            for market in MARKETS}
    return out

def bins(part):
    if not part:return []
    out=[]
    for i in range(5):
        group=[r for r in part if i*.2<=r["p"]<(i+1)*.2 or i==4 and i*.2<=r["p"]<=1.]
        if group:
            out.append({"range":[round(i*.2,2),round((i+1)*.2,2)],
                        "n":len(group),"mean_probability":sum(r["p"] for r in group)/len(group),
                        "observed_rate":sum(r["y"] for r in group)/len(group)})
    return out

def binary_summary(part):
    n=len(part)
    return {"n":n,"brier":sum(z["brier"] for z in part)/n if n else None,
            "logloss":sum(z["logloss"] for z in part)/n if n else None,
            "direction_accuracy_pct":100*sum(int((z["p"]>=.5)==bool(z["y"])) for z in part)/n if n else None,
            "calibration_bins":bins(part)}

def ms_summary(part):
    n=len(part)
    return {"n":n,"brier":sum(x["brier"] for x in part)/n if n else None,
            "logloss":sum(x["logloss"] for x in part)/n if n else None,
            "top1_accuracy_pct":100*sum(x["is_correct"] for x in part)/n if n else None}

def decide_diag(d,item):
    if d is None:return
    sealed_payload(d,"263_four_model_value_decision_research_v1")
    if (d.get("forecast_sha256")!=item["forecast_sha256"] or
        d.get("status")!="RESEARCH_PAS" or d.get("betting_authorized") is not False):
        raise ScoreBlocked("DECISION_NOT_LINKED_OR_NOT_PAS")
    outcome=item["outcome"]
    actual={**{m:int(outcome==letter) for m,letter in (("MS1","H"),("MSX","D"),("MS2","A"))},
            **{k:int(item["score"][0]>0 and item["score"][1]>0) if k=="BTTS_YES"
               else int(sum(item["score"])>=int(k.split("_")[1].split(".")[0])+1)
               for k in ("BTTS_YES","OVER_1.5","OVER_2.5","OVER_3.5")}}
    for row in d.get("all_market_diagnostics",[]):
        key=row.get("market")
        if key not in DIAG:continue
        prob=row.get("calibrated_probability")
        if (prob is None or row.get("anchor_model") not in ("C3","M4") or
            not isinstance(prob,(float,int)) or isinstance(prob,bool) or
            not math.isfinite(prob) or not 0<=prob<=1 or
            not isinstance(row.get("dev_brier_skill"),(float,int)) or
            row["dev_brier_skill"]<=0 or row.get("support_count",0)<3):
            continue
        item["calibrated_diagnostics"][key]=_binary(prob,actual[key])

def evaluate(root=".",*,evidence_dir="experiments/263/sabah_postmatch_inputs",now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ScoreBlocked("AWARE_CLOCK_REQUIRED")
    now=now.astimezone(timezone.utc)
    root=Path(root);forecast_root=root/"forward_morning_263"
    files=sorted(forecast_root.glob("*/*.json"))
    if len(files)>100:raise ScoreBlocked("NEW100_CAP_EXCEEDED")
    sealed_forecasts={}
    for path in files:
        f=jsonread(path)
        sealed_payload(f,"quad_forward_263_v1")
        x=f["fixture"]
        if not re.fullmatch(r"[a-f0-9]{24}",path.stem):
            raise ScoreBlocked("FORECAST_FILENAME_NOT_LOCKED")
        if x["match_local_date"]!=path.parent.name:
            raise ScoreBlocked("FORECAST_LOCAL_DATE_NOT_PATH")
        if f["payload_sha256"] in sealed_forecasts:
            raise ScoreBlocked("DUPLICATE_REGISTERED_FORECAST_SHA")
        sealed_forecasts[f["payload_sha256"]]=(f,path)
    observed={}
    for path in sorted((root/evidence_dir).glob("*/*.json")):
        result=checked_score(jsonread(path),now)
        key=result["forecast_sha256"]
        if key in observed:raise ScoreBlocked("DUPLICATE_OR_CONFLICTING_OFFICIAL_ATTESTATION")
        if key not in sealed_forecasts:
            raise ScoreBlocked("UNREGISTERED_OR_OTHER_COHORT_RESULT_REFUSED")
        observed[key]=result
    completed=[];pending=[]
    for key,(forecast,fp) in sealed_forecasts.items():
        fixture=forecast["fixture"];ko=read_aware(fixture["kickoff_utc"])
        if key not in observed:
            pending.append({"forecast_sha256":key,"league":fixture["league"],
                            "kickoff_utc":fixture["kickoff_utc"],
                            "status":"PENDING_OFFICIAL_POSTMATCH_ATTESTATION" if ko<now
                                     else "MATCH_NOT_FINISHED_YET"})
            continue
        if now<ko:raise ScoreBlocked("CANNOT_SCORE_PREKICKOFF")
        row=scores_for(forecast,observed[key])
        side=root/"experiments/263/sabah_research/new100"/fixture["match_local_date"]/fp.stem/"decision.json"
        if side.exists():decide_diag(jsonread(side),row)
        completed.append(row)
    models={};markets={};calibrated={}
    for model in MODELS:
        model_rows=[r["model_scores"][model] for r in completed if model in r["model_scores"]]
        models[model]=ms_summary(model_rows)
        markets[model]={key:binary_summary([r["market_scores"][model][key] for r in completed
                                             if model in r["market_scores"]])
                        for key in MARKETS}
    common=[x for x in completed if all(k in x["model_scores"] for k in MODELS)]
    paired={}
    for base in ("B","C2","C3"):
        shared=[x for x in completed if base in x["model_scores"] and "M4" in x["model_scores"]]
        paired[base+"_minus_M4"]={
            "n":len(shared),
            "brier_positive_means_M4_better":
                sum(x["model_scores"][base]["brier"]-x["model_scores"]["M4"]["brier"]
                    for x in shared)/len(shared) if shared else None,
            "no_confidence_interval_until_10_distinct_days":True}
    for k in DIAG:
        calibrated[k]=binary_summary([r["calibrated_diagnostics"][k] for r in completed
                                        if k in r["calibrated_diagnostics"]])
    report={"schema":REPORT,"generated_at_utc":now.isoformat(),
            "cohort":"new100","registered":len(files),
            "human_attested_official_result_count":len(completed),
            "independently_network_verified_result_count":0,
            "pending":pending,"outcomes":completed,
            "per_model_MS":models,"per_model_KG_and_goal_lines":markets,
            "calibrated_DEV_diagnostics":calibrated,
            "four_model_common_n":len(common),
            "same_match_M4_comparisons":paired,
            "result_provenance":"HUMAN_ATTESTED_OFFICIAL_PAGE_NOT_NETWORK_REVERIFIED",
            "model_fitting_or_parameters_changed":False,
            "forecasts_modified":False,"betting_success_claimed":False,
            "evaluation_status":"DESCRIPTIVE_RESEARCH_ONLY_NO_MODEL_PROMOTION",
            "limitations":[
                "Attestation is not independent network verification of final score",
                "Only previously SHA-locked new100 forecast files are scored",
                "Brier and correct direction are descriptive, not guaranteed prediction accuracy",
                "Model n can differ; paired M4 comparison uses identical fixtures",
                "Calibrated DEV market probabilities are scored only when supported",
                "No confidence interval or model superiority from tiny samples",
                "No 96-match or acceptance3 tests are added to new100"]}
    report["payload_sha256"]=sha(report)
    return report

def mobile(report):
    lines=["# 2.6.3 — Yeni 100 pilotu maç sonu karnesi","",
           "**Mühürlü tahmin:** "+str(report["registered"])+"/100",
           "**Maç sonrası insan teyitli resmî sayfa sonucu:** "+
               str(report["human_attested_official_result_count"]),
           "**Bağımsız ağ doğrulaması:** 0 — henüz yapılmadı","",
           "Bunlar yalnız araştırma değerlendirmeleridir; bahis başarısı veya model üstünlüğü ilan edilmez.","",
           "| Model | MS örnek | MS isabet | MS Brier | KG örnek | KG yön isabet |",
           "|---|---:|---:|---:|---:|---:|"]
    for model in MODELS:
        ms=report["per_model_MS"][model]
        kg=report["per_model_KG_and_goal_lines"][model]["BTTS"]
        fmt=lambda p:"—" if p is None else ("%.1f%%"%p).replace(".",",")
        brier="—" if ms["brier"] is None else ("%.4f"%ms["brier"]).replace(".",",")
        lines.append("| "+model+" | "+str(ms["n"])+" | "+fmt(ms["top1_accuracy_pct"])+" | "+
                     brier+" | "+str(kg["n"])+" | "+fmt(kg["direction_accuracy_pct"])+" |")
    lines+=["","**Üst/Alt kalibrasyon ve Brier:**"]
    for model in MODELS:
        for line in ("OVER_1.5","OVER_2.5","OVER_3.5"):
            d=report["per_model_KG_and_goal_lines"][model][line]
            b="—" if d["brier"] is None else ("%.4f"%d["brier"]).replace(".",",")
            lines.append("- "+model+" "+line+": N="+str(d["n"])+", Brier="+b)
    lines+=["","**Ortak dört-modelli maç sayısı:** "+str(report["four_model_common_n"]),
            "**Bekleyen veya doğrulanmamış:** "+str(len(report["pending"])),"",
            "Kaynak sınıfı: insan tarafından resmî sayfadan aktarılmış; ağ üzerinden bağımsız doğrulanmadı."]
    return "\n".join(lines)+"\n"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence-dir",default="experiments/263/sabah_postmatch_inputs")
    p.add_argument("--out",required=True)
    p.add_argument("--mobile",required=True)
    args=p.parse_args()
    report=evaluate(evidence_dir=args.evidence_dir)
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")
    m=Path(args.mobile);m.parent.mkdir(parents=True,exist_ok=True);m.write_text(mobile(report),encoding="utf-8")
    print(json.dumps({"registered":report["registered"],"human_attested_results":
                      report["human_attested_official_result_count"],
                      "independent_verified":0,"pending":len(report["pending"]),
                      "models_unchanged":True},ensure_ascii=False))
if __name__=="__main__":main()
