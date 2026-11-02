"""Read-only UEFA xG-free M0/M1/M2 prereg and chronological readiness.

One source-linked *protocol* check. Never fits, scores, publishes,
picks a model or creates a pilot entry. Strictly reads previous accepted
132 official match URL review and previous 132 goal-only input readiness.
Outcomes are not inspected; split by previously published UEFA calendar date.
No internet, no missing xG search, no old regression re-runs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

VERSION="263_UEFA_M0_M1_M2_CHRONO_PROTOCOL_ACCEPTANCE_V1"
SCHEMA="263_UEFA_XG_FREE_M0_M1_M2_CHRONOLOGICAL_PREREG_V1"
OFFICIAL_SCHEMA="263_UEFA_2025_26_CL_EL_132_OFFICIAL_MATCH_ID_SOURCE_REVIEW_V1"
GOAL_SCHEMA="263_UEFA_GOL_ONLY_ASOF_FEATURE_READINESS_V1"
OUT=Path("data/europe_staged_263/2025_26_xg_free_preregistered_experiment")
class ProtocolError(ValueError):pass

def parse_date(value):
    if type(value)!=str:raise ProtocolError("DATE_TYPE_INVALID")
    try:d=date.fromisoformat(value)
    except ValueError as ex:raise ProtocolError("DATE_ISO_INVALID") from ex
    if d.isoformat()!=value:raise ProtocolError("DATE_NONCANONICAL")
    return d

def validate_plan(p):
    if p.get("schema")!=SCHEMA or p.get("status")!="PREREGISTRATION_ONLY_NO_MODEL_FITTING":
        raise ProtocolError("PLAN_SCHEMA_OR_STATUS_INVALID")
    if p.get("experiment_title")!="RETROSPEKTIF_WALK_FORWARD_NO_LIVE_PREGAME_PROOF":
        raise ProtocolError("PLAN_MUST_NOT_CALL_IT_LIVE_PREGAME")
    if p.get("candidate_policy",{}).get("xg_xga_xg_proxies_banned_for_both_sides") is not True:
        raise ProtocolError("XG_POLICY_MUST_BE_BANNED")
    if p.get("candidate_policy",{}).get("h2h_banned") is not True:
        raise ProtocolError("H2H_POLICY_MUST_BE_BANNED")
    if p.get("scope",{}).get("new_untouched_season_test_available") is True:
        raise ProtocolError("UNTOUCHED_TEST_FALSE_CLAIM")
    splits=p.get("split",{})
    if splits.get("method")!="STRICT_CALENDAR_CUTOFF_NO_RANDOM_CV" or splits.get("new_untouched_season_test_available") is not False:
        raise ProtocolError("UNTOUCHED_TEST_OR_SPLIT_CLAIM_WRONG")
    expected=[("train","2025-09-01","2025-12-01",84,60,24),
              ("validation","2025-12-01","2026-01-01",16,12,4),
              ("holdout","2026-01-01","2026-02-01",32,23,9)]
    for name,lo,hi,n,cl,el in expected:
        s=splits.get(name,{})
        if (s.get("start"),s.get("end_exclusive"),s.get("expected_raw"),
            s.get("expected_cl"),s.get("expected_el"))!=(lo,hi,n,cl,el):
            raise ProtocolError("FROZEN_CHRONOLOGICAL_SPLIT_CHANGED")
    if p.get("candidate_policy",{}).get("expected_paired_eligible_total")!=124:
        raise ProtocolError("EXPECTED_124_ELIGIBLE_SCOPE_CHANGED")
    if set(p.get("pre_registered_competing_designs",{}))!={"M0","M1","M2"}:
        raise ProtocolError("ONLY_M0_M1_M2_ALLOWED")
    d=p.get("decision_rules",{})
    if any(d.get(x) is not False for x in ("auto_promote_to_main","allow_calibration_or_live_pilot_from_this_dataset")):
        raise ProtocolError("NO_AUTOMATIC_PROMOTION")
    if p.get("metrics",{}).get("primary")!="paired_mean_1X2_log_loss":
        raise ProtocolError("PRIMARY_METRIC_CHANGED")
    return expected

def evaluate_protocol(plan,official,goals):
    expected=validate_plan(plan)
    if (official.get("schema")!=OFFICIAL_SCHEMA or official.get("status")!="REVIEW_ONLY_NO_MODEL"
        or official.get("model_training_permitted") is not False):
        raise ProtocolError("OFFICIAL_MATCH_IDS_NOT_PREVIOUSLY_REVIEWED")
    if (goals.get("schema")!=GOAL_SCHEMA or goals.get("status")!="REVIEW_ONLY_NO_MODEL"
        or goals.get("training_permitted") is not False):
        raise ProtocolError("GOAL_ONLY_INPUTS_NOT_PREVIOUSLY_REVIEWED")
    om=official.get("matches");gm=goals.get("matches")
    if not isinstance(om,list) or len(om)!=132 or not isinstance(gm,list) or len(gm)!=132:
        raise ProtocolError("REVIEW_INPUTS_NOT_132")
    by_id={}
    for m in gm:
        k=m.get("uefa_official_match_id")
        if type(k)!=int or k in by_id:raise ProtocolError("GOAL_INPUT_ID_DUPLICATE")
        if (m.get("training_or_pilot_allowed") is not False or
            m.get("asof_source_publication_time_proven") is not False or
            m.get("global_league_strength_scale_validated") is not False):
            raise ProtocolError("GOAL_INPUTS_WRONGLY_PROMOTED")
        by_id[k]=m
    seen=set();roster=defaultdict(list);eligible=Counter();dates=defaultdict(set)
    for m in om:
        k=m.get("uefa_official_match_id")
        if type(k)!=int or k in seen:raise ProtocolError("OFFICIAL_ID_DUPLICATED")
        seen.add(k)
        prev=by_id.get(k)
        if prev is None:raise ProtocolError("UNPAIRED_UEFA_ID_WITH_GOAL_INPUTS")
        if prev.get("target_date")!=m.get("date") or prev.get("competition")!=m.get("competition"):
            raise ProtocolError("MATCH_ID_DATE_COMPETITION_MISMATCH")
        if (prev.get("team_goals_inputs",{}).get("home",{}).get("canonical_team_id")!=m.get("home_id_candidate")
            or prev.get("team_goals_inputs",{}).get("away",{}).get("canonical_team_id")!=m.get("away_id_candidate")):
            raise ProtocolError("TEAM_ID_OR_ORIENTATION_MISMATCH")
        if m.get("model_eligible") is not False:raise ProtocolError("OLD_UEFA_MATCH_WRONGLY_PROMOTED")
        dt=parse_date(m.get("date"))
        fold=next((name for name,lo,hi,*_ in expected if parse_date(lo)<=dt<parse_date(hi)),None)
        if fold is None:raise ProtocolError("MATCH_NOT_IN_FROZEN_DATE_FOLDS")
        cup=m["competition"]
        if cup not in ("UEFA_CL","UEFA_EL"):raise ProtocolError("UNEXPECTED_COMPETITION")
        dates[fold].add(m["date"])
        condition=(prev.get("both_4_plus_domestic_results") is True
            and prev.get("both_have_2_each_home_away") is True
            and prev.get("both_leagues_have_30_plus_past_games") is True)
        if condition:eligible[fold]+=1
        roster[fold].append({"uefa_official_match_id":k,"competition":cup,
                            "date":m["date"],"structurally_eligible":condition,
                            "training_or_pilot_allowed":False})
    if set(by_id)!=seen:raise ProtocolError("UNUSED_GOAL_INPUTS")
    counts={}
    for name,lo,hi,n,cl,el in expected:
        rows=roster[name]
        by_cup=Counter(m["competition"] for m in rows)
        if len(rows)!=n or by_cup!=Counter({"UEFA_CL":cl,"UEFA_EL":el}):
            raise ProtocolError("DATE_SPLIT_OR_SOURCE_COUNTS_CHANGED")
        counts[name]={"source_candidates":n,"uefa_cl":cl,"uefa_el":el,
                      "eligible_goal_based_both_sides":eligible[name],
                      "not_eligible":n-eligible[name],
                      "distinct_play_dates":len(dates[name])}
    if sum(eligible.values())!=124:
        raise ProtocolError("PREVIOUS_GOAL_ONLY_124_COHORT_CHANGED")
    return {"schema":VERSION,"status":"PROTOCOL_FROZEN_READ_ONLY_NO_MODEL_FIT",
        "source_matches":132,"goal_only_structural_eligible_matches":124,
        "splits":counts,"identical_paired_subset_for_all_M0_M1_M2_required":True,
        "xg_or_xg_proxy_requested":False,"h2h_used":False,
        "fresh_new_season_holdout_available":False,
        "historical_prematch_provenance_verified":False,
        "M1_interleague_strength_estimated":False,
        "M2_opponent_adjustment_estimated":False,
        "1X2_or_goal_probabilities_generated":False,
        "descriptive_single_season_comparison_only":True,
        "automated_promotion_forbidden":True,
        "pilot_modified":False,"main_modified":False},roster

def run(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",default="experiments/263/evidence/uefa_xg_free_m0_m1_m2_prereg_2026_11_02.json")
    p.add_argument("--official",required=True)
    p.add_argument("--goal-inputs",required=True)
    p.add_argument("--out",default=str(OUT))
    a=p.parse_args(argv)
    paths={"protocol":Path(a.protocol),"official":Path(a.official),"goal_inputs":Path(a.goal_inputs)}
    data={k:json.loads(v.read_text(encoding="utf8")) for k,v in paths.items()}
    report,rows=evaluate_protocol(data["protocol"],data["official"],data["goal_inputs"])
    report["source_sha256"]={k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in paths.items()}
    folder=Path(a.out)
    if Path("data/europe_staged_263") not in folder.parents:
        raise ProtocolError("OUTPUT_ONLY_EXPERIMENT_QUARANTINE")
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"locked_experiment_preflight.json").write_text(
        json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    (folder/"review_only_chronological_folds.json").write_text(
        json.dumps({"status":"NO_OUTCOME_OR_FIT","folds":rows,"model_training_approved":False},
                   ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("M0_M1_M2_PREREG_PREFLIGHT="+json.dumps(report,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":run()
