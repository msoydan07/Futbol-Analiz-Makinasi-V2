"""Reusable original-PDF-listed fixture model research without forging OFFICIAL gate.

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
from experiments.p1_market_intelligence.p1_market import no_vig,best_choices,MARKETS
from check_active_decisions_263 import verify_active_policy

INPUT=Path(__file__).with_name("nov22_eight_pdf_research_input.json")
HISTORY=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
BASELINE=ROOT/"m4_quad_base/historical_results.csv"
AUDIT=ROOT/"data/results_only_263/4617_research_input_provenance.json"
REGISTRY=ROOT/"experiments/263/evidence/identity_index_263.json"
M4_LOCK=ROOT/"experiments/263/m4_lock.json"
V4_LOCK=ROOT/"experiments/263/model_first_selection_lock_20261121_v4.json"
OUT=Path("/tmp/eight_league_25_pdf_model_research_no_official_gate.json")
RESEARCH_SCHEMA="263_USER_IDDAA_PDF_ONLY_MODEL_RESEARCH_V1"

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

def one(row,all_rows,reg,lock,setting,acceptance,*,now=None):
    league,hn,an,tstr,file,*_=row
    day=row[12]
    kickoff=datetime.fromisoformat(day+"T"+tstr+":00").replace(
         tzinfo=ZoneInfo("Europe/Istanbul")).astimezone(timezone.utc)
    now=now or datetime.now(timezone.utc)
    quoted,probs,p0=p0_from_row(row)
    out={"fixture":f"{hn} - {an}","league":league,"time":tstr,"source_file":file,
         "date":day,"runner_created_at":now.isoformat(),"p0":p0,
         "p0_probabilities":probs,"odds":quoted,
         "source_grade":"USER_IDDAA_PDF_TRANSCRIPTION_NOT_OFFICIAL_FEDERATION_PROOF",
         "official_fixture_verified":False,"official_seal_created":False,
         "model_status":"NOT_STARTED","p2_status":"NO_MODEL"}
    if not now.tzinfo or now>=kickoff:
        out["model_status"]="MATCH_STARTED_BEFORE_THIS_RESEARCH_RUN"
        return out
    # Exact, reviewable book->federation club-name crosswalks confirmed from
    # the existing 215-team canonical registry. NO fuzzy matching and NO
    # change to the source PDF or production identity cache.
    reviewed_book_alias={
        ("ESP1","Racing Santander"):"R. Racing Club",
        ("ITA1","AC Milan"):"Milan",
        ("BEL1","Standard Liege"):"Standard de Liège",
    }
    def resolve_source_alias(label):
        official=reviewed_book_alias.get((league,label),label)
        tid=resolve(reg,league,official)
        if official!=label:
            out.setdefault("book_to_canonical_name_match",{})[label]=official
        return tid
    try:
        hid=resolve_source_alias(hn);aid=resolve_source_alias(an)
        if hid==aid:raise ValueError("HOME_AWAY_RESOLVED_TO_IDENTICAL_CLUB")
        out["resolved_club_ids"]={"home":hid,"away":aid}
    except (KeyError,ValueError) as e:
        out.update(model_status="UNRESOLVED_CANONICAL_TEAM_ID",
                   model_error=str(e)[:190])
        return out
    raw=[r for r in all_rows if r["league"]==league and r["match_date"]<day]
    if any(r["league"]==league and r["match_date"]>=day for r in all_rows):
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
        freshness=review_gap(raw,league,day,now=now)
        out["freshness_status"]=freshness.get("status")
        if freshness["age_days"]>10 and freshness["status"]!="BOUNDED_GAP_NO_MISSING_RESULTS_IN_PUBLIC_FEED_RESEARCH_ONLY":
            out["model_status"]="STALE_HISTORICAL_INPUT_GATE"
            return out
    except Exception as e:
        out.update(model_status="FRESHNESS_EVIDENCE_FAILED",model_error=str(e)[:150])
        return out
    b=base_rates(past)
    try:
        fit=fit_m4(past,league,day,setting)
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



def make_input_row(parsed):
    """Convert one verified original user PDF row, never guess prices or teams."""
    odds=parsed.get("odds")
    if (parsed.get("status")!="PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK"
        or not isinstance(odds,dict)):
        raise ValueError("NOT_A_PARSED_IDDAA_FIRST_PDF_ROW")
    return [parsed["league"],parsed["home_label"],parsed["away_label"],
            parsed["kickoff_time_tr"],"user-original-iddaa-pdf",
            odds.get("MS1"),odds.get("MSX"),odds.get("MS2"),
            odds.get("O25_UNDER"),odds.get("O25_OVER"),
            odds.get("BTTS_YES"),odds.get("BTTS_NO"),
            parsed["match_date_tr"]]


def verify_research_record(record,pdfsha,row):
    from model_first_decision_263 import digest
    if (record.get("schema")!=RESEARCH_SCHEMA
        or record.get("source_pdf_sha256")!=pdfsha
        or record.get("row_index")!=row["index"]
        or record.get("league")!=row.get("league")
        or record.get("fixture")!=row.get("pdf_home")+" - "+row.get("pdf_away")
        or record.get("official_fixture_verified") is not False
        or record.get("official_seal_created") is not False
        or record.get("model_status")!="RESEARCH_MODEL_CALCULATED_FROM_USER_PDF_FIXTURE_NO_OFFICIAL_SEAL"
        or record.get("price_affected_main_selection") is not False
        or record.get("payload_sha256")!=digest({k:v for k,v in record.items()
                                                if k!="payload_sha256"})):
        raise ValueError("PDF_RESEARCH_RECORD_OR_ORIGINAL_PDF_SHA_INVALID")
    return record


def attach(bulletin,calibrated,*,history,source_baseline,source_acceptance,
           m4_lock,dev_lock,now=None):
    """One immutable first-PDF session gets an explicit LOWER-TRUST sidecar.

    Existing official SHA forecasts and selections remain untouched.
    Do not silently promote this sidecar to an official fixture seal.
    """
    import copy
    from iddaa_pdf_first_quote_263 import sha256
    from iddaa_pdf_team_alias_preflight_263 import resolve_label,index_registry
    if (bulletin.get("pdf_sha256")!=calibrated.get("pdf_sha256")
        or len(bulletin.get("rows",[]))!=len(calibrated.get("rows",[]))):
        raise ValueError("PDF_SOURCE_FALLBACK_SOURCE_OR_ROW_COUNT_MISMATCH")
    old=calibrated.get("signed_research_session_sha256")
    if old!=sha256({k:v for k,v in calibrated.items()
                   if k!="signed_research_session_sha256"}):
        raise ValueError("ORIGINAL_SESSION_SHA_INVALID")
    if source_baseline is None or source_acceptance is None:
        # No historical provenance relaxation: the official route can still
        # emit its own technical/PDF-source issue report.
        return calibrated
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError("AWARE_TIME_REQUIRED")
    now=now.astimezone(timezone.utc)
    records=clean_rows(history)
    source_status,history_sha=verify_snapshot(history,records,now,
                                               base=source_baseline,
                                               source_audit=source_acceptance)
    reg=Registry(REGISTRY)
    idx,official_names,members=index_registry()
    lock=json.loads(Path(dev_lock).read_text(encoding="utf-8"))
    if (lock.get("schema")!="263_MODEL_FIRST_RESEARCH_LOCK_V2"
        or lock.get("no_odds_input_to_selection") is not True
        or lock.get("price_may_not_be_gate") is not True
        or lock.get("calibration_v4") is None
        or lock.get("officially_approved") is not False):
        raise ValueError("FROZEN_MODEL_SELECTION_POLICY_INVALID")
    setting=use_lock(json.loads(Path(m4_lock).read_text(encoding="utf-8")))
    result=copy.deepcopy(calibrated)
    count=0;excluded=0
    for idxrow,parsed in enumerate(bulletin["rows"]):
        current=result["rows"][idxrow]
        if (current.get("index")!=idxrow
            or current.get("league")!=parsed.get("league")
            or current.get("pdf_home")!=parsed.get("home_label")
            or current.get("pdf_away")!=parsed.get("away_label")
            or current.get("match_date_tr")!=parsed.get("match_date_tr")
            or current.get("kickoff_time_tr")!=parsed.get("kickoff_time_tr")):
            raise ValueError("PDF_ORIGINAL_ROW_IDENTITY_OR_ORDER_INVALID")
        if current.get("model_first_decision") is not None:
            continue
        if parsed.get("status")!="PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK":
            continue
        if (parsed.get("league") is None or parsed.get("league") not in members):
            continue
        # Reconcile original PDF labels against the existing immutable 215-club
        # registry. Curated exact aliases only, never fuzzy team-ID guesses.
        h=resolve_label(parsed["league"],parsed["home_label"],idx)
        a=resolve_label(parsed["league"],parsed["away_label"],idx)
        if (h["status"]!="MAPPED" or a["status"]!="MAPPED" or
            h["team_id"]==a["team_id"]):
            current["pdf_source_research_status"]="TEAM_NAME_OR_MEMBERSHIP_REVIEW"
            excluded+=1
            continue
        if (current.get("home_id") not in (None,h["team_id"]) or
            current.get("away_id") not in (None,a["team_id"])):
            raise ValueError("PDF_AND_OFFICIAL_ROW_TEAM_ID_DISAGREEMENT")
        if current.get("model_forecast_created") is True:
            # Official forecast exists; research must never replace its SHA.
            continue
        try:
            raw=make_input_row(parsed)
            calc=one(raw,records,reg,lock,setting,source_status,now=now)
            if calc.get("model_status")!="RESEARCH_MODEL_CALCULATED_FROM_USER_PDF_FIXTURE_NO_OFFICIAL_SEAL":
                current["pdf_source_research_status"]=calc.get("model_status","RESEARCH_BLOCKED")
                excluded+=1
                continue
            if (calc["resolved_club_ids"]["home"]!=h["team_id"] or
                calc["resolved_club_ids"]["away"]!=a["team_id"] or
                calc["date"]!=parsed["match_date_tr"]):
                raise ValueError("PDF_RESEARCH_CANONICAL_ID_OR_DATE_MISMATCH")
            calc.update({
                "schema":RESEARCH_SCHEMA,
                "row_index":idxrow,
                "source_pdf_sha256":bulletin["pdf_sha256"],
                "source_grade":"USER_IDDAA_PDF_ONLY_NOT_OFFICIAL_FIXTURE_VERIFIED",
                "price_affected_main_selection":False,
                "original_official_forecast_replaced":False,
                "training_history_sha256":history_sha,
            })
            from model_first_decision_263 import digest
            calc["payload_sha256"]=digest(calc)
            verify_research_record(calc,bulletin["pdf_sha256"],current)
            current["pdf_source_research"]=calc
            current["pdf_source_research_status"]="PDF_SOURCE_MATH_READY_NOT_OFFICIAL_SEAL"
            count+=1
        except (ValueError,TypeError,KeyError,OSError,AssertionError) as exc:
            current["pdf_source_research_status"]="PDF_RESEARCH_MATH_OR_DATA_BLOCKED"
            current["pdf_source_research_reason"]=f"{type(exc).__name__}: {exc}"[:160]
            excluded+=1
    result["pdf_source_model_math_count"]=count
    result["pdf_source_research_blocked_count"]=excluded
    result["source_pdf_only_rows_are_not_official_seals"]=True
    result["signed_research_session_sha256"]=sha256({
        k:v for k,v in result.items() if k!="signed_research_session_sha256"})
    return result
