"""UEFA 2.6.3 xG-free M0/M1/M2 NEXT-stage feasibility, read-only.

Read previously locked 132 official match-ID records, 132 goals-only inputs
and the accepted preregistration. NO re-fetch, re-fit, new predictions, odds,
external leagues, H2H or xG. Inspect train-window interleague graph and the
availability of full PRIOR UEFA matches for BOTH teams at every target date.

Most historical UEFA opponents outside the selected ten-league subset were
intentionally never researched. Missing results MUST NOT become fake 0 points
or fabricated opponent ratings. Historical first-publication remains unknown.
"""
from __future__ import annotations
import argparse
import json
import hashlib
from collections import Counter,defaultdict,deque
from datetime import date
from pathlib import Path
from uefa_xg_free_model_comparison_prereg_263 import (
    evaluate_protocol,validate_plan,ProtocolError)

VERSION="263_UEFA_INTERLEAGUE_GRAPH_M2_PREMATCH_FEASIBILITY_V1"
OUT=Path("data/europe_staged_263/2025_26_xg_free_model_graph_preflight")
# UEFA 2025/26 league-stage rounds inferred ONLY from explicitly
# dated previously approved fixture list; never a new fixture search.
ROUNDS={
"UEFA_CL":(
("2025-09-16","2025-09-18"),("2025-09-30","2025-10-01"),
("2025-10-21","2025-10-22"),("2025-11-04","2025-11-05"),
("2025-11-25","2025-11-26"),("2025-12-09","2025-12-10"),
("2026-01-20","2026-01-21"),("2026-01-28","2026-01-28")),
"UEFA_EL":(
("2025-09-24","2025-09-25"),("2025-10-02","2025-10-02"),
("2025-10-23","2025-10-23"),("2025-11-06","2025-11-06"),
("2025-11-27","2025-11-27"),("2025-12-11","2025-12-11"),
("2026-01-22","2026-01-22"),("2026-01-29","2026-01-29")),
}
class GraphError(ValueError):pass

def round_number(cup,day):
    dates=ROUNDS.get(cup)
    if dates is None:raise GraphError("UNKNOWN_COMPETITION")
    a=[i+1 for i,(lo,hi) in enumerate(dates) if lo<=day<=hi]
    if len(a)!=1:raise GraphError("UNKNOWN_HISTORICAL_UEFA_ROUND_DATE")
    return a[0]

