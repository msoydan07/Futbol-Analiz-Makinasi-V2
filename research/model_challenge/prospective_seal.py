"""Append-only, pre-kickoff research challenger forecast seal.

This script does NOT produce model predictions. It accepts an explicitly
provided pre-match candidate from an independent research process, verifies
its fixture and as-of evidence, and seals it against later editing. Do not
call it a live challenger until a model inference workflow is attached.
Never alters 2.6.3 production/pilot data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCHEMA = "MC_PROSPECTIVE_SHADOW_SEAL_V1"
MODELS = ("Elo", "Poisson", "XGBoost", "EqualWeightHybrid")
KNOWN_LEAGUES = frozenset((
  "ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1"
))
class Rejected(ValueError): pass

def dt(value):
    if not isinstance(value,str):
        raise Rejected("timestamp is not a string")
    try:
        result = datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as err:
        raise Rejected("invalid timestamp") from err
    if result.tzinfo is None or result.utcoffset() is None:
        raise Rejected("timezone missing")
    return result.astimezone(timezone.utc)

def digest(payload):
    body=json.dumps(payload,sort_keys=True,separators=(",",":"),
                    ensure_ascii=False,allow_nan=False).encode("utf8")
    return hashlib.sha256(body).hexdigest()

def validate(candidate,now):
    if not isinstance(candidate,dict) or set(candidate)!={
        "schema","fixture","source","models","created_at_utc"}:
        raise Rejected("unrecognized candidate fields")
    if candidate["schema"]!="MC_PROSPECTIVE_SHADOW_INPUT_V1":
        raise Rejected("invalid schema")
    if not isinstance(candidate["fixture"],dict) or set(candidate["fixture"])!={
        "fixture_id","league","home_id","away_id","kickoff_utc"}:
        raise Rejected("fixture fields invalid")
    f=candidate["fixture"]
    if (f["league"] not in KNOWN_LEAGUES or
        any(not isinstance(f[k],str) or not re.fullmatch(r"[A-Za-z0-9._:-]{2,96}",f[k])
            for k in ("fixture_id","home_id","away_id")) or
        f["home_id"]==f["away_id"]):
        raise Rejected("fixture identities invalid")
    if not isinstance(candidate["source"],dict) or set(candidate["source"])!={
        "official_fixture_url","source_verified_at_utc","history_asof_utc",
        "model_code_sha","history_sha"}:
        raise Rejected("source evidence fields invalid")
    s=candidate["source"]
    if (not isinstance(s["official_fixture_url"],str) or
       not s["official_fixture_url"].startswith("https://") or
       len(s["official_fixture_url"])>500):
        raise Rejected("missing https fixture evidence")
    if any(not isinstance(s[k],str) or not re.fullmatch(r"[a-f0-9]{40,64}",s[k])
           for k in ("model_code_sha","history_sha")):
        raise Rejected("missing model/history provenance")
    created=dt(candidate["created_at_utc"])
    kickoff=dt(f["kickoff_utc"])
    verified=dt(s["source_verified_at_utc"])
    history=dt(s["history_asof_utc"])
    if (not history<=verified<=created<=now<kickoff or
        (now-created)>timedelta(minutes=15) or
        (kickoff-now)<timedelta(minutes=2)):
        raise Rejected("stale or after-kickoff forecast, or invalid evidence order")
    models=candidate["models"]
    if not isinstance(models,dict) or set(models)!=set(MODELS):
        raise Rejected("all four model outputs required")
    for key,model in models.items():
        if not isinstance(model,dict) or set(model)!={"status","probabilities"}:
            raise Rejected("invalid model output")
        status=model["status"]
        p=model["probabilities"]
        if status=="PAS":
            if p is not None: raise Rejected("PAS must have null probabilities")
        elif status=="AVAILABLE":
            if (not isinstance(p,dict) or set(p)!={"H","D","A"} or
                any(type(x) not in (float,int) or not math.isfinite(x) or
                    x<=0 or x>=1 for x in p.values()) or
                abs(sum(p.values())-1)>1e-6):
                raise Rejected("invalid model 1X2 distribution")
        else:
            raise Rejected("unknown model status")
    # Coherent hybrid must equal mean of all three, or mark PAS.
    bases=[models[name] for name in ("Elo","Poisson","XGBoost")]
    hybrid=models["EqualWeightHybrid"]
    if any(b["status"]!="AVAILABLE" for b in bases):
        if hybrid["status"]!="PAS":raise Rejected("hybrid cannot exist without components")
    else:
        if hybrid["status"]!="AVAILABLE":raise Rejected("hybrid missing")
        if any(abs(hybrid["probabilities"][side] -
                    sum(b["probabilities"][side] for b in bases)/3)>1e-6
               for side in ("H","D","A")):
            raise Rejected("hybrid mismatch: expected predeclared equal weights")
    return candidate

def seal(candidate,root,now=None):
    now=now or datetime.now(timezone.utc)
    now=dt(now.isoformat())
    validate(candidate,now)
    f=candidate["fixture"]
    name=hashlib.sha256(json.dumps([f["league"],f["fixture_id"],
        f["home_id"],f["away_id"],f["kickoff_utc"]],
        separators=(",",":"),ensure_ascii=False).encode()).hexdigest()[:32]
    output=Path(root)/"research"/"model_challenge"/"prospective_shadow"/f["league"]/(name+".json")
    payload={"schema":SCHEMA,"research_only":True,
        "betting_authorized":False,
        "validated_at_utc":now.isoformat(),
        "candidate":candidate}
    payload["payload_sha256"]=digest(payload)
    output.parent.mkdir(parents=True,exist_ok=True)
    try:
        with output.open("x",encoding="utf8") as handle:
            handle.write(json.dumps(payload,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    except FileExistsError as err:
        raise Rejected("immutable shadow fixture already sealed") from err
    return output,payload["payload_sha256"]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",required=True)
    p.add_argument("--root",default=".")
    args=p.parse_args()
    with open(args.candidate,encoding="utf8") as f:
        candidate=json.load(f)
    path,sha=seal(candidate,args.root)
    print(json.dumps({"status":"RESEARCH_ONLY_SEALED","path":str(path),
                      "payload_sha256":sha,"betting_authorized":False}))
if __name__=="__main__":
    main()
