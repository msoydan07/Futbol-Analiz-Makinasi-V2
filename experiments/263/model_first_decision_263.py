"""Normal fixed-specialist model-FIRST decision: highest realization likelihood.

Nov20 expert routing: M4 coherent MS triple; C3 KG and 2.5 O/U raw vectors.
Frozen Aug joint calibration applies ONLY to M4 MS; C3 odds percentages
are UNCALIBRATED descriptive probabilities. Old locks and seals untouched.
"""
from __future__ import annotations
import hashlib
import json
import math
from datetime import datetime, timezone

SCHEMA = "263_MODEL_FIRST_FOUR_MODEL_DECISION_RESEARCH_V2"
REF_SCHEMA = "263_MARKET_FIFTH_REFERENCE_RESEARCH_V2"
GROUPS = {"MS": ("MS1", "MSX", "MS2"), "KG": ("BTTS_YES", "BTTS_NO"),
          "O25": ("OVER_2.5", "UNDER_2.5")}

class EvidenceError(ValueError):
    pass

def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
           separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()

def verified(obj, schema):
    if not isinstance(obj, dict) or obj.get("schema") != schema:
        raise EvidenceError("SCHEMA_MISMATCH")
    old = obj.get("payload_sha256")
    if not isinstance(old, str) or old != digest({k:v for k,v in obj.items() if k != "payload_sha256"}):
        raise EvidenceError("SHA_TAMPERED_OR_MISSING")
    return obj

