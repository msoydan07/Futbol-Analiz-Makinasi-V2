"""Read-only morning 10-league score-gap status, no predictions or source mutation.

The output is NOT an official calendar or bookmaker source; a LIVE verified
named fixture is still required before any normal 2.6.3 prediction.
"""
import json
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from exp_263_batch import clean_rows
from freshness_gap_guard_263 import review_gap,StaleLeagueData
from season_refresh_263 import LEAGUES

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"data/results_only_263/2026-11-10_completed_4617_scores_only.csv"

def check():
    if not SOURCE.is_file():raise ValueError("PINNED_4617_HISTORY_NOT_AVAILABLE")
    import hashlib
    actual=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if actual!="637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89":
        raise ValueError("LOCKED_4617_SHA_CHANGED")
    rows=clean_rows(SOURCE)
    if len(rows)!=4617:raise ValueError("4617_COUNT_CHANGED")
    now=datetime.now(timezone.utc)
    day=now.astimezone(ZoneInfo("Europe/Istanbul")).date().isoformat()
    output={"schema":"263_TEN_LEAGUE_FRESHNESS_READONLY_AUDIT_V1",
            "day_turkey":day,"checked_at_utc":now.isoformat(),
            "snapshot_sha256":actual,"source":"PUBLIC_FOOTBALL_DATA_NOT_OFFICIAL_FEDERATION",
            "forecasts_generated":0,"seals_modified":False,"odds_queried":False,
            "model_modified":False,"xg_used":False,"leagues":{}}
    for lg in sorted(LEAGUES):
        current=[r for r in rows if r["league"]==lg and r["season"]=="2026-2027"]
        latest=max(r["match_date"] for r in current)
        age=(datetime.fromisoformat(day).date()-datetime.fromisoformat(latest).date()).days
        try:
            d=review_gap(rows,lg,day,now=now)
            state="PUBLIC_PROVIDER_BOUNDED_GAP_ALLOWED_RESEARCH" if age>10 else "WITHIN_DEFAULT_LIMIT"
            output["leagues"][lg]={"state":state,"last_completed":latest,"age_days":age,
                "evidence":d}
        except (ValueError,OSError,TypeError,KeyError) as exc:
            output["leagues"][lg]={"state":"BLOCKED_NO_FORECAST",
                "last_completed":latest,"age_days":age,
                "reason":str(exc)[:150]}
    output["allowed_count"]=sum(x["state"]!="BLOCKED_NO_FORECAST" for x in output["leagues"].values())
    output["blocked_count"]=len(LEAGUES)-output["allowed_count"]
    return output

if __name__=="__main__":
    print("READONLY_TEN_LEAGUE_GAP_STATUS="+json.dumps(check(),sort_keys=True))
