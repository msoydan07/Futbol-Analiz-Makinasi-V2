"""Read-only 2.6.2 data readiness report. No prediction/model calculations."""
import csv,json
from pathlib import Path
from collections import Counter
P=Path("data")
def read(name):
 with (P/name).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def main():
 h=read("historical_results.csv")
 x=read("historical_verified_xg.csv")
 by=Counter((r["league"],r["season"]) for r in h)
 xby=Counter((r["league"],r["season"]) for r in x)
 required={
  "full_time_result":["home_goals","away_goals","result"],
  "half_time_result":["half_time_home_goals","half_time_away_goals","half_time_result"],
  "shots":["home_shots","away_shots"],
  "shots_on_target":["home_shots_on_target","away_shots_on_target"],
  "full_time_corners":["home_corners","away_corners"],
  "fouls":["home_fouls","away_fouls"],
  "yellow_cards":["home_yellow_cards","away_yellow_cards"],
  "red_cards":["home_red_cards","away_red_cards"]
 }
 league_rows=[]
 for league,season in sorted(by):
  subset=[r for r in h if r["league"]==league and r["season"]==season]
  coverage={}
  for group,fields in required.items():
   filled=sum(all(r.get(k,"")!="" for k in fields) for r in subset)
   coverage[group]={"present":filled,"missing":len(subset)-filled,"coverage_pct":round(100*filled/len(subset),2)}
  coverage["verified_xg"]={"present":xby[(league,season)],"missing":len(subset)-xby[(league,season)],"coverage_pct":round(100*xby[(league,season)]/len(subset),2)}
  league_rows.append({"league":league,"season":season,"historical_matches":len(subset),"coverage":coverage})
 groups={k:{"present":sum(r["coverage"][k]["present"] for r in league_rows),"missing":sum(r["coverage"][k]["missing"] for r in league_rows)} for k in [*required,"verified_xg"]}
 excluded={"injuries":"MATCHDAY_ONLY","suspensions":"MATCHDAY_ONLY","confirmed_lineups":"MATCHDAY_ONLY","first_half_corners":"OUT_OF_SCOPE_BY_DECISION"}
 missing_external={"future_seven_day_fixtures":"NOT_VERIFIED","official_kickoff_times":"NOT_VERIFIED","odds_and_timestamp":"NOT_COLLECTED","rest_and_travel":"NEEDS_FUTURE_FIXTURES","referee":"NOT_IMPORTED","tactical_context":"NOT_COLLECTED"}
 out={"version":"262_data_readiness_v1","separation":"SOURCE_AND_COVERAGE_ONLY; no predictions, Elo, Poisson or probability computations","historical_matches":len(h),"league_season_groups":len(league_rows),"coverage_totals":groups,"by_league_season":league_rows,"excluded_or_matchday":excluded,"external_data_gaps":missing_external,"decision":"DATA_PREPARATION_INCOMPLETE","manual_entry":"Only after verified-source search; record source URL and retrieval timestamp","notes":["Missing xG is missing, never replaced with invented numbers","Group present requires all constituent fields nonempty","This report does not certify correctness of every source statistic"]}
 (P/"262_data_readiness.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"historical_matches":len(h),"league_season_groups":len(league_rows),"coverage_totals":groups,"external_data_gaps":missing_external,"decision":out["decision"]},ensure_ascii=False))
if __name__=="__main__":main()
