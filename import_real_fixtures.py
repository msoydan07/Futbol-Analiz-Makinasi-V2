"""Register real Football-Data league fixtures against persistent team IDs.

Date is metadata; league+season+home+away is the stable domestic league identity.
Only valid, nonambiguous observed rows are imported.
"""
import csv
import datetime as dt
import json
from collections import Counter, defaultdict
from pathlib import Path
from identity import Registry

ROOT = Path("data")
def parse_date(value):
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError("Unsupported match date: " + value)

def main():
    registry = Registry(ROOT / "team_registry.json")
    with (ROOT / "fixture_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    with (ROOT / "fixture_source_audit.csv").open(encoding="utf-8-sig", newline="") as f:
        source_audit = list(csv.DictReader(f))
    if len(source_audit) != 20 or any(r["status"] != "OK" for r in source_audit):
        raise SystemExit("Incomplete fixture source coverage")
    keys = Counter((r["season"], r["league"], r["home"], r["away"])
                   for r in rows if r["status"] == "CANDIDATE_ONLY")
    errors, imported, skipped_empty = [], 0, 0
    error_types = Counter()
    error_samples = defaultdict(list)
    def record_error(reason, detail):
        errors.append(detail)
        error_types[reason] += 1
        if len(error_samples[reason]) < 8:
            error_samples[reason].append(detail)
    for row in rows:
        if row["status"] == "EMPTY_SOURCE_ROW":
            skipped_empty += 1
            continue
        if row["status"] != "CANDIDATE_ONLY":
            record_error(row["status"], f"Invalid candidate {row['season']}/{row['league']} row {row['source_row']}: {row['status']}")
            continue
        key = row["season"], row["league"], row["home"], row["away"]
        if keys[key] > 1:
            record_error("REPEATED_HOME_AWAY", "Repeated home/away league fixture: " + repr(key))
            continue
        try:
            home = registry.resolve_team(row["home"])
            away = registry.resolve_team(row["away"])
            date = parse_date(row["date"])
            registry.register_dated_fixture(row["league"], row["season"], home, away, date)
            imported += 1
        except (ValueError, KeyError) as exc:
            record_error(type(exc).__name__, repr(key) + ": " + str(exc))
    summary = {"source_count": len(source_audit), "candidate_rows": len(rows),
               "imported": imported, "registered": len(registry.data["fixtures"]),
               "skipped_empty_source_rows": skipped_empty,
               "errors": errors[:100], "error_count": len(errors),
               "error_types": dict(error_types), "error_samples": dict(error_samples)}
    (ROOT / "fixture_import_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k != "errors"}, indent=2))
    if errors:
        raise SystemExit("Fixture import rejected; inspect fixture_import_report.json")
    if imported + skipped_empty + len(errors) != len(rows):
        raise SystemExit("Unaccounted source rows")
    if imported == 0 or len(registry.data["fixtures"]) != imported:
        raise SystemExit("Fixture identity count mismatch")
    registry.path = ROOT / "match_registry.json"
    registry.save()
    print("PASS: all observed fixtures linked to verified source team names and stable match IDs")

if __name__ == "__main__":
    main()
