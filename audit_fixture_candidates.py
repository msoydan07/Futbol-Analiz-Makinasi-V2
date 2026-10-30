"""Audit historical fixture rows; candidate keys are NOT permanent fixture IDs.

Requires the same football-data source as collect_team_candidates.py.
Outputs a summary and flags duplicate/ambiguous rows. No fabricated provider IDs.
"""
import csv
import io
import json
import urllib.request
from collections import Counter
from pathlib import Path
from collect_team_candidates import LEAGUES, SEASONS, BASE

OUT = Path("data")
def main():
    OUT.mkdir(exist_ok=True)
    rows_out = []
    audit = []
    for season, short in SEASONS.items():
        for league, code in LEAGUES.items():
            url = f"{BASE}/{short}/{code}.csv"
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "FutbolAnalizV2/1.0"})
                with urllib.request.urlopen(request, timeout=25) as response:
                    data = response.read().decode("utf-8-sig", errors="replace")
                matches = list(csv.DictReader(io.StringIO(data)))
                for index, row in enumerate(matches, start=2):
                    home, away, date = (row.get(k) or "").strip() for k in ("HomeTeam", "AwayTeam", "Date")
                    if not home or not away or not date:
                        rows_out.append({"season": season, "league": league, "source_row": index,
                                         "date": date, "home": home, "away": away,
                                         "candidate_key": "", "status": "MISSING_REQUIRED_FIELD"})
                        continue
                    key = json.dumps([season, league, date, home, away], ensure_ascii=False)
                    rows_out.append({"season": season, "league": league, "source_row": index,
                                     "date": date, "home": home, "away": away,
                                     "candidate_key": key, "status": "CANDIDATE_ONLY"})
                audit.append({"season": season, "league": league, "status": "OK", "rows": len(matches), "error": ""})
            except Exception as exc:
                audit.append({"season": season, "league": league, "status": "FAILED", "rows": 0, "error": str(exc)[:160]})
    counts = Counter(r["candidate_key"] for r in rows_out if r["candidate_key"])
    for row in rows_out:
        if row["candidate_key"] and counts[row["candidate_key"]] > 1:
            row["status"] = "AMBIGUOUS_DUPLICATE"
    for filename, records, fields in (
        ("fixture_candidates.csv", rows_out, ["season", "league", "source_row", "date", "home", "away", "candidate_key", "status"]),
        ("fixture_source_audit.csv", audit, ["season", "league", "status", "rows", "error"]),
    ):
        with (OUT / filename).open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)
    print("Fixture source audit:", dict(Counter(r["status"] for r in audit)))
    print("Fixture candidates:", dict(Counter(r["status"] for r in rows_out)))
    print("Permanent provider fixture IDs: NOT PROVIDED by this CSV; no fixture registered.")
    if any(r["status"] == "FAILED" for r in audit):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
