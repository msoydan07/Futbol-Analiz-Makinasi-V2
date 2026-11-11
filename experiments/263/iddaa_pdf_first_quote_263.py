"""SHA-sealed pre-forecast user iddaa PDF price bridge for existing 2.6.3 policy.

The user has supplied an iddaa.com PDF once. This code never re-queries
iddaa, Pinnacle, Nesine or any other bookmaker. Original PDF bytes must
be present at the invoking boundary and independently re-parsed ONCE
locally to protect against a manually edited JSON intermediate.

PDF observed < four-model forecast < decision < verified kickoff.
This is ARCHIVED_PDF_PRE_FORECAST, never a fresh post-forecast T-60 quote.
Missing side removes only its own no-vig GROUP; other groups survive.
No 1.5/3.5 price or selection can ever enter this snapshot.
"""
from __future__ import annotations
import hashlib,json,math
from datetime import datetime,timezone,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA="263_iddaa_pdf_first_sha_price_v1"
ALLOWED=("MS1","MSX","MS2","OVER_2.5","UNDER_2.5","BTTS_YES","BTTS_NO")
GROUPS={
  "MS":("MS1","MSX","MS2"),
  "GOALS_2.5":("UNDER_2.5","OVER_2.5"),
  "KG":("BTTS_YES","BTTS_NO"),
}
TR=ZoneInfo("Europe/Istanbul")
MAX_PRICE_AGE=timedelta(hours=24)

def canonical_bytes(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,
                      separators=(",",":"),allow_nan=False).encode("utf-8")
def sha256(obj):return hashlib.sha256(canonical_bytes(obj)).hexdigest()
def utc(value):
    parsed=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if parsed.tzinfo is None:raise ValueError("PDF_FIRST_TIMEZONE_REQUIRED")
    return parsed.astimezone(timezone.utc)
def fixture_key(f):
    return ":".join((f["league"],f["home_id"],f["away_id"],
                     f["match_local_date"]))

def verify_original_pdf(pdf_path,bulletin):
    """Local PDF, not another online odds lookup. Every extracted byte/row
    must match the stored bulletin; user does not need to send anything twice.
    """
    from iddaa_pdf_bulletin_263 import parse_pdf
    source=Path(pdf_path)
    if not source.is_file():raise ValueError("ORIGINAL_USER_PDF_REQUIRED")
    original=parse_pdf(source)
    if sha256(original)!=sha256(bulletin):
        raise ValueError("PDF_REPARSE_AND_BULLETIN_CONTENT_DIFFER")
    if original["pdf_sha256"]!=hashlib.sha256(source.read_bytes()).hexdigest():
        raise ValueError("ORIGINAL_USER_PDF_SHA_MISMATCH")
    return original["pdf_sha256"]

