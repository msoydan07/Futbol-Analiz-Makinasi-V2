"""Compare observed league membership across two seasons without guessing promotions.

Run after collect_team_candidates.py. An entrant/exit is NOT proof of promotion
or relegation: lower leagues outside the ten-league scope are not observed.
"""
import csv
from collections import defaultdict
from pathlib import Path

SOURCE = Path("data/team_candidates.csv")
OUTPUT = Path("data/season_membership_audit.csv")
SEASONS = ("2025-2026", "2026-2027")


def main():
    membership = defaultdict(set)
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            membership[(row["source_name"].strip(), row["season"])].add(row["league"])
    names = sorted({name for name, _ in membership}, key=str.casefold)
    results = []
    for name in names:
        before = membership.get((name, SEASONS[0]), set())
        after = membership.get((name, SEASONS[1]), set())
        if before and after:
            status = "CHANGED_LEAGUE" if before != after else "SAME_LEAGUE"
        else:
            status = "ENTERED_SCOPE" if after else "LEFT_SCOPE"
        results.append({
            "source_name": name, "league_2025_26": ";".join(sorted(before)),
            "league_2026_27": ";".join(sorted(after)),
            "status": status,
            "verification": "SOURCE_OBSERVED_NOT_OFFICIALLY_VERIFIED",
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    from collections import Counter
    print("Membership audit:", dict(Counter(r["status"] for r in results)))


if __name__ == "__main__":
    main()
