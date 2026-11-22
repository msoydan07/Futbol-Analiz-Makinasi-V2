"""One-shot PDF-listed fixture model research without forging OFFICIAL gate.

Independent route for user supplied iddaa PDF if an external official fixture
crawler fails. Exact frozen B/C2/C3/M4 functions and v4 calibration, but NO
official fixture verification, NO signed model-first select(), NO official SHA
seal, NO bookmaker-price-driven football model, NO production mutation.

Source: user PDF + canonical club identity + accepted historical results only.
Refuse if team not resolved / not present in target league history, stale
results not audit-cleared, or kickoff already passed. Do not fabricate fixtures.
"""
from __future__ import annotations
import json, math, hashlib, sys
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from functools import lru_cache
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"experiments/263"),str(ROOT/"experiments/p1_market_intelligence")]
from identity import Registry
from team_name_resolver import resolve
from exp_263_batch import clean_rows,c1,fit_c3,predict_c3
from forward_quad import verify_snapshot,_b_lambdas,_safe_legacy_poisson_joint
from analysis_math_core import canonical_c2_lambda,score_market
from m4_integrated import use_lock,fit_m4,predict_m4,score_markets
from model_first_decision_263 import canonical,joint_poisson,GROUPS
from model_first_frozen_c3_calibration_263 import calibrated_binary_pair,verify_policy
from freshness_gap_guard_263 import review_gap
from full_match_eligibility_263 import full_match_rows
from p1_market import no_vig,best_choices,MARKETS
from check_active_decisions_263 import verify_active_policy

INPUT=Path(__file__).with_name("nov22_eight_pdf_research_input.json")
HISTORY=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
BASELINE=ROOT/"m4_quad_base/historical_results.csv"
AUDIT=ROOT/"data/results_only_263/4617_research_input_provenance.json"
REGISTRY=ROOT/"experiments/263/evidence/identity_index_263.json"
M4_LOCK=ROOT/"experiments/263/m4_lock.json"
V4_LOCK=ROOT/"experiments/263/model_first_selection_lock_20261121_v4.json"
OUT=Path("/tmp/eight_league_25_pdf_model_research_no_official_gate.json")
DAY="2026-11-22"

def base_rates(rows):
    n=len(rows)
    count=Counter()
    for r in rows:
        h=int(r["home_goals"]);a=int(r["away_goals"])
        count["MS1"]+=h>a;count["MSX"]+=h==a;count["MS2"]+=h<a
        count["OVER_2.5"]+=h+a>2.5;count["UNDER_2.5"]+=h+a<2.5
        count["BTTS_YES"]+=h>0 and a>0;count["BTTS_NO"]+=h==0 or a==0
    return {k:(count[k]+1)/(n+3 if k.startswith("MS") else n+2)
            for k in ("MS1","MSX","MS2","OVER_2.5","UNDER_2.5","BTTS_YES","BTTS_NO")}

def p0_from_row(raw):
    quoted={"MS1":raw[5],"MSX":raw[6],"MS2":raw[7],
            "UNDER_2.5":raw[8],"OVER_2.5":raw[9],
            "BTTS_YES":raw[10],"BTTS_NO":raw[11]}
    groups={g:{key:quoted[key] for key in keys}
            for g,keys in MARKETS.items()
            if all(isinstance(quoted[key],(float,int)) and quoted[key]>1 for key in keys)}
    probs={g:no_vig(v)["probabilities"] for g,v in groups.items()}
    top=best_choices(probs)["main"] if set(probs)==set(MARKETS) else None
    return quoted,probs,top

