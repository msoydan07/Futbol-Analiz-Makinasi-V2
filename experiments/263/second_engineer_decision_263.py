"""Independent second-engineer audit of per-outcome DEV calibration.

A separately calibrated MS1, MSX and MS2 may fail the sum-to-one law
for a mutually exclusive 1-X-2 event distribution. Keep raw 1X2 vectors
and individual DEV market indications clearly distinct. NO renormalization
or probabilistic model change and no retroactive sealed decision mutation.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from second_engineer_calibration_263 import collect,hash_payload,EvidenceBlocked,coherent,probability
DAY="2026-11-08"

def analyse(root):
    root=Path(root)
    sealed,results=collect(root)
    counts={"decisions":0,"all_three_dev_ms_observed":0,
            "joint_sum_not_one":0,"no_complete_dev_ms_triple":0,
            "raw_m4_joint_sum_wrong":0,"different_dev_anchor_models":0}
    worst={"distance_to_one":0,"example_path":None,"ms_sum":None,
           "choice_anchor_models":None}
    original_paths={}
    for fname in ("new100_42469245388.json","new100_42469487639.json"):
        batch=json.loads((root/"experiments/263/sabah_batch_reports"/fname).read_text(encoding="utf-8"))
        for row in batch["outcomes"]:
            if row.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
            key=(row["league"],row["home"],row["away"])
            if key in original_paths:raise EvidenceBlocked("DUPLICATE_DECISION_SOURCE_ID")
            original_paths[key]=Path(row["forecast_path"]).stem
    if set(original_paths)!=set(sealed):
        raise EvidenceBlocked("DECISION_ARCHIVE_NOT_EXACTLY_LINKED_TO_REGISTERED_SEALS")
    for key,forecast in sorted(sealed.items()):
        stem=original_paths[key]
        dpath=root/"experiments/263/sabah_research/new100"/DAY/stem/"decision.json"
        d=json.loads(dpath.read_text(encoding="utf-8"))
        if (hash_payload(d)!=d.get("payload_sha256") or
            d.get("forecast_sha256")!=forecast.get("payload_sha256") or
            d.get("betting_authorized") is not False):
            raise EvidenceBlocked("DEV_DECISION_HASH_OR_FORECAST_LINK_INVALID")
        counts["decisions"]+=1
        m4=forecast["model_predictions"].get("M4",{})
        if m4.get("status")=="AVAILABLE":
            coherent(m4["goals"]["markets"])
        diag={x["market"]:x for x in d.get("all_market_diagnostics",[])
              if isinstance(x,dict) and x.get("market") in ("MS1","MSX","MS2")}
        allkeys=("MS1","MSX","MS2")
        if any(k not in diag or diag[k].get("calibrated_probability") is None for k in allkeys):
            counts["no_complete_dev_ms_triple"]+=1
            continue
        q=[probability(diag[k]["calibrated_probability"]) for k in allkeys]
        anchors=[diag[k].get("anchor_model") for k in allkeys]
        counts["all_three_dev_ms_observed"]+=1
        if len(set(anchors))>1:counts["different_dev_anchor_models"]+=1
        distance=abs(sum(q)-1)
        if distance>1e-6:counts["joint_sum_not_one"]+=1
        if distance>worst["distance_to_one"]:
            worst={"distance_to_one":round(distance,6),
                   "example_path":str(dpath.relative_to(root)),
                   "ms_sum":round(sum(q),6),"choice_anchor_models":anchors}
    if counts["decisions"]!=40:
        raise EvidenceBlocked("INCOMPLETE_EXISTING_DECISION_ARCHIVE")
    return {"schema":"263_SECOND_ENGINEER_DEV_MS_PROBABILITY_AUDIT_V1",
            "status":"PER_MARKET_DEV_CALIBRATION_IS_NOT_COHERENT_1X2_VECTOR",
            "counts":counts,
            "largest_inconsistency":worst,
            "risk":"If independent DEV q(MS1),q(MSX),q(MS2) are displayed as a normalized 1X2 distribution, their sum may differ from 1. Their separate binary calibration and price comparison do not create a valid joint multinomial forecast.",
            "remediation":"Preserve original sealed q for individual diagnostic only; phone/PDF label must say 'DEV single-market indicator, not 1X2 distribution'. Keep B/C2/C3/M4 original 1X2 vector separately. Do NOT renormalize, retune, promote or overwrite.",
            "original_40_forecasts_changed":False,"original_40_decisions_changed":False,
            "main_or_M4_changed":False,"source_scores_not_independently_network_verified":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    out=Path(args.out)
    data=analyse(args.root)
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():
        if json.loads(out.read_text(encoding="utf-8"))!=data:
            raise EvidenceBlocked("EXISTING_DEV_MS_AUDIT_DIFFERS_FROM_RECOMPUTED_SEALS")
    else:
        out.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":data["status"],"counts":data["counts"],
                      "largest_inconsistency":data["largest_inconsistency"]},ensure_ascii=False))

if __name__=="__main__":main()
