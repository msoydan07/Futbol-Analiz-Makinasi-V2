"""CC0 OpenFootball research-only historical ingest with fail-closed QA.

Run: python research/model_challenge/ingest_openfootball.py --out /tmp/football-research
Network access required. Does NOT change existing 2.6.3/pilot files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import urllib.error
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

PIN = "e6744429ee395bc86f247348c6184bb08d4eb361"
BASE = f"https://raw.githubusercontent.com/openfootball/football.json/{PIN}"
# Only verifiable real 2025/26 filename codes; at.2 substitutes for absent en.5.
LEAGUES = {
    "ENG1": "en.1", "ENG2": "en.2", "ENG3": "en.3", "ENG4": "en.4",
    "GER1": "de.1", "GER2": "de.2",
    "ESP1": "es.1", "ESP2": "es.2",
    "ITA1": "it.1", "ITA2": "it.2",
    "FRA1": "fr.1", "FRA2": "fr.2",
    "NED1": "nl.1", "TUR1": "tr.1", "POR1": "pt.1", "BEL1": "be.1",
    "SCO1": "sco.1", "GRE1": "gr.1", "AUT1": "at.1", "AUT2": "at.2",
}
SEASONS = ("2022-23", "2023-24", "2024-25", "2025-26")
FIELDS = ("league", "season", "date", "home", "away", "home_goals",
          "away_goals", "source_file", "source_sha256")


class Reject(Exception):
    pass


def normalize_one(doc, league, season, src, digest, *, cutoff):
    if not isinstance(doc, dict) or not isinstance(doc.get("matches"), list):
        raise Reject("bad document / matches schema")
    seen = {}
    records = []
    missing_results = 0
    for index, item in enumerate(doc["matches"]):
        if not isinstance(item, dict):
            raise Reject(f"nonobject match {index}")
        raw_date = item.get("date")
        try:
            d = date.fromisoformat(raw_date)
        except (ValueError, TypeError):
            raise Reject(f"invalid match date {index}")
        if d > cutoff:
            continue
        home, away = item.get("team1"), item.get("team2")
        if (not isinstance(home, str) or not isinstance(away, str)
                or not home.strip() or not away.strip() or home == away):
            raise Reject(f"invalid teams {index}")
        score = item.get("score", {}).get("ft") if isinstance(item.get("score"), dict) else None
        if score is None:
            missing_results += 1
            continue
        if (not isinstance(score, list) or len(score) != 2 or
                any(type(v) is not int or v < 0 or v > 30 for v in score)):
            raise Reject(f"invalid full-time score {index}")
        key = (d.isoformat(), home.casefold().strip(), away.casefold().strip())
        if key in seen:
            if seen[key] != tuple(score):
                raise Reject(f"conflicting duplicate score {index}")
            raise Reject(f"duplicate match {index}")
        seen[key] = tuple(score)
        records.append(dict(zip(FIELDS, (league, season, d.isoformat(), home.strip(),
                                         away.strip(), score[0], score[1], src, digest))))
    return records, missing_results


def get_json(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "research-model-challenge/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as f:
            raw = f.read(15_000_000)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None, None
        raise
    if len(raw) >= 15_000_000:
        raise Reject("source too large")
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def ingest(*, out, seasons=SEASONS, cutoff=date(2026, 11, 9), fetch=get_json):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    normalized = []
    coverage = []
    for season in seasons:
        if not re.fullmatch(r"20\d\d-\d\d", season):
            raise Reject("invalid season")
        for league, code in LEAGUES.items():
            src = f"{season}/{code}.json"
            obj, sha = fetch(f"{BASE}/{src}")
            if obj is None:
                coverage.append({"league": league, "season": season,
                                 "status": "SOURCE_MISSING", "rows": 0})
                continue
            try:
                rows, missing = normalize_one(obj, league, season, src, sha, cutoff=cutoff)
                coverage.append({"league": league, "season": season,
                                 "status": "ACCEPTED", "rows": len(rows),
                                 "unplayed_or_missing_results": missing, "source_sha256": sha})
                normalized.extend(rows)
            except Reject as exc:
                coverage.append({"league": league, "season": season,
                                 "status": "REJECTED_QA", "rows": 0,
                                 "reason": str(exc), "source_sha256": sha})
    keyset = set()
    for row in normalized:
        key = (row["league"], row["date"], row["home"], row["away"])
        if key in keyset:
            raise Reject(f"cross-season duplicate: {key}")
        keyset.add(key)
    normalized.sort(key=lambda r: (r["date"], r["league"], r["home"], r["away"]))
    csvfile = out / "normalized_matches.csv"
    with csvfile.open("w", newline="", encoding="utf-8") as fd:
        writer = csv.DictWriter(fd, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(normalized)
    report = {
        "schema": "MC_SOURCE_COVERAGE_V1", "source": "openfootball/football.json",
        "license": "CC0-1.0", "git_commit": PIN, "as_of": cutoff.isoformat(),
        "matches": len(normalized), "league_count": len(set(x["league"] for x in normalized)),
        "coverage": coverage, "normalized_sha256": hashlib.sha256(csvfile.read_bytes()).hexdigest(),
        "excluded_future_matches": True, "historical_odds_available": False,
        "timestamped_xg_available": False,
    }
    (out / "coverage.json").write_text(json.dumps(report, ensure_ascii=False,
                                                  indent=2) + "\n", encoding="utf-8")
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--cutoff", default="2026-11-09")
    args = p.parse_args()
    result = ingest(out=args.out, cutoff=date.fromisoformat(args.cutoff))
    print(json.dumps({k: result[k] for k in ("matches", "league_count",
                                            "normalized_sha256")}, indent=2))


if __name__ == "__main__":
    main()
