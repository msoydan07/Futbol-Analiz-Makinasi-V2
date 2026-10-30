"""Apply reviewed federation/league names without guessing source-name aliases.

CSV columns: source_name,official_name,federation,evidence_url,review_status
Only VERIFIED rows are promoted; other source names remain provisional.
"""
import csv
from pathlib import Path
from identity import Registry

BASE = Path("data")
INPUT = BASE / "official_team_names.csv"
REGISTRY = BASE / "team_registry_provisional.json"
OUTPUT = BASE / "team_registry.json"
REPORT = BASE / "official_name_audit.csv"

def main():
    registry = Registry(REGISTRY)
    results = []
    if INPUT.exists():
        with INPUT.open(encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                source_name = row["source_name"].strip()
                status = row["review_status"].strip()
                try:
                    team_id = registry.resolve_team(source_name)
                    if status != "VERIFIED":
                        results.append((source_name, "PENDING", "Not reviewed"))
                        continue
                    registry.set_official_team_name(
                        team_id, row["official_name"], row["federation"], row["evidence_url"]
                    )
                    results.append((source_name, "VERIFIED", ""))
                except (KeyError, ValueError) as exc:
                    results.append((source_name, "REJECTED", str(exc)))
    else:
        print("No official mapping CSV: all identities remain provisional")
    registry.path = OUTPUT
    registry.save()
    with REPORT.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["source_name", "status", "reason"])
        writer.writerows(results)
    counts = {"VERIFIED": 0, "PROVISIONAL": 0}
    for team in registry.data["teams"].values():
        counts["VERIFIED" if team.get("verification") == "FEDERATION_VERIFIED" else "PROVISIONAL"] += 1
    print("Official identity audit:", counts)
    if any(r[1] == "REJECTED" for r in results):
        raise SystemExit("Rejected mappings require review")

if __name__ == "__main__":
    main()
