"""2025/26 UEFA xG-free historic domestic goal inputs / archival provenance.

ONE NEW diagnostic: read only the locked 4413 domestic-history snapshot and
the 132 previously accepted official UEFA match-ID link review overlay.
Compute SAME-SEASON strictly-previous-calendar-date domestic goals, with each
team's prior home/away counts and same-league scoring baselines.

No xG or xG substitutes. No model coefficients, lambdas, forecasting, H2H,
later opponent ratings, league-to-league equality assumption, betting,
pilot, roster, new club registry, or existing experiment replay.

A 2026-compiled archive cannot establish that its CSV bytes/stats were
published or retrievable at every historical 2025/26 kickoff.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
from uefa_ten_league_scope_gate_263 import validated_index

VERSION="263_UEFA_GOL_ONLY_ASOF_FEATURE_READINESS_V1"
HISTORY_SHA="35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1"
UEFA_SCHEMA="263_UEFA_2025_26_CL_EL_132_OFFICIAL_MATCH_ID_SOURCE_REVIEW_V1"
SEASON="2025-2026"
COUNTS={"UEFA_CL":95,"UEFA_EL":37}
REQUIRED={"fixture_id","league","season","match_date","home_id","away_id",
          "home_goals","away_goals","result"}
EXPLICIT_TIMESTAMPS=(
    "published_at_utc","source_published_at_utc","source_first_seen_at_utc",
    "source_fetched_at_utc","source_checked_at_utc","retrieved_at_utc",
    "original_archived_at_utc","ingested_at_utc")
OUTPUT=Path("data/europe_staged_263/2025_26_goal_only_temporal_readiness")
class ReadinessError(ValueError):pass

def load_locked_history(path):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=HISTORY_SHA:
        raise ReadinessError("LOCKED_4413_DOMESTIC_ARCHIVE_SHA_MISMATCH")
    reader=csv.DictReader(raw.decode("utf-8-sig").splitlines())
    if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
        raise ReadinessError("HISTORICAL_GOALS_REQUIRED_COLUMNS_MISSING")
    seen=set();rows=[]
    for lineno,r in enumerate(reader,2):
        try:
            d=date.fromisoformat(r["match_date"])
            h=int(r["home_goals"]);a=int(r["away_goals"])
        except (TypeError,ValueError) as e:raise ReadinessError("INVALID_GOALS_OR_DATE_IN_FROZEN_CSV") from e
        if (r["fixture_id"] in seen or not r["fixture_id"] or
            r["home_id"]==r["away_id"] or not r["league"] or not r["season"] or
            not 0<=h<=40 or not 0<=a<=40 or
            r["result"]!=("H" if h>a else "D" if h==a else "A")):
            raise ReadinessError("HISTORICAL_ROW_INTEGRITY_OR_RESULT_INVALID")
        seen.add(r["fixture_id"])
        rows.append({"fixture_id":r["fixture_id"],"league":r["league"],
                     "season":r["season"],"date":d,"home_id":r["home_id"],
                     "away_id":r["away_id"],"home_goals":h,"away_goals":a})
    if len(rows)!=4413:raise ReadinessError("HISTORICAL_ARCHIVE_NOT_4413")
    fields=set(reader.fieldnames)
    present=sorted(fields.intersection(EXPLICIT_TIMESTAMPS))
    # Do NOT elevate a column merely named source_checked_at; provenance
    # of original per-match first publication is independent evidence.
    provenance={"first_publication_timestamps_in_locked_CSV_proven":False,
                "candidate_metadata_columns_present":present,
                "snapshot_as_of_each_uefa_kickoff_archived":False,
                "provider_csv_url_is_not_archival_snapshot_proof":True,
                "archive_sha256":HISTORY_SHA,
                "source_rows":len(rows)}
    return rows,provenance

def load_official_review(path):
    raw=Path(path).read_bytes()
    p=json.loads(raw.decode("utf8"))
    if p.get("schema")!=UEFA_SCHEMA or p.get("status")!="REVIEW_ONLY_NO_MODEL" or p.get("model_training_permitted") is not False:
        raise ReadinessError("UEFA_OFFICIAL_ID_REVIEW_PROVENANCE_WRONG")
    matches=p.get("matches")
    if not isinstance(matches,list) or len(matches)!=132:
        raise ReadinessError("UEFA_REVIEW_132_MATCH_COUNT_CHANGED")
    if Counter(m.get("competition") for m in matches)!=Counter(COUNTS):
        raise ReadinessError("UEFA_REVIEW_CUP_COUNTS_CHANGED")
    seen=set()
    for m in matches:
        k=m.get("uefa_official_match_id")
        if type(k)!=int or k in seen or m.get("model_eligible") is not False:
            raise ReadinessError("UEFA_DUPLICATE_ID_OR_IMPROPER_TRAINING_APPROVAL")
        seen.add(k)
    return matches,hashlib.sha256(raw).hexdigest()

def safe_mean(total,n):
    return round(total/n,6) if n else None

def goals_features(history,uefa,idx):
    """Pure deterministic goal counts, no fitted weights or score prediction."""
    validated_index(idx)
    members={}
    for league,ids in idx["season_memberships"][SEASON].items():
        for team in ids:
            if team in members:raise ReadinessError("CLUB_IN_MULTIPLE_2025_26_LEAGUES")
            members[team]=league
    domestic=defaultdict(list)
    for r in history:
        if r["season"]==SEASON:
            domestic[r["league"]].append(r)
    outputs=[];aggregate=defaultdict(Counter)
    for m in sorted(uefa,key=lambda x:(x["date"],x["competition"],x["uefa_official_match_id"])):
        try:target=date.fromisoformat(m["date"])
        except (TypeError,ValueError) as e:raise ReadinessError("UEFA_DATE_INVALID") from e
        by_side={};league_baseline_cache={}
        for side in ("home","away"):
            id=m[side+"_id_candidate"]
            league=members.get(id)
            if league is None:raise ReadinessError("UEFA_TEAM_OUTSIDE_2025_26_TEN_LEAGUE_SCOPE")
            if league not in league_baseline_cache:
                pre=[r for r in domestic.get(league,[]) if r["date"]<target]
                league_baseline_cache[league]=pre
            pre=league_baseline_cache[league]
            # Role-conditioned domestic scoring baseline. DO NOT apply a
            # league's raw scoring average as an equal-strength scale across countries.
            home_g=sum(r["home_goals"] for r in pre)
            away_g=sum(r["away_goals"] for r in pre)
            own=[r for r in pre if id in (r["home_id"],r["away_id"])]
            own_home=[r for r in own if r["home_id"]==id]
            own_away=[r for r in own if r["away_id"]==id]
            all_for=sum(r["home_goals"] if r["home_id"]==id else r["away_goals"] for r in own)
            all_against=sum(r["away_goals"] if r["home_id"]==id else r["home_goals"] for r in own)
            by_side[side]={
                "canonical_team_id":id,"domestic_league":league,
                "past_domestic_games":len(own),
                "past_domestic_home_games":len(own_home),
                "past_domestic_away_games":len(own_away),
                "past_team_scored_goals":all_for,
                "past_team_conceded_goals":all_against,
                "domestic_home_goals_scored":sum(x["home_goals"] for x in own_home),
                "domestic_home_goals_conceded":sum(x["away_goals"] for x in own_home),
                "domestic_away_goals_scored":sum(x["away_goals"] for x in own_away),
                "domestic_away_goals_conceded":sum(x["home_goals"] for x in own_away),
                "domestic_league_games_before_target":len(pre),
                "domestic_league_home_goals_per_game_before_target":safe_mean(home_g,len(pre)),
                "domestic_league_away_goals_per_game_before_target":safe_mean(away_g,len(pre)),
                "domestic_last_played_before_target":max((x["date"].isoformat() for x in own),default=None),
                "raw_team_goals_for_per_game":safe_mean(all_for,len(own)),
                "raw_team_goals_against_per_game":safe_mean(all_against,len(own)),
                "source_data_retrievable_at_original_kickoff_verified":False}
            if any(x["date"]>=target for x in own+pre):
                raise ReadinessError("LEAKAGE_FUTURE_OR_SAME_DAY_MATCH")
        home=by_side["home"];away=by_side["away"]
        goals4=home["past_domestic_games"]>=4 and away["past_domestic_games"]>=4
        goals8=home["past_domestic_games"]>=8 and away["past_domestic_games"]>=8
        baseline=home["domestic_league_games_before_target"]>=30 and away["domestic_league_games_before_target"]>=30
        roles=all(row["past_domestic_home_games"]>=2 and row["past_domestic_away_games"]>=2 for row in (home,away))
        group=aggregate[m["competition"]]
        group["review_matches"]+=1
        group["both_4_plus_past_goal_games"]+=int(goals4)
        group["both_8_plus_past_goal_games"]+=int(goals8)
        group["both_2_home_and_2_away_domestic_games"]+=int(roles)
        group["both_leagues_30_plus_prior_domestic_games"]+=int(baseline)
        group["both_4_plus_and_league_30_plus"]+=int(goals4 and baseline)
        group["both_4_plus_and_2_each_role_and_league_30_plus"]+=int(goals4 and roles and baseline)
        outputs.append({"uefa_official_match_id":m["uefa_official_match_id"],
                        "competition":m["competition"],"target_date":m["date"],
                        "team_goals_inputs":by_side,
                        "both_4_plus_domestic_results":goals4,
                        "both_8_plus_domestic_results":goals8,
                        "both_have_2_each_home_away":roles,
                        "both_leagues_have_30_plus_past_games":baseline,
                        "goal_only_feature_extraction_complete":True,
                        "global_league_strength_scale_validated":False,
                        "asof_source_publication_time_proven":False,
                        "training_or_pilot_allowed":False})
    if len(outputs)!=132 or Counter(x["competition"] for x in outputs)!=Counter(COUNTS):
        raise ReadinessError("UEFA_COHORT_CHANGED")
    return {"schema":VERSION,
            "status":"GOALS_ONLY_RETROSPECTIVE_FEATURE_READINESS_NOT_VALIDATED_PREGAME",
            "sample_size":len(outputs),
            "by_competition":{k:dict(v) for k,v in sorted(aggregate.items())},
            "all_132_have_strict_pre_date_goal_feature_extracts":True,
            "pre_kickoff_source_publishing_proven":False,
            "historical_snapshot_first_seen_proven":False,
            "model_fitted":False,"probabilities_generated":False,
            "global_league_strength_calibrated":False,
            "xg_searched_or_used":False,"xg_proxy_constructed":False,
            "data_usable_as_retrospective_feature_AUDIT_ONLY":True,
            "candidate_model_training_approved":False,
            "prod_main_modified":False,"pilot_recorded":False},outputs

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--domestic",required=True)
    p.add_argument("--official-132",required=True)
    p.add_argument("--index",default="experiments/263/evidence/identity_index_263.json")
    p.add_argument("--out",default=str(OUTPUT))
    a=p.parse_args()
    domestic,provenance=load_locked_history(a.domestic)
    reviewed,review_sha=load_official_review(a.official_132)
    idx=json.loads(Path(a.index).read_text(encoding="utf8"))
    report,rows=goals_features(domestic,reviewed,idx)
    report["history_provenance"]=provenance
    report["official_132_review_artifact_sha256"]=review_sha
    out=Path(a.out)
    if Path("data/europe_staged_263") not in out.parents:
        raise ReadinessError("OUTPUT_MUST_STAY_QUARANTINED")
    out.mkdir(parents=True,exist_ok=True)
    (out/"xg_free_temporal_goal_feature_coverage.json").write_text(
        json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    (out/"132_goal_only_feature_inputs_REVIEW_ONLY.json").write_text(
        json.dumps({"schema":VERSION,"status":"REVIEW_ONLY_NO_MODEL",
                    "training_permitted":False,"matches":rows},
                   ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("UEFA_GOL_ONLY_ASOF_READINESS="+json.dumps(report,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
