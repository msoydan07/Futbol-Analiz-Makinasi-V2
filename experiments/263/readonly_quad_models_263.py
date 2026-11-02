"""Side-effect-free frozen B/C2/C3/M4 prediction for a named PREMATCH report.

Uses identical imported model functions and the locked M4 settings. Does not
invoke forward_quad.predict_quad_from_verified_gate (which writes a pilot).
Never select main model, calibrate, record or place bets.
"""
import hashlib
import json
from pathlib import Path
from exp_263_batch import c1,fit_c3,predict_c3,scores
from analysis_math_core import canonical_c2_lambda,score_market
from forward_quad import _legacy_joint,_b_lambdas,FROZEN
from m4_integrated import fit_m4,predict_m4,score_markets,use_lock

MODELS=("B","C2","C3","M4")
class ReadonlyQuadError(ValueError): pass

def read_only_quad(rows,case,*,lock_path=None):
    if not isinstance(rows,list) or not isinstance(case,dict):
        raise ReadonlyQuadError("UNSUPPORTED_INPUT")
    for f in ("league","home_id","away_id","target_date"):
        if not isinstance(case.get(f),str) or not case[f]:
            raise ReadonlyQuadError("MATCH_IDENTITY_MISSING")
    lock_path=Path(lock_path) if lock_path is not None else Path(__file__).with_name("m4_lock.json")
    lock=json.loads(lock_path.read_text(encoding="utf-8"))
    setting=use_lock(lock)
    if lock.get("frozen_source_sha256")!=FROZEN:
        raise ReadonlyQuadError("M4_LOCK_SOURCE_MISMATCH")
    m4_code=Path(__file__).with_name("m4_integrated.py")
    if hashlib.sha256(m4_code.read_bytes()).hexdigest()!=lock.get("m4_engine_sha256"):
        raise ReadonlyQuadError("M4_LOCK_CODE_MISMATCH")
    league=case["league"];h=case["home_id"];a=case["away_id"];day=case["target_date"]
    # In particular no target-day completed match (kickoff order not known).
    past=[r for r in rows if r["league"]==league and r["match_date"]<day]
    past.sort(key=lambda r:(r["match_date"],r["fixture_id"]))
    if len(past)<60:
        return {m:{"status":"UNAVAILABLE","reason":"LEAGUE_PRIOR_HISTORY_LT_60"} for m in MODELS}
    if any(r["home_id"]==r["away_id"] for r in past):
        raise ReadonlyQuadError("INVALID_HISTORICAL_IDENTITIES")
    outputs={}
    b=c1(past,h,a);lambdas=_b_lambdas(past,h,a)
    if (b is None)!=(lambdas is None):
        raise ReadonlyQuadError("FROZEN_B_COMPATIBILITY")
    outputs["B"]={"status":"AVAILABLE","goals":_legacy_joint(*lambdas,b[0])} if b else {
        "status":"UNAVAILABLE","reason":"B_INSUFFICIENT_CONTEXT"}
    current=[r for r in past if r["season"]=="2026-2027"]
    prev=[r for r in past if r["season"]=="2025-2026"]
    c2,reason=canonical_c2_lambda(current,prev,h,a)
    outputs["C2"]={"status":"AVAILABLE","goals":score_market(c2["lambda_home"],c2["lambda_away"])} if c2 else {
        "status":"UNAVAILABLE","reason":reason}
    fitted=fit_c3(past);lam3=predict_c3(fitted,h,a) if fitted else None
    s3=scores(*lam3) if lam3 else None
    outputs["C3"]={"status":"AVAILABLE","goals":_legacy_joint(*lam3,s3[0])} if s3 else {
        "status":"UNAVAILABLE","reason":"C3_FIT_OR_LAMBDA_UNAVAILABLE"}
    mfit=fit_m4(past,league,day,setting)
    mlam=predict_m4(mfit,h,a) if mfit else None
    outputs["M4"]={"status":"AVAILABLE","goals":score_markets(*mlam)} if mlam else {
        "status":"UNAVAILABLE","reason":"M4_FIT_OR_LAMBDA_UNAVAILABLE"}
    if set(outputs)!=set(MODELS):
        raise ReadonlyQuadError("FOUR_MODEL_OUTPUT_INCOMPLETE")
    return outputs
