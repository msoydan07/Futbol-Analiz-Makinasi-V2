"""M4 stage-five read-only xG source-vintage evidence gate. Does NOT run any model.
Use audited xG ZIP and precomputed shared C3/M4 match coverage. Exports aggregates only.
A vintage cannot be certified from column presence alone: a historical snapshot and
source rights must be independently established before any production xG usage.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

XG_COLUMNS={"fixture_id","league","season","match_date","home_id","away_id",
            "home_xg","away_xg","understat_source_url"}
COHORT_COLUMNS={"fixture_id","league","date","both_5_venue"}
ASOF_COLUMNS={"published_at","retrieved_at","model_version","source_value_version"}

def audit(archive:Path,cohort:Path,artifact_created_at:str,out:Path)->dict:
    timestamp=datetime.fromisoformat(artifact_created_at.replace("Z","+00:00"))
    if timestamp.tzinfo is None:raise ValueError("Timestamp must include timezone")
    with zipfile.ZipFile(archive) as z:
        payload=z.read("historical_verified_xg.csv")
        report=json.loads(z.read("historical_verified_xg_report.json"))
    reader=csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    fields=set(reader.fieldnames or ())
    if not XG_COLUMNS.issubset(fields):raise ValueError("missing xG schema")
    xg=list(reader)
    if len(xg)!=report.get("verified_xg_rows") or report.get("prediction_engine_modified") is not False:
        raise ValueError("xG audit mismatch")
    if len({r["fixture_id"] for r in xg})!=len(xg):
        raise ValueError("duplicate xG fixture")
    with cohort.open(encoding="utf-8-sig",newline="") as fh:
        rdr=csv.DictReader(fh)
        if not COHORT_COLUMNS.issubset(rdr.fieldnames or []):
            raise ValueError("missing cohort schema")
        rows=list(rdr)
    if len({r["fixture_id"] for r in rows})!=len(rows):
        raise ValueError("duplicate cohort fixture")
    selected=[r for r in rows if r["both_5_venue"].lower() in ("true","1")]
    if not selected:raise ValueError("no eligible research candidates")
    absent=sorted(ASOF_COLUMNS-fields)
    outcome={
        "status":"ASOF_NOT_CERTIFIED_FOR_STRICT_HISTORICAL_BACKTEST",
        "xg_rows":len(xg),
        "xg_csv_sha256":hashlib.sha256(payload).hexdigest(),
        "shared_c3_m4_cohort":len(rows),
        "five_plus_five_venue_research_candidates":len(selected),
        "candidate_min_date":min(r["date"] for r in selected),
        "candidate_max_date":max(r["date"] for r in selected),
        "month_counts":dict(sorted(Counter(r["date"][:7] for r in selected).items())),
        "league_counts":dict(sorted(Counter(r["league"] for r in selected).items())),
        "artifact_created_at":artifact_created_at,
        "targets_before_examined_artifact":sum(r["date"]<timestamp.date().isoformat() for r in selected),
        "missing_provenance_columns":absent,
        "historical_provider_vintage_proven":0,
        "provider_xg_revisions_observed":None,
        "raw_public_redistribution_rights_verified":False,
        "no_model_test":True,
        "raw_xg_exported":False,
        "interpretation":"No as-of evidence: absence of proof does not mean that pre-match xG did not exist."
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return outcome

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--archive",required=True,type=Path)
    p.add_argument("--cohort",required=True,type=Path)
    p.add_argument("--artifact-created-at",required=True)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(audit(a.archive,a.cohort,a.artifact_created_at,a.out),ensure_ascii=False,indent=2))
