"""Bayern Köln Nov20: ONE read-only diagnostic; no model or seal changes.

Exact accepted 4617 scores input, original pre-day filtering, original
B/C3 functions. Temporarily intercept scipy optimizer only to READ result
success and gradient, without changing optimizer parameters or data.
"""
from pathlib import Path
import hashlib,json,math
import numpy as np
from datetime import datetime
import exp_263_batch as legacy
from full_match_eligibility_263 import full_match_rows
from forward_quad import _b_lambdas

DATA=Path("data/results_only_263/2026-11-10_completed_4617_scores_only.csv")
SHA="637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89"
HOME="c8be3a92-94db-5ef4-9cb4-7a9877fc7bbe"
AWAY="86c2df96-ecbc-5200-93f2-2b56083efbe6"
DAY="2026-11-20"

def tail(lh,la):
    if lh is None or la is None:return None
    if min(lh,la)<0:return None
    # exactly same 0..10 single-team finite mass as frozen code
    a=sum(math.exp(-lh)*lh**i/math.factorial(i) for i in range(11))
    b=sum(math.exp(-la)*la**i/math.factorial(i) for i in range(11))
    return 1-a*b

def main():
    actual_sha=hashlib.sha256(DATA.read_bytes()).hexdigest()
    if actual_sha!=SHA:raise ValueError("HISTORY_SHA_MISMATCH_NO_DIAG")
    all_rows=legacy.clean_rows(DATA)
    league_rows,excluded,policy_sha=full_match_rows(
        [r for r in all_rows if r["league"]=="GER1"])
    past=[r for r in league_rows if r["match_date"]<DAY]
    if not past:raise ValueError("NO_PREMATCH_GER1_ROWS")
    homes=[r for r in past if r["home_id"]==HOME]
    aways=[r for r in past if r["away_id"]==AWAY]
    b_lam=_b_lambdas(past,HOME,AWAY)
    b_original=legacy.c1(past,HOME,AWAY)
    b_tail=tail(*b_lam) if b_lam else None
    optim={}
    old_minimize=legacy.minimize
    def readonly_capture(*args,**kwargs):
        result=old_minimize(*args,**kwargs)
        optim.update({"success":bool(result.success),"status":int(result.status),
                      "message":str(result.message),"iterations":int(result.nit),
                      "gradient_norm":float(np.linalg.norm(result.jac))
                                     if result.jac is not None else None,
                      "finite_coefficients":bool(np.isfinite(result.x).all())})
        return result
    try:
        legacy.minimize=readonly_capture
        fitted=legacy.fit_c3(past)
    finally:legacy.minimize=old_minimize
    c3_lam=legacy.predict_c3(fitted,HOME,AWAY) if fitted else None
    c3_output=legacy.scores(*c3_lam) if c3_lam else None
    c3_raw=None
    if fitted is not None:
        beta,ix,m=fitted
        def v(team,start):return float(beta[start+ix[team]]) if team in ix else 0.
        c3_raw=[math.exp(float(beta[0])+v(HOME,2)+v(AWAY,2+m)),
                math.exp(float(beta[1])+v(AWAY,2)+v(HOME,2+m))]
    c3_tail=tail(*c3_raw) if c3_raw else None
    if fitted is None:c3_reason="FIT_FAILED"
    elif c3_lam is None:c3_reason="PREDICT_OUTSIDE_0_05_TO_5_LAMBDA"
    elif c3_output is None:c3_reason="POISSON_TAIL_OVER_0_001" if c3_tail>0.001 else "OTHER_SCORES_FAIL"
    else:c3_reason="AVAILABLE"
    b_reason=("POISSON_TAIL_OVER_0_001" if b_lam and b_original is None
              and b_tail is not None and b_tail>0.001 else
              "AVAILABLE" if b_original is not None else "INSUFFICIENT_CONTEXT_OR_OTHER")
    result={"fixture":"GER1 Bayern München - Köln 2026-11-20",
        "kind":"READONLY_PREMATCH_MODEL_DIAG",
        "history_sha256":actual_sha,
        "league_rows_asof":len(past),"excluded_partial_matches":len(excluded),
        "b":{"home_context_all":len(homes),"away_context_all":len(aways),
             "lambda_home":b_lam[0] if b_lam else None,
             "lambda_away":b_lam[1] if b_lam else None,
             "tail_mass_0_10":b_tail,
             "original_c1_available":b_original is not None,"reason":b_reason},
        "c3":{"optimizer":optim,"fit_returned":fitted is not None,
              "lambda_raw_unbounded":c3_raw,"lambda_validated":c3_lam,
              "tail_mass_0_10":c3_tail,
              "original_scores_available":c3_output is not None,
              "reason":c3_reason},
        "frozen_models_modified":False,"no_pilot_forecasts_rewritten":True}
    print("ROOT_CAUSE_ONE_SHOT_JSON="+json.dumps(result,ensure_ascii=False,allow_nan=False))
    if b_reason!="POISSON_TAIL_OVER_0_001":raise ValueError("B_DIAG_DISAGREES_WITH_PREMATCH_RUN")
    if c3_reason=="AVAILABLE":raise ValueError("C3_DIAG_DISAGREES_WITH_PREMATCH_RUN")

if __name__=="__main__":main()
