"""Durable fail-closed per-Turkey-day / league / Pinnacle h2h credit reservation.

Reservation is written BEFORE an external call. A failed call also consumes the
daily slot: never silently retry. Use a shared persistent directory and serialize
all callers through a single GitHub Actions concurrency group; separate runners
without shared storage must NOT call the API independently.
"""
from __future__ import annotations
import argparse
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA="SABAH_PINNACLE_RESERVATION_V1"
LEAGUES=frozenset(("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1"))
TR=ZoneInfo("Europe/Istanbul")
class AlreadyReserved(ValueError): pass

def reserve(root, league, now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError("AWARE_CLOCK_REQUIRED")
    if league not in LEAGUES: raise ValueError("UNSUPPORTED_LEAGUE")
    now=now.astimezone(timezone.utc)
    day=now.astimezone(TR).date().isoformat()
    root=Path(root)
    folder=root/day
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/(league+"_pinnacle_h2h.json")
    record={"schema":SCHEMA,"day_turkey":day,"league":league,
            "bookmaker":"pinnacle","market":"h2h",
            "reserved_at_utc":now.isoformat(),
            "status":"CREDIT_RESERVED_OUTCOME_UNKNOWN",
            "retry_allowed_same_day":False}
    try:
        with path.open("x",encoding="utf-8") as f:
            json.dump(record,f,sort_keys=True,ensure_ascii=False)
            f.write("\n")
    except FileExistsError:
        raise AlreadyReserved("DAILY_LEAGUE_CREDIT_ALREADY_RESERVED") from None
    return path,record

def check_existing(root,league,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError("AWARE_CLOCK_REQUIRED")
    if league not in LEAGUES:raise ValueError("UNSUPPORTED_LEAGUE")
    day=now.astimezone(TR).date().isoformat()
    path=Path(root)/day/(league+"_pinnacle_h2h.json")
    if not path.exists():return None
    record=json.loads(path.read_text(encoding="utf-8"))
    if (record.get("schema")!=SCHEMA or record.get("league")!=league or
        record.get("day_turkey")!=day or record.get("bookmaker")!="pinnacle" or
        record.get("market")!="h2h" or record.get("retry_allowed_same_day") is not False):
        raise ValueError("INVALID_EXISTING_CREDIT_RESERVATION")
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ledger",required=True)
    p.add_argument("--league",required=True)
    a=p.parse_args()
    path,record=reserve(a.ledger,a.league)
    print(json.dumps({"reservation_path":str(path),"status":record["status"],
                      "safe_to_attempt_one_external_call":True},ensure_ascii=False))

if __name__=="__main__":main()
