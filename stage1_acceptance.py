"""Single acceptance gate for stage 1: factual identity coverage, not green-only checks."""
import csv
import json
from pathlib import Path

BASE = Path("data")


def read_csv(name):
    with (BASE / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    sources = read_csv("source_audit.csv")
    candidates = read_csv("team_candidates.csv")
    review = read_csv("team_identity_review.csv")
    memberships = read_csv("team_memberships.csv")
    registry = json.loads((BASE / "team_registry_provisional.json").read_text(encoding="utf-8"))
    source_keys = {(r["league"], r["season"]) for r in sources}
    expected = {(league, season) for league in
                ("ENG1", "ENG2", "GER1", "ESP1", "ITA1", "FRA1", "NED1", "TUR1", "POR1", "BEL1")
                for season in ("2025-2026", "2026-2027")}
    if source_keys != expected or any(r["status"] != "OK" for r in sources):
        raise AssertionError("Incomplete source coverage")
    names = {r["source_name"] for r in candidates}
    if len(review) != len(names) or len(registry["teams"]) != len(names):
        raise AssertionError("Team name/registry mismatch")
    candidate_rows = {(r["source_name"], r["season"], r["league"]) for r in candidates}
    member_rows = {(r["source_name"], r["season"], r["league"]) for r in memberships}
    if len(member_rows) != len(memberships) or member_rows != candidate_rows:
        raise AssertionError("Membership mismatch or duplicate")
    if any(r["team_id"] not in registry["teams"] for r in memberships):
        raise AssertionError("Orphan membership")
    pending = [r for r in review if r["review_status"] != "VERIFIED"]
    fixture_count = len(registry["fixtures"])
    print(f"Source coverage: {len(sources)}/20; teams: {len(names)}; memberships: {len(memberships)}")
    print(f"Unverified team identities: {len(pending)}; registered fixtures: {fixture_count}")
    if pending or not fixture_count:
        print("STAGE 1 NOT ACCEPTED: verified club identities and source-backed fixtures required")
        return 2
    print("Stage 1 acceptance conditions met")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
