#!/usr/bin/env python3
"""Build a Kâhin weekly envelope from a reviewed, explicit weekly input manifest.
This is a packaging gate, not a source collector or independent fixture verifier.
The branch operator must review all ten league fixture lists before creating input.json.
"""
import csv,datetime as dt,hashlib,io,json,re,sys
from pathlib import Path
from zoneinfo import ZoneInfo
L=set("ENG1 ENG2 GER1 ESP1 ITA1 FRA1 NED1 TUR1 POR1 BEL1".split())
TZ=ZoneInfo("Europe/Istanbul")
BASE=Path("mobile/weekly")
def require(ok,why):
    if not ok: raise ValueError(why)
def sha(b): return hashlib.sha256(b).hexdigest()
def utc(s):
    x=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
    require(x.tzinfo is not None,"timezone missing")
    return x.astimezone(dt.timezone.utc)
def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def build(m,now):
    start=dt.date.fromisoformat(m["week_start"]); end=start+dt.timedelta(days=6)
    require(start.weekday()==2 and start==now.astimezone(TZ).date(),"publish only on the actual Wednesday")
    require(m["schema"]=="KAHIN_REVIEWED_WEEKLY_INPUT_V1","manifest schema")
    require(set(m["coverage"])==L and all(v in ("LISTED","NO_FIXTURES") for v in m["coverage"].values()),"all ten leagues must be reviewed")
    require(set(m["league_source_urls"])==L and all(isinstance(u,str) and u.startswith("https://") for u in m["league_source_urls"].values()),"league source evidence")
    hp=m["history_path"]; pp=m["provenance_path"]
    require(re.fullmatch(r"data/research_263/[A-Za-z0-9_.-]+\.csv",hp) and re.fullmatch(r"data/research_263/[A-Za-z0-9_.-]+\.json",pp),"history scope")
    hist=Path(hp).read_bytes(); pv=read(pp)
    require(pv["source_snapshot_path"]==hp and sha(hist)==pv["source_snapshot_sha256"] and pv["all_source_scores_identical"] is True,"history evidence mismatch")
    registry=read("experiments/263/evidence/identity_index_263.json")
    rows=list(csv.DictReader(io.StringIO(hist.decode("utf-8"))))
    require(len(rows)==pv["usable_total_rows"],"history count")
    seen=set(); counts={l:0 for l in L}; latest={}
    for r in rows:
        date=dt.date.fromisoformat(r["match_date"]); h,a=int(r["home_goals"]),int(r["away_goals"])
        require(r["fixture_id"] not in seen and r["league"] in L and date<start and min(h,a)>=0 and r["result"]==("H" if h>a else "A" if h<a else "D") and r["home_id"]!=r["away_id"] and all(i in registry["teams"] for i in (r["home_id"],r["away_id"])),"history row")
        seen.add(r["fixture_id"]); counts[r["league"]]+=1;latest[r["league"]]=max(date,latest.get(r["league"],date))
    require(min(counts.values())>=60,"history coverage")
    fs=m["fixtures"]; require(isinstance(fs,list) and 1<=len(fs)<=300,"fixture count")
    keys=set()
    for f in fs:
        ko=utc(f["kickoff_utc"]); day=ko.astimezone(TZ).date()
        require(f["league"] in L and f["fixture_id"] and f["fixture_id"] not in seen and start<=day<=end and ko>now and f["home_id"]!=f["away_id"] and str(f["source_url"]).startswith("https://"),"fixture invalid")
        yr=day.year-(day.month<7); mem=registry["season_memberships"][f"{yr}-{yr+1}"][f["league"]]
        require(all(i in mem and i in registry["teams"] for i in (f["home_id"],f["away_id"])) and (day-latest[f["league"]]).days<=10,"fixture team/freshness")
        k=(f["league"],ko,f["home_id"],f["away_id"]);require(k not in keys,"duplicate fixture")
        seen.add(f["fixture_id"]);keys.add(k);f["kickoff_utc"]=ko.isoformat().replace("+00:00","Z")
    for l in L:require((m["coverage"][l]=="LISTED")==any(f["league"]==l for f in fs),"coverage conflict")
    source_note="Reviewed fixture manifest (source URLs retained); history: two public secondary score sources, not federation verification. "+json.dumps(m["league_source_urls"],ensure_ascii=False,sort_keys=True)
    p=dict(schema="KAHIN_WEEKLY_DATA_V1",week_start=start.isoformat(),week_end=end.isoformat(),created_at_utc=now.isoformat().replace("+00:00","Z"),source_note=source_note,history_csv=hist.decode("utf-8"),registry=registry,coverage=m["coverage"],fixtures=fs)
    raw=json.dumps(p,ensure_ascii=False,separators=(",",":"),allow_nan=False)
    return dict(schema="KAHIN_WEEKLY_ENVELOPE_V1",payload=raw,sha256=sha(raw.encode()))
if __name__=="__main__":
    pack=build(read(BASE/"input.json"),dt.datetime.now(dt.timezone.utc))
    out=BASE/"latest.json"
    if out.exists():
        old=read(out);require(old["sha256"]==sha(old["payload"].encode()),"previous package digest")
        p=json.loads(old["payload"]);n=json.loads(pack["payload"])
        require(p["week_start"]<n["week_start"],"same/older week must not overwrite published pack")
        prev={r["fixture_id"]:r for r in csv.DictReader(io.StringIO(p["history_csv"]))}
        new={r["fixture_id"]:r for r in csv.DictReader(io.StringIO(n["history_csv"]))}
        require(all(new.get(k)==v for k,v in prev.items()),"old history modified or lost")
    out.write_text(json.dumps(pack,ensure_ascii=False),encoding="utf-8")
    print("Kahin package created",pack["sha256"])
