"""Opt-in API bridge: OddsPapi iddaa pre-KO quote, no scraping, no synthetic live odds.

Never claims direct iddaa verification: an independent aggregator reports bookmaker
prices. Restricted iddaa feed requires explicit paid/unlocked key; without it PAS.
Only unique EXACT team+UTC fixture identity, live provider market catalogue,
full opposite prices, 10-minute observation, and genuine bookmaker fixture URL.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,re,unicodedata,urllib.error,urllib.parse,urllib.request
from datetime import datetime,timezone,timedelta
from pathlib import Path
from forward_c3 import canonical_bytes,read_aware
from market_fifth_baseline_263 import OBSERVATION_SCHEMA,fixture_key,sealed_payload
from classification_odds_263 import GROUPS,odds_evidence
from four_model_value_policy_263 import decide,render
from morning_quote_policy_263 import read_for_forecast

API="https://api.oddspapi.io/v4"
BOOK="iddaa"
SCHEMA="263_oddspapi_iddaa_attempt_v1"
TIME_TOLERANCE=timedelta(minutes=2)
UPDATE_MAX_AGE=timedelta(minutes=30)
GROUPS_ORDER=("MS","KG","GOALS_1.5","GOALS_2.5","GOALS_3.5")
GOAL_LINES={"GOALS_1.5":1.5,"GOALS_2.5":2.5,"GOALS_3.5":3.5}
class QuoteBlocked(ValueError):pass

def cleanname(s):
    if not isinstance(s,str):return ""
    return re.sub(r"[^a-z0-9]+","",unicodedata.normalize("NFKD",s.casefold())
                  .encode("ascii","ignore").decode())
def nowaware(t):
    if t is None:t=datetime.now(timezone.utc)
    if t.tzinfo is None:raise QuoteBlocked("AWARE_UTC_CLOCK_REQUIRED")
    return t.astimezone(timezone.utc)
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

def _get(endpoint,key,params):
    if not key:raise QuoteBlocked("NO_ODDSPAPI_KEY_CONFIGURED")
    query=urllib.parse.urlencode({**params,"apiKey":key})
    # Fixed endpoint and host. Never send user-supplied URLs, redirects, or keys to logs.
    url=API+"/"+endpoint+"?"+query
    req=urllib.request.Request(url,headers={"Accept":"application/json"})
    try:
        with urllib.request.build_opener(_NoRedirect()).open(req,timeout=15) as res:
            if res.geturl().split("?")[0] != API+"/"+endpoint:
                raise QuoteBlocked("API_REDIRECT_OR_HOST_MISMATCH")
            raw=res.read(3_000_001)
            if len(raw)>3_000_000:raise QuoteBlocked("ODDSPAPI_RESPONSE_TOO_LARGE")
    except urllib.error.HTTPError as exc:
        if exc.code==403:raise QuoteBlocked("ODDSPAPI_IDDAA_RESTRICTED_403") from None
        if exc.code==429:raise QuoteBlocked("ODDSPAPI_RATE_LIMITED_429") from None
        raise QuoteBlocked("ODDSPAPI_HTTP_"+str(exc.code)) from None
    except (urllib.error.URLError,TimeoutError):
        raise QuoteBlocked("ODDSPAPI_NETWORK_UNAVAILABLE") from None
    try:return json.loads(raw)
    except (TypeError,ValueError):raise QuoteBlocked("ODDSPAPI_INVALID_JSON") from None

def match_fixture(forecast,fixtures,now):
    if not isinstance(fixtures,list):raise QuoteBlocked("ODDSPAPI_FIXTURE_LIST_INVALID")
    fx=forecast["fixture"]
    ko=read_aware(fx["kickoff_utc"])
    expected=(cleanname(fx["home_id"]),cleanname(fx["away_id"]))
    if not all(expected):raise QuoteBlocked("UNRECOGNIZED_OFFICIAL_TEAM_ID")
    possible=[]
    for x in fixtures:
        if not isinstance(x,dict) or x.get("sportId")!=10 or x.get("statusId")!=0 or not x.get("hasOdds"):
            continue
        try:
            start=read_aware(x["startTime"])
            if abs(start-ko)>TIME_TOLERANCE:continue
        except (KeyError,TypeError,ValueError):continue
        # No fuzzy or swapped teams: ambiguous fixtures are blocked, not guessed.
        h={cleanname(x.get("participant1Name")),cleanname(x.get("participant1ShortName"))}
        a={cleanname(x.get("participant2Name")),cleanname(x.get("participant2ShortName"))}
        if expected[0] in h and expected[1] in a:
            possible.append(x)
    if len(possible)!=1:raise QuoteBlocked("NO_UNIQUE_EXACT_KICKOFF_TEAM_FIXTURE_MATCH")
    return possible[0]

def normalize_market_catalog(catalog):
    if not isinstance(catalog,list):raise QuoteBlocked("ODDSPAPI_MARKETS_INVALID")
    mappings={}
    for x in catalog:
        if not isinstance(x,dict) or x.get("sportId")!=10 or x.get("playerProp") is not False:
            continue
        if str(x.get("period","")).lower()!="fulltime":continue
        name=str(x.get("marketName","")).casefold().strip()
        names=[str(y.get("outcomeName","")).strip().lower() for y in x.get("outcomes",[]) if isinstance(y,dict)]
        group=None;lookup=None
        if name=="full time result" and names==["1","x","2"]:
            group="MS";lookup={"1":"MS1","x":"MSX","2":"MS2"}
        elif name=="both teams to score" and set(names)=={"yes","no"}:
            group="KG";lookup={"yes":"BTTS_YES","no":"BTTS_NO"}
        elif name=="over under full time" and set(names)=={"over","under"}:
            for group_candidate,handicap in GOAL_LINES.items():
                if x.get("handicap")==handicap:
                    group=group_candidate
                    lookup={"over":"OVER_"+str(handicap),"under":"UNDER_"+str(handicap)}
        if not group:continue
        ids={}
        for out in x["outcomes"]:
            rawname=str(out["outcomeName"]).strip().lower()
            key=lookup[rawname]
            ids[str(out["outcomeId"])]=key
        if len(ids)!=len(GROUPS[group]) or set(ids.values())!=set(GROUPS[group]):
            continue
        mappings.setdefault(group,[]).append((str(x["marketId"]),ids))
    # Duplicate market identifiers for same group are ambiguous; no silent choice.
    return {g:v[0] for g,v in mappings.items() if len(v)==1}

def _source_url(url):
    if not isinstance(url,str):raise QuoteBlocked("IDDAA_DIRECT_FIXTURE_LINK_REQUIRED")
    u=urllib.parse.urlsplit(url)
    host=(u.hostname or "").lower()
    if (u.scheme!="https" or host not in ("iddaa.com","www.iddaa.com")
        or u.username or u.password):
        raise QuoteBlocked("IDDAA_DIRECT_FIXTURE_LINK_REQUIRED")
    return url

def build_observation(forecast,fixture,odds,markets,now):
    now=nowaware(now)
    sealed_payload(forecast,"quad_forward_263_v1")
    fx=forecast["fixture"]
    if not read_aware(forecast["created_at_utc"])<=now<read_aware(fx["kickoff_utc"]):
        raise QuoteBlocked("NOT_PRE_KICKOFF")
    if (now-read_aware(forecast["created_at_utc"])).total_seconds()>600:
        raise QuoteBlocked("FORECAST_TOO_OLD_FOR_SAME_T60_OBSERVATION")
    if odds.get("fixtureId")!=fixture.get("fixtureId") or odds.get("sportId")!=10 or odds.get("statusId")!=0:
        raise QuoteBlocked("ODDSPAPI_WRONG_EVENT_OR_LIVE_STATUS")
    updated=read_aware(odds["updatedAt"])
    if updated>now+timedelta(seconds=20) or now-updated>UPDATE_MAX_AGE:
        raise QuoteBlocked("PROVIDER_EVENT_UPDATE_STALE_OR_FUTURE")
    section=odds.get("bookmakerOdds",{}).get(BOOK)
    if not isinstance(section,dict) or section.get("bookmakerIsActive") is not True or section.get("suspended") is not False:
        raise QuoteBlocked("IDDAA_BOOKMAKER_NOT_ACTIVE")
    link=_source_url(section.get("fixturePath"))
    table=section.get("markets")
    if not isinstance(table,dict):raise QuoteBlocked("NO_PROVIDER_MARKETS")
    mappings=normalize_market_catalog(markets)
    quotes={}
    for group in GROUPS_ORDER:
        if group not in mappings:continue
        market_id,sel_ids=mappings[group]
        market=table.get(market_id)
        if not isinstance(market,dict) or market.get("marketActive") is not True:continue
        received=market.get("outcomes")
        if not isinstance(received,dict) or set(received)!=set(sel_ids):continue
        values={}
        for oid,key in sel_ids.items():
            rec=received.get(oid,{}).get("players")
            if not isinstance(rec,dict) or len(rec)!=1:break
            row=next(iter(rec.values()))
            if not isinstance(row,dict) or row.get("active") is not True:break
            price=row.get("price")
            if isinstance(price,bool) or not isinstance(price,(int,float)) or not math.isfinite(price) or not 1<price<=1000:
                break
            changed=row.get("changedAt")
            if changed is None:break
            t=read_aware(changed)
            if t>now+timedelta(seconds=20):break
            values[key]=float(price)
        if set(values)!=set(GROUPS[group]):continue
        key=fixture_key(fx)
        quote={"fixture_key":key,"market_group":group,"stage":"PREMATCH",
            "verification":"PROVIDER_API_OBSERVED","source":"iddaa.com",
            "source_url":link,"checked_at_utc":now.isoformat(),"decimal_odds":values}
        statuses={s:odds_evidence(s,quote,key,fx["kickoff_utc"],now.isoformat()) for s in values}
        if all(x["status"]=="COMPLETE_PREMATCH_QUOTES_PROVIDER_API_OBSERVED" for x in statuses.values()):
            quotes[group]=quote
    if not quotes:raise QuoteBlocked("NO_COMPLETE_CURRENT_IDDAA_MARKET_PAIRS")
    digest=hashlib.sha256(canonical_bytes(odds)).hexdigest()
    obs={"schema":OBSERVATION_SCHEMA,"fixture_key":fixture_key(fx),
      "forecast_payload_sha256":forecast["payload_sha256"],
      "analysis_at_utc":now.isoformat(),"source_domain":"iddaa.com",
      "source_review":{"method":"ODDSPAPI_REST_RESPONSE",
          "reviewer":"AGGREGATOR_API_NOT_HUMAN",
          "reviewed_at_utc":now.isoformat(),
          "visible_source_note":"OddsPapi iddaa book-feed observation; no direct site recheck or guarantee",
          "provider":"oddspapi.io","provider_odds_sha256":digest,
          "provider_fixture_id":odds["fixtureId"],
          "provider_updated_at_utc":updated.isoformat(),
          "bookmaker_fixture_url":link},
      "quotes":quotes,"evidence_scope":"AGGREGATOR_API_NOT_DIRECT_BOOKMAKER_VERIFIED",
      "price_provider_api_connected":True,"true_webpage_price_not_proven_by_code":True,
      "betting_authorized":False}
    obs["payload_sha256"]=hashlib.sha256(canonical_bytes(obs)).hexdigest()
    return obs

def fetch_for_forecast(f,key,*,now=None,getter=_get):
    now=nowaware(now)
    if not key:raise QuoteBlocked("NO_ODDSPAPI_KEY_CONFIGURED")
    sealed_payload(f,"quad_forward_263_v1")
    ko=read_aware(f["fixture"]["kickoff_utc"])
    if now>=ko:raise QuoteBlocked("FIXTURE_ALREADY_STARTED")
    frm=(ko-timedelta(minutes=30)).isoformat().replace("+00:00","Z")
    to=(ko+timedelta(minutes=30)).isoformat().replace("+00:00","Z")
    fixtures=getter("fixtures",key,{"sportId":10,"from":frm,"to":to,"statusId":0,"hasOdds":"true"})
    fixture=match_fixture(f,fixtures,now)
    catalog=getter("markets",key,{"language":"en"})
    odds=getter("odds",key,{"fixtureId":fixture["fixtureId"],"bookmakers":"iddaa","language":"en","verbosity":3})
    return build_observation(f,fixture,odds,catalog,now)

def batch(report_file,dev_lock,*,key=None,now=None,
          baseline_dir="experiments/263/quad_research_links",
          observation_dir="experiments/263/market_quotes_locked",
          decision_dir="experiments/263/quad_priced_decisions"):
    now=nowaware(now)
    report=json.loads(Path(report_file).read_text(encoding="utf-8"))
    if report.get("schema")!="quad_named_match_batch_report_v1":
        raise QuoteBlocked("INVALID_FOUR_MODEL_BATCH_REPORT")
    lock=json.loads(Path(dev_lock).read_text(encoding="utf-8"))
    outputs=[]
    for item in report["outcomes"]:
        if item.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
        path=Path(item["path"])
        if not path.is_file():raise QuoteBlocked("NEW_FORECAST_FILE_MISSING")
        f=json.loads(path.read_text(encoding="utf-8"))
        sealed_payload(f,"quad_forward_263_v1")
        if f["payload_sha256"]!=item["payload_sha256"]:raise QuoteBlocked("BATCH_FORECAST_SHA_DIFFERENT")
        day=f["fixture"]["match_local_date"];stem=path.stem
        basefile=Path(baseline_dir)/day/stem/"baseline.json"
        if not basefile.is_file():raise QuoteBlocked("BASELINE_NOT_WRITTEN_SAME_JOB")
        try:
            obs=fetch_for_forecast(f,key,now=now)
            b=json.loads(basefile.read_text(encoding="utf-8"))
            result=decide(f,b,lock,obs,morning_snapshot=read_for_forecast(f),now=now)
            quote_dest=Path(observation_dir)/day/(stem+".json")
            dec_dest=Path(decision_dir)/day/(stem+".json")
            if quote_dest.exists() or dec_dest.exists():raise QuoteBlocked("PROVIDER_RECORD_ALREADY_PRESENT")
            quote_dest.parent.mkdir(parents=True,exist_ok=True)
            dec_dest.parent.mkdir(parents=True,exist_ok=True)
            with quote_dest.open("x",encoding="utf-8") as o:
                json.dump(obs,o,indent=2,sort_keys=True,ensure_ascii=False);o.write("\n")
            with dec_dest.open("x",encoding="utf-8") as o:
                json.dump(result,o,indent=2,sort_keys=True,ensure_ascii=False);o.write("\n")
            with dec_dest.with_suffix(".md").open("x",encoding="utf-8") as o:o.write(render(result))
            outputs.append({"path":str(path),"status":"AGGREGATOR_API_SOURCED_VALUE_DECISION_EXPERIMENTAL",
                "odds_sha256":obs["payload_sha256"],"decision_sha256":result["payload_sha256"],
                "market_groups":sorted(obs["quotes"])})
        except QuoteBlocked as e:
            outputs.append({"path":str(path),"status":"API_ODDS_UNAVAILABLE_RETAIN_NO_ODDS_PAS",
                "reason":str(e)})
    return {"schema":SCHEMA,"runtime_utc":now.isoformat(),
        "provider":"OddsPapi","bookmaker_requested":"iddaa",
        "restricted_feed_requires_approved_key":True,
        "direct_iddaa_site_independently_verified":False,
        "betting_authorized":False,
        "items":outputs}
def verify_precommit(report_file,*,now=None,
                     observation_dir="experiments/263/market_quotes_locked",
                     decision_dir="experiments/263/quad_priced_decisions"):
    """Git push safety. Reject stale/missing/cross-linked provider records before KO."""
    now=nowaware(now)
    report=json.loads(Path(report_file).read_text(encoding="utf-8"))
    if report.get("schema")!="quad_named_match_batch_report_v1":
        raise QuoteBlocked("BAD_FORECAST_BATCH_REPORT")
    checked=0
    for item in report["outcomes"]:
        if item.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
        fp=Path(item["path"])
        f=json.loads(fp.read_text(encoding="utf-8"))
        sealed_payload(f,"quad_forward_263_v1")
        day=f["fixture"]["match_local_date"];stem=fp.stem
        observation=Path(observation_dir)/day/(stem+".json")
        decided=Path(decision_dir)/day/(stem+".json")
        if observation.exists()!=decided.exists():
            raise QuoteBlocked("SINGLE_SIDED_PROVIDER_RECORD_CANNOT_PUSH")
        if not observation.exists():continue
        obs=json.loads(observation.read_text(encoding="utf-8"))
        sealed_payload(obs,OBSERVATION_SCHEMA)
        d=json.loads(decided.read_text(encoding="utf-8"))
        saved=d.pop("payload_sha256",None)
        if hashlib.sha256(canonical_bytes(d)).hexdigest()!=saved:
            raise QuoteBlocked("PROVIDER_DECISION_HASH_INVALID")
        if obs.get("evidence_scope")!="AGGREGATOR_API_NOT_DIRECT_BOOKMAKER_VERIFIED":
            raise QuoteBlocked("PROVIDER_SCOPE_CHANGED")
        if (obs["forecast_payload_sha256"]!=f["payload_sha256"]
            or d["forecast_sha256"]!=f["payload_sha256"]
            or d["quote_sha256"]!=obs["payload_sha256"]):
            raise QuoteBlocked("PROVIDER_DECISION_SOURCE_CHAIN_BROKEN")
        observed=read_aware(obs["analysis_at_utc"])
        kickoff=read_aware(f["fixture"]["kickoff_utc"])
        if not read_aware(f["created_at_utc"])<=observed<=now<kickoff:
            raise QuoteBlocked("PROVIDER_PRECOMMIT_NOT_PREMATCH")
        if (now-observed).total_seconds()>600:
            raise QuoteBlocked("PROVIDER_PRECOMMIT_ODDS_NOW_STALE")
        checked+=1
    return checked

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",required=True)
    p.add_argument("--dev-lock",default="experiments/263/forward_dev_calibration_lock_263.json")
    p.add_argument("--attempt-report")
    p.add_argument("--verify-precommit",action="store_true")
    args=p.parse_args()
    if args.verify_precommit:
        print(json.dumps({"provider_precommit_checked":
            verify_precommit(args.report)}))
        return
    if not args.attempt_report:
        raise SystemExit("ATTEMPT_REPORT_REQUIRED")
    value=batch(args.report,args.dev_lock,key=os.environ.get("ODDSPAPI_API_KEY"))
    target=Path(args.attempt_report)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as f:
        json.dump(value,f,indent=2,ensure_ascii=False,sort_keys=True);f.write("\n")
    print(json.dumps({"provider":value["provider"],"status":[x["status"] for x in value["items"]]}))
if __name__=="__main__":main()