def analyze(plan,official,goals,preregistered):
    locked,folds=evaluate_protocol(plan,official,goals)
    if preregistered.get("schema")!="263_UEFA_M0_M1_M2_CHRONO_PROTOCOL_ACCEPTANCE_V1":
        raise GraphError("PREREG_ACCEPTED_STATUS_MISSING")
    if preregistered.get("status")!="PROTOCOL_FROZEN_READ_ONLY_NO_MODEL_FIT":
        raise GraphError("PREREG_MUST_REMAIN_NOT_FITTED")
    if preregistered.get("source_sha256",{}).get("official")!=hashlib.sha256(
        (json.dumps(official,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()).hexdigest():
        # Raw file hash should be checked in CLI, not JSON reserialization;
        # callers of analyze() can supply canonical dicts independently.
        pass
    for fold in ("train","validation","holdout"):
        if locked["splits"][fold]!=preregistered.get("splits",{}).get(fold):
            raise GraphError("FROZEN_PREREG_FOLD_COUNTERS_CHANGED")
    goal_idx={r["uefa_official_match_id"]:r for r in goals["matches"]}
    candidates=official["matches"]
    fold_of={r["uefa_official_match_id"]:group for group,items in folds.items() for r in items}
    if len(fold_of)!=132:raise GraphError("FROZEN_FOLD_ID_DUPLICATION")
    # Training fold must not use December or January result rows to fit strength.
    training=[r for r in candidates if fold_of[r["uefa_official_match_id"]]=="train" and
              goal_idx[r["uefa_official_match_id"]]["both_4_plus_domestic_results"] and
              goal_idx[r["uefa_official_match_id"]]["both_have_2_each_home_away"] and
              goal_idx[r["uefa_official_match_id"]]["both_leagues_have_30_plus_past_games"]]
    if len(training)!=locked["splits"]["train"]["eligible_goal_based_both_sides"]:
        raise GraphError("ELIGIBLE_TRAINING_SELECTION_CHANGED")
    edges=Counter();degrees=Counter();neighbors=defaultdict(set);leagues=set()
    for m in training:
        features=goal_idx[m["uefa_official_match_id"]]["team_goals_inputs"]
        home=features["home"]["domestic_league"];away=features["away"]["domestic_league"]
        leagues.update((home,away))
        if home!=away:
            a,b=sorted((home,away));edges[(a,b)]+=1
            degrees[a]+=1;degrees[b]+=1
            neighbors[a].add(b);neighbors[b].add(a)
    components=[];remaining=set(leagues)
    while remaining:
        origin=min(remaining);component={origin};frontier=[origin]
        while frontier:
            current=frontier.pop()
            for next_league in neighbors[current]:
                if next_league not in component:
                    component.add(next_league);frontier.append(next_league)
        remaining-=component
        components.append(sorted(component))
    components.sort(key=lambda l:(-len(l),l))
    # Earlier approved UEFA events only. No outside-ten-league matches here:
    # the true previous-round count may exceed this partial corpus.
    seen_before=defaultdict(list)
    rows=[];by_fold=defaultdict(Counter);incomplete_by_cup=Counter()
    for m in sorted(candidates,key=lambda r:(r["date"],r["competition"],r["uefa_official_match_id"])):
        cup=m["competition"];md=round_number(cup,m["date"])
        mid=m["uefa_official_match_id"];fold=fold_of[mid]
        counts=[]
        for side in ("home","away"):
            tid=m[side+"_id_candidate"]
            previous=[r for r in seen_before[(cup,tid)] if r["date"]<m["date"]]
            counts.append(len(previous))
            if len(previous)>md-1:raise GraphError("PRIOR_UC_MATCH_COUNT_GREATER_THAN_ROUNDS")
        complete=all(n==md-1 for n in counts)
        eligible=bool(goal_idx[mid]["both_4_plus_domestic_results"]
           and goal_idx[mid]["both_have_2_each_home_away"]
           and goal_idx[mid]["both_leagues_have_30_plus_past_games"])
        if eligible:
            by_fold[fold]["eligible_124"]+=1
            if complete:by_fold[fold]["both_teams_full_prior_UEFA_history_in_132"]+=1
            else:
                by_fold[fold]["prior_UEFA_history_missing_in_scope"]+=1
                incomplete_by_cup[cup]+=1
        rows.append({"match_id":mid,"cup":cup,"date":m["date"],"matchday":md,
                     "fold":fold,"historical_domestic_goals_eligible":eligible,
                     "approved_ten_league_only_prior_UEFA_matches_found_each":counts,
                     "full_prior_UEFA_matches_needed_each":md-1,
                     "complete_prior_UEFA_matches_in_scope":complete,
                     "M2_match_level_pregame_context_verified":False,
                     "M0_or_M1_training_approved":False})
        seen_before[(cup,m["home_id_candidate"])].append(m)
        seen_before[(cup,m["away_id_candidate"])].append(m)
    for fold in ("train","validation","holdout"):
        if by_fold[fold]["eligible_124"]!=locked["splits"][fold]["eligible_goal_based_both_sides"]:
            raise GraphError("ELIGIBLE_BY_FOLD_CHANGED")
    # Estimating a partial strength network needs a connected supported graph.
    # Connectivity is necessary, NOT sufficient to identify calibrated
    # international strength or eliminate selection bias.
    graph_is_connected=len(components)==1 and len(leagues)==10
    can_model_M2=sum(x["prior_UEFA_history_missing_in_scope"] for x in by_fold.values())==0
    result={"schema":VERSION,"status":"READ_ONLY_GRAPH_AND_UEFA_PRIOR_HISTORY_FEASIBILITY",
            "locked_train_matches":len(training),
            "train_cross_league_edges_unique":len(edges),
            "train_cross_league_games":sum(edges.values()),
            "train_leagues_seen":sorted(leagues),
            "train_components":components,
            "train_graph_ten_league_connected":graph_is_connected,
            "train_league_degrees":dict(sorted(degrees.items())),
            "train_different_league_neighbor_counts":{x:len(neighbors[x]) for x in sorted(leagues)},
            "train_interleague_pair_games":{a+"__"+b:n for (a,b),n in sorted(edges.items())},
            "M1_graph_connected_is_only_necessary_not_sufficient":True,
            "M1_international_strength_calibrated":False,
            "M2_prior_UEFA_complete_for_all_124":can_model_M2,
            "M2_must_be_excluded_from_three_way_paired_fit_if_incomplete":not can_model_M2,
            "prior_history_incomplete_by_competition":dict(incomplete_by_cup),
            "by_fold":{k:dict(v) for k,v in sorted(by_fold.items())},
            "historical_statistic_publication_time_verified":False,
            "complete_2025_26_UEFA_history_for_each_club_verified":False,
            "no_scope_expansion_to_foreign_clubs":True,
            "xg_used":False,"xg_proxy_built":False,
            "fitted_strength_model":False,"M0_M1_M2_comparison_performed":False,
            "auto_model_promotion":False,"main_modified":False,"pilot_modified":False}
    return result,rows

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",default="experiments/263/evidence/uefa_xg_free_m0_m1_m2_prereg_2026_11_02.json")
    p.add_argument("--official",required=True)
    p.add_argument("--goals",required=True)
    p.add_argument("--prereg",required=True)
    a=p.parse_args()
    paths={k:Path(getattr(a,k)) for k in ("protocol","official","goals","prereg")}
    obj={k:json.loads(v.read_text(encoding="utf8")) for k,v in paths.items()}
    lock=obj["prereg"].get("source_sha256",{})
    if hashlib.sha256(paths["official"].read_bytes()).hexdigest()!=lock.get("official"):
        raise GraphError("PREREG_OFFICIAL_SOURCE_SHA_CHANGED")
    if hashlib.sha256(paths["goals"].read_bytes()).hexdigest()!=lock.get("goal_inputs"):
        raise GraphError("PREREG_GOAL_SOURCE_SHA_CHANGED")
    if hashlib.sha256(paths["protocol"].read_bytes()).hexdigest()!=lock.get("protocol"):
        raise GraphError("PREREG_PROTOCOL_SHA_CHANGED")
    report,rows=analyze(obj["protocol"],obj["official"],obj["goals"],obj["prereg"])
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"graph_and_M2_readiness.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    (OUT/"132_prior_UEFA_visibility_REVIEW_ONLY.json").write_text(
        json.dumps({"status":"REVIEW_ONLY_NO_MODEL","rows":rows},
                  ensure_ascii=False,indent=2)+"\n")
    print("UEFA_GRAPH_M2_PREFLIGHT="+json.dumps(report,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
