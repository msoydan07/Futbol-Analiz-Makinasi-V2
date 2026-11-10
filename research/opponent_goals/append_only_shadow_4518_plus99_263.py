"""Construct a STRICT research-only append-only SHADOW of 4518 + 99.

This is NOT production accepted history; no raw provider CSV committed.
The nine older manual ENG2 score-only rows are preserved byte/fieldwise,
and sources/HT/shot stat backfills go into a SEPARATE review task.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json
from collections import Counter,defaultdict
from pathlib import Path
from urllib.parse import urlsplit
from staged_candidate_99_joint_audit import (
    load_csv,ACCEPTED_SHA,STAGED_SHA,key,evidence_99,
    validate_source_identity,AuditStop,enforce
)

def make(root,staged_file,shadow_file=None):
    root=Path(root)
    accepted=load_csv(root/"data/quad_accepted_263/extended_history.csv",ACCEPTED_SHA)
    staged=load_csv(staged_file,STAGED_SHA)
    accepted_id={r["fixture_id"]:r for r in accepted}
    staged_id={r["fixture_id"]:r for r in staged}
    enforce(len(accepted)==4518 and len(staged)==4617,"SOURCE_COUNTS_CHANGED")
    enforce(set(accepted_id)<=set(staged_id),"ACCEPTED_RECORD_REMOVED_FROM_STAGE")
    published=evidence_99(root)
    newer=[r for r in staged if r["fixture_id"] not in accepted_id]
    enforce(len(newer)==99,"CANDIDATE_COUNT_UNEXPECTED")
    newkeys={key(r) for r in newer}
    enforce(len(newkeys)==99 and newkeys==set(published),"CANDIDATE_IDENTITY_LEDGER_MISMATCH")
    for r in newer:
        validate_source_identity(r)
        pub=published[key(r)]
        enforce((int(r["home_goals"]),int(r["away_goals"]))==
                (pub["home_goals"],pub["away_goals"]),"PUBLIC_SOURCE_SCORE_DISAGREES")
    # Do not use staged versions of previous 4518. No per-field enrichment
    # is permissible until separately verified.
    old_changed=[(accepted_id[k],staged_id[k]) for k in accepted_id
                 if accepted_id[k]!=staged_id[k]]
    enforce(len(old_changed)==9,"ORIGINAL_DIFF_COUNT_UNEXPECTED")
    old_source=Counter(urlsplit(a["source_url"]).hostname or "NONE" for a,b in old_changed)
    new_source=Counter(urlsplit(b["source_url"]).hostname or "NONE" for a,b in old_changed)
    old_fields=Counter();new_fields=Counter()
    inspection=("half_time_home_goals","half_time_away_goals","home_shots","away_shots",
                "home_shots_on_target","away_shots_on_target","home_corners","away_corners",
                "home_yellow_cards","away_yellow_cards")
    for old,stage in old_changed:
        for f in inspection:
            old_fields[f]+=old.get(f,"")!=""
            new_fields[f]+=stage.get(f,"")!=""
    allrows=accepted+sorted(newer,key=lambda r:(r["match_date"],r["league"],r["fixture_id"]))
    enforce(len(allrows)==4617 and len({r["fixture_id"] for r in allrows})==4617,
            "SHADOW_APPEND_ONLY_KEY_COLLISION")
    enforce(all(allrows[i]==accepted[i] for i in range(len(accepted))),
            "OLD_4518_ROWS_NOT_BITWISE_EQUIVALENT_IN_LOGIC")
    fieldnames=list(accepted[0])
    out=io.StringIO(newline="")
    writer=csv.DictWriter(out,fieldnames=fieldnames,lineterminator="\n")
    writer.writeheader()
    for row in allrows:
        enforce(set(row)==set(fieldnames),"STAGED_NEW_ROW_SCHEMA_DIFFERS")
        writer.writerow({f:row[f] for f in fieldnames})
    bytes_=out.getvalue().encode("utf8")
    # Cross-check reparsing exact old dictionaries and new row data
    parsed=list(csv.DictReader(io.StringIO(bytes_.decode("utf8"))))
    enforce(parsed[:4518]==accepted,"SERIALIZATION_ALTERED_ACCEPTED_ROWS")
    enforce({key(r) for r in parsed[4518:]}==newkeys,"SERIALIZATION_ALTERED_NEW_CANDIDATES")
    if shadow_file:
        target=Path(shadow_file)
        target.write_bytes(bytes_)
    return {
      "schema":"263_SAFE_APPEND_ONLY_4518_PLUS_99_SHADOW_RESEARCH_V1",
      "status":"SHADOW_STAGED_WITH_ORIGINAL_4518_UNCHANGED_NOT_ACCEPTED",
      "snapshot_base_sha256":ACCEPTED_SHA,
      "observed_tuesday_stage_sha256":STAGED_SHA,
      "candidate_rows":99,
      "original_accepted_rows_unchanged":4518,
      "shadow_rows":4617,
      "research_shadow_serialized_sha256":hashlib.sha256(bytes_).hexdigest(),
      "shadow_written_outside_git":bool(shadow_file),
      "original_old_nine_records_not_overwritten":len(old_changed),
      "nine_old_changed_rows_league_counts":dict(Counter(x["league"] for x,y in old_changed)),
      "nine_old_source_hosts":dict(old_source),
      "nine_stage_source_hosts":dict(new_source),
      "old_nine_nonempty_fields_before":dict(old_fields),
      "old_nine_nonempty_fields_in_candidate_stage_NOT_ADOPTED":dict(new_fields),
      "candidate_99_scores_match_public_score_ledgers":True,
      "new_99_provider_source_independently_verified":False,
      "per_fixture_federation_id_verified":False,
      "usage_rights_verified":False,
      "train_or_calibrate_M4_with_shadow":False,
      "accepted_history_altered":False,
      "existing_seals_or_calibration_altered":False,
      "next_gate":"Independent official fixture-ID and rights check; separately review 9 ENG2 old-row half-time/shot/source changes without overwriting immutable old records.",
      "limitations":[
        "The reconstructed shadow is NOT uploaded to GitHub or production as an accepted dataset",
        "99 newly staged source rows came from existing unverified Tuesday regenerated provider CSV",
        "League/date/teams/score concordance with a web public score ledger is not federation game-ID attestation",
        "9 previously accepted ENG2 scores originally had non-provider research provenance, so silent staged stats additions are held",
        "Old 4518 row dictionaries are exactly preserved but CSV overall has a NEW SHA because it includes 99 extra rows",
        "No live provider access or source redistribution; no new independent blind performance evidence",
      ]}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--root",default=".")
    a.add_argument("--staged",required=True)
    a.add_argument("--shadow",required=True)
    a.add_argument("--out",required=True)
    args=a.parse_args()
    obj=make(args.root,args.staged,args.shadow)
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        enforce(json.loads(path.read_text(encoding="utf8"))==obj,
                "APPEND_ONLY_SHADOW_MANIFEST_EXISTS_AND_DIFFERS")
    else:path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({"status":obj["status"],"candidate_rows":obj["candidate_rows"],
      "base_preserved":obj["original_accepted_rows_unchanged"],
      "nine_old_changes_left_untouched":obj["original_old_nine_records_not_overwritten"],
      "oldSourceHosts":obj["nine_old_source_hosts"],
      "stageSourceHosts":obj["nine_stage_source_hosts"],
      "oldMissingStats":obj["old_nine_nonempty_fields_before"],
      "stagedStatsHeld":obj["old_nine_nonempty_fields_in_candidate_stage_NOT_ADOPTED"]},ensure_ascii=False))
if __name__=="__main__":main()
