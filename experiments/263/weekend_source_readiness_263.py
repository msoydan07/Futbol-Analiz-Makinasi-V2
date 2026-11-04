"""Read-only 6-8 Nov source readiness. No fixture discovery or model fitting.

This checks source integrity and per-league pre-KO cutoff, never claims all score
sources independently verified. A real game still needs a fresh official gate.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import defaultdict
from datetime import date,datetime,timezone,timedelta
from pathlib import Path

from full_match_eligibility_263 import full_match_rows

def read_aware(value):
    t=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if t.tzinfo is None:
        raise ValueError("ACCEPTANCE_TIME_MUST_HAVE_UTC_OFFSET")
    return t.astimezone(timezone.utc)

SOURCE_SHA="1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9"
BASE_SHA="35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1"
LEAGUES=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
DATES=("2026-11-06","2026-11-07","2026-11-08")
SCHEMA="263_4518_t60_weekend_10_league_source_readiness_v1"

def analyze(history_path,acceptance_path,*,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError("NAIVE_AUDIT_TIME")
    now=now.astimezone(timezone.utc)
    content=Path(history_path).read_bytes()
    actual_sha=hashlib.sha256(content).hexdigest()
    if actual_sha!=SOURCE_SHA:raise ValueError("ACCEPTED_HISTORY_SHA_CHANGED")
    acceptance=json.loads(Path(acceptance_path).read_text(encoding="utf-8"))
    if (acceptance.get("schema")!="263_owner_accepted_research_source_v1"
        or acceptance.get("status")!="HUMAN_VERIFIED_SOURCE_ACCEPTANCE"
        or acceptance.get("snapshot_sha256")!=SOURCE_SHA
        or acceptance.get("baseline_sha256")!=BASE_SHA
        or acceptance.get("all_4518_independently_verified") is not False
        or acceptance.get("research_only") is not True
        or not acceptance.get("reviewer")):
        raise ValueError("HUMAN_RESEARCH_ACCEPTANCE_PROOF_MISMATCH")
    reviewed=read_aware(acceptance["reviewed_at_utc"])
    if reviewed>now or now-reviewed>timedelta(days=7):
        raise ValueError("SOURCE_ACCEPTANCE_EXPIRED_FOR_CURRENT_READINESS")
    rows=list(csv.DictReader(content.decode("utf-8-sig").splitlines()))
    if len(rows)!=4518:raise ValueError("UNEXPECTED_ACCEPTED_MATCH_COUNT")
    ids=set();by=defaultdict(list)
    for r in rows:
        ident=r["fixture_id"]
        if not ident or ident in ids:raise ValueError("DUPLICATE_OR_MISSING_MATCH_ID")
        ids.add(ident)
        if r["league"] not in LEAGUES:raise ValueError("LEAGUE_OUT_OF_SCOPE")
        if r["season"] not in ("2025-2026","2026-2027"):
            raise ValueError("INVALID_SEASON")
        when=date.fromisoformat(r["match_date"])
        if when>now.date():raise ValueError("FUTURE_RESULT_IN_SOURCE")
        if not r["home_id"] or not r["away_id"] or r["home_id"]==r["away_id"]:
            raise ValueError("BAD_TEAM_IDENTITIES")
        home,away=int(r["home_goals"]),int(r["away_goals"])
        if min(home,away)<0 or r["result"]!=("H" if home>away else "A" if home<away else "D"):
            raise ValueError("RESULT_MISMATCH")
        if not r["source_url"].startswith("https://"):
            raise ValueError("SOURCE_URL_MISSING")
        by[r["league"]].append(r)
    if set(by)!=set(LEAGUES):raise ValueError("MISSING_ONE_OF_TEN_LEAGUES")
    results={}
    for league in LEAGUES:
        all_league=by[league]
        eligible,excluded,eligibility_sha=full_match_rows(all_league)
        last=max(x["match_date"] for x in eligible)
        previous=sum(x["season"]=="2025-2026" for x in eligible)
        current=sum(x["season"]=="2026-2027" for x in eligible)
        missing_ext=sum(not x["source_row"] or not x["home_corners"] for x in all_league)
        windows={}
        for d in DATES:
            match_day=date.fromisoformat(d)
            days=(match_day-date.fromisoformat(last)).days
            windows[d]={"age_days":days,
                "mechanical_ready":len(eligible)>=120 and 0<days<=10,
                "later_results_may_require_refresh":True}
        results[league]={"rows_in_source":len(all_league),
            "full_match_training_rows":len(eligible),
            "previous_season_rows":previous,"current_season_rows":current,
            "last_result_date":last,"excluded_shortened_match_ids":excluded,
            "source_rows_with_missing_extended_fields":missing_ext,
            "match_completion_policy_sha256":eligibility_sha,
            "target_dates":windows}
    is_ready=all(window["mechanical_ready"] for r in results.values()
                 for window in r["target_dates"].values())
    result={"schema":SCHEMA,
        "status":"MACHINE_CUTOFF_READY_NOT_LIVE_MATCH_VERIFIED" if is_ready else "MACHINE_SOURCE_NOT_READY",
        "audited_at_utc":now.isoformat(),"source_sha256":actual_sha,
        "human_source_acceptance_reviewed_at_utc":reviewed.isoformat(),
        "source_count":len(rows),"league_count":len(by),
        "research_only":True,"all_rows_independently_verified":False,
        "actual_official_fixtures_verified":0,
        "first_11_checked":False,"odds_source_verified":False,
        "no_roi_or_betting_authorized":True,
        "last_result_date_may_need_new_refresh_at_real_T_minus_60":True,
        "ready_all":is_ready,"leagues":results}
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--history",default="data/quad_accepted_263/extended_history.csv")
    p.add_argument("--acceptance",default="data/quad_accepted_263/source_acceptance.json")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    result=analyze(a.history,a.acceptance)
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as f:
        json.dump(result,f,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)
        f.write("\n")
    print(json.dumps({"status":result["status"],"ready_all":result["ready_all"],
        "leagues":result["league_count"],"rows":result["source_count"]}))
    if not result["ready_all"]:raise SystemExit("SOME_LEAGUES_OUTSIDE_TEMPORAL_READINESS")
if __name__=="__main__":main()
