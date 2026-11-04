"""One-shot research-only four-model forecast -> empirical baseline -> M4 decision view.

No fitting, no official pilot increment, no odds and no fallback to unverified data.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from forward_empirical_baseline_263 import produce
from forward_baseline_provenance_263 import connect_verified_baseline
from forward_decision_view_263 import render

def integrate(forecast, lock, history_path, *, now=None):
    baseline=produce(forecast,history_path,now=now)
    decision=connect_verified_baseline(forecast,lock,baseline)
    view=render(decision)
    if decision["pilot_count_increment"]!=0 or decision["betting_authorized"] is not False:
        raise ValueError("OFFICIAL_PILOT_MUTATION_FORBIDDEN")
    return baseline,decision,view

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--forecast",required=True)
    ap.add_argument("--history",required=True)
    ap.add_argument("--calibration-lock",default="experiments/263/forward_dev_calibration_lock_263.json")
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()
    f=json.loads(Path(args.forecast).read_text(encoding="utf-8"))
    lock=json.loads(Path(args.calibration_lock).read_text(encoding="utf-8"))
    b,d,v=integrate(f,lock,args.history)
    target=Path(args.output_dir)
    if target.exists():raise SystemExit("NO_OVERWRITE_EXISTING_RESEARCH_OUTPUT")
    target.mkdir(parents=True)
    for name,record in (("baseline.json",b),("decision.json",d)):
        with (target/name).open("x",encoding="utf-8") as handle:
            json.dump(record,handle,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
            handle.write("\n")
    with (target/"decision.md").open("x",encoding="utf-8") as handle:
        handle.write(v)
    print(json.dumps({"status":d["status"],"research_only":True,
        "forecast_sha256":f["payload_sha256"],"baseline_sha256":b["payload_sha256"],
        "calibration_lock_sha256":lock["payload_sha256"],
        "pilot_count_increment":0},sort_keys=True))
if __name__=="__main__":main()
