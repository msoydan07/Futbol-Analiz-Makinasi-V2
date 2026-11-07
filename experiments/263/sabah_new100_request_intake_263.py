"""Strict Git-push intake for user-named new100; independent no-op probe."""
from __future__ import annotations
import argparse,json,re
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from sabah_manual_window_263 import in_manual_window
from sabah_batch_263 import named,Blocked

TR=ZoneInfo("Europe/Istanbul")
SCHEMA="263_NEW100_PUSH_INTAKE_V1"
REAL=r"experiments/263/sabah_requests/[A-Za-z0-9_-]+\.json"
PROBE=r"experiments/263/sabah_readiness_probes/[A-Za-z0-9_-]+\.json"
class IntakeBlocked(ValueError):pass

def inspect(path,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise IntakeBlocked("AWARE_CLOCK_REQUIRED")
    now=now.astimezone(TR)
    if not in_manual_window(now):raise IntakeBlocked("TURKEY_MORNING_WINDOW_CLOSED")
    if not isinstance(path,str) or not (re.fullmatch(REAL,path) or re.fullmatch(PROBE,path)):
        raise IntakeBlocked("ONLY_NEW_ADD_NAMED_OR_PROBE_PATH")
    input_path=Path(path)
    if input_path.is_symlink() or not input_path.is_file():
        raise IntakeBlocked("REQUEST_NOT_COMMITTED_OR_SYMLINK")
    data=json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(data,dict):
        raise IntakeBlocked("REQUEST_SCHEMA_INVALID")
    day=now.date().isoformat()
    if data.get("day_turkey")!=day:
        raise IntakeBlocked("NOT_TODAY_NO_BACKDATED_REQUEST")
    if re.fullmatch(PROBE,path):
        if data!={"schema":"NEW100_READINESS_PROBE_V1",
                  "day_turkey":day,"mode":"NO_MODELS_NO_ODDS_NO_PILOT",
                  "cohort":"new100"}:
            raise IntakeBlocked("PROBE_MUST_NOT_CONTAIN_FIXTURES")
        return {"schema":SCHEMA,"kind":"readiness_only","day_turkey":day,
                "fixture_count":0,"models_computed":0,"new_pilot_records":0,
                "bookmaker_api_calls":0,"verified_live_model_execution":False,
                "manual_dispatch_confirmed":False,
                "push_route_accepted":True,
                "source_path":path}
    rows=named("new100",day,path)
    if not 1<=len(rows)<=100:raise IntakeBlocked("INVALID_NAMED_MATCH_COUNT")
    return {"schema":SCHEMA,"kind":"real_named_request","day_turkey":day,
            "fixture_count":len(rows),"models_computed":0,
            "bookmaker_api_calls":0,"source_path":path,
            "not_an_automatic_match_selector":True}

def main():
    p=argparse.ArgumentParser();p.add_argument("--path",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args();out=inspect(a.path)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        json.dump(out,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
        f.write("\n")
    print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
