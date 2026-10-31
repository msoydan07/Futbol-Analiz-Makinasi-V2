"""Build conservative Understat-to-Football-Data aliases using reviewed official team names.

Only exact official-name joins or explicit, reviewed aliases are accepted.
Never infer team identity from a matching score alone.
"""
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

LEAGUE_FED={"ENG1":{"Premier League","EFL"},"GER1":{"Bundesliga"},
            "ESP1":{"LALIGA"},"ITA1":{"Lega Serie A"},"FRA1":{"LFP"}}
# Understat source name -> Football-Data source name, manually reviewed club identity.
OVERRIDES={
 "ENG1":{"Bournemouth":"Bournemouth","Brighton":"Brighton","Manchester City":"Man City",
         "Manchester United":"Man United","Newcastle United":"Newcastle",
         "Nottingham Forest":"Nott'm Forest","Tottenham":"Tottenham",
         "West Ham":"West Ham","Wolverhampton Wanderers":"Wolves"},
 "GER1":{"Bayer Leverkusen":"Leverkusen","Borussia Dortmund":"Dortmund",
         "Borussia M.Gladbach":"M'gladbach","Bayern Munich":"Bayern Munich",
         "Eintracht Frankfurt":"Ein Frankfurt","FC Cologne":"FC Koln",
         "FC Heidenheim":"Heidenheim","Freiburg":"Freiburg","Hamburger SV":"Hamburg",
         "Mainz 05":"Mainz","RasenBallsport Leipzig":"RB Leipzig","St. Pauli":"St Pauli",
         "VfB Stuttgart":"Stuttgart","Werder Bremen":"Werder Bremen"},
 "ESP1":{"Alaves":"Alaves","Athletic Club":"Ath Bilbao","Atletico Madrid":"Ath Madrid",
         "Barcelona":"Barcelona","Celta Vigo":"Celta","Espanyol":"Espanol",
         "Deportivo La Coruna":"La Coruna","Racing Santander":"Santander","Real Betis":"Betis",
         "Real Sociedad":"Sociedad","Rayo Vallecano":"Vallecano"},
 "ITA1":{"AC Milan":"Milan","Inter":"Inter","Parma Calcio 1913":"Parma"},
 "FRA1":{"Paris Saint Germain":"Paris SG","Marseille":"Marseille","Monaco":"Monaco"}
}
def norm(s):
    return re.sub(r"\\s+"," ",unicodedata.normalize("NFKC",s).casefold().strip())
def load(path):
    with open(path,encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def main():
    official=load("data/official_team_names.csv")
    observed=load("data/team_candidates.csv")
    understat=load("data/understat_matches.csv")
    names=defaultdict(set)
    for r in observed:
        names[r["league"]].add(r["source_name"])
    by_official=defaultdict(lambda:defaultdict(set))
    for r in official:
        if r["review_status"]!="VERIFIED":continue
        for league,feds in LEAGUE_FED.items():
            if r["federation"] in feds and r["source_name"] in names[league]:
                by_official[league][norm(r["official_name"])].add(r["source_name"])
    candidates=defaultdict(set)
    for r in understat:
        if r["league"] in LEAGUE_FED:
            candidates[r["league"]].update([r["home_team"],r["away_team"]])
    aliases={}
    report=[]
    for league in sorted(candidates):
        aliases[league]={}
        for name in sorted(candidates[league]):
            if name in names[league]:
                report.append({"league":league,"understat":name,"football_data":name,"status":"EXACT"})
                continue
            target=OVERRIDES.get(league,{}).get(name)
            status="REVIEWED_OVERRIDE" if target else ""
            if not target:
                matches=by_official[league].get(norm(name),set())
                if len(matches)==1:
                    target=next(iter(matches))
                    status="OFFICIAL_EXACT"
            if target and target in names[league]:
                aliases[league][name]=target
                report.append({"league":league,"understat":name,"football_data":target,"status":status})
            else:
                report.append({"league":league,"understat":name,"football_data":"","status":"UNRESOLVED"})
    Path("data/understat_reviewed_aliases.json").write_text(json.dumps(aliases,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with open("data/understat_alias_review.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["league","understat","football_data","status"])
        w.writeheader();w.writerows(report)
    print(json.dumps({"total_names":len(report),"statuses":{k:sum(r["status"]==k for r in report)
          for k in sorted({r["status"] for r in report})}},ensure_ascii=False))
if __name__=="__main__":main()
