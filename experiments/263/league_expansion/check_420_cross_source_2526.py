#!/usr/bin/env python3
"""One-shot independent 2025/26 score comparison, research ONLY.

CSV: MatchDaySync source; comparison: FBref match schedule, separately retrieved.
Both sources are held in memory, never rehosted as raw rows or training data.
GitHub Actions stores aggregate audit and at most 12 mismatched fixture identities.
"""
import hashlib
from html.parser import HTMLParser
import json
import re
from urllib.request import Request, urlopen

from verify_public_season_csv_2526 import csv_rows, name_map, norm

LEAGUES = {
    "CHE1": {
        "csv": "https://matchdaysync.com/api/public/csv/swiss-super-league/2025-26/matches",
        "reference": "https://fbref.com/en/comps/57/2025-2026/schedule/2025-2026-Swiss-Super-League-Scores-and-Fixtures",
        "pinned_sha256": "46a8b9aedb6bf294a6991e701609c04d511eb844bd02a24094349ce4be51678c",
        "expected_matches": 228,
        "aliases": {"Grasshopper": "Grasshoppers","Lausanne-Sport": "Lausanne",
                    "FC Winterthur": "Winterthur","Grasshopper Club": "Grasshoppers"},
    },
    "DNK1": {
        "csv": "https://matchdaysync.com/api/public/csv/danish-superliga/2025-26/matches",
        "reference": "https://fbref.com/en/comps/50/2025-2026/schedule/2025-2026-Danish-Superliga-Scores-and-Fixtures",
        "pinned_sha256": "8b5e31555919beb083b875b8d38bc2227350ffc950a39308bbd803cefa64d6fa",
        "expected_matches": 192,
        "aliases": {"SønderjyskE": "Sonderjyske", "Vejle BK": "Vejle",
                    "Nordsjælland": "Nordsjaelland",
                    "FC Copenhagen": "Copenhagen", "Odense": "Odense"},
    },
}


class FBrefScheduleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_row = False
        self.row = None
        self.field = None
        self.field_text = []
        self.completed = []

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if tag == "tr":
            self.in_row = True
            self.row = {}
        elif self.in_row and tag in ("td", "th"):
            self.field = props.get("data-stat")
            self.field_text = []

    def handle_data(self, value):
        if self.in_row and self.field:
            self.field_text.append(value)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.in_row:
            if self.field:
                self.row[self.field] = "".join(self.field_text).strip()
            self.field = None
            self.field_text = []
        elif tag == "tr" and self.in_row:
            if self.row:
                self.completed.append(self.row)
            self.row = None
            self.in_row = False

    def handle_comment(self, content):
        if "data-stat=" in content and "<tr" in content:
            nested = FBrefScheduleParser()
            nested.feed(content)
            self.completed.extend(nested.completed)


def scrape_reference(html_source):
    parser = FBrefScheduleParser()
    parser.feed(html_source)
    outputs = []
    for row in parser.completed:
        date = row.get("date", "")
        home = row.get("home_team", "")
        away = row.get("away_team", "")
        ft = row.get("score", "")
        m = re.fullmatch(r"\s*(\d{1,2})\s*[–—-]\s*(\d{1,2})(?:\s*\(.*\))?\s*", ft)
        if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", date):
            continue
        if not home or not away or not m:
            continue
        outputs.append({"date": date, "home": home, "away": away,
                        "hg": int(m.group(1)), "ag": int(m.group(2))})
    return outputs


def canonicalize(league, raw):
    table = name_map(league)
    for label, name in LEAGUES[league]["aliases"].items():
        table[norm(label)] = name
    return table.get(norm(raw))


def convert(league, source_rows, *, csv=False):
    records, skipped, collisions = {}, [], []
    for row in source_rows:
        status = (row.get("status") or "").lower().strip() if csv else "finished"
        if csv and status not in ("finished", "completed", "ft", "full-time", "full time"):
            skipped.append("not_finished")
            continue
        day = (row.get("date") or "")[:10]
        home = canonicalize(league, row.get("home") or "")
        away = canonicalize(league, row.get("away") or "")
        if home is None or away is None:
            skipped.append("unknown_team")
            continue
        h = row.get("home_goals") if csv else row.get("hg")
        a = row.get("away_goals") if csv else row.get("ag")
        if str(h) not in tuple(map(str, range(31))) or str(a) not in tuple(map(str, range(31))):
            skipped.append("invalid_score")
            continue
        key = (day, home, away)
        score = (int(h), int(a))
        if key in records:
            collisions.append(key)
            continue
        records[key] = score
    return records, skipped, collisions


