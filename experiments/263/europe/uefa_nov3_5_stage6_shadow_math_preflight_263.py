"""Stage 6 UEFA 2026-11-03..05: two in-memory shadow math paths for 17 matches.

No saved per-match probabilities, goals, tips or immutable ledgers.
Reuse the *unchanged* 2025/26 retrospective mathematical implementation.
The historical source was REVIEW_ONLY, so beta is exploratory, never an
approved betting or operational model parameter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from uefa_elo_m0_paired_retrospective_263 import (
    lambdas, predict, base_features, clip, K_SMOOTH, CLIP_HI, CLIP_LO
)

VERSION="263_UEFA_STAGE6_17_FIXTURE_TWO_SHADOW_MATH_PREFLIGHT_V1"
SOURCES={
    "stage4":"56e3210d425aeaa6b2a7bfc9d3244a0ae644b7a55b6c133308406a4647cb4c97",
    "stage5":"6b4aa434357fdd9b75d0f6c0f3e730b48dec6e7dec1cf6266c7d328d1ce45c5c",
    "retro":"03c1b1fea46bcf941ad1271a0fe6fb0d536df8dcff9d2182a30bca91b7cdff17",
}
FIRST_KICKOFF_UTC="2026-11-03T17:45:00+00:00"
EXPECTED_DAYS={"2026-11-03":6,"2026-11-04":6,"2026-11-05":5}
EXPECTED_CUPS={"UEFA_CL":12,"UEFA_EL":5}
OUTPUT=Path("data/europe_staged_263/stage6_shadow_math_only/math_preflight_audit_NO_PREDICTIONS.json")

class PreflightError(ValueError):pass

def checked_json(path,sha):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sha:
        raise PreflightError("FROZEN_INPUT_HASH_CHANGED:"+Path(path).name)
    return json.loads(raw)

def aware_utc(v):
    try:x=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    except (TypeError,ValueError) as e:raise PreflightError("UNREADABLE_TIMESTAMP") from e
    if x.tzinfo is None:raise PreflightError("NAIVE_TIMESTAMP")
    return x.astimezone(timezone.utc)

def upstream_inputs(stage4,stage5,retro,scope):
    """Fail closed without re-running or retraining the prior experiments."""
    if (stage4.get("schema")!="263_UEFA_NOV3_5_STAGE4_NINE_LEAGUE_PREMATCH_GOALS_V1"
        or stage4.get("fixture_status_counts")!={"DESCRIPTIVE_GOAL_PROFILE_SOURCE_READY":17}
        or stage4.get("approved_international_strength_or_uefa_poisson_model") is not False
        or stage4.get("probabilities_calculated") is not False
        or stage4.get("prediction_saved") is not False):
        raise PreflightError("STAGE4_SOURCE_OR_MODEL_POLICY_CHANGED")
    if (stage5.get("schema")!="263_UEFA_17_FIXTURES_STAGE5_ELO_AND_NEWS_SOURCE_AUDIT_V1"
        or stage5.get("coverage",{}).get("elo_with_rd_and_before_kickoff")!=34
        or stage5.get("coverage",{}).get("matches")!=17
        or stage5.get("safety",{}).get("elo_influence_on_lambda") is not False
        or stage5.get("safety",{}).get("model_forecast_authorized") is not False
        or stage5.get("safety",{}).get("pilot_recorded") is not False):
        raise PreflightError("STAGE5_ELO_OR_MODEL_POLICY_CHANGED")
    if (retro.get("schema")!="263_EUROPE_ELO_M0_PAIRED_RETROSPECTIVE_DISCOVERY_V1"
        or retro.get("status")!="RETROSPEKTIF_KESIF_NO_LIVE_PREGAME_PROOF"
        or retro.get("Elo_weight_approved_for_model") is not False
        or retro.get("goal_lambda_approved") is not False
        or retro.get("source_read_only_training_permitted") is not False
        or retro.get("source_coverage",{}).get("paired_total")!=124):
        raise PreflightError("EXPERIMENTAL_BETA_SOURCE_POLICY_CHANGED")
    if (scope.get("schema")!="UEFA_263_NOV3_5_OFFICIAL_FIXTURE_SCOPE_ACCEPTANCE_REVIEW"
        or scope.get("eligible_total")!=17
        or len(scope.get("verified_fixtures",[]))!=17):
        raise PreflightError("STAGE3_FIXTURE_SCOPE_CHANGED")
    proto=retro["fixed_protocol"]
    if not (proto["training_n"]==76 and proto["validation_n"]==16 and proto["holdout_n"]==32
        and proto["k_smoothing"]==K_SMOOTH==5.0
        and proto["goal_lambda_bounds"]==[CLIP_LO,CLIP_HI]
        and proto["Elo_normalization"]==400
        and proto["Elo_delta_bounds"]==[-2,2]
        and proto["beta_bounds"]==[-1,1]
        and proto["ridge"]==20):
        raise PreflightError("FROZEN_RETRO_MATH_PROTOCOL_CHANGED")
    if not (math.isclose(proto["UEFA_train_home_goal_mean"],135/76,abs_tol=1e-12)
            and math.isclose(proto["UEFA_train_away_goal_mean"],101/76,abs_tol=1e-12)
            and math.isclose(proto["beta_retrospective_fitted"],0.5254760017675575,abs_tol=1e-12)):
        raise PreflightError("UNEXPECTED_HISTORIC_BASE_OR_EXPLORATORY_BETA")
    return proto

def to_retro_profile(profile,role,league,match_date):
    """Adapter only: do not recompute a historical result or invent home/away data."""
    if profile.get("match_cutoff_date_exclusive")!=match_date:
        raise PreflightError("STAGE4_PROFILE_TARGET_DATE_DRIFT")
    if profile.get("team_id") is None:
        raise PreflightError("MISSING_CANONICAL_ID")
    if (profile.get("no_xg_or_h2h_or_elo_adjustments") is not True
        or profile.get("past_current_season_games",0)<4
        or profile.get("past_current_season_home_games",0)<2
        or profile.get("past_current_season_away_games",0)<2
        or profile.get("domestic_league_games_before_match",0)<30):
        raise PreflightError("SOURCE_PROFILE_INSUFFICIENT_OR_NON_GOAL_FEATURE")
    if len(profile.get("recent_5",[]))!=5:
        raise PreflightError("FIVE_MATCH_FORM_UNEXPECTED")
    for recent in profile["recent_5"]:
        if (recent.get("date",match_date)>=match_date
            or recent.get("opponent_previous_domestic_ppg") is None):
            raise PreflightError("RECENT_MATCH_DATE_LEAK_OR_OPPONENT_UNKNOWN")
    if (profile.get("last_completed_domestic_match") is None or
        profile["last_completed_domestic_match"]>=match_date):
        raise PreflightError("LAST_DOMESTIC_RESULT_FROM_FUTURE")
    if role not in ("home","away"):
        raise PreflightError("ROLE_UNEXPECTED")
    for field in (
        "domestic_home_goals_for","domestic_home_goals_against",
        "domestic_away_goals_for","domestic_away_goals_against",
        "past_current_season_home_games","past_current_season_away_games"):
        x=profile.get(field)
        if type(x) is not int or x<0:
            raise PreflightError("ROLE_GOALS_MISSING_OR_INVALID:"+field)
    league_home=profile.get("domestic_league_home_goals_per_game")
    league_away=profile.get("domestic_league_away_goals_per_game")
    if (not isinstance(league_home,(float,int)) or
        not isinstance(league_away,(float,int)) or
        not 0<league_home<10 or not 0<league_away<10):
        raise PreflightError("LEAGUE_HOME_AWAY_BASELINE_BAD")
    return {
        "domestic_home_goals_scored":profile["domestic_home_goals_for"],
        "domestic_home_goals_conceded":profile["domestic_home_goals_against"],
        "domestic_away_goals_scored":profile["domestic_away_goals_for"],
        "domestic_away_goals_conceded":profile["domestic_away_goals_against"],
        "past_domestic_home_games":profile["past_current_season_home_games"],
        "past_domestic_away_games":profile["past_current_season_away_games"],
        "domestic_league_home_goals_per_game_before_target":league_home,
        "domestic_league_away_goals_per_game_before_target":league_away,
        "team_id":profile["team_id"],
        "domestic_league":league,
    }

def make_pair(stage4_fixture,stage5_fixture,stage3_fixture):
    fid=stage4_fixture["uefa_match_id"]
    if fid!=stage5_fixture.get("uefa_match_id") or fid!=stage3_fixture.get("uefa_match_id"):
        raise PreflightError("UEFA_MATCH_ID_NOT_PAIRED")
    if not (stage4_fixture["kickoff_utc"]==stage5_fixture["kickoff_utc"]==stage3_fixture["kickoff_utc"]
            and stage4_fixture["competition"]==stage5_fixture["competition"]==stage3_fixture["competition"]
            and stage4_fixture["date"]==stage5_fixture["date"]==stage3_fixture["date"]):
        raise PreflightError("FIXTURE_TIME_COMPETITION_MISMATCH")
    for side in ("home","away"):
        team_id=stage4_fixture[side+"_id"]
        if (team_id!=stage5_fixture[side+"_team"]["canonical_team_id"] or
            team_id!=stage3_fixture[side+"_identity"]["canonical_team_id"]):
            raise PreflightError("PREMATCH_CANONICAL_CLUB_ID_MISMATCH")
    ko=aware_utc(stage4_fixture["kickoff_utc"])
    if (aware_utc(stage4_fixture["data_collection_utc"])>=ko or
        stage4_fixture.get("status")!="DESCRIPTIVE_GOAL_PROFILE_SOURCE_READY"):
        raise PreflightError("STAGE4_SOURCE_CAPTURE_NOT_BEFORE_KICKOFF")
    h,away=stage5_fixture["home_team"],stage5_fixture["away_team"]
    if not all(
        d.get("board_as_of")=="2026-11-03" and
        d.get("last_match_date")<stage5_fixture["date"] and
        0<d.get("elo",0)<4000 and 0<d.get("rd",0)<1000 and
        d.get("identity_confidence")=="NAME_COUNTRY_EXACT_SOURCE_SLUG_ONLY_NO_SHARED_UEFA_ID"
        for d in (h,away)
    ):
        raise PreflightError("ELO_SCORE_RATING_RD_OR_IDENTITY_UNSAFE")
    if stage5_fixture.get("model_probs_generated") is not False:
        raise PreflightError("EARLIER_STAGE_PRETENDED_TO_PRODUCE_PREDICTIONS")
    return {
        "date":stage4_fixture["date"],
        "competition":stage4_fixture["competition"],
        "kickoff":ko,
        "home":{"elo":h["elo"],"profile":to_retro_profile(
            stage4_fixture["domestic_home"],"home",stage4_fixture["domestic_home_league"],stage4_fixture["date"])},
        "away":{"elo":away["elo"],"profile":to_retro_profile(
            stage4_fixture["domestic_away"],"away",stage4_fixture["domestic_away_league"],stage4_fixture["date"])},
    }

def compute_volatile(pair,home_baseline,away_baseline,beta):
    """Return ephemeral values to the caller, NEVER write them to disk."""
    lh0,la0=lambdas(pair,home_baseline,away_baseline,0.0)
    lh1,la1=lambdas(pair,home_baseline,away_baseline,beta)
    probs0,over0,btts0=predict(lh0,la0)
    probs1,over1,btts1=predict(lh1,la1)
    result={"M0":(lh0,la0,probs0,over0,btts0),
            "M0Elo":(lh1,la1,probs1,over1,btts1)}
    for name,(home,away,probs,over,btts) in result.items():
        if not (math.isfinite(home) and math.isfinite(away)
                and CLIP_LO<=home<=CLIP_HI and CLIP_LO<=away<=CLIP_HI
                and len(probs)==3 and all(math.isfinite(p) and 0<=p<=1 for p in probs)
                and math.isclose(sum(probs),1,abs_tol=1e-12)
                and 0<=over<=1 and 0<=btts<=1):
            raise PreflightError("POISSON_MASS_OR_PROBABILITY_INVARIANT_FAILED:"+name)
    return result

def audit(stage4,stage5,retro,scope,*,now=None):
    now=now or datetime.now(timezone.utc)
    now=aware_utc(now.isoformat()) if isinstance(now,datetime) else aware_utc(now)
    proto=upstream_inputs(stage4,stage5,retro,scope)
    fixtures=stage4["fixtures"];elolist=stage5["matches"];official=scope["verified_fixtures"]
    if not(len(fixtures)==len(elolist)==len(official)==17):
        raise PreflightError("EXPECTED_EXACTLY_17_PAIRED_FIXTURES")
    ids=[r["uefa_match_id"] for r in fixtures]
    if len(set(ids))!=17 or set(ids)!={m["uefa_match_id"] for m in elolist} or set(ids)!={m["uefa_match_id"] for m in official}:
        raise PreflightError("DUPLICATE_OR_UNMATCHED_UEFA_MATCH_ID")
    emap={m["uefa_match_id"]:m for m in elolist}
    fmap={m["uefa_match_id"]:m for m in official}
    first=min(aware_utc(f["kickoff_utc"]) for f in fixtures)
    if first!=aware_utc(FIRST_KICKOFF_UTC):
        raise PreflightError("FIRST_UEFA_KICKOFF_CHANGED")
    if now>=first:
        raise PreflightError("SHADOW_MATH_PREFLIGHT_TOO_LATE_FOR_ALL_17")
    e_captured=aware_utc(stage5["source_evidence"]["beyondelo_audited_utc"])
    if e_captured>=first or aware_utc(stage4["analysis_time_utc"])>=first:
        raise PreflightError("ARCHIVED_PREMATCH_SNAPSHOTS_NOT_BEFORE_FIRST_KICKOFF")
    n=Counter();cup=Counter();teams=set()
    max_probability_sum_residual=0.0
    max_role_factor=0.0
    # No array of per-match probabilities or correct-score selections is retained.
    for f in fixtures:
        s=emap[f["uefa_match_id"]];source=fmap[f["uefa_match_id"]]
        pair=make_pair(f,s,source)
        # The league-strength and recent opponent PPG remain explanatory only.
        factors=base_features(pair)
        if not all(math.isfinite(v) and 0<v<100 for v in factors):
            raise PreflightError("LEAGUE_RELATIVE_RATE_NUMERIC_INVALID")
        max_role_factor=max(max_role_factor,*factors)
        shadow=compute_volatile(pair,proto["UEFA_train_home_goal_mean"],
                                proto["UEFA_train_away_goal_mean"],
                                proto["beta_retrospective_fitted"])
        for output in shadow.values():
            max_probability_sum_residual=max(max_probability_sum_residual,
                abs(sum(output[2])-1))
        teams.update([f["home_id"],f["away_id"]])
        n[f["date"]]+=1;cup[f["competition"]]+=1
        del shadow
    if dict(n)!=EXPECTED_DAYS or dict(cup)!=EXPECTED_CUPS or len(teams)!=34:
        raise PreflightError("17_MATCH_DISTRIBUTION_OR_34_TEAM_GATE_FAILED")
    # Public report intentionally contains NO match identifier, lambda, single-match
    # probability, betting pick, model winner, record, or prediction ledger.
    return {
        "schema":VERSION,
        "status":"17_OF_17_VOLATILE_SHADOW_MATH_INVARIANTS_PASSED_NO_FORECAST_RECORD",
        "purpose":"Only in-memory 17-match M0 vs exploratory M0Elo numerical feasibility preflight",
        "matches_tested":17,
        "unique_teams_tested":34,
        "day_count":dict(sorted(n.items())),
        "competition_count":dict(sorted(cup.items())),
        "model_variants_tested":["M0_REFERENCE_ONLY","M0_PLUS_ELO_UNAPPROVED_SHADOW"],
        "historical_math_reused_unchanged":True,
        "historic_beta_used_only_in_unpersisted_shadow":True,
        "historic_coefficients_retrained_or_tuned":False,
        "home_away_roles_normalized_by_their_own_leagues":True,
        "recent_opponent_ppg_used_as_model_multiplier":False,
        "UEFA_country_coefficient_used_as_model_multiplier":False,
        "injury_or_unverified_lineups_used_as_model_multiplier":False,
        "xg_or_h2h_used":False,
        "every_kickoff_after_preflight_run":True,
        "all_inputs_pre_kickoff_captured":True,
        "max_probability_mass_normalization_error":max_probability_sum_residual,
        "any_per_match_lambda_or_probability_saved":False,
        "any_real_match_prediction_recorded":False,
        "pilot_recorded":False,
        "mathematical_calibration_or_main_approval":False,
        "main_branch_modified":False,
        "input_snapshots_sha256":SOURCES,
        "stage3_source":"experiments/263/evidence/uefa_2026_11_03_05_fixture_scope_review.json",
    }

def main():
    p=argparse.ArgumentParser()
    for x in ("stage4","stage5","retro","stage3"):
        p.add_argument("--"+x,required=True)
    p.add_argument("--out",default=str(OUTPUT))
    args=p.parse_args()
    out=Path(args.out)
    if "data/europe_staged_263/stage6_shadow_math_only" not in str(out):
        raise PreflightError("MATH_PREFLIGHT_REPORT_OUTPUT_NOT_QUARANTINED")
    out.parent.mkdir(parents=True,exist_ok=True)
    try:
        report=audit(
            checked_json(args.stage4,SOURCES["stage4"]),
            checked_json(args.stage5,SOURCES["stage5"]),
            checked_json(args.retro,SOURCES["retro"]),
            json.loads(Path(args.stage3).read_text(encoding="utf8")))
    except Exception as ex:
        report={"schema":VERSION,"status":"STAGE6_MATH_PREFLIGHT_BLOCKED",
            "error_type":type(ex).__name__,
            "reason":str(ex)[:250],
            "match_probabilities_saved":False,"main_modified":False,
            "pilot_recorded":False}
        out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print("STAGE6_BLOCKED="+json.dumps(report,ensure_ascii=False))
        raise
    out.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("STAGE6_MATH_PREFLIGHT="+json.dumps({
        "status":report["status"],"matches":report["matches_tested"],
        "teams":report["unique_teams_tested"],
        "max_probability_normalization_error":report["max_probability_mass_normalization_error"],
        "per_match_values_saved":False,"main_changed":False},ensure_ascii=False))

if __name__=="__main__":main()
