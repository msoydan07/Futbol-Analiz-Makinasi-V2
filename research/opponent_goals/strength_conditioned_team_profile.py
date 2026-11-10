"""Honest team-vs-opponent-strength descriptive profile, NO tactics inferred.

Pre-match Elo ratings of PAST matches; current opponent labels are just prior
strength buckets. Past shots/SOT are disclosed historical outcomes, NOT
pressing, defensive-block height, xG or guaranteed counterattacking behavior.
"""
from __future__ import annotations
import argparse,json
from collections import defaultdict,Counter
from pathlib import Path
from datetime import date
from data_opponent_goal_audit import read_rows,past_only_elo

LABELS=("opponent_150_plus","opponent_50_to_150","similar_under_50","team_50_to_150","team_150_plus")
class MatchupBlocked(ValueError):pass

def opponent_band(our_minus_their):
    if our_minus_their<=-150:return LABELS[0]
    if our_minus_their<=-50:return LABELS[1]
    if our_minus_their<50:return LABELS[2]
    if our_minus_their<150:return LABELS[3]
    return LABELS[4]

def measure(group):
    n=len(group)
    def avr(k):return round(sum(r[k] for r in group)/n,4) if n else None
    n_shots=sum(r["shot_team"] is not None and r["shot_opp"] is not None for r in group)
    shot_share=(sum(r["shot_team"]/(r["shot_team"]+r["shot_opp"]) for r in group
                    if r["shot_team"] is not None and r["shot_opp"] is not None
                       and r["shot_team"]+r["shot_opp"]>0))
    n_share=sum(r["shot_team"] is not None and r["shot_opp"] is not None
                and r["shot_team"]+r["shot_opp"]>0 for r in group)
    return {"n":n,
            "matches_with_8plus_pre_match_team_and_opponent_history":sum(r["both_prior_8plus"] for r in group),
            "avg_goals_scored":avr("gf"),"avg_goals_allowed":avr("ga"),
            "avg_points":avr("pts"),"btts_frequency":avr("btts"),
            "over_2_5_frequency":avr("over25"),
            "shot_pair_coverage":n_shots,
            "mean_historical_shot_share":round(shot_share/n_share,4) if n_share else None,
            "quality_flag":"DESCRIPTIVE_MIN_8_GAMES_ONLY_NOT_TACTICALLY_GROUNDED" if n>=8 else "TOO_FEW_FOR_OPPONENT_STYLE_OR_INDEPENDENT_PROBABILITY"}

def audit(root,cutoff="2026-11-10"):
    root=Path(root); rows,header,sha=read_rows(root/"data/quad_accepted_263/extended_history.csv")
    date.fromisoformat(cutoff)
    past=[r for r in rows if r["match_date"]<cutoff]
    snapshots=past_only_elo(past)
    team_game=defaultdict(list)
    all_games=Counter()
    for r in past:
        snap=snapshots[r["fixture_id"]]
        hg,ag=int(r["home_goals"]),int(r["away_goals"])
        for side in ("home","away"):
            home=(side=="home")
            team=r[f"{side}_id"]; league=r["league"]
            diff=(1 if home else -1)*snap["gap"]
            our_shots,other_shots=r.get(f"{side}_shots",""),r.get(f"{'away' if home else 'home'}_shots","")
            hstats=(int(our_shots) if our_shots not in ("",None) else None,
                    int(other_shots) if other_shots not in ("",None) else None)
            record={
             "gf":hg if home else ag,
             "ga":ag if home else hg,
             "btts":int(hg>0 and ag>0),
             "over25":int(hg+ag>=3),
             "pts":3 if (hg>ag if home else ag>hg) else 1 if hg==ag else 0,
             "shot_team":hstats[0],"shot_opp":hstats[1],
             "both_prior_8plus":min(snap["home_prior_count"],snap["away_prior_count"])>=8}
            team_game[(league,team,"HOME" if home else "AWAY",opponent_band(diff))].append(record)
            all_games[(league,team)]+=1
    if len(past)!=4518:raise MatchupBlocked("UNEXPECTED_LOSS_OF_ACCEPTED_HISTORY")
    cells={"total_league_team_venue_strength_cells_observed":len(team_game),
           "cells_with_8plus_past_games":sum(len(v)>=8 for v in team_game.values()),
           "cells_with_5plus_past_games":sum(len(v)>=5 for v in team_game.values()),
           "cells_with_under_5_past_games":sum(len(v)<5 for v in team_game.values())}
    idx=json.loads((root/"experiments/263/evidence/identity_index_263.json").read_text(encoding="utf8"))
    besiktas=idx["aliases"]["besiktas"]
    focus={}
    for venue in ("HOME","AWAY"):
        focus[venue]={b:measure(team_game.get(("TUR1",besiktas,venue,b),[])) for b in LABELS}
    # Privacy-safe no individual past match list or provider raw rows.
    return {"schema":"263_20261110_OPPONENT_STRENGTH_PROFILE_PAST_ONLY_V1",
            "accepted_history_sha256":sha,"as_of_exclusive":cutoff,"leagues":10,
            "past_accepted_matches":len(past),
            "strength_rating":"Fixed, league-local 1500 start, home+65, K18, before same-day scores; no parameter tuning.",
            "team_opponent_venue_coverage":cells,
            "example_besiktas_team_id":besiktas,"example_besiktas":focus,
            "all_teams_sample_sizes_per_league":dict(Counter({l:sum(1 for (lg,team) in all_games if lg==l) for l in sorted({lg for lg,team in all_games})})),
            "opponent_strength_proxy_is_not_formation_or_pressing":True,
            "not_a_live_match_forecast":True,"new_model_integration":False,
            "limitation":"Shots/gols in previous matches reveal past outcomes, not future tactical behavior. Each score band can have tiny sample; team opponent profile cannot be treated as % probability without calibration."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--root",default=".")
    p.add_argument("--out",required=True)
    a=p.parse_args();data=audit(a.root)
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if json.loads(path.read_text(encoding="utf8"))!=data:raise MatchupBlocked("AUDIT_SOURCE_CHANGED")
    else:path.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"cells":data["team_opponent_venue_coverage"],
         "besiktas_home":data["example_besiktas"]["HOME"],
         "besiktas_away":data["example_besiktas"]["AWAY"]},ensure_ascii=False))
if __name__=="__main__":main()
