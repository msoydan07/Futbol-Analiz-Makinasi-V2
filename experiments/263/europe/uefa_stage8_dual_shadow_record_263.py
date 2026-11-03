"""Stage8: construct an actual T-60 two-shadow UEFA record from PRE-ARCHIVED inputs.

Trigger is a NEW reviewed lineup evidence JSON file committed to the experiment
branch. Until that file exists, no forecasts are computed or recorded.
No pregame source can be promoted by using only its original article date.
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,math
from pathlib import Path
from uefa_stage8_prematch_lock_guard_263 import validate,LockError
from uefa_nov3_5_stage6_shadow_math_preflight_263 import (
    make_pair,compute_volatile,SOURCES,upstream_inputs,aware_utc)
UTC=dt.timezone.utc
SCHEMA="263_UEFA_STAGE8_REVIEWED_LINEUP_EVIDENCE_V1"
MAX_AGE=dt.timedelta(hours=16)
MAX_REVIEW_AGE=dt.timedelta(minutes=50)
def read_bytes_checked(path,sha):
    b=Path(path).read_bytes()
    if hashlib.sha256(b).hexdigest()!=sha:
        raise LockError("SOURCE_SNAPSHOT_CHANGED")
    return json.loads(b)
def parse_lineup(part,now,ko):
    if not isinstance(part,dict):raise LockError("LINEUP_REVIEW_NOT_PROVIDED")
    state=part.get("status")
    if state not in ("OFFICIAL","NOT_PUBLISHED","UNVERIFIED"):
        raise LockError("INVALID_LINEUP_REVIEW_STATE")
    links=part.get("source_urls")
    if not isinstance(links,list) or any(not isinstance(u,str) or not u.startswith("https://") or len(u)>1000 for u in links):
        raise LockError("BAD_LINEUP_LINKS")
    if state in ("OFFICIAL","NOT_PUBLISHED") and not links:
        raise LockError("CLAIMED_OFFICIAL_LINEUP_NEEDS_SOURCE_URL")
    reviewed=aware_utc(part.get("reviewed_utc"))
    if not now-MAX_REVIEW_AGE<=reviewed<=now or reviewed>=ko:
        raise LockError("LINEUP_REVIEW_NOT_FRESH_OR_AFTER_KO")
    if part.get("human_reviewed") is not True:
        raise LockError("LINEUP_MUST_BE_HUMAN_OR_WEB_VERIFIED")
    return state,links,reviewed.isoformat()
def candidate_batch(s4,s5,retro,scope,evidence,now):
    now=aware_utc(now)
    if evidence.get("schema")!=SCHEMA:raise LockError("REVIEW_EVIDENCE_SCHEMA")
    if evidence.get("purpose")!="REAL_PREMATCH_USER_REQUESTED_SHADOW_ONLY":
        raise LockError("UNAPPROVED_TRIGGER_PURPOSE")
    proto=upstream_inputs(s4,s5,retro,scope)
    pairs4={str(x["uefa_match_id"]):x for x in s4["fixtures"]}
    pairs5={str(x["uefa_match_id"]):x for x in s5["matches"]}
    pairs3={str(x["uefa_match_id"]):x for x in scope["verified_fixtures"]}
    selected=evidence.get("fixtures")
    if not isinstance(selected,list) or not 1<=len(selected)<=6:
        raise LockError("ONE_COHORT_MUST_HAVE_1_TO_6_MATCHES")
    if len({str(x.get("uefa_match_id")) for x in selected})!=len(selected):
        raise LockError("DUPLICATE_UEFA_MATCH_IN_COHORT")
    source_times=(aware_utc(s4["analysis_time_utc"]),
                  aware_utc(s5["source_evidence"]["beyondelo_audited_utc"]))
    outputs=[]
    shared_kickoff=None
    for entry in selected:
        key=str(entry.get("uefa_match_id"))
        if not (key in pairs3 and key in pairs4 and key in pairs5):
            raise LockError("NOT_AN_ELIGIBLE_VERIFIED_UEFA_FIXTURE")
        sf=pairs4[key];e=pairs5[key];off=pairs3[key]
        pair=make_pair(sf,e,off)
        ko=pair["kickoff"]
        # T-60: earliest allowed T-75, latest 1s before kickoff.
        if not 0<(ko-now).total_seconds()<=75*60:
            raise LockError("OUTSIDE_T_MINUS_75_KICKOFF_WINDOW")
        if shared_kickoff is not None and shared_kickoff!=ko:
            raise LockError("MIXED_KICKOFFS_REQUIRE_SEPARATE_RECORDS")
        shared_kickoff=ko
        # Morning snapshots can be used ONLY for same-day games after recheck;
        # later days require a separately refreshed archive.
        for t in source_times:
            if not t<=now or (now-t)>MAX_AGE or t.date()!=ko.date():
                raise LockError("SAME_DAY_FRESH_SOURCE_REQUIRED_BEFORE_RECORD")
        if sf["date"]!=ko.date().isoformat() or e["date"]!=sf["date"]:
            raise LockError("FIXTURE_DAY_CHANGED")
        home_state,home_urls,h_rev=parse_lineup(entry.get("home_lineup"),now,ko)
        away_state,away_urls,a_rev=parse_lineup(entry.get("away_lineup"),now,ko)
        n_official=sum(x=="OFFICIAL" for x in (home_state,away_state))
        if n_official==2:lineup_status="BOTH_OFFICIAL"
        elif n_official==1:lineup_status="ONE_OFFICIAL"
        elif home_state==away_state=="NOT_PUBLISHED":lineup_status="NOT_ANNOUNCED"
        else:lineup_status="NOT_VERIFIED"
        # Avoid claiming "not announced" without a real article check.
        ll=sorted(set(home_urls+away_urls))
        if not ll and lineup_status!="NOT_VERIFIED":
            raise LockError("MISSING_RESOLVABLE_OFFICIAL_LINEUP_URL")
        temp=compute_volatile(pair,
             proto["UEFA_train_home_goal_mean"],
             proto["UEFA_train_away_goal_mean"],
             proto["beta_retrospective_fitted"])
        def one(src):
            lh,la,probs,over,btts=src
            return {"lambda_home":lh,"lambda_away":la,
                    "1x2":{"home":probs[0],"draw":probs[1],"away":probs[2]},
                    "over_2_5":over,"btts_yes":btts}
        newer=max(source_times[0],source_times[1],
                  aware_utc(h_rev),aware_utc(a_rev))
        record={
            "schema":"263_UEFA_STAGE8_PREMATCH_DUAL_SHADOW_RECORD_V1",
            "uefa_match_id":int(key),
            "competition":sf["competition"],
            "home":sf["home"],"away":sf["away"],
            "canonical_home_id":sf["home_id"],
            "canonical_away_id":sf["away_id"],
            "kickoff_utc":sf["kickoff_utc"],
            "data_captured_utc":newer.isoformat(),
            "record_constructed_utc":now.isoformat(),
            "source_observed_utc":{
                "stage4_football_data":source_times[0].isoformat(),
                "stage5_beyondelo":source_times[1].isoformat(),
                "lineup_home_review":h_rev,"lineup_away_review":a_rev},
            "source_sha256":dict(SOURCES),
            "lineup_status":lineup_status,
            "lineup_verification_by_side":{
                "home":home_state,"away":away_state},
            "lineup_source_urls":ll,
            "lineup_used_as_numeric_adjustment":False,
            "elo_beta_production_approved":False,
            "pilot_100_matches_affected":False,
            "odds_or_ev_present":False,
            "M0_model_role":"UNAPPROVED_GOL_ONLY_REFERENCE",
            "M0_plus_Elo_model_role":"UNAPPROVED_EXPLORATORY_SHADOW",
            "model_outputs":{
                "M0_REFERENCE_ONLY":one(temp["M0"]),
                "M0_PLUS_ELO_EXPERIMENTAL":one(temp["M0Elo"])}
        }
        validate(record,now.isoformat())
        outputs.append(record)
    return outputs
def main():
    p=argparse.ArgumentParser()
    for s in ("stage4","stage5","retro","stage3","evidence","out_dir"):
        p.add_argument("--"+s.replace("_","-"),required=True)
    a=p.parse_args()
    now=dt.datetime.now(UTC)
    inputs=[
        read_bytes_checked(a.stage4,SOURCES["stage4"]),
        read_bytes_checked(a.stage5,SOURCES["stage5"]),
        read_bytes_checked(a.retro,SOURCES["retro"]),
        json.loads(Path(a.stage3).read_text(encoding="utf8")),
        json.loads(Path(a.evidence).read_text(encoding="utf8"))]
    records=candidate_batch(*inputs,now)
    root=Path(a.out_dir)
    if root.as_posix()!="experiments/263/locked_prematch":
        raise LockError("LOCK_ROOT_REQUIRED")
    # Preflight entire cohort, including existing target files, BEFORE ANY WRITE.
    targets=[]
    for rec in records:
        file=root/(f"uefa_{rec['uefa_match_id']}.json")
        if file.exists():raise LockError("PREVIOUS_FORECAST_LOCK_EXISTS_NO_OVERWRITE")
        targets.append(file)
    # A late clock check prevents generation if cutoff passed in the middle.
    if any(dt.datetime.now(UTC)>=aware_utc(x["kickoff_utc"]) for x in records):
        raise LockError("KICKOFF_PASSED_BEFORE_RECORD_PERSISTED")
    root.mkdir(parents=True,exist_ok=True)
    for rec,file in zip(records,targets):
        raw=json.dumps(rec,sort_keys=True,ensure_ascii=False,
                       separators=(",",":"),allow_nan=False).encode("utf8")
        with file.open("x",encoding="utf8") as handle:
            json.dump({"record":rec,"lock_created_utc":dt.datetime.now(UTC).isoformat(),
                       "canonical_candidate_sha256":hashlib.sha256(raw).hexdigest()},
                      handle,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
            handle.write("\n")
    print("PREMATCH_SHADOW_RECORDS_CREATED_LOCAL_UNTIL_REMOTE_GIT_COMMIT="+str(len(records)))
    print("MATCH_IDS="+",".join(str(x["uefa_match_id"]) for x in records))
    print("EARLIEST_KICKOFF_UTC="+min(x["kickoff_utc"] for x in records))
if __name__=="__main__":main()
