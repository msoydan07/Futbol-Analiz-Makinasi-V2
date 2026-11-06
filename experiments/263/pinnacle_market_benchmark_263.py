"""Read-only, same-time Pinnacle market benchmark for sealed B/C2/C3/M4 records.

Deliberately never changes the forecast, official decision, S1/S2, or pilot count.
Requires unique officially verified fixture, verified team identity, same bookmaker,
complete pre-KO 1X2 prices and strict ten-minute temporal alignment.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
from free_bulk_odds_263 import canonical,utc,SPORTS
from odds_provider_oddspapi_263 import expected_verified_team_names,cleanname
from market_fifth_baseline_263 import sealed_payload

SCHEMA="263_pinnacle_readonly_benchmark_v1"
MODELS=("B","C2","C3","M4")
MAX_GAP_SECONDS=600
MAX_UPDATE_AGE_SECONDS=600

class BenchmarkBlocked(ValueError):pass

def not_available(reason,forecast,bulk):
    return {"schema":SCHEMA,"status":"NO_VALID_SAME_TIME_PINNACLE_REFERENCE",
            "reason":reason,"forecast_sha256":forecast.get("payload_sha256"),
            "source_bulk_sha256":bulk.get("payload_sha256"),
            "independent_benchmark":True,"official_S1_S2_approved":False,
            "betting_authorized":False,"changes_forecast_or_decision":False,
            "official_pilot_count_increment":0}

def compare(forecast,bulk):
    """Accept only one exact source event and one all-sides Pinnacle market."""
    sealed_payload(forecast,"quad_forward_263_v1")
    if not isinstance(bulk,dict) or bulk.get("schema")!="263_free_bulk_external_odds_research_v1":
        raise BenchmarkBlocked("NOT_VERIFIED_BULK_SCHEMA")
    digest=bulk.get("payload_sha256")
    if not isinstance(digest,str) or hashlib.sha256(
        canonical({k:v for k,v in bulk.items() if k!="payload_sha256"})
        ).hexdigest()!=digest:
        raise BenchmarkBlocked("BULK_SHA_CHANGED")
    if (bulk.get("bookmaker_filter")!="pinnacle"
        or bulk.get("S1_S2_official_approved") is not False
        or bulk.get("betting_authorized") is not False):
        raise BenchmarkBlocked("UNFILTERED_OR_UNSAFE_ODDS_INPUT")
    fixture=forecast["fixture"]
    if fixture.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE":
        return not_available("OFFICIAL_FIXTURE_NOT_VERIFIED",forecast,bulk)
    league=fixture.get("league")
    if league not in SPORTS:return not_available("LEAGUE_OUT_OF_SCOPE",forecast,bulk)
    created=utc(forecast["created_at_utc"])
    observed=utc(bulk["checked_at_utc"])
    kickoff=utc(fixture["kickoff_utc"])
    if not (created<=observed<kickoff):
        return not_available("NOT_SAME_PREMATCH_WINDOW",forecast,bulk)
    if (observed-created).total_seconds()>MAX_GAP_SECONDS:
        return not_available("FORECAST_AND_PRICE_MORE_THAN_10_MIN_APART",forecast,bulk)
    if bulk.get("day_turkey")!=fixture.get("match_local_date"):
        return not_available("LOCAL_DATE_MISMATCH",forecast,bulk)
    try:
        names_home,names_away=expected_verified_team_names(forecast)
    except ValueError:
        return not_available("CANONICAL_TEAM_MAPPING_FAILED",forecast,bulk)
    entries=bulk.get("leagues",{}).get(league,[])
    candidates=[]
    for event in entries:
        if event.get("sport")!=SPORTS[league] or utc(event["kickoff_utc"])!=kickoff:
            continue
        if (cleanname(event.get("home_team")) not in names_home or
            cleanname(event.get("away_team")) not in names_away):
            continue
        candidates.append(event)
    if len(candidates)!=1:
        return not_available("NO_UNIQUE_EXACT_TEAM_AND_KICKOFF_MATCH",forecast,bulk)
    e=candidates[0]
    books=[x for x in e.get("bookmakers",[]) if x.get("bookmaker_key")=="pinnacle"]
    if len(books)!=1:
        return not_available("PINNACLE_MISSING_OR_DUPLICATE",forecast,bulk)
    all_1x2=[m for m in books[0].get("markets",[]) if m.get("market")=="h2h"]
    if len(all_1x2)!=1:
        return not_available("NO_SINGLE_COMPLETE_1X2_MARKET",forecast,bulk)
    m=all_1x2[0]
    if set(m.get("prices",{}))!={"H","D","A"}:
        return not_available("ONE_OR_MORE_PRICES_MISSING",forecast,bulk)
    last=utc(m["source_last_update_utc"])
    if (last>observed or (observed-last).total_seconds()>MAX_UPDATE_AGE_SECONDS
        or abs((last-created).total_seconds())>MAX_GAP_SECONDS):
        return not_available("PINNACLE_PRICE_NOT_IN_10_MIN_WINDOW",forecast,bulk)
    odds=m["prices"]
    if any(isinstance(odds[k],bool) or not isinstance(odds[k],(float,int))
           or not math.isfinite(odds[k]) or not 1<odds[k]<1000 for k in ("H","D","A")):
        return not_available("INVALID_SOURCE_PRICES",forecast,bulk)
    implied={k:1/odds[k] for k in ("H","D","A")}
    gross=sum(implied.values())
    if not 1<gross<1.3:
        return not_available("IMPLAUSIBLE_OR_NONPOSITIVE_BOOKMAKER_MARGIN",forecast,bulk)
    fair={k:implied[k]/gross for k in ("H","D","A")}
    model_rows={}
    for name in MODELS:
        model=forecast.get("model_predictions",{}).get(name,{})
        if model.get("status")!="AVAILABLE":
            return not_available("FOUR_ORIGINAL_MODELS_NOT_AVAILABLE",forecast,bulk)
        ps=model.get("goals",{}).get("markets",{}).get("1X2",{})
        if set(ps)!={"H","D","A"} or any(
            not isinstance(ps[k],(int,float)) or isinstance(ps[k],bool)
            or not math.isfinite(ps[k]) or not 0<=ps[k]<=1 for k in ("H","D","A")):
            return not_available("MODEL_1X2_MISSING_OR_INVALID",forecast,bulk)
        if abs(sum(ps.values())-1)>1e-4:
            return not_available("MODEL_1X2_NOT_NORMALIZED",forecast,bulk)
        model_rows[name]={
            "probabilities":{k:ps[k] for k in ("H","D","A")},
            "vs_pinnacle_pp":{k:round(100*(ps[k]-fair[k]),4) for k in ("H","D","A")}}
    result={"schema":SCHEMA,"status":"READ_ONLY_SAME_TIME_BENCHMARK",
        "market":"MS_1X2","no_vig_method":"PROPORTIONAL_NOT_TRUE_PROBABILITY",
        "provider":"The Odds API (the-odds-api.com)",
        "bookmaker":"pinnacle","bookmaker_verified_directly":False,
        "source_event_id":e.get("provider_event_id"),
        "match":e["home_team"]+" – "+e["away_team"],
        "league":league,"kickoff_utc":kickoff.isoformat(),
        "forecast_recorded_at_utc":created.isoformat(),
        "price_observed_at_utc":observed.isoformat(),
        "bookmaker_last_update_utc":last.isoformat(),
        "odds":{k:odds[k] for k in ("H","D","A")},
        "overround_pp":round(100*(gross-1),4),
        "pinnacle_no_vig_probabilities":fair,"models":model_rows,
        "forecast_sha256":forecast["payload_sha256"],
        "source_bulk_sha256":bulk["payload_sha256"],
        "independent_benchmark":True,"official_S1_S2_approved":False,
        "betting_authorized":False,"changes_forecast_or_decision":False,
        "official_pilot_count_increment":0,
        "accuracy_not_yet_established":True}
    result["payload_sha256"]=hashlib.sha256(canonical(result)).hexdigest()
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--forecast",required=True)
    p.add_argument("--bulk",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    f=json.loads(Path(args.forecast).read_text(encoding="utf-8"))
    bulk=json.loads(Path(args.bulk).read_text(encoding="utf-8"))
    result=compare(f,bulk)
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf-8") as out:
        json.dump(result,out,ensure_ascii=False,sort_keys=True,indent=2);out.write("\n")
    print(json.dumps({"status":result["status"],"reason":result.get("reason"),
                      "forecast_and_decision_unchanged":True},ensure_ascii=False))
if __name__=="__main__":main()
