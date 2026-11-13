#!/usr/bin/env python3
"""One-shot Swiss Super League 2025/26 independent FT audit.

Matches MatchDaySync pinned 228-match CSV to original RSSSF 2025/26 score text.
No raw copied datasets, user data, score archives, training, or model changes.
No inference from aggregate-only consistency; date/club/result must all match.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
import hashlib
from html.parser import HTMLParser
import html
import json
import re
import sys
from urllib.request import Request, urlopen

from verify_public_season_csv_2526 import csv_rows, norm, name_map

PRIMARY = "https://matchdaysync.com/api/public/csv/swiss-super-league/2025-26/matches"
INDEPENDENT = "https://www.rsssf.org/tablesz/zwit2026.html"
EXPECTED_SHA = "46a8b9aedb6bf294a6991e701609c04d511eb844bd02a24094349ce4be51678c"
WITNESSES = "experiments/263/league_expansion/che_dnk_2526_51_independent_match_score_witnesses_20261114.json"

MONTHS = {"jan": 1, "janv": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
          "apr": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
          "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12}
DATE_LINE = re.compile(r"^\s*\[\s*([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(202[56]))?(?:\s+[^]]+)?\]\s*$")
RESULT_LINE = re.compile(r"^\s*([^\d\[\]\n][^\d\n]*?)\s+(\d{1,2})-(\d{1,2})\s+(.+?)\s*$")
ALIASES = {"FC Lausanne": "Lausanne", "Grasshopper Club": "Grasshoppers",
           "FC St.Gallen": "St Gallen", "FC St. Gallen": "St Gallen",
           "FC Zuerich": "Zurich", "FC Zürich": "Zurich",
           "FC Basel": "Basel", "BSC Young Boys": "Young Boys"}

class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in ("br", "p", "pre", "h1", "h2", "h3", "h4", "div"):
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        elif tag in ("p", "pre", "h1", "h2", "h3", "h4", "div"):
            self.parts.append("\n")
    def handle_data(self, data):
        if not self.skip: self.parts.append(data)


def decode_html(source: bytes) -> str:
    for enc in ("utf-8", "windows-1252", "latin-1"):
        try:
            return source.decode(enc)
        except UnicodeDecodeError:
            continue
    return source.decode("latin-1")


def to_lines(source: str) -> list[str]:
    parser = TextOnly()
    parser.feed(source)
    return html.unescape("".join(parser.parts)).splitlines()


def canonical(raw: str, lookup: dict[str, str]) -> str | None:
    raw = re.sub(r"\s+\[[^]]+\]\s*$", "", raw).strip()
    return lookup.get(norm(raw))


def rsssf_results(text: str) -> tuple[dict, dict]:
    lookup = name_map("CHE1")
    lookup.update({norm(k):v for k,v in ALIASES.items()})
    lines = to_lines(text)
    start = next((i for i,x in enumerate(lines) if re.fullmatch(r"\s*Round 1\s*",x)), None)
    if start is None: raise ValueError("MISSING_RSSSF_ROUND_1")
    # Swiss Super League: 33 pre-split matchdays; 5 after-split matchdays
    # in Championship + Relegation sections. Stop BEFORE relegation promotion barrage.
    end = next((i for i in range(start,len(lines))
                if "Promotion/Relegation Playoff" in lines[i]), None)
    if end is None: raise ValueError("MISSING_PROMOTION_RELEGATION_STOP")
    match_lines = lines[start:end]
    found, unknown, repeats, no_date = {}, Counter(), [], 0
    current_day = None
    for line in match_lines:
        m = DATE_LINE.match(line)
        if m:
            month = MONTHS.get(m.group(1).lower())
            day = int(m.group(2))
            year = int(m.group(3)) if m.group(3) else (2025 if month and month>=7 else 2026)
            try: current_day = date(year,month,day).isoformat()
            except (TypeError,ValueError): current_day = None
            continue
        m = RESULT_LINE.match(line)
        if not m: continue
        home = canonical(m.group(1),lookup)
        away = canonical(m.group(4),lookup)
        # Ignore standings, scorer notes, match commentary, etc.;
        # record unknown football team-like score lines for manual review.
        if home is None or away is None:
            if home is not None or away is not None:
                unknown["ONE_TEAM_NOT_MAPPED"] += 1
            continue
        if home == away:
            unknown["SAME_TEAM"] += 1
            continue
        if not current_day:
            no_date += 1
            continue
        key = (current_day,home,away)
        if key in found:
            repeats.append(key)
            continue
        found[key] = (int(m.group(2)),int(m.group(3)))
    return found, {"parsed_scored_games":len(found),
                   "not_mapped_football_lines":dict(unknown),
                   "duplicate_keys":len(repeats), "score_without_valid_day":no_date,
                   "selection_start":"first Round 1", "selection_end":"Promotion/Relegation Playoff"}


def primary_results(rows: list[dict]) -> tuple[dict, int]:
    lookup = name_map("CHE1")
    records,duplicates = {},0
    for row in rows:
        if row.get("status","").strip().lower()!="finished":
            continue
        home = canonical(row.get("home",""),lookup)
        away = canonical(row.get("away",""),lookup)
        if home is None or away is None: raise ValueError("PRIMARY_UNMAPPED_CLUB")
        d = row.get("date","")[:10]
        key = (d,home,away)
        if key in records: duplicates+=1
        if not re.fullmatch(r"20\d\d-\d\d-\d\d",d): raise ValueError("PRIMARY_BAD_DATE")
        goals = (int(row["home_goals"]),int(row["away_goals"]))
        records[key] = goals
    return records,duplicates


def audit(csv_raw: bytes, rsssf_raw: bytes, existing_witnesses: list[dict]) -> dict:
    file_sha = hashlib.sha256(csv_raw).hexdigest()
    if file_sha != EXPECTED_SHA:
        return {"status":"STOP_SOURCE_HASH_CHANGED", "observed_csv_sha256":file_sha,
                "new_independent_score_checks":0, "trainable_rows":0}
    primary,dups = primary_results(csv_rows(csv_raw.decode("utf-8-sig")))
    independent, parser = rsssf_results(decode_html(rsssf_raw))
    common=set(primary)&set(independent)
    same={key for key in common if primary[key]==independent[key]}
    different=sorted(common-same)
    missing=sorted(set(primary)-set(independent))
    extra=sorted(set(independent)-set(primary))
    already={(w["date"],w["home"],w["away"]) for w in existing_witnesses if w["league"]=="CHE1"}
    previously_checked = len(already & same)
    newly_verified=len(same-already)
    full=(len(primary)==228 and len(independent)==228 and len(same)==228 and not dups
          and not parser["duplicate_keys"] and not missing and not extra
          and not parser["not_mapped_football_lines"] and parser["score_without_valid_day"]==0)
    return {
        "league":"CHE1","season":"2025-26",
        "reference":INDEPENDENT, "reference_type":"RSSSF independently published score/result rounds 1-33 and 5 split rounds",
        "csv_sha256":file_sha, "source_scored_rows":len(primary),"source_duplicate_keys":dups,
        "independent_scored_rows":len(independent), "rsssf_parser":parser,
        "date_club_score_joint_keys":len(common),
        "matched_date_club_score":len(same),"score_disagreements":len(different),
        "unmatched_csv_fixtures":len(missing),"unmatched_rsssf_fixtures":len(extra),
        "prior_36_witnesses_in_score_match":previously_checked,
        "new_unique_score_checks_beyond_36":newly_verified,
        "different_examples":[{"date":k[0],"home":k[1],"away":k[2],"csv_goals":primary[k],"rsssf_goals":independent[k]} for k in different[:12]],
        "csv_missing_examples":[{"date":k[0],"home":k[1],"away":k[2]} for k in missing[:12]],
        "rsssf_extra_examples":[{"date":k[0],"home":k[1],"away":k[2]} for k in extra[:12]],
        "independent_full_228_match_score_gate":"PASS" if full else "FAIL_CLOSED",
        "training_approved":0, "rehosted_source_data":False,
        "note":"Result-match comparison is factual QA; license for full source CSV reuse and all other training gates remain unapproved."
    }


def self_test():
    sample = """
    Super League
    Round 1
    [July 25]
    FC Zürich              2-3 FC Sion
    [July 26]
    FC St. Gallen          2-1 FC Basel
    Round 33
    [April 18]
    FC Basel                1-3 FC Thun [played in Thun]
    Playoff Stage
    Championship Playoff
    [May 14]
    FC Thun                 3-8 BSC Young Boys
    Relegation Playoff
    [May 17]
    Grasshopper Club        3-2 FC Winterthur
    Promotion/Relegation Playoff
    [May 18]
    FC Aarau                0-0 Grasshopper Club
    """
    parsed,detail=rsssf_results("<pre>"+sample+"</pre>")
    assert len(parsed)==5, (parsed,detail)
    assert parsed[("2025-07-25","Zurich","Sion")]==(2,3)
    assert parsed[("2026-05-14","Thun","Young Boys")]==(3,8)
    assert ("2026-05-18","Aarau","Grasshoppers") not in parsed
    assert detail["duplicate_keys"]==0
    print("PASS Swiss RSSSF parser: day/year/club mapping, 33+split, exclude external barrage")


if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--self-test",action="store_true")
    a.add_argument("--live",action="store_true")
    args=a.parse_args()
    if args.self_test: self_test()
    if args.live:
        def get(url,accept):
            request=Request(url,headers={"User-Agent":"Research-Independent-FT-QA/1.0 (one-time, read-only)","Accept":accept})
            with urlopen(request,timeout=20) as resp:
                raw=resp.read(3000001)
                if len(raw)>3000000: raise ValueError("REMOTE_FILE_TOO_BIG")
                return raw
        with open(WITNESSES,"r",encoding="utf-8") as f:
            old=json.load(f)["checks"]
        report={"status":"INDEPENDENT_CHECK_ATTEMPTED","league":"CHE1","season":"2025-26",
                "raw_datasets_archived":False,"training_approved":0,"main_m4_modified":False}
        try:
            csv_bytes=get(PRIMARY,"text/csv")
            independent_html=get(INDEPENDENT,"text/html")
            report.update(audit(csv_bytes,independent_html,old))
        except Exception as exc:
            report["status"]="SOURCE_UNAVAILABLE_OR_PARSER_EXCEPTION"
            report["exception_class"]=type(exc).__name__
            report["trainable_rows"]=0
        print("SWISS_FULL_COMPARE_START")
        print(json.dumps(report,ensure_ascii=False,indent=2))
        print("SWISS_FULL_COMPARE_END")
