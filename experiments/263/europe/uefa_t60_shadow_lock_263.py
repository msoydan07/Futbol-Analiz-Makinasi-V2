"""UEFA 2026-11-03..05 Stage8 preparation: trigger-only T-60 shadow lock.

No data/predictions are recorded by importing or unit-testing this module.
At kickoff-minus-60, one NEW scoped request may trigger exactly one atomic
batch of append-only *experimental shadow* records. Uses the accepted
historical M0/M0+Elo functions unchanged, but re-fetches actual live
nine domestic league CSVs and current beyondELO board once each.

The published XI is kept as context/evidence only until effects are proven.
A URL in a request is a CLAIM, not independently checked by GitHub CI.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
from collections import Counter
from datetime import datetime,timezone,timedelta,date
from pathlib import Path
from urllib.parse import urlsplit

from uefa_nov3_5_domestic_goal_data_263 import (
    DIVS,get_source,decode_league,team_profile,MIN_TEAM_GAMES,
    MIN_EACH_VENUE,MIN_LEAGUE_GAMES)
from uefa_nov3_5_stage6_shadow_math_preflight_263 import (
    compute_volatile,to_retro_profile,upstream_inputs,aware_utc,SOURCES as S6_SHA)
from uefa_elo_m0_paired_retrospective_263 import poisson_logpmf
from mackolik_identity_gate_263 import _validate_identity_source,_memberships
from uefa_ten_league_scope_gate_263 import validated_index
from elo_source_acceptance_263 import fetch as get_elo

REQUEST_SCHEMA="263_UEFA_T60_SHADOW_LOCK_REQUEST_V1"
RECORD_SCHEMA="263_UEFA_T60_TWO_SHADOW_IMMUTABLE_RECORD_V1"
REPORT_SCHEMA="263_UEFA_T60_SIX_SLOT_BATCH_LOCK_REPORT_V1"
SLOTS_SCHEMA="263_UEFA_NOV3_5_17_MATCH_TMINUS60_SLOT_PLAN_V1"
PATH_STAGE3="experiments/263/evidence/uefa_2026_11_03_05_fixture_scope_review.json"
PATH_SLOTS="experiments/263/evidence/uefa_nov3_5_t60_six_slots_263.json"
PATH_INDEX="experiments/263/evidence/identity_index_263.json"
PATH_STAGE4="data/europe_staged_263/t60_inputs/goals/stage4_goal_data_readiness.json"
PATH_STAGE5="data/europe_staged_263/t60_inputs/news/17_match_elo_news_readiness.json"
PATH_RETRO="data/europe_staged_263/t60_inputs/retro/retrospective_elo_vs_m0_report.json"
PATH_SOURCE_CSV="data/europe_staged_263/t60_inputs/goals/source_csv"
ROOT_RECORDS="experiments/263/europe/t60_locked"
ROOT_AUDIT="experiments/263/europe/t60_lock_reports"
REQ_DIR="experiments/263/europe/t60_requests"
ELO_URL="https://public-api.beyondelo.com/v1/datasets/club-ratings.csv"
TMIN_EARLIEST=timedelta(minutes=75)
TMIN_LATEST=timedelta(minutes=15)
MAX_BOARD_AGE=timedelta(days=3)
MAX_FOOTBALL_DATA_LAG=timedelta(days=4)
SOURCE_HOSTS={"uefa.com","www.uefa.com","fotmob.com","www.fotmob.com",
"sofascore.com","www.sofascore.com","livescore.com","www.livescore.com",
"mackolik.com","www.mackolik.com","espn.com","www.espn.com"}
class LockError(ValueError):pass

def json_bytes(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,
                      separators=(",",":"),allow_nan=False).encode("utf8")

def stamp(obj):
    return hashlib.sha256(json_bytes(obj)).hexdigest()

def load(path):
    return json.loads(Path(path).read_text(encoding="utf8"))

def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def checked(path,expected):
    if sha_file(path)!=expected:
        raise LockError("CHANGED_FROZEN_SOURCE_SHA:"+Path(path).name)
    return load(path)

def source_url_ok(url):
    if not isinstance(url,str):return False
    try:
        p=urlsplit(url)
        return p.scheme=="https" and p.hostname in SOURCE_HOSTS and not p.username \
               and not p.password and p.port is None and bool(p.path.strip("/"))
    except ValueError:return False

def validate_slot(request,slots,official,now):
    if not isinstance(request,dict) or set(request)!={
        "schema","slot_key","fixture_review","lineups"
    } or request["schema"]!=REQUEST_SCHEMA:
        raise LockError("T60_REQUEST_SCHEMA_INVALID")
    if (slots.get("schema")!=SLOTS_SCHEMA
        or slots.get("session_count")!=6 or slots.get("fixture_count")!=17
        or len(slots.get("slots",[]))!=6):
        raise LockError("SIX_SLOT_PREPLANNED_SCOPE_MISMATCH")
    by_slot={x["slot_key"]:x for x in slots["slots"]}
    if len(by_slot)!=6 or request["slot_key"] not in by_slot:
        raise LockError("UNPLANNED_OR_DUPLICATE_SLOT")
    slot=by_slot[request["slot_key"]]
    if (official.get("schema")!="UEFA_263_NOV3_5_OFFICIAL_FIXTURE_SCOPE_ACCEPTANCE_REVIEW"
        or official.get("eligible_total")!=17
        or len(official.get("verified_fixtures",[]))!=17):
        raise LockError("UEFA_OFFICIAL_17_SCOPE_CHANGED")
    fixtures={x["uefa_match_id"]:x for x in official["verified_fixtures"]}
    mids=slot["uefa_match_ids"]
    if not mids or len(mids)!=len(set(mids)) or any(mid not in fixtures for mid in mids):
        raise LockError("SLOT_FIXTURE_ID_NOT_IN_OFFICIAL_SCOPE")
    if len({mid for g in slots["slots"] for mid in g["uefa_match_ids"]})!=17:
        raise LockError("SIX_SLOTS_FAIL_EXHAUSTIVE_17")
    kicks={aware_utc(fixtures[mid]["kickoff_utc"]) for mid in mids}
    if len(kicks)!=1:raise LockError("SLOT_KICKOFF_NOT_ONE_UNIQUE_TIME")
    kickoff=next(iter(kicks))
    now=aware_utc(now)
    remaining=kickoff-now
    if not TMIN_LATEST<=remaining<=TMIN_EARLIEST:
        raise LockError("OUTSIDE_TMINUS75_TO_TMINUS15_LOCK_WINDOW")
    if (slot["date"]!=kickoff.astimezone(
        timezone(timedelta(hours=3))).date().isoformat()):
        raise LockError("LOCAL_MATCH_DATE_CHANGED")
    fr=request["fixture_review"]
    if not isinstance(fr,dict) or set(fr)!={"status","reviewed_at_utc","official_urls"}:
        raise LockError("FIXTURE_REVIEW_REQUIRED")
    if fr["status"]!="ASSISTANT_WEB_OFFICIAL_PAGE_REVIEWED":
        raise LockError("CURRENT_OFFICIAL_MATCH_PAGE_REVIEW_MISSING")
    observed=aware_utc(fr["reviewed_at_utc"])
    if not observed<=now or now-observed>timedelta(hours=2):
        raise LockError("UEFA_MATCH_CENTER_REVIEW_STALE_OR_FUTURE")
    expected={str(k):fixtures[k]["official_match_url"] for k in mids}
    if fr["official_urls"]!=expected:
        raise LockError("UEFA_OFFICIAL_URLS_NOT_MATCHED")
    # Review is a recorded statement by the web reviewer, never a GitHub fetch.
    lineup=request["lineups"]
    if not isinstance(lineup,dict) or set(lineup)!={str(mid) for mid in mids}:
        raise LockError("EACH_MATCH_REQUIRES_EXPLICIT_XI_STATE")
    checked_lineups={}
    for mid in mids:
        value=lineup[str(mid)]
        if not isinstance(value,dict) or set(value)!={
            "status","observed_at_utc","source_url",
            "home_starting_xi","away_starting_xi"
        }:
            raise LockError("LINEUP_EVIDENCE_SCHEMA_WRONG")
        state=value["status"]
        if state not in ("NOT_CONFIRMED","TWO_CONFIRMED_XI_SOURCE_CLAIM"):
            raise LockError("LINEUP_STATUS_UNSUPPORTED")
        if state=="NOT_CONFIRMED":
            if any(value.get(k) is not None for k in (
                "observed_at_utc","source_url","home_starting_xi","away_starting_xi")):
                raise LockError("UNCONFIRMED_XI_MUST_NOT_GUESS_PLAYERS")
            checked_lineups[mid]={"status":"FIRST_XI_NOT_CONFIRMED_NON_BLOCKING",
                                  "source_ci_verified":False,
                                  "home_starting_xi":None,"away_starting_xi":None}
            continue
        if not source_url_ok(value["source_url"]):
            raise LockError("XI_SOURCE_HOST_INVALID")
        t=aware_utc(value["observed_at_utc"])
        if t>now or now-t>timedelta(minutes=100):
            raise LockError("XI_OBSERVATION_STALE_OR_FUTURE")
        for field in ("home_starting_xi","away_starting_xi"):
            players=value[field]
            if (not isinstance(players,list) or len(players)!=11 or
                not all(isinstance(p,str) and 1<=len(p.strip())<=120 for p in players) or
                len({p.casefold().strip() for p in players})!=11):
                raise LockError("XI_NAMES_INCOMPLETE_OR_REPEATED")
        checked_lineups[mid]={
            "status":"CONFIRMED_XI_CLAIM_REVIEWED_BY_ASSISTANT_NOT_RUNNER",
            "observed_at_utc":t.isoformat(),
            "source_url":value["source_url"],
            "home_starting_xi":value["home_starting_xi"],
            "away_starting_xi":value["away_starting_xi"],
            "source_ci_verified":False,
            "xi_numeric_effect_on_model":False}
    return slot,kickoff,checked_lineups

def current_source_goals(index,original,now,kickoff,
                         *,fetcher=get_source,source_root=PATH_SOURCE_CSV):
    # All 9 original audited source rows must still exist with same final result;
    # additional genuinely completed earlier-date matches may be appended.
    mem=_memberships(index,"2026-2027")
    collected={};audit={}
    for league in sorted(DIVS):
        division=DIVS[league]
        old_path=Path(source_root)/(division+".csv")
        baseline=old_path.read_bytes()
        if hashlib.sha256(baseline).hexdigest()!=original["data_sources"][league]["source_sha256"]:
            raise LockError("OLD_ACCEPTED_RAW_SOURCE_SHA_DIFFERS:"+league)
        old,old_audit=decode_league(baseline,league,index,mem,now)
        if old_audit["source_fully_usable"] is not True:
            raise LockError("OLD_SOURCE_ALREADY_INVALID:"+league)
        raw,fetched,url=fetcher(league,now)
        if not isinstance(raw,bytes) or not isinstance(fetched,datetime):
            raise LockError("LIVE_SOURCE_RETURNED_BAD_BYTES_OR_CLOCK")
        received=aware_utc(fetched)
        if received>=kickoff:
            raise LockError("LEAGUE_SOURCE_FETCH_COMPLETED_AFTER_KICKOFF")
        if url!=("https://www.football-data.co.uk/mmz4281/2627/"+division+".csv"):
            raise LockError("UNEXPECTED_DOMESTIC_URL")
        fresh,fa=decode_league(raw,league,index,mem,now)
        if not fa["source_fully_usable"]:
            raise LockError("LIVE_SOURCE_INVALID_OR_HAS_UNKNOWN_TEAM:"+league)
        def directed(rows):
            return {(r["home_id"],r["away_id"]):
                    (r["date"].isoformat(),r["home_goals"],r["away_goals"])
                    for r in rows}
        oldpairs=directed(old);newpairs=directed(fresh)
        if not all(newpairs.get(key)==row for key,row in oldpairs.items()):
            raise LockError("EARLIER_ACCEPTED_COMPLETED_RESULT_CHANGED:"+league)
        recent_date=max(x["date"] for x in fresh)
        if (now.date()-recent_date)>MAX_FOOTBALL_DATA_LAG:
            raise LockError("CURRENT_DOMESTIC_LEAGUE_ROWS_TOO_STALE:"+league)
        collected[league]=fresh
        audit[league]={"source_url":url,"sha256":hashlib.sha256(raw).hexdigest(),
            "fetched_utc":received.isoformat(),
            "completed_matches":len(fresh),
            "new_completed_since_first_snapshot":len(fresh)-len(old),
            "last_completed_result":recent_date.isoformat(),
            "source_identity_unverified_independent_federation":True}
    return collected,audit

def current_elo(stage5,now,kickoff,*,elo_fetch=get_elo):
    info,rows=elo_fetch("club-ratings.csv")
    if info.get("status")!="FETCHED_AND_SCHEMA_VALID" or not rows:
        raise LockError("LIVE_CURRENT_ELO_BOARD_NOT_AVAILABLE")
    slugs={r["slug"]:r for r in rows if r.get("slug")}
    if len(slugs)!=len([r for r in rows if r.get("slug")]):
        raise LockError("DUPLICATE_ELO_PROVIDER_SLUG")
    known={}
    for m in stage5["matches"]:
        for side in ("home_team","away_team"):
            old=m[side];slug=old["source_slug"]
            current=slugs.get(slug)
            if (current is None or current["name"]!=old["source_club_name"] or
                current.get("is_ranked","").lower()!="true"):
                raise LockError("CURRENT_ELO_CANONICAL_SOURCE_SLUG_CHANGED:"+slug)
            asof=date.fromisoformat(current["as_of"])
            last=date.fromisoformat(current["last_match_date"])
            if (asof>now.date() or last>=kickoff.date() or
                last>asof or now.date()-asof>MAX_BOARD_AGE or
                not math.isfinite(float(current["elo"])) or
                not math.isfinite(float(current["rd"])) or
                float(current["rd"])<=0):
                raise LockError("LIVE_ELO_DATE_OR_RANGE_UNSAFE:"+slug)
            known[old["canonical_team_id"]]={"elo":float(current["elo"]),
                "rd":float(current["rd"]),
                "source_slug":slug,"source_name":current["name"],
                "board_as_of":current["as_of"],
                "last_rated_match":current["last_match_date"],
                "rating_model_preapproved":False}
    if len(known)!=34:raise LockError("EXPECTED_34_ELO_TEAMS")
    source_observed_utc=datetime.now(timezone.utc)
    if source_observed_utc>=kickoff:
        raise LockError("CURRENT_ELO_OBSERVED_AFTER_KICKOFF")
    return known,{"source_url":ELO_URL,"source_sha256":info["sha256"],
                "observed_utc":source_observed_utc.isoformat(),
                "last_modified_claim":info.get("last_modified"),
                "board_ratings_not_certified_as_UEFA_club_ids":True}

def score_mode(lh,la):
    # Most likely exact football score is a descriptive model output, no pick.
    return max(((h,a) for h in range(11) for a in range(11)),
               key=lambda z:poisson_logpmf(z[0],lh)+poisson_logpmf(z[1],la))

def model_output(t):
    lh,la,probs,over,btts=t
    winner="HOME" if probs[0]>max(probs[1:]) else (
        "DRAW" if probs[1]>max(probs[0],probs[2]) else "AWAY")
    h,a=score_mode(lh,la)
    if not all(math.isfinite(x) for x in (lh,la,*probs,over,btts)):
        raise LockError("NONFINITE_MODEL_OUTPUT")
    if (not math.isclose(sum(probs),1,abs_tol=1e-12) or
        not all(0<=p<=1 for p in (*probs,over,btts))):
        raise LockError("MODEL_PROBABILITIES_INVALID")
    return {"expected_home_goals":lh,"expected_away_goals":la,
        "1x2":{"home":probs[0],"draw":probs[1],"away":probs[2]},
        "over_2p5":over,"under_2p5":1-over,
        "both_teams_score_yes":btts,"both_teams_score_no":1-btts,
        "most_likely_exact_score":{"home":h,"away":a},
        "max_1x2_probability_label":winner,
        "market_ev":None,"betting_pick_authorized":False}

def batch(request,*,now,fixture,slots,stage4,stage5,retro,index,
          source_root=PATH_SOURCE_CSV,fetcher=get_source,elo_fetch=get_elo,
          request_sha=None,trigger_sha=None,run_id=None,
          dest_records=ROOT_RECORDS,dest_reports=ROOT_AUDIT,write=True):
    now=aware_utc(now)
    s,kickoff,xi=validate_slot(request,slots,fixture,now)
    # Reuse stage6 contract as evidence only. Its original whole-17
    # clock guard must NOT be repeated after earlier matches have started.
    proto=upstream_inputs(stage4,stage5,retro,fixture)
    if (stage4["analysis_time_utc"] and
        aware_utc(stage4["analysis_time_utc"])>=kickoff):
        raise LockError("OLD_STAGE4_CAPTURE_AFTER_SELECTED_KICKOFF")
    if aware_utc(stage5["source_evidence"]["beyondelo_audited_utc"])>=kickoff:
        raise LockError("OLD_STAGE5_RATING_AFTER_SELECTED_KICKOFF")
    if (not stage4.get("all_17_sufficient_for_descriptive_profiles") or
        stage5["coverage"]["confirmed_starting_XIs"]!=0):
        raise LockError("UNEXPECTED_PREVIOUS_SOURCE_ACCEPTANCE_STATE")
    _validate_identity_source(index);validated_index(index)
    records_root=Path(dest_records)
    report_root=Path(dest_reports)
    slot_id=s["slot_key"]
    ids=set(s["uefa_match_ids"])
    previous={x["uefa_match_id"]:x for x in stage5["matches"]}
    fixtures={x["uefa_match_id"]:x for x in fixture["verified_fixtures"]}
    old={x["uefa_match_id"]:x for x in stage4["fixtures"]}
    if len(old)!=17 or set(old)!=set(previous) or set(old)!=set(fixtures):
        raise LockError("PREPARED_17_MEMBER_TABLE_MISMATCH")
    # Reject any previously saved prediction across all slots, not just
    # this batch. No replacement of any old file, even by identical data.
    for mid in ids:
        if list(records_root.rglob(str(mid)+".json")):
            raise LockError("IMMUTABLE_MATCH_RECORD_ALREADY_EXISTS:"+str(mid))
    report_path=report_root/(slot_id+".json")
    if report_path.exists():raise LockError("IMMUTABLE_SLOT_REPORT_ALREADY_EXISTS")

    league_rows,sources=current_source_goals(index,stage4,now,kickoff,
                         fetcher=fetcher,source_root=source_root)
    elo,elo_meta=current_elo(stage5,now,kickoff,elo_fetch=elo_fetch)
    if datetime.now(timezone.utc)>=kickoff:
        raise LockError("MATCH_HAS_BEGUN_BEFORE_RECORD_CREATION")

    results=[]
    for mid in s["uefa_match_ids"]:
        fx=fixtures[mid];baseline=old[mid];base_elo=previous[mid]
        if (baseline["home_id"]!=fx["home_identity"]["canonical_team_id"] or
            baseline["away_id"]!=fx["away_identity"]["canonical_team_id"] or
            fx["kickoff_utc"]!=baseline["kickoff_utc"]):
            raise LockError("ACCEPTED_FIXTURE_CHANGED")
        pair={"home":{},"away":{}}
        role_features={}
        for side in ("home","away"):
            team_id=baseline[side+"_id"]
            league=baseline["domestic_"+side+"_league"]
            current=team_profile(league_rows[league],team_id,date.fromisoformat(fx["date"]))
            if (current["past_current_season_games"]<MIN_TEAM_GAMES or
                current["past_current_season_home_games"]<MIN_EACH_VENUE or
                current["past_current_season_away_games"]<MIN_EACH_VENUE or
                current["domestic_league_games_before_match"]<MIN_LEAGUE_GAMES):
                raise LockError("CURRENT_TEAM_PREMATCH_SAMPLE_INSUFFICIENT")
            data=to_retro_profile(current,side,league,fx["date"])
            pair[side]={"profile":data,"elo":elo[team_id]["elo"]}
            role_features[side]={"canonical_team_id":team_id,"league":league,
               "current_season_games_before_UEFA_match":current["past_current_season_games"],
               "last_domestic_result":current["last_completed_domestic_match"],
               "home_games":current["past_current_season_home_games"],
               "away_games":current["past_current_season_away_games"],
               "last_five_points":current["recent_5_points"],
               "recent_opponent_ppg":current["recent_opponent_prior_ppg_avg"],
               "rd":elo[team_id]["rd"],
               "source_elo_as_of":elo[team_id]["board_as_of"],
               "elo_last_rated_match":elo[team_id]["last_rated_match"]}
        ephemeral=compute_volatile(pair,proto["UEFA_train_home_goal_mean"],
                  proto["UEFA_train_away_goal_mean"],proto["beta_retrospective_fitted"])
        model0=model_output(ephemeral["M0"])
        model1=model_output(ephemeral["M0Elo"])
        rec={"schema":RECORD_SCHEMA,"status":"PREKICKOFF_EXPERIMENTAL_SHADOW_LOCK_NOT_PILOT",
             "uefa_match_id":mid,"competition":fx["competition"],
             "season":"2026-2027","official_match_url":fx["official_match_url"],
             "home":fx["home_uefa"],"away":fx["away_uefa"],
             "home_id":baseline["home_id"],"away_id":baseline["away_id"],
             "kickoff_utc":fx["kickoff_utc"],
             "lock_created_at_utc":now.isoformat(),
             "minutes_before_kickoff":round((kickoff-now).total_seconds()/60,2),
             "source_data":{"domestic":sources,"elo":elo_meta,
                 "stage4_accepted_sha256":S6_SHA["stage4"],
                 "stage5_accepted_sha256":S6_SHA["stage5"],
                 "historic_m0_experiment_sha256":S6_SHA["retro"],
                 "source_review_status":"WEB_REVIEW_CLAIM_NOT_REFETCHED_BY_GITHUB_CI",
                 "fixture_review_utc":request["fixture_review"]["reviewed_at_utc"],
                 "fixture_review_url":request["fixture_review"]["official_urls"][str(mid)]},
             "pre_match_context":role_features,
             "first_elevens":xi[mid],
             "models":{"M0_UNAPPROVED_REFERENCE":model0,
                       "M0_ELO_EXPERIMENTAL_SHADOW":model1},
             "hypothesis":"First prospective independent comparison of M0 and unapproved M0+Elo",
             "model_parameters_predeclared":{
                 "UEFA_train_home_goal_mean":proto["UEFA_train_home_goal_mean"],
                 "UEFA_train_away_goal_mean":proto["UEFA_train_away_goal_mean"],
                 "smoothing_k":proto["k_smoothing"],
                 "exploratory_Elo_beta":proto["beta_retrospective_fitted"],
                 "Elo_normalization":proto["Elo_normalization"]},
             "safety":{"mathematical_probability_not_betting_advice":True,
                "lineups_recorded_as_context_only_not_goal_multiplier":True,
                "source_claim_not_actual_independent_UEFA_GitHub_fetch":True,
                "Elo_weight_not_approved":True,
                "pilot_increment":0,
                "odds_EV_not_calculated":True,
                "main_branch_not_modified":True,
                "no_post_match_results_accessed":True},
             "trigger":{"request_sha256":request_sha,
                  "github_trigger_commit_sha":trigger_sha,
                  "github_actions_run_id":run_id}}
        rec["payload_sha256"]=stamp(rec)
        results.append(rec)
    if len(results)!=len(ids):
        raise LockError("BATCH_INCOMPLETE_OR_AFTER_KICKOFF")
    # Persist the ACTUAL time the batch finished computing, never the
    # earlier Python-entry timestamp that preceded network source fetches.
    # Dry rehearsals remain deterministic and never create real records.
    created_utc=datetime.now(timezone.utc) if write else now
    if created_utc>=kickoff:
        raise LockError("LOCK_READY_TOO_LATE_TO_PUBLISH")
    for record in results:
        record["lock_created_at_utc"]=created_utc.isoformat()
        record["minutes_before_kickoff"]=round((kickoff-created_utc).total_seconds()/60,2)
        record["payload_sha256"]=stamp({k:v for k,v in record.items() if k!="payload_sha256"})
    report={"schema":REPORT_SCHEMA,"status":"PREMATCH_SHADOW_LOCK_BATCH_READY",
       "slot_key":slot_id,"lock_created_at_utc":created_utc.isoformat(),
       "kickoff_utc":kickoff.isoformat(),
       "utc_pre_kickoff":True,"matches":len(results),
       "immutable_records":[{"uefa_match_id":r["uefa_match_id"],
                  "relative_path":str(records_root/slot_id/(str(r["uefa_match_id"])+".json")),
                  "payload_sha256":r["payload_sha256"]} for r in results],
       "source_digest_goal_csvs":{lg:v["sha256"] for lg,v in sources.items()},
       "source_digest_elo":elo_meta["source_sha256"],
       "official_XI_not_a_model_multiplier":True,
       "registration_is_experimental_shadow_not_100_pilot":True,
       "no_main_model_or_parameters_changed":True}
    report["payload_sha256"]=stamp(report)
    if write:
        folder=records_root/slot_id
        folder.mkdir(parents=True,exist_ok=False)
        for record in results:
            filename=folder/(str(record["uefa_match_id"])+".json")
            with filename.open("x",encoding="utf8") as handle:
                json.dump(record,handle,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
                handle.write("\n")
        report_root.mkdir(parents=True,exist_ok=True)
        with report_path.open("x",encoding="utf8") as handle:
            json.dump(report,handle,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
            handle.write("\n")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--request",required=True)
    args=p.parse_args()
    now=datetime.now(timezone.utc)
    request_path=Path(args.request)
    if not re.fullmatch(
        r"experiments/263/europe/t60_requests/\d{4}-\d{2}-\d{2}_\d{4}_TR\.json",
        request_path.as_posix()):
        raise LockError("UNEXPECTED_T60_REQUEST_FILENAME_OR_PATH")
    request=load(request_path)
    if request_path.stem!=request.get("slot_key"):
        raise LockError("REQUEST_FILENAME_NOT_MATCHED_TO_SLOT")
    report=batch(request,now=now,
        fixture=load(PATH_STAGE3),slots=load(PATH_SLOTS),
        stage4=checked(PATH_STAGE4,S6_SHA["stage4"]),
        stage5=checked(PATH_STAGE5,S6_SHA["stage5"]),
        retro=checked(PATH_RETRO,S6_SHA["retro"]),
        index=load(PATH_INDEX),request_sha=sha_file(request_path),
        trigger_sha=os.getenv("GITHUB_SHA"),run_id=os.getenv("GITHUB_RUN_ID"))
    print("T60_SHADOW_LOCK_PREPARED="+json.dumps({
        "slot":report["slot_key"],"count":report["matches"],
        "file_paths":[x["relative_path"] for x in report["immutable_records"]],
        "shadow_only":True,"pilot":False},ensure_ascii=False))
if __name__=="__main__":
    main()
