"""Build a leakage-safe, identity-linked historical results table.

Re-fetches sources, but rejects any mismatch with the fixture audit snapshot.
No future information is used; same-day ordering is not inferred.
"""
import csv
import io
import json
import urllib.request
from collections import Counter
from pathlib import Path
from audit_result_quality import inspect
from collect_team_candidates import LEAGUES, SEASONS, BASE
from identity import Registry
from import_real_fixtures import parse_date

ROOT = Path("data")
FIELDS = ["fixture_id", "league", "season", "match_date", "home_id", "away_id",
          "home_goals", "away_goals", "result", "source_row", "source_url"]

def build():
    registry = Registry(ROOT / "match_registry.json")
    with (ROOT / "fixture_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
        candidates = list(csv.DictReader(f))
    with (ROOT / "fixture_source_audit.csv").open(encoding="utf-8-sig", newline="") as f:
        audits = list(csv.DictReader(f))
    report = {"expected_rows": len(candidates), "sources": 0, "linked": 0,
              "errors": [], "league_season_counts": {}}
    out = []
    source_rows = {(r["season"], r["league"], int(r["source_row"])): r for r in candidates}
    fixture_index = {}
    for fid, fixture in registry.data["fixtures"].items():
        key = (fixture["league"], fixture["season"], fixture["home_id"],
               fixture["away_id"], fixture["match_date"])
        if key in fixture_index:
            report["errors"].append("Duplicate registry identity: " + repr(key))
        fixture_index[key] = fid
    for season, short in SEASONS.items():
        for league, code in LEAGUES.items():
            url = f"{BASE}/{short}/{code}.csv"
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "FutbolAnalizV2/1.0"})
                with urllib.request.urlopen(request, timeout=25) as response:
                    payload = response.read().decode("utf-8-sig", errors="replace")
                reader = csv.DictReader(io.StringIO(payload))
                rows = list(reader)
                audited = [a for a in audits if a["season"] == season and a["league"] == league]
                if len(audited) != 1 or audited[0]["status"] != "OK" or int(audited[0]["rows"]) != len(rows):
                    raise ValueError("Source count changed since fixture audit")
                report["sources"] += 1
                for number, row in enumerate(rows, start=2):
                    candidate = source_rows.get((season, league, number))
                    if candidate is None:
                        raise ValueError(f"Missing source row {number}")
                    home, away, date = ((row.get(k) or "").strip() for k in ("HomeTeam", "AwayTeam", "Date"))
                    if (home, away, date) != (candidate["home"], candidate["away"], candidate["date"]):
                        raise ValueError(f"Source row changed at {number}; refuse stale join")
                    if candidate["status"] != "CANDIDATE_ONLY":
                        raise ValueError(f"Noncandidate source row {number}: {candidate['status']}")
                    status, reason = inspect(row)
                    if status != "COMPLETE":
                        raise ValueError(f"Source row {number} no longer complete: {status} {reason}")
                    home_id, away_id = registry.resolve_team(home), registry.resolve_team(away)
                    key = (league, season, home_id, away_id, parse_date(date))
                    fid = fixture_index.get(key)
                    if not fid:
                        raise ValueError(f"Unlinked fixture row {number}: {key}")
                    out.append({"fixture_id": fid, "league": league, "season": season,
                                "match_date": key[-1], "home_id": home_id, "away_id": away_id,
                                "home_goals": int(row["FTHG"]), "away_goals": int(row["FTAG"]),
                                "result": row["FTR"], "source_row": number, "source_url": url})
            except Exception as exc:
                report["errors"].append(f"{season}/{league}: {exc}")
    report["linked"] = len(out)
    report["league_season_counts"] = dict(Counter(f'{r["league"]}/{r["season"]}' for r in out))
    report["distinct_fixture_ids"] = len({r["fixture_id"] for r in out})
    report["chronology_rule"] = "Order by match_date; same-date matches have no assumed kickoff order"
    report["future_leakage_rule"] = "For predictions, use only prior dates, never same-day or later matches"
    report["accepted"] = (not report["errors"] and report["sources"] == 20 and
                          len(out) == len(candidates) == len(registry.data["fixtures"]) and
                          report["distinct_fixture_ids"] == len(out))
    (ROOT / "historical_results_audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["accepted"]:
        raise SystemExit("Historical result join rejected; inspect historical_results_audit.json")
    out.sort(key=lambda r: (r["match_date"], r["league"], r["fixture_id"]))
    with (ROOT / "historical_results.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out)

if __name__ == "__main__":
    build()
