"""2.6.3 Europe CL/EL: NO-xG data-research contract (2026-11-02).

Intentional common-denominator design for mixed ten-league UEFA fixtures.
No xG, xGA, npxG, PSxG, xG proxies, third-party expected-goal estimates,
or xG-specific web searches -- EVEN WHEN available for one/both clubs.

Does not prohibit a GOALS-BASED statistical model later calculating its
own Poisson expected scoring rate (lambda); lambda is not an observed xG
metric and is not computed here. A model still requires separate tests.
No data fetching or model fitting in this module. The trusted collector
receives an exact approved request field list; returned facts are audited.
Production/domestic 10-league pipelines are NOT touched.
"""
from __future__ import annotations
import argparse,json,re
from datetime import datetime,timezone
from pathlib import Path
from uefa_user_time_research_263 import requested_europe_research
from uefa_ten_league_scope_gate_263 import INDEX_DEFAULT

POLICY="263_UEFA_NO_XG_BOTH_SIDES_V1"
RESEARCH_FIELDS=(
    "completed_goals_for_against",
    "domestic_home_away_goal_results",
    "opponent_strength_from_result_history",
    "domestic_league_scoring_baseline",
    "recent_goals_and_match_form",
    "shots_and_shots_on_target_if_both_sourced",
    "pre_match_uefa_results_and_points",
    "rest_and_travel_if_verified",
    "squad_absences_if_verified",
    "confirmed_starting_lineups_at_t60_if_published",
    "odds_if_verified",)
# xG is NOT a prerequisite and cannot be introduced as a fill-in
# or prediction-time superiority adjustment for one of the clubs.
BANNED_TOKENS=frozenset(("xg","xga","npxg","psxg","xgot",
                         "expectedgoals","npxga","xpts"))
META_KEYS=frozenset(("source_url","source_name","retrieved_at_utc",
                     "observed_at_utc","verified","status","notes","value",
                     "home","away","competition","match_date",
                     "source_checked_at_utc","record_id","unit"))
class XGPolicyViolation(ValueError):pass

def key_forbidden(name):
    """For all external-fact keys; never inspect model-projected lambda keys."""
    if not isinstance(name,str):return True
    tokens=re.findall("[a-z0-9]+",name.casefold())
    return bool(BANNED_TOKENS.intersection(tokens) or
                any(a=="expected" and b=="goals" for a,b in zip(tokens,tokens[1:])))

def validate_research_facts(facts):
    """Fail closed if a fetched fact tree contains xG or unknown top-level field.

    This tests the *shape* of trusted adapter results; it cannot prove the
    adapter actually contacted its cited source.
    """
    if not isinstance(facts,dict):raise XGPolicyViolation("COLLECTOR_RETURN_NOT_DICT")
    for feature in facts:
        if key_forbidden(feature):raise XGPolicyViolation("XG_RESEARCH_FEATURE_FORBIDDEN")
        if feature not in RESEARCH_FIELDS and feature not in META_KEYS:
            raise XGPolicyViolation("UNREVIEWED_EXTERNAL_FIELD:"+str(feature)[:60])
    def walk(node):
        if isinstance(node,dict):
            for k,v in node.items():
                if key_forbidden(k):
                    raise XGPolicyViolation("XG_FIELD_IN_COLLECTOR_DATA")
                walk(v)
        elif isinstance(node,(list,tuple)):
            for part in node:walk(part)
    walk(facts)
    return facts

def user_requested_europe_without_xg(competition,home,away,local_date,
                                     local_time,*,index,now=None,collector=None):
    """Local 10-league + user-time gate FIRST. No collector on rejected scope.

    Downstream trusted collector may ONLY be asked for RESEARCH_FIELDS.
    Callable signature: collector(base_gate_result, fields=RESEARCH_FIELDS).
    No collector means a policy-bearing research request, not a prediction.
    """
    gate,_=requested_europe_research(competition,home,away,local_date,
                                    local_time,index=index,now=now)
    gate["europe_research_policy"]={
        "version":POLICY,"data_mode":"SAME_GOALS_BASED_FEATURES_BOTH_TEAMS",
        "fields_to_request":list(RESEARCH_FIELDS),
        "xg_and_xga_research_allowed":False,
        "missing_xg_is_data_defect":False,
        "xg_xga_used_as_model_inputs":False,
        "xg_based_fallback_or_proxy_allowed":False,
        "user_supplied_kickoff_not_officially_verified":True,
        "model_fitted_or_approved":False,
        "production_or_pilot_modified":False,
    }
    if not gate["data_research_allowed"]:
        return gate,None
    if collector is None:return gate,None
    if not callable(collector):
        raise XGPolicyViolation("TRUSTED_COLLECTOR_CALLABLE_REQUIRED")
    # Deliberately narrow interface to stop constructing xG field searches.
    facts=collector(gate,fields=RESEARCH_FIELDS)
    return gate,validate_research_facts(facts)

def main(argv=None):
    p=argparse.ArgumentParser(description="CL/EL no xG research request gate")
    p.add_argument("--competition",choices=["UEFA_CL","UEFA_EL"],required=True)
    p.add_argument("--home",required=True);p.add_argument("--away",required=True)
    p.add_argument("--date",required=True);p.add_argument("--time",required=True)
    p.add_argument("--index",default=INDEX_DEFAULT)
    a=p.parse_args(argv)
    idx=json.loads(Path(a.index).read_text(encoding="utf8"))
    result,_=user_requested_europe_without_xg(a.competition,a.home,a.away,
        a.date,a.time,index=idx)
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=="__main__":main()
