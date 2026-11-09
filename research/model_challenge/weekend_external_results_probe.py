"""Read-only third-party 2026/27 weekend score CANDIDATE probe.

Matches immutable existing 2.6.3 SHA-sealed morning forecasts against
football-data.co.uk results using official-identity-registry aliases
and actual match local calendar dates. Does NOT create a human-attested or
network-independently verified postmatch observation, never modifies
pilot/new100 seals, and never asserts all fixtures were found.

The 20% joint-score mix weight was fixed on August–September before this
script. This was invented after weekend match outcomes existed, so any
comparison here is NOT blind prospective method validation.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,urllib.request
from collections import defaultdict,Counter
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from identity import Registry,normalize
from collect_team_candidates import LEAGUES,BASE
from experiments.263.official_page_lookup_263 import TIMEZONES
from audit_weekend_sealed_goals import digest

SCHEMA="MC_NOVEMBER_EXTERNAL_SCORE_CANDIDATE_DIAGNOSTIC_V1"
MARKETS={"BTTS_YES":"BTTS_YES","OVER_1.5":"OVER_1.5",
         "OVER_2.5":"OVER_2.5","OVER_3.5":"OVER_3.5"}
BASELINES={"BTTS_YES":lambda h,a:int(h>0 and a>0),
           "OVER_1.5":lambda h,a:int(h+a>=2),
           "OVER_2.5":lambda h,a:int(h+a>=3),
           "OVER_3.5":lambda h,a:int(h+a>=4)}
SHRINK=35.
WEIGHT=.20
ALLOWED={"www.football-data.co.uk","football-data.co.uk"}

def dateparse(s):
    for fmt in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d"):
        try:return datetime.strptime(s.strip(),fmt).date().isoformat()
        except ValueError:pass
    raise ValueError("unrecognized score date")

def retrieve(url):
    from urllib.parse import urlparse
    with urllib.request.urlopen(urllib.request.Request(url,headers={
        "User-Agent":"FutbolAnalizResearch/1.0"}),timeout=25) as response:
        effective=response.geturl();raw=response.read(2_500_001)
    p,q=urlparse(url),urlparse(effective)
    if (len(raw)>2_500_000 or p.scheme!="https" or q.scheme!="https" or
        p.hostname not in ALLOWED or q.hostname not in ALLOWED or
        p.path!=q.path or q.query or q.fragment):
        raise ValueError("unacceptable redirect")
    sha=hashlib.sha256(raw).hexdigest()
    rr=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if not rr or not {"Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"}.issubset(rr[0]):
        raise ValueError("bad source CSV")
    return rr,sha

def result_index(reg,*,fetch=retrieve):
    index={};diagnostics={}
    for league,code in LEAGUES.items():
        url=f"{BASE}/2627/{code}.csv"
        try:
            rows,sha=fetch(url)
            n=0;unmapped=0
            for row in rows:
                if not row.get("Date") or row.get("FTHG","")=="" or row.get("FTAG","")=="":
                    continue
                try:
                    d=dateparse(row["Date"])
                    h,a=int(row["FTHG"]),int(row["FTAG"])
                    if not(0<=h<=30 and 0<=a<=30):continue
                    res="H" if h>a else "A" if h<a else "D"
                    if row["FTR"]!=res:continue
                    hi=reg.data["aliases"].get(normalize(row["HomeTeam"]))
                    ai=reg.data["aliases"].get(normalize(row["AwayTeam"]))
                    if not hi or not ai or hi==ai:
                        unmapped+=1;continue
                    key=(league,d,hi,ai)
                    if key in index:
                        raise ValueError("duplicate external score identity")
                    index[key]={"score":[h,a],"source_url":url,
                                "source_sha256":sha,"source_date":d,
                                "source_classification":"THIRD_PARTY_NOT_OFFICIAL_ATTESTED"}
                    n+=1
                except (ValueError,TypeError):
                    unmapped+=1
            diagnostics[league]={"scored_rows_mapped":n,"other_rows_unmapped":unmapped,
                "source_url":url,"sha256":sha,"status":"DOWNLOADED_THIRD_PARTY_NOT_VERIFIED"}
        except Exception as exc:
            diagnostics[league]={"status":"SOURCE_BLOCKED",
               "reason":type(exc).__name__+":"+str(exc)[:110]}
    return index,diagnostics

def score(root,output,*,fetch=retrieve):
    root=Path(root)
    reg=Registry(root/"experiments/263/evidence/identity_index_263.json")
    idx,sources=result_index(reg,fetch=fetch)
    hist=list(csv.DictReader(open(root/"data/quad_accepted_263/extended_history.csv",
                                  encoding="utf8",newline="")))
    if len(hist)!=4518:
        raise ValueError("NOT_ACCEPTED_4518_BASELINE")
    counts=defaultdict(lambda:[0,0,0,0,0])
    for row in hist:
        if row["match_date"]>="2026-11-06":
            raise ValueError("history later than first weekend forecast")
        h,a=int(row["home_goals"]),int(row["away_goals"])
        for league in (row["league"],"ALL"):
            v=counts[league]
            v[0]+=1
            for k,f in enumerate(BASELINES.values(),1):v[k]+=f(h,a)
    matches=[];unmatched=[];invalid=[]
    paths=sorted(root.glob("forward_morning_263/*/*.json"))+sorted(root.glob("forward_quad_263/*/*.json"))
    for f in paths:
        obj=json.loads(f.read_text(encoding="utf8"))
        if obj.get("schema")!="quad_forward_263_v1" or obj.get("payload_sha256")!=digest({
                k:v for k,v in obj.items() if k!="payload_sha256"}):
            invalid.append({"file":str(f.relative_to(root)),"reason":"SHA_INVALID"});continue
        fx=obj["fixture"];date=datetime.fromisoformat(fx["kickoff_utc"].replace("Z","+00:00")).astimezone(
            ZoneInfo(TIMEZONES[fx["league"]])).date().isoformat()
        key=(fx["league"],date,fx["home_id"],fx["away_id"])
        external=idx.get(key)
        if external is None:
            unmatched.append({"fixture":str(f.relative_to(root)),"league":fx["league"],
                              "date":date,"reason":"NO_EXACT_EXTERNAL_PROVIDER_RESULT"})
            continue
        model=obj["model_predictions"].get("M4",{})
        if model.get("status")!="AVAILABLE":
            invalid.append({"file":str(f.relative_to(root)),"reason":"NO_M4"});continue
        m=model["goals"]["markets"]
        h,a=external["score"]
        per={}
        for i,(market,labeler) in enumerate(BASELINES.items(),1):
            value=float(m[market])
            league=counts[fx["league"]];alln=counts["ALL"]
            prior=(league[i]+SHRINK*(alln[i]/alln[0]))/(league[0]+SHRINK)
            mixed=(1-WEIGHT)*value+WEIGHT*prior
            label=labeler(h,a)
            if not all(math.isfinite(z) and 0<=z<=1 for z in (value,mixed)):
                raise ValueError("bad probabilities")
            per[market]={"old":value,"candidate":mixed,"actual":label,
                "original_brier":(value-label)**2,
                "candidate_brier":(mixed-label)**2}
        matches.append({"fixture":str(f.relative_to(root)),
            "forecast_sha":obj["payload_sha256"],"league":fx["league"],
            "date":date,"score":external["score"],
            "source_url":external["source_url"],
            "source_sha256":external["source_sha256"],"markets":per})
    summary={}
    for market in BASELINES:
        x=[r["markets"][market] for r in matches]
        if x:summary[market]={"n":len(x),
            "old_brier":sum(r["original_brier"] for r in x)/len(x),
            "candidate_brier":sum(r["candidate_brier"] for r in x)/len(x)}
    result={"schema":SCHEMA,"evaluation_status":"CANDIDATE_THIRD_PARTY_RESULTS_NOT_OFFICIAL_ATTESTATION",
        "actual_seal_files":len(paths),"matched_thirdparty_scored":len(matches),
        "no_source_match":len(unmatched),"invalid_seals":invalid,
        "source_diagnostics":sources,"unmatched":unmatched,
        "aggregate":summary,"matches":matches,
        "calibration_weight_development_selected":WEIGHT,
        "weekend_outcomes_not_used_to_fit_weight":True,
        "weekend_outcomes_were_known_before_this_method_was_authored":True,
        "not_blind_prospective_validation":True,
        "research_only":True,"no_changes_to_official_postmatch":True,
        "betting_authorized":False}
    out=Path(output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:result[k] for k in ("actual_seal_files",
         "matched_thirdparty_scored","no_source_match","aggregate")},indent=2))
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    score(args.root,args.out)
