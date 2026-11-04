"""One-time early (T-2d) REAL named-fixture shadow. Not T-60 or accepted 96.

Downloads pinned batch externally via GitHub Actions, and calls the real TFF
official adapter again. Never pretends the 4509 results were human-verified.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path

from analyze_named_match_gate import run
from forward_quad import predict_quad_from_verified_gate
from weekend_shadow_source_263 import SHA

def main():
 now=datetime.now(timezone.utc)
 gate=run("TUR1","Gaziantep FK","Kasımpaşa")
 if gate.get("status")!="VERIFIED" or gate.get("kickoff_utc")!="2026-11-06T17:00:00+00:00":
  raise SystemExit("NO_EARLY_SHADOW: fresh official TFF source is not verified: "+str(gate.get("reason",gate.get("status"))))
 # Explicit EARLY experiment, not the later T-60 registered 96-cohort:
 target,pred=predict_quad_from_verified_gate(
  gate,"/tmp/weekend_source_4509/extended_history.csv",
  "forward_quad_shadow_263","experiments/263/m4_lock.json",now=now,
  base="/tmp/frozen_4413/historical_results.csv",
  shadow_evidence="/tmp/weekend_source_4509/preflight_report.json")
 if (pred["data"]["snapshot_sha256"]!=SHA or
     pred["data"]["research_shadow_unverified_source"] is not True or
     pred["data"]["human_source_acceptance"] is not False or
     pred["status"]!="EXPERIMENTAL_EARLY_SHADOW_UNVERIFIED_SOURCE_NO_BETTING"):
  raise SystemExit("SHADOW_SOURCE_POLICY_MISLABEL")
 print(json.dumps({"status":pred["status"],"fixture":pred["fixture"],
                    "models":{n:v["status"] for n,v in pred["model_predictions"].items()},
                    "forecast_created_utc":pred["created_at_utc"],
                    "SHA":pred["payload_sha256"],"file":str(target),
                    "not_accepted_96_pilot":True},ensure_ascii=False))

if __name__=="__main__":main()
