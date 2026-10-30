"""Audit official-name collisions and source coverage without altering stable IDs."""
import csv
import json
from collections import defaultdict
from pathlib import Path
from identity import normalize

ROOT = Path("data")
def main():
    with (ROOT / "official_team_names.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    with (ROOT / "team_identity_review.csv").open(encoding="utf-8-sig", newline="") as f:
        observed = {r["source_name"] for r in csv.DictReader(f)}
    grouped = defaultdict(list)
    problems = []
    seen = set()
    for row in rows:
        name = row["source_name"]
        if name in seen:
            problems.append("DUPLICATE_SOURCE_NAME: " + name)
        seen.add(name)
        if name not in observed:
            problems.append("UNKNOWN_SOURCE_NAME: " + name)
        if row["review_status"] == "VERIFIED":
            grouped[normalize(row["official_name"])].append(name)
            if not row["official_name"].strip() or not row["evidence_url"].startswith("https://"):
                problems.append("MISSING_EVIDENCE: " + name)
    for official, aliases in grouped.items():
        if len(aliases) > 1:
            problems.append("POSSIBLE_SAME_CLUB_DIFFERENT_IDS: " + official + " -> " + ", ".join(aliases))
    missing = sorted(observed - seen)
    problems += ["MISSING_SOURCE_NAME: " + n for n in missing]
    result = {"observed": len(observed), "mapped": len(seen),
              "verified_flags": sum(r["review_status"] == "VERIFIED" for r in rows),
              "pending": [r["source_name"] for r in rows if r["review_status"] != "VERIFIED"],
              "problems": problems}
    (ROOT / "identity_integrity_report.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if problems:
        raise SystemExit("Identity integrity problems require review")

if __name__ == "__main__":
    main()
