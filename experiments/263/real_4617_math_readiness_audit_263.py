"""Read-only real 4,617-score as-of readiness audit for all ten frozen 2.6.3 leagues.

Only mathematical/identity/input readiness, NEVER predictive accuracy claims.
No new pilot, parameter sweep, online quotes, retuning, or sealed-record writes.
For each league uses already frozen settings with as-of 2026-11-11 history,
excludes the one awarded-but-incomplete game, and checks B/C2/C3/M4
availability independently. Results are one aggregate JSON diagnostics file.

Input source evidence: score-only 4617 research snapshot, not full independent
official confirmation; preserves 43 partially verified source records caveat.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from collections import Counter
from datetime import date
from pathlib import Path

from exp_263_batch import clean_rows,c1,fit_c3,predict_c3,scores as old_scores
from full_match_eligibility_263 import full_match_rows
from m4_integrated import fit_m4,predict_m4,score_markets,use_lock
from analysis_math_core import canonical_c2_lambda,score_market
from iddaa_pdf_team_alias_preflight_263 import index_registry

FROZEN_RESEARCH_SHA="637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89"
CUTOFF="2026-11-11"
LEAGUES=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
def _health(m):
    # C2 representation exposes flat MS*; M4/C3 embeds 1X2 H/D/A.
    if "1X2" in m:
        h,d,a=[float(m["1X2"][k]) for k in ("H","D","A")]
    else:
        h,d,a=[float(m[k]) for k in ("MS1","MSX","MS2")]
    over=float(m["OVER_2.5"]);under=float(m["UNDER_2.5"])
    kg=float(m["BTTS_YES"]);no=float(m["BTTS_NO"])
    q=(h,d,a,over,under,kg,no)
    if not all(math.isfinite(x) and 0<=x<=1 for x in q):
        raise ValueError("NON_FINITE_PROBABILITY_OR_NEGATIVE")
    if (abs(h+d+a-1)>1e-8 or abs(over+under-1)>1e-8 or abs(kg+no-1)>1e-8):
        raise ValueError("MULTI_MARKET_NORMALIZATION_FAILURE")
    return True

def audit(history,*,lock):
    path=Path(history)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=FROZEN_RESEARCH_SHA:
        raise ValueError("4617_RESEARCH_HISTORY_CHANGED")
    rows=clean_rows(path)
    if len(rows)!=4617:raise ValueError("EXPECTED_EXACT_4617_RESULTS")
    if set(r["league"] for r in rows)!=set(LEAGUES):
        raise ValueError("UNEXPECTED_LEAGUE_SCOPE")
    if len({r["fixture_id"] for r in rows})!=4617:
        raise ValueError("DUPLICATED_OR_EMPTY_MATCH_ID")
    if any(r["match_date"]>=CUTOFF or r["home_id"]==r["away_id"]
           for r in rows):
        raise ValueError("FUTURE_OR_SAME_TEAM_TRAINING_MATCH")
    full,partial_exclusions,policy_sha=full_match_rows(rows)
    if len(full)!=4616 or len(partial_exclusions)!=1:
        raise ValueError("NOT_FULL_MATCH_ELIGIBILITY_POLICY")
    by_league=Counter(r["league"] for r in full)
    index,names,_=index_registry()
    registered=set(names)
    bad_ids=sorted(set(r["home_id"] for r in rows)|set(r["away_id"] for r in rows)-registered)
    # Historical pre-promotion teams may be outside 26-27 membership but
    # must remain in immutable registry.
    if any(team_id not in registered for r in rows for team_id in
           (r["home_id"],r["away_id"])):
        raise ValueError("UNREGISTERED_HISTORICAL_TEAM_UUID")
    config=json.loads(Path(lock).read_text(encoding="utf-8"))
    settings=use_lock(config)
    records=[]
    for league in LEAGUES:
        past=[r for r in full if r["league"]==league]
        if len(past)<60:raise ValueError("INSUFFICIENT_M4_REAL_HISTORY_"+league)
        current=[r for r in past if r["season"]=="2026-2027"]
        previous=[r for r in past if r["season"]=="2025-2026"]
        if not current:raise ValueError("MISSING_CURRENT_SEASON_"+league)
        recent=max(current,key=lambda r:(r["match_date"],r["fixture_id"]))
        home,away=recent["home_id"],recent["away_id"]
        fit=fit_m4(full,league,CUTOFF,settings)
        if fit is None:
            raise ValueError("M4_FIT_FAILED_REAL_"+league)
        goals=predict_m4(fit,home,away)
        if goals is None:
            raise ValueError("M4_EXPECTED_GOALS_OUT_OF_RANGE_"+league)
        m4=score_markets(*goals)
        _health(m4["markets"])
        # Independent C2 score function must yield the same physical Poisson
        # probabilities as frozen M4 scorer when lambdas are identical.
        independent=score_market(*goals)["markets"]
        _health(independent)
        for market,other in (
          ("BTTS_YES",independent["BTTS_YES"]),
          ("OVER_2.5",independent["OVER_2.5"]),
          ("UNDER_2.5",independent["UNDER_2.5"]),
        ):
            if abs(m4["markets"][market]-other)>1e-10:
                raise ValueError("M4_VS_CANONICAL_POISSON_DIFFERENTIAL_"+league+"_"+market)
        # Existing frozen other models, with honest insufficiency statuses.
        b=c1(past,home,away)
        b_status="AVAILABLE" if b is not None else "UNAVAILABLE"
        if b is not None:
            if abs(sum(b[0])-1)>1e-10 or any(not 0<=p<=1 for p in b[0]):
                raise ValueError("B_LEGACY_1X2_INVALID_"+league)
        c2,reason=canonical_c2_lambda(current,previous,home,away)
        c2_status="AVAILABLE" if c2 is not None else "UNAVAILABLE_"+str(reason)
        if c2 is not None:_health(score_market(c2["lambda_home"],c2["lambda_away"])["markets"])
        c3fit=fit_c3(past)
        c3goals=predict_c3(c3fit,home,away) if c3fit else None
        c3=old_scores(*c3goals) if c3goals else None
        c3_status="AVAILABLE" if c3 is not None else "UNAVAILABLE"
        if c3 is not None and abs(sum(c3[0])-1)>1e-10:
            raise ValueError("C3_LEGACY_1X2_INVALID_"+league)
        records.append({
            "league":league,"eligible_history":len(past),
            "current_season_completed":len(current),
            "previous_season_completed":len(previous),
            "latest_completed_match_date":recent["match_date"],
            "sample_team_pair_source":"LATEST_COMPLETED_FIXTURE_NOT_A_FUTURE_PREDICTION",
            "M4":"AVAILABLE","M4_lambda_home":goals[0],
            "M4_lambda_away":goals[1],
            "B":b_status,"C2":c2_status,"C3":c3_status,
            "M4_2_5_over":m4["markets"]["OVER_2.5"],
            "M4_KG_var":m4["markets"]["BTTS_YES"],
        })
    return {
        "schema":"263_real_4617_asof_ten_league_math_readiness_v1",
        "historical_sha256":digest,
        "history_provenance":"RESEARCH_RESULTS_ONLY_43_PARTIALLY_OFFICIAL_REVIEWED",
        "cutoff_date_exclusive":CUTOFF,
        "n_source_rows":len(rows),"n_full_90min_eligible":len(full),
        "n_awarded_abandoned_training_excluded":len(partial_exclusions),
        "full_match_policy_sha256":policy_sha,
        "n_leagues":len(records),
        "model_settings":vars(settings),
        "fit_mode":"ONE_FIXED_ASOF_RESEARCH_SMOKE_NOT_BACKTEST_OR_LIVE_FORECAST",
        "all_M4_ten_league_smokes_available":True,
        "official_pilot_count_changed":0,"betting_authorized":False,
        "no_odds_api_calls":True,
        "leagues":records,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--history",default="data/results_only_263/2026-11-10_completed_4617_scores_only.csv")
    p.add_argument("--lock",default="experiments/263/m4_lock.json")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    report=audit(args.history,lock=args.lock)
    output=Path(args.out)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x",encoding="utf-8") as f:
        json.dump(report,f,sort_keys=True,ensure_ascii=False,indent=2)
        f.write("\n")
    print("REAL_4617_AUDIT_SUMMARY="+json.dumps({
        "n_source":report["n_source_rows"],
        "eligible":report["n_full_90min_eligible"],
        "excluded_abandoned":report["n_awarded_abandoned_training_excluded"],
        "leagues":report["n_leagues"],
        "models_by_league":[{
           "league":row["league"],"history":row["eligible_history"],
           "B":row["B"],"C2":row["C2"],"C3":row["C3"],
           "M4":row["M4"]}
           for row in report["leagues"]]},ensure_ascii=False))
if __name__=="__main__":main()
