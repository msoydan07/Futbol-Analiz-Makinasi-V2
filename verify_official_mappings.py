"""Verify every reviewed official mapping against observed team names and registry."""
import csv
from pathlib import Path
from identity import Registry

ROOT = Path("data")
def read(name):
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def main():
    candidates = {r["source_name"] for r in read("team_identity_review.csv")}
    mappings = read("official_team_names.csv")
    registry = Registry(ROOT / "team_registry.json")
    seen = set()
    failures = []
    verified = 0
    for row in mappings:
        name = row["source_name"]
        if name in seen or name not in candidates:
            failures.append(f"duplicate or unknown source name: {name}")
        seen.add(name)
        if row["review_status"] != "VERIFIED":
            continue
        verified += 1
        try:
            tid = registry.resolve_team(name)
            team = registry.data["teams"][tid]
            if (team["name"] != row["official_name"]
                or team.get("verification") != "FEDERATION_VERIFIED"
                or team.get("official_name_evidence_url") != row["evidence_url"]):
                failures.append(f"unapplied official mapping: {name}")
        except KeyError:
            failures.append(f"unresolved team: {name}")
    print(f"Reviewed official names: {verified}; pending: {len(candidates) - verified}; total observed: {len(candidates)}")
    if failures:
        raise SystemExit("\n".join(failures))
    print("PASS: all VERIFIED mappings applied without identity mismatch")
    if verified < len(candidates):
        print("STAGE 1 INCOMPLETE: remaining teams still need official-name evidence")

if __name__ == "__main__":
    main()
