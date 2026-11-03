"""UEFA 2.6.3: source-backed international Elo *reference* attached AFTER official match gate.

Not a calibrated goal model. No added lambda, EV, 1X2, pilot or production writes.
Provider: beyondELO (https://beyondelo.com), CC BY 4.0.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
import unicodedata
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

BASE="https://public-api.beyondelo.com/v1/datasets/club-ratings.csv"
COHORT="experiments/263/evidence/elo_uefa_active_cohort_2026_11_03.json"
ALIASES="experiments/263/evidence/elo_33_alias_name_review_2026_11_03.json"
COUNTRIES={"BEL1":"BEL","ENG1":"ENG","ESP1":"ESP","FRA1":"FRA",
           "GER1":"GER","ITA1":"ITA","NED1":"NED","POR1":"POR","TUR1":"TUR"}
VERSION="263_EUROPE_ELO_SOURCE_BRIDGE_REFERENCE_ONLY_V1"
SOURCE_MAX_BYTES=2_000_000
SOURCE_MAX_LAG_DAYS=2
LAST_RATED_MAX_LAG_DAYS=45

class EloBridgeError(ValueError): pass

def norm(s):
    if not isinstance(s,str): return ""
    s=unicodedata.normalize("NFKD",s.casefold().replace("ı","i").replace("ß","ss"))
    return " ".join("".join(ch if ch.isalnum() else " " for ch in s
                            if not unicodedata.combining(ch)).split())

def iso_day(v):
    try: return date.fromisoformat(v)
    except (TypeError, ValueError): raise EloBridgeError("INVALID_DATE")

def stamp(v):
    if not isinstance(v,datetime) or v.tzinfo is None:
        raise EloBridgeError("UTC_AWARE_TIMESTAMP_REQUIRED")
    return v.astimezone(timezone.utc)

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validated_cohort(index,cohort):
    all_ids=set(cohort.get("eligible_team_ids",[]))
    excluded=set(cohort.get("excluded_team_ids",[]))
    members=index["season_memberships"]["2026-2027"]
    actual=set(members["ENG2"])
    erz=[tid for tid in members["TUR1"] if norm(index["teams"][tid]["name"])=="erzurumspor fk"]
    if (len(all_ids)!=167 or len(excluded)!=25 or len(erz)!=1 or
        excluded!=actual|set(erz) or all_ids & excluded or
        all_ids!=({tid for league,ids in members.items()
                   if league!="ENG2" for tid in ids}-set(erz))):
        raise EloBridgeError("EUROPE_ELO_SCOPE_COHORT_UNEXPECTED")
    leagues={tid:league for league,ids in members.items() for tid in ids}
    return all_ids,leagues

def parse_current(raw):
    if not isinstance(raw,bytes) or not raw or len(raw)>SOURCE_MAX_BYTES:
        raise EloBridgeError("CURRENT_CSV_SIZE_INVALID")
    try:
        reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        needed={"slug","name","country_code","elo","rd","is_ranked","last_match_date","as_of"}
        if not needed.issubset(set(reader.fieldnames or [])):
            raise EloBridgeError("ELO_CURRENT_REQUIRED_COLUMNS_MISSING")
        data=list(reader)
    except UnicodeDecodeError as exc: raise EloBridgeError("CSV_ENCODING") from exc
    if not data: raise EloBridgeError("CSV_EMPTY")
    slugs=defaultdict(list)
    for row in data:
        if (row.get("slug") or "").strip():
            slugs[row["slug"]].append(row)
    return data,slugs

def build_crosswalk(index,cohort,review,raw):
    """Reconcile all 167 canonical IDs by unique exact local name/alias or reviewed name triple.

    Must never map an unrecognized provider name to a team just because ratings are similar.
    Returned identity standard is *name-based*, not independent UEFA team-ID proof.
    """
    active,leagues=validated_cohort(index,cohort)
    if review.get("schema")!="263_EUROPE_ELO_33_NAMED_ALIAS_REVIEW_V1":
        raise EloBridgeError("REVIEWED_ALIAS_SCHEMA_MISSING")
    manual={}
    for x in review.get("entries",[]):
        tid=x["canonical_team_id"]
        if (tid in manual or tid not in active or x["league"]!=leagues[tid] or
            x["official_name"]!=index["teams"][tid]["name"] or
            x["official_evidence_url"]!=index["teams"][tid]["official_name_evidence_url"] or
            x["provider_country_expected"]!=COUNTRIES[x["league"]]):
            raise EloBridgeError("ALIAS_REVIEW_IDENTITY_POLICY_VIOLATED")
        manual[tid]=x
    if len(manual)!=33 or len({x["provider_slug"] for x in manual.values()})!=33:
        raise EloBridgeError("MANUAL_REVIEW_COUNT_UNEXPECTED")
    rows,by_slug=parse_current(raw)
    alias_ids=defaultdict(set)
    for alias,tid in index["aliases"].items():
        if tid in active: alias_ids[norm(alias)].add(tid)
    for tid in active:
        club=index["teams"][tid]
        for alias in (club["name"],club.get("key","")):
            if norm(alias): alias_ids[norm(alias)].add(tid)
    candidates=defaultdict(list)
    unsafe=defaultdict(set)
    for row in rows:
        slug=row.get("slug","").strip()
        if not slug: continue
        hits=alias_ids.get(norm(slug),set()) | alias_ids.get(norm(row.get("name","")),set())
        if len(hits)!=1: continue
        tid=next(iter(hits))
        if len(by_slug[slug])!=1 or row["country_code"]!=COUNTRIES[leagues[tid]]:
            unsafe[tid].add("DUPLICATE_SLUG_OR_COUNTRY_MISMATCH")
            continue
        candidates[tid].append((row,"NORMALIZED_OFFICIAL_ALIAS"))
    result={};blocked={}
    for tid in active:
        reviewed=manual.get(tid)
        choices=candidates.get(tid,[])
        if reviewed is not None:
            slug=reviewed["provider_slug"]
            manual_rows=by_slug.get(slug,[])
            if (len(manual_rows)!=1 or
                norm(manual_rows[0]["name"])!=norm(reviewed["provider_name_expected"]) or
                manual_rows[0]["country_code"]!=reviewed["provider_country_expected"]):
                blocked[tid]="REVIEWED_SOURCE_SLUG_NAME_OR_COUNTRY_CHANGED"
                continue
            row=manual_rows[0]
            if choices and any(r["slug"]!=slug for r,_ in choices):
                blocked[tid]="AUTO_VS_MANUAL_IDENTITY_CONFLICT"
                continue
            source="REVIEWED_FEDERATION_NAME_PLUS_PROVIDER_SLUG"
        elif len(choices)==1 and not unsafe.get(tid):
            row,source=choices[0]
        else:
            blocked[tid]="SOURCE_IDENTITY_NOT_UNIQUELY_RECONCILED"
            continue
        if not row.get("slug"):
            blocked[tid]="SOURCE_SLUG_EMPTY"; continue
        result[tid]={"canonical_team_id":tid,"official_name":index["teams"][tid]["name"],
                     "league":leagues[tid],"provider_name":row["name"],
                     "provider_slug":row["slug"],"source_identity_level":source,
                     "source_row":row}
    slug_to_ids=defaultdict(list)
    for tid,x in result.items(): slug_to_ids[x["provider_slug"]].append(tid)
    for tids in slug_to_ids.values():
        if len(tids)>1:
            for tid in tids: blocked[tid]="DUPLICATE_PROVIDER_CLUB_ASSIGNMENT";result.pop(tid,None)
    return result,blocked

def fetch_current_snapshot():
    request=urllib.request.Request(
        BASE,headers={"Accept":"text/csv","User-Agent":"UEFA263-Elo-Verified-After-Fixture"})
    with urllib.request.urlopen(request,timeout=15) as resp:
        if resp.status!=200 or resp.geturl()!=BASE:
            raise EloBridgeError("CURRENT_SOURCE_URL_OR_HTTP_REJECTED")
        raw=resp.read(SOURCE_MAX_BYTES+1)
    return raw,datetime.now(timezone.utc)

def preflight_elo(scope,cohort):
    """Return a decision before any provider request, even when original UEFA scope passes."""
    if not scope.get("allow_further_research",False):
        return "UEFA_SCOPE_BLOCKED"
    active=set(cohort.get("eligible_team_ids",[]))
    if (scope["home"].get("canonical_team_id") not in active or
        scope["away"].get("canonical_team_id") not in active):
        return "EUROPE_ELO_COHORT_EXCLUDED"
    return "ELIGIBLE_FOR_ELO_SOURCE_REVIEW"

def reference_for_match(scope,fixture,index,cohort,review,
                        source_provider=None,at_utc=None):
    """Attach only after scope + actual official fixture have passed.

    source_provider is a test injection returning (raw_csv_bytes, fetched_at_utc).
    Never use source after KO, for earlier seasons, or on a future-dated snapshot.
    """
    check=preflight_elo(scope,cohort)
    result={"version":VERSION,"status":check,"provider":"beyondELO",
            "license":"CC BY 4.0 — https://beyondelo.com",
            "uefa_club_ids_independently_verified":False,
            "elo_affects_goal_lambda":False,"elo_1x2_probabilities":None,
            "model_calibration_approved":False,"betting_approval":False}
    if check!="ELIGIBLE_FOR_ELO_SOURCE_REVIEW": return result
    if not isinstance(fixture,dict) or not fixture.get("official_article_directly_fetched"):
        return {**result,"status":"OFFICIAL_FIXTURE_REQUIRED_BEFORE_ELO"}
    kickoff=stamp(datetime.fromisoformat(fixture["kickoff_utc"]))
    now=stamp(at_utc or datetime.now(timezone.utc))
    if now >= kickoff:
        return {**result,"status":"MATCH_ALREADY_STARTED_SOURCE_NOT_FETCHED"}
    provider=source_provider or fetch_current_snapshot
    try:
        raw,fetched_at=provider()
        fetched_at=stamp(fetched_at)
        if fetched_at > now+timedelta(minutes=1) or fetched_at >= kickoff:
            raise EloBridgeError("DATA_FETCH_TIMESTAMP_AFTER_CUTOFF")
        mapping,blocked=build_crosswalk(index,cohort,review,raw)
        home=scope["home"]["canonical_team_id"]
        away=scope["away"]["canonical_team_id"]
        if home not in mapping or away not in mapping:
            return {**result,"status":"ELO_IDENTITY_NOT_VERIFIED",
                    "missing_canonical_ids":[tid for tid in (home,away) if tid not in mapping],
                    "identity_failure_reason":{tid:blocked.get(tid,"NOT_FOUND") for tid in (home,away) if tid not in mapping},
                    "mapped_candidate_count":len(mapping)}
        asof_dates={r["as_of"] for r in (mapping[home]["source_row"],mapping[away]["source_row"])}
        if len(asof_dates)!=1: raise EloBridgeError("MULTIPLE_SNAPSHOT_ASOF_DATES")
        asof=iso_day(next(iter(asof_dates)))
        if asof>fetched_at.date() or (fetched_at.date()-asof).days>SOURCE_MAX_LAG_DAYS:
            raise EloBridgeError("STALE_OR_FUTURE_SOURCE_BOARD")
        if asof>kickoff.date():
            raise EloBridgeError("FUTURE_BOARD_FOR_KICKOFF")
        details=[]
        for tid in (home,away):
            record=mapping[tid]
            row=record["source_row"]
            last=iso_day(row["last_match_date"])
            if (last>=kickoff.date() or last>asof or
                (asof-last).days>LAST_RATED_MAX_LAG_DAYS or
                row["is_ranked"].casefold()!="true"):
                raise EloBridgeError("CLUB_RATING_OLD_OR_AFTER_KICKOFF")
            elo=float(row["elo"]);rd=float(row["rd"])
            if not math.isfinite(elo) or not 0<=elo<=4000 or not math.isfinite(rd) or not 0<=rd<=1000:
                raise EloBridgeError("ELO_OR_RD_INVALID")
            details.append({"canonical_id":tid,"official_name":record["official_name"],
                            "league":record["league"],"provider_slug":record["provider_slug"],
                            "provider_name":record["provider_name"],
                            "identity_check":record["source_identity_level"],
                            "elo":elo,"rd":rd,"last_rated_match":last.isoformat()})
        return {**result,"status":"ELO_DESCRIPTIVE_REFERENCE_ATTACHED_NOT_MODEL_CALIBRATED",
                "home":details[0],"away":details[1],
                "home_minus_away_elo":round(details[0]["elo"]-details[1]["elo"],3),
                "board_as_of":asof.isoformat(),
                "fetched_at_utc":fetched_at.isoformat(),
                "source_sha256":hashlib.sha256(raw).hexdigest(),
                "mapped_candidate_count":len(mapping),"active_elo_cohort":len(cohort["eligible_team_ids"]),
                "unmapped_candidate_count":len(blocked),
                "source_identity_limit":"NAME_AND_COUNTRY_RECONCILIATION_ONLY_NO_SHARED_UEFA_ID",
                "model_calibration_approved":False}
    except (OSError,ValueError,KeyError,UnicodeError,OverflowError) as exc:
        return {**result,"status":"ELO_SOURCE_OR_INTEGRITY_NOT_VERIFIED",
                "reason":str(exc)[:120],"error_type":type(exc).__name__}
