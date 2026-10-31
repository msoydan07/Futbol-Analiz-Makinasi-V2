"""Build auditable identity candidates from observed source team names.

This does NOT approve aliases or modify the permanent identity registry.
"""
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

INPUT = Path("data/team_candidates.csv")
OUTPUT = Path("data/team_identity_review.csv")


def slug(name):
    s = unicodedata.normalize("NFKD", name.casefold())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def build():
    observed = defaultdict(lambda: {"leagues": set(), "seasons": set()})
    with INPUT.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = row["source_name"].strip()
            if not name:
                raise ValueError("Empty source team name")
            observed[name]["leagues"].add(row["league"])
            observed[name]["seasons"].add(row["season"])
    proposed = defaultdict(list)
    for name in observed:
        proposed[slug(name)].append(name)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        fields = ["source_name", "suggested_key", "leagues", "seasons", "review_status"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for name in sorted(observed, key=str.casefold):
            key = slug(name)
            writer.writerow({
                "source_name": name,
                "suggested_key": key,
                "leagues": ";".join(sorted(observed[name]["leagues"])),
                "seasons": ";".join(sorted(observed[name]["seasons"])),
                "review_status": "KEY_COLLISION" if len(proposed[key]) > 1 else "PENDING_VERIFICATION",
            })
    collisions = {key: names for key, names in proposed.items() if len(names) > 1}
    print(f"Observed distinct source names: {len(observed)}; suggested key collisions: {len(collisions)}")
    if collisions:
        print(f"Collisions requiring review: {collisions}")


if __name__ == "__main__":
    build()
