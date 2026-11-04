"""Real morning price archive for 2.6.3. Human-observed, NOT automatic odds scraping.

Saved before the T-60 forecast, then matched by league, exact team IDs and UTC kickoff.
The original market prices are NEVER misrepresented as current quotes.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from classification_odds_263 import GROUPS,odds_evidence
from forward_c3 import canonical_bytes,read_aware
from market_quote_intake_263 import ACCEPTED_DOMAINS
from market_fifth_baseline_263 import fixture_key,sealed_payload

SCHEMA="263_morning_market_snapshot_v1"
REQUEST="263_morning_market_request_v1"
REQUEST_RE=re.compile(r"experiments/263/morning_quote_requests/[A-Za-z0-9_-]+\.json")
GROUP_ORDER=("MS","KG","GOALS_1.5","GOALS_2.5","GOALS_3.5")
TR=ZoneInfo("Europe/Istanbul")
def sha(x):return hashlib.sha256(canonical_bytes(x)).hexdigest()
def domain(url):
    if not isinstance(url,str):raise ValueError("MORNING_SOURCE_URL_REQUIRED")
    u=urlsplit(url);host=(u.hostname or "").lower().removeprefix("www.")
    if u.scheme!="https" or host not in ACCEPTED_DOMAINS or u.username or u.password:
        raise ValueError("MORNING_SOURCE_DOMAIN_NOT_ALLOWED")
    return host
def identity(fx):
    if not isinstance(fx,dict) or set(fx)!={"league","home_id","away_id","match_local_date","kickoff_utc","official_fixture_url"}:
        raise ValueError("MORNING_FIXTURE_FIELDS_INVALID")
    if any(not isinstance(v,str) or not v for v in fx.values()) or fx["home_id"]==fx["away_id"]:
        raise ValueError("MORNING_FIXTURE_IDENTITIES_INVALID")
    ko=read_aware(fx["kickoff_utc"])
    official=urlsplit(fx["official_fixture_url"])
    if official.scheme!="https" or not official.hostname or official.username or official.password:
        raise ValueError("MORNING_OFFICIAL_FIXTURE_LINK_REQUIRED")
    return sha([fx["league"],fx["home_id"],fx["away_id"],ko.isoformat()])[:24]
def record_request(relative,root,output,now):
    now=read_aware(now.isoformat())
    if not REQUEST_RE.fullmatch(relative):raise ValueError("MORNING_REQUEST_PATH_INVALID")
    rp=(Path(root)/relative).resolve()
    if not rp.is_relative_to(Path(root).resolve()) or not rp.is_file():
        raise ValueError("MORNING_REQUEST_MISSING")
    req=json.loads(rp.read_text(encoding="utf-8"))
    keys={"schema","fixture","source_url","source_domain","reviewer","reviewed_at_utc",
          "observed_at_utc","visible_source_note","market_prices"}
    if not isinstance(req,dict) or set(req)!=keys or req["schema"]!=REQUEST:
        raise ValueError("MORNING_REQUEST_SCHEMA_INVALID")
    fx=req["fixture"];stem=identity(fx)
    observed=read_aware(req["observed_at_utc"]);reviewed=read_aware(req["reviewed_at_utc"])
    ko=read_aware(fx["kickoff_utc"])
    if not reviewed<=observed<=now<ko or now-observed>timedelta(minutes=30):
        raise ValueError("MORNING_OBSERVATION_NOT_NEW")
    local=observed.astimezone(TR)
    if not 5<=local.hour<13 or local.date().isoformat()!=fx["match_local_date"]:
        raise ValueError("NOT_SAME_DAY_MORNING_TURKEY")
    source=domain(req["source_url"])
    if req["source_domain"]!=source:raise ValueError("MORNING_SOURCE_MISMATCH")
    if not isinstance(req["reviewer"],str) or len(req["reviewer"].strip())<2:
        raise ValueError("MORNING_REVIEWER_MISSING")
    if not isinstance(req["visible_source_note"],str) or len(req["visible_source_note"].strip())<15:
        raise ValueError("MORNING_SOURCE_NOTE_MISSING")
    market_prices=req["market_prices"]
    if not isinstance(market_prices,dict) or not market_prices or not set(market_prices).issubset(GROUP_ORDER):
        raise ValueError("MORNING_GROUPS_INVALID")
    key=fixture_key(fx);quotes={}
    for group in GROUP_ORDER:
        if group not in market_prices:continue
        values=market_prices[group]
        if not isinstance(values,dict) or set(values)!=set(GROUPS[group]):
            raise ValueError("MORNING_INCOMPLETE_COUNTERMARKET")
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 1<v<=1000 for v in values.values()):
            raise ValueError("MORNING_PRICE_INVALID")
        q={"fixture_key":key,"market_group":group,"verification":"INDEPENDENTLY_CHECKED",
           "stage":"PREMATCH","source":source,"source_url":req["source_url"],
           "checked_at_utc":observed.isoformat(),
           "decimal_odds":{k:float(values[k]) for k in GROUPS[group]}}
        if any(odds_evidence(k,q,key,ko.isoformat(),observed.isoformat())["status"]!="COMPLETE_PREMATCH_QUOTES_SOURCE_FLAGGED_AS_CHECKED" for k in GROUPS[group]):
            raise ValueError("MORNING_MARKET_MARGINS_OR_OPPOSITES_INVALID")
        quotes[group]=q
    snap={"schema":SCHEMA,"fixture":fx,"fixture_key":key,
          "observed_at_utc":observed.isoformat(),"captured_at_utc":now.isoformat(),
          "source_domain":source,"source_review":{"method":"MANUAL_PUBLIC_PAGE",
              "reviewer":req["reviewer"].strip(),"reviewed_at_utc":reviewed.isoformat(),
              "visible_source_note":req["visible_source_note"].strip(),
              "original_request_path":relative,
              "original_request_sha256":hashlib.sha256(rp.read_bytes()).hexdigest()},
          "quotes":quotes,"not_current_at_T60":True,"research_only":True,
          "auto_scraped":False,"bookmaker_page_independently_rechecked_by_code":False}
    snap["payload_sha256"]=sha(snap)
    dest=Path(output)/fx["match_local_date"]/(stem+".json")
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf-8") as f:json.dump(snap,f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
    return {"status":"ARCHIVED_MORNING_SOURCE_SNAPSHOT","path":str(dest),
        "payload_sha256":snap["payload_sha256"],"fixture_key":key}
def read_for_forecast(f,root="experiments/263/morning_quotes_locked"):
    fx=f["fixture"]
    spec={k:fx[k] for k in ("league","home_id","away_id","match_local_date","kickoff_utc")}
    # A forecast may omit the display-only official_source (legacy test records).
    # The immutable key never uses a URL, only team IDs, league and exact UTC KO.
    stem=sha([fx["league"],fx["home_id"],fx["away_id"],
             read_aware(fx["kickoff_utc"]).isoformat()])[:24]
    file=Path(root)/fx["match_local_date"]/(stem+".json")
    return json.loads(file.read_text(encoding="utf-8")) if file.is_file() else None
def extract(snap,f,now):
    if snap is None:return {}
    now=read_aware(now.isoformat())
    sealed_payload(snap,SCHEMA)
    fx=f["fixture"];sf=snap["fixture"]
    if any(sf.get(k)!=fx.get(k) for k in ("league","home_id","away_id","match_local_date")):
        raise ValueError("MORNING_WRONG_FIXTURE")
    if read_aware(sf["kickoff_utc"])!=read_aware(fx["kickoff_utc"]):
        raise ValueError("MORNING_WRONG_KICKOFF")
    if snap.get("fixture_key")!=fixture_key(fx):raise ValueError("MORNING_WRONG_FIXTURE_KEY")
    if snap.get("not_current_at_T60") is not True or snap.get("research_only") is not True:
        raise ValueError("MORNING_FALSE_CURRENT_CLAIM")
    review=snap["source_review"]
    if review.get("method")!="MANUAL_PUBLIC_PAGE" or not review.get("reviewer") or not review.get("visible_source_note"):
        raise ValueError("MORNING_REVIEW_MISSING")
    seen=read_aware(snap["observed_at_utc"]);saved=read_aware(snap["captured_at_utc"])
    start=read_aware(f["created_at_utc"]);ko=read_aware(fx["kickoff_utc"])
    if not seen<=saved<=start<=now<ko or (saved-seen).total_seconds()>1800:
        raise ValueError("MORNING_PREMATCH_SEQUENCE_INVALID")
    if seen.astimezone(TR).date()!=saved.astimezone(TR).date() or not 5<=seen.astimezone(TR).hour<13:
        raise ValueError("MORNING_NOT_REALLY_MORNING")
    groupquotes=snap["quotes"]
    if not isinstance(groupquotes,dict) or not groupquotes:raise ValueError("MORNING_EMPTY_MARKETS")
    prices={}
    for group,q in groupquotes.items():
        if group not in GROUP_ORDER or q.get("market_group")!=group or q.get("fixture_key")!=snap["fixture_key"]:
            raise ValueError("MORNING_WRONG_MARKET_ID")
        if domain(q.get("source_url"))!=snap["source_domain"] or q.get("source")!=snap["source_domain"]:
            raise ValueError("MORNING_CROSS_BOOKMAKER_QUOTES")
        if read_aware(q["checked_at_utc"])!=seen:raise ValueError("MORNING_TIME_MISMATCH")
        for key in GROUPS[group]:
            val=odds_evidence(key,q,snap["fixture_key"],ko.isoformat(),seen.isoformat())
            if val["status"]!="COMPLETE_PREMATCH_QUOTES_SOURCE_FLAGGED_AS_CHECKED":
                raise ValueError("MORNING_OPPOSITE_MARKET_INVALID")
            prices[key]={"odds":val["decimal_odds"],"fair":val["no_vig"],
                "source":snap["source_domain"],"url":q["source_url"],
                "checked":seen.isoformat(),"age_class":"MORNING_ARCHIVE_NOT_CURRENT",
                "snapshot_sha256":snap["payload_sha256"]}
    return prices
def batch(manifest,root,out,report,now):
    requests=[s.strip() for s in Path(manifest).read_text(encoding="utf-8").splitlines() if s.strip()]
    if not 1<=len(requests)<=24 or len(requests)!=len(set(requests)):
        raise ValueError("INVALID_MORNING_REQUEST_BATCH")
    rows=[]
    for r in requests:
        try:rows.append({"request":r,**record_request(r,root,out,now)})
        except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as err:
            rows.append({"request":r,"status":"BLOCKED_MORNING_PRICE","reason":str(err)[:150]})
    result={"schema":"263_morning_batch_v1","items":rows,
      "accepted":sum(x["status"]=="ARCHIVED_MORNING_SOURCE_SNAPSHOT" for x in rows),
      "blocked":sum(x["status"]=="BLOCKED_MORNING_PRICE" for x in rows),
      "bookmaker_independent_network_check":False,"research_only":True}
    Path(report).parent.mkdir(parents=True,exist_ok=True)
    with Path(report).open("x",encoding="utf-8") as file:
        json.dump(result,file,ensure_ascii=False,sort_keys=True,indent=2);file.write("\n")
    return result
def conditional(forecast_report,lock_path,root=".",now=None):
    from four_model_value_policy_263 import decide,render
    now=now or datetime.now(timezone.utc)
    report=json.loads(Path(forecast_report).read_text(encoding="utf-8"))
    if report.get("schema")!="quad_named_match_batch_report_v1":raise ValueError("BAD_FOUR_MODEL_REPORT")
    lock=json.loads(Path(lock_path).read_text(encoding="utf-8"))
    saved=[]
    for row in report["outcomes"]:
        if row.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
        path=Path(root)/row["path"];f=json.loads(path.read_text(encoding="utf-8"))
        sealed_payload(f,"quad_forward_263_v1")
        if f["payload_sha256"]!=row["payload_sha256"]:raise ValueError("MORNING_FORECAST_SHA_MISMATCH")
        m=read_for_forecast(f,Path(root)/"experiments/263/morning_quotes_locked")
        if m is None:continue
        day=f["fixture"]["match_local_date"];stem=path.stem
        b=json.loads((Path(root)/"experiments/263/quad_research_links"/day/stem/"baseline.json").read_text(encoding="utf-8"))
        out=decide(f,b,lock,morning_snapshot=m,now=now)
        if out["morning_quote_sha256"]!=m["payload_sha256"] or out["quote_sha256"] is not None:
            raise ValueError("MORNING_CONDITIONAL_SHA_MISMATCH")
        dest=Path(root)/"experiments/263/quad_conditional_morning_decisions"/day/(stem+".json")
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open("x",encoding="utf-8") as file:
            json.dump(out,file,sort_keys=True,indent=2,ensure_ascii=False);file.write("\n")
        with dest.with_suffix(".md").open("x",encoding="utf-8") as file:file.write(render(out))
        saved.append({"path":str(dest),"status":out["status"],"decision_sha256":out["payload_sha256"]})
    return saved
def main():
    p=argparse.ArgumentParser();p.add_argument("mode",choices=("ingest","conditional"))
    p.add_argument("--manifest");p.add_argument("--root",default=".")
    p.add_argument("--out",default="experiments/263/morning_quotes_locked")
    p.add_argument("--report");p.add_argument("--forecast-report")
    p.add_argument("--dev-lock",default="experiments/263/forward_dev_calibration_lock_263.json")
    a=p.parse_args();now=datetime.now(timezone.utc)
    if a.mode=="ingest":
        if not a.manifest or not a.report:raise SystemExit("MORNING_MANIFEST_REPORT_REQUIRED")
        result=batch(a.manifest,a.root,a.out,a.report,now)
        print(json.dumps({"accepted":result["accepted"],"blocked":result["blocked"]}))
        if result["accepted"]==0:raise SystemExit("NO_VALID_MORNING_PRICE")
    else:
        if not a.forecast_report:raise SystemExit("FORECAST_REPORT_REQUIRED")
        print(json.dumps({"conditional_created":len(conditional(a.forecast_report,a.dev_lock,a.root,now))}))
if __name__=="__main__":main()