def one(row,all_rows,reg,lock,setting,acceptance):
    league,hn,an,tstr,file,*_=row
    kickoff=datetime.fromisoformat(DAY+"T"+tstr+":00").replace(
         tzinfo=ZoneInfo("Europe/Istanbul")).astimezone(timezone.utc)
    now=datetime.now(timezone.utc)
    quoted,probs,p0=p0_from_row(row)
    out={"fixture":f"{hn} - {an}","league":league,"time":tstr,"source_file":file,
         "date":DAY,"runner_created_at":now.isoformat(),"p0":p0,
         "p0_probabilities":probs,"odds":quoted,
         "source_grade":"USER_IDDAA_PDF_TRANSCRIPTION_NOT_OFFICIAL_FEDERATION_PROOF",
         "official_fixture_verified":False,"official_seal_created":False,
         "model_status":"NOT_STARTED","p2_status":"NO_MODEL"}
    if now>=kickoff:
        out["model_status"]="MATCH_STARTED_BEFORE_THIS_RESEARCH_RUN"
        return out
    try:
        hid=resolve(reg,league,hn);aid=resolve(reg,league,an)
        if hid==aid:raise ValueError("HOME_AWAY_RESOLVED_TO_IDENTICAL_CLUB")
        out["resolved_club_ids"]={"home":hid,"away":aid}
    except (KeyError,ValueError) as e:
        out.update(model_status="UNRESOLVED_CANONICAL_TEAM_ID",
                   model_error=str(e)[:190])
        return out
    raw=[r for r in all_rows if r["league"]==league and r["match_date"]<DAY]
    if any(r["league"]==league and r["match_date"]>=DAY for r in all_rows):
        out["model_status"]="HISTORICAL_RESULTS_CONTAIN_FUTURE_MATCH"
        return out
    past,excluded,policy=full_match_rows(raw)
    if len(past)<120:
        out.update(model_status="MISSING_LEAGUE_HISTORY",historical_n=len(past))
        return out
    hist_home=sum(r["home_id"]==hid or r["away_id"]==hid for r in past)
    hist_away=sum(r["home_id"]==aid or r["away_id"]==aid for r in past)
    out["historical_team_matches"]={"home":hist_home,"away":hist_away}
    out["historical_n"]=len(past)
    out["historical_last_result"]=max(r["match_date"] for r in past)
    if not hist_home or not hist_away:
        out["model_status"]="NO_HISTORICAL_CONTEXT_FOR_A_CLUB"
        return out
    try:
        freshness=review_gap(raw,league,DAY,now=now)
        out["freshness_status"]=freshness.get("status")
        if freshness["age_days"]>10 and freshness["status"]!="BOUNDED_GAP_NO_MISSING_RESULTS_IN_PUBLIC_FEED_RESEARCH_ONLY":
            out["model_status"]="STALE_HISTORICAL_INPUT_GATE"
            return out
    except Exception as e:
        out.update(model_status="FRESHNESS_EVIDENCE_FAILED",model_error=str(e)[:150])
        return out
    b=base_rates(past)
    try:
        fit=fit_m4(past,league,DAY,setting)
        ml=predict_m4(fit,hid,aid)
        if ml is None:raise ValueError("M4_NO_VALID_PAIR_LAMBDAS")
        m4raw=score_markets(*ml)
        m4=canonical(m4raw["markets"])
        theta=lock["m4_joint_calibration_august"]
        lh=max(.05,min(5.,math.exp(theta[0]+theta[2]*math.log(ml[0]))))
        la=max(.05,min(5.,math.exp(theta[1]+theta[2]*math.log(ml[1]))))
        ms=joint_poisson(lh,la)
        fit3=fit_c3(past)
        cl=predict_c3(fit3,hid,aid) if fit3 else None
        c3raw=_safe_legacy_poisson_joint(*cl)[0] if cl is not None else None
        c3=canonical(c3raw["markets"]) if c3raw else None
        if c3 is None:raise ValueError("FROZEN_C3_MISSING")
        v={"MS":{k:ms[k] for k in GROUPS["MS"]}}
        cp=lock["calibration_v4"]
        verify_policy(cp)
        for fam,pos,neg in (("KG","BTTS_YES","BTTS_NO"),
                            ("O25","OVER_2.5","UNDER_2.5")):
            p_yes,p_no=calibrated_binary_pair(c3[pos],b[pos],pos,cp)
            v[fam]={pos:p_yes,neg:p_no}
        all_chosen=[{"market":k,"family":fam,"anchor_model":"M4" if fam=="MS" else "C3",
                      "calibrated_probability":round(p,10)}
                     for fam,vals in v.items() for k,p in vals.items()]
        ranked=sorted(all_chosen,key=lambda x:(-x["calibrated_probability"],x["market"]))
        top=ranked[0]
        alt=next((x for x in ranked[1:] if x["family"]!=top["family"]),None)
        out["main"]=top;out["alternative"]=alt
        out["model_seven"]={r["market"]:r["calibrated_probability"] for r in ranked}
        out["model_status"]="RESEARCH_MODEL_CALCULATED_FROM_USER_PDF_FIXTURE_NO_OFFICIAL_SEAL"
        out["math_source"]="FROZEN_263_FITS_AND_V4_CALIBRATION_NOT_SELECT_SIGNATURE"
    except Exception as e:
        out.update(model_status="MODEL_MATH_OR_DATA_ERROR",
                   model_error=f"{type(e).__name__}:{e}"[:210])
        return out
    if p0 is None:
        out["p2_status"]="ORAN_EKSIK"
    elif top["market"]!=p0["choice"]:
        out["p2_status"]="FARKLI"
    else:
        delta=abs(100*(top["calibrated_probability"]-p0["probability"]))
        out["percentage_point_gap"]=round(delta,4)
        out["p2_status"]="UYUMLU" if delta<=5 else "YUZDELER_UZAK"
    return out

def main():
    verify_active_policy(ROOT)
    from forward_quad import verify_snapshot
    raw=clean_rows(HISTORY)
    status,digest=verify_snapshot(HISTORY,raw,datetime.now(timezone.utc),base=BASELINE,source_audit=AUDIT)
    reg=Registry(REGISTRY)
    lock=json.loads(V4_LOCK.read_text(encoding="utf-8"))
    setting=use_lock(json.loads(M4_LOCK.read_text(encoding="utf-8")))
    items=json.loads(INPUT.read_text(encoding="utf-8"))["rows"]
    result={"schema":"PDF_FIXTURE_UNVERIFIED_RESEARCH_25_MODEL_20261122_V1",
            "history_acceptance":status,"history_sha256":digest,
            "user_pdf_assumed_fixture_only":True,
            "federation_confirmation_asserted":False,
            "using_official_forward_select_function":False,
            "new_signed_forecasts":False,
            "results":[]}
    try:
        for i,row in enumerate(items,1):
            item=one(row,raw,reg,lock,setting,status)
            result["results"].append(item)
            print("PDF_RESEARCH_ROW",json.dumps({
                 "n":i,"fixture":item["fixture"],"model_status":item["model_status"],
                 "main":item.get("main"),"p0":item.get("p0"),
                 "p2":item.get("p2_status"),
                 "error":item.get("model_error")},ensure_ascii=False),flush=True)
    finally:
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
        print("FINAL_RESEARCH",json.dumps({
            "n":len(result["results"]),
            "model_ready":sum(x["model_status"]=="RESEARCH_MODEL_CALCULATED_FROM_USER_PDF_FIXTURE_NO_OFFICIAL_SEAL" for x in result["results"]),
            "p0_complete":sum(x["p0"] is not None for x in result["results"]),
            "blocked":{k:sum(x["model_status"]==k for x in result["results"])
                      for k in set(x["model_status"] for x in result["results"])},
        },ensure_ascii=False))
if __name__=="__main__":main()
