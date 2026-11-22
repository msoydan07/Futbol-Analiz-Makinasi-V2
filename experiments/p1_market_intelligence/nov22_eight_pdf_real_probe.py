"""One-pass, 25 named 22-Nov-2026 real-lookup research probe; not official new seals.

Source: eight independently transcribed user PDFs, sha recorded per original
file. Reader cannot re-open private PDF bytes on GitHub. Do not present this
as canonical signed PDF acceptance or betting authorization. Never alter old
decisions. Model is computed only BEFORE kickoff, with official fixture gate.
"""
from __future__ import annotations
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"experiments/263"),
             str(ROOT/"experiments/p1_market_intelligence")]
from analyze_named_match_gate import run as live_gate
from forward_quad import predict_quad_from_verified_gate
from forward_empirical_baseline_263 import produce
from model_first_decision_263 import select, verified, SCHEMA as DECISION_SCHEMA
from p1_market import no_vig, analyze_prices, best_choices, MARKETS
from p2_market_alignment import _align
from check_active_decisions_263 import verify_active_policy

INPUT=Path(__file__).with_name("nov22_eight_pdf_research_input.json")
HISTORY=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
BASELINE=ROOT/"m4_quad_base/historical_results.csv"
AUDIT=ROOT/"data/results_only_263/4617_research_input_provenance.json"
M4_LOCK=ROOT/"experiments/263/m4_lock.json"
V4_LOCK=ROOT/"experiments/263/model_first_selection_lock_20261121_v4.json"
ORDER=("MS1","MSX","MS2","U25","O25","KG_VAR","KG_YOK")
TO_CANON=("MS1","MSX","MS2","UNDER_2.5","OVER_2.5","BTTS_YES","BTTS_NO")
TO_GROUP={"MS1":"MS","MSX":"MS","MS2":"MS",
          "UNDER_2.5":"OU25","OVER_2.5":"OU25",
          "BTTS_YES":"KG","BTTS_NO":"KG"}

def roundp(p): return round(p*100,4) if p is not None else None

def one_case(row, pdfsha):
    league,home,away,tstr,pdffile,*values=row
    fixture=f"{home} - {away}"
    odds=dict(zip(TO_CANON,values))
    offered={}
    unquoted=[k for k,v in odds.items() if v is None]
    for g,keys in MARKETS.items():
        if all(isinstance(odds.get(k),(float,int)) and odds[k]>1 for k in keys):
            offered[g]={k:odds[k] for k in keys}
    report={
        "fixture":fixture,"league":league,"home":home,"away":away,
        "date":"2026-11-22","kickoff_tr":tstr,"source_pdf":pdffile,
        "source_pdf_sha256":pdfsha,"source_original_pdf_bytes_on_runner":False,
        "manual_transcription_not_approved_first_PDF_snapshot":True,
        "model_forecast_persisted_to_approved_repo":False,
        "main_or_historical_seals_modified":False,
        "raw_odds":odds,"not_offered_selection":unquoted,
        "p0_status":"NOT_STARTED","model_status":"NOT_STARTED",
        "p2_status":"NOT_STARTED",
    }
    try:
        group_probs={g:no_vig(p)["probabilities"] for g,p in offered.items()}
        leader=best_choices(group_probs)["main"] if set(offered)==set(MARKETS) else None
        report["p0"]={"probabilities":group_probs,"complete_seven":leader is not None,
                      "top":leader,"unquoted":unquoted,
                      "missing_groups":sorted(set(MARKETS)-set(offered))}
        report["p0_status"]="COMPLETE_SEVEN" if leader else "INCOMPLETE_UNQUOTED"
        if leader:
            try:
                p1=analyze_prices(offered)
                report["p1"]={"top":p1["p1_select"]["main"],
                              "probabilities":p1["p1"]["p1_probabilities"],
                              "not_independent_football_evidence":True}
            except Exception as exc:
                report["p1"]={"status":"RESEARCH_CALC_ERROR","error":str(exc)[:170]}
        else:
            report["p1"]={"status":"NOT_RUN_INCOMPLETE_SEVEN"}
    except Exception as exc:
        report.update(p0_status="P0_PRICES_INVALID",p0_error=str(exc)[:200])
        return report
    kickoff=datetime.fromisoformat("2026-11-22T"+tstr+":00").replace(
        tzinfo=ZoneInfo("Europe/Istanbul")).astimezone(timezone.utc)
    now=datetime.now(timezone.utc)
    report["computed_utc"]=now.isoformat()
    if now>=kickoff:
        report["model_status"]="CUTOFF_ALREADY_PASSED"
        report["p2_status"]="NO_VALID_NEW_PREMATCH_MODEL"
        return report
    try:
        gate=live_gate(league,home,away)
        report["official_gate_status"]=gate.get("status")
        report["official_gate_reason"]=gate.get("reason")
        if gate.get("status")!="VERIFIED":
            report["model_status"]="OFFICIAL_FIXTURE_GATE_BLOCKED"
            report["p2_status"]="NO_VALID_NEW_PREMATCH_MODEL"
            return report
        if datetime.fromisoformat(gate["kickoff_utc"])!=kickoff:
            report["model_status"]="OFFICIAL_KICKOFF_MISMATCH"
            report["official_kickoff_utc"]=gate["kickoff_utc"]
            report["p2_status"]="NO_VALID_NEW_PREMATCH_MODEL"
            return report
    except Exception as exc:
        report.update(model_status="OFFICIAL_GATE_EXCEPTION",
                      model_error=f"{type(exc).__name__}: {exc}"[:230],
                      p2_status="NO_VALID_NEW_PREMATCH_MODEL")
        return report
    try:
        _,f=predict_quad_from_verified_gate(
            gate,str(HISTORY),str(ROOT/"tmp_25_probe"/"forecasts"),
            str(M4_LOCK),now=datetime.now(timezone.utc),
            base=str(BASELINE),source_audit=str(AUDIT))
        report["temporary_research_forecast_sha256"]=f["payload_sha256"]
        report["model_features"]={
            "historical_rows":f["data"]["league_history_rows"],
            "last_result":f["data"]["league_latest_result_date"],
            "model_statuses":{k:v["status"] for k,v in f["model_predictions"].items()}}
        b=produce(f,HISTORY,now=datetime.now(timezone.utc))
        lock=json.loads(V4_LOCK.read_text(encoding="utf-8"))
        d=select(f,b,lock,now=datetime.now(timezone.utc))
        verified(d,DECISION_SCHEMA)
        m=d.get("main_candidate")
        a=d.get("alternative_candidate")
        report["model"]={"status":d["status"],
                         "decision_sha256":d["payload_sha256"],
                         "forecast_sha256":f["payload_sha256"],
                         "main":m,"alternative":a}
        report["model_status"]="TEMP_RESEARCH_FROZEN_MODEL_DECISION" if m else "MODEL_NO_MAIN"
    except Exception as exc:
        report.update(model_status="MODEL_DATA_OR_POLICY_GATE_BLOCKED",
                      model_error=f"{type(exc).__name__}: {exc}"[:235],
                      p2_status="NO_VALID_NEW_PREMATCH_MODEL")
        return report
    try:
        if m:
            p2=_align(d,offered,
                     source={"kind":"EIGHT_USER_PDF_OFFLINE_MANUAL_RESEARCH",
                             "pdf_sha256":pdfsha,
                             "original_pdf_bytes_on_runner":False},
                     unquoted_market_keys=tuple(unquoted))
            report["p2"]={k:v for k,v in p2.items()
                          if k not in ("p0_probabilities",)}
            report["p2_status"]=p2["status"]
        else:
            report["p2_status"]="MODEL_NO_MAIN"
    except Exception as exc:
        report.update(p2_status="P2_COMPARISON_ERROR",
                      p2_error=f"{type(exc).__name__}: {exc}"[:235])
    return report

