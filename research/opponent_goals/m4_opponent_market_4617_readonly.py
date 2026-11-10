"""M4 as-of opponent-strength -> KG/2.5 read-only explanation.

NO new model or calibration. It diagnoses that the frozen M4 actually changes
home/away lambda by opponent's learned defence/attack and away-venue terms.
It also independently checks two mathematically exact Poisson market identities
on all 10 leagues' genuine 4617 accepted results-only history.

Do not interpret a counterfactual matchup as a real upcoming fixture, betting
pick, or validation of predictive accuracy.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments/263"))
from exp_263_batch import clean_rows
from full_match_eligibility_263 import full_match_rows
from m4_integrated import fit_m4, predict_m4, score_markets, use_lock

HISTORY=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
OLD=ROOT/"data/quad_accepted_263/extended_history.csv"
LOCK=ROOT/"experiments/263/m4_lock.json"
HISTORY_SHA="637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89"
OLD_SHA="1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9"
LEAGUES=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")

class DiagnosticInvalid(ValueError):
    pass

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(ok,msg):
    if not ok:raise DiagnosticInvalid(msg)

def explain_strength(fit,home,away):
    """Deterministic exact decomposition of *unchanged* live M4 formula."""
    beta,ix,m,n=fit
    require(home in ix and away in ix and home!=away,"INSUFFICIENT_IDENTIFIED_TEAMS")
    def b(team,at):return float(beta[at+ix[team]])
    parts={
        "home_base":float(beta[0]),
        "home_team_attack":b(home,2),
        "home_team_venue_attack":b(home,2+2*m),
        "opponent_away_defence":b(away,2+m),
        "opponent_away_venue_defence":b(away,2+5*m),
        "away_base":float(beta[1]),
        "opponent_away_attack":b(away,2),
        "opponent_away_venue_attack":b(away,2+3*m),
        "home_team_defence":b(home,2+m),
        "home_team_venue_defence":b(home,2+4*m),
    }
    log_home=sum(parts[k] for k in ("home_base","home_team_attack","home_team_venue_attack",
                                     "opponent_away_defence","opponent_away_venue_defence"))
    log_away=sum(parts[k] for k in ("away_base","opponent_away_attack","opponent_away_venue_attack",
                                     "home_team_defence","home_team_venue_defence"))
    expected=predict_m4(fit,home,away)
    require(expected is not None,"M4_EXPECTED_GOALS_OUTSIDE_SAFE_RANGE")
    actual=(math.exp(log_home),math.exp(log_away))
    require(all(math.isclose(a,b,abs_tol=1e-11,rel_tol=1e-11)
                for a,b in zip(actual,expected)),"OPPONENT_COMPONENTS_NOT_MATCHING_M4")
    return {
        "home_lambda":expected[0],"away_lambda":expected[1],
        "opponent_home_scoring_log_effect":(parts["opponent_away_defence"]+
                                            parts["opponent_away_venue_defence"]),
        "opponent_away_scoring_log_effect":(parts["opponent_away_attack"]+
                                            parts["opponent_away_venue_attack"]),
        "exact_frozen_m4_decomposition":parts,
    }

def closed_forms(lh,la):
    """Independent analytic Poisson probability reference, no matrix reuse."""
    require(all(math.isfinite(z) and 0.05<=z<=5 for z in (lh,la)),"BAD_LAMBDA")
    total=lh+la
    btts=(-math.expm1(-lh))*(-math.expm1(-la))
    over25=1-math.exp(-total)*(1+total+total*total/2)
    return {"BTTS_YES":btts,"OVER_2.5":over25}

def verify_market(lh,la):
    raw=score_markets(lh,la)["markets"]
    ref=closed_forms(lh,la)
    for market in ref:
        require(math.isclose(raw[market],ref[market],abs_tol=2e-10,rel_tol=2e-10),
                "M4_GOAL_MARKET_INCONSISTENT_WITH_EXACT_POISSON_"+market)
    require(math.isclose(sum(raw["1X2"].values()),1,abs_tol=2e-10),
            "INVALID_MS_PROBABILITY_SUM")
    require(math.isclose(raw["BTTS_YES"]+raw["BTTS_NO"],1,abs_tol=2e-10),
            "INVALID_KG_PAIR")
    require(math.isclose(raw["OVER_2.5"]+raw["UNDER_2.5"],1,abs_tol=2e-10),
            "INVALID_25_PAIR")
    return ref

def run(cutoff="2026-11-11"):
    date.fromisoformat(cutoff)
    require(cutoff>="2026-11-11","DIAGNOSTIC_CANNOT_RETROFIT_PRIOR_DAY")
    require(sha(OLD)==OLD_SHA and sha(HISTORY)==HISTORY_SHA,"INPUT_SOURCE_SHA_CHANGED")
    rows=clean_rows(HISTORY)
    old=clean_rows(OLD)
    require(len(rows)==4617 and len(old)==4518,"SOURCE_ROW_COUNT_CHANGED")
    oldmap={r["fixture_id"]:r for r in old}
    require(len(oldmap)==4518,"DUPLICATE_ORIGINAL_FIXTURE")
    require(all(r["fixture_id"] in oldmap and r==oldmap[r["fixture_id"]] for r in rows[:4518]),
            "ORIGINAL_4518_NOT_IDENTICAL")
    new=rows[4518:]
    require(len(new)==99 and len({r["fixture_id"] for r in new})==99,
            "99_NEW_MATCHES_NOT_UNIQUE")
    require(all(r["match_date"]<cutoff for r in new),"NEW_SCORE_FROM_FUTURE")
    lock=json.loads(LOCK.read_text(encoding="utf-8"))
    settings=use_lock(lock)
    require(lock["m4_engine_sha256"]==sha(ROOT/"experiments/263/m4_integrated.py"),
            "FROZEN_M4_ENGINE_SHA_CHANGED")
    out=[]
    for league in LEAGUES:
        league_rows=[r for r in rows if r["league"]==league and r["match_date"]<cutoff]
        eligible,excluded,eligibility_sha=full_match_rows(league_rows)
        require(len(eligible)>=60,"M4_MIN_TRAIN_NOT_MET_"+league)
        fit=fit_m4(eligible,league,cutoff,settings)
        require(fit is not None and fit[3]==len(eligible),"M4_FIT_FAILED_"+league)
        beta,ix,m,n=fit
        hcount=Counter(r["home_id"] for r in eligible)
        acount=Counter(r["away_id"] for r in eligible)
        anchors=sorted((x for x in ix if hcount[x]>=8),key=lambda x:(-hcount[x],x))
        require(anchors,"NO_STABLE_HOME_TEAM_"+league)
        home=anchors[0]
        opponents=sorted((x for x in ix if x!=home and acount[x]>=8),
            key=lambda away:(float(beta[2+m+ix[away]]+beta[2+5*m+ix[away]]),away))
        require(len(opponents)>=4,"FEWER_THAN_FOUR_AWAY_OPPONENTS_"+league)
        strong,weak=opponents[0],opponents[-1]
        # Strong/weak label is strictly M4's fitted defensive component.
        # It does NOT claim independent real-world or league-table ranking.
        pairs=[("more_resistant_model_defence",strong),
               ("more_permissive_model_defence",weak)]
        records=[]
        for label,away in pairs:
            example=explain_strength(fit,home,away)
            lam_h,lam_a=example["home_lambda"],example["away_lambda"]
            reference=verify_market(lam_h,lam_a)
            records.append({"diagnostic_opponent_tag":label,"opponent_internal_team_id":away,
                            "away_games_in_history":acount[away],
                            "m4_components":example,
                            "independent_closed_form_reference":reference,
                            "market_probabilities":{k:score_markets(lam_h,lam_a)["markets"][k]
                                                    for k in ("BTTS_YES","OVER_2.5","UNDER_2.5")}})
        first,second=records
        d1=first["m4_components"];d2=second["m4_components"]
        defender_change=d2["opponent_away_scoring_log_effect"]-d1["opponent_away_scoring_log_effect"]
        home_lambda_change=d2["opponent_home_scoring_log_effect"]-d1["opponent_home_scoring_log_effect"]
        require(home_lambda_change>0,"STRONG_WEAK_DEFENCE_INCORRECTLY_ORDERED_"+league)
        require(math.isclose(math.log(d2["home_lambda"]/d1["home_lambda"]),
                              home_lambda_change,abs_tol=1e-10),
                "OPPONENT_DEFENCE_NOT_PROPAGATED_TO_HOME_GOALS_"+league)
        require(math.isclose(math.log(d2["away_lambda"]/d1["away_lambda"]),
                              defender_change,abs_tol=1e-10),
                "OPPONENT_ATTACK_NOT_PROPAGATED_TO_AWAY_GOALS_"+league)
        out.append({
          "league":league,"asof_exclusive":cutoff,
          "full_match_train_rows":n,"partial_match_exclusion_count":len(excluded),
          "new_99_archive_rows_on_this_league":sum(r["league"]==league for r in new),
          "fixed_home_team_internal_id":home,"home_games_in_history":hcount[home],
          "counterfactuals":records,
          "opponent_only_home_lambda_log_delta":home_lambda_change,
          "opponent_only_away_lambda_log_delta":defender_change,
          "btts_probability_delta_pp":100*(second["market_probabilities"]["BTTS_YES"]-
                                            first["market_probabilities"]["BTTS_YES"]),
          "over25_probability_delta_pp":100*(second["market_probabilities"]["OVER_2.5"]-
                                              first["market_probabilities"]["OVER_2.5"]),
        })
    require(len(out)==10 and sum(x["new_99_archive_rows_on_this_league"] for x in out)==99,
            "RESEARCH_DIAGNOSTIC_DID_NOT_COVER_ALL_TEN_AND_99")
    return {
      "schema":"263_M4_OPPONENT_GOALS_KG_O25_4617_EXACT_DECOMPOSITION_V1",
      "status":"FROZEN_M4_MATH_EXPLAINABILITY_ONLY_NO_NEW_MODEL",
      "asof_exclusive":cutoff,
      "source_history_sha256":HISTORY_SHA,"original_4518_sha256":OLD_SHA,
      "leagues_diagnosed":10,"new_99_score_rows_present":99,
      "frozen_m4_engine_sha256":lock["m4_engine_sha256"],
      "m4_settings_unchanged":lock["settings"],
      "market_analytic_identity_verified":True,
      "opponent_effect_is_already_present_in_frozen_M4":True,
      "proof_not_new_predictive_accuracy":True,
      "no_model_promotion_or_historical_forecast_rewrite":True,
      "details":out,
      "limitations":[
        "All matchup counterfactuals are model explanations, not real fixtures or predictions.",
        "An opponent's ranking is model-fitted away defence only, NOT an Elo or independent league quality.",
        "Opponent strength changes lambda through M4 attack/defence and venue; KG and 2.5 over then follow independent Poisson.",
        "No independent goal correlation / tempo interaction is present beyond these lambdas.",
        "This audit cannot establish that an adjustment to KG or OVER2.5 would improve accuracy; old 984-game DC/bivariate tests are NOT repeated.",
        "Not an external source attestation or an approved betting forecast."]
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="")
    args=p.parse_args()
    report=run()
    raw=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if args.out:
        Path(args.out).write_text(raw,encoding="utf-8")
    print(json.dumps({
      "status":report["status"],"leagues":report["leagues_diagnosed"],
      "additional_scores":report["new_99_score_rows_present"],
      "opponent_effects_active":report["opponent_effect_is_already_present_in_frozen_M4"],
      "same_mathematics":report["m4_settings_unchanged"]
    },ensure_ascii=False))
