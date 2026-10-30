"""Audit actual team names in ten leagues, two seasons; no automatic identity guesses.

Usage: python collect_team_candidates.py
Produces data/team_candidates.csv and data/source_audit.csv.
Only source-observed names are written. The identity registry is not mutated.
"""
import csv
import io
import urllib.error
import urllib.request
from pathlib import Path

LEAGUES = {
    "ENG1": "E0", "ENG2": "E1", "GER1": "D1", "ESP1": "SP1",
    "ITA1": "I1", "FRA1": "F1", "NED1": "N1", "TUR1": "T1",
    "POR1": "P1", "BEL1": "B1",
}
SEASONS = {"2025-2026": "2526", "2026-2027": "2627"}
BASE = "https://www.football-data.co.uk/mmz4281"
OUT = Path("data")


def collect():
    OUT.mkdir(exist_ok=True)
    teams, audit = [], []
    for season, short in SEASONS.items():
        for league, code in LEAGUES.items():
            url = f"{BASE}/{short}/{code}.csv"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "FutbolAnalizV2/1.0"})
                with urllib.request.urlopen(req, timeout=25) as response:
                    payload = response.read().decode("utf-8-sig", errors="replace")
                rows = list(csv.DictReader(io.StringIO(payload)))
                if not rows or not {"HomeTeam", "AwayTeam"}.issubset(rows[0]):
                    raise ValueError("Missing HomeTeam/AwayTeam columns")
                names = sorted({(row.get(key) or "").strip() for row in rows
                                for key in ("HomeTeam", "AwayTeam")} - {""})
                if not names:
                    raise ValueError("No team names")
                teams.extend({"season": season, "league": league, "source_name": name,
                              "canonical_key": "", "review_status": "PENDING"}
                             for name in names)
                audit.append({"season": season, "league": league, "url": url,
                              "status": "OK", "rows": len(rows), "teams": len(names), "error": ""})
            except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
                audit.append({"season": season, "league": league, "url": url,
                              "status": "FAILED", "rows": 0, "teams": 0,
                              "error": str(exc)[:160]})
    for filename, fields, rows in (
        ("team_candidates.csv", ["season", "league", "source_name", "canonical_key", "review_status"], teams),
        ("source_audit.csv", ["season", "league", "url", "status", "rows", "teams", "error"], audit),
    ):
        with (OUT / filename).open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    failures = sum(row["status"] != "OK" for row in audit)
    print(f"Sources: {len(audit)}, successful: {len(audit)-failures}, failed: {failures}; candidate rows: {len(teams)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(collect())
