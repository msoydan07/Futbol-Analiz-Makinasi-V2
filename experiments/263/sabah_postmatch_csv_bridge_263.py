"""2.6.3 postmatch provisional bridge, strictly read-only.

Fetch FREE public Football-Data season CSVs. Join ONLY to existing SHA-sealed
new100 forecasts via original same-SHA batch metadata and date/team identities.
This is NOT independent official league/federation result verification and never
creates a human-attested result or modifies predictions.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,unicodedata,urllib.request
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from score_nov8_webreview_263 import score_1x2,binary,avg

ROOT=Path(__file__).resolve().parents[2]
CODES={"ENG1":"E0","ENG2":"E1","GER1":"D1","ESP1":"SP1",
       "ITA1":"I1","FRA1":"F1","NED1":"N1","TUR1":"T1",
       "POR1":"P1","BEL1":"B1"}
FED={"Premier League":"ENG1","EFL":"ENG2","Bundesliga":"GER1",
     "LALIGA":"ESP1","Lega Serie A":"ITA1","LFP":"FRA1",
     "Eredivisie":"NED1","TFF":"TUR1","Liga Portugal":"POR1",
     "Pro League":"BEL1"}
MODELS=("B","C2","C3","M4")
MARKETS=("MS","BTTS","OVER_1.5","OVER_2.5","OVER_3.5")
BASE="https://www.football-data.co.uk/mmz4281/2627"
MAX_BYTES=3000000
SCHEMA="263_NEW100_EXTERNAL_CSV_POSTMATCH_RESEARCH_V1"
class Blocked(ValueError):pass

def norm(s):
    if not isinstance(s,str) or not s.strip():raise Blocked("EMPTY_TEAM_NAME")
    s=unicodedata.normalize("NFKD",s.casefold())
    s="".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.findall(r"\w+",s))

class Aliases:
    def __init__(self,root):
        self.parent={}
        def join(league,a,b):
            a,b=(league,norm(a)),(league,norm(b))
            self.parent.setdefault(a,a);self.parent.setdefault(b,b)
            self.parent[self.find(a)]=self.find(b)
        with (root/"data/official_team_names.csv").open(encoding="utf-8-sig",newline="") as f:
            for x in csv.DictReader(f):
                if x["review_status"]=="VERIFIED" and x["federation"] in FED:
                    join(FED[x["federation"]],x["source_name"],x["official_name"])
        with (root/"data/team_aliases_reviewed.csv").open(encoding="utf-8-sig",newline="") as f:
            for x in csv.DictReader(f):
                if x["league"] in CODES and x["source"] and x["evidence_url"].startswith("https://"):
                    join(x["league"],x["source_name"],x["registry_name"])
    def find(self,x):
        if x not in self.parent:return x
        if self.parent[x]!=x:self.parent[x]=self.find(self.parent[x])
        return self.parent[x]
    def key(self,league,name):return self.find((league,norm(name)))

def aware(s):
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None:raise Blocked("TIMEZONE_REQUIRED")
    return d.astimezone(timezone.utc)
def sha(obj):
    data=json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()
def readjson(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def parse_date(d):
    for fmt in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d"):
        try:return datetime.strptime(d.strip(),fmt).date().isoformat()
        except ValueError:continue
    raise Blocked("SOURCE_DATE_NOT_PARSEABLE")

def read_seals(root):
    out={}
    for p in sorted((root/"forward_morning_263").glob("*/*.json")):
        if not re.fullmatch(r"[a-f0-9]{24}\.json",p.name):raise Blocked("INVALID_SHA_SEAL_FILENAME")
        f=readjson(p)
        if f.get("schema")!="quad_forward_263_v1" or sha({k:v for k,v in f.items() if k!="payload_sha256"})!=f.get("payload_sha256"):
            raise Blocked("INVALID_OR_TAMPERED_SEAL")
        x=f["fixture"]
        created=aware(f["created_at_utc"]);checked=aware(x["source_checked_at_utc"]);ko=aware(x["kickoff_utc"])
        if (x["league"] not in CODES or x["match_local_date"]!=p.parent.name
            or x.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE"
            or not(created<ko and checked<ko and checked<=created+timedelta(seconds=60))):
            raise Blocked("NO_VERIFIED_PREKICKOFF_FIXTURE")
        if f["payload_sha256"] in out:raise Blocked("DUPLICATE_SEALED_SHA")
        out[f["payload_sha256"]]=(f,p)
    if len(out)>100:raise Blocked("NEW100_LIMIT_EXCEEDED")
    return out

def batch_index(root,known):
    result={}
    for p in sorted((root/"experiments/263/sabah_batch_reports").glob("new100_*.json")):
        d=readjson(p)
        if d.get("cohort")!="new100" or d.get("schema")!="SABAH_TOPLU_KAYIT_V1":
            raise Blocked("BAD_BATCH_SCHEMA")
        for o in d["outcomes"]:
            if o.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
            s=o["forecast_sha256"]
            if s in result or s not in known:raise Blocked("BATCH_UNKNOWN_OR_DUPLICATE_SHA")
            f,filepath=known[s]
            if o["forecast_path"]!=str(filepath.relative_to(root)) or o["league"]!=f["fixture"]["league"] or o["kickoff_utc"]!=f["fixture"]["kickoff_utc"]:
                raise Blocked("BATCH_FORECAST_LINK_WRONG")
            if f["fixture"]["match_local_date"]!=d["day_turkey"]:
                raise Blocked("BATCH_DAY_MISMATCH")
            result[s]=o
    if set(result)!=set(known):raise Blocked("UNLINKED_NEW100_SHA")
    return result

def parse_source(text,league,aliases):
    reader=csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    if not {"Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"}.issubset(set(reader.fieldnames or [])):
        raise Blocked("SOURCE_REQUIRED_COLUMNS_MISSING")
    records=defaultdict(list)
    for rowno,row in enumerate(reader,start=2):
        if not row.get("Date") or not row.get("HomeTeam") or not row.get("AwayTeam"):
            continue
        if not (row.get("FTHG") or "").strip() or not (row.get("FTAG") or "").strip():
            continue
        if row.get("Div") and row["Div"].strip()!=CODES[league]:
            raise Blocked("SOURCE_LEAGUE_WRONG")
        h,a=(row[x].strip() for x in ("FTHG","FTAG"))
        if not h.isdigit() or not a.isdigit() or max(int(h),int(a))>20:
            raise Blocked("SOURCE_INVALID_SCORE")
        h,a=int(h),int(a)
        if row["FTR"].strip()!=("H" if h>a else "A" if h<a else "D"):
            raise Blocked("SOURCE_RESULT_CONTRADICTION")
        k=(parse_date(row["Date"]),aliases.key(league,row["HomeTeam"]),aliases.key(league,row["AwayTeam"]))
        records[k].append({"score":(h,a),"row":rowno})
    return records

def safe_csv_target(actual,requested):
    a,b=urlsplit(actual),urlsplit(requested)
    return (a.scheme=="https" and a.hostname in ("football-data.co.uk","www.football-data.co.uk")
            and a.username is None and a.password is None and a.port is None
            and a.path==b.path and not a.query and not a.fragment)

def fetch_csv(league,fetcher=None):
    url=f"{BASE}/{CODES[league]}.csv"
    if fetcher is None:
        def fetcher(url):
            req=urllib.request.Request(url,headers={"User-Agent":"FutbolAnaliz263-ResultResearch/1.0"})
            with urllib.request.urlopen(req,timeout=18) as x:
                if not safe_csv_target(x.geturl(),url):raise Blocked("CSV_REDIRECT_UNAPPROVED")
                return x.read(MAX_BYTES+1)
    raw=fetcher(url)
    if not isinstance(raw,bytes) or len(raw)>MAX_BYTES:raise Blocked("SOURCE_SIZE_INVALID")
    return {"url":url,"sha256":hashlib.sha256(raw).hexdigest()},raw.decode("utf-8-sig")

def old_review(root,aliases):
    p=root/"experiments/263/nov8_webreview_results_263.json"
    if not p.exists():return {}
    d=readjson(p)
    if d.get("schema")!="263_NOV8_WEB_REVIEW_RESEARCH_ONLY_V1":raise Blocked("OLD_REVIEW_SCHEMA_UNKNOWN")
    records={}
    for x in d["rows"]:
        k=(d["day_turkey"],x["league"],aliases.key(x["league"],x["home"]),aliases.key(x["league"],x["away"]))
        if k in records:raise Blocked("DUPLICATE_OLD_REVIEW")
        records[k]=x
    return records

def report(root=ROOT,*,now=None,fetcher=None):
    root=Path(root);now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise Blocked("NAIVE_AUDIT_NOW")
    now=now.astimezone(timezone.utc)
    aliases=Aliases(root);seals=read_seals(root)
    meta=batch_index(root,seals);review=old_review(root,aliases)
    leagues=sorted({x["fixture"]["league"] for x,_ in seals.values()})
    datasets={};sources={}
    for league in leagues:
        try:
            source,raw=fetch_csv(league,fetcher)
            datasets[league]=parse_source(raw,league,aliases)
            sources[league]={"status":"FETCHED_EXTERNAL_CSV","source":source}
        except (Blocked,URLError,OSError,UnicodeError,TimeoutError,ValueError) as exc:
            sources[league]={"status":"SOURCE_UNAVAILABLE_OR_REJECTED","reason":str(exc)[:180]}
    completed=[];pending=[];groups=defaultdict(list)
    for s,(f,path) in seals.items():
        x=f["fixture"];league=x["league"];o=meta[s];date=x["match_local_date"]
        pair=(date,aliases.key(league,o["home"]),aliases.key(league,o["away"]))
        witness=review.get((date,league,*pair[1:]))
        candidates=datasets.get(league,{}).get(pair,[])
        basic={"forecast_sha256":s,"league":league,"home":o["home"],"away":o["away"],
               "kickoff_utc":x["kickoff_utc"],"forecast_path":str(path.relative_to(root))}
        if len(candidates)>1:
            pending.append({**basic,"status":"DUPLICATE_SOURCE_FIXTURE"});continue
        if not candidates:
            status="SOURCE_UNAVAILABLE" if league not in datasets else "CSV_MISSING_OR_NAME_UNRESOLVED"
            if witness and witness["status"]=="POSTPONED":status="POSTPONED_PER_WEB_REVIEW"
            pending.append({**basic,"status":status});continue
        if now<aware(x["kickoff_utc"])+timedelta(minutes=110):
            pending.append({**basic,"status":"MATCH_STILL_WITHIN_NORMAL_DURATION"});continue
        score=candidates[0]["score"]
        if witness and (witness["status"]!="FULL_TIME" or score!=(witness["home_goals"],witness["away_goals"])):
            pending.append({**basic,"status":"CONFLICT_RESEARCH_AND_CSV"});continue
        kind="CSV_AND_WEB_REVIEW_AGREE_NOT_OFFICIAL" if witness else "CSV_ONLY_PROVISIONAL"
        models={}
        for model in MODELS:
            d=f["model_predictions"].get(model,{})
            if d.get("status")!="AVAILABLE":continue
            markets=d["goals"]["markets"]
            measures={"MS":score_1x2(markets["1X2"],score),
                      "BTTS":binary(markets["BTTS_YES"],int(min(score)>0))}
            for line in ("1.5","2.5","3.5"):
                measures["OVER_"+line]=binary(markets["OVER_"+line],int(sum(score)>float(line)))
            models[model]=measures
            groups[("ALL_PROVISIONAL",model)].append(measures)
            groups[(kind,model)].append(measures)
        completed.append({**basic,"status":kind,"score":list(score),"source":sources[league]["source"],
                          "csv_row":candidates[0]["row"],"web_review_url":witness["source_url"] if witness else None,
                          "models":models})
    sections={}
    for kind in ("ALL_PROVISIONAL","CSV_AND_WEB_REVIEW_AGREE_NOT_OFFICIAL","CSV_ONLY_PROVISIONAL"):
        sections[kind]={m:{k:avg([v[k] for v in groups[(kind,m)]]) for k in MARKETS} for m in MODELS}
    return {"schema":SCHEMA,"generated_at_utc":now.isoformat(),"registered":len(seals),
            "provisional_completed":len(completed),"pending":len(pending),
            "official_result_count":0,"human_attestation_generated":False,
            "source_status":sources,"scored":completed,"not_scored":pending,"by_model":sections,
            "model_retrained":False,"forecast_changed":False,"odds_api_calls":0,
            "warning":"EXTERNAL CSV PROVISIONAL ONLY; no officially verified result, no bet/ROI, never alter historical SHA or existing human attestation."}

def mobile(r):
    rows=["# 2.6.3 — Maç sonu ücretsiz sonuç köprüsü (ön kontrol)","",
          f"**SHA kayıt:** {r['registered']} · **CSV eşleşmiş:** {r['provisional_completed']} · **Bekleyen:** {r['pending']}",
          "**Resmî doğrulama:** 0 — bu rapor resmî skor teyidi DEĞİLDİR.","",
          "| Model | MS N | MS doğru | MS Brier | KG doğru | 2,5 doğru |",
          "|---|---:|---:|---:|---:|---:|"]
    for m in MODELS:
        z=r["by_model"]["ALL_PROVISIONAL"][m]
        rows.append(f"| {m} | {z['MS']['n']} | {z['MS']['direction_correct']} | {z['MS']['brier']} | {z['BTTS']['direction_correct']} | {z['OVER_2.5']['direction_correct']} |")
    rows+=["","Kaynağı eksik, çelişkili veya ertelenmiş maçlar puanlanmaz. M4 ve eski mühürler aynen kalır."]
    return "\n".join(rows)+"\n"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True);p.add_argument("--mobile",required=True)
    args=p.parse_args();r=report()
    Path(args.out).write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    Path(args.mobile).write_text(mobile(r),encoding="utf-8")
    print(json.dumps({"registered":r["registered"],"provisional_completed":r["provisional_completed"],
                      "pending":r["pending"],"source_status":{k:x["status"] for k,x in r["source_status"].items()},
                      "official_result_count":0},ensure_ascii=False))
if __name__=="__main__":main()