def aware(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None: raise ValueError("tz")
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise EvidenceError("BAD_AWARE_CLOCK") from exc

def validprob(value):
    if (isinstance(value, bool) or not isinstance(value, (int,float))
            or not math.isfinite(value) or not 0 <= value <= 1):
        raise EvidenceError("BAD_PROBABILITY")
    return float(value)

def canonical(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get("1X2"), dict):
        raise EvidenceError("MS_REQUIRED")
    ms = raw["1X2"]
    p = {"MS1":validprob(ms["H"]), "MSX":validprob(ms["D"]),
         "MS2":validprob(ms["A"])}
    if abs(sum(p.values())-1)>1e-6: raise EvidenceError("MS_NOT_NORMALIZED")
    for pos,neg in (("BTTS_YES","BTTS_NO"), ("OVER_2.5","UNDER_2.5")):
        p[pos] = validprob(raw[pos]); p[neg] = validprob(raw[neg])
        if abs(p[pos]+p[neg]-1)>1e-6: raise EvidenceError("BINARY_NOT_NORMALIZED")
    return p

def joint_poisson(lh, la):
    if any(not isinstance(x,(int,float)) or not math.isfinite(x)
           or not .05 <= x <= 5 for x in (lh,la)):
        raise EvidenceError("BAD_GOAL_LAMBDA")
    def pmf(mu):
        a=[math.exp(-mu)]
        for n in range(1,70):
            a.append(a[-1]*mu/n)
            if 1-sum(a)<1e-13: break
        return a
    h,a=pmf(lh),pmf(la)
    mass=sum(h)*sum(a)
    if 1-mass>1e-9: raise EvidenceError("GOAL_MATRIX_TAIL")
    p={x:0. for x in ("MS1","MSX","MS2","BTTS_YES","OVER_2.5")}
    for i,x in enumerate(h):
        for j,y in enumerate(a):
            v=x*y/mass
            p["MS1" if i>j else "MSX" if i==j else "MS2"]+=v
            if i and j: p["BTTS_YES"]+=v
            if i+j>=3: p["OVER_2.5"]+=v
    p["BTTS_NO"]=1-p["BTTS_YES"]
    p["UNDER_2.5"]=1-p["OVER_2.5"]
    return p

def select(forecast, baseline, lock, *, now):
    """One SHA-sealed model decision, WITHOUT an odds or price argument."""
    verified(forecast,"quad_forward_263_v1")
    verified(baseline,"263_asof_market_baseline_v2")
    if forecast.get("status")!="EXPERIMENTAL_PREMATCH_FOUR_MODEL_NO_BETTING":
        raise EvidenceError("NOT_APPROVED_FOUR_MODEL_RECORD")
    fx=forecast["fixture"];stamp=aware(forecast["created_at_utc"]);asof=aware(now)
    if not stamp<=asof<aware(fx["kickoff_utc"]): raise EvidenceError("NOT_PREKICKOFF")
    if fx.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE":
        raise EvidenceError("FIXTURE_UNVERIFIED")
    if baseline.get("forecast_sha256")!=forecast["payload_sha256"]:
        raise EvidenceError("BASELINE_FORECAST_SHA_MISMATCH")
    if (baseline.get("method")!="PAST_RESULTS_LEAGUE_MARKET_RATE"
        or baseline.get("source_snapshot_sha256")!=forecast.get("data",{}).get("snapshot_sha256")):
        raise EvidenceError("BASELINE_SOURCE_OR_METHOD_MISMATCH")
    if (baseline.get("league")!=fx["league"]
        or not baseline.get("last_result_date")
        or baseline["last_result_date"]>=fx["match_local_date"]):
        raise EvidenceError("HISTORICAL_LEAKAGE_OR_LEAGUE_MISMATCH")
    bt=aware(baseline.get("created_at_utc"))
    if not stamp<=bt<=asof or (bt-stamp).total_seconds()>600:
        raise EvidenceError("BASELINE_ASOF_TIME_INVALID")
    if (lock.get("schema")!="263_MODEL_FIRST_RESEARCH_LOCK_V2"
        or lock.get("officially_approved") is not False
        or lock.get("market_reference_only") is not True
        or lock.get("no_odds_input_to_selection") is not True
        or lock.get("price_may_not_be_gate") is not True):
        raise EvidenceError("WRONG_MODEL_LOCK")
    if lock.get("payload_sha256")!=digest({k:v for k,v in lock.items() if k!="payload_sha256"}):
        raise EvidenceError("MODEL_LOCK_SHA_MISMATCH")
    # Versioned lock: preserve the original v3 SHA replay exactly. The
    # independent 2025/26-trained C3 calibration is activated ONLY by v4.
    calibration_v4=lock.get("calibration_v4")
    if calibration_v4 is not None:
        from model_first_frozen_c3_calibration_263 import verify_policy
        try: verify_policy(calibration_v4)
        except ValueError as ex: raise EvidenceError("FROZEN_C3_POLICY_INVALID") from ex
        if (lock.get("historical_reference",{}).get("ranking")!=
            "DIAGNOSTIC_ONLY_NOT_USED_FOR_V4_CALIBRATED_MARKET_SELECTION"):
            raise EvidenceError("V4_HISTORY_MUST_NOT_RANK_NEW_CALIBRATION")
    if (lock.get("family_anchors")!={"MS":"M4","KG":"C3","O25":"C3"}
        or lock.get("historical_20261119_family_anchors")!={"MS":"M4","KG":"M4","O25":"M4"}
        or lock.get("frozen_m4_calibration_only_applies_to_MS") is not True):
        raise EvidenceError("FIXED_EXPERT_POLICY_MISMATCH")
    mods=forecast.get("model_predictions")
    if not isinstance(mods,dict) or set(mods)!=set(("B","C2","C3","M4")):
        raise EvidenceError("FOUR_MODEL_SLOTS_REQUIRED")
    raw={}
    for name,m in mods.items():
        raw[name]=canonical(m["goals"]["markets"]) if m.get("status")=="AVAILABLE" else None
    if raw["M4"] is None: raise EvidenceError("ANCHOR_M4_UNAVAILABLE")
    if sum(p is not None for p in raw.values()) < lock["min_available_models"]:
        raise EvidenceError("REQUIRED_MODEL_COVERAGE_MISSING")
    goals=mods["M4"]["goals"]
    theta=lock["m4_joint_calibration_august"]
    if len(theta)!=3 or any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in theta):
        raise EvidenceError("MODEL_CALIBRATION_CORRUPT")
    lh,la=goals["lambda_home"],goals["lambda_away"]
    if any(not isinstance(x,(int,float)) or not math.isfinite(x) or not .05<=x<=5 for x in (lh,la)):
        raise EvidenceError("BAD_GOAL_LAMBDA")
    lh=max(.05,min(5.,math.exp(theta[0]+theta[2]*math.log(lh))))
    la=max(.05,min(5.,math.exp(theta[1]+theta[2]*math.log(la))))
    m4_calibrated=joint_poisson(lh,la)
    # A single M4 1X2 vector sums exactly to one; do NOT select H/D/A
    # independently from different models or calibrated weights.
    assert abs(sum(m4_calibrated[k] for k in GROUPS["MS"])-1)<1e-7
    expert_vectors={"MS":{k:m4_calibrated[k] for k in GROUPS["MS"]}}
    fallback_families=[]
    for fam in ("KG","O25"):
        model="C3" if raw["C3"] is not None else "M4"
        if model!="C3":fallback_families.append(fam)
        expert_vectors[fam]={k:raw[model][k] for k in GROUPS[fam]}
        if abs(sum(expert_vectors[fam].values())-1)>1e-7:
            raise EvidenceError("SPECIALIST_BINARY_NOT_NORMALIZED")
    b=baseline.get("markets")
    if not isinstance(b,dict):raise EvidenceError("BASELINE_MARKETS_MISSING")
    if calibration_v4 is not None and raw["C3"] is not None:
        # C3 market probabilities are not on the same calibrated scale as
        # August-M4 MS. Do not use original raw Nov8 SHA outcomes to adjust
        # this new model identity. Correct KG and O25 separately using a
        # previously frozen 2025/26 C3 reliability transform.
        from model_first_frozen_c3_calibration_263 import calibrated_binary_pair
        for fam,pos,neg in (("KG","BTTS_YES","BTTS_NO"),
                            ("O25","OVER_2.5","UNDER_2.5")):
            try:
                yes,no=calibrated_binary_pair(raw["C3"][pos],validprob(b[pos]),
                                              pos,calibration_v4)
            except ValueError as ex:
                raise EvidenceError("FROZEN_C3_CALIBRATION_FAILED") from ex
            expert_vectors[fam]={pos:yes,neg:no}
    # Core objective, not an extra decision layer: determine which of the
    # seven outcomes is MOST LIKELY TO OCCUR. Never impose a global 60%
    # probability floor, league-base lift, payout/odds or model-agreement gate.
    # B/C2 only annotate agreement; frozen goal models and family anchors stay.
    from historical_probability_reliability_263 import rank_candidates
    history_cfg=lock.get("historical_reference")
    if history_cfg is not None:
        if (history_cfg.get("origin")!="NOV8_PREKICKOFF_SHA_AND_NOV12_TERMINAL_SCORE_ARCHIVE"
            or history_cfg.get("available_from_utc")!="2026-11-13T00:00:00+00:00"
            or history_cfg.get("price_influence") is not False
            or history_cfg.get("ranking")!=(
                 "DIAGNOSTIC_ONLY_NOT_USED_FOR_V4_CALIBRATED_MARKET_SELECTION"
                 if calibration_v4 is not None else "HIGHEST_ESTIMATED_REALIZATION")):
            raise EvidenceError("NORMAL_HISTORY_POLICY_NOT_MATCHED")
        from normal_historical_reference_263 import load as load_actual_reference
        # Real 8-Nov seals contain RAW C3 identity, not 2025-frozen binary
        # calibrated identity. They are NOT legitimate reliability examples
        # for v4 ranking. For v3 keep the old SHA-valid behavior unchanged.
        history=[] if calibration_v4 is not None else load_actual_reference(asof=asof,lock=lock)
    else:
        # Older SHA-signed research decisions remain verifiable with the old
        # lock; future operational entrypoints use the v3 lock above.
        history=[]
    details=[]
    for family,keys in GROUPS.items():
        for key in keys:
            ref=validprob(b[key]);prob=expert_vectors[family][key]
            available=[name for name,p in raw.items() if p is not None]
            agreeing=[name for name in available if raw[name][key]>=ref+.02]
            expert="M4" if family=="MS" or family in fallback_families else "C3"
            details.append({
                "market":key,"family":family,"anchor_model":expert,
                "probability_type":("M4_AUG_JOINT_CALIBRATED" if family=="MS"
                                    else "C3_2025_FROZEN_BINARY_LOGIT" if calibration_v4 is not None and expert=="C3"
                                    else "C3_RAW_UNCALIBRATED" if expert=="C3"
                                    else "M4_RAW_FALLBACK_UNCALIBRATED"),
                "expert_fallback":family in fallback_families,
                "calibrated_probability":round(prob,10),
                "historical_base":round(ref,10),
                "lift_pp":round(100*(prob-ref),6),
                "confidence_score":round(prob,8),
                "agreeing_models":agreeing,"available_models":available,
                "qualification_reasons":[],
                "support_is_diagnostic_not_a_selection_gate":True})
    if calibration_v4 is not None:
        # The operational objective is calibrated occurrence probability
        # itself. Do not perturb ranking using 39 results from a different
        # C3 calibration version. A close gap is uncertainty, NOT auto-PAS.
        ranked=sorted(details,key=lambda row:(-row["calibrated_probability"],row["market"]))
        for row in ranked:
            row["estimated_realization_probability"]=row["calibrated_probability"]
            row["decision_evidence_status"]="FROZEN_HISTORICAL_TRAINING_NOT_BLIND_VALIDATED"
            row["historical_reliability"]={
                "status":"NO_SAME_VERSION_LIVE_SHA_REFERENCE","n":0}
            row["frozen_binary_calibration_train_n"]=(
                calibration_v4["train_n"] if row["probability_type"]==
                    "C3_2025_FROZEN_BINARY_LOGIT" else None)
    else:
        ranked=rank_candidates(details,history,league=fx["league"],asof=asof,
                               min_samples=(history_cfg or {}).get("min_historical_report_n",20),
                               min_local_samples=(history_cfg or {}).get("min_same_league_n",8),
                               prior_strength=(history_cfg or {}).get("prior_strength",20))
    main=ranked[0] if ranked else None
    alternate=next((x for x in ranked[1:] if x["family"]!=main["family"]),None) if main else None
    out={"schema":SCHEMA,"status":"RESEARCH_CANDIDATE_NOT_APPROVED" if main else "RESEARCH_PAS_MODEL_ONLY",
         "forecast_sha256":forecast["payload_sha256"],"baseline_sha256":baseline["payload_sha256"],
         "model_policy_sha256":lock["payload_sha256"],"fixture":fx,
         "main_candidate":main,"alternative_candidate":alternate,"model_market_diagnostics":ranked,
         "fixed_family_experts":{"MS":"M4","KG":"C3","O25":"C3"},
         "used_fallback_families":fallback_families,
         "market_prices_not_required_for_model_decision":True,
         "reason":None if main else "NO_COMPUTABLE_MODEL_MARKET",
         "ranking_objective":"HIGHEST_ESTIMATED_REALIZATION_PROBABILITY",
         "hard_60pct_model_gate":False,
         "historical_pre_match_market_observations":len(history),
         "historical_completed_matches":len({r["fixture_id"] for r in history}),
         "historical_reference_source":("NONE_FOR_NEW_CALIBRATION_VERSION"
              if calibration_v4 is not None else
              "NOV8_ORIGINAL_SHA_SIGNED_RESULTS" if history else "NONE_ASOF"),
         "historical_reference_is_independently_validated":False,
         "odds_affected_selection":False,"price_used_in_decision":False,
         "new_model_fit":False,"forecast_unchanged":True,"betting_authorized":False,
         "production_modified":False,"official_S1_S2_approved":False}
    if calibration_v4 is not None:
        out.update({
            "selection_policy_version":"20261121_C3_2025_FROZEN_V4",
            "calibration_train_n_2025_26":calibration_v4["train_n"],
            "nov8_raw_sha_history_used_to_rank":False,
            "top_two_probability_gap_pp":(
                round(100*(ranked[0]["calibrated_probability"]-
                           ranked[1]["calibrated_probability"]),4) if len(ranked)>1 else None),
            "near_tie_within_two_percentage_points":(
                ranked[0]["calibrated_probability"]-
                ranked[1]["calibrated_probability"]<=.02 if len(ranked)>1 else False),
            "independent_forward_superiority_established":False,
            "prior_v3_original_forecast_seals_unchanged":True,
        })
    out["payload_sha256"]=digest(out)
    return out

