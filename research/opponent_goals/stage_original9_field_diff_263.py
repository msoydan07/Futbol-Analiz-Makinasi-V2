"""Explain exactly why Tuesday's staged 4617 cannot overwrite accepted 4518.

Metadata-only diff of NINE old records, SHA-pinned against existing GitHub
experiment stage; old accepted rows are immutable. No third-party downloads.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from collections import Counter
from staged_candidate_99_joint_audit import (
    load_csv,ACCEPTED_SHA,STAGED_SHA,AuditStop,enforce,key,evidence_99,
)

CRITICAL={"fixture_id","league","season","match_date","home_id",
          "away_id","home_goals","away_goals","result",
          "source_row","source_url"}
def compute(root,staged_path):
    root=Path(root)
    a=load_csv(root/"data/quad_accepted_263/extended_history.csv",ACCEPTED_SHA)
    b=load_csv(staged_path,STAGED_SHA)
    amap={r["fixture_id"]:r for r in a}
    bmap={r["fixture_id"]:r for r in b}
    differences=[];column_counts=Counter();critical_count=0
    for fixture_id in sorted(set(amap)&set(bmap)):
        old,new=amap[fixture_id],bmap[fixture_id]
        modified=sorted(c for c in set(old)|set(new) if old.get(c)!=new.get(c))
        if not modified:continue
        if any(c in CRITICAL for c in modified):critical_count+=1
        for c in modified:column_counts[c]+=1
        differences.append({
          "old_fixture_id_sha256":hashlib.sha256(fixture_id.encode("utf8")).hexdigest(),
          "league":old.get("league"),
          "changed_fields":modified,
          "structural_or_source_critical_change":any(c in CRITICAL for c in modified),
          "old_row_is_preserved_in_accepted_4518":True})
    ensure_staged_99={key(r) for rid,r in bmap.items() if rid not in amap}
    evidence=evidence_99(root)
    enforce(len(differences)==9,"STAGE_OLD_CHANGE_COUNT_NOT_NINE")
    enforce(len(ensure_staged_99)==99 and ensure_staged_99==set(evidence),
            "THE_99_PUBLIC_RESEARCH_KEYS_NOT_THE_99_STAGED_NEW")
    return {"schema":"263_ORIGINAL_NINE_STAGED_DIFF_DIAGNOSIS_V1",
        "status":"REJECT_STAGED_OVERWRITE_REQUIRE_APPEND_ONLY_AND_PROVENANCE_GATE",
        "accepted_source_sha256":ACCEPTED_SHA,"candidate_stage_sha256":STAGED_SHA,
        "modified_preexisting_rows":len(differences),
        "critical_source_or_score_change_rows":critical_count,
        "changed_field_counts":dict(sorted(column_counts.items())),
        "modified_old_row_metadata":differences,
        "99_new_unique_source_dates_teams_scores_match_public":True,
        "source_independently_verified":False,
        "any_production_change":False,
        "safe_next_action":"Prepare isolated shadow view preserving every accepted original row verbatim; append ONLY 99 candidate rows with a separate provisional evidence manifest, do not activate for training.",
        "underlying_approved_csv_modified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--staged",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    d=compute(args.root,args.staged)
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if json.loads(target.read_text(encoding="utf8"))!=d:
            raise AuditStop("APPEND_ONLY_DIAGNOSTIC_REPORT_DIFFERS")
    else:target.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({"changed_original_rows":d["modified_preexisting_rows"],
        "critical_source_or_score":d["critical_source_or_score_change_rows"],
        "by_column":d["changed_field_counts"]},ensure_ascii=False))
if __name__=="__main__":main()
