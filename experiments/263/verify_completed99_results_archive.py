"""Safe results-only archive integrity gate (not a model recalibration).

The 99 completed scores are permanently recorded as simple factual outcomes in
 data/quad_accepted_263/completed_99_results_only_20261110.json.

Reconstruction uses the old 4518 ORIGINAL accepted rows and copies only
 fixture identity fields from 99 new staged rows. No new shot/corner/card or
 provider CSV statistics are admitted, and old nine ENG2 records are not edited.
All candidate results must also equal independent public scoreboard ledgers.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[2]
ARCHIVE="data/quad_accepted_263/completed_99_results_only_20261110.json"
ACCEPTED="data/quad_accepted_263/extended_history.csv"
STAGED="data/staged_263/extended_history.csv"
ACCEPTED_SHA="1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9"
STAGED_SHA="7f005d88465fa742354854a0459f06fbb17efe9fbb648e26a18844d0f7753958"
CODES=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
GRADES=("OFFICIAL_PAGE_AND_PROVIDER_RESEARCH_CONCORDANT",
        "DIRECT_LEAGUE_OR_CLUB_SCORE_PAGE",
        "PUBLIC_SECONDARY_SCORE_WITH_PARTIAL_OFFICIAL_FIXTURE")
IDENTITY=("fixture_id","league","season","match_date","home_id","away_id",
          "home_goals","away_goals","result","source_url")
class Rejected(ValueError):
    pass

def require(condition,reason):
    if not condition:raise Rejected(reason)

def match_key(r):
    return (r["league"],r["match_date"],r["home_id"],r["away_id"])

def load_csv(root,path,expected_sha):
    raw=(root/path).read_bytes()
    require(hashlib.sha256(raw).hexdigest()==expected_sha,"ORIGINAL_INPUT_SHA_NOT_MATCH")
    dr=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    require(set(IDENTITY).issubset(set(dr.fieldnames or [])),"INPUT_SCHEMA_CHANGED")
    fields=list(dr.fieldnames)
    records=list(dr)
    require(all(set(x)==set(fields) and None not in x for x in records),"MALFORMED_CSV")
    return fields,records

def load_archive(root):
    return json.loads((root/ARCHIVE).read_text(encoding="utf-8"))

def build(root=ROOT, *, archive_override=None, output_csv=None):
    root=Path(root)
    a=archive_override if archive_override is not None else load_archive(root)
    require(a.get("schema")=="263_RESULTS_ONLY_APPEND_ARCHIVE_V1","ARCHIVE_SCHEMA")
    require(a.get("base_accepted_history_sha256")==ACCEPTED_SHA,"ARCHIVE_BASE_HASH_CHANGED")
    require(a.get("new_completed_result_count")==99 and a.get("logical_total_results_after_append")==4617,
            "ARCHIVE_COUNT_METADATA_CHANGED")
    require(a.get("record_policy",{}).get("promoted_into_M4_training") is False,"MODEL_PROMOTION_NOT_AUTHORIZED")
    require(a.get("record_policy",{}).get("official_fixture_id_independently_attested") is False,
            "MISLEADING_OFFICIAL_ID_ATTESTATION")
    entries=a.get("records",[])
    require(isinstance(entries,list) and len(entries)==99,"ARCHIVE_99_REQUIRED")
    fieldnames,original=load_csv(root,ACCEPTED,ACCEPTED_SHA)
    sf,stage=load_csv(root,STAGED,STAGED_SHA)
    require(fieldnames==sf,"STAGE_SCHEMA_NOT_SAME")
    require(len(original)==4518 and len(stage)==4617,"INPUT_HISTORY_COUNTS_CHANGED")
    old_id={r["fixture_id"]:r for r in original}
    stage_id={r["fixture_id"]:r for r in stage}
    require(len(old_id)==4518 and len(stage_id)==4617,"DUPLICATE_INTERNAL_FIXTURE_ID")
    require(set(old_id)<=set(stage_id),"OLD_FIXTURE_REMOVED_FROM_STAGE")
    changed_old=[i for i in old_id if old_id[i]!=stage_id[i]]
    require(len(changed_old)==9 and all(old_id[i]["league"]=="ENG2" for i in changed_old),
            "OLD_STATS_CHANGE_UNEXPECTED_NEVER_OVERWRITE")
    old_keys={match_key(r) for r in original}
    require(len(old_keys)==4518,"DUPLICATE_ORIGINAL_NATURAL_KEY")
    newer={match_key(r):r for r in stage if r["fixture_id"] not in old_id}
    require(len(newer)==99 and len({r["fixture_id"] for r in newer.values()})==99,
            "STAGED_NEW_NATURAL_KEY_DUPLICATE")
    require(not (set(newer)&old_keys),"NEW_ALREADY_IN_ORIGINAL_ARCHIVE")
    entries_by_key={}
    tier=Counter()
    for row in entries:
        key=match_key(row)
        require(key not in entries_by_key,"DUPLICATE_RESULT_ENTRY")
        entries_by_key[key]=row
        require(row.get("league") in CODES and row.get("season")=="2026-2027",
                "BAD_LEAGUE_OR_SEASON")
        require(re.fullmatch(r"2026-11-0[4-9]",row["match_date"]) is not None,
                "INVALID_MATCH_DATE")
        require(all(re.fullmatch(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}",row[f]) for f in ("home_id","away_id")),
                "UNRESOLVED_TEAM_ID")
        h,g=row.get("home_goals"),row.get("away_goals")
        require(type(h) is int and type(g) is int and 0<=h<=20 and 0<=g<=20,
                "INVALID_FINISHED_SCORE")
        require(row.get("result")==("H" if h>g else "A" if h<g else "D"),
                "RESULT_INCONSISTENT")
        u=urlsplit(row.get("score_source_url",""))
        require(u.scheme=="https" and u.hostname and u.path and not u.username and not u.password,
                "NO_GROUNDED_PUBLIC_SOURCE")
        require(row.get("source_class") in GRADES,"UNKNOWN_PROVENANCE_GRADE")
        require(row.get("status")=="COMPLETED_PUBLIC_SCORE_RESEARCH_CONCORDANT",
                "UNACCEPTED_RESEARCH_SCORE_STATUS")
        tier[row["source_class"]]+=1
    require(tier==Counter(dict(zip(GRADES,(28,28,43)))),"PROVENANCE_TIERS_CHANGED")
    require(set(entries_by_key)==set(newer),"STAGE_99_NOT_EXACTLY_ARCHIVED")
    sanitized=[]
    for k in sorted(newer):
        stage_row=newer[k];outcome=entries_by_key[k]
        for f in ("home_goals","away_goals","result"):
            require(str(outcome[f])==stage_row[f],"CANDIDATE_SCORE_VS_ARCHIVE_CONFLICT")
        clean=dict.fromkeys(fieldnames,"")
        for f in ("fixture_id","league","season","match_date","home_id","away_id"):
            clean[f]=stage_row[f]
        for f in ("home_goals","away_goals","result"):
            clean[f]=str(outcome[f])
        clean["source_url"]=outcome["score_source_url"]
        sanitized.append(clean)
    # The original 4518 dictionaries stay bytewise untouched on disk and
    # field-identical in the *separate* generated, results-only snapshot.
    result_rows=original+sanitized
    require(len(result_rows)==4617 and all(result_rows[i]==original[i] for i in range(4518)),
            "OLD_4518_DATA_MUTATED")
    require(all(not row[f] for row in sanitized for f in fieldnames if f not in IDENTITY),
            "UNVERIFIED_ADVANCED_STATS_COPIED")
    buf=io.StringIO(newline="")
    wr=csv.DictWriter(buf,fieldnames=fieldnames,lineterminator="\n")
    wr.writeheader();wr.writerows(result_rows)
    payload=buf.getvalue().encode("utf-8")
    reread=list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    require(reread[:4518]==original and len(reread)==4617,
            "RESULT_SNAPSHOT_SERIALIZATION_ALTERED_ORIGINAL")
    if output_csv is not None:
        p=Path(output_csv);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
    return {
        "schema":"263_RESULTS_ARCHIVE_99_SAFE_REBUILD_ACCEPTANCE_V1",
        "status":"99_COMPLETED_SCORES_PERMANENTLY_ARCHIVED_RESULTS_ONLY",
        "new_result_records":99,"preexisting_accepted_records_preserved":4518,
        "logical_total_result_records":4617,"old_ENG2_changed_stage_rows_ignored":9,
        "new_99_identity_and_scores_match_stage":True,
        "score_source_distribution":dict(tier),
        "original_4518_sha256":ACCEPTED_SHA,
        "results_only_4617_snapshot_sha256":hashlib.sha256(payload).hexdigest(),
        "new_99_advanced_fields_admitted":0,
        "base_accepted_csv_modified":False,
        "production_M4_modified_or_retrained":False,
        "official_per_match_ids_verified":False,
        "archive_is_permanent_in_github":True,
        "candidate_stage_full_statistics_accepted":False,
        "limitations":["99 scores are public research-concordant facts, not official single-fixture-ID attestations",
                       "Core 4518 production CSV and model lock remain original; generated 4617 results-only snapshot is separate",
                       "No provider-owned full CSV or new advanced stats are copied into the permanent results archive"],
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="")
    x=parser.parse_args()
    result=build(output_csv=x.out or None)
    print(json.dumps(result,ensure_ascii=False,indent=2))
