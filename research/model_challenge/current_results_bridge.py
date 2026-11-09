"""Read-only current-season results bridge, with immutable club-id matching.

Links 2026/27 Football-Data scores to the pinned 20-league OpenFootball
training archive only when BOTH source names resolve to the same trusted
2.6.3 canonical IDs. No fuzzy match, invented fixture or blind fallback.
The resulting research CSV is never written to existing 2.6.3 locations.

Fetch/publish policy is conservative: a league with incomplete names,
ambiguous IDs, malformed score, duplicate fixture, or stale results is
QUARANTINED, never silently completed with misleading data. A source
record itself is not a human attestation of the final result.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,urllib.request,sys
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from identity import Registry
from collect_team_candidates import LEAGUES,BASE
from xgb_live_inference import load_history

SCHEMA="MC_2627_SOURCE_IDENTITY_AUDIT_V1"
def read_football_data(url):
    req=urllib.request.Request(url,headers={"User-Agent":"FutbolAnalizResearch/1.0"})
    with urllib.request.urlopen(req,timeout=25) as response:
        payload=response.read(3_000_001)
        effective=response.geturl()
    if len(payload)>3_000_000 or effective!=url or not url.startswith("https://www.football-data.co.uk/"):
        raise ValueError("invalid or redirected source")
    text=payload.decode("utf-8-sig")
    rows=list(csv.DictReader(io.StringIO(text)))
    if not rows or not {"Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"}.issubset(rows[0]):
        raise ValueError("invalid score source columns")
    return rows,hashlib.sha256(payload).hexdigest()

def source_date(value):
    for fmt in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d"):
        try:return __import__("datetime").datetime.strptime(value.strip(),fmt).date()
        except ValueError:pass
    raise ValueError("unsupported date format")

def identity_map(archive,registry,league):
    """A research archive name maps to exactly one verified canonical ID."""
    indices=defaultdict(set)
    aliases=registry.data["aliases"]
    from identity import normalize
    for r in archive:
        if r["league"]!=league:continue
        for column in ("home","away"):
            name=r[column];tid=aliases.get(normalize(name))
            if tid: indices[tid].add(name)
    # Ambiguous historical aliases for one ID are not safe in current model's
    # per-name feature states; never merge names without a refit.
    return {k:next(iter(v)) for k,v in indices.items() if len(v)==1}, {
       k:sorted(v) for k,v in indices.items() if len(v)>1}

def bridge(archive,registry,league,source_rows,*,cutoff):
    from identity import normalize
    id_to_historical,ambiguous=identity_map(archive,registry,league)
    aliases=registry.data["aliases"]
    seen=set();mapped=[];failures=[];future=0
    for index,r in enumerate(source_rows):
        if not r.get("Date") and not r.get("HomeTeam") and not r.get("AwayTeam"):
            continue
        try:day=source_date(r["Date"])
        except (ValueError,TypeError):
            failures.append({"row":index,"reason":"INVALID_DATE"});continue
        if day>=cutoff:
            future+=1;continue
        if not r.get("FTHG") and r.get("FTHG")!="0":
            # Scheduled future fixture without a final result: not part of history.
            continue
        try:
            home,away=int(r["FTHG"]),int(r["FTAG"])
            expected="H" if home>away else "D" if home==away else "A"
            if min(home,away)<0 or max(home,away)>30 or r["FTR"]!=expected:
                raise ValueError("invalid final score")
            hi=aliases.get(normalize(r["HomeTeam"]))
            ai=aliases.get(normalize(r["AwayTeam"]))
            if not hi or not ai or hi==ai:
                raise ValueError("unresolved fixture identity")
            if hi in ambiguous or ai in ambiguous:
                raise ValueError("ambiguous archive identity")
            if hi not in id_to_historical or ai not in id_to_historical:
                raise ValueError("no exact historical archive team for identity")
            nameh=id_to_historical[hi];namea=id_to_historical[ai]
            key=(day.isoformat(),nameh,namea)
            if key in seen:raise ValueError("duplicated scored match")
            seen.add(key)
            mapped.append({"league":league,"season":"2026-27","date":day.isoformat(),
                 "home":nameh,"away":namea,"home_goals":str(home),
                 "away_goals":str(away),"source_file":"football-data-2627",
                 "source_sha256":"SOURCE_HASH_SET_AT_AGGREGATION"})
        except (ValueError,KeyError,TypeError) as err:
            failures.append({"row":index,"date":day.isoformat(),
              "home":str(r.get("HomeTeam",""))[:60],
              "away":str(r.get("AwayTeam",""))[:60],
              "reason":str(err)[:100]})
    return mapped,failures,{"unplayed_future":future,"ambiguous_archive_ids":len(ambiguous)}

def audit(archive_csv,registry_json,*,asof,fetch=read_football_data):
    history,_=load_history(archive_csv,asof)
    reg=Registry(registry_json)
    if reg.data.get("index_type")!="CANONICAL_REGISTRY_READ_ONLY_IDENTITY_CACHE_V1":
        raise ValueError("expected frozen 2.6.3 identity index")
    import importlib
    gate=importlib.import_module("experiments.263.mackolik_identity_gate_263")
    gate._validate_identity_source(reg.data)
    results=[];merged=[];digests={}
    for league,code in LEAGUES.items():
        url=f"{BASE}/2627/{code}.csv"
        try:
            source,checksum=fetch(url)
            mapped,errors,stats=bridge(history,reg,league,source,cutoff=asof)
            last=max((x["date"] for x in mapped),default=None)
            eligible=len(mapped)+len(errors)
            ok=(not errors and len(mapped)>=15 and last is not None and
                (asof-date.fromisoformat(last)).days<=21)
            for row in mapped:row["source_sha256"]=checksum
            results.append({"league":league,"url":url,"source_sha256":checksum,
               "status":"ACCEPTED" if ok else "BLOCKED",
               "mapped":len(mapped),"issues":len(errors),
               "latest_mapped_result":last,"issue_examples":errors[:6],**stats})
            if ok:
                merged.extend(mapped);digests[league]=checksum
        except Exception as e:
            results.append({"league":league,"url":url,"status":"BLOCKED",
              "reason":type(e).__name__+":"+str(e)[:150]})
    keys=set();overlap=0
    for r in history+merged:
        k=(r["league"],r["date"],r["home"],r["away"])
        if k in keys:overlap+=1
        keys.add(k)
    if overlap:
        raise ValueError("new results overlap existing archive")
    accepted=[r for r in results if r["status"]=="ACCEPTED"]
    report={"schema":SCHEMA,"asof_exclusive":asof.isoformat(),
      "archive_played_rows":len(history),"fresh_accepted_rows":len(merged),
      "league_sources_accepted":len(accepted),"league_sources_total":len(LEAGUES),
      "sources":results,"source_verified_for_training":False,
      "automatic_full_10league_release_ready":len(accepted)==10,
      "history_requires_independent_score_crosscheck":True,
      "model_production_promoted":False}
    return history,merged,report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",required=True)
    parser.add_argument("--registry",default="experiments/263/evidence/identity_index_263.json")
    parser.add_argument("--out",required=True)
    parser.add_argument("--cutoff",required=True,help="UTC calendar date exclusion")
    a=parser.parse_args()
    history,extra,report=audit(a.archive,a.registry,asof=date.fromisoformat(a.cutoff))
    output=Path(a.out);output.mkdir(parents=True,exist_ok=True)
    (output/"source_audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if report["automatic_full_10league_release_ready"]:
        fields=("league","season","date","home","away","home_goals","away_goals",
                "source_file","source_sha256")
        with (output/"combined_history.csv").open("w",encoding="utf8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(
                {k:r.get(k,"") for k in fields} for r in history+extra)
    print(json.dumps({"accepted_sources":report["league_sources_accepted"],
        "total_sources":report["league_sources_total"],
        "fresh_rows":report["fresh_accepted_rows"],
        "status":"READY_REVIEW" if report["automatic_full_10league_release_ready"]
                 else "PARTIAL_BLOCKED_WITH_AUDIT"},ensure_ascii=False))
if __name__=="__main__":main()
