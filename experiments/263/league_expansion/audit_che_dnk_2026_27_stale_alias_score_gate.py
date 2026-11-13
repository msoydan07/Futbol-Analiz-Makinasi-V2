#!/usr/bin/env python3
"""Read-only 2026/27 CHE1 & DNK1 full-time source quality/freshness audit.

Never imports a full external CSV into GitHub, model training, main, or SHA seals.
Exact historical 2025/26 CSV QA is separate and must not be repeated.
The known 2026/27 public CSV is a restored, possibly stale snapshot and has
source-specific rights limitations. Duplicate fixtures and aliases are not new games.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
import csv, hashlib, io, json, re
from pathlib import Path
from urllib.request import Request, urlopen
from verify_public_season_csv_2526 import norm, name_map, csv_rows

ROOT = Path("experiments/263/league_expansion")
BASELINE_54_PATH = ROOT / "cc0_new_485_2526_2627_QUARANTINE_20261113.csv"
CUTOFF = date(2026,11,13)
START = date(2026,7,1)

LEAGUES = {
  "CHE1": {
    "slug":"swiss-super-league", "real_clubs":12, "independent_scored_count":78,
    "independent_goals":293,
    "score_reference":"https://uniquescores.com/football/league/swiss-super-league/results/",
    "extra_aliases":{"Vaduz":["FC Vaduz"],"Thun":["FC Thun","Thun"],
                     "St Gallen":["FC St.Gallen 1879","FC St. Gallen 1879","St. Gallen"],
                     "Lugano":["FC Lugano"],"Sion":["FC Sion"]},
    "clubs":["Thun","St Gallen","Lugano","Sion","Basel","Young Boys",
             "Luzern","Servette","Lausanne","Zurich","Grasshoppers","Vaduz"],
    "recent":[
      ("2026-11-07","Vaduz","Sion",0,4),
      ("2026-11-07","Luzern","Young Boys",2,3),
      ("2026-11-07","Grasshoppers","Lausanne",1,1),
      ("2026-11-08","St Gallen","Lugano",5,0),
      ("2026-11-08","Servette","Zurich",0,0),
      ("2026-11-08","Thun","Basel",3,3)
    ]
  },
  "DNK1": {
    "slug":"danish-superliga", "real_clubs":12, "independent_scored_count":84,
    "independent_goals":257,
    "score_reference":"https://uniquescores.com/football/league/danish-superliga/results/",
    "extra_aliases":{
      "Lyngby":["Lyngby BK","Lyngby Boldklub"],
      "Horsens":["AC Horsens","Horsens"],
      "Copenhagen":["FCK","FC Kobenhavn","FC København"],
      "Odense":["OB","Odense BK"],
      "Nordsjaelland":["Nordsjælland","FC Nordsjælland"],
      "Sonderjyske":["Sønderjyske","SønderjyskE","Sønderjyske Fodbold"],
      "Brondby":["Brøndby IF"],
      "Viborg":["Viborg FF"]
    },
    "clubs":["AGF","Midtjylland","Nordsjaelland","Brondby","Viborg",
             "Sonderjyske","Copenhagen","Odense","Silkeborg","Randers",
             "Lyngby","Horsens"],
    "recent":[
      ("2026-11-06","Silkeborg","Lyngby",1,0),
      ("2026-11-07","Odense","Viborg",1,2),
      ("2026-11-08","Copenhagen","Brondby",1,0),
      ("2026-11-08","AGF","Horsens",2,0),
      ("2026-11-08","Randers","Nordsjaelland",1,6),
      ("2026-11-08","Midtjylland","Sonderjyske",2,2)
    ]
  }
}


def canonical_lookup(league):
    cfg=LEAGUES[league]
    lookup=name_map(league)
    for canonical,names in cfg["extra_aliases"].items():
        for label in [canonical,*names]:
            key=norm(label)
            if lookup.get(key) not in (None,canonical):
                raise ValueError("ALIASES_NOT_DISJOINT:"+label)
            lookup[key]=canonical
    return lookup


def assess(league, rows, baseline54=None):
    cfg=LEAGUES[league]
    lookup=canonical_lookup(league)
    valid=set(cfg["clubs"])
    report=Counter()
    raw_names=defaultdict(set)
    seen={}
    duplicate_keys=defaultdict(list)
    conflict_keys=[]
    rejected=[]
    dates=[]
    for row in rows:
        report["source_rows"]+=1
        st=str(row.get("status") or "").strip().casefold()
        if st not in {"finished","completed","ft","full-time","full time"}:
            report["not_confirmed_finished"]+=1
            continue
        report["source_finished_labels"]+=1
        daystr=str(row.get("date") or "")[:10]
        try: day=date.fromisoformat(daystr)
        except ValueError: day=None
        if day is None or not START<=day<=CUTOFF:
            report["out_of_window_or_invalid_date"]+=1
            rejected.append({"reason":"OUT_OF_WINDOW","date":daystr})
            continue
        rh=str(row.get("home") or "").strip()
        ra=str(row.get("away") or "").strip()
        h=lookup.get(norm(rh))
        a=lookup.get(norm(ra))
        if h not in valid or a not in valid or h==a:
            report["invalid_club_or_same_team"]+=1
            rejected.append({"reason":"INVALID_CLUB","date":daystr,"home":rh,"away":ra})
            continue
        sh=str(row.get("home_goals") or "").strip()
        sa=str(row.get("away_goals") or "").strip()
        if not re.fullmatch(r"\d{1,2}",sh) or not re.fullmatch(r"\d{1,2}",sa):
            report["invalid_or_missing_ft_score"]+=1
            rejected.append({"reason":"NO_FT","date":daystr,"home":h,"away":a})
            continue
        hg=int(sh);ag=int(sa)
        if hg>30 or ag>30:
            report["impossible_goal_count"]+=1
            continue
        key=(daystr,h,a)
        raw_names[h].add(rh);raw_names[a].add(ra)
        if key in seen:
            duplicate_keys[key].append((hg,ag))
            if seen[key] != (hg,ag):
                conflict_keys.append(key)
                report["duplicate_with_conflicting_ft_score"]+=1
            else:
                report["exact_canonical_fixture_duplicate"]+=1
            continue
        seen[key]=(hg,ag)
        dates.append(daystr)
    report["canonical_unique_fixtures"]=len(seen)
    report["canonical_total_goals"]=sum(h+a for h,a in seen.values())
    report["canonical_0_0"]=sum(h==0 and a==0 for h,a in seen.values())
    report["source_rows_with_canonical_aliases"]=sum(len(v)>1 for v in raw_names.values())
    distinct=set(x for k in seen for x in k[1:])
    recent={}
    for day,h,a,hg,ag in cfg["recent"]:
        got=seen.get((day,h,a))
        recent[f"{day}|{h}|{a}"]={
            "present":got is not None,"same_score":got==(hg,ag),
            "expected":[hg,ag],"observed":list(got) if got is not None else None
        }
    recent_matches=sum(v["same_score"] for v in recent.values())
    if baseline54 is not None and league=="CHE1":
        base_keys={}
        for row in baseline54:
            if row.get("league")!="CHE1" or row.get("season")!="2026-27":continue
            h=lookup.get(norm(row["home"]));a=lookup.get(norm(row["away"]))
            key=(row["date"],h,a)
            if h and a:
                base_keys[key]=(int(row["ft_home"]),int(row["ft_away"]))
        matched=[k for k,sc in base_keys.items() if seen.get(k)==sc]
        wrong=[k for k,sc in base_keys.items() if k in seen and seen[k]!=sc]
        missing=[k for k in base_keys if k not in seen]
        baseline={
            "existing_cc0_2026_27_che1_rows":len(base_keys),
            "same_fixture_and_score":len(matched),
            "score_conflicts":len(wrong),
            "fixture_missing_in_2026_csv":len(missing),
            "last_cc0_scored_date":max((k[0] for k in base_keys),default=None),
            "conflict_examples":[{"date":k[0],"home":k[1],"away":k[2],
                "cc0":list(base_keys[k]),"other":list(seen[k])} for k in wrong[:8]],
            "missing_examples":[{"date":k[0],"home":k[1],"away":k[2]} for k in missing[:8]]
        }
    else: baseline=None
    complete=(len(seen)==cfg["independent_scored_count"]
              and report["canonical_total_goals"]==cfg["independent_goals"]
              and len(distinct)==cfg["real_clubs"]
              and recent_matches==len(cfg["recent"])
              and report["invalid_club_or_same_team"]==0
              and report["out_of_window_or_invalid_date"]==0
              and report["duplicate_with_conflicting_ft_score"]==0)
    return {
      "league":league,"season":"2026-27","cutoff_inclusive":CUTOFF.isoformat(),
      "current_source":"MatchDaySync publicly downloadable snapshot (11 October restored, updates disconnected)",
      "source_finished_label_count":report["source_finished_labels"],
      "canonical_scored_match_count":len(seen),
      "expected_completed_from_other_sources":cfg["independent_scored_count"],
      "canonical_goal_count":report["canonical_total_goals"],
      "expected_goals_from_other_sources":cfg["independent_goals"],
      "first_last_scored_date":[min(dates),max(dates)] if dates else [],
      "distinct_canonical_clubs":len(distinct),
      "expected_clubs":cfg["real_clubs"],
      "duplicate_same_score":report["exact_canonical_fixture_duplicate"],
      "duplicate_different_score":report["duplicate_with_conflicting_ft_score"],
      "not_confirmed_finished":report["not_confirmed_finished"],
      "invalid_teams":report["invalid_club_or_same_team"],
      "finished_but_invalid_date":report["out_of_window_or_invalid_date"],
      "invalid_ft":report["invalid_or_missing_ft_score"],
      "source_score_0_0":report["canonical_0_0"],
      "alias_variants":{k:sorted(v) for k,v in sorted(raw_names.items()) if len(v)>1},
      "duplicate_examples":[{"date":k[0],"home":k[1],"away":k[2],"raw_extra":len(v)} for k,v in list(duplicate_keys.items())[:12]],
      "conflict_examples":[{"date":k[0],"home":k[1],"away":k[2]} for k in conflict_keys[:8]],
      "rejected_examples":rejected[:12],
      "independent_recent_round_witness_count":len(cfg["recent"]),
      "independent_recent_round_present_score_equal":recent_matches,
      "independent_recent_round_witnesses":recent,
      "cc0_prior_54_comparison":baseline,
      "completeness_and_score_gate":"PASS_SOURCE_CANDIDATE_NOT_TRAINING" if complete else "FAIL_CLOSED_STALE_OR_INCOMPLETE_SOURCE",
      "rights_to_republish_or_train":"NOT_ESTABLISHED",
      "new_quarantine_rows_added":0,"new_training_rows_approved":0,
      "existing_main_m4_and_SHA_untouched":True,
      "note":"If source is stale or duplicates/conflicts exist, no automatic transfer. Even full score checksum is not license approval."
    }


def self_test():
    lookup=canonical_lookup("CHE1")
    assert lookup[norm("FC Vaduz")]=="Vaduz"
    assert lookup[norm("FC St. Gallen 1879")]=="St Gallen"
    assert canonical_lookup("DNK1")[norm("Lyngby Boldklub")]=="Lyngby"
    assert canonical_lookup("DNK1")[norm("AC Horsens")]=="Horsens"
    base=[
        {"date":"2026-11-08","home":"Servette","away":"Zurich","status":"finished","home_goals":"0","away_goals":"0"},
        {"date":"2026-11-08","home":"Servette FC","away":"FC Zürich","status":"finished","home_goals":"0","away_goals":"0"},
        {"date":"2026-11-21","home":"Vaduz","away":"Sion","status":"finished","home_goals":"8","away_goals":"1"},
        {"date":"2026-11-07","home":"Luzern","away":"Young Boys","status":"scheduled","home_goals":"2","away_goals":"3"}
    ]
    result=assess("CHE1",base)
    assert result["canonical_scored_match_count"]==1,result
    assert result["duplicate_same_score"]==1,result
    assert result["finished_but_invalid_date"]==1,result
    assert result["source_score_0_0"]==1,result
    assert result["independent_recent_round_present_score_equal"]==1,result
    assert result["new_training_rows_approved"]==0,result
    print("SELFTEST_PASS 2026/27 alias, Vaduz/Lyngby/Horsens, duplicate, real 0-0, future FT rejected")


def fetch_source(league):
    slug=LEAGUES[league]["slug"]
    url=f"https://matchdaysync.com/api/public/csv/{slug}/2026-27/matches"
    req=Request(url,headers={"User-Agent":"Research-Only-Once-NewSeason-Audit/1.0","Accept":"text/csv"})
    with urlopen(req,timeout=20) as response:
        if "csv" not in response.headers.get("Content-Type","").lower():
            raise ValueError("NOT_CSV")
        raw=response.read(2_000_001)
        if len(raw)>2_000_000: raise ValueError("CSV_SIZE_OVER_LIMIT")
    return raw,url


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--live",action="store_true")
    a=parser.parse_args()
    if a.self_test:self_test()
    if a.live:
        baseline=list(csv.DictReader(BASELINE_54_PATH.open(encoding="utf-8")))
        outputs=[]
        for league in LEAGUES:
            row={"league":league,"status":"NOT_STARTED"}
            try:
                raw,url=fetch_source(league)
                if not raw.decode("utf-8-sig").startswith("# Source:"):
                    raise ValueError("MISSING_CSV_SOURCE_HEADER")
                rows=csv_rows(raw.decode("utf-8-sig"))
                row=assess(league,rows,baseline)
                row["source_sha256"]=hashlib.sha256(raw).hexdigest()
                row["source_url"]=url
                row["status"]="SOURCE_AUDIT_COMPLETE"
            except Exception as exc:
                row={"league":league,"status":"SOURCE_UNAVAILABLE_OR_PARSE_ERROR",
                     "error_class":type(exc).__name__,"new_training_rows_approved":0}
            outputs.append(row)
        doc={"run_utc":datetime.now(timezone.utc).isoformat(),
             "scope":"NEW_SEASON_2026_27_CHE_DNK_ONE_PASS_AUDIT",
             "independent_score_witness_sources":[LEAGUES[k]["score_reference"] for k in LEAGUES],
             "source_csv_rows_rehosted":0,
             "public_quarantine_rows_added":0,
             "model_changes":0,"no_raw_dataset_artifacts":True,
             "leagues":outputs}
        print("NEW_SEASON_QA_START")
        print(json.dumps(doc,indent=2,ensure_ascii=False))
        print("NEW_SEASON_QA_END")
