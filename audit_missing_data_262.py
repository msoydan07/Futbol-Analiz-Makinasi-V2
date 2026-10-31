"""Single evidence-based missing-data inventory for the 2.6.2 pipeline."""
import csv,json
from collections import Counter
from pathlib import Path
P=Path("data")
def rows(name):
 with (P/name).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def main():
 h=rows("historical_results.csv")
 x=rows("historical_verified_xg.csv")
 ids={r["fixture_id"] for r in x}
 if len(ids)!=len(x):raise ValueError("Duplicate xG fixture")
 by=Counter((r["league"],r["season"]) for r in h)
 xby=Counter((r["league"],r["season"]) for r in x)
 fields=["half_time_home_goals","half_time_away_goals","home_shots","away_shots",
         "home_shots_on_target","away_shots_on_target","home_corners","away_corners",
         "home_yellow_cards","away_yellow_cards","home_red_cards","away_red_cards"]
 out=[]
 for league,season in sorted(by):
  subset=[r for r in h if (r["league"],r["season"])==(league,season)]
  n=len(subset)
  entry={"league":league,"season":season,"matches":n,"verified_xg":xby[(league,season)],
         "xg_missing":n-xby[(league,season)],"fields":{}}
  for field in fields:
   filled=sum(r.get(field,"")!="" for r in subset)
   entry["fields"][field]={"filled":filled,"missing":n-filled}
  out.append(entry)
 audit=json.loads((P/"historical_results_audit.json").read_text(encoding="utf-8"))
 quarantine=audit.get("quarantined_stat_groups",[])
 known=[dict(q,decision="EXCLUDE_AFFECTED_SHOT_PAIR_ONLY",manual_action="NOT_REQUIRED") for q in quarantine]
 report={"known_source_anomalies":known,"known_anomaly_count":len(known),"known_anomaly_policy":"Retain valid fixture/results; ignore only invalid stat pair; revisit only if source changes","version":"262_data_inventory_v1","historical_matches":len(h),
         "verified_xg_matches":len(x),"xg_missing_total":len(h)-len(x),
         "by_league_season":out,
         "not_in_current_historical_sources":["first_half_corners","injuries","suspensions","lineups","odds"],
         "asof_policy":"Only matches with match_date strictly before prediction date",
         "manual_policy":"Do not ask for manual entry before source search and impact assessment",
         "integration_status":"verified historical xG file exists; prediction engine not yet wired"}
 (P/"missing_data_inventory_262.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"historical_matches":len(h),"verified_xg_matches":len(x),
  "xg_missing_total":len(h)-len(x),"league_seasons":len(out)},ensure_ascii=False))
if __name__=="__main__":main()
