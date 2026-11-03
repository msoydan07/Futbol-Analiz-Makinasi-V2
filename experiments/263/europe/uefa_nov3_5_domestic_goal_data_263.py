"""2026-11-03 to 05 UEFA stage-4 domestic goal data audit, nine leagues, 17 fixtures.

Source: football-data.co.uk 2026/27 nine top-league season CSVs, downloaded once.
Never modify source CSV; archive bytes/SHA and fetch UTC. Do NOT inspect odds,
xG, H2H, Elo or future results. Descriptive inputs only; no lambda/probabilities.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
import re
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from mackolik_identity_gate_263 import _candidate_id, _memberships, _validate_identity_source
from uefa_ten_league_scope_gate_263 import validated_index

VERSION="263_UEFA_NOV3_5_STAGE4_NINE_LEAGUE_PREMATCH_GOALS_V1"
BASE="https://www.football-data.co.uk/mmz4281/2627"
DIVS={"ENG1":"E0","GER1":"D1","ESP1":"SP1","ITA1":"I1","FRA1":"F1",
      "NED1":"N1","POR1":"P1","BEL1":"B1","TUR1":"T1"}
SCOPE_PATH=Path("experiments/263/evidence/elo_uefa_active_cohort_2026_11_03.json")
FIXTURES_PATH=Path("experiments/263/evidence/uefa_2026_11_03_05_fixture_scope_review.json")
INDEX_PATH=Path("experiments/263/evidence/identity_index_263.json")
OUT_DIR=Path("data/europe_staged_263/2026_11_03_05_stage4_goals")
SOURCE_MAX_BYTES=2_000_000
SOURCE_TIMEOUT=20
MIN_TEAM_GAMES=4
MIN_EACH_VENUE=2
MIN_LEAGUE_GAMES=30

class DataAuditError(ValueError):pass

def parse_date(value):
    if not isinstance(value,str) or not value.strip():raise DataAuditError("MATCH_DATE_MISSING")
    for fmt in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d"):
        try:return datetime.strptime(value.strip(),fmt).date()
        except ValueError:pass
    raise DataAuditError("MATCH_DATE_UNREADABLE")

def parse_int(v):
    s=str(v or "").strip()
    return int(s) if s.isascii() and s.isdigit() else None

def get_source(league, now_utc):
    url=BASE+"/"+DIVS[league]+".csv"
    req=urllib.request.Request(url,headers={
        "User-Agent":"FootballAnalysis263-Research-Data-Audit/1.0",
        "Accept":"text/csv,*/*;q=0.5",
    })
    with urllib.request.urlopen(req,timeout=SOURCE_TIMEOUT) as response:
        final=urlsplit(response.geturl())
        if (response.status!=200 or final.scheme!="https" or
            final.hostname not in ("www.football-data.co.uk","football-data.co.uk") or
            final.path!="/mmz4281/2627/"+DIVS[league]+".csv"):
            raise DataAuditError("SOURCE_REDIRECT_OR_HTTP_REJECTED")
        raw=response.read(SOURCE_MAX_BYTES+1)
    received=datetime.now(timezone.utc)
    if len(raw)>SOURCE_MAX_BYTES or not raw:
        raise DataAuditError("SOURCE_EMPTY_OR_OVERSIZE")
    return raw,received,url

def decode_league(raw,league,index,members,source_now):
    """Parse real completed records, exact source alias only, no fuzzy matching."""
    if not isinstance(raw,bytes) or len(raw)>SOURCE_MAX_BYTES:
        raise DataAuditError("SOURCE_RAW_SIZE")
    try:source=raw.decode("utf-8-sig")
    except UnicodeError as e:raise DataAuditError("SOURCE_ENCODING") from e
    if "\x00" in source:raise DataAuditError("SOURCE_CONTAINS_NUL")
    reader=csv.DictReader(io.StringIO(source))
    required={"Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"}
    if not required.issubset(set(reader.fieldnames or ())):
        raise DataAuditError("SOURCE_REQUIRED_COLUMNS_MISSING")
    all_rows=list(reader)
    if not 1<=len(all_rows)<=1000:raise DataAuditError("SOURCE_SEASON_ROW_COUNT_UNEXPECTED")
    completed=[]
    unresolved=Counter();errors=[];counts=Counter();unique=set()
    for line,r in enumerate(all_rows,2):
        home=str(r.get("HomeTeam") or "").strip()
        away=str(r.get("AwayTeam") or "").strip()
        if not home and not away:
            counts["blank"]+=1;continue
        if not home or not away:
            errors.append({"line":line,"reason":"ONE_TEAM_EMPTY"});continue
        h=parse_int(r.get("FTHG"));a=parse_int(r.get("FTAG"))
        result=str(r.get("FTR") or "").strip().upper()
        if h is None and a is None and not result:
            counts["unplayed"]+=1;continue
        if h is None or a is None or result not in ("H","A","D"):
            errors.append({"line":line,"reason":"PARTIAL_SCORE"});continue
        if not 0<=h<=40 or not 0<=a<=40 or result!=("H" if h>a else "A" if h<a else "D"):
            errors.append({"line":line,"reason":"INVALID_SCORE_RESULT"});continue
        try:day=parse_date(r["Date"])
        except DataAuditError:
            errors.append({"line":line,"reason":"COMPLETED_ROW_DATE_INVALID"});continue
        if day>=source_now.date():
            errors.append({"line":line,"reason":"SCORED_ROW_AT_OR_AFTER_FETCH_DATE","date":day.isoformat()})
            continue
        if day<date(2026,7,1):
            errors.append({"line":line,"reason":"SOURCE_OUTSIDE_CURRENT_SEASON","date":day.isoformat()})
            continue
        hid=_candidate_id(index,home,league,members,{})
        aid=_candidate_id(index,away,league,members,{})
        if not hid:unresolved[home]+=1
        if not aid:unresolved[away]+=1
        if not hid or not aid:
            counts["unmapped_completed"]+=1;continue
        if hid==aid:
            errors.append({"line":line,"reason":"SAME_CANONICAL_TEAM"});continue
        pair=(hid,aid)
        if pair in unique:
            errors.append({"line":line,"reason":"DUPLICATE_DIRECTED_SEASON_PAIR"});continue
        unique.add(pair)
        completed.append({"date":day,"home_id":hid,"away_id":aid,"home_goals":h,
                          "away_goals":a,"line":line})
        counts["matched_completed"]+=1
    completed.sort(key=lambda r:(r["date"],r["line"]))
    return completed,{
        "provider_rows":len(all_rows),
        "matched_completed":len(completed),
        "unplayed_source_rows":counts["unplayed"],
        "empty_source_rows":counts["blank"],
        "unmapped_completed_source_rows":counts["unmapped_completed"],
        "unmapped_source_names":dict(sorted(unresolved.items())),
        "invalid_result_or_duplicate_rows":errors[:50],
        "invalid_result_or_duplicate_count":len(errors),
        "last_scored_date_from_matched_rows":max((r["date"].isoformat() for r in completed),default=None),
        "identity_reconciliation":"EXACT_EXISTING_SOURCE_ALIAS_AND_CURRENT_LEAGUE_MEMBERSHIP_ONLY",
        "source_fully_usable":not errors and not unresolved and len(completed)>=MIN_LEAGUE_GAMES
    }

def side_of(r,team):
    if r["home_id"]==team:
        return {"venue":"home","for":r["home_goals"],"against":r["away_goals"],
                "opponent":r["away_id"]}
    if r["away_id"]==team:
        return {"venue":"away","for":r["away_goals"],"against":r["home_goals"],
                "opponent":r["home_id"]}
    raise DataAuditError("TEAM_NOT_IN_MATCH")

def points(goals_for,goals_against):
    return 3 if goals_for>goals_against else 1 if goals_for==goals_against else 0

def opponent_earlier_ppg(rows,opponent,before):
    earlier=[r for r in rows if r["date"]<before and opponent in (r["home_id"],r["away_id"])]
    if len(earlier)<3:return None
    return round(sum(points(s["for"],s["against"]) for s in (side_of(r,opponent) for r in earlier))/len(earlier),3)

def team_profile(rows,team,target):
    pre=[r for r in rows if r["date"]<target]
    team_rows=[r for r in pre if team in (r["home_id"],r["away_id"])]
    team_rows.sort(key=lambda r:(r["date"],r["line"]))
    overall=[side_of(r,team) for r in team_rows]
    home=[side_of(r,team) for r in team_rows if r["home_id"]==team]
    away=[side_of(r,team) for r in team_rows if r["away_id"]==team]
    league_n=len(pre)
    if league_n:
        league_home=sum(r["home_goals"] for r in pre)/league_n
        league_away=sum(r["away_goals"] for r in pre)/league_n
    else:
        league_home=league_away=None
    recent=team_rows[-5:]
    last_five=[{"date":r["date"].isoformat(),"venue":side_of(r,team)["venue"],
                "goals_for":side_of(r,team)["for"],
                "goals_against":side_of(r,team)["against"],
                "points":points(side_of(r,team)["for"],side_of(r,team)["against"]),
                "opponent_id":side_of(r,team)["opponent"],
                "opponent_previous_domestic_ppg":opponent_earlier_ppg(
                    rows,side_of(r,team)["opponent"],r["date"])}
               for r in recent]
    ppg=[x["opponent_previous_domestic_ppg"] for x in last_five
         if x["opponent_previous_domestic_ppg"] is not None]
    last_date=max((r["date"] for r in team_rows),default=None)
    return {"team_id":team,"match_cutoff_date_exclusive":target.isoformat(),
            "past_current_season_games":len(team_rows),
            "past_current_season_home_games":len(home),
            "past_current_season_away_games":len(away),
            "all_venues_goals_for":sum(x["for"] for x in overall),
            "all_venues_goals_against":sum(x["against"] for x in overall),
            "all_venues_points":sum(points(x["for"],x["against"]) for x in overall),
            "domestic_home_goals_for":sum(x["for"] for x in home),
            "domestic_home_goals_against":sum(x["against"] for x in home),
            "domestic_away_goals_for":sum(x["for"] for x in away),
            "domestic_away_goals_against":sum(x["against"] for x in away),
            "domestic_league_games_before_match":league_n,
            "domestic_league_home_goals_per_game":round(league_home,4) if league_home is not None else None,
            "domestic_league_away_goals_per_game":round(league_away,4) if league_away is not None else None,
            "last_completed_domestic_match":last_date.isoformat() if last_date else None,
            "days_since_last_domestic_game":(target-last_date).days if last_date else None,
            "recent_5":[*last_five],
            "recent_5_points":sum(x["points"] for x in last_five),
            "recent_5_goals_for":sum(x["goals_for"] for x in last_five),
            "recent_5_goals_against":sum(x["goals_against"] for x in last_five),
            "recent_opponent_strength_method":"Past domestic opponent PPG strictly before THAT past match; descriptive only",
            "recent_opponent_prior_ppg_avg":round(sum(ppg)/len(ppg),3) if ppg else None,
            "recent_opponent_prior_ppg_coverage":len(ppg),
            "no_xg_or_h2h_or_elo_adjustments":True}

def preview(league_data,source_audits,fixtures,active,source_now):
    reports=[]
    for f in fixtures:
        home=f["home_identity"];away=f["away_identity"]
        hid=home["canonical_team_id"];aid=away["canonical_team_id"]
        hl=home["league"];al=away["league"]
        if hid not in active or aid not in active or hl not in DIVS or al not in DIVS:
            raise DataAuditError("FIXTURE_VIOLATES_EUROPE_ELO_SCOPE")
        cutoff=date.fromisoformat(f["date"])
        kickoff=datetime.fromisoformat(f["kickoff_utc"])
        out={"uefa_match_id":f["uefa_match_id"],"competition":f["competition"],
             "date":f["date"],"home":f["home_uefa"],"away":f["away_uefa"],
             "home_id":hid,"away_id":aid,"domestic_home_league":hl,
             "domestic_away_league":al,"kickoff_utc":kickoff.isoformat(),
             "data_collection_utc":source_now.isoformat(),
             "status":"NOT_READY_UNTIL_SOURCE_CHECKED",
             "model_forecast_authorized":False,"pilot_recorded":False}
        if source_now>=kickoff:
            out["status"]="SOURCE_CAPTURE_AT_OR_AFTER_KICKOFF"
        elif hl not in league_data or al not in league_data:
            out["status"]="AT_LEAST_ONE_LEAGUE_SOURCE_MISSING"
        elif not source_audits[hl]["source_fully_usable"] or not source_audits[al]["source_fully_usable"]:
            out["status"]="SOURCE_OR_IDENTITY_PARTIAL_REVIEW_REQUIRED"
        else:
            h=team_profile(league_data[hl],hid,cutoff)
            a=team_profile(league_data[al],aid,cutoff)
            out["domestic_home"]=h;out["domestic_away"]=a
            conditions=(h["past_current_season_games"]>=MIN_TEAM_GAMES and
                        a["past_current_season_games"]>=MIN_TEAM_GAMES and
                        h["past_current_season_home_games"]>=MIN_EACH_VENUE and
                        a["past_current_season_away_games"]>=MIN_EACH_VENUE and
                        h["domestic_league_games_before_match"]>=MIN_LEAGUE_GAMES and
                        a["domestic_league_games_before_match"]>=MIN_LEAGUE_GAMES)
            out["status"]="DESCRIPTIVE_GOAL_PROFILE_SOURCE_READY" if conditions else "DOMESTIC_SAMPLE_INSUFFICIENT"
            out["all_venue_role_count_detail"]={
                "home_team_home_games":h["past_current_season_home_games"],
                "away_team_away_games":a["past_current_season_away_games"]}
        reports.append(out)
    return reports

def run(*,fetcher=get_source,now=None,write=True):
    now=now or datetime.now(timezone.utc)
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise DataAuditError("UTC_AWARE_CAPTURE_REQUIRED")
    now=now.astimezone(timezone.utc)
    idx=json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    _validate_identity_source(idx);validated_index(idx)
    cohort=json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    fdata=json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    selected=fdata.get("verified_fixtures",[])
    if len(selected)!=17 or fdata.get("eligible_total")!=17 or len(cohort.get("eligible_team_ids",[]))!=167:
        raise DataAuditError("PREVIOUS_STAGE3_SEALED_COHORT_MISSING")
    if set(DIVS)!=set(cohort["allowed_league_codes"]):
        raise DataAuditError("EXPECTED_NINE_LEAGUES_CHANGED")
    members=_memberships(idx,"2026-2027")
    active=set(cohort["eligible_team_ids"])
    source_rows={};source_audit={};raw_files={}
    for league in sorted(DIVS):
        url=BASE+"/"+DIVS[league]+".csv"
        try:
            raw,fetched,url=fetcher(league,now)
            if fetched.tzinfo is None or fetched>datetime.now(timezone.utc)+timedelta(minutes=1):
                raise DataAuditError("INVALID_FETCH_TIME")
            rows,audit=decode_league(raw,league,idx,members,now)
            audit.update({"status":"SOURCE_FETCHED_AND_PARSED",
                          "source_url":url,"source_sha256":hashlib.sha256(raw).hexdigest(),
                          "source_fetched_at_utc":fetched.isoformat(),
                          "source_page_last_updated_label":"2026-11-02, not per-row publication proof"})
            source_rows[league]=rows
            raw_files[DIVS[league]+".csv"]=raw
            source_audit[league]=audit
        except (ValueError,KeyError,OSError,TimeoutError,UnicodeError) as exc:
            source_audit[league]={"status":"SOURCE_NOT_VERIFIED",
                                  "source_url":url,
                                  "error_type":type(exc).__name__,
                                  "reason":str(exc)[:160],
                                  "source_fully_usable":False}
    outputs=preview(source_rows,source_audit,selected,active,now)
    statuses=Counter(x["status"] for x in outputs)
    report={
        "schema":VERSION,
        "status":"STAGE4_DESCRIPTIVE_DATA_READINESS_AUDITED",
        "analysis_time_utc":now.isoformat(),
        "scope_leagues":sorted(DIVS),
        "fixtures_expected":17,
        "distinct_teams_expected":34,
        "source_fetched_only_once_per_league":True,
        "football_data_site_last_updated_2026_11_02":True,
        "source_publication_of_each_row_independently_verified":False,
        "source_identity_uses_only_exact_reviewed_registry_aliases":True,
        "source_snapshot_before_every_uefa_kickoff_rechecked_per_fixture":True,
        "current_season_only":True,
        "latest_domestic_day_exclusive":now.date().isoformat(),
        "team_model_minimums":{"past_matches":MIN_TEAM_GAMES,
                               "role_games_for_UEFA_home_away":MIN_EACH_VENUE,
                               "league_matches":MIN_LEAGUE_GAMES},
        "data_quality_method":"Per-match league result day strictly before UEFA calendar day; recent opponent prior-to-THAT-match PPG, no model coefficient",
        "data_sources":source_audit,
        "fixture_status_counts":dict(statuses),
        "fixtures":outputs,
        "all_17_sufficient_for_descriptive_profiles":statuses.get("DESCRIPTIVE_GOAL_PROFILE_SOURCE_READY",0)==17,
        "approved_international_strength_or_uefa_poisson_model":False,
        "probabilities_calculated":False,"elo_adjustment_applied":False,
        "main_modified":False,"prediction_saved":False,"pilot_recorded":False,
    }
    if write:
        OUT_DIR.mkdir(parents=True,exist_ok=True)
        for name,raw in raw_files.items():
            p=OUT_DIR/"source_csv"/name
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(raw)
        (OUT_DIR/"stage4_goal_data_readiness.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print("UEFA_STAGE4_ONE_SHOT="+json.dumps({
        "status":report["status"],"counts":report["fixture_status_counts"],
        "source_leagues_received":len(source_rows),
        "fully_valid_leagues":sum(bool(r.get("source_fully_usable")) for r in source_audit.values()),
        "unmapped_provider_source_names":{lg:list(r.get("unmapped_source_names",{})) for lg,r in source_audit.items() if r.get("unmapped_source_names")},
        "predictions":False},ensure_ascii=False,sort_keys=True))
    return report
if __name__=="__main__":run()
