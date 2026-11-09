"""Audit actual repository-visible sealed 2.6.3 forecasts vs result attestations.

The user's mentioned 95 predictions is a hypothesis to verify, not a
substitute for files. Work only from actual immutable seal payloads,
never merge duplicates or assign unmatched real-world scores by names.
This script is read-only and creates a diagnostic JSON artifact.
"""
from __future__ import annotations
import argparse,json,hashlib
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),
        ensure_ascii=False,allow_nan=False).encode("utf8")).hexdigest()

def analyze(root):
    root=Path(root)
    seals=sorted((root/"forward_morning_263").glob("*/*.json"))
    older=sorted((root/"forward_quad_263").glob("*/*.json"))
    attestations=sorted((root/"experiments/263/sabah_postmatch_inputs").rglob("*.json"))
    sha_index={};valid=[];rejections=[]
    for filename in seals+older:
        try:
            obj=json.loads(filename.read_text(encoding="utf8"))
            sha=obj.get("payload_sha256")
            if (obj.get("schema")!="quad_forward_263_v1" or
                sha!=digest({k:v for k,v in obj.items() if k!="payload_sha256"})):
                raise ValueError("not an intact quad seal")
            fx=obj["fixture"];created=datetime.fromisoformat(obj["created_at_utc"].replace("Z","+00:00"))
            kickoff=datetime.fromisoformat(fx["kickoff_utc"].replace("Z","+00:00"))
            if created.tzinfo is None or kickoff.tzinfo is None or not created<kickoff:
                raise ValueError("not an authenticated pre-kickoff time")
            if sha in sha_index:raise ValueError("duplicate seal hash")
            sha_index[sha]=obj
            valid.append({"relative_path":str(filename.relative_to(root)),
                          "sha":sha,"league":fx["league"],"date":fx["kickoff_utc"][:10],
                          "m4":obj.get("model_predictions",{}).get("M4",{}).get("status")})
        except Exception as exc:
            rejections.append({"path":str(filename.relative_to(root)),
                               "reason":str(exc)[:160]})
    matched=0;ambiguous=[]
    for name in attestations:
        try:
            obj=json.loads(name.read_text(encoding="utf8"))
            s=obj["forecast_sha256"]
            if s not in sha_index:raise ValueError("result without sealed forecast")
            fx=sha_index[s]["fixture"]
            if any(fx.get(k)!=obj.get(k) for k in ("league","home_id","away_id","kickoff_utc")):
                raise ValueError("result identity inconsistent")
            if obj.get("final_status")!="FULL_TIME_HUMAN_REVIEWED":
                raise ValueError("result not accepted")
            matched+=1
        except Exception as exc:
            ambiguous.append({"path":str(name.relative_to(root)),"reason":str(exc)[:150]})
    byday=Counter(x["date"] for x in valid)
    return {"schema":"MC_263_WEEKEND_FORWARD_COVERAGE_AUDIT_V1",
      "repository_visible_seal_files":len(seals)+len(older),
      "intact_pre_kickoff_seals":len(valid),
      "invalid_seals":rejections,
      "seals_by_kickoff_utc_day":dict(sorted(byday.items())),
      "m4_available":sum(x["m4"]=="AVAILABLE" for x in valid),
      "result_attestation_files":len(attestations),
      "matched_result_candidate_count":matched,
      "result_issues":ambiguous,
      "claimed_95_independently_confirmed":len(valid)>=95 and matched>=95,
      "missing_records_are_not_generated":True,
      "source_scope":"CURRENT_CHECKED_OUT_RESEARCH_BRANCH_ONLY",
      "live_brier_scored":False,
      "results_must_pass_existing_263_official_evidence_gate":True,
      "promotion_to_263":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    data=analyze(args.root)
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