def market_reference(decision, market_groups, *, source_pdf_sha256):
    """Signed fifth-reference report only. NEVER updates model decision SHA."""
    verified(decision,SCHEMA)
    if not isinstance(source_pdf_sha256,str) or len(source_pdf_sha256)!=64:
        raise EvidenceError("PDF_SHA_INVALID")
    rows=[]
    for family,keys in GROUPS.items():
        group=market_groups.get("MS" if family=="MS" else "KG" if family=="KG" else "GOALS_2.5",{})
        if group.get("status")!="FULL_MARKET_QUOTE_AVAILABLE":
            rows.append({"family":family,"status":"NO_COMPLETE_GROUP"})
            continue
        pairs=[]
        for key in keys:
            p=validprob(group["no_vig"][key]);o=group["prices"][key]
            if not isinstance(o,(int,float)) or not math.isfinite(o) or o<=1:
                raise EvidenceError("INVALID_REFERENCE_PRICE")
            model=next(x for x in decision["model_market_diagnostics"] if x["market"]==key)
            pairs.append({"market":key,"odds":o,"market_no_vig":p,
                          "model_probability":model["calibrated_probability"],
                          "model_minus_market_pp":round((model["calibrated_probability"]-p)*100,4)})
        rows.append({"family":family,"status":"DESCRIPTIVE_FIFTH_REFERENCE","pairs":pairs})
    out={"schema":REF_SCHEMA,"decision_sha256":decision["payload_sha256"],
         "forecast_sha256":decision["forecast_sha256"],"source_pdf_sha256":source_pdf_sha256,
         "odds_used_for_model_selection":False,"rows":rows,"betting_authorized":False}
    out["payload_sha256"]=digest(out)
    return out
