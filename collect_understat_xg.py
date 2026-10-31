"""Export Understat match xG for five leagues to the strict audit CSV schema.

Run after installing soccerdata:
  python -m pip install soccerdata
  python collect_understat_xg.py
  python audit_understat_xg.py --understat-csv data/understat_matches.csv

Experimental read-only collection. Never joins directly into prediction features.
"""
import csv
from datetime import datetime
from pathlib import Path

LEAGUES = {
    "ENG-Premier League": "ENG1",
    "GER-Bundesliga": "GER1",
    "ESP-La Liga": "ESP1",
    "ITA-Serie A": "ITA1",
    "FRA-Ligue 1": "FRA1",
}
SEASONS = {"2526": "2025-2026", "2627": "2026-2027"}
COLUMNS = ["league","season","match_date","home_team","away_team",
           "home_goals","away_goals","home_xg","away_xg","source_url"]

def export():
    import soccerdata as sd
    reader = sd.Understat(leagues=list(LEAGUES), seasons=list(SEASONS))
    df = reader.read_schedule(include_matches_without_data=False).reset_index()
    rows = []
    for record in df.to_dict(orient="records"):
        league = LEAGUES.get(str(record["league"]))
        season = SEASONS.get(str(record["season"]))
        if not league or not season or not bool(record["is_result"]):
            continue
        date = record["date"]
        day = date.date().isoformat() if hasattr(date, "date") else str(date)[:10]
        if any(str(record.get(k, "")).lower() in ("nan","none","<na>","")
               for k in ("home_goals","away_goals","home_xg","away_xg")):
            continue
        rows.append({"league":league,"season":season,"match_date":day,
                     "home_team":record["home_team"],"away_team":record["away_team"],
                     "home_goals":int(record["home_goals"]),
                     "away_goals":int(record["away_goals"]),
                     "home_xg":record["home_xg"],"away_xg":record["away_xg"],
                     "source_url":record["url"]})
    out = Path("data/understat_matches.csv")
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8",newline="") as file:
        writer = csv.DictWriter(file,fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Understat rows exported: {len(rows)}; file: {out}")
    if not rows:
        raise RuntimeError("No finished matches returned; inspect league/season compatibility")

if __name__ == "__main__":
    export()
