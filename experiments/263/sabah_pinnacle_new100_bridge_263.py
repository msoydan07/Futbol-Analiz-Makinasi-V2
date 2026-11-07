"""NEW100 sealed B/C2/C3/M4 -> Pinnacle research sidecar (no wager).

A new100 pilot forecast is committed FIRST. For SAME-MORNING prices, the
GitHub workflow must then commit + push ONE per-day per-league reservation
BEFORE a single The Odds API bookmaker=pinnacle h2h call.
Any absent/mismatched/stale quote stays PAS and consumes no extra credit.
This module itself has NO network code and never changes frozen forecasts,
decisions, user cohort counts or model weights.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from free_bulk_odds_263 import canonical,utc
from market_fifth_baseline_263 import sealed_payload
from pinnacle_market_benchmark_263 import compare,BenchmarkBlocked
from sabah_batch_263 import SCHEMA as BATCH_SCHEMA,sha as batch_sha
from sabah_pinnacle_credit_guard_263 import check_existing
from sabah_pinnacle_capture_263 import SNAP
from sabah_new100_commit_guard_263 import RECEIPT as RECEIPT_SCHEMA
from forward_c3 import read_aware

TR=ZoneInfo("Europe/Istanbul")
SCHEMA="263_NEW100_SAMEJOB_PINNACLE_RESEARCH_V1"
MODELS=("B","C2","C3","M4")
SIDES={"MS1":"H","MSX":"D","MS2":"A"}
class PriceBridgeBlocked(ValueError):pass

def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def digest(obj):return hashlib.sha256(canonical(obj)).hexdigest()
def seal(obj):
    x=dict(obj)
    x["payload_sha256"]=digest(x)
    return x
def validate_inputs(report,receipt,root):
    if report.get("schema")!=BATCH_SCHEMA or report.get("cohort")!="new100":
        raise PriceBridgeBlocked("NEW100_BATCH_ONLY")
    if report.get("payload_sha256")!=batch_sha({k:v for k,v in report.items() if k!="payload_sha256"}):
        raise PriceBridgeBlocked("BATCH_REPORT_SHA_CHANGED")
    if (receipt.get("schema")!=RECEIPT_SCHEMA
        or receipt.get("payload_sha256")!=batch_sha({k:v for k,v in receipt.items() if k!="payload_sha256"})
        or receipt.get("batch_report_sha256")!=report["payload_sha256"]
        or receipt.get("cohort")!="new100"
        or receipt.get("new_count")!=report.get("new_forecasts")
        or receipt.get("bookmaker_api_calls")!=0):
        raise PriceBridgeBlocked("NEW100_PILOT_RECEIPT_NOT_SEALED")
    if not 1<=receipt["new_count"]<=100 or len(receipt.get("records",[]))!=receipt["new_count"]:
        raise PriceBridgeBlocked("NEW100_COUNT_INVALID")
    paths={r["forecast_path"]:r for r in receipt["records"]}
    if len(paths)!=receipt["new_count"]:raise PriceBridgeBlocked("DUPLICATE_RECEIPT_PATHS")
    forecasts=[]
    for row in report["outcomes"]:
        if row.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
        rel=row.get("forecast_path")
        if not isinstance(rel,str) or not re.fullmatch(r"forward_morning_263/\d{4}-\d{2}-\d{2}/[a-f0-9]{24}\.json",rel):
            raise PriceBridgeBlocked("UNSAFE_FORECAST_PATH")
        if rel not in paths:raise PriceBridgeBlocked("FORECAST_NOT_IN_PILOT_RECEIPT")
        path=(root/rel).resolve()
        if not path.is_relative_to(root.resolve()):raise PriceBridgeBlocked("FORECAST_PATH_TRAVERSAL")
        f=read(path);sealed_payload(f,"quad_forward_263_v1")
        if row.get("forecast_sha256")!=f["payload_sha256"] or paths[rel].get("forecast_sha256")!=f["payload_sha256"]:
            raise PriceBridgeBlocked("FORECAST_LINK_MISMATCH")
        fixture=f.get("fixture",{})
        if (fixture.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE"
            or fixture.get("match_local_date")!=report["day_turkey"]
            or row.get("decision_status")!="RESEARCH_PAS"):
            raise PriceBridgeBlocked("SOURCE_OR_PAS_POLICY_INVALID")
        statuses={m:f.get("model_predictions",{}).get(m,{}).get("status") for m in MODELS}
        if (sum(s=="AVAILABLE" for s in statuses.values())<3
            or any(statuses[m]!="AVAILABLE" for m in ("C3","M4"))):
            raise PriceBridgeBlocked("MODELS_INSUFFICIENT")
        forecasts.append((row,f))
    if len(forecasts)!=receipt["new_count"]:raise PriceBridgeBlocked("FORECAST_COUNT_MISMATCH")
    return forecasts

def plan(report,receipt,root,ledger,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise PriceBridgeBlocked("AWARE_CLOCK_REQUIRED")
    now=now.astimezone(timezone.utc)
    root=Path(root)
    registered=validate_inputs(report,receipt,root)
    local=now.astimezone(TR)
    if local.date().isoformat()!=report["day_turkey"]:
        raise PriceBridgeBlocked("NO_HISTORICAL_OR_NEXT_DAY_PRICE_REQUEST")
    if not 5<=local.hour<13:
        raise PriceBridgeBlocked("ONLY_SAME_MORNING_ANALYSIS_05_TO_12_59_TURKEY")
    eligible={}
    blocked=[]
    for row,f in registered:
        league=f["fixture"]["league"]
        ko=utc(f["fixture"]["kickoff_utc"]);created=utc(f["created_at_utc"])
        minutes=(ko-now).total_seconds()/60
        age=(now-created).total_seconds()
        status=None
        if not 0<=age<=600:status="FORECAST_NOT_WITHIN_SAME_10_MINUTES"
        elif minutes<=2:status="KICKOFF_ALREADY_TOO_CLOSE_OR_PAST"
        else:
            if check_existing(ledger,league,now) is not None:
                status="DAILY_LEAGUE_PINNACLE_CREDIT_ALREADY_RESERVED"
            else:eligible.setdefault(league,[]).append(row["forecast_path"])
        if status:blocked.append({"league":league,"forecast_sha256":f["payload_sha256"],"reason":status})
    if len(eligible)>10:raise PriceBridgeBlocked("MAX_TEN_LEAGUES_EXCEEDED")
    return {"schema":"263_NEW100_PINNACLE_DAY_LEAGUE_PLAN_V1",
            "observed_at_utc":now.isoformat(),"day_turkey":report["day_turkey"],
            "cohort":"new100","reserve_only_after_forecast_committed":True,
            "quote_phase":"MORNING_ANALYSIS_TIME_NOT_T_MINUS_60",
            "morning_window_turkey":"05:00-12:59",
            "quote_max_age_from_forecast_seconds":600,
            "one_h2h_credit_max_per_league":True,"leagues":sorted(eligible),
            "eligible_forecasts_by_league":eligible,"skipped":blocked,
            "max_external_calls":len(eligible),"bookmaker":"pinnacle",
            "provider":"The Odds API","market":"h2h",
            "betting_authorized":False,"forecasts_unchanged":True}

def prequery(report,receipt,root,league,now=None):
    """Recheck same-morning live quote eligibility after pushed reservation."""
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise PriceBridgeBlocked("AWARE_CLOCK_REQUIRED")
    now=now.astimezone(timezone.utc)
    local=now.astimezone(TR)
    if local.date().isoformat()!=report.get("day_turkey"):
        raise PriceBridgeBlocked("WRONG_TURKEY_DAY_FOR_NETWORK_CALL")
    if not 5<=local.hour<13:
        raise PriceBridgeBlocked("ONLY_SAME_MORNING_ANALYSIS_05_TO_12_59_TURKEY")
    eligible=[]
    for row,f in validate_inputs(report,receipt,Path(root)):
        if f["fixture"]["league"]!=league:continue
        ko=utc(f["fixture"]["kickoff_utc"]);created=utc(f["created_at_utc"])
        if 0<=(now-created).total_seconds()<=600 and (ko-now).total_seconds()>120:
            eligible.append(f["payload_sha256"])
    if not eligible:raise PriceBridgeBlocked("LEAGUE_HAS_NO_SAME_MORNING_PREKICKOFF_FORECAST")
    return {"league":league,"eligible_forecast_sha256":eligible,
            "call_allowed_only_after_persisted_one_time_reservation":True,
            "as_of_utc":now.isoformat(),"bookmaker":"pinnacle","market":"h2h",
            "quote_phase":"MORNING_ANALYSIS_TIME_NOT_T_MINUS_60"}

def validate_snapshot(obj,league,day):
    if (obj.get("schema")!=SNAP or obj.get("league")!=league
        or obj.get("day_turkey")!=day or obj.get("bookmaker")!="pinnacle"
        or obj.get("market")!="h2h" or obj.get("provider")!="The Odds API"
        or obj.get("retry_automatically") is not False or obj.get("betting_authorized") is not False):
        raise PriceBridgeBlocked("UNTRUSTED_PINNACLE_DAILY_SNAPSHOT")
    if obj.get("payload_sha256")!=digest({k:v for k,v in obj.items() if k!="payload_sha256"}):
        raise PriceBridgeBlocked("SNAPSHOT_SHA_TAMPERED")
    return obj

def calibrated_sidecar(root,report,forecast,row,reference):
    day=report["day_turkey"];stem=Path(row["forecast_path"]).stem
    path=root/"experiments/263/sabah_research/new100"/day/stem/"decision.json"
    d=read(path);sealed_payload(d,"263_four_model_value_decision_research_v1")
    if (d.get("forecast_sha256")!=forecast["payload_sha256"]
        or d.get("payload_sha256")!=row.get("decision_sha256")
        or d.get("status")!="RESEARCH_PAS" or d.get("quote_sha256") is not None
        or d.get("main_candidate") is not None or d.get("betting_authorized") is not False):
        raise PriceBridgeBlocked("ORIGINAL_CALIBRATED_PAS_DECISION_MODIFIED")
    accepted={}
    fair=reference["pinnacle_no_vig_probabilities"]
    odds=reference["odds"]
    for diag in d.get("all_market_diagnostics",[]):
        market=diag.get("market")
        if market not in SIDES:continue
        prob=diag.get("calibrated_probability")
        support=diag.get("support_count",0)
        dev=diag.get("dev_brier_skill")
        anchor=diag.get("anchor_model")
        if (not isinstance(prob,(int,float)) or isinstance(prob,bool)
            or not math.isfinite(prob) or not 0<=prob<=1
            or anchor not in ("C3","M4")
            or not isinstance(dev,(int,float)) or not math.isfinite(dev) or dev<=0
            or not isinstance(support,int) or support<3):
            accepted[market]={"status":"NO_SUPPORTED_DEV_CALIBRATION","calibrated_probability":None}
            continue
        side=SIDES[market]
        accepted[market]={
            "status":"DESCRIPTIVE_CALIBRATED_PINNACLE_RESEARCH",
            "calibrated_probability":prob,
            "pinnacle_no_vig":fair[side],
            "difference_percentage_points":round(100*(prob-fair[side]),4),
            "illustrative_EV_percent":round(100*(prob*odds[side]-1),4),
            "pinnacle_decimal_odds":odds[side],
            "anchor_model":anchor,"support_count":support,
            "never_an_approved_bet":True}
    return accepted,d["payload_sha256"]

def render(report,receipt,root,snapshots):
    root=Path(root);snapshots=Path(snapshots)
    registered=validate_inputs(report,receipt,root)
    day=report["day_turkey"]
    items=[]
    for row,f in registered:
        league=f["fixture"]["league"]
        result={"league":league,"forecast_path":row["forecast_path"],
                "forecast_sha256":f["payload_sha256"],
                "kickoff_utc":f["fixture"]["kickoff_utc"],
                "status":"NO_VALID_SAME_TIME_PINNACLE_REFERENCE",
                "reason":"NO_DAILY_PINNACLE_SNAPSHOT",
                "odds_status":"NO_VERIFIED_CURRENT_ODDS",
                "research_only":True,"betting_authorized":False,
                "quote_phase":"MORNING_ANALYSIS_TIME_NOT_T_MINUS_60"}
        p=snapshots/day/(league+".json")
        if p.is_file():
            snap=validate_snapshot(read(p),league,day)
            result["daily_snapshot_sha256"]=snap["payload_sha256"]
            if snap.get("source_bulk") is None:
                result["reason"]=snap.get("reason") or "PROVIDER_FAILED_NO_RETRY"
            else:
                try:
                    matched=compare(f,snap["source_bulk"])
                except (BenchmarkBlocked,ValueError,KeyError,TypeError) as e:
                    result["reason"]="PINNACLE_COMPARISON_BLOCKED:"+type(e).__name__
                else:
                    if matched.get("status")=="READ_ONLY_SAME_TIME_BENCHMARK":
                        q,original_decision_sha=calibrated_sidecar(root,report,f,row,matched)
                        result.update(status="READ_ONLY_SAME_TIME_PINNACLE_AND_CALIBRATED",
                                      reason=None,
                                      comparison=matched,
                                      calibrated_MS_research=q,
                                      original_PAS_decision_sha256=original_decision_sha,
                                      odds_status="PINNACLE_API_OBSERVED_NOT_DIRECT_BOOKMAKER_VERIFIED")
                    else:result["reason"]=matched.get("reason","NOT_MATCHED")
        items.append(result)
    data={"schema":SCHEMA,"day_turkey":day,"cohort":"new100",
          "provider":"The Odds API","bookmaker":"pinnacle","market":"h2h",
          "quote_phase":"MORNING_ANALYSIS_TIME_NOT_T_MINUS_60",
          "price_is_sealed_as_morning_observation_not_t60":True,
          "official_S1_S2_approved":False,"betting_authorized":False,
          "no_pilot_count_change":True,"forecast_or_decision_modified":False,
          "not_a_market_based_bet_selection":True,
          "matches_compared":sum(x["status"]=="READ_ONLY_SAME_TIME_PINNACLE_AND_CALIBRATED" for x in items),
          "matches_total":len(items),
          "items":items}
    return seal(data)

def mobile(data):
    lines=["# 2.6.3 | Pinnacle SABAH MS piyasa kıyası | "+data["day_turkey"],"",
        "Kaynak: The Odds API üzerinde Pinnacle; doğrudan Pinnacle sitesinden bağımsız doğrulanmadı.",
        "**Bu rapor bahis önerisi DEĞİL.** Eski mühürlü tahmin/karar değişmedi.","",
        "| Lig | Tahmin SHA | Karşılaştırma | 1 / X / 2 marjsız | Kalibre 1/X/2 farkı |",
        "|---|---|---|---|---|"]
    for row in data["items"]:
        if row["status"]!="READ_ONLY_SAME_TIME_PINNACLE_AND_CALIBRATED":
            values="-";fair="-";diff=row["reason"]
        else:
            q=row["calibrated_MS_research"]
            vals=row["comparison"]["pinnacle_no_vig_probabilities"]
            fair=" / ".join(f"%{100*vals[k]:.1f}" for k in ("H","D","A"))
            diff="; ".join(k+" "+(f'{q[k]["difference_percentage_points"]:+.1f} pp'
                               if k in q and q[k].get("difference_percentage_points") is not None else "destek yok")
                           for k in SIDES)
        lines.append("| "+row["league"]+" | "+row["forecast_sha256"][:10]+" | "+
                     row["status"]+" | "+fair+" | "+diff+" |")
    lines+=["",str(data["matches_compared"])+"/"+str(data["matches_total"])+
            " maçta aynı-zaman koşullu Pinnacle kıyası var.",
            "Sadece sabah 05:00–12:59 TSİ alınan fiyatlar; tahmin-fiyat arası 10 dakikayı aşarsa kıyas yok.",
            "Pinnacle sabah fiyatı maç saatinde yeniden sorgulanmaz. KG ve gol çizgilerinde oran alınmadı; yalnız MS h2h.",
            "EV yüzdesi yalnız açıklayıcı senaryo, sistemin ana/alternatif bahis seçimi değildir.",
            "Orijinal karar **RESEARCH_PAS** ve yeni100 pilot sayacı değişmez."]
    return "\n".join(lines)+"\n"

def write_new(path,content):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8") as f:
        if isinstance(content,str):f.write(content)
        else:json.dump(content,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("plan","prequery","render","verify"))
    p.add_argument("--report",required=True);p.add_argument("--receipt",required=True)
    p.add_argument("--root",default=".");p.add_argument("--ledger",default="experiments/263/pinnacle_daily_reservations")
    p.add_argument("--snapshots",default="experiments/263/pinnacle_daily_snapshots")
    p.add_argument("--out",required=True);p.add_argument("--mobile")
    p.add_argument("--league")
    args=p.parse_args()
    report=read(args.report);receipt=read(args.receipt)
    if args.mode=="prequery":
        if not args.league:raise PriceBridgeBlocked("LEAGUE_REQUIRED")
        data=prequery(report,receipt,args.root,args.league)
        write_new(args.out,data)
        print("ONE_LEAGUE_CREDIT_SAFETY_PREQUERY_OK",args.league)
        return
    if args.mode=="plan":
        data=plan(report,receipt,args.root,args.ledger)
        write_new(args.out,data)
        print(json.dumps({"eligible_leagues":data["leagues"],"max_calls":data["max_external_calls"],
                          "skipped_count":len(data["skipped"]),"no_api_called":True},ensure_ascii=False))
        return
    data=render(report,receipt,args.root,args.snapshots)
    if args.mode=="verify":
        original=read(args.out)
        if original!=data:raise PriceBridgeBlocked("PINNACLE_REPORT_NOT_REPRODUCIBLE")
        if args.mobile and Path(args.mobile).read_text(encoding="utf-8")!=mobile(data):
            raise PriceBridgeBlocked("PINNACLE_MOBILE_NOT_REPRODUCIBLE")
        print("PINNACLE_NEW100_COMPARISON_SHA_OK",data["matches_compared"])
        return
    write_new(args.out,data)
    if args.mobile:write_new(args.mobile,mobile(data))
    print(json.dumps({"compared":data["matches_compared"],"total":data["matches_total"],
                      "no_changes_to_original_forecasts":True},ensure_ascii=False))
if __name__=="__main__":main()
