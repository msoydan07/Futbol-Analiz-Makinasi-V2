#!/usr/bin/env python3
"""Read-only research outcome bridge. No prediction or archive writes.
A GitHub push guard success before KO plus independently matching two public
score feeds is required. A source disagreement or missing identity stays pending.
Two public sources are NOT federation certification.
"""
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, io, json, os, re, subprocess, sys
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from zoneinfo import ZoneInfo
from P0_HAFIZA_MUHUR_SONUC_ZINCIRI_V1 import check_receipt, evaluate_once, utc, SCORE_SCHEMA
from GUNLUK_SERBEST_ANALIZ_KAPISI_V2 import TZ

BRANCH="experiment/p0-oran-hafizasi-22-lig-20261122"
REPO="msoydan07/Futbol-Analiz-Makinasi-V2"
PREFIX="experiments/263/serbest_analiz_v2/odds_receipts"
WORKFLOW="263-p0-hafiza-preko-guard-v1.yml"
CODES=dict(ENG1=("E0","eng.1"),ENG2=("E1","eng.2"),GER1=("D1","ger.1"),
           ESP1=("SP1","esp.1"),ITA1=("I1","ita.1"),FRA1=("F1","fra.1"),
           NED1=("N1","ned.1"),TUR1=("T1","tur.1"),POR1=("P1","por.1"),BEL1=("B1","bel.1"))
class Pending(ValueError): pass

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Pending('SOURCE_REDIRECT_BLOCKED')

@lru_cache(maxsize=128)
def fetch(url):
    host=urlparse(url).hostname
    if urlparse(url).scheme!='https' or host not in {"api.github.com","www.football-data.co.uk","site.api.espn.com"}:
        raise Pending("SOURCE_HOST_NOT_ALLOWED")
    headers={"User-Agent":"263-research-result-verifier/1","Accept":"application/json" if host!="www.football-data.co.uk" else "text/csv"}
    if host=="api.github.com" and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
    with build_opener(NoRedirect()).open(Request(url,headers=headers),timeout=20) as f:
        if urlparse(f.geturl()).hostname!=host:
            raise Pending("SOURCE_REDIRECT_HOST_CHANGED")
        raw=f.read(12_000_001)
        if len(raw)>12_000_000:raise Pending("SOURCE_TOO_LARGE")
        return raw

def git(root,*args):
    p=subprocess.run(["git",*args],cwd=root,text=True,capture_output=True,check=True)
    return p.stdout.strip()

def accepted_run(runs,sha,ko):
    matches=[]
    for r in runs:
        if (r.get("head_sha")!=sha or r.get("head_branch")!=BRANCH
            or r.get("event")!="push" or r.get("conclusion")!="success"
            or r.get("status")!="completed" or r.get("run_attempt")!=1):
            continue
        created,updated=utc(r["created_at"]),utc(r["updated_at"])
        if created<=updated<ko:matches.append(r)
    if len(matches)!=1:raise Pending("NO_UNIQUE_SUCCESSFUL_GITHUB_GUARD_BEFORE_KO")
    return matches[0]

def git_proof(root,path,doc,get=fetch):
    if git(root,"rev-parse","--is-shallow-repository")!="false":raise Pending("FULL_GIT_HISTORY_REQUIRED")
    rel=path.relative_to(root).as_posix()
    # A historical receipt must have exactly one introducing commit and no edits.
    commits=git(root,"log","--full-history","--format=%H","HEAD","--",rel).splitlines()
    if len(commits)!=1:raise Pending("RECEIPT_NOT_IMMUTABLE_IN_GIT")
    sha=commits[0]
    changes=git(root,"diff-tree","--no-commit-id","--name-status","-r",sha).splitlines()
    if "A\t"+rel not in changes or any(not x.startswith("A\t"+PREFIX+"/") for x in changes):
        raise Pending("INTRODUCTION_NOT_RECEIPT_ONLY")
    if git(root,"status","--porcelain","--",rel):raise Pending("LOCAL_RECEIPT_MODIFIED")
    url=f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW}/runs?"+urlencode({"head_sha":sha,"event":"push","per_page":100})
    data=json.loads(get(url))
    run=accepted_run(data.get("workflow_runs",[]),sha,utc(doc["kickoff_utc"]))
    return {"commit_sha":sha,"run_id":run["id"],"run_url":run.get("html_url"),"guard_completed_utc":run["updated_at"]}

def score_int(value):
    if isinstance(value,bool) or not re.fullmatch(r"\d{1,2}",str(value)):raise Pending("INVALID_SCORE")
    return int(value)

def mapped(resolve,league,name):
    try:return resolve(league,name)
    except (ValueError,KeyError):return None

