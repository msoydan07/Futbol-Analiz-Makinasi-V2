"""Read-only Understat xG match audit. No predictions or historical files are modified.

Usage:
  python audit_understat_xg.py --understat-csv data/understat_matches.csv

Input CSV headers: league,season,match_date,home_team,away_team,home_goals,
away_goals,home_xg,away_xg,source_url.
Optional reviewed aliases JSON: {"ENG1":{"Manchester United":"Man United"}}.
The Understat source CSV must be obtained lawfully and independently.
"""
import argparse
import csv
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

LEAGUES = {"ENG1", "GER1", "ESP1", "ITA1", "FRA1"}
FIELDS = {"league","season","match_date","home_team","away_team","home_goals",
          "away_goals","home_xg","away_xg","source_url"}

def norm(value):
    value = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    return re.sub(r"\\s+", " ", value)

def day(value):
    return date.fromisoformat(value[:10]).isoformat()

def score(value):
    number = int(value)
    if number < 0 or str(number) != str(value).strip():
        raise ValueError("invalid score")
    return number

def xg(value):
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError("invalid xG")
    return number

def read(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def run(args):
    base = read(args.historical)
    source = read(args.understat_csv)
    candidates = read(args.candidates)
    if not source or not FIELDS.issubset(source[0]):
        raise ValueError("Understat input missing required fields")
    if not base or not {"fixture_id","league","season","match_date","home_goals","away_goals","source_row"}.issubset(base[0]):
        raise ValueError("Historical results missing required fields")
    if not candidates or not {"league","season","source_row","home","away"}.issubset(candidates[0]):
        raise ValueError("Fixture candidates missing required fields")
    aliases = json.loads(Path(args.aliases).read_text(encoding="utf-8")) if args.aliases else {}
    overrides = json.loads(Path(args.reviewed_dates).read_text(encoding="utf-8")) if args.reviewed_dates else []
    override_by_url = {v["source_url"]: v for v in overrides}
    if len(override_by_url) != len(overrides):
        raise ValueError("Duplicate reviewed date override source URL")
    historical_by_id = {r["fixture_id"]: r for r in base}
    if len(historical_by_id) != len(base):
        raise ValueError("Duplicate historical fixture IDs")
    used_overrides = set()
    observed_override_urls = set()
    already_exact_overrides = set()
    names = {(r["league"],r["season"],r["source_row"]):r for r in candidates}
    index = defaultdict(list)
    for r in base:
        if r["league"] not in LEAGUES:
            continue
        name = names.get((r["league"],r["season"],r["source_row"]))
        if name is None:
            raise ValueError("Missing candidate name for fixture "+r["fixture_id"])
        key = (r["league"],r["season"],day(r["match_date"]),
               norm(name["home"]),norm(name["away"]))
        index[key].append(r)
    seen = set()
    results = []
    counts = Counter()
    for row_no,r in enumerate(source,start=2):
        status = "INVALID"
        fid = ""
        reason = ""
        try:
            league = r["league"].strip()
            season = r["season"].strip()
            if league not in LEAGUES:
                raise ValueError("unsupported league")
            if season not in {"2025-2026","2026-2027"}:
                raise ValueError("unsupported season")
            alias = aliases.get(league,{})
            home = alias.get(r["home_team"].strip(),r["home_team"].strip())
            away = alias.get(r["away_team"].strip(),r["away_team"].strip())
            key = (league,season,day(r["match_date"]),norm(home),norm(away))
            h,a = score(r["home_goals"]),score(r["away_goals"])
            hx,ax = xg(r["home_xg"]),xg(r["away_xg"])
            matches = index.get(key,[])
            url = r.get("source_url", "")
            if url in override_by_url:
                observed_override_urls.add(url)
                if len(matches) == 1 and (h,a) == (int(matches[0]["home_goals"]),int(matches[0]["away_goals"])):
                    v = override_by_url[url]
                    if (v["league"],v["season"],v["home_team"],v["away_team"],int(v["home_goals"]),int(v["away_goals"])) == (league,season,r["home_team"],r["away_team"],h,a):
                        already_exact_overrides.add(url)
            if not matches and url in override_by_url:
                v = override_by_url[url]
                target = historical_by_id.get(v["fixture_id"])
                if target is None:
                    raise ValueError("Reviewed override fixture not found")
                # A previously reviewed fixture ID may be stale after registry regeneration.
                # Never trust it blindly: recover only a unique fixture with the reviewed
                # league, season, verified date, reviewed teams and exact final score.
                target_name_probe = names.get((target["league"],target["season"],target["source_row"]))
                expected_names = (norm(home),norm(away))
                actual_names = (norm(target_name_probe["home"]),norm(target_name_probe["away"])) if target_name_probe else None
                if actual_names != expected_names:
                    possible = []
                    for candidate in base:
                        if candidate["league"] != league or candidate["season"] != season or day(candidate["match_date"]) != v["verified_date"]:
                            continue
                        candidate_names = names.get((candidate["league"],candidate["season"],candidate["source_row"]))
                        if candidate_names and (norm(candidate_names["home"]),norm(candidate_names["away"])) == expected_names and (int(candidate["home_goals"]),int(candidate["away_goals"])) == (h,a):
                            possible.append(candidate)
                    if len(possible) != 1:
                        raise ValueError("Reviewed fixture identity stale; exact date/team/score candidate count=" + str(len(possible)))
                    target = possible[0]
                target_name = names.get((target["league"],target["season"],target["source_row"]))
                if not target_name:
                    raise ValueError("Reviewed override candidate name missing")
                checks = (
                    v["league"] == league and v["season"] == season,
                    v["source_date"] == day(r["match_date"]),
                    v.get("source_url") == r.get("source_url"),
                    v["verified_date"] == day(target["match_date"]),
                    v["home_team"] == r["home_team"] and v["away_team"] == r["away_team"],
                    int(v["home_goals"]) == h and int(v["away_goals"]) == a,
                    target["league"] == league and target["season"] == season,
                    norm(target_name["home"]) == norm(home) and norm(target_name["away"]) == norm(away),
                    int(target["home_goals"]) == h and int(target["away_goals"]) == a,
                    bool(v.get("evidence_url","").startswith("https://")),
                )
                if not all(checks):
                    labels = ("league_season","source_date","source_url","verified_date","source_teams","source_score","target_league_season","target_teams","target_score","evidence_url")
                    failing = [label for label,ok in zip(labels,checks) if not ok]
                    detail = {"failed":failing,"expected_target": {"home":home,"away":away},"actual_target":{"home":target_name["home"],"away":target_name["away"]},"target_fixture_id":target["fixture_id"]}
                    raise ValueError("Reviewed override mismatch: " + json.dumps(detail,ensure_ascii=False))
                matches = [target]
                used_overrides.add(url)
            if len(matches) == 0:
                status,reason = "UNMATCHED","No exact reviewed team/date match"
            elif len(matches) != 1:
                status,reason = "AMBIGUOUS","Multiple historical matches"
            else:
                match = matches[0]
                fid = match["fixture_id"]
                if fid in seen:
                    status,reason = "DUPLICATE","Multiple Understat rows for fixture"
                elif (h,a) != (int(match["home_goals"]),int(match["away_goals"])):
                    status,reason = "SCORE_MISMATCH","Full-time score disagrees"
                else:
                    status,reason = "MATCHED","Exact teams, date and score"
                    seen.add(fid)
        except (ValueError,TypeError,KeyError) as exc:
            reason = str(exc)
        counts[(r.get("league",""),r.get("season",""),status)] += 1
        results.append({"source_row":row_no,"league":r.get("league",""),
                        "season":r.get("season",""),"home_team":r.get("home_team",""),
                        "away_team":r.get("away_team",""),"fixture_id":fid,
                        "status":status,"reason":reason,
                        "source_url":r.get("source_url","")})
    # Always preserve row-level matching diagnostics, even when an override check fails.
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    with Path(args.output).open("w",encoding="utf-8",newline="") as handle:
        writer = csv.DictWriter(handle,fieldnames=list(results[0]) if results else
            ["source_row","league","season","home_team","away_team","fixture_id","status","reason","source_url"])
        writer.writeheader()
        writer.writerows(results)
    stale_overrides = sorted(set(override_by_url) - observed_override_urls)
    if stale_overrides:
        raise ValueError("Reviewed source URLs no longer present: " + ", ".join(stale_overrides))
    not_applied = sorted(observed_override_urls - used_overrides - already_exact_overrides)
    if not_applied:
        diagnostics = [r for r in results if r["source_url"] in not_applied]
        raise ValueError("Reviewed date overrides unresolved: " + json.dumps(diagnostics,ensure_ascii=False))
    expected = Counter((r["league"],r["season"]) for r in base if r["league"] in LEAGUES)
    matched = Counter((r["league"],r["season"]) for r in base if r["fixture_id"] in seen)
    summary = {"read_only":True,"source_rows":len(source),"historical_eligible":sum(expected.values()),
               "matched_unique":len(seen),"reviewed_date_overrides_applied":len(used_overrides),"reviewed_overrides_already_exact":len(already_exact_overrides),"coverage_by_league_season":[
                   {"league":league,"season":season,"historical":total,
                    "matched":matched[(league,season)]}
                   for (league,season),total in sorted(expected.items())],
               "status_counts":[{"league":league,"season":season,"status":status,"count":total}
                                for (league,season,status),total in sorted(counts.items())],
               "policy":"No fuzzy matches, no score conflicts, no auto-added xG, no future leakage"}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    with Path(args.output).open("w",encoding="utf-8",newline="") as handle:
        writer = csv.DictWriter(handle,fieldnames=list(results[0]) if results else
            ["source_row","league","season","home_team","away_team","fixture_id","status","reason","source_url"])
        writer.writeheader()
        writer.writerows(results)
    Path(args.report).write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,ensure_ascii=False))
    return 0

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--understat-csv",required=True)
    p.add_argument("--historical",default="data/historical_results.csv")
    p.add_argument("--candidates",default="data/fixture_candidates.csv")
    p.add_argument("--aliases",default="")
    p.add_argument("--reviewed-dates",default="")
    p.add_argument("--output",default="data/understat_xg_match_audit.csv")
    p.add_argument("--report",default="data/understat_xg_match_report.json")
    raise SystemExit(run(p.parse_args()))
