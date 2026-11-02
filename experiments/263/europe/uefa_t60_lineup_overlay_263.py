"""2.6.3 EUROPE T-60 FIRST XI overlay; no full fixture hunt required.

Runs AFTER the accepted user-supplied-time ten-league gate. Optional trusted
lineup collector provides one observed match-centre observation including:
competition, exact 2 participants, source date/time, and confirmed starting XI.
No direct trusted adapter is implemented here: GitHub cannot automatically
reach UEFA; a JSON/source claim alone is NEVER an independent source fetch.
Missing lineup, mixed predicted/confirmed, stale evidence, mismatched teams,
source time conflict or unavailable provider => lineup UNSUPPORTED, base
pre-match data research MAY CONTINUE. No lambda/EV/model/pilot changes.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
from urllib.parse import urlsplit
from uefa_user_time_research_263 import requested_europe_research
from uefa_ten_league_scope_gate_263 import norm

VERSION="263_UEFA_PREMATCH_XI_MATCH_ANCHOR_v1"
HOSTS={"www.uefa.com","uefa.com","www.livescore.com","livescore.com",
       "www.fotmob.com","fotmob.com","www.sofascore.com","sofascore.com",
       "www.espn.com","espn.com","www.mackolik.com","mackolik.com"}

def source_url_ok(value):
    if not isinstance(value,str):return False
    try:
        u=urlsplit(value)
        return u.scheme=="https" and u.netloc.lower() in HOSTS and bool(u.path and u.path!="/") and (
            u.username is None and u.password is None and u.port is None and
            u.query=="" and u.fragment=="")
    except ValueError:return False

def aware(value):
    if not isinstance(value,str):return None
    try:
        t=datetime.fromisoformat(value.replace("Z","+00:00"))
        if t.tzinfo is None:return None
        return t.astimezone(timezone.utc)
    except ValueError:return None

def valid_xi(players):
    return (isinstance(players,list) and len(players)==11 and
            all(isinstance(x,str) and 1<=len(x.strip())<=120 for x in players)
            and len({norm(x) for x in players})==11)

def review_lineup_observation(event,request,index,now):
    """Treat callback outputs as CLAIMS until independently reviewed outside CI."""
    status={"schema":VERSION,"status":"LINEUPS_NOT_CONFIRMED",
            "analysis_can_continue":True,"official_fixture_research_required":False,
            "match_identity_checked_against_local_registry":False,
            "lineup_source_independently_fetched_by_github":False,
            "lineup_source_verified_in_this_call":False,
            "lineup_math_effect_authorized":False,
            "model_percentages_adjusted":False,
            "pilot_recorded":False,
            "home_starting_xi":None,"away_starting_xi":None}
    if event is None:
        status["reason"]="NO_MATCH_CENTRE_LINEUPS_PUBLISHED_OR_RETRIEVED"
        return status
    required={"competition","home","away","kickoff_utc","observed_at_utc",
              "source_url","lineup_status","home_starting_xi","away_starting_xi"}
    if not isinstance(event,dict) or set(event)!=required:
        status["reason"]="LINEUP_EVIDENCE_FIELDS_INVALID"
        return status
    if event["competition"]!=request["competition"]:
        status["reason"]="WRONG_UEFA_COMPETITION"
        return status
    h=index["aliases"].get(norm(event["home"])) if isinstance(event["home"],str) else None
    a=index["aliases"].get(norm(event["away"])) if isinstance(event["away"],str) else None
    scope=request["scope"]
    if (h is None or a is None
        or h!=scope["home"]["canonical_team_id"]
        or a!=scope["away"]["canonical_team_id"]):
        status["reason"]="LINEUPS_BELONG_TO_DIFFERENT_MATCH_OR_UNRESOLVED_TEAM"
        return status
    status["match_identity_checked_against_local_registry"]=True
    source_time=aware(event["kickoff_utc"])
    observed=aware(event["observed_at_utc"])
    reported=aware(request["reported_kickoff_utc"])
    if source_time is None or reported is None or observed is None:
        status["reason"]="INVALID_KICKOFF_OR_OBSERVATION_TIMESTAMPS"
        return status
    if abs((reported-source_time).total_seconds())>900:
        status["reason"]="USER_VS_SOURCE_KICKOFF_CONFLICT_GT_15_MIN"
        return status
    if not observed<=now<source_time:
        status["reason"]="AFTER_KICKOFF_OR_FUTURE_LINEUP_OBSERVATION"
        return status
    if now-observed>timedelta(minutes=90):
        status["reason"]="STALE_LINEUP_OBSERVATION"
        return status
    if not source_url_ok(event["source_url"]):
        status["reason"]="UNREVIEWED_LINEUP_SOURCE_HOST"
        return status
    if event["lineup_status"]!="CONFIRMED":
        status["reason"]="PREDICTED_OR_UNPUBLISHED_XI_NOT_ACCEPTED"
        return status
    if not valid_xi(event["home_starting_xi"]) or not valid_xi(event["away_starting_xi"]):
        status["reason"]="MISSING_OR_DUPLICATE_XI_PLAYERS"
        return status
    # It is legal to preserve a source claim for web-assisted review.
    # Do NOT claim independent GitHub source verification or authorize math.
    status.update(status="CONFIRMED_LINEUP_SOURCE_CLAIM_MATCHED_AWAITING_SOURCE_REVIEW",
                  reason="MATCH_TIME_AND_PLAYER_SHAPE_PASS_SOURCE_REVIEW_STILL_REQUIRED",
                  source_url=event["source_url"],
                  observed_at_utc=observed.isoformat(),
                  source_kickoff_utc=source_time.isoformat(),
                  home_starting_xi=event["home_starting_xi"],
                  away_starting_xi=event["away_starting_xi"])
    return status

def requested_with_matchday_lineup(competition,home,away,local_date,local_time,
                                  *,index,now,lineup_provider=None):
    """Research gate FIRST; provider never called when blocked or not yet T-120."""
    if now.tzinfo is None:raise ValueError("TIMEZONE_AWARE_NOW_REQUIRED")
    result,_=requested_europe_research(competition,home,away,local_date,
                                      local_time,index=index,now=now)
    if not result["data_research_allowed"]:
        result["lineup_observation"]={"schema":VERSION,
           "status":"LINEUP_LOOKUP_SKIPPED_DUE_TO_EARLY_GATE",
           "analysis_can_continue":False}
        return result
    cutoff=aware(result["reported_kickoff_utc"])
    if cutoff-now.astimezone(timezone.utc)>timedelta(minutes=120):
        event=None
        reason="LINEUP_CHECK_WINDOW_NOT_YET_OPEN"
    else:
        reason=None
        try:
            event=lineup_provider(result) if callable(lineup_provider) else None
        except Exception:
            event=None
            reason="LINEUP_SOURCE_PROVIDER_UNAVAILABLE"
    lineup=review_lineup_observation(event,result,index,now.astimezone(timezone.utc))
    if reason:lineup["reason"]=reason
    result["lineup_observation"]=lineup
    # The match data research gate is independent of published first elevens.
    return result
