#!/usr/bin/env python3
"""Publish only already verified two-source score metadata, append-only.
This runs in the same trusted research workflow after review(), never on a user report.
No private PDF, archive, or model prediction changes.
"""
import argparse, datetime as dt, json, re
from pathlib import Path
from P0_HAFIZA_MUHUR_SONUC_ZINCIRI_V1 import check_receipt, utc, evaluate_once, SCORE_SCHEMA

BASE=Path("experiments/263/serbest_analiz_v2")
STATUS="TWO_PUBLIC_SOURCES_AGREE_NOT_FEDERATION_VERIFIED"
def hex64(x): return isinstance(x,str) and re.fullmatch(r"[a-f0-9]{64}",x)
def publish(root, report):
    if report.get("schema")!="P0_HAFIZA_AUTO_POSTMATCH_RESEARCH_V1" or report.get("total")!=len(report["records"]):
        raise ValueError("Invalid verifier report")
    observed=utc(report["asof_utc"])
    if observed>dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=5): raise ValueError("Future report")
    dest=root/BASE/"verified_results"; dest.mkdir(parents=True,exist_ok=True)
    pending=[];seen=set()
    for row in report["records"]:
        if row.get("status")!=STATUS:continue
        name=row["receipt"]; sig=row["payload_sha256"]
        if not hex64(sig) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}_[a-f0-9]{24}\.json",name) or not name.endswith("_"+sig[:24]+".json"):raise ValueError("Bad receipt name")
        p=root/BASE/"odds_receipts"/name
        if p.is_symlink():raise ValueError("Receipt symlink")
        d=check_receipt(json.loads(p.read_text(encoding="utf-8")))
        ko=utc(d["kickoff_utc"])
        if d["payload_sha256"]!=sig or d["fixture_key"]!=row["fixture_key"] or d["match"]!=row["match"] or observed<ko+dt.timedelta(hours=2):raise ValueError("Receipt or time mismatch")
        if sig in seen:raise ValueError("Duplicate result")
        seen.add(sig)
        proof=row["git_proof"];e=row["evidence"]
        if not re.fullmatch(r"[a-f0-9]{40}",proof["commit_sha"]) or type(proof["run_id"])!=int or proof["run_id"]<=0 or utc(proof["guard_completed_utc"])>=ko:raise ValueError("Guard proof")
        if not all(hex64(e[k]) for k in ("football_data_sha256","espn_sha256")) or not e["football_data_url"].startswith("https://www.football-data.co.uk/") or not e["espn_url"].startswith("https://site.api.espn.com/") or not e["espn_event_id"]:raise ValueError("Score evidence")
        h,a=row["score"]
        if any(type(n)!=int or not 0<=n<=99 for n in (h,a)):raise ValueError("Bad score")
        recomputed=evaluate_once([d],{"schema":SCORE_SCHEMA,"scores":[{"fixture_key":d["fixture_key"],"match_status":"FINAL","home_goals":h,"away_goals":a,"observed_after_utc":observed.isoformat()}]},now=observed)
        if recomputed["provisional_scored"]!=1 or recomputed["records"][0]["picks"]!=row["picks"]:raise ValueError("Result evaluation mismatch")
        out={"schema":"P0_HAFIZA_PUBLIC_RESULT_V1","status":STATUS,"receipt":name,"payload_sha256":sig,"fixture_key":d["fixture_key"],"match":d["match"],"league":d["league"],"home_id":d["home_id"],"away_id":d["away_id"],"kickoff_utc":d["kickoff_utc"],"observed_after_utc":observed.isoformat(),"score":[h,a],"git_proof":{k:proof[k] for k in ("commit_sha","run_id","guard_completed_utc")},"evidence":{k:e[k] for k in ("football_data_url","espn_url","espn_event_id","football_data_sha256","espn_sha256")},"picks":row["picks"]}
        target=dest/(sig+".json")
        if target.is_symlink():raise ValueError("Result symlink")
        if target.exists():
            prior=json.loads(target.read_text(encoding="utf-8"))
            # Later source snapshots may change. Never replace the initial evidence.
            stable=("schema","status","receipt","payload_sha256","fixture_key","match","league","home_id","away_id","kickoff_utc","score","picks")
            if any(prior.get(k)!=out[k] for k in stable):raise ValueError("Existing result conflict; manual review")
            continue
        pending.append((target,out))
    for target,out in pending:
        with target.open("x",encoding="utf-8") as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write("\n")
    return len(pending)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--report",type=Path,required=True)
    a=p.parse_args();print("New public result metadata:",publish(a.root,json.loads(a.report.read_text(encoding="utf-8"))))
