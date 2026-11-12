"""Safe read-only result discovery for already SHA-sealed 2.6.3 forecasts.

An external football-data.co.uk score is NOT an official federation attestation.
Research-web concordance is reported separately. No score is admitted into
sabah_postmatch_inputs, forecasts, model calibration or betting decisions.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,unicodedata,urllib.request
from urllib.parse import urlsplit
from collections import defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.error import URLError
from score_nov8_webreview_263 import score_1x2,binary,avg

ROOT=Path(__file__).resolve().parents[2]
CODES={"ENG1":"E0","ENG2":"E1","GER1":"D1","ESP1":"SP1","ITA1":"I1",
       "FRA1":"F1","NED1":"N1","TUR1":"T1","POR1":"P1","BEL1":"B1"}
FED={"Premier League":"ENG1","EFL":"ENG2","Bundesliga":"GER1",
     "LALIGA":"ESP1","Lega Serie A":"ITA1","LFP":"FRA1",
     "Eredivisie":"NED1","TFF":"TUR1","Liga Portugal":"POR1",
     "Pro League":"BEL1"}
MODELS=("B","C2","C3","M4")
URL="https://www.football-data.co.uk/mmz4281/2627/{div}.csv"
MAX_BYTES=3000000
SCHEMA="263_POSTMATCH_CSV_SOURCE_CANDIDATE_V1"
class Blocked(ValueError):pass

def norm(s):
    if not isinstance(s,str) or not s.strip():raise Blocked("EMPTY_TEAM_NAME")
    x=unicodedata.normalize("NFKD",s.casefold())
    x="".join(c for c in x if not unicodedata.combining(c))
    return " ".join(re.findall(r"\w+",x))

class Names:
    def __init__(self,root):
        self.parent={}
        for f in csv.DictReader((root/"data/official_team_names.csv").open(encoding="utf-8-sig",newline="")):
            if f["review_status"]=="VERIFIED" and f["federation"] in FED:
                self.join(FED[f["federation"]],f["source_name"],f["official_name"])
        for f in csv.DictReader((root/"data/team_aliases_reviewed.csv").open(encoding="utf-8-sig",newline="")):
            if f["league"] in CODES and f["source"] and f["evidence_url"].startswith("https://"):
                self.join(f["league"],f["source_name"],f["registry_name"])
    def get(self,k):
        if k not in self.parent:return k
        if self.parent[k]!=k:self.parent[k]=self.get(self.parent[k])
        return self.parent[k]
    def join(self,league,a,b):
        a=(league,norm(a));b=(league,norm(b))
        for k in (a,b):self.parent.setdefault(k,k)
        self.parent[self.get(a)]=self.get(b)
    def key(self,league,name):return self.get((league,norm(name)))

def stamp(s):
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None:raise Blocked("CLOCK_WITHOUT_OFFSET")
    return d.astimezone(timezone.utc)
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def game_date(s):
    for fmt in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d"):
        try:return datetime.strptime(s.strip(),fmt).date().isoformat()
        except ValueError:pass
    raise Blocked("BAD_CSV_DATE")

def sealed(root):
    found={}
    for path in sorted((root/"forward_morning_263").glob("*/*.json")):
        f=json.loads(path.read_text(encoding="utf-8"))
        if not re.fullmatch(r"[0-9a-f]{24}\.json",path.name) or f.get("schema")!="quad_forward_263_v1":
            raise Blocked("FORECAST_SCHEMA_OR_NAME_INVALID")
        h=f.get("payload_sha256")
        if not isinstance(h,str) or h!=digest({k:v for k,v in f.items() if k!="payload_sha256"}):
            raise Blocked("FORECAST_SHA_CHANGED")
        x=f["fixture"];league=x["league"]
        if (league not in CODES or x["match_local_date"]!=path.parent.name or
            x["fixture_verification"]!="VERIFIED_BY_LIVE_OFFICIAL_GATE"):
            raise Blocked("FIXTURE_NOT_VERIFIED")
        made,checked,ko=stamp(f["created_at_utc"]),stamp(x["source_checked_at_utc"]),stamp(x["kickoff_utc"])
        if not(made<ko and checked<ko and checked<=made+timedelta(seconds=60)):
            raise Blocked("NOT_REAL_PREMATCH_FORECAST")
        if h in found:raise Blocked("DUPLICATE_FORECAST")
        found[h]=f
    if len(found)>100:raise Blocked("NEW100_MAX_EXCEEDED")
    return found

def registered_names(root):
    names={}
    for path in sorted((root/"experiments/263/sabah_batch_reports").glob("new100_*.json")):
        doc=json.loads(path.read_text(encoding="utf-8"))
        if doc.get("cohort")!="new100" or doc.get("schema")!="SABAH_TOPLU_KAYIT_V1":
            raise Blocked("INVALID_BATCH_COHORT")
        for x in doc["outcomes"]:
            if x.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
            h=x["forecast_sha256"]
            if h in names:raise Blocked("DUPLICATE_BATCH_FORECAST")
            names[h]=x
    return names

def feed_rows(raw,league,names):
    data=csv.DictReader(io.StringIO(raw.lstrip("\ufeff")))
    if not {"Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"}.issubset(data.fieldnames or []):
        raise Blocked("MISSING_RESULT_CSV_COLUMNS")
    found=defaultdict(list)
    for lineno,row in enumerate(data,start=2):
        if not row.get("Date") or not row.get("HomeTeam") or not row.get("AwayTeam"):
            continue
        if (row.get("FTHG") or "").strip()=="" or (row.get("FTAG") or "").strip()=="":
            continue
        if row.get("Div") and row["Div"]!=CODES[league]:raise Blocked("INCORRECT_CSV_DIVISION")
        a,b=row["FTHG"].strip(),row["FTAG"].strip()
        if not (a.isdigit() and b.isdigit() and int(a)<=20 and int(b)<=20):raise Blocked("BAD_FULL_TIME_SCORE")
        h,g=int(a),int(b)
        outcome="H" if h>g else "D" if h==g else "A"
        if row["FTR"].strip()!=outcome:raise Blocked("SCORE_VS_FTR_CONFLICT")
        k=(game_date(row["Date"]),names.key(league,row["HomeTeam"]),names.key(league,row["AwayTeam"]))
        found[k].append({"score":[h,g],"csv_line":lineno})
    return found

def sources_for(root,names,leagues,fetcher):
    feeds={};status={}
    for league in sorted(leagues):
        url=URL.format(div=CODES[league])
        try:
            if fetcher is None:
                request=urllib.request.Request(url,headers={"User-Agent":"FutbolAnaliz263-Postmatch/1.0"})
                with urllib.request.urlopen(request,timeout=15) as res:
                    resolved=urlsplit(res.geturl())
                    original=urlsplit(url)
                    if not (resolved.scheme=="https" and
                            resolved.hostname in ("football-data.co.uk","www.football-data.co.uk") and
                            resolved.path==original.path and not resolved.query and
                            not resolved.username and not resolved.password and not resolved.port):
                        raise Blocked("UNEXPECTED_CSV_REDIRECT_HOST_OR_PATH")
                    data=res.read(MAX_BYTES+1)
            else:data=fetcher(url)
            if len(data)>MAX_BYTES:raise Blocked("EXTERNAL_CSV_TOO_LARGE")
            feeds[league]=feed_rows(data.decode("utf-8-sig"),league,names)
            status[league]={"status":"FETCHED","url":url,"sha256":hashlib.sha256(data).hexdigest()}
        except (URLError,TimeoutError,OSError,ValueError,UnicodeError,Blocked) as exc:
            status[league]={"status":"SOURCE_UNAVAILABLE","reason":str(exc)[:140]}
    return feeds,status

def previous_web_review(root,names):
    path=root/"experiments/263/nov8_webreview_results_263.json"
    if not path.is_file():return {}
    doc=json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema")!="263_NOV8_WEB_REVIEW_RESEARCH_ONLY_V1":raise Blocked("WEB_REVIEW_SCHEMA_INVALID")
    result={}
    for x in doc["rows"]:
        league=x["league"]
        k=(doc["day_turkey"],league,names.key(league,x["home"]),names.key(league,x["away"]))
        if k in result:raise Blocked("DUPLICATE_WEB_REVIEW")
        result[k]=x
    return result

def score_market(f,goals):
    result={}
    for model in MODELS:
        m=f.get("model_predictions",{}).get(model,{})
        if m.get("status")!="AVAILABLE":continue
        p=m["goals"]["markets"]
        s={"MS":score_1x2(p["1X2"],goals),
           "KG":binary(p["BTTS_YES"],int(goals[0]>0 and goals[1]>0))}
        for line in ("1.5","2.5","3.5"):
            s["OVER_"+line]=binary(p["OVER_"+line],int(sum(goals)>float(line)))
        result[model]=s
    return result

def evaluate(root=ROOT,*,now=None,fetcher=None,official_tff_fetcher=None):
    root=Path(root);now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise Blocked("CLOCK_NEEDS_TIMEZONE")
    now=now.astimezone(timezone.utc)
    names=Names(root)
    forecasts=sealed(root);named=registered_names(root)
    # Old Nov8 results are already stored. Resolve them by original SHA.
    # Never re-fetch the same finished scores on subsequent daily runs.
    # Explicit injected source tests still exercise the legacy live bridge.
    if fetcher is None and official_tff_fetcher is None:
        from postmatch_terminal_archive_263 import REL,checked,summary
        if len(forecasts)==40 and (root/REL).is_file():
            return summary(checked(root,forecasts,named),forecasts,score_market,avg)
    review=previous_web_review(root,names)
    if any(k not in named for k in forecasts):raise Blocked("SEAL_WITHOUT_BATCH_IDENTITY")
    feeds,source_status=sources_for(root,names,{f["fixture"]["league"] for f in forecasts.values()},fetcher)
    grouped=defaultdict(list);done=[];pending=[];counts=defaultdict(int)
    federation_network_checked=0
    for sha,f in sorted(forecasts.items()):
        x=f["fixture"];league=x["league"];b=named[sha]
        if b["league"]!=league or b["kickoff_utc"]!=x["kickoff_utc"]:
            raise Blocked("BATCH_IDENTITY_MISMATCH")
        date=x["match_local_date"]
        home,away=names.key(league,b["home"]),names.key(league,b["away"])
        key=(date,home,away);w=review.get((date,league,home,away))
        extra={"forecast_sha256":sha,"league":league,"home":b["home"],"away":b["away"],"day":date}
        rows=feeds.get(league,{}).get(key,[])
        if len(rows)>1:reason="DUPLICATE_SOURCE_MATCH"
        elif league not in feeds:reason="SOURCE_UNAVAILABLE"
        elif not rows:reason="NO_EXACT_RESULT"
        elif now<stamp(x["kickoff_utc"])+timedelta(minutes=90):reason="MATCH_NOT_FINISHED"
        elif w and (w["status"]!="FULL_TIME" or rows[0]["score"]!=[w["home_goals"],w["away_goals"]]):
            reason="WEB_REVIEW_CONFLICT"
        else:reason=None
        tff=None
        if (reason=="NO_EXACT_RESULT" and league=="TUR1" and
            w and w.get("status")=="FULL_TIME" and
            w.get("source_url")=="https://www.tff.org/Default.aspx?macId=317879&pageId=29" and
            (fetcher is None or official_tff_fetcher is not None)):
            # Dedicated named single-match fallback: never generalize arbitrary
            # missing CSV scores to a URL-only or team-name-only assertion.
            try:
                from postmatch_tff_one_match_263 import verify_one
                proof=verify_one(f,b,now=now,fetcher=official_tff_fetcher)
                if proof["score"]!=[w["home_goals"],w["away_goals"]]:
                    reason="WEB_REVIEW_CONFLICT"
                else:
                    tff=proof;reason=None
            except (ValueError,TypeError,KeyError,OSError,TimeoutError) as exc:
                # One failed independent source cannot fabricate any score.
                extra["tff_source_status"]="NOT_INDEPENDENTLY_VERIFIED"
                extra["tff_failure_type"]=type(exc).__name__
        if (reason is None and league=="TUR1" and w
            and w.get("status")=="FULL_TIME"
            and (fetcher is None or official_tff_fetcher is not None)):
            # Preserve original CSV + web research status unless an exact
            # pinned independent federation match page also proves score.
            try:
                from postmatch_tff_remaining_two_263 import PINS,url_for,verify_two
                if sha in PINS and w.get("source_url")==url_for(sha):
                    official=verify_two(f,b,now=now,fetcher=official_tff_fetcher)
                    if (official["score"]==rows[0]["score"] and
                        official["score"]==[w["home_goals"],w["away_goals"]]):
                        tff=official
                    else:extra["tff_source_status"]="OFFICIAL_SCORE_CONFLICT"
            except (ValueError,TypeError,KeyError,OSError,TimeoutError) as exc:
                extra["tff_source_status"]="NOT_INDEPENDENTLY_VERIFIED"
                extra["tff_failure_type"]=type(exc).__name__
        if reason:
            if reason=="NO_EXACT_RESULT" and w and w["status"]=="POSTPONED":reason="WEB_REPORTED_POSTPONED"
            counts[reason]+=1;pending.append({**extra,"status":reason});continue
        label=("OFFICIAL_TFF_NETWORK_READ_RESEARCH_NOT_HUMAN_ATTESTED" if tff
               else "TWO_SOURCE_RESEARCH_CONCORDANT_NOT_OFFICIAL" if w
               else "CSV_ONLY_PROVISIONAL")
        used_score=tff["score"] if tff else rows[0]["score"]
        scores=score_market(f,used_score)
        for model,metrics in scores.items():
            grouped[("ALL_PROVISIONAL",model)].append(metrics)
            grouped[(label,model)].append(metrics)
        counts[label]+=1
        if tff:federation_network_checked+=1
        done.append({**extra,"status":label,"score":used_score,
                     "csv_line":None if tff else rows[0]["csv_line"],
                     "csv_url":None if tff else source_status[league]["url"],
                     "csv_sha256":None if tff else source_status[league]["sha256"],
                     "official_network_evidence":tff,
                     "web_review_url":w["source_url"] if w else None})
    def agg(part):
        return {"n":len(part),**{m:avg([x[m] for x in part])
                 for m in ("MS","KG","OVER_1.5","OVER_2.5","OVER_3.5")}}
    classes=("ALL_PROVISIONAL","CSV_ONLY_PROVISIONAL","TWO_SOURCE_RESEARCH_CONCORDANT_NOT_OFFICIAL",
             "OFFICIAL_TFF_NETWORK_READ_RESEARCH_NOT_HUMAN_ATTESTED")
    return {"schema":"263_POSTMATCH_CSV_SOURCE_CANDIDATE_V1","created_at_utc":now.isoformat(),
        "registered":len(forecasts),"provisional_scored":len(done),"pending":len(pending),
        "human_attestations_written":0,"independent_federation_verified":federation_network_checked,
        "per_model":{c:{m:agg(grouped[(c,m)]) for m in MODELS} for c in classes},
        "sources":source_status,"status_counts":dict(counts),"rows":done,"pending_rows":pending,
        "forecast_modified":False,"models_retrained":False,"odds_api_calls":0,
        "limitations":["Football-data.co.uk is NOT an official league/federation source",
                       "Matching prior web research increases confidence but is NOT independent official network verification",
                       "Only exact date and reviewed team aliases accepted; missing or mismatched scores remain pending",
                       "One TFF direct public match-page reading is source evidence, not human attestation",
                       "Nothing enters the official human-attestation result file directory"]}

def mobile(r):
    lines=["# 2.6.3 — Maç sonrası günlük kaynak kontrolü","",
        "**Mühürlü:** "+str(r["registered"])+" · **Dış CSV ile eşleşen:** "+str(r["provisional_scored"])+" · **Bekleyen:** "+str(r["pending"]),"",
        "**Kaynak sınırı:** Dış CSV eşleşmeleri resmî değildir. TFF resmî sayfasından bağımsız okunan maç sayısı: "
        +str(r["independent_federation_verified"])+". İnsan onaylı resmî attestation: 0.","",
        "| Model | N | MS yön | MS Brier | KG yön | 2.5 Alt/Üst yön |",
        "|---|---:|---:|---:|---:|---:|"]
    for m in MODELS:
        z=r["per_model"]["ALL_PROVISIONAL"][m]
        lines.append(f"| {m} | {z['n']} | {z['MS']['direction_correct']}/{z['n']} | {z['MS']['brier']} | {z['KG']['direction_correct']}/{z['n']} | {z['OVER_2.5']['direction_correct']}/{z['n']} |")
    lines+=["","**Kaynak durumu:** "+str(r["status_counts"]),"",
      "Maç öncesi tahmin SHA'ları korunmuştur. M4 matematiği değişmedi. Değer/ROI iddiası yok."]
    return "\n".join(lines)+"\n"

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--out",required=True);a.add_argument("--mobile",required=True)
    args=a.parse_args()
    r=evaluate()
    Path(args.out).write_text(json.dumps(r,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    Path(args.mobile).write_text(mobile(r),encoding="utf-8")
    print(json.dumps({**{k:r[k] for k in ("registered","provisional_scored","pending","status_counts","sources")},"unresolved":r["pending_rows"]},ensure_ascii=False))
if __name__=="__main__":main()
