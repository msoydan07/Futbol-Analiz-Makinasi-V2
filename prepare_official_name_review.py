"""Create a reviewable official-name mapping worksheet from observed source names.

Preserves any previously reviewed mappings. Never guesses an official name.
"""
import csv
from pathlib import Path

BASE = Path("data")
CANDIDATES = BASE / "team_identity_review.csv"
MAPPINGS = BASE / "official_team_names.csv"
FIELDS = ["source_name", "official_name", "federation", "evidence_url", "review_status"]

def main():
    previous = {}
    if MAPPINGS.exists():
        with MAPPINGS.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                previous[row["source_name"]] = {key: row.get(key, "") for key in FIELDS}
    with CANDIDATES.open(encoding="utf-8-sig", newline="") as stream:
        names = sorted({row["source_name"] for row in csv.DictReader(stream)})
    records = [previous.get(name, {"source_name": name, "official_name": "",
                                   "federation": "", "evidence_url": "",
                                   "review_status": "PENDING"}) for name in names]
    with MAPPINGS.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(f"Official-name review rows: {len(records)}; already reviewed: "
          f"{sum(row['review_status'] == 'VERIFIED' for row in records)}")

if __name__ == "__main__":
    main()
