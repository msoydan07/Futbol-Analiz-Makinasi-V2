"""Read-only reliability note from an existing chronological calibration report.

Does not alter probabilities or declare any bet valuable.
"""
import json
from pathlib import Path

def assess(model,report_path="data/model_b_calibration_audit.json"):
 try:
  report=json.loads(Path(report_path).read_text(encoding="utf-8"))
  probs=model["markets"]["1x2"]
  peak=max(probs.values())
  if not (0<=peak<=1):raise ValueError("Invalid probability")
  idx=min(9,int(peak*10))
  bucket=report["top_choice"][idx]
  n=int(bucket["n"])
  observed=bucket["observed"]
  predicted=bucket["predicted"]
  if n<100:
   level="LIMITED_EVIDENCE"
   message="Few historical examples at this probability level; do not claim high confidence."
  elif predicted is not None and observed is not None and observed+0.03<predicted:
   level="OVERCONFIDENCE_WARNING"
   message="Historical outcomes in this bin were below predicted probabilities."
  else:
   level="DESCRIPTIVE_ONLY"
   message="Historical bin is descriptive; it does not guarantee this match outcome."
  return {"status":"AVAILABLE","level":level,"sample_size":n,"bin":bucket["range"],
          "mean_predicted":predicted,"observed_frequency":observed,
          "message":message,"probabilities_changed":False,
          "source":"model_b_calibration_audit.json",
          "scope":"1X2 highest-probability pick only; not goals, BTTS or corners"}
 except (OSError,KeyError,ValueError,TypeError,IndexError) as exc:
  return {"status":"UNAVAILABLE","reason":str(exc)[:160],
          "probabilities_changed":False,"message":"No verified calibration report; no confidence claim."}