def source_pair(doc,fd,espn,resolve):
    league=doc["league"];ko=utc(doc["kickoff_utc"])
    local=ko.astimezone(ZoneInfo(TZ[league])).date()
    ids=(doc["home_id"],doc["away_id"])
    if not all(ids) or ids[0]==ids[1]:raise Pending("BAD_SEALED_TEAM_IDS")
    a=[]
    for row in csv.DictReader(io.StringIO(fd.decode("utf-8-sig"))):
        try:day=dt.datetime.strptime(row.get("Date",""),"%d/%m/%Y").date()
        except ValueError:continue
        if day!=local:continue
        if (mapped(resolve,league,row.get("HomeTeam","")),mapped(resolve,league,row.get("AwayTeam","")))!=ids:continue
        if row.get("FTR") not in ("H","D","A"):raise Pending("FOOTBALL_DATA_NOT_FINAL")
        h,v=score_int(row.get("FTHG")),score_int(row.get("FTAG"))
        if row["FTR"]!=("H" if h>v else "A" if h<v else "D"):raise Pending("FOOTBALL_DATA_SCORE_CONFLICT")
        # Validate optional clock syntax; ESPN supplies exact UTC kickoff.
        if row.get("Time"):
            try:dt.time.fromisoformat(row["Time"])
            except ValueError:raise Pending("BAD_FOOTBALL_DATA_CLOCK")
            # Football-Data time is not guaranteed league-local; no guessed timezone.
        a.append((h,v))
    b=[]
    for event in espn.get("events",[]):
        try:event_ko=utc(event["date"])
        except (ValueError,KeyError,TypeError):continue
        if event_ko!=ko:continue
        comps=event.get("competitions",[])
        if len(comps)!=1:continue
        comp=comps[0];sides={x.get("homeAway"):x for x in comp.get("competitors",[])}
        if len(comp.get("competitors",[]))!=2 or set(sides)!={"home","away"}:continue
        def side_id(side):
            t=side.get("team",{})
            found={mapped(resolve,league,t.get(k,"")) for k in ("displayName","shortDisplayName","name") if t.get(k)}
            found.discard(None)
            return next(iter(found)) if len(found)==1 else None
        if (side_id(sides["home"]),side_id(sides["away"]))!=ids:continue
        status=comp.get("status",event.get("status",{})).get("type",{})
        if status.get("completed") is not True or status.get("name")!="STATUS_FULL_TIME":
            raise Pending("ESPN_NOT_REGULATION_FULL_TIME")
        if not event.get("id"):raise Pending("ESPN_EVENT_ID_MISSING")
        b.append((score_int(sides["home"].get("score")),score_int(sides["away"].get("score")),str(event["id"])))
    if len(a)!=1 or len(b)!=1:raise Pending("SOURCE_MATCH_NOT_UNIQUE_OR_MISSING")
    if a[0]!=b[0][:2]:raise Pending("INDEPENDENT_SCORE_CONFLICT")
    return a[0],b[0][2]

def lookup(doc,resolve,get=fetch):
    league=doc["league"];ko=utc(doc["kickoff_utc"])
    local=ko.astimezone(ZoneInfo(TZ[league])).date()
    start=local.year if local.month>=7 else local.year-1
    season=f"{start%100:02d}{(start+1)%100:02d}"
    code,slug=CODES[league]
    a=f"https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
    days=[ko.date()+dt.timedelta(days=i) for i in (-1,1)]
    b=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={days[0]:%Y%m%d}-{days[1]:%Y%m%d}&limit=200"
    raw_a,raw_b=get(a),get(b)
    score,eid=source_pair(doc,raw_a,json.loads(raw_b),resolve)
    return score,{"football_data_url":a,"espn_url":b,"espn_event_id":eid,
        "football_data_sha256":hashlib.sha256(raw_a).hexdigest(),
        "espn_sha256":hashlib.sha256(raw_b).hexdigest()}

def review(root,now=None,proof=git_proof,scorer=lookup,resolve=None):
    now=utc(now or dt.datetime.now(dt.timezone.utc));root=Path(root).resolve()
    if resolve is None:
        sys.path[:0]=[str(root),str(root/"experiments/263")]
        from sabah_official_fixture_gateway_263 import OfficialFixtureGateway
        resolve=OfficialFixtureGateway().resolve_id
    out=[];seen=set()
    for p in sorted((root/PREFIX).glob("*.json")):
        row={"receipt":p.name}
        try:
            if p.is_symlink() or not p.resolve().is_relative_to(root/PREFIX):raise Pending("UNSAFE_PATH")
            d=check_receipt(json.loads(p.read_text(encoding="utf-8")))
            row.update(match=d["match"],fixture_key=d["fixture_key"],payload_sha256=d["payload_sha256"])
            if d["fixture_key"] in seen:raise Pending("DUPLICATE_FIXTURE")
            seen.add(d["fixture_key"])
            if now<utc(d["kickoff_utc"])+dt.timedelta(hours=2):raise Pending("MATCH_NOT_READY")
            row["git_proof"]=proof(root,p,d)
            (h,a),evidence=scorer(d,resolve)
            score={"fixture_key":d["fixture_key"],"match_status":"FINAL","home_goals":h,"away_goals":a,
                   "observed_after_utc":now.isoformat()}
            result=evaluate_once([d],{"schema":SCORE_SCHEMA,"scores":[score]},now=now)
            if result["provisional_scored"]!=1:raise Pending("EVALUATOR_DID_NOT_SCORE")
            row.update(status="TWO_PUBLIC_SOURCES_AGREE_NOT_FEDERATION_VERIFIED",
                       evidence=evidence,score=[h,a],picks=result["records"][0]["picks"])
        except Exception as exc:
            row.update(status="PENDING",reason=str(exc)[:180])
        out.append(row)
    done=[r for r in out if r["status"]=="TWO_PUBLIC_SOURCES_AGREE_NOT_FEDERATION_VERIFIED"]
    return {"schema":"P0_HAFIZA_AUTO_POSTMATCH_RESEARCH_V1","asof_utc":now.isoformat(),
            "total":len(out),"verified_two_public_sources":len(done),"pending":len(out)-len(done),
            "hit_count":{s:sum(int(r["picks"][s]["correct"]) for r in done if s in r["picks"]) for s in ("P0","HAFIZA")},
            "records":out,"warning":"Read-only research. No federation claim. No receipt or history rewritten."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path.cwd());p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    root=a.root.resolve();target=a.out.resolve()
    if target.is_relative_to(root):p.error("report must be outside repository")
    result=review(root);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!="records"},ensure_ascii=False))
if __name__=="__main__":main()