def match_audit(league, csv_source, reference_source):
    csv_rows_converted, csv_skipped, csv_dup = convert(league, csv_source, csv=True)
    ref_rows, ref_skipped, ref_dup = convert(league, reference_source, csv=False)
    common = set(csv_rows_converted) & set(ref_rows)
    matched = [k for k in common if csv_rows_converted[k] == ref_rows[k]]
    mismatched = [k for k in common if csv_rows_converted[k] != ref_rows[k]]
    missing = set(csv_rows_converted) - set(ref_rows)
    extra = set(ref_rows) - set(csv_rows_converted)
    all_match = (
        len(csv_rows_converted) == LEAGUES[league]["expected_matches"]
        and len(ref_rows) == LEAGUES[league]["expected_matches"]
        and len(common) == len(csv_rows_converted)
        and not mismatched and not csv_dup and not ref_dup
        and not csv_skipped and not ref_skipped
    )
    return {
        "csv_unique": len(csv_rows_converted),
        "independent_unique": len(ref_rows),
        "same_day_team_fixture_keys": len(common),
        "same_score": len(matched),
        "different_score": len(mismatched),
        "unmatched_csv": len(missing),
        "extra_reference": len(extra),
        "csv_duplicate_count": len(csv_dup),
        "reference_duplicate_count": len(ref_dup),
        "csv_skipped_count": len(csv_skipped),
        "reference_skipped_count": len(ref_skipped),
        "conflict_examples": [
            {"date": k[0], "home": k[1], "away": k[2],
             "csv_score": list(csv_rows_converted[k]),"reference_score": list(ref_rows[k])}
            for k in sorted(mismatched)[:12]
        ],
        "unmatched_csv_examples": [
            {"date": k[0], "home": k[1], "away": k[2]} for k in sorted(missing)[:12]
        ],
        "independent_comparison_status": "FULL_MATCH" if all_match else "PARTIAL_OR_CONFLICT__NOT_APPROVED",
        "training_approved": 0,
    }


def download(url, accept, *, limit=3000000):
    req = Request(url, headers={"User-Agent":"Mozilla/5.0 (compatible; ResearchSourceVerification/1.0)",
                                "Accept":accept, "Accept-Language":"en-US,en;q=0.8"})
    with urlopen(req,timeout=18) as response:
        data = response.read(limit+1)
        if len(data)>limit: raise ValueError("BODY_TOO_LARGE")
    return data


def live_audit(league):
    cfg = LEAGUES[league]
    entry = {"league":league,"season":"2025-26",
             "reference_url":cfg["reference"],
             "previously_pinned_csv_sha256":cfg["pinned_sha256"],
             "state":"INDEPENDENT_SOURCE_NOT_VERIFIED"}
    try:
        raw = download(cfg["csv"],"text/csv")
        hashval = hashlib.sha256(raw).hexdigest()
        entry["csv_sha256_seen"] = hashval
        if hashval != cfg["pinned_sha256"]:
            entry["state"] = "CSV_HASH_CHANGED__STOP_NO_COMPARISON"
            return entry
        source = csv_rows(raw.decode("utf-8-sig"))
        if len(source) != cfg["expected_matches"]:
            entry["state"] = "CSV_COUNT_CHANGED__STOP_NO_COMPARISON"
            return entry
        independent_raw = download(cfg["reference"], "text/html")
        independent = scrape_reference(independent_raw.decode("utf-8",errors="replace"))
        entry.update(match_audit(league,source,independent))
        entry["state"] = "MATCH_LEVEL_CHECK_COMPLETE" if entry["independent_comparison_status"] == "FULL_MATCH" else "MATCH_LEVEL_PARTIAL_OR_CONFLICT"
    except Exception as e:
        entry["state"] = "INDEPENDENT_CHECK_BLOCKED"
        entry["error_type"] = type(e).__name__
        entry["error_detail_class_only"] = "external_access_or_parser_failure"
    return entry


def self_test():
    html = '<table><tbody><tr><th data-stat="date">2025-07-25</th><td data-stat="home_team">Zürich</td><td data-stat="score">2–3</td><td data-stat="away_team">Sion</td></tr></tbody></table>'
    r = scrape_reference(html)
    assert len(r)==1 and r[0]["hg"]==2
    src = [{"date":"2025-07-25","home":"Zurich","away":"Sion","home_goals":"2","away_goals":"3","status":"finished"}]
    comp = match_audit("CHE1",src,r)
    assert comp["same_score"]==1 and comp["different_score"]==0
    r2 = [{"date":"2025-07-25","home":"Zürich","away":"Sion","hg":2,"ag":1}]
    comp2 = match_audit("CHE1",src,r2)
    assert comp2["different_score"]==1 and comp2["same_score"]==0
    assert comp["independent_comparison_status"]!="FULL_MATCH"  # not 228 matches
    print("PASS synthetic: HTML row parser, canonical aliases, exact score and conflicting score")


if __name__ == "__main__":
    import argparse
    opts = argparse.ArgumentParser()
    opts.add_argument("--self-test",action="store_true")
    opts.add_argument("--live",action="store_true")
    a = opts.parse_args()
    if a.self_test: self_test()
    if a.live:
        report = {
            "purpose": "READ_ONLY_INDEPENDENT_MATCH_LEVEL_COMPARISON",
            "raw_match_rows_in_report": False,
            "added_to_quarantine": 0,
            "trainable_rows_admitted": 0,
            "main_m4_touched": False,
            "sources": [live_audit(league) for league in ("CHE1","DNK1")]
        }
        print("CROSS_SOURCE_REPORT_START")
        print(json.dumps(report,ensure_ascii=False,indent=2))
        print("CROSS_SOURCE_REPORT_END")