def main():
    verify_active_policy(ROOT)
    for p,sha in [
        (HISTORY,"637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89"),
        (BASELINE,"35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1")]:
        if hashlib.sha256(p.read_bytes()).hexdigest()!=sha:
            raise RuntimeError("HISTORICAL_INPUT_SHA_INVALID:"+str(p))
    data=json.loads(INPUT.read_text(encoding="utf-8"))
    assert len(data["rows"])==25 and len(set(x[0] for x in data["rows"]))==8
    result={"schema":"NOV22_EIGHT_LEAGUES_25_RESEARCH_P0_MAIN_P2_V1",
            "started_utc":datetime.now(timezone.utc).isoformat(),
            "source":"USER_UPLOADED_EIGHT_IDDAA_PDFS_MANUALLY_TRANSCRIBED",
            "original_pdf_bytes_on_runner":False,"new_official_sha_seals":False,
            "is_canonical_first_PDF_batch":False,"results":[]}
    out=Path("/tmp/eight_league_25_three_machine_research.json")
    try:
        for i,row in enumerate(data["rows"]):
            observation=one_case(row,data["pdf_sha256"][row[4]])
            result["results"].append(observation)
            print("EIGHT_PDF_ONE_MATCH",json.dumps({
                "match":i+1,"fixture":observation["fixture"],
                "market":observation["p0"].get("top") if observation.get("p0") else None,
                "model":observation.get("model",{}).get("main"),
                "status":observation["model_status"],"p2":observation["p2_status"],
                "reason":observation.get("model_error") or observation.get("official_gate_reason")
            },ensure_ascii=False),flush=True)
    finally:
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
        print("FINAL_COUNTS",json.dumps({
            "examined":len(result["results"]),
            "model_produced":sum(z["model_status"]=="TEMP_RESEARCH_FROZEN_MODEL_DECISION"
                for z in result["results"]),
            "p0_full":sum(z.get("p0",{}).get("complete_seven",False)
                for z in result["results"]),
            "p2_computed":sum(z["p2_status"] in ("UYUMLU","TERCIHLER_FARKLI","YUZDELER_UZAK",
                "MODEL_TOP_CHOICE_NOT_OFFERED_IN_PDF","P0_SEVEN_MARKETS_INCOMPLETE")
                for z in result["results"])
        },ensure_ascii=False),flush=True)

if __name__=="__main__":main()
