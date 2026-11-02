"""Europe-only pre-kickoff match incentives and aggregate context.

Observational feature contract, NOT a prediction model or automatic low-goal
factor. Every source claim remains UNVERIFIED until an independent UEFA read.
Strict pre-kickoff timestamps prevent post-match standing/score leakage.
"""
from __future__ import annotations
from urllib.parse import urlsplit
from uefa_stage_263 import aware, source_id

VERSION="263_EUROPE_PREMATCH_CONTEXT_ONLY_v1"
class EuropeContextError(ValueError): pass

def integer(value, field, lower, upper):
    if type(value) is not int or not lower<=value<=upper:
        raise EuropeContextError(field+"_OUT_OF_RANGE")
    return value

def official_context_link(competition,link):
    if not isinstance(link,str):
        raise EuropeContextError("UEFA_CONTEXT_LINK_MISSING")
    u=urlsplit(link)
    comp={"UEFA_CL":"uefachampionsleague","UEFA_EL":"uefaeuropaleague"}.get(competition)
    if comp is None:
        raise EuropeContextError("UNSUPPORTED_TOURNAMENT")
    if (u.scheme!="https" or u.netloc.lower() not in ("www.uefa.com","uefa.com")
        or u.query or u.fragment or u.username or u.password
        or not u.path.startswith("/"+comp+"/")):
        raise EuropeContextError("UEFA_CONTEXT_SOURCE_NOT_OFFICIAL_FORMAT")
    # A correctly shaped URL never proves that a source was really accessed.
    return link

def standing(snapshot,field):
    if not isinstance(snapshot,dict) or set(snapshot)!={"played","points","goal_difference","rank"}:
        raise EuropeContextError(field+"_STANDING_FIELDS")
    played=integer(snapshot["played"],field+"_PLAYED",0,7)
    points=integer(snapshot["points"],field+"_POINTS",0,21)
    if points>played*3:
        raise EuropeContextError(field+"_POINTS_GREATER_THAN_MAX")
    goals=integer(snapshot["goal_difference"],field+"_GD",-100,100)
    rank=integer(snapshot["rank"],field+"_RANK",1,36)
    zone=("CURRENT_TOP_8" if rank<=8 else
          "CURRENT_PLAYOFF_9_24" if rank<=24 else "CURRENT_OUTSIDE_25_36")
    return {"played":played,"points":points,"goal_difference":goals,
            "rank":rank,"current_table_zone_not_final_result":zone,
            "remaining_league_games":8-played}

