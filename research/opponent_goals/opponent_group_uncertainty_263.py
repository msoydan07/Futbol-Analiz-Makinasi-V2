"""Third-party-skeptic's read-only uncertainty interpretation of team strength cells.

Uses EXISTING fixed past-only opponent-strength report. No model fit,
no historical reprocessing, no fixture score download and no new odds.
Wilson binomial bands are merely references and can UNDERESTIMATE the
error when opponents, season shocks or match dates are dependent.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
from statistics import NormalDist

class EvidenceError(ValueError):pass
def check(condition,reason):
    if not condition:raise EvidenceError(reason)
def wilson(k,n,z=NormalDist().inv_cdf(.975)):
    check(type(k)==int and type(n)==int and 0<=k<=n,"INVALID_WILSON_COUNTS")
    if n==0:return None
    p=k/n;t=z*z/n
    midpoint=(p+t/2)/(1+t)
    half=z*math.sqrt(p*(1-p)/n+t/(4*n))/(1+t)
    return [round(max(0.,midpoint-half),4),round(min(1.,midpoint+half),4)]

def interval_for(group,metric):
    n=group["n"];p=group[metric]
    check(type(n)==int and 0<=n<=4518,"INVALID_CELL_COUNT")
    if n==0:
        check(p is None,"EMPTY_CELL_MUST_NOT_HAVE_RATE")
        return {"n":0,"empirical_rate":None,"successes":None,"95pct_Wilson_independent_reference_only":None,
               "evidence":"NO_MATCHES_CANNOT_ESTIMATE"}
    check(type(p) in (int,float) and 0<=p<=1,"INVALID_FREQUENCY")
    k=round(n*p)
    check(abs(k/n-p)<=0.000051,"FREQUENCY_NOT_INTEGER_COMPATIBLE")
    return {"n":n,"empirical_rate":p,"successes":k,
      "95pct_Wilson_independent_reference_only":wilson(k,n),
      "evidence":"INSUFFICIENT_FOR_PROSPECTIVE_TACTICAL_CLAIM" if n<30
          else "DESCRIPTIVE_NOT_OUT_OF_SAMPLE"}
def build(root):
    root=Path(root)
    src=root/"research/opponent_goals/reports/team_opponent_strength_20261110.json"
    raw=src.read_bytes()
    base=json.loads(raw.decode("utf8"))
    check(base["schema"]=="263_20261110_OPPONENT_STRENGTH_PROFILE_PAST_ONLY_V1","WRONG_BASE_SCHEMA")
    cov=base["team_opponent_venue_coverage"]
    check(cov["total_league_team_venue_strength_cells_observed"]==1280,"UNKNOWN_CELL_GROUP")
    check(cov["cells_with_under_5_past_games"]==609,"UNKNOWN_SPARSE_CELL_COUNT")
    check(cov["cells_with_8plus_past_games"]==477,"UNKNOWN_8PLUS_CELL_COUNT")
    bk=base["example_besiktas"]
    out={}
    for venue in ("HOME","AWAY"):
        out[venue]={}
        for band,group in bk[venue].items():
            out[venue][band]={
              "n":group["n"],
              "KG_VAR":interval_for(group,"btts_frequency"),
              "OVER_2_5":interval_for(group,"over_2_5_frequency"),
              "descriptive_average_goals_scored":group["avg_goals_scored"],
              "descriptive_average_goals_allowed":group["avg_goals_allowed"],
              "historic_shot_share":group["mean_historical_shot_share"],
              "can_infer_pressing_formation_or_matchup_style":False}
    home=out["HOME"]
    a=home["similar_under_50"]["OVER_2_5"]
    b=home["team_50_to_150"]["OVER_2_5"]
    if a["n"]!=11 or b["n"]!=10:
        raise EvidenceError("BESIKTAS_HOME_SAMPLES_CHANGED")
    return {
      "schema":"263_GOALS_OPPONENT_STRENGTH_SAMPLE_UNCERTAINTY_V1",
      "decision":"DO_NOT_PROMOTE_OPPONENT_STRENGTH_STYLE_COEFFICIENT",
      "source_report_sha256":hashlib.sha256(raw).hexdigest(),
      "source_history_sha256":base["accepted_history_sha256"],
      "cell_coverage":{"n_total":1280,"n_under_5":609,
                       "percent_under_5":round(609/1280*100,2),
                       "n_8plus":477,"percent_8plus":round(477/1280*100,2)},
      "besiktas_home_only_reference":{"similar_opponent_2_5_Over_n":a["n"],
                         "similar_opponent_2_5_Over_k":a["successes"],
                         "team_50_to_150_ahead_2_5_Over_n":b["n"],
                         "team_50_to_150_ahead_2_5_Over_k":b["successes"],
                         "intervals_overlap":not (a["95pct_Wilson_independent_reference_only"][1]<
                                                   b["95pct_Wilson_independent_reference_only"][0] or
                                                   b["95pct_Wilson_independent_reference_only"][1]<
                                                   a["95pct_Wilson_independent_reference_only"][0])},
      "team_and_strength_category_intervals":out,
      "limitations":[
        "Historic outcome frequencies are NOT pre-match probabilities or tactical press/low-block labels",
        "Wilson assumes independent binomial observations: team games across league/seasons correlated, CI may be too narrow",
        "Grouping by past Elo plus home/away divides team history into tiny cells; don't turn 8/10 into an 80% future forecast",
        "Retrospective report reuses previously studied data and neither calibrates nor improves M4 by itself",
        "No new xG, pressing or lineup source identified for all 10 current-season leagues",
        "No original 4518 file, forecasts, model parameters, odds or official postmatch attestation modified"
      ],
      "original_m4_and_seals_changed":False,
      "probability_recalibration_authorized":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    obj=build(args.root)
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():
        if json.loads(out.read_text(encoding="utf8"))!=obj:
            raise EvidenceError("EXISTING_RESEARCH_REPORT_DIFFERS")
    else:out.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"decision":obj["decision"],"sample_coverage":obj["cell_coverage"],
          "home_besiktas_over25":obj["besiktas_home_only_reference"],
          "intervals":{"similar":obj["team_and_strength_category_intervals"]["HOME"]["similar_under_50"]["OVER_2_5"]["95pct_Wilson_independent_reference_only"],
            "moderate_favorite":obj["team_and_strength_category_intervals"]["HOME"]["team_50_to_150"]["OVER_2_5"]["95pct_Wilson_independent_reference_only"]}},ensure_ascii=False))

if __name__=="__main__":main()
