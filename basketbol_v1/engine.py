"""Basketbol V1: a coherent score/margin and total distribution, no odds."""
from __future__ import annotations
import math
from collections import defaultdict
from dataclasses import dataclass

VARIANTS=("BASE","ELO","FORM","HYBRID")
PRIOR={"NBA":{"points":112.0,"home":2.2,"sd_margin":15.0,"sd_total":20.0},
       "EL":{"points":82.0,"home":3.2,"sd_margin":12.0,"sd_total":16.0}}
def phi(x):return (1+math.erf(x/math.sqrt(2)))/2
def clipped(p):return min(1-1e-8,max(1e-8,p))

@dataclass(frozen=True)
class Forecast:
    league:str
    season:int
    day:str
    home:str
    away:str
    variant:str
    margin:float
    total:float
    sd_margin:float
    sd_total:float
    prior_games:int
    @property
    def home_score(self):return (self.total+self.margin)/2
    @property
    def away_score(self):return (self.total-self.margin)/2
    def home_win(self):return clipped(phi(self.margin/self.sd_margin))
    def over(self,line):
        if not isinstance(line,(int,float)) or not math.isfinite(line) or line%1==0:
            raise ValueError("HALF_POINT_TOTAL_LINE_REQUIRED_NO_PUSH")
        return clipped(phi((self.total-line)/self.sd_total))
    def cover(self,home_handicap):
        if not isinstance(home_handicap,(int,float)) or not math.isfinite(home_handicap) or home_handicap%1==0:
            raise ValueError("HALF_POINT_HANDICAP_REQUIRED_NO_PUSH")
        return clipped(phi((self.margin+home_handicap)/self.sd_margin))
    def json(self,total_line=None,home_handicap=None):
        x={"league":self.league,"season":self.season,"day":self.day,"home":self.home,"away":self.away,
           "model":self.variant,"expected_home":round(self.home_score,2),"expected_away":round(self.away_score,2),
           "margin":round(self.margin,2),"total":round(self.total,2),"p_home":round(self.home_win(),5),
           "p_away":round(1-self.home_win(),5),"prior_games":self.prior_games,
           "sd_margin":round(self.sd_margin,2),"sd_total":round(self.sd_total,2)}
        if total_line is not None:
            x.update(total_line=total_line,p_over=round(self.over(total_line),5),
                     p_under=round(1-self.over(total_line),5))
        if home_handicap is not None:
            x.update(home_handicap=home_handicap,p_home_cover=round(self.cover(home_handicap),5),
                     p_away_cover=round(1-self.cover(home_handicap),5))
        x["research_only_no_betting_or_odd"]=True
        return x

class Ratings:
    def __init__(self,league):
        if league not in PRIOR:raise ValueError("UNKNOWN_LEAGUE")
        x=PRIOR[league]
        self.league=league;self.mu=x["points"];self.ha=x["home"]
        self.elo=defaultdict(float);self.off=defaultdict(float);self.concede=defaultdict(float)
        self.var={name:[x["sd_margin"]**2,x["sd_total"]**2] for name in VARIANTS}
        self.season=None;self.last_day=None;self.count=0;self.teams=set()
    def start_season(self,season):
        if self.season is not None and season<=self.season:raise ValueError("SEASON_NON_CHRONOLOGICAL")
        if self.season is not None:
            for d,factor in ((self.elo,.62),(self.off,.48),(self.concede,.48)):
                for team in d:d[team]*=factor
        self.season=season
    def predict(self,season,day,home,away,neutral=False):
        if self.season!=season:raise ValueError("NOT_IN_SEASON")
        if self.last_day is not None and day<=self.last_day:raise ValueError("TODAY_OR_PAST_DENIED")
        if home==away:raise ValueError("SAME_TEAM")
        advantage=0 if neutral else self.ha
        m_elo=advantage+self.elo[home]-self.elo[away]
        home_form=self.mu+advantage/2+self.off[home]+self.concede[away]
        away_form=self.mu-advantage/2+self.off[away]+self.concede[home]
        m_form=home_form-away_form;t_form=home_form+away_form
        vals={"BASE":(advantage,2*self.mu),
              "ELO":(m_elo,2*self.mu),
              "FORM":(m_form,t_form),
              "HYBRID":(.60*m_elo+.40*m_form,.15*2*self.mu+.85*t_form)}
        return {name:Forecast(self.league,season,day,home,away,name,m,t,
                              max(7,math.sqrt(self.var[name][0])),
                              max(9,math.sqrt(self.var[name][1])),self.count)
                for name,(m,t) in vals.items()}
    def apply_day(self,games,prior):
        if not games:return
        day=games[0].day
        if any(g.day!=day for g in games):raise ValueError("MULTIPLE_DAYS")
        if self.last_day is not None and day<=self.last_day:raise ValueError("LEAKY_DAY")
        # Every forecast for the whole day was already calculated.
        for g in games:
            if set(prior[g.game_id])!=set(VARIANTS):raise ValueError("MISSING_FORECAST")
        for g in games:
            h,a=g.home,g.away;ha=0 if g.neutral else self.ha
            diff=g.margin-(ha+self.elo[h]-self.elo[a])
            self.elo[h]+=.075*diff;self.elo[a]-=.075*diff
            ehome=g.home_score-(self.mu+ha/2+self.off[h]+self.concede[a])
            eaway=g.away_score-(self.mu-ha/2+self.off[a]+self.concede[h])
            self.off[h]+=.07*ehome;self.concede[a]+=.07*ehome
            self.off[a]+=.07*eaway;self.concede[h]+=.07*eaway
            self.mu+=.012*(g.total/2-self.mu)
            for name,f in prior[g.game_id].items():
                z=self.var[name]
                z[0]=.985*z[0]+.015*min((g.margin-f.margin)**2,2500)
                z[1]=.985*z[1]+.015*min((g.total-f.total)**2,4900)
            self.teams.update((h,a));self.count+=1
        self.last_day=day

def replay(games):
    if not games:return []
    if len({g.league for g in games})!=1:raise ValueError("MIXED_LEAGUES")
    if len({(g.season,g.game_id) for g in games})!=len(games):raise ValueError("DUPLICATE_GAME")
    ordered=sorted(games,key=lambda g:(g.season,g.day,g.game_id))
    bydate=defaultdict(list)
    for g in ordered:bydate[(g.season,g.day)].append(g)
    state=Ratings(games[0].league);out=[]
    for (season,day),slate in sorted(bydate.items()):
        if state.season!=season:state.start_season(season)
        predictions={g.game_id:state.predict(season,day,g.home,g.away,g.neutral) for g in slate}
        for g in slate:
            for p in predictions[g.game_id].values():out.append((g,p))
        state.apply_day(slate,predictions)
    return out

def before_game(games,league,season,day,home,away,neutral=False):
    if league not in PRIOR:raise ValueError("UNKNOWN_LEAGUE")
    hist=[g for g in games if g.league==league and
          (g.season<season or g.season==season and g.day<day)]
    if not hist:raise ValueError("NO_PRIOR_DATA")
    state=Ratings(league);bydate=defaultdict(list)
    for g in hist:bydate[(g.season,g.day)].append(g)
    for (s,d),slate in sorted(bydate.items()):
        if state.season!=s:state.start_season(s)
        p={g.game_id:state.predict(s,d,g.home,g.away,g.neutral) for g in slate}
        state.apply_day(slate,p)
    if state.season<season:state.start_season(season)
    if home not in state.teams or away not in state.teams:raise ValueError("UNKNOWN_TEAM")
    return state.predict(season,day,home,away,neutral)
