"""First user iddaa PDF day lock (research only).

A PDF printed on an earlier day is not a fresh morning bulletin. The second
PDF must NEVER start another new first-PDF forecast session, even if its SHA
differs. Operates before any private provider fetch, forecast, or seal.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA="263_FIRST_USER_PDF_SINGLE_MORNING_LOCK_V1"
TR=ZoneInfo("Europe/Istanbul")
LEAGUES=frozenset(("ENG1","ENG2","GER1","ESP1","ITA1","FRA1",
                   "NED1","TUR1","POR1","BEL1"))
class FirstPdfBlocked(ValueError):
    pass

def canonical(obj):
    return json.dumps(obj,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode("utf-8")

def aware(value):
    if isinstance(value,datetime):
        parsed=value
    else:
        try:parsed=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        except (ValueError,TypeError) as exc:
            raise FirstPdfBlocked("PDF_OR_CLOCK_INVALID") from exc
    if parsed.tzinfo is None:
        raise FirstPdfBlocked("PDF_OR_CLOCK_MISSING_TIMEZONE")
    return parsed.astimezone(timezone.utc)

def verify_current_first_pdf(bulletin,*,now=None):
    """Only same-day first PDF; zero suitable current fixtures = hard block."""
    current=aware(now or datetime.now(timezone.utc))
    if not isinstance(bulletin,dict):
        raise FirstPdfBlocked("ORIGINAL_IDDAA_BULLETIN_REQUIRED")
    if (bulletin.get("schema")!="263_iddaa_pdf_pregame_bulletin_v1"
        or bulletin.get("source_domain")!="iddaa.com"):
        raise FirstPdfBlocked("ONLY_USER_IDDAA_FIRST_PDF_ACCEPTED")
    sha=bulletin.get("pdf_sha256")
    if (not isinstance(sha,str) or len(sha)!=64 or
        any(x not in "0123456789abcdef" for x in sha)):
        raise FirstPdfBlocked("ORIGINAL_PDF_SHA_INVALID")
    stamp=aware(bulletin.get("pdf_capture_utc"))
    local_day=current.astimezone(TR).date().isoformat()
    if stamp-current>timedelta(minutes=3):
        raise FirstPdfBlocked("PDF_CREATION_AFTER_ACTUAL_CLOCK")
    if stamp.astimezone(TR).date().isoformat()!=local_day:
        raise FirstPdfBlocked("STALE_OR_FUTURE_FIRST_PDF_DIFFERENT_TURKEY_DAY")
    if current-stamp>timedelta(hours=15):
        raise FirstPdfBlocked("FIRST_PDF_TOO_OLD_TODAY")
    rows=bulletin.get("rows")
    if not isinstance(rows,list):
        raise FirstPdfBlocked("ORIGINAL_PDF_ROWS_MISSING")
    eligible=[r for r in rows if isinstance(r,dict)
              and r.get("league") in LEAGUES
              and r.get("match_date_tr")==local_day
              and r.get("status")=="PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK"
              and isinstance(r.get("home_label"),str)
              and isinstance(r.get("away_label"),str)
              and r["home_label"].strip() and r["away_label"].strip()]
    if not eligible:
        raise FirstPdfBlocked("NO_TODAY_TEN_LEAGUE_USABLE_FIRST_PDF_FIXTURE")
    keys={(r["league"],r["match_date_tr"],r["home_label"].casefold(),
           r["away_label"].casefold()) for r in eligible}
    if len(keys)!=len(eligible):
        raise FirstPdfBlocked("DUPLICATE_CURRENT_FIRST_PDF_FIXTURES")
    return {"schema":"263_FIRST_PDF_PREFLIGHT_RESEARCH_V1",
            "pdf_sha256":sha,"first_pdf_local_date":local_day,
            "current_ten_league_eligible_fixtures":len(eligible),
            "odds_only_fifth_reference":True,
            "production_forecast_approved":False,
            "second_pdf_resealing_allowed":False}

def claim_single_first_pdf(root,preflight):
    """Create a daily write-once lock via atomic O_EXCL. Same PDF may retry.

    A second PDF of different SHA on the same day is REJECTED, not mistaken
    for a new first PDF. Human review is required to replace a failed
    first-PDF session; the old record must not be silently rewritten.
    """
    if not isinstance(preflight,dict) or preflight.get("schema")!="263_FIRST_PDF_PREFLIGHT_RESEARCH_V1":
        raise FirstPdfBlocked("VERIFIED_FIRST_PDF_PREFLIGHT_REQUIRED")
    day=preflight["first_pdf_local_date"]
    sha=preflight["pdf_sha256"]
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    path=root/("_first_pdf_day_"+day+".json")
    entry={"schema":SCHEMA,"first_pdf_local_date":day,
           "pdf_sha256":sha,"session_kind":"FIRST_PDF_ONLY",
           "forecast_second_pdf_forbidden":True}
    entry["payload_sha256"]=hashlib.sha256(canonical(entry)).hexdigest()
    try:
        with path.open("x",encoding="utf-8") as f:
            json.dump(entry,f,ensure_ascii=False,sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        status="FIRST_PDF_DAY_LOCK_CREATED"
    except FileExistsError:
        try:existing=json.loads(path.read_text(encoding="utf-8"))
        except (OSError,ValueError) as exc:
            raise FirstPdfBlocked("FIRST_PDF_DAY_LOCK_UNREADABLE") from exc
        digest=existing.get("payload_sha256")
        if (existing.get("schema")!=SCHEMA or
            digest!=hashlib.sha256(canonical({k:v for k,v in existing.items()
                                               if k!="payload_sha256"})).hexdigest() or
            existing.get("first_pdf_local_date")!=day):
            raise FirstPdfBlocked("FIRST_PDF_DAY_LOCK_TAMPERED")
        if existing.get("pdf_sha256")!=sha:
            raise FirstPdfBlocked("SECOND_PDF_CANNOT_CREATE_ANOTHER_MORNING_SEAL")
        status="SAME_FIRST_PDF_ONLY_ALLOW_EXISTING_SESSION_OR_SAFE_RETRY"
    return {"status":status,"pdf_sha256":sha,"local_date":day,
            "first_pdf_day_lock":str(path),
            "production_approved":False}
