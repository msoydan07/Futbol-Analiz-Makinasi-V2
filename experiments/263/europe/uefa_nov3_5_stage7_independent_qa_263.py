"""UEFA 2.6.3 Stage 7: independent 17-match data + mathematics quality gate.

One audit on already archived 2026-11-03 data. Unlike Stage 6, this
re-reads the *raw* 9 domestic source CSV files and independently
reconstructs all 34 profiles and Poisson outputs. It NEVER persists
per-match lambda, probabilities, winners, bets, or immutable ledgers.

The numerical correctness of M0/M0+Elo is distinct from calibrated
forecast performance; the latter remains UNSUPPORTED.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import re
import unicodedata
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
from uefa_nov3_5_stage6_shadow_math_preflight_263 import (
    compute_volatile,make_pair,aware_utc,SOURCES as STAGE6_SOURCES)
from uefa_elo_m0_paired_retrospective_263 import K_SMOOTH
VERSION="263_UEFA_STAGE7_INDEPENDENT_17_MATCH_QUALITY_V1"
STAGE6_REPORT_SHA="dea2fa1cb24d415e8e23dba37dff7c54132258af1150845e4fa5d498541dedf3"
DIVS={"ENG1":"E0","GER1":"D1","ESP1":"SP1","ITA1":"I1","FRA1":"F1",
      "NED1":"N1","POR1":"P1","BEL1":"B1","TUR1":"T1"}
GOAL_FIELDS=("past_current_season_games","past_current_season_home_games",
    "past_current_season_away_games","all_venues_goals_for",
    "all_venues_goals_against","all_venues_points",
    "domestic_home_goals_for","domestic_home_goals_against",
    "domestic_away_goals_for","domestic_away_goals_against",
    "recent_5_points","recent_5_goals_for","recent_5_goals_against")
class QualityError(ValueError):pass

def sha(data):
    return hashlib.sha256(data).hexdigest()
def checked(path,expected):
    raw=Path(path).read_bytes()
    if sha(raw)!=expected:
        raise QualityError("FROZEN_EVIDENCE_SHA_CHANGED:"+Path(path).name)
    return json.loads(raw)
def index_key(name):
    """Independent spelling key, constrained to previously verified index IDs."""
    text=str(name).strip().replace("ı","i").replace("İ","I")
    return "".join(c for c in unicodedata.normalize("NFKD",text.casefold())
                   if c.isascii() and c.isalnum())

def independent_source_rows(source_dir,stage4,index):
    membership=index["season_memberships"]["2026-2027"]
    alias_by_league={}
    for league in DIVS:
        candidates=defaultdict(set)
        eligible=set(membership[league])
        for alias,tid in index["aliases"].items():
            if tid in eligible:
                candidates[index_key(alias)].add(tid)
        alias_by_league[league]=candidates
    all_rows={};audits={}
    for league,division in sorted(DIVS.items()):
        path=Path(source_dir)/(division+".csv")
        raw=path.read_bytes()
        evidence=stage4["data_sources"][league]
        if (sha(raw)!=evidence["source_sha256"]
            or evidence.get("source_fully_usable") is not True
            or evidence.get("status")!="SOURCE_FETCHED_AND_PARSED"):
            raise QualityError("NINE_LEAGUE_SOURCE_SHA_OR_ACCEPTANCE_CHANGED:"+league)
        source_clock=aware_utc(evidence["source_fetched_at_utc"])
        if source_clock>=aware_utc("2026-11-03T17:45:00+00:00"):
            raise QualityError("DOMESTIC_SOURCE_NOT_CAPTURED_PREMATCH")
        data=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        expected_columns={"Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"}
        if not expected_columns.issubset(set(data.fieldnames or [])):
            raise QualityError("DOMESTIC_SOURCE_COLUMNS_MISSING:"+league)
        parsed=[];unplayed=0;empty=0;seen=set()
        for lineno,row in enumerate(data,2):
            h=str(row.get("HomeTeam") or "").strip()
            a=str(row.get("AwayTeam") or "").strip()
            if not h and not a:
                empty+=1;continue
            if not h or not a:raise QualityError("SOURCE_ONE_TEAM_MISSING")
            goals=[str(row.get(k) or "").strip() for k in ("FTHG","FTAG")]
            result=str(row.get("FTR") or "").strip()
            if not any([*goals,result]):
                unplayed+=1;continue
            if not all(re.fullmatch(r"\d+",x) for x in goals) or result not in ("H","D","A"):
                raise QualityError("SOURCE_PARTIAL_OR_INVALID_SCORE")
            hg,ag=(int(x) for x in goals)
            if not(0<=hg<=40 and 0<=ag<=40):
                raise QualityError("SOURCE_GOAL_OUT_OF_RANGE")
            if result!=("H" if hg>ag else "A" if hg<ag else "D"):
                raise QualityError("SOURCE_RESULT_SCORE_CONFLICT")
            d=None
            for fmt in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d"):
                try:d=datetime.strptime(row["Date"],fmt).date();break
                except ValueError:continue
            if d is None or not date(2026,7,1)<=d<date(2026,11,3):
                raise QualityError("DOMESTIC_SCORED_ROW_INVALID_ASOF_DATE")
            ids=[]
            for club in (h,a):
                matching=alias_by_league[league].get(index_key(club),set())
                if len(matching)!=1:raise QualityError("CANONICAL_PROVIDER_ID_NOT_UNIQUE")
                ids.append(next(iter(matching)))
            if ids[0]==ids[1] or tuple(ids) in seen:
                raise QualityError("REPEATED_DIRECTED_PAIR_OR_SAME_CLUB")
            seen.add(tuple(ids))
            parsed.append({"date":d,"h":ids[0],"a":ids[1],"gh":hg,"ga":ag,
                           "line":lineno})
        parsed.sort(key=lambda x:(x["date"],x["line"]))
        if (len(parsed)!=evidence["matched_completed"]
            or unplayed!=evidence["unplayed_source_rows"]
            or empty!=evidence["empty_source_rows"]
            or len(parsed)<30):
            raise QualityError("SOURCE_GOAL_COUNTERS_CHANGED:"+league)
        if max(r["date"] for r in parsed).isoformat()!=evidence["last_scored_date_from_matched_rows"]:
            raise QualityError("SOURCE_LAST_SCORED_DATE_CHANGED:"+league)
        all_rows[league]=parsed
        audits[league]={"completed":len(parsed),
                        "last_match":max(x["date"] for x in parsed).isoformat()}
    if sum(v["completed"] for v in audits.values())!=812:
        raise QualityError("ORIGINAL_NINE_LEAGUES_812_GOALS_CHANGED")
    return all_rows,audits

def side(row,club):
    if row["h"]==club:
        return {"venue":"home","gf":row["gh"],"ga":row["ga"],"opp":row["a"]}
    if row["a"]==club:
        return {"venue":"away","gf":row["ga"],"ga":row["gh"],"opp":row["h"]}
    raise QualityError("CLUB_ABSENT_FROM_RESULT")

def points(gf,ga):
    return 3 if gf>ga else 1 if gf==ga else 0

def check_profile(original,league,team,target,rows):
    day=date.fromisoformat(target)
    before=[x for x in rows if x["date"]<day]
    games=[x for x in before if team in (x["h"],x["a"])]
    games.sort(key=lambda x:(x["date"],x["line"]))
    own=[side(x,team) for x in games]
    home=[x for x in own if x["venue"]=="home"]
    away=[x for x in own if x["venue"]=="away"]
    computed={
      "past_current_season_games":len(own),
      "past_current_season_home_games":len(home),
      "past_current_season_away_games":len(away),
      "all_venues_goals_for":sum(x["gf"] for x in own),
      "all_venues_goals_against":sum(x["ga"] for x in own),
      "all_venues_points":sum(points(x["gf"],x["ga"]) for x in own),
      "domestic_home_goals_for":sum(x["gf"] for x in home),
      "domestic_home_goals_against":sum(x["ga"] for x in home),
      "domestic_away_goals_for":sum(x["gf"] for x in away),
      "domestic_away_goals_against":sum(x["ga"] for x in away),
      "recent_5_points":sum(points(side(x,team)["gf"],side(x,team)["ga"]) for x in games[-5:]),
      "recent_5_goals_for":sum(side(x,team)["gf"] for x in games[-5:]),
      "recent_5_goals_against":sum(side(x,team)["ga"] for x in games[-5:]),
    }
    if any(computed[k]!=original[k] for k in GOAL_FIELDS):
        raise QualityError("INDEPENDENT_TEAM_GOAL_AGGREGATES_DISAGREE:"+league)
    if (original["team_id"]!=team or original["match_cutoff_date_exclusive"]!=target
        or original["domestic_league_games_before_match"]!=len(before)):
        raise QualityError("SOURCE_TARGET_ROLE_OR_LEAGUE_MATCH_COUNT_CHANGED")
    bh=sum(x["gh"] for x in before)/len(before)
    ba=sum(x["ga"] for x in before)/len(before)
    if (abs(round(bh,4)-original["domestic_league_home_goals_per_game"])>1e-10
        or abs(round(ba,4)-original["domestic_league_away_goals_per_game"])>1e-10):
        raise QualityError("INDEPENDENT_DOMESTIC_LEAGUE_GOAL_BASELINE_DISAGREES")
    if (not(len(games)>=4 and len(home)>=2 and len(away)>=2)
        or len(original["recent_5"])!=5):
        raise QualityError("DOMESTIC_ROLE_SAMPLE_INSUFFICIENT")
    matched_ppg=0
    for raw,computed_recent in zip(games[-5:],original["recent_5"]):
        observed=side(raw,team)
        if (computed_recent["date"]!=raw["date"].isoformat()
            or computed_recent["venue"]!=observed["venue"]
            or computed_recent["goals_for"]!=observed["gf"]
            or computed_recent["goals_against"]!=observed["ga"]
            or computed_recent["points"]!=points(observed["gf"],observed["ga"])
            or computed_recent["opponent_id"]!=observed["opp"]):
            raise QualityError("RECENT_FIVE_OPPONENT_OR_DATE_CHANGED")
        older=[x for x in rows if x["date"]<raw["date"] and
               observed["opp"] in (x["h"],x["a"])]
        if len(older)<3:
            expected=None
        else:
            expected=round(sum(points(side(x,observed["opp"])["gf"],
                                      side(x,observed["opp"])["ga"]) for x in older)/len(older),3)
        if expected!=computed_recent["opponent_previous_domestic_ppg"]:
            raise QualityError("PREVIOUS_OPPONENT_PPG_HAS_LOOKAHEAD_OR_BAD_VALUE")
        matched_ppg+=int(expected is not None)
    if matched_ppg!=original["recent_opponent_prior_ppg_coverage"]:
        raise QualityError("OPPONENT_PPG_COVERAGE_CHANGED")
    if original["last_completed_domestic_match"]!=games[-1]["date"].isoformat():
        raise QualityError("LAST_DOMESTIC_TEAM_MATCH_CHANGED")
    return matched_ppg

def independent_model(pair,proto,beta):
    """Separate mathematical derivation; does NOT call retrospective formula."""
    h=pair["home"]["profile"];a=pair["away"]["profile"]
    k=float(proto["k_smoothing"])
    def smooth_ratio(g,n,league_mu):
        if not 0<league_mu<8:raise QualityError("ZERO_OR_IMPLAUSIBLE_LEAGUE_BASE")
        return (float(g)/league_mu+k)/(float(n)+k)
    h_attack=smooth_ratio(h["domestic_home_goals_scored"],h["past_domestic_home_games"],
                         h["domestic_league_home_goals_per_game_before_target"])
    a_weak=smooth_ratio(a["domestic_away_goals_conceded"],a["past_domestic_away_games"],
                        a["domestic_league_home_goals_per_game_before_target"])
    a_attack=smooth_ratio(a["domestic_away_goals_scored"],a["past_domestic_away_games"],
                          a["domestic_league_away_goals_per_game_before_target"])
    h_weak=smooth_ratio(h["domestic_home_goals_conceded"],h["past_domestic_home_games"],
                        h["domestic_league_away_goals_per_game_before_target"])
    clip=lambda x:max(0.15,min(5.0,x))
    lh=clip(proto["UEFA_train_home_goal_mean"]*h_attack*a_weak)
    la=clip(proto["UEFA_train_away_goal_mean"]*a_attack*h_weak)
    d=max(-2,min(2,(pair["home"]["elo"]-pair["away"]["elo"])/400))
    if not math.isfinite(d):raise QualityError("RATING_GAP_NAN")
    # No independent additional league coefficient; only optional explicit Elo.
    return clip(lh*math.exp(beta*d)),clip(la*math.exp(-beta*d))

def poisson_independent(lh,la):
    """Independent recurrence + 61-goal score-grid, unlike fixed 26-term scorer."""
    def dist(mu):
        arr=[math.exp(-mu)]
        for j in range(1,61):arr.append(arr[-1]*mu/j)
        return arr
    h=dist(lh);a=dist(la)
    p_home=math.fsum(x*math.fsum(a[:i]) for i,x in enumerate(h))
    p_draw=math.fsum(x*y for x,y in zip(h,a))
    p_away=math.fsum(x*math.fsum(h[:i]) for i,x in enumerate(a))
    mass=p_home+p_draw+p_away
    under=math.fsum(h[i]*a[j] for i in range(3) for j in range(3-i))
    btts=math.fsum(h[1:])*math.fsum(a[1:])
    return (p_home/mass,p_draw/mass,p_away/mass),1-under,btts,abs(1-mass)

def audit(stage4,stage5,retro,stage6,scope,index,source_dir,*,now=None):
    if (stage6["status"]!="17_OF_17_VOLATILE_SHADOW_MATH_INVARIANTS_PASSED_NO_FORECAST_RECORD"
        or stage6["matches_tested"]!=17 or stage6["unique_teams_tested"]!=34
        or stage6["any_per_match_lambda_or_probability_saved"] is not False
        or stage6["mathematical_calibration_or_main_approval"] is not False):
        raise QualityError("FROZEN_STAGE6_SUMMARY_INCONSISTENT")
    if (stage4["fixture_status_counts"]!={"DESCRIPTIVE_GOAL_PROFILE_SOURCE_READY":17}
        or stage5["coverage"]["matches"]!=17
        or retro["Elo_weight_approved_for_model"] is not False
        or retro["historical_rating_first_seen_verified"] is not False
        or stage5["coverage"]["news_el_secondary_provisional_team_reports"]!=10
        or stage5["coverage"]["confirmed_starting_XIs"]!=0):
        raise QualityError("PREVIOUS_EXPLORATORY_DATA_STATUS_MUST_REMAIN_UNAPPROVED")
    raw,counts=independent_source_rows(source_dir,stage4,index)
    m4={m["uefa_match_id"]:m for m in stage4["fixtures"]}
    m5={m["uefa_match_id"]:m for m in stage5["matches"]}
    m3={m["uefa_match_id"]:m for m in scope["verified_fixtures"]}
    if not(len(m4)==len(m5)==len(m3)==17 and set(m4)==set(m5)==set(m3)):
        raise QualityError("THREE_SOURCE_MATCH_ID_PAIR_MISMATCH")
    proto=retro["fixed_protocol"];beta=proto["beta_retrospective_fitted"]
    if not (abs(beta-0.5254760017675575)<1e-13 and
           abs(proto["UEFA_train_home_goal_mean"]-135/76)<1e-13 and
           abs(proto["UEFA_train_away_goal_mean"]-101/76)<1e-13):
        raise QualityError("FIXED_HISTORICAL_BETA_OR_BASE_DRIFT")
    now=now or datetime.now(timezone.utc)
    now=aware_utc(now)
    first=min(aware_utc(m["kickoff_utc"]) for m in m4.values())
    dates=Counter();cups=Counter();team_ids=set()
    tolerance=0;massloss=0;opponent_n=0
    clipped=0;role_n=0
    for fid in sorted(m4):
        f=m4[fid];e=m5[fid];official=m3[fid]
        pair=make_pair(f,e,official)
        if abs(e["elo_home_minus_away"]-(e["home_team"]["elo"]-e["away_team"]["elo"]))>1e-12:
            raise QualityError("ELO_GAP_AGGREGATE_INCONSISTENT")
        if f["kickoff_utc"]!=official["kickoff_utc"]:
            raise QualityError("UEFA_FIXTURE_DATE_DRIFT")
        if aware_utc(f["data_collection_utc"])>=pair["kickoff"]:
            raise QualityError("STAGE4_SOURCE_IN_FUTURE_OF_KICKOFF")
        for side in ("home","away"):
            tid=f[side+"_id"];lg=f["domestic_"+side+"_league"]
            if lg not in raw:
                raise QualityError("COVERED_TEAM_LEAGUE_ABSENT")
            team_ids.add(tid)
            opponent_n+=check_profile(f["domestic_"+side],lg,tid,f["date"],raw[lg])
            role_n+=1
        stage6volatile=compute_volatile(pair,proto["UEFA_train_home_goal_mean"],
                                        proto["UEFA_train_away_goal_mean"],beta)
        for name,b in (("M0",0.0),("M0Elo",beta)):
            res=stage6volatile[name]
            calculated_lh,calculated_la=independent_model(pair,proto,b)
            tolerance=max(tolerance,abs(calculated_lh-res[0]),abs(calculated_la-res[1]))
            if abs(calculated_lh-res[0])>3e-12 or abs(calculated_la-res[1])>3e-12:
                raise QualityError("INDEPENDENT_LAMBDA_OR_ELO_EFFECT_DISAGREES")
            pp,over,btts,mass=poisson_independent(calculated_lh,calculated_la)
            tolerance=max(tolerance,*(abs(pp[i]-res[2][i]) for i in range(3)),
                          abs(over-res[3]),abs(btts-res[4]))
            massloss=max(massloss,mass)
            if (max([*(abs(pp[i]-res[2][i]) for i in range(3)),
                     abs(over-res[3]),abs(btts-res[4])])>3e-12 or mass>1e-12):
                raise QualityError("INDEPENDENT_1X2_OVER25_BOTH_SCORE_DIFFER")
            clipped+=int(calculated_lh in (0.15,5.0) or calculated_la in (0.15,5.0))
        del stage6volatile
        dates[f["date"]]+=1;cups[f["competition"]]+=1
    if (len(team_ids)!=34 or opponent_n!=170 or role_n!=34 or
        dates!=Counter({"2026-11-03":6,"2026-11-04":6,"2026-11-05":5}) or
        cups!=Counter({"UEFA_CL":12,"UEFA_EL":5})):
        raise QualityError("17_MATCH_34_TEAM_OR_OPPONENT_170_COVERAGE_CHANGED")
    if clipped:
        raise QualityError("POISSON_GOAL_CLIPPING_CAN_DISTORT_SHADOW_FEASIBILITY")
    first_time_status="BEFORE_FIRST_KICKOFF" if now<first else "AFTER_FIRST_KICKOFF_NO_NEW_PREMATCH_ASSERTION"
    return {
        "schema":VERSION,
        "status":"STAGE7_INDEPENDENT_NUMERICAL_AND_ARCHIVED_DATA_QA_ACCEPTED",
        "assessed_utc":now.isoformat(),
        "cutoff_status":first_time_status,
        "source_evidence":{
            "stage4_sha":STAGE6_SOURCES["stage4"],
            "stage5_sha":STAGE6_SOURCES["stage5"],
            "retro_sha":STAGE6_SOURCES["retro"],
            "stage6_sha":STAGE6_REPORT_SHA,
        },
        "independent_checks":{
            "nine_raw_provider_csvs_reparsed_and_sums_match":True,
            "matched_2026_27_domestic_results":812,
            "nine_leagues":9,
            "fixture_count":17,
            "team_role_profiles_independently_derived":role_n,
            "recent_five_opponent_PPG_rows_independently_derived":opponent_n,
            "poisson_variants_per_match":2,
            "lambda_and_markets_checked_in_memory":True,
            "max_independent_formula_abs_difference":tolerance,
            "max_poisson_61_term_normalization_deficit":massloss,
            "lambda_clipping_occurrences":clipped,
            "home_away_attack_defense_have_both_current_season_sample":True,
            "early_2026_27_local_results_discarded_if_same_or_after_UEFA_day":True,
            "raw_source_cryptographic_sha_verified":True,
        },
        "source_summary_by_league":dict(sorted(counts.items())),
        "remaining_limitations":[
            "Retrospective UEFA training source has no original historical first_seen proof.",
            "Neither M0 nor Elo shadow is independently calibrated on live 2026/27 outcomes.",
            "Elo experimental beta not approved for production.",
            "UEFA/club numeric shared club-ID crosswalk not independently proven.",
            "UEFA Europa League squad reports currently third-party; no official matchday XI verified.",
            "17 prospective football matches are too few to establish general predictive performance.",
            "Shadow predictions have never been saved; no prospective score comparison can yet occur."
        ],
        "decisions":{
            "stage7_data_and_formula_integrity":"PASS",
            "stage7_predictive_accuracy_or_calibration":"NOT_DEMONSTRATED",
            "stage7_live_UEFA_auto_verification":"NOT_DEMONSTRATED",
            "stage8_locked_forecast_and_pilot_authorized":False,
            "stage8_requires_explicit_user_go_ahead":True,
            "never_relabel_in_memory_sanity_test_as_archived_prematch_forecast":True,
            "main_models_modified":False,
            "main_modified":False,
            "elo_beta_promoted_to_production":False,
            "any_per_match_predictions_or_lambda_saved":False,
            "pilot_recorded":False,
        }
    }

def main():
    p=argparse.ArgumentParser()
    for name in ("stage4","stage5","retro","stage6","stage3","identity","source_csv_dir","output"):
        p.add_argument("--"+name.replace("_","-"),required=True)
    x=p.parse_args()
    raw=checked(x.stage4,STAGE6_SOURCES["stage4"])
    news=checked(x.stage5,STAGE6_SOURCES["stage5"])
    retro=checked(x.retro,STAGE6_SOURCES["retro"])
    s6=checked(x.stage6,STAGE6_REPORT_SHA)
    sc=json.loads(Path(x.stage3).read_text(encoding="utf8"))
    index=json.loads(Path(x.identity).read_text(encoding="utf8"))
    report=audit(raw,news,retro,s6,sc,index,x.source_csv_dir)
    out=Path(x.output)
    if "data/europe_staged_263/stage7_qa_only" not in str(out):
        raise QualityError("STAGE7_OUTPUT_OUTSIDE_REVIEW_ONLY_QUARANTINE")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("UEFA_STAGE7_QA="+json.dumps({
        "status":report["status"],
        "quality":report["decisions"]["stage7_data_and_formula_integrity"],
        "source_rows":report["independent_checks"]["matched_2026_27_domestic_results"],
        "match_count":report["independent_checks"]["fixture_count"],
        "opponent_rows":report["independent_checks"]["recent_five_opponent_PPG_rows_independently_derived"],
        "max_diff":report["independent_checks"]["max_independent_formula_abs_difference"],
        "prediction_saved":False,"forecast_accuracy_proven":False},sort_keys=True))

if __name__=="__main__":main()
