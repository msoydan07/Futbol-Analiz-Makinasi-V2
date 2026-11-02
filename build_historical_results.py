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
STAT_COLUMNS = {"half_time_home_goals":"HTHG","half_time_away_goals":"HTAG","half_time_result":"HTR","home_shots":"HS","away_shots":"AS","home_shots_on_target":"HST","away_shots_on_target":"AST","home_corners":"HC","away_corners":"AC","home_fouls":"HF","away_fouls":"AF","home_yellow_cards":"HY","away_yellow_cards":"AY","home_red_cards":"HR","away_red_cards":"AR"}
GROUPS = {"half_time":["half_time_home_goals","half_time_away_goals","half_time_result"],"shots":["home_shots","away_shots","home_shots_on_target","away_shots_on_target"],"corners":["home_corners","away_corners"],"fouls":["home_fouls","away_fouls"],"cards":["home_yellow_cards","away_yellow_cards","home_red_cards","away_red_cards"]}
def read_stats(row, league, season, coverage, quarantined, source_row):
    result = {}
    for key, col in STAT_COLUMNS.items():
        raw = (row.get(col) or "").strip()
        if not raw:
            result[key] = ""
        elif col == "HTR":
            if raw not in ("H","D","A"): raise ValueError("Invalid HTR")
            result[key] = raw
        else:
            try: val = int(raw)
            except ValueError: raise ValueError("Invalid "+col+": "+raw)
            if val < 0: raise ValueError("Negative "+col)
            result[key] = val
    h,a,r = (result[k] for k in GROUPS["half_time"])
    if h != "" and a != "":
        if h > int(row["FTHG"]) or a > int(row["FTAG"]): raise ValueError("HT goals exceed FT goals")
        if r != "" and r != ("H" if h>a else "A" if h<a else "D"): raise ValueError("HTR mismatch")
    for side in ("home","away"):
        shots, target = result[side+"_shots"],result[side+"_shots_on_target"]
        if shots != "" and target != "" and target > shots:
            quarantined.append({"league":league,"season":season,"source_row":source_row,"side":side,"reason":"shots_on_target_exceed_shots","source_shots":shots,"source_shots_on_target":target})
            result[side+"_shots"] = ""
            result[side+"_shots_on_target"] = ""
    for group, fields in GROUPS.items():
        if all(result[k] != "" for k in fields): coverage[league+"/"+season+"/"+group] += 1
    return result

FIELDS = ["fixture_id", "league", "season", "match_date", "home_id", "away_id",
          "home_goals", "away_goals", "result", "source_row", "source_url"] + list(STAT_COLUMNS)

def build():
    registry = Registry(ROOT / "match_registry.json")
    with (ROOT / "fixture_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
        candidates = list(csv.DictReader(f))
    with (ROOT / "fixture_source_audit.csv").open(encoding="utf-8-sig", newline="") as f:
        audits = list(csv.DictReader(f))
    completed_candidates = [r for r in candidates if r["status"] == "CANDIDATE_ONLY"]
    unplayed_candidates = [r for r in candidates if r["status"] == "UNPLAYED_SOURCE_ROW"]
    empty_candidates = [r for r in candidates if r["status"] == "EMPTY_SOURCE_ROW"]
    # Pipeline acceptance counts ONLY completed score records, never future
    # scoreless fixtures or provider padding. Keep totals as separate evidence.
    report = {"expected_rows": len(completed_candidates),
              "candidate_source_rows_total": len(candidates),
              "skipped_unplayed_source_rows": len(unplayed_candidates),
              "skipped_empty_source_rows": len(empty_candidates),
              "sources": 0, "linked": 0,
              "errors": [], "league_season_counts": {}}
    out = []
    coverage = Counter()
    quarantined = []
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
                    status, reason = inspect(row)
                    if status in ("UNPLAYED", "EMPTY"):
                        required = "UNPLAYED_SOURCE_ROW" if status == "UNPLAYED" else "EMPTY_SOURCE_ROW"
                        if candidate["status"] != required:
                            raise ValueError(f"Source result changed since fixture audit at {number}")
                        continue
                    home, away, date = ((row.get(k) or "").strip() for k in ("HomeTeam", "AwayTeam", "Date"))
                    if (home, away, date) != (candidate["home"], candidate["away"], candidate["date"]):
                        raise ValueError(f"Source row changed at {number}; refuse stale join")
                    if candidate["status"] != "CANDIDATE_ONLY":
                        raise ValueError(f"Noncandidate source row {number}: {candidate['status']}")
                    if status != "COMPLETE":
                        raise ValueError(f"Source row {number} no longer complete: {status} {reason}")
                    home_id, away_id = registry.resolve_team(home), registry.resolve_team(away)
                    key = (league, season, home_id, away_id, parse_date(date))
                    fid = fixture_index.get(key)
                    if not fid:
                        raise ValueError(f"Unlinked fixture row {number}: {key}")
                    stats = read_stats(row, league, season, coverage, quarantined, number)
                    out.append({"fixture_id": fid, "league": league, "season": season,
                                "match_date": key[-1], "home_id": home_id, "away_id": away_id,
                                "home_goals": int(row["FTHG"]), "away_goals": int(row["FTAG"]),
                                "result": row["FTR"], "source_row": number, "source_url": url, **stats})
            except Exception as exc:
                report["errors"].append(f"{season}/{league}: {exc}")
    report["linked"] = len(out)
    report["quarantined_stat_groups"] = quarantined
    report["quarantined_stat_group_count"] = len(quarantined)
    report["quarantine_policy"] = "Only affected home/away shots pair blanked; valid goals, corners, and cards retained"
    report["stat_group_complete_rows_by_league_season"] = dict(sorted(coverage.items()))
    report["not_included"] = ["xG","xGA","first_half_corners","odds","lineups"]
    report["league_season_counts"] = dict(Counter(f'{r["league"]}/{r["season"]}' for r in out))
    report["distinct_fixture_ids"] = len({r["fixture_id"] for r in out})
    report["chronology_rule"] = "Order by match_date; same-date matches have no assumed kickoff order"
    report["future_leakage_rule"] = "For predictions, use only prior dates, never same-day or later matches"
    report["accepted"] = (not report["errors"] and report["sources"] == 20 and
                          len(out) == len(completed_candidates) == len(registry.data["fixtures"]) and
                          report["distinct_fixture_ids"] == len(out) and
                          len(candidates) == (len(completed_candidates)
                                              + len(unplayed_candidates) + len(empty_candidates)))
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