def build_snapshot(bulletin,session,session_row,forecast,*,source_pdf=None,
                   verified_pdf_sha=None):
    """Only accept proof of ORIGINAL PDF identity. Test injection may set
    verified_pdf_sha, but normal CLI MUST use source_pdf via verify_original_pdf.
    """
    from iddaa_pdf_session_263 import pdf_prices,market_no_vig,SCHEMA as SESSION
    from iddaa_pdf_bulletin_263 import SCHEMA as BULLETIN
    if source_pdf is not None:
        actual_sha=verify_original_pdf(source_pdf,bulletin)
    elif verified_pdf_sha is not None:
        actual_sha=verified_pdf_sha  # explicit test harness, not CLI
    else:
        raise ValueError("ORIGINAL_USER_PDF_REQUIRED")
    if (bulletin.get("schema")!=BULLETIN or
        bulletin.get("source_domain")!="iddaa.com" or
        session.get("schema")!=SESSION or
        session.get("source_bookmaker")!="iddaa.com" or
        session.get("pdf_sha256")!=actual_sha or
        bulletin.get("pdf_sha256")!=actual_sha):
        raise ValueError("PDF_FIRST_SOURCE_AND_SESSION_MISMATCH")
    if session.get("bookmaker_reverification_calls")!=0:
        raise ValueError("SECOND_BOOKMAKER_CALLS_NOT_ALLOWED")
    i=session_row.get("index")
    if not isinstance(i,int) or isinstance(i,bool) or i<0 or i>=len(bulletin["rows"]):
        raise ValueError("PDF_FIRST_INVALID_ROW_INDEX")
    if session.get("rows",[])[i]!=session_row:
        raise ValueError("PDF_FIRST_SESSION_ROW_REWRITTEN")
    r=bulletin["rows"][i]
    if (r.get("status")!="PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK"
        or session_row.get("status")!="FOUR_MODELS_FORECAST_SHA_CREATED"
        or session_row.get("model_forecast_created") is not True):
        raise ValueError("PDF_FIRST_UNQUALIFIED_ROW")
    for source_field,dest_field in (("league","league"),("home_label","pdf_home"),
            ("away_label","pdf_away"),("match_date_tr","match_date_tr"),
            ("kickoff_time_tr","kickoff_time_tr"),("page","pdf_page")):
        if r[source_field]!=session_row.get(dest_field):
            raise ValueError("PDF_FIRST_ROW_IDENTITY_CHANGED_"+dest_field)
    if session_row.get("prices")!=pdf_prices(r):
        raise ValueError("PDF_FIRST_REWRITTEN_PRICES")
    if session_row.get("market_no_vig")!=market_no_vig(r):
        raise ValueError("PDF_FIRST_REWRITTEN_NO_VIG")
    if (session_row.get("price_capture_utc")!=session["pdf_capture_utc"]
        or session["pdf_capture_utc"]!=bulletin["pdf_capture_utc"]):
        raise ValueError("PDF_FIRST_CAPTURE_TIMESTAMP_CHANGED")
    # Prediction itself will be cryptographically verified by the existing
    # four_model_value_policy_263.decide / sealed_payload gate.
    fx=forecast["fixture"]
    if (session_row.get("model_forecast_sha256")!=forecast.get("payload_sha256")
        or (session_row.get("league"),session_row.get("home_id"),
            session_row.get("away_id"))!=
           (fx.get("league"),fx.get("home_id"),fx.get("away_id"))
        or fx.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE"):
        raise ValueError("PDF_FIRST_FORECAST_FIXTURE_SHA_IDENTITY_MISMATCH")
    ko=utc(fx["kickoff_utc"])
    local=ko.astimezone(TR)
    if (local.date().isoformat(),local.strftime("%H:%M"))!=(
            r["match_date_tr"],r["kickoff_time_tr"]):
        raise ValueError("PDF_FIRST_OFFICIAL_VS_PDF_KICKOFF_MISMATCH")
    official=session_row.get("official") or {}
    if (official.get("source_url")!=fx.get("official_source")
        or official.get("kickoff_utc")!=ko.isoformat()):
        raise ValueError("PDF_FIRST_OFFICIAL_GATE_PROOF_MISSING")
    observed=utc(bulletin["pdf_capture_utc"])
    created=utc(forecast["created_at_utc"])
    if not observed<=created<ko:
        raise ValueError("PDF_FIRST_INVALID_OBSERVATION_FORECAST_ORDER")
    markets=market_no_vig(r)
    complete={}
    for group,keys in GROUPS.items():
        m=markets[group]
        if m.get("status")!="FULL_MARKET_QUOTE_AVAILABLE":
            continue
        prices=m.get("prices") or {}
        fair=m.get("no_vig") or {}
        if set(prices)!=set(keys) or set(fair)!=set(keys):
            raise ValueError("PDF_FIRST_INCOMPLETE_MARKET_IN_COMPLETE_GROUP")
        complete[group]={"prices":prices,"no_vig":fair}
    snap={
        "schema":SCHEMA,
        "source_domain":"iddaa.com",
        "human_source_type":"ORIGINAL_USER_CHROME_PRINT_TO_PDF",
        "network_bookmaker_reverified":False,
        "source_pdf_sha256":actual_sha,
        "source_pdf_page":r["page"],
        "source_row_index":i,
        "source_row_home":r["home_label"],
        "source_row_away":r["away_label"],
        "source_row_local_date":r["match_date_tr"],
        "source_row_local_time":r["kickoff_time_tr"],
        "source_row_league":r["league"],
        "fixture_key":fixture_key(fx),
        "forecast_sha256":forecast["payload_sha256"],
        "kickoff_utc":ko.isoformat(),
        "observed_at_utc":observed.isoformat(),
        "created_after_pdf_forecast_utc":created.isoformat(),
        "groups":complete,
        "missing_or_invalid_groups":[g for g in GROUPS if g not in complete],
        "price_age_class":"ARCHIVED_PDF_PRE_FORECAST",
        "is_current_live_quote":False,
        "bookmaker_api_calls":0,
    }
    snap["payload_sha256"]=sha256(snap)
    return snap

def extract(snapshot,forecast,now):
    """Existing four-model decision accepts these prices only in PDF mode.
    This does not pretend odds were observed after the forecast.
    """
    from iddaa_pdf_session_263 import SCHEMA as _session_schema # no circular policy
    if not isinstance(snapshot,dict) or snapshot.get("schema")!=SCHEMA:
        raise ValueError("PDF_FIRST_PRICE_SCHEMA_INVALID")
    digest=snapshot.get("payload_sha256")
    if not isinstance(digest,str) or digest!=sha256(
          {k:v for k,v in snapshot.items() if k!="payload_sha256"}):
        raise ValueError("PDF_FIRST_PRICE_SNAPSHOT_SHA_MISMATCH")
    if (snapshot.get("source_domain")!="iddaa.com"
        or snapshot.get("human_source_type")!="ORIGINAL_USER_CHROME_PRINT_TO_PDF"
        or snapshot.get("network_bookmaker_reverified") is not False
        or snapshot.get("bookmaker_api_calls")!=0
        or snapshot.get("price_age_class")!="ARCHIVED_PDF_PRE_FORECAST"
        or snapshot.get("is_current_live_quote") is not False):
        raise ValueError("PDF_FIRST_SOURCE_SCOPE_MISMATCH")
    f=forecast["fixture"]
    if (snapshot.get("forecast_sha256")!=forecast.get("payload_sha256")
        or snapshot.get("fixture_key")!=fixture_key(f)
        or utc(snapshot["kickoff_utc"])!=utc(f["kickoff_utc"])):
        raise ValueError("PDF_FIRST_FORECAST_JOIN_WRONG")
    seen=utc(snapshot["observed_at_utc"])
    created=utc(forecast["created_at_utc"])
    now=now.astimezone(timezone.utc)
    ko=utc(f["kickoff_utc"])
    if not seen<=created<=now<ko or snapshot["created_after_pdf_forecast_utc"]!=created.isoformat():
        raise ValueError("PDF_FIRST_TIME_SEQUENCE_INVALID")
    if created-seen>MAX_PRICE_AGE or now-seen>MAX_PRICE_AGE:
        return {},"PDF_FIRST_ARCHIVED_PRICE_OVER_24_HOURS_PAS"
    values={};groups=snapshot["groups"]
    if not set(groups).issubset(GROUPS):
        raise ValueError("PDF_FIRST_FORBIDDEN_MARKET_GROUP")
    for group,parts in groups.items():
        keys=GROUPS[group]
        prices=parts["prices"];fair=parts["no_vig"]
        if set(prices)!=set(keys) or set(fair)!=set(keys):
            raise ValueError("PDF_FIRST_INCOMPLETE_SIDE")
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or
              not math.isfinite(v) or v<=1 or v>=1000 for v in prices.values()):
            raise ValueError("PDF_FIRST_INVALID_PRICE")
        gross=sum(1/prices[k] for k in keys)
        if not 1<gross<1.3:
            raise ValueError("PDF_FIRST_MARGIN_OUT_OF_RANGE")
        if any(abs(fair[k]-(1/prices[k])/gross)>1e-10 for k in keys):
            raise ValueError("PDF_FIRST_MARJLESS_IMPLIED_MISMATCH")
        for key in keys:
            values[key]={"odds":prices[key],"fair":fair[key],
                         "source":"iddaa.com",
                         "url":"https://www.iddaa.com/program/futbol",
                         "checked":seen.isoformat(),
                         "age_class":"ARCHIVED_PDF_PRE_FORECAST",
                         "snapshot_sha256":digest}
    return values,"USER_IDDAA_PDF_PRE_FORECAST_NOT_NETWORK_REVERIFIED"
