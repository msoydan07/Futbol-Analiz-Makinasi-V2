"""iddaa PDF FIRST -> 1 official lookup per leg -> existing B/C2/C3/M4.

No retracing prices on secondary bookmakers. Only 10 leagues. No changes to
the existing 96-match pilot and no model refit after outcome. Unavailable
official fixture or model input only blocks THAT row, never the full batch.
Live adapter one per match, executed concurrently to avoid sequential delays.
"""
from __future__ import annotations
import argparse,hashlib,importlib,json,math
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from iddaa_pdf_bulletin_263 import SCHEMA as INPUT_SCHEMA,TR
from iddaa_pdf_team_alias_preflight_263 import index_registry,resolve_label
from mackolik_identity_gate_263 import OFFICIAL_ADAPTERS,_official
from classification_odds_263 import canonical_markets
def read_aware(value):
    """Lightweight UTC parse; do not import numpy/M4 during PDF intake."""
    parsed=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if parsed.tzinfo is None:raise ValueError("AWARE_DATETIME_REQUIRED")
    return parsed.astimezone(timezone.utc)

SCHEMA="263_iddaa_pdf_first_official_gate_session_v1"
SELECT=("MS1","MSX","MS2","OVER_2.5","UNDER_2.5","BTTS_YES","BTTS_NO")
PDF_TO_MARKET={"MS1":"MS1","MSX":"MSX","MS2":"MS2",
               "O25_OVER":"OVER_2.5","O25_UNDER":"UNDER_2.5",
               "BTTS_YES":"BTTS_YES","BTTS_NO":"BTTS_NO"}
MARKET_GROUPS={
 "MS":("MS1","MSX","MS2"),
 "GOALS_2.5":("UNDER_2.5","OVER_2.5"),
 "KG":("BTTS_YES","BTTS_NO"),
}

def pdf_prices(row):
    if row.get("odds") is None:return {}
    return {market:float(row["odds"][pdfkey])
            for pdfkey,market in PDF_TO_MARKET.items()
            if row["odds"].get(pdfkey) is not None}

def market_no_vig(row):
    """No-vig only when all opposite sides are present and margin is plausible.
    Missing any one selection marks group as incomplete and never shifts column.
    """
    prices=pdf_prices(row);out={}
    for grp,keys in MARKET_GROUPS.items():
        if any(p not in prices for p in keys):
            out[grp]={"status":"PRICE_MISSING_ONE_OR_MORE_SIDES"}
            continue
        if any(not math.isfinite(prices[k]) or prices[k]<=1 for k in keys):
            out[grp]={"status":"INVALID_PRICE"};continue
        gross=sum(1/prices[k] for k in keys)
        if not (1<gross<1.30):
            out[grp]={"status":"PRICE_MARGIN_OUTSIDE_SAFE_RANGE","gross":gross}
            continue
        out[grp]={"status":"FULL_MARKET_QUOTE_AVAILABLE",
                  "margin_pp":100*(gross-1),
                  "no_vig":{k:(1/prices[k])/gross for k in keys},
                  "prices":{k:prices[k] for k in keys}}
    return out

def _check_official(observed,league,home_id,away_id,index,now):
    """Verify official adapter's parsed observation: no second site or
    source URL only evidence, exact teams, source, Turkish kickoff and freshness.
    """
    if not isinstance(observed,dict) or observed.get("status")!="VERIFIED_OFFICIAL_FIXTURE":
        return {"status":"OFFICIAL_FIXTURE_NOT_VERIFIED"}
    if not _official(observed.get("source_url"),league):
        return {"status":"OFFICIAL_SOURCE_HOST_UNTRUSTED"}
    home=resolve_label(league,observed.get("home"),index)
    away=resolve_label(league,observed.get("away"),index)
    if (home.get("team_id"),away.get("team_id"))!=(home_id,away_id):
        return {"status":"OFFICIAL_TEAM_ORDER_OR_ALIAS_MISMATCH"}
    try:
        ko=read_aware(observed["kickoff_utc"])
        checked=read_aware(observed["retrieved_at_utc"])
        if not checked<=now<ko or (now-checked).total_seconds()>86400:
            raise ValueError("OFFICIAL_CHECK_OR_KICKOFF_OUTSIDE_PREMATCH")
        if (ko-now).total_seconds()>8*86400:
            raise ValueError("OFFICIAL_KICKOFF_TOO_FAR_AWAY")
    except (KeyError,TypeError,ValueError,OverflowError) as exc:
        return {"status":"OFFICIAL_TIME_INVALID","detail":str(exc)[:100]}
    return {"status":"OFFICIAL_READY","kickoff_utc":ko.isoformat(),
            "retrieved_at_utc":checked.isoformat(),
            "source_url":observed["source_url"],
            "local_date_tr":ko.astimezone(TR).date().isoformat(),
            "local_time_tr":ko.astimezone(TR).strftime("%H:%M")}

