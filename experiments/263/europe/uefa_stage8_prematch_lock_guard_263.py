"""Stage8 PREP ONLY: validate a future, explicitly submitted pre-kickoff shadow record.

This module does not calculate forecasts, fetch team news, or create records.
The actual record is constructed only after T-60 human-reviewed data,
and MUST be committed before kickoff. Do not silently promote beta.
"""
import argparse, datetime as dt, hashlib, json, math, pathlib, sys
UTC=dt.timezone.utc
MODELS=("M0_REFERENCE_ONLY","M0_PLUS_ELO_EXPERIMENTAL")
MARKETS=("home","draw","away")
class LockError(ValueError):pass
def parse(t):
    try: x=dt.datetime.fromisoformat(t.replace("Z","+00:00"))
    except (ValueError,AttributeError):raise LockError("INVALID_DATETIME")
    if x.tzinfo is None:raise LockError("NAIVE_DATETIME")
    return x.astimezone(UTC)
def validate(record,now):
    if record.get("schema")!="263_UEFA_STAGE8_PREMATCH_DUAL_SHADOW_RECORD_V1":raise LockError("SCHEMA")
    ko=parse(record["kickoff_utc"]);capture=parse(record["data_captured_utc"])
    now=parse(now)
    if not (capture<=now<ko):raise LockError("TOO_LATE_OR_FUTURE_SOURCE")
    if not (0<(ko-now).total_seconds()<=7200):raise LockError("OUTSIDE_T_MINUS_120_WINDOW")
    if record.get("competition") not in ("UEFA_CL","UEFA_EL"):raise LockError("COMPETITION")
    if not isinstance(record.get("uefa_match_id"),str) or not record["uefa_match_id"]:raise LockError("MATCH_ID")
    if record.get("lineup_status") not in ("BOTH_OFFICIAL","ONE_OFFICIAL","NOT_ANNOUNCED"):raise LockError("LINEUP_STATUS")
    if not isinstance(record.get("lineup_source_urls"),list):raise LockError("LINEUP_EVIDENCE")
    if record["lineup_status"]!="NOT_ANNOUNCED" and not record["lineup_source_urls"]:raise LockError("LINEUP_SOURCE_REQUIRED")
    if record.get("lineup_used_as_numeric_adjustment") is not False:raise LockError("UNAPPROVED_LINEUP_MODIFIER")
    if record.get("elo_beta_production_approved") is not False:raise LockError("UNAPPROVED_BETA")
    if record.get("pilot_100_matches_affected") is not False:raise LockError("PILOT_PROTECTED")
    if not isinstance(record.get("source_sha256"),dict) or not all(
        isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v)
        for v in record["source_sha256"].values()
    ) or not {"stage4","stage5","retro"}.issubset(record["source_sha256"]):raise LockError("MISSING_SOURCE_HASH")
    paths=record.get("model_outputs")
    if not isinstance(paths,dict) or set(paths)!=set(MODELS):raise LockError("TWO_SHADOWS_REQUIRED")
    for key,val in paths.items():
        p=val.get("1x2")
        if not isinstance(p,dict) or set(p)!=set(MARKETS):raise LockError("1X2_FIELDS")
        if not all(isinstance(p[m],(float,int)) and math.isfinite(p[m]) and 0<=p[m]<=1 for m in MARKETS):raise LockError("BAD_PROB")
        if abs(sum(p.values())-1)>1e-10:raise LockError("MASS")
        if not all(isinstance(val.get(z),(float,int)) and math.isfinite(val[z]) and 0<=val[z]<=1 for z in ("over_2_5","btts_yes")):raise LockError("MARKETS")
        if not all(isinstance(val.get(z),(float,int)) and math.isfinite(val[z]) and .15<=val[z]<=5 for z in ("lambda_home","lambda_away")):raise LockError("LAMBDA")
    if record.get("odds_or_ev_present") is not False:raise LockError("NO_ODDS_OR_EV")
    return True
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    src=pathlib.Path(args.candidate)
    dst=pathlib.Path(args.output)
    if dst.exists():raise LockError("NO_OVERWRITE")
    if not str(dst).startswith("experiments/263/locked_prematch/"):raise LockError("QUARANTINE_ONLY")
    raw=src.read_bytes();rec=json.loads(raw)
    now=dt.datetime.now(UTC).isoformat()
    validate(rec,now)
    # No record before full validation. One exclusive-create, fail if exists.
    dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open("x",encoding="utf-8") as f:
        json.dump({"record":rec,"lock_created_utc":now,
                   "canonical_candidate_sha256":hashlib.sha256(raw).hexdigest()},
                  f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
    print("LOCK_FILE_CREATED_REQUIRES_GIT_COMMIT_AND_REMOTE_SHA_FOR_AUDIT:"+str(dst))
if __name__=="__main__":main()
