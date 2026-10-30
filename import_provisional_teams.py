"""Import exact observed team names into a PROVISIONAL identity registry.

No cross-source alias is guessed. Every entry remains unverified until reviewed.
"""
import csv
from pathlib import Path
from identity import Registry

INPUT = Path("data/team_identity_review.csv")
OUTPUT = Path("data/team_registry_provisional.json")
MEMBERSHIP = Path("data/team_memberships.csv")


def main():
    registry = Registry(OUTPUT)
    memberships = []
    with INPUT.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("No candidate teams")
    for row in rows:
        if row["review_status"] == "KEY_COLLISION":
            raise ValueError("Key collision; manual resolution required")
        if row["review_status"] != "PENDING_VERIFICATION":
            raise ValueError("Unexpected review status")
        name, key = row["source_name"], row["suggested_key"]
        team_id = registry.register_team(key, name)
        registry.data["teams"][team_id]["verification"] = "PROVISIONAL_SOURCE_NAME_ONLY"
    with Path("data/team_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            memberships.append({
                "team_id": registry.resolve_team(row["source_name"]),
                "source_name": row["source_name"],
                "season": row["season"],
                "league": row["league"],
                "verification": "SOURCE_OBSERVED_NOT_OFFICIALLY_VERIFIED",
            })
    registry.save()
    with MEMBERSHIP.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["team_id", "source_name", "season", "league", "verification"])
        writer.writeheader()
        writer.writerows(memberships)
    assert len(registry.data["teams"]) == len(rows)
    assert len(memberships) > 0
    assert all(row["team_id"] in registry.data["teams"] for row in memberships)
    print(f"Provisional teams: {len(rows)}, observed memberships: {len(memberships)}")
    print("NOT approved canonical club identities; verification remains pending.")


if __name__ == "__main__":
    main()
