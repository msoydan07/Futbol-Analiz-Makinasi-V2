"""17 UEFA fixtures Nov 3–5 2026: stage 5 Elo + squad source-tier acceptance.

Input archives are already published, no new HTTP requests. No coefficient,
1X2 probabilities, Poisson, bettors, immutable prediction or main writes.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter
from datetime import date,datetime,timezone,timedelta
from pathlib import Path

VERSION="263_UEFA_17_FIXTURES_STAGE5_ELO_AND_NEWS_SOURCE_AUDIT_V1"
ELO_SHA="073a461d810396af6ae74216e8d400d5c5d27a654a153014d36dc4a4c7ee8be5"
CL_NEWS="https://www.uefa.com/uefachampionsleague/news/02ab-21f9907f0a27-6a6a67e9775d-1000--champions-league-predicted-line-ups-matchday-4-team-news-/"
EL_NEWS="https://starting11.com/europa-league"
MIN_UTC=datetime.fromisoformat("2026-11-03T00:00:00+00:00")
MAX_RATING_AGE_DAYS=15
class Stage5Error(ValueError):pass

def iso_utc(s):
    t=datetime.fromisoformat(str(s).replace("Z","+00:00"))
    if t.tzinfo is None:raise Stage5Error("TIMESTAMP_IS_NAIVE")
    return t.astimezone(timezone.utc)

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf8"))

def validate_inputs(raw,source,cross,stage4,fixture,news):
    if hashlib.sha256(raw).hexdigest()!=ELO_SHA:
        raise Stage5Error("ELO_SOURCE_SHA_MISMATCH")
    if (cross.get("schema")!="EUROPE_263_167_CLUB_SOURCE_NAME_CROSSWALK_ACCEPTANCE"
        or cross.get("source_sha256")!=ELO_SHA or cross.get("model_weight_approved") is not False
        or cross.get("reconciled_name_candidate_count")!=167
        or len(cross.get("clubs",[]))!=167):
        raise Stage5Error("167_ELO_CROSSWALK_NOT_LOCKED")
    if (source.get("source",{}).get("current",{}).get("sha256")!=ELO_SHA or
        source["source"]["current"].get("rows")!=1472 or
        source["source"]["current"].get("status")!="STAGED"):
        raise Stage5Error("CURRENT_SOURCE_INTEGRITY_REPORT_CHANGED")
    captured=iso_utc(source["audited_utc"])
    if not MIN_UTC<=captured<MIN_UTC+timedelta(days=1):
        raise Stage5Error("ELO_SOURCE_AUDIT_DAY_UNEXPECTED")
    if (stage4.get("schema")!="263_UEFA_NOV3_5_STAGE4_NINE_LEAGUE_PREMATCH_GOALS_V1"
        or stage4.get("fixture_status_counts")!={"DESCRIPTIVE_GOAL_PROFILE_SOURCE_READY":17}
        or stage4.get("fixtures_expected")!=17
        or len(stage4.get("fixtures",[]))!=17
        or stage4.get("approved_international_strength_or_uefa_poisson_model") is not False):
        raise Stage5Error("LOCKED_STAGE4_EVIDENCE_CHANGED")
    if (fixture.get("schema")!="UEFA_263_NOV3_5_OFFICIAL_FIXTURE_SCOPE_ACCEPTANCE_REVIEW"
        or fixture.get("eligible_total")!=17
        or len(fixture.get("verified_fixtures",[]))!=17):
        raise Stage5Error("STAGE3_SCOPE_REVIEW_CHANGED")
    if (news.get("schema")!="263_UEFA_NOV_3_5_STAGE5_CL_OFFICIAL_EL_SECONDARY_NEWS_REVIEW_V1"
        or len(news.get("clubs",{}))!=34
        or news.get("player_eligibility_verified_from_club_uefa_team_sheets") is not False):
        raise Stage5Error("STAGE5_NEWS_SOURCE_REVIEW_NOT_ACCEPTED")
    rd=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    required={"slug","name","country_code","elo","rd","as_of","last_match_date","is_ranked"}
    if not required.issubset(rd.fieldnames or []):
        raise Stage5Error("SOURCE_MISSING_ELO_COLUMNS")
    rows=list(rd)
    if len(rows)!=1472:raise Stage5Error("SOURCE_RATING_ROW_COUNT_CHANGED")
    by_slug={}
    for row in rows:
        slug=(row.get("slug") or "").strip()
        if slug:
            if slug in by_slug:raise Stage5Error("DUPLICATE_PROVIDER_SLUG_IN_CURRENT_BOARD")
            by_slug[slug]=row
    by_id={c["canonical_id"]:c for c in cross["clubs"]}
    if len(by_id)!=167 or len({c["provider_slug"] for c in cross["clubs"]})!=167:
        raise Stage5Error("CROSSWALK_CLUB_ID_OR_SLUG_DUPLICATION")
    original={p["uefa_match_id"]:p for p in fixture["verified_fixtures"]}
    if len(original)!=17:raise Stage5Error("DUPLICATE_UEFA_FIXTURE_ID")
    ratings={}
    final=[];counts=Counter()
    all_ids=set()
    for f in stage4["fixtures"]:
        fid=f["uefa_match_id"]
        official=original.get(fid)
        if not official or f["home_id"]!=official["home_identity"]["canonical_team_id"] or f["away_id"]!=official["away_identity"]["canonical_team_id"]:
            raise Stage5Error("STAGE3_VS_STAGE4_TEAM_ID_MISMATCH")
        if f["kickoff_utc"]!=official["kickoff_utc"] or f["status"]!="DESCRIPTIVE_GOAL_PROFILE_SOURCE_READY":
            raise Stage5Error("STAGE3_VS_STAGE4_FIXTURE_OR_GOAL_SOURCE_DRIFT")
        kickoff=iso_utc(f["kickoff_utc"])
        if captured>=kickoff or iso_utc(stage4["analysis_time_utc"])>=kickoff:
            raise Stage5Error("DATA_SNAPSHOT_NOT_BEFORE_UEFA_KICKOFF")
        home=f["home_id"];away=f["away_id"]
        team_records=[]
        for team_id,side in ((home,"home"),(away,"away")):
            all_ids.add(team_id)
            crossrow=by_id.get(team_id)
            newsrow=news["clubs"].get(team_id)
            if crossrow is None or newsrow is None:
                raise Stage5Error("CLUB_ELO_OR_NEWS_REVIEW_MISSING")
            if (newsrow["official_club_name"]!=crossrow["official_name"] or
                newsrow["fixture_id"]!=fid or
                newsrow["fixture_kickoff_utc"]!=f["kickoff_utc"] or
                newsrow["confirmed_starting_eleven_available"] is not False):
                raise Stage5Error("NEWS_PLAYER_IDENTITY_OR_MATCH_SCOPE_MISMATCH")
            level=newsrow["confidence"]
            expected_level=("UEFA_EDITORIAL_PREMATCH_REPORT_NOT_CONFIRMED_TEAM_SHEET" if f["competition"]=="UEFA_CL"
                            else "SECONDARY_UNCONFIRMED_REPORT_REQUIRES_OFFICIAL_RECHECK")
            expected_source=CL_NEWS if f["competition"]=="UEFA_CL" else EL_NEWS
            if level!=expected_level or newsrow["source_url"]!=expected_source:
                raise Stage5Error("TEAM_NEWS_SOURCE_TIER_INCORRECT")
            counts[level]+=1
            src=by_slug.get(crossrow["provider_slug"])
            if src is None or src["name"]!=crossrow["provider_name"] or src["elo"]!=crossrow["elo_snapshot"]:
                raise Stage5Error("SOURCE_PROVIDER_NAME_SLUG_RATING_CHANGED")
            if src["country_code"] not in ("ENG","GER","ESP","ITA","FRA","NED","POR","BEL","TUR"):
                raise Stage5Error("PROVIDER_COUNTRY_UNEXPECTED")
            if src["rd"]!=crossrow["rd_snapshot"] or src["is_ranked"].strip().lower()!="true":
                raise Stage5Error("RATING_SOURCE_RD_OR_RANKED_CHANGED")
            if src["as_of"]!=captured.date().isoformat():
                raise Stage5Error("FUTURE_OR_STALE_RATING_BOARD")
            last=date.fromisoformat(src["last_match_date"])
            if last>=kickoff.date() or (captured.date()-last).days>MAX_RATING_AGE_DAYS or last>captured.date():
                raise Stage5Error("LAST_RATING_MATCH_NOT_STRICTLY_PRE_UEFA")
            elo=float(src["elo"]);rd_value=float(src["rd"])
            if not math.isfinite(elo) or not 0<elo<4000 or not math.isfinite(rd_value) or not 0<rd_value<1000:
                raise Stage5Error("ELO_RD_OUT_OF_ALLOWED_RANGE")
            num_days=(kickoff.date()-last).days
            if team_id in ratings:
                raise Stage5Error("DUPLICATE_TEAM_IN_17_FIXTURES")
            ratings[team_id]={"canonical_team_id":team_id,
                "official_club_name":crossrow["official_name"],
                "elo":elo,"rd":round(rd_value,3),
                "source_slug":src["slug"],"source_club_name":src["name"],
                "last_match_date":src["last_match_date"],
                "last_rated_match_to_kickoff_calendar_days":num_days,
                "board_as_of":src["as_of"],
                "identity_confidence":"NAME_COUNTRY_EXACT_SOURCE_SLUG_ONLY_NO_SHARED_UEFA_ID",
                "news":{"source_url":newsrow["source_url"],"source_tier":level,
                        "reported_out":newsrow["reported_out"],"reported_doubtful":newsrow["reported_doubtful"],
                        "reported_no_absences":newsrow["reported_no_absences"],
                        "list_completeness":newsrow["list_completeness"],
                        "confirmed_starting_eleven_available":False,
                        "official_club_player_eligibility_verified":False}}
            team_records.append(ratings[team_id])
        final.append({"uefa_match_id":fid,"competition":f["competition"],
            "home":f["home"],"away":f["away"],"date":f["date"],
            "kickoff_utc":f["kickoff_utc"],"home_team":team_records[0],
            "away_team":team_records[1],
            "elo_home_minus_away":team_records[0]["elo"]-team_records[1]["elo"],
            "model_probs_generated":False,
            "official_starting_xi_status":"NOT_YET_PUBLISHED_OR_NOT_CHECKED_NONBLOCKING",
            "squad_injury_readiness":"UEFA_EDITORIAL_PREVIEW" if f["competition"]=="UEFA_CL" else "SECONDARY_PREVIEW_NEEDS_OFFICIAL_RECHECK",
            "model_alpha_or_elo_lambda_authorized":False})
    if len(all_ids)!=34 or set(ratings)!=set(news["clubs"]) or len(final)!=17:
        raise Stage5Error("34_CLUB_OR_17_MATCH_EXHAUSTIVE_CHECK_FAILED")
    if counts!=Counter({"UEFA_EDITORIAL_PREMATCH_REPORT_NOT_CONFIRMED_TEAM_SHEET":24,
                        "SECONDARY_UNCONFIRMED_REPORT_REQUIRES_OFFICIAL_RECHECK":10}):
        raise Stage5Error("SQUAD_SOURCE_TIERS_NOT_24_10")
    if len({m["uefa_match_id"] for m in final})!=17:raise Stage5Error("DUPLICATE_MATCH_IN_RESULTS")
    return {
        "schema":VERSION,
        "status":"17_PAIRS_PREMATCH_ELO_READY_24_CL_UEFA_EDITORIAL_10_EL_SECONDARY_NEWS_STAGED",
        "assessment_source":"PREVIOUSLY_ARCHIVED_SHA256_RATING_AND_GOAL_SOURCES_PLUS_WEB_REVIEWED_TEAM_NEWS",
        "source_evidence":{"beyondelo_snapshot_sha256":ELO_SHA,
            "beyondelo_audited_utc":captured.isoformat(),
            "beyondelo_board_as_of":captured.date().isoformat(),
            "source_integrity":"beyondELO https://beyondelo.com CC BY 4.0",
            "news_champions_league":CL_NEWS,"news_europa_league_secondary":EL_NEWS,
            "all_prior_data_captured_pre_kickoff":True,
            "source_news_has_exclusive_first_seen_utc":False},
        "coverage":{"matches":17,"distinct_teams":34,
            "elo_with_rd_and_before_kickoff":34,
            "news_cl_uefa_editorial_team_reports":24,
            "news_el_secondary_provisional_team_reports":10,
            "official_UEFA_or_club_player_eligibility_confirmations_for_all_clubs":0,
            "confirmed_starting_XIs":0,
            "first_XI_missing_does_not_block":True},
        "safety":{"elo_influence_on_lambda":False,
            "squad_impact_on_lambda":False,
            "model_forecast_authorized":False,
            "main_modified":False,
            "pilot_recorded":False,
            "immutable_prediction_ledger_written":False,
            "retrospective_beta_0p525_not_applied":True,
            "pre_match_source_article_does_not_prove_team_sheet":True,
            "EL_secondary_source_not_verified_as_UEFA_or_club_official":True},
        "matches":final
    }

def main():
    p=argparse.ArgumentParser()
    for a in ("elo_csv","elo_integrity","crosswalk","stage4","fixtures","news","out"):
        p.add_argument("--"+a.replace("_","-"),required=True)
    a=p.parse_args()
    try:
        report=validate_inputs(Path(a.elo_csv).read_bytes(),
           read_json(a.elo_integrity),read_json(a.crosswalk),
           read_json(a.stage4),read_json(a.fixtures),read_json(a.news))
    except Exception as exc:
        report={"schema":VERSION,"status":"STAGE5_SOURCE_OR_INTEGRITY_NOT_ACCEPTED",
            "error_type":type(exc).__name__,"reason":str(exc)[:200],
            "model_forecast_authorized":False,"pilot_recorded":False}
        Path(a.out).parent.mkdir(parents=True,exist_ok=True)
        Path(a.out).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print("STAGE5_BLOCKED="+json.dumps(report,ensure_ascii=False))
        raise
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("STAGE5_17_TEAM_NEWS="+json.dumps({
        "status":report["status"],"coverage":report["coverage"],
        "model":False,"first_xi_nonblocking":True,"no_pilot":True},ensure_ascii=False))
if __name__=="__main__":main()