def context_for(candidate,pre_match,as_of):
    if not isinstance(candidate,dict) or not isinstance(pre_match,dict):
        raise EuropeContextError("CANDIDATE_AND_CONTEXT_OBJECTS_REQUIRED")
    if candidate.get("result_state")!="FUTURE_SCHEDULED_CANDIDATE":
        raise EuropeContextError("ONLY_FUTURE_CANDIDATE_CONTEXT")
    competition=candidate.get("competition")
    asof=aware(as_of,"ASOF")
    kickoff=aware(candidate.get("kickoff_utc"),"KICKOFF")
    observed=aware(pre_match.get("observed_at"),"OBSERVED")
    if not observed<=asof<kickoff:
        raise EuropeContextError("POST_KICKOFF_OR_FUTURE_CONTEXT_LEAKAGE")
    source=official_context_link(competition,pre_match.get("source_url"))
    phase=candidate.get("round")
    if phase not in ("LEAGUE_PHASE","QUALIFYING","KNOCKOUT","FINAL"):
        raise EuropeContextError("UNSUPPORTED_STAGE")
    shared={"schema":VERSION,"fixture_id":candidate["id"],"competition":competition,
            "phase":phase,"snapshot_checked_at_utc":observed.isoformat(),
            "analysis_at_utc":asof.isoformat(),"kickoff_utc":kickoff.isoformat(),
            "source_url":source,
            "data_status":"OPERATOR_SOURCE_CLAIM_NOT_INDEPENDENTLY_RECHECKED",
            "90_minute_market_only":True,
            "goal_multiplier":None,
            "goal_increase_decrease_not_inferred":True,
            "model_effect_estimated":False,"models_promoted":[],
            "forecast_authorized":False,"ABC_authorized":False,
            "pilot_registered":False,"domestic_leagues_modified":False}
    if phase=="LEAGUE_PHASE":
        if set(pre_match)!={"observed_at","source_url","matchday","standings"}:
            raise EuropeContextError("LEAGUE_PHASE_CONTEXT_FIELDS")
        matchday=integer(pre_match["matchday"],"MATCHDAY",1,8)
        raw=pre_match["standings"]
        if not isinstance(raw,dict) or set(raw)!={"home","away"}:
            raise EuropeContextError("TWO_PREMATCH_STANDINGS_REQUIRED")
        h=standing(raw["home"],"HOME");a=standing(raw["away"],"AWAY")
        if h["rank"]==a["rank"]:
            raise EuropeContextError("DUPLICATE_STANDING_RANK")
        return {**shared,"format":"36_TEAMS_EIGHT_DIFFERENT_OPPONENTS",
                "matchday":matchday,
                "home_standing_before_kickoff":h,
                "away_standing_before_kickoff":a,
                "points_gap_home_minus_away":h["points"]-a["points"],
                "goal_difference_gap_home_minus_away":h["goal_difference"]-a["goal_difference"],
                "goal_difference_tiebreak_exists":True,
                "top8_or_top24_outcome_not_determined_by_current_rank":True,
                "must_win_or_cautious_tactics_not_deduced":True}
    if phase in ("QUALIFYING","KNOCKOUT"):
        allowed={"observed_at","source_url","leg","first_leg_source_url","first_leg_goals_for_current_home",
                 "first_leg_goals_for_current_away"}
        if set(pre_match)-allowed or not {"observed_at","source_url","leg"}.issubset(pre_match):
            raise EuropeContextError("TWO_LEG_CONTEXT_FIELDS")
        leg=integer(pre_match["leg"],"LEG",1,2)
        prior_fields={"first_leg_source_url","first_leg_goals_for_current_home",
                      "first_leg_goals_for_current_away"}
        if leg==1 and set(pre_match)&prior_fields:
            raise EuropeContextError("FIRST_LEG_CANNOT_HAVE_PRIOR_AGGREGATE")
        if leg==2 and not prior_fields.issubset(pre_match):
            raise EuropeContextError("SECOND_LEG_NEEDS_PREVIOUS_FINAL_SCORE")
        delta=None;prior=None
        if leg==2:
            source_id(competition,pre_match["first_leg_source_url"])
            if pre_match["first_leg_source_url"]==candidate.get("source_url"):
                raise EuropeContextError("FIRST_LEG_MUST_BE_DIFFERENT_MATCH_ID")
            h=integer(pre_match["first_leg_goals_for_current_home"],"PRIOR_HOME_GOALS",0,40)
            a=integer(pre_match["first_leg_goals_for_current_away"],"PRIOR_AWAY_GOALS",0,40)
            delta=h-a
            prior={"first_leg_uefa_source":pre_match["first_leg_source_url"],
                   "home_team_aggregate_goals_before_kickoff":h,
                   "away_team_aggregate_goals_before_kickoff":a,
                   "aggregate_difference_for_home_before_kickoff":delta,
                   "previous_result_independently_verified":False}
        return {**shared,"format":"TWO_LEG_AGGREGATE","leg":leg,
                "aggregate_before_kickoff":prior,
                "qualification_rule":"HIGHER_AGGREGATE_GOALS_ADVANCES",
                "extra_time_penalties_excluded_from_90min_market":True,
                "aggregate_score_does_not_imply_goal_multiplier":True}
    if set(pre_match)!={"observed_at","source_url"}:
        raise EuropeContextError("FINAL_CONTEXT_FIELDS")
    if candidate.get("neutral_venue") is not True:
        raise EuropeContextError("FINAL_NEUTRAL_VENUE_REQUIRED")
    return {**shared,"format":"SINGLE_NEUTRAL_VENUE_FINAL",
            "one_match_trophy_decider":True,
            "extra_time_penalties_excluded_from_90min_market":True}