def analyze_one(n,row,*,index,team_names,pdf_time,now,
                official_lookup=None,forecast_options=None,baseline_clock=None):
    output={"index":n,"league":row.get("league"),
            "pdf_home":row.get("home_label"),"pdf_away":row.get("away_label"),
            "match_date_tr":row.get("match_date_tr"),
            "kickoff_time_tr":row.get("kickoff_time_tr"),
            "pdf_page":row.get("page"),
            "pdf_row_status":row.get("status"),
            "prices":pdf_prices(row),"market_no_vig":market_no_vig(row),
            "price_capture_utc":pdf_time.isoformat(),
            "source_bookmaker":"iddaa.com",
            "pdf_name_mapping_only":True,"official_lookup_attempts":0,
            "model_forecast_created":False}
    if row.get("league") is None:
        output["status"]="SKIPPED_OUT_OF_10_LEAGUES";return output
    if row.get("odds") is None:
        output["status"]="ONE_ROW_PRICE_LAYOUT_REVIEW";return output
    league=row["league"]
    home=resolve_label(league,row.get("home_label"),index)
    away=resolve_label(league,row.get("away_label"),index)
    if home["status"]!="MAPPED" or away["status"]!="MAPPED":
        output["status"]="ONE_ROW_NAME_REVIEW"
        output["team_identity_reason"]=(home["status"],away["status"])
        return output
    h,a=home["team_id"],away["team_id"]
    if h==a:
        output["status"]="ONE_ROW_SAME_TEAM_REVIEW";return output
    output["home_id"],output["away_id"]=h,a
    home_official,away_official=team_names[h],team_names[a]
    if pdf_time>now:
        output["status"]="SOURCE_PDF_CAPTURE_AFTER_TRUSTED_CLOCK";return output
    # PDF shows Istanbul kickoff (e.g. 20:00) rather than source league TZ.
    # This is used only for pre-KO filtering, not as official fixture evidence.
    try:
        shown=datetime.fromisoformat(row["match_date_tr"]+"T"+row["kickoff_time_tr"])
        shown=shown.replace(tzinfo=TR).astimezone(timezone.utc)
    except (ValueError,TypeError,KeyError):
        output["status"]="ONE_ROW_UNREADABLE_KICKOFF";return output
    if not pdf_time<shown or not now<shown:
        output["status"]="KICKOFF_PASSED_OR_PDF_NOT_PREMATCH";return output
    try:
        if official_lookup is None:
            # Current page only. No stale week-11 article, price requery or
            # unchecked fallback to an old referee announcement.
            from iddaa_pdf_live_official_263 import lookup as live_official
            fn=lambda h,a:live_official(league,h,a,now=now)
        else:
            fn=official_lookup
        output["official_lookup_attempts"]=1
        observed=fn(home_official,away_official)
    except Exception as exc:
        output["status"]="ONE_ROW_OFFICIAL_ADAPTER_ERROR"
        output["error_type"]=type(exc).__name__
        return output
    verified=_check_official(observed,league,h,a,index,now)
    if verified["status"]!="OFFICIAL_READY":
        output["status"]="ONE_ROW_"+verified["status"]
        return output
    if (verified["local_date_tr"],verified["local_time_tr"])!=(
            row["match_date_tr"],row["kickoff_time_tr"]):
        output["status"]="ONE_ROW_OFFICIAL_PDF_TIME_OR_DATE_DIFFER"
        output["official_date_tr"]=verified["local_date_tr"]
        output["official_time_tr"]=verified["local_time_tr"]
        return output
    output["status"]="ONE_OFFICIAL_SOURCE_CONFIRMED"
    output["official"]=verified
    output["pdf_name_mapping_only"]=False
    # Workload is a separate read-only sidecar. The original official page was
    # already fetched for the match; NEVER fetch a second league/cup/odds page.
    # No sidecar may influence B/C2/C3/M4 probabilities or block a valid row.
    try:
        from iddaa_pdf_workload_263 import workload_for_pdf
        output["rotation_7day"]=workload_for_pdf(
            observed,verified,league,h,a,now)
    except (ValueError,KeyError,TypeError,OverflowError,ImportError):
        output["rotation_7day"]={
            "schema":"263_PDF_7DAY_WORKLOAD_V1",
            "status":"ADJACENT_SOURCE_REJECTED_DATA_INCOMPLETE",
            "model_probabilities_changed":False,
            "new_odds_network_calls":0,
            "new_official_network_calls":0}
    if not forecast_options:return output
    # Important: original pilot out-dir / old 96 sealed predictions untouched.
    # This is a NEW session-specific directory; the original forecasting
    # module still enforces its full history/M4/source SHA safety checks.
    try:
        from forward_quad import predict_quad_from_verified_gate
        gate={"status":"VERIFIED","league":league,"home_id":h,"away_id":a,
              "kickoff_utc":verified["kickoff_utc"],
              "source_url":verified["source_url"],
              "retrieved_at_utc":verified["retrieved_at_utc"]}
        target,forecast=predict_quad_from_verified_gate(
            gate,forecast_options["history"],forecast_options["out_dir"],
            forecast_options["lock"],now=now,
            base=forecast_options.get("baseline"),
            source_audit=forecast_options.get("source_acceptance"))
        output["model_forecast_created"]=True
        output["model_forecast_sha256"]=forecast["payload_sha256"]
        output["model_forecast_path"]=str(target)
        output["model_1x2_and_core_markets"]={}
        for model,item in forecast["model_predictions"].items():
            if item.get("status")=="AVAILABLE":
                marks=canonical_markets(item["goals"]["markets"])
                output["model_1x2_and_core_markets"][model]={k:marks[k] for k in SELECT}
            else:
                output["model_1x2_and_core_markets"][model]={"status":item.get("status")}
        output["status"]="FOUR_MODELS_FORECAST_SHA_CREATED"
        # Empirical baseline uses the SAME accepted-as-of history and the
        # SHA-sealed forecast. Store immediately, not at the end of a 20-game
        # batch where the strict 10-minute baseline seal could go stale.
        try:
            from forward_empirical_baseline_263 import produce as build_baseline
            baseline_now=baseline_clock() if baseline_clock is not None else now
            baseline=build_baseline(forecast,forecast_options["history"],now=baseline_now)
            baseline_root=Path(forecast_options.get("empirical_baseline_out_dir",
                "experiments/263/iddaa_pdf_empirical_baselines_263"))
            target_baseline=(baseline_root/forecast["fixture"]["match_local_date"]/
                             (target.stem+".json"))
            target_baseline.parent.mkdir(parents=True,exist_ok=True)
            with target_baseline.open("x",encoding="utf-8") as handle:
                json.dump(baseline,handle,sort_keys=True,ensure_ascii=False,indent=2)
                handle.write("\n")
            output["empirical_baseline_sha256"]=baseline["payload_sha256"]
            output["empirical_baseline_path"]=str(target_baseline)
        except (ValueError,KeyError,AssertionError,OSError,ImportError) as baseline_exc:
            output["empirical_baseline_status"]="BASELINE_RESEARCH_PROVENANCE_BLOCKED"
            output["empirical_baseline_reason"]=str(baseline_exc)[:160]
    except (ValueError,KeyError,AssertionError,OSError,ImportError) as exc:
        output["status"]="ONE_ROW_FOUR_MODEL_EVIDENCE_BLOCKED"
        output["model_error_type"]=type(exc).__name__
        output["model_reason"]=str(exc)[:180]
    return output

