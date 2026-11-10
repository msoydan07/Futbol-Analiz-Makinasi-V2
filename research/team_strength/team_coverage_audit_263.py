"""Read-only team-strength history coverage audit for the frozen M4 research engine.

No coefficients, ratings, sealed forecasts, historical source rows, betting picks
or pilot results are changed. Threshold flags are diagnostic heuristics ONLY.
The existing frozen M4 is allowed to silently center unseen teams at league
baseline; this audit exposes that, without falsely labeling the baseline as
a reliable team-specific estimate.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments/263"))
from exp_263_batch import clean_rows
from full_match_eligibility_263 import full_match_rows

HISTORY=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"
BASE=ROOT/"data/quad_accepted_263/extended_history.csv"
M4=ROOT/"experiments/263/m4_integrated.py"
EXPECTED={
    "source_4617":"637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89",
    "base_4518":"1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9",
    "m4_frozen":"eac755e54086738f40d7f30a514b2c9bb789b2c428ffef4ee70bb2fd2b49bc45",
}
LEAGUES=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
CURRENT="2026-2027"
HALF_LIFE_DAYS=360
# Research diagnostic heuristic, NOT a validated threshold for win rate.
MIN_CURRENT_ROLE=4
MIN_CURRENT_ALL=6
MIN_HISTORICAL_ROLE=8
STALE_DAYS=60

class AuditBlocked(ValueError):pass
def require(x,msg):
    if not x:raise AuditBlocked(msg)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def effective_n(days):
    """Kish effective n under the SAME 360-day decay as locked M4.

    This is descriptive sample diversity, not parameter precision, team
    ranking, or proof of M4 success.
    """
    if not days:return 0.0
    w=[math.exp(-math.log(2)*d/HALF_LIFE_DAYS) for d in days]
    return sum(w)**2/sum(v*v for v in w)

def team_profile(past,league,team,role,cutoff):
    require(league in LEAGUES,"UNKNOWN_LEAGUE")
    require(role in ("home","away"),"UNKNOWN_ROLE")
    require(isinstance(team,str) and len(team.strip())>0,"INVALID_TEAM_ID")
    cutoff_date=date.fromisoformat(cutoff)
    require(all(x["league"]==league and x["match_date"]<cutoff for x in past),
            "HISTORY_NOT_SCOPED_TO_LEAGUE_AND_PREMATCH_DATE")
    chosen=[x for x in past if x[role+"_id"]==team]
    appearances=[x for x in past if team in (x["home_id"],x["away_id"])]
    current_role=[x for x in chosen if x["season"]==CURRENT]
    current_any=[x for x in appearances if x["season"]==CURRENT]
    ages=[(cutoff_date-date.fromisoformat(x["match_date"])).days for x in chosen]
    last=max((x["match_date"] for x in appearances),default=None)
    staleness=(cutoff_date-date.fromisoformat(last)).days if last else None
    recent_any=sum((cutoff_date-date.fromisoformat(x["match_date"])).days<=60
                   for x in appearances)
    flags=[]
    if not appearances:
        flags.append("UNSEEN_TEAM_M4_LEAGUE_BASELINE_FALLBACK")
    else:
        if not current_any:flags.append("NO_CURRENT_SEASON_MATCH")
        if len(current_any)<MIN_CURRENT_ALL:flags.append("CURRENT_SEASON_TOTAL_LT6")
        if len(current_role)<MIN_CURRENT_ROLE:flags.append("CURRENT_SEASON_ROLE_LT4")
        if len(chosen)<MIN_HISTORICAL_ROLE:flags.append("HISTORICAL_ROLE_LT8")
        if staleness>STALE_DAYS:flags.append("LAST_MATCH_MORE_THAN_60_DAYS_OLD")
    # Red flag requires an explicit coverage note, NEVER a probability boost.
    severity=("UNSEEN" if not appearances else
              "THIN_OR_STALE" if flags else "NO_HEURISTIC_FLAG")
    return {
      "league":league,"team_internal_id":team,"role":role,"asof_exclusive":cutoff,
      "historical_all_matches":len(appearances),
      "historical_role_matches":len(chosen),
      "current_season_all_matches":len(current_any),
      "current_season_role_matches":len(current_role),
      "last_match_date":last,"days_since_last_match":staleness,
      "any_venue_matches_last_60d":recent_any,
      "historical_role_effective_n":round(effective_n(ages),3),
      "different_opponents_in_role":len({x["away_id" if role=="home" else "home_id"] for x in chosen}),
      "flags":flags,"coverage_grade":severity,
      "high_confidence_certified":False,
      "actual_predictive_accuracy_inferred":False
    }

def load_verified_prematch(cutoff,root=ROOT):
    date.fromisoformat(cutoff)
    require(cutoff>="2026-11-11","RESEARCH_DATE_NOT_SUPPORTED")
    root=Path(root)
    paths=(root/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv",
           root/"data/quad_accepted_263/extended_history.csv",
           root/"experiments/263/m4_integrated.py")
    for p,k in zip(paths,("source_4617","base_4518","m4_frozen")):
        require(p.is_file() and sha(p)==EXPECTED[k],"FROZEN_INPUT_SHA_CHANGED_"+k)
    old=clean_rows(paths[1]);new=clean_rows(paths[0])
    require(len(old)==4518 and len(new)==4617,"FROZEN_HISTORY_ROW_COUNT_CHANGED")
    a={r["fixture_id"]:r for r in old}
    b={r["fixture_id"]:r for r in new}
    require(len(b)==4617 and all(b.get(k)==v for k,v in a.items()),
            "OLD_4518_MODIFIED_OR_MISSING")
    require(len(set(b)-set(a))==99,"NEW_99_RESULTS_COUNT_CHANGED")
    require(all(r["match_date"]<cutoff for r in new),
            "NO_FUTURE_OR_SAME_DAY_RESULTS_ALLOWED")
    eligible,excluded,sha_policy=full_match_rows(new)
    require(len(eligible)==4616 and len(excluded)==1,
            "NORMAL_90MINUTE_MATCH_POLICY_CHANGED")
    return eligible,excluded,sha_policy

def matchup_check(rows,league,home,away,cutoff):
    require(league in LEAGUES,"UNKNOWN_LEAGUE")
    require(home!=away,"IDENTICAL_OPPONENTS")
    past=[r for r in rows if r["league"]==league and r["match_date"]<cutoff]
    require(len(past)>=60,"INSUFFICIENT_LEAGUE_CONTEXT")
    h=team_profile(past,league,home,"home",cutoff)
    a=team_profile(past,league,away,"away",cutoff)
    return {
      "league":league,"home":h,"away":a,
      "has_unseen_team":any(x["coverage_grade"]=="UNSEEN" for x in (h,a)),
      "has_low_or_stale_context":any(x["coverage_grade"]!="NO_HEURISTIC_FLAG" for x in (h,a)),
      "use_original_M4_probabilities_unchanged":True,
      "do_not_report_confidence_from_coverage_heuristic":True,
      "not_a_verified_live_fixture":True,
    }

def audit(cutoff="2026-11-11",root=ROOT):
    rows,excluded,policy_sha=load_verified_prematch(cutoff,root)
    out=[]
    for league in LEAGUES:
        past=[r for r in rows if r["league"]==league and r["match_date"]<cutoff]
        require(len(past)>=60,"MIN_LEAGUE_ROWS_MISSING_"+league)
        active=sorted({team for r in past if r["season"]==CURRENT
                       for team in (r["home_id"],r["away_id"])})
        require(active,"CURRENT_SEASON_NOT_REPRESENTED_"+league)
        home_profiles=[team_profile(past,league,t,"home",cutoff) for t in active]
        away_profiles=[team_profile(past,league,t,"away",cutoff) for t in active]
        byrole={"home":home_profiles,"away":away_profiles}
        coverage={}
        for role,profiles in byrole.items():
            flags=Counter(f for p in profiles for f in p["flags"])
            coverage[role]={
                "active_team_count":len(profiles),
                "historical_role_lt8":flags["HISTORICAL_ROLE_LT8"],
                "current_season_role_lt4":flags["CURRENT_SEASON_ROLE_LT4"],
                "no_current_season_match":flags["NO_CURRENT_SEASON_MATCH"],
                "current_season_total_lt6":flags["CURRENT_SEASON_TOTAL_LT6"],
                "last_match_over60_days":flags["LAST_MATCH_MORE_THAN_60_DAYS_OLD"],
                "not_flagged":sum(not p["flags"] for p in profiles)
            }
        out.append({
            "league":league,"full_90min_history_rows":len(past),
            "latest_known_result":max(x["match_date"] for x in past),
            "active_current_season_teams":len(active),
            "coverage_by_role":coverage,
            # ID-only report: no reverse-inferred club names.
            "teams_with_flags":{role:[p for p in byrole[role] if p["flags"]]
                                for role in ("home","away")},
        })
    return {
      "schema":"263_TEAM_STRENGTH_CURRENT_COVERAGE_READONLY_V1",
      "status":"DIAGNOSTIC_ONLY_NO_M4_CHANGE",
      "asof_exclusive":cutoff,
      "leagues":len(out),
      "history_rows_including_99":4617,
      "eligible_90min_history_rows":len(rows),
      "excluded_awarded_early_finish":len(excluded),
      "historical_source_sha256":EXPECTED["source_4617"],
      "m4_engine_sha256":EXPECTED["m4_frozen"],
      "current_season":CURRENT,
      "research_heuristic_thresholds":{
        "minimum_historical_role":MIN_HISTORICAL_ROLE,
        "minimum_current_season_role":MIN_CURRENT_ROLE,
        "minimum_current_season_total":MIN_CURRENT_ALL,
        "stale_days_more_than":STALE_DAYS,
      },
      "findings":out,
      "model_or_seals_modified":False,
      "prediction_probabilities_edited":False,
      "real_future_match_predicted":False,
      "limitations":[
          "Team IDs are internal verified registry identifiers, not necessarily display names.",
          "Current-season active means represented by at least one finished current-season match, not all future teams.",
          "Flags are engineering research heuristics, not empirical thresholds guaranteeing predictive error.",
          "M4 unseen-team league-average fallback is observed in frozen source; this audit surfaces it without altering math.",
          "No past/old pilots re-simulated or retuned. All history rows strictly precede the target date.",
          "Effective N for team-specific venue samples is descriptive, not posterior precision.",
          "An upcoming match must separately be proven by official live fixture gate before forecasting.",
      ],
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--asof",default="2026-11-11")
    p.add_argument("--out",required=True)
    p.add_argument("--league")
    p.add_argument("--home-id")
    p.add_argument("--away-id")
    opt=p.parse_args()
    if any(x is not None for x in (opt.league,opt.home_id,opt.away_id)):
        require(all(x is not None for x in (opt.league,opt.home_id,opt.away_id)),
                "MATCHUP_REQUIRES_BOTH_TEAM_IDS_AND_LEAGUE")
        rows,_,_=load_verified_prematch(opt.asof)
        report={
            "schema":"263_TEAM_STRENGTH_MATCHUP_READONLY_V1",
            "scope":"UNVERIFIED_MATCHUP_DIAGNOSTIC_ONLY",
            "asof_exclusive":opt.asof,
            **matchup_check(rows,opt.league,opt.home_id,opt.away_id,opt.asof)
        }
    else:
        report=audit(opt.asof)
    output=Path(opt.out)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    if "findings" in report:
        print(json.dumps({
          "leagues":report["leagues"],
          "eligible":report["eligible_90min_history_rows"],
          "coverage":{x["league"]:{
              role:x["coverage_by_role"][role] for role in ("home","away")}
              for x in report["findings"]},
          "model_changed":False
        },ensure_ascii=False))
    else:
        print(json.dumps({"league":report["league"],"unseen":report["has_unseen_team"],
                          "flagged":report["has_low_or_stale_context"]}))
if __name__=="__main__":
    main()
