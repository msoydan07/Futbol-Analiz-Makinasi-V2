"""A real computational pregame SCENARIO, not official fixture verification."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from sources import download
from benchmark import SPLIT,choose_dev,grade
from engine import replay,before_game

def calculate(*,league,day,home,away,total_line=None,home_handicap=None,neutral=False,clock=None):
    clock=clock or datetime.now(timezone.utc)
    if clock.tzinfo is None:raise ValueError("AWARE_CLOCK_REQUIRED")
    today=clock.astimezone(ZoneInfo("Europe/Istanbul")).date().isoformat()
    if day<today:raise ValueError("RETROACTIVE_PREGAME_REQUEST_DENIED")
    if league not in SPLIT:raise ValueError("LEAGUE_NOT_VERIFIED")
    season=SPLIT[league]["current_replay"]
    games,manifest=download(league)
    # Selection only on an earlier historical development season, never on game result.
    allrows=replay(games)
    dev={name:grade([(g,p) for g,p in allrows
                      if g.season==SPLIT[league]["development"] and p.variant==name])
         for name in ("BASE","ELO","FORM","HYBRID")}
    chosen,_=choose_dev(dev)
    forecasts=before_game(games,league,season,day,home,away,neutral)
    return {"schema":"BASKETBOL_V1_SCENARIO_NO_OFFICIAL_FIXTURE_VERIFICATION",
            "created_at_utc":clock.astimezone(timezone.utc).isoformat(),
            "request_day_turkey":today,
            "model_selection_development_season":SPLIT[league]["development"],
            "selected_historical_model":chosen,
            "forecast":forecasts[chosen].json(total_line,home_handicap),
            "source_snapshots":manifest,
            "event_officially_scheduled_verified":False,
            "live_forward_pilot_shalocked":False,
            "odds_or_bet_recommendation":False,
            "caveat":"Fixture not independently confirmed; scores-only model lacks injury, roster and possession context."}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--league",choices=["NBA","EL","EC"],required=True)
    a.add_argument("--day",required=True)
    a.add_argument("--home",required=True)
    a.add_argument("--away",required=True)
    a.add_argument("--total-line",type=float)
    a.add_argument("--home-handicap",type=float)
    a.add_argument("--neutral",action="store_true")
    a.add_argument("--out",required=True)
    x=a.parse_args()
    result=calculate(league=x.league,day=x.day,home=x.home,away=x.away,
                     total_line=x.total_line,home_handicap=x.home_handicap,neutral=x.neutral)
    Path(x.out).write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"warning":"UNVERIFIED_FIXTURE_SCENARIO_ONLY","forecast":result["forecast"]},ensure_ascii=False))
if __name__=="__main__":main()