def run_session(bulletin,*,now=None,official_lookup=None,forecast_options=None,
                max_workers=5):
    if bulletin.get("schema")!=INPUT_SCHEMA:
        raise ValueError("IDDAA_PDF_SCHEMA_MISMATCH")
    if bulletin.get("source_domain")!="iddaa.com" or not bulletin.get("pdf_sha256"):
        raise ValueError("IDDAA_SOURCE_UNTRUSTED")
    fixed_clock=now is not None   # deterministic injected unit tests only
    now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    pdf_time=read_aware(bulletin["pdf_capture_utc"])
    index,names,_=index_registry()
    rows=bulletin["rows"]
    if not isinstance(rows,list) or len(rows)>300:
        raise ValueError("IMPLAUSIBLE_PDF_BATCH_SIZE")
    by_number=[None]*len(rows)
    def task(i,row):
        # For real execution use the actual per-row as-of clock, rather than
        # incorrectly backdating all forecasts to the start of a long batch.
        row_now=now if fixed_clock else datetime.now(timezone.utc)
        baseline_clock=(lambda:now) if fixed_clock else (lambda:datetime.now(timezone.utc))
        return analyze_one(i,row,index=index,team_names=names,
            pdf_time=pdf_time,now=row_now,official_lookup=official_lookup,
            forecast_options=forecast_options,baseline_clock=baseline_clock)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures={pool.submit(task,i,r):i for i,r in enumerate(rows)}
        for future in as_completed(futures):
            idx=futures[future]
            try:by_number[idx]=future.result()
            except Exception as exc:
                by_number[idx]={"index":idx,"status":"SINGLE_ROW_UNEXPECTED_ERROR",
                                "error_type":type(exc).__name__}
    return {"schema":SCHEMA,"pdf_sha256":bulletin["pdf_sha256"],
            "pdf_capture_utc":pdf_time.isoformat(),
            "session_created_utc":now.isoformat(),
            "source_bookmaker":"iddaa.com","bookmaker_reverification_calls":0,
            "official_source_checked_once_per_resolved_fixture":True,
            "forecast_and_price_are_separately_timestamped":True,
            "source_is_user_print_not_live_scraped":True,
            "modifies_original_96_pilot":False,
            "modifies_frozen_models":False,
            "n_rows":len(rows),
            "n_official":sum(isinstance(r.get("official"),dict) and
                 r["official"].get("status")=="OFFICIAL_READY"
                 for r in by_number),
            "n_forecast":sum(r.get("model_forecast_created") for r in by_number),
            "rows":by_number}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--intake-json",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--history")
    p.add_argument("--m4-lock",default="experiments/263/m4_lock.json")
    p.add_argument("--baseline")
    p.add_argument("--source-acceptance")
    p.add_argument("--forecast-out-dir",default="experiments/263/iddaa_pdf_forecasts_263")
    args=p.parse_args()
    bulletin=json.loads(Path(args.intake_json).read_text(encoding="utf-8"))
    options=None
    if args.history:
        # A unique session path prevents overwriting old immutable forecasts.
        pdf_short=bulletin["pdf_sha256"][:16]
        options={"history":args.history,"lock":args.m4_lock,
                 "baseline":args.baseline,"source_acceptance":args.source_acceptance,
                 "out_dir":str(Path(args.forecast_out_dir)/pdf_short),
                 "empirical_baseline_out_dir":str(
                    Path("experiments/263/iddaa_pdf_empirical_baselines_263")/pdf_short)}
    result=run_session(bulletin,forecast_options=options)
    output=Path(args.out);output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x",encoding="utf-8") as file:
        json.dump(result,file,ensure_ascii=False,indent=2,sort_keys=True)
        file.write("\n")
    print(json.dumps({"n_rows":result["n_rows"],"n_official":result["n_official"],
                      "n_forecast":result["n_forecast"],"out":str(output)}))

if __name__=="__main__":main()
