"""Append-only provenance bridge: forecast -> no-odds PAS -> optional pre-KO price decision.
Never creates fixtures, bookmaker quotes or post-kickoff predictions.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
from forward_c3 import read_aware
from forward_calibration_bridge_263 import _digest
from forward_empirical_baseline_263 import produce
from four_model_value_policy_263 import decide,render
from market_fifth_baseline_263 import sealed_payload,OBSERVATION_SCHEMA
from market_quote_intake_263 import REQUEST_SCHEMA
from morning_quote_policy_263 import read_for_forecast

FORECAST_RE=re.compile(r"forward_quad_263/(\d{4}-\d{2}-\d{2})/([a-f0-9]{24})\.json")
QUOTE_RE=re.compile(r"experiments/263/market_quotes_locked/(\d{4}-\d{2}-\d{2})/([a-f0-9]{24})\.json")
REQUEST_RE=re.compile(r"experiments/263/market_quote_requests/[A-Za-z0-9_-]+\.json")
FORECAST_STATUS="REGISTERED_FOUR_MODELS_EXPERIMENTAL"
QUOTE_STATUS="MANUAL_ATTESTATION_SEALED_LOCALLY_AWAIT_GITHUB_PREKO_COMMIT"
def safe(root,rel,pattern):
    if not isinstance(rel,str) or not pattern.fullmatch(rel):
        raise ValueError("UNSAFE_RECORD_PATH")
    parent=Path(root).resolve();p=(parent/rel).resolve()
    if not p.is_relative_to(parent) or not p.is_file():
        raise ValueError("REQUIRED_SOURCE_RECORD_MISSING")
    return p
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def save(p,content):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8") as f:
        if isinstance(content,str):f.write(content)
        else:json.dump(content,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")
def forecast(root,rel,now):
    p=safe(root,rel,FORECAST_RE);f=read(p)
    sealed_payload(f,"quad_forward_263_v1")
    day,ident=FORECAST_RE.fullmatch(rel).groups()
    if f["fixture"]["match_local_date"]!=day:raise ValueError("FORECAST_DATE_MISMATCH")
    if not read_aware(f["created_at_utc"])<=now<read_aware(f["fixture"]["kickoff_utc"]):
        raise ValueError("POST_KICKOFF_RECORD_FORBIDDEN")
    return f,day,ident
def batch_items(report,mode):
    data=read(report)
    if mode=="baseline":
        if data.get("schema")!="quad_named_match_batch_report_v1":raise ValueError("BAD_FORECAST_REPORT")
        return [x for x in data["outcomes"] if x["status"]==FORECAST_STATUS]
    if data.get("schema")!="263_manual_market_quote_batch_report_v1":raise ValueError("BAD_QUOTE_REPORT")
    return [x for x in data["items"] if x["status"]==QUOTE_STATUS]
def link_baseline(report,history,devlock,root,out,now):
    items=batch_items(report,"baseline")
    if not items:raise ValueError("NO_NEW_FORECASTS")
    lock=read(devlock);results=[]
    for item in items:
        f,day,ident=forecast(root,item["path"],now)
        if f["payload_sha256"]!=item["payload_sha256"]:raise ValueError("FORECAST_REPORT_SHA_MISMATCH")
        b=produce(f,history,now=now)
        d=decide(f,b,lock,observation=None,now=now)
        if d["status"]!="RESEARCH_PAS" or d["quote_sha256"] is not None:
            raise ValueError("UNVERIFIED_PRICE_CANNOT_CREATE_VALUE_PICK")
        dest=Path(out)/day/ident
        if dest.exists():raise ValueError("PRELIMINARY_ALREADY_WRITTEN")
        save(dest/"baseline.json",b)
        save(dest/"preprice_decision.json",d)
        save(dest/"preprice_decision.md",render(d))
        results.append((item["path"],f["payload_sha256"],d["payload_sha256"]))
    return results
def _quote_forecast(root,item):
    quote=read(safe(root,item["path"],QUOTE_RE))
    sealed_payload(quote,OBSERVATION_SCHEMA)
    if quote["payload_sha256"]!=item["payload_sha256"]:raise ValueError("QUOTE_REPORT_SHA_MISMATCH")
    request=quote["source_review"]["request_path"]
    req_file=safe(root,request,REQUEST_RE)
    if hashlib.sha256(req_file.read_bytes()).hexdigest()!=quote["source_review"]["request_file_sha256"]:
        raise ValueError("QUOTE_REQUEST_REVISED")
    req=read(req_file)
    if req.get("schema")!=REQUEST_SCHEMA:raise ValueError("WRONG_QUOTE_REQUEST_SCHEMA")
    return quote,req["forecast_path"]
def link_priced(report,devlock,root,bases,out,now):
    items=batch_items(report,"priced")
    if not items:raise ValueError("NO_NEW_QUOTES")
    lock=read(devlock);results=[]
    for item in items:
        q,rel=_quote_forecast(root,item)
        f,day,ident=forecast(root,rel,now)
        baseline_file=Path(bases)/day/ident/"baseline.json"
        if not baseline_file.is_file():raise ValueError("MISSING_LOCKED_ASOF_BASELINE")
        b=read(baseline_file)
        d=decide(f,b,lock,observation=q,morning_snapshot=read_for_forecast(f),now=now)
        if d["quote_sha256"]!=q["payload_sha256"]:raise ValueError("ODDS_DECISION_SHA_LINK_MISMATCH")
        dest=Path(out)/day/(ident+".json")
        if dest.exists():raise ValueError("PRICE_DECISION_ALREADY_WRITTEN")
        save(dest,d);save(dest.with_suffix(".md"),render(d))
        results.append((rel,q["payload_sha256"],d["payload_sha256"]))
    return results
def precommit(report,mode,root,bases,priced,now):
    items=batch_items(report,mode)
    if not items:raise ValueError("NOTHING_TO_PRECOMMIT")
    for item in items:
        if mode=="baseline":rel=item["path"]
        else:_,rel=_quote_forecast(root,item)
        f,day,ident=forecast(root,rel,now)
        if mode=="baseline":
            required=[Path(bases)/day/ident/"baseline.json",Path(bases)/day/ident/"preprice_decision.json"]
        else:required=[Path(priced)/day/(ident+".json")]
        for p in required:
            val=read(p)
            if val.get("forecast_sha256")!=f["payload_sha256"] or _digest({k:v for k,v in val.items() if k!="payload_sha256"})!=val.get("payload_sha256"):
                raise ValueError("PRECOMMIT_RECORD_TAMPERED_OR_UNLINKED")
    return len(items)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("baseline","priced","verify-baseline","verify-priced"))
    p.add_argument("--report",required=True)
    p.add_argument("--history")
    p.add_argument("--dev-lock",default="experiments/263/forward_dev_calibration_lock_263.json")
    p.add_argument("--root",default=".")
    p.add_argument("--baselines",default="experiments/263/quad_research_links")
    p.add_argument("--priced-output",default="experiments/263/quad_priced_decisions")
    args=p.parse_args();now=datetime.now(timezone.utc)
    if args.mode=="baseline":
        if not args.history:raise SystemExit("HISTORY_REQUIRED")
        result=link_baseline(args.report,args.history,args.dev_lock,args.root,args.baselines,now)
    elif args.mode=="priced":result=link_priced(args.report,args.dev_lock,args.root,args.baselines,args.priced_output,now)
    else:result=precommit(args.report,args.mode.removeprefix("verify-"),args.root,args.baselines,args.priced_output,now)
    print(json.dumps({"mode":args.mode,"linked":len(result) if isinstance(result,list) else result}))
if __name__=="__main__":main()
