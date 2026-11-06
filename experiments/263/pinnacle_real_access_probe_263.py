"""One-shot free-tier Pinnacle access probe; never a betting decision."""
import argparse,hashlib,json,os
from datetime import date,datetime,time,timezone,timedelta
from pathlib import Path
from free_bulk_odds_263 import SPORTS,TR,canonical,fetch,normalize_event,QuoteUnavailable

LEAGUES=("ENG1","GER1","TUR1")
SCHEMA="263_real_pinnacle_access_probe_v1"

def probe(day,now,key,getter=fetch):
    if not key:raise QuoteUnavailable("NO_FREE_THE_ODDS_API_KEY_CONFIGURED")
    now=now.astimezone(timezone.utc)
    today=now.astimezone(TR).date()
    if day not in (today,today+timedelta(days=1)):
        raise QuoteUnavailable("ONLY_TODAY_OR_TOMORROW_ALLOWED")
    start=datetime.combine(day,time.min,tzinfo=TR).astimezone(timezone.utc)
    end=datetime.combine(day+timedelta(days=1),time.min,tzinfo=TR).astimezone(timezone.utc)
    stamp=lambda x:x.strftime("%Y-%m-%dT%H:%M:%SZ")
    params={"bookmakers":"pinnacle","markets":"h2h","oddsFormat":"decimal",
            "commenceTimeFrom":stamp(start),"commenceTimeTo":stamp(end)}
    report={"schema":SCHEMA,"checked_at_utc":now.isoformat(),"day_turkey":day.isoformat(),
        "source":"The Odds API","bookmaker":"pinnacle","market":"h2h",
        "test_leagues":list(LEAGUES),"requests_made":0,
        "max_credits_if_all_nonempty":3,"remaining_credits":None,
        "league_results":{},"blocked":{},
        "result":"NO_VERIFIED_PINNACLE_PRICE_YET",
        "modifies_models_or_sealed_predictions":False,"betting_authorized":False}
    for league in LEAGUES:
        try:
            events,remaining=getter(SPORTS[league],params,key)
            report["requests_made"]+=1
            report["remaining_credits"]=remaining
            raw=len(events);accepted=[]
            for event in events:
                row=normalize_event(event,SPORTS[league],day,now,
                                    bookmaker_filter="pinnacle")
                if row and any(m.get("market")=="h2h" and set(m.get("prices",{}))=={"H","D","A"}
                    for book in row["bookmakers"] for m in book["markets"]):
                    accepted.append(row)
            report["league_results"][league]={"api_event_count":raw,
                                              "accepted_1x2_count":len(accepted),
                                              "examples":accepted[:5]}
            if accepted:
                report["result"]="LIVE_PINNACLE_ACCESS_VERIFIED_FOR_AT_LEAST_ONE_MATCH"
                break
        except QuoteUnavailable as exc:
            report["requests_made"]+=1
            report["blocked"][league]=str(exc)
            if str(exc) in ("ODDS_API_HTTP_401","ODDS_API_HTTP_403","ODDS_API_HTTP_429"):
                break
    report["payload_sha256"]=hashlib.sha256(canonical(report)).hexdigest()
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--day-turkey",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=probe(date.fromisoformat(a.day_turkey),
                 datetime.now(timezone.utc),os.environ.get("THE_ODDS_API_KEY"))
    target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as fp:
        json.dump(report,fp,ensure_ascii=False,indent=2,sort_keys=True);fp.write("\n")
    print(json.dumps({"result":report["result"],
        "requests_made":report["requests_made"],
        "remaining_credits":report["remaining_credits"],
        "league_counts":{k:v["accepted_1x2_count"]
                         for k,v in report["league_results"].items()},
        "blocked":report["blocked"]},ensure_ascii=False))
    if report["result"]!="LIVE_PINNACLE_ACCESS_VERIFIED_FOR_AT_LEAST_ONE_MATCH":
        raise SystemExit("PINNACLE_REAL_PRICE_NOT_YET_VERIFIED")

if __name__=="__main__":main()
