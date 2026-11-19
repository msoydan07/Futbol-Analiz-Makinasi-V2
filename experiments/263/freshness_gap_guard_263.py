"""Fail-closed, read-only public-provider gap check for >10-day league breaks.

Why: calendar DAYS since last completed match are not the same as missed MATCHES.
No new model, no xG, no history alteration, no official federation endorsement.
Only allows a bounded (>10, <=21 day) gap when a newly fetched, complete-looking
public season CSV confirms *no later completed match* and its near-cutoff
scores/identities agree with the already accepted 2026-27 snapshot.

This is public SECONDARY provider evidence, not a federation confirmation.
The existing pre-kickoff official named-fixture check remains mandatory.
"""
from __future__ import annotations

import hashlib
import json
import math
import urllib.request
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

from season_refresh_263 import LEAGUES, SOURCE_PREFIX, _csv, _count, parse_date
from mackolik_identity_gate_263 import _memberships, _candidate_id, _validate_identity_source

MAX_DEFAULT_DAYS=10
MAX_RESEARCH_BREAK_DAYS=21
OVERLAP_DAYS=21
MAX_CSV_BYTES=2_000_000
SCHEMA="263_MATCH_GAP_PUBLIC_PROVIDER_CHECK_V1"
CACHE_MAX_AGE_SECONDS=600
_CACHE={}

class StaleLeagueData(ValueError):
    pass

def _source(league, *, now, fetcher=None):
    """Actual morning uses only a fixed HTTPS public-source URL."""
    if league not in LEAGUES:
        raise StaleLeagueData("UNSUPPORTED_LEAGUE")
    url=SOURCE_PREFIX+LEAGUES[league]+".csv"
    if fetcher is None:
        def fetcher(u):
            req=urllib.request.Request(u,headers={"User-Agent":
                "FootballResearchAudit/263 (gap-check; no-odds; no-login)"})
            with urllib.request.urlopen(req,timeout=15) as r:
                if getattr(r,"status",None)!=200 or r.geturl()!=u:
                    raise StaleLeagueData("SOURCE_REDIRECT_OR_STATUS_REJECTED")
                data=r.read(MAX_CSV_BYTES+1)
            return data
    if not callable(fetcher):
        raise StaleLeagueData("SOURCE_FETCHER_INVALID")
    if fetcher is None: # unreachable but prevents accidentally treating a missing source as evidence
        raise StaleLeagueData("NO_PUBLIC_SOURCE")
    try:
        data=fetcher(url)
    except (OSError,TimeoutError,ValueError) as exc:
        raise StaleLeagueData("FRESH_SOURCE_UNAVAILABLE_"+type(exc).__name__) from exc
    if not isinstance(data,bytes) or not 1000 <= len(data) <= MAX_CSV_BYTES:
        raise StaleLeagueData("SOURCE_EMPTY_OR_OVERSIZE")
    try:
        parsed=_csv(data)
    except ValueError as exc:
        raise StaleLeagueData("SOURCE_CSV_UNRELIABLE") from exc
    return parsed,hashlib.sha256(data).hexdigest(),url

def _identity(league, resolver):
    if resolver is not None:
        if not callable(resolver):
            raise StaleLeagueData("IDENTITY_RESOLVER_INVALID")
        return resolver
    file=Path(__file__).with_name("evidence")/"identity_index_263.json"
    try:
        index=json.loads(file.read_text(encoding="utf-8"))
        _validate_identity_source(index)
        membership=_memberships(index,"2026-2027")
    except (ValueError,KeyError,OSError,TypeError) as exc:
        raise StaleLeagueData("IDENTITY_REGISTRY_INVALID") from exc
    def _exact(name):
        club=_candidate_id(index,name,league,membership,{})
        if club is None:
            raise StaleLeagueData("UNKNOWN_PROVIDER_TEAM_IN_GAP")
        return club
    return _exact

def _compute(rows,league,target_date,now,raw_rows,source_sha,url,resolver=None):
    if league not in LEAGUES:
        raise StaleLeagueData("UNSUPPORTED_LEAGUE")
    if now.tzinfo is None:
        raise StaleLeagueData("NAIVE_CLOCK")
    try:
        target=date.fromisoformat(target_date)
    except (ValueError,TypeError) as exc:
        raise StaleLeagueData("INVALID_TARGET_DATE") from exc
    if target>now.date()+timedelta(days=7) or target<now.date():
        raise StaleLeagueData("GAP_CHECK_NOT_LIVE_PREMATCH_WEEK")
    hist=[r for r in rows if r.get("league")==league and r.get("season")=="2026-2027"]
    if len(hist)<40:
        raise StaleLeagueData("NOT_ENOUGH_CURRENT_SEASON_HISTORY")
    try:
        latest=max(date.fromisoformat(r["match_date"]) for r in hist)
    except (KeyError,ValueError,TypeError) as exc:
        raise StaleLeagueData("BAD_HISTORICAL_DATE") from exc
    age=(target-latest).days
    if age<=MAX_DEFAULT_DAYS:
        return {"schema":SCHEMA,"status":"WITHIN_NORMAL_TEN_DAY_LIMIT",
                "last_completed_date":latest.isoformat(),"age_days":age,
                "source_network_called":False}
    if age>MAX_RESEARCH_BREAK_DAYS:
        raise StaleLeagueData("GAP_EXCEEDS_LIMIT_REQUIRES_REFRESH")
    if age<=0:
        raise StaleLeagueData("HISTORY_CONTAINS_FUTURE_RESULTS")
    resolve=_identity(league,resolver)
    # Final results only; never count unplayed future fixtures as completed.
    completed=[]
    upcoming=0
    for row in raw_rows:
        try:
            h=str(row.get("HomeTeam") or "").strip()
            a=str(row.get("AwayTeam") or "").strip()
            if not h and not a:continue
            if not h or not a:
                raise StaleLeagueData("PROVIDER_TEAM_FIELD_PARTIAL")
            day=date.fromisoformat(parse_date(row.get("Date","")))
            hg=_count(row.get("FTHG"))
            ag=_count(row.get("FTAG"))
            res=str(row.get("FTR") or "").strip()
        except (ValueError,TypeError) as exc:
            raise StaleLeagueData("PROVIDER_UNPARSABLE_DATE_OR_SCORE") from exc
        if hg is None and ag is None and not res:
            if day>=target:upcoming+=1
            continue
        if (hg is None or ag is None or hg<0 or ag<0 or hg>40 or ag>40
            or res!=("H" if hg>ag else "A" if hg<ag else "D")):
            raise StaleLeagueData("PROVIDER_PARTIAL_OR_BAD_COMPLETED_RESULT")
        if day>=target:
            # Same-day or future scores cannot train the prematch model.
            continue
        completed.append((day,h,a,hg,ag))
    if not completed or upcoming<1:
        # Explicit future fixtures provide a small guard against empty/truncated
        # season pages. Still NOT proof of complete federation coverage.
        raise StaleLeagueData("SOURCE_NO_SCHEDULE_OR_RESULTS")
    if len(completed)<len(hist):
        raise StaleLeagueData("SOURCE_SHORTER_THAN_ACCEPTED_CURRENT_SEASON")
    provider_latest=max(r[0] for r in completed)
    if provider_latest>latest:
        raise StaleLeagueData("NEW_COMPLETED_RESULTS_MUST_REFRESH_HISTORY")
    if provider_latest<latest:
        raise StaleLeagueData("PROVIDER_BEHIND_ACCEPTED_HISTORY")
    span=latest-timedelta(days=OVERLAP_DAYS)
    snapshot={}
    for r in hist:
        d=date.fromisoformat(r["match_date"])
        if span<=d<=latest:
            k=(d,r["home_id"],r["away_id"])
            score=(int(r["home_goals"]),int(r["away_goals"]))
            if k in snapshot or min(score)<0:
                raise StaleLeagueData("HISTORICAL_OVERLAP_NOT_UNIQUE")
            snapshot[k]=score
    if len(snapshot)<5:
        raise StaleLeagueData("TOO_FEW_OVERLAP_MATCHES")
    provider={}
    for d,h,a,hg,ag in completed:
        if not span<=d<=latest:continue
        hi=resolve(h)
        ai=resolve(a)
        if hi==ai:raise StaleLeagueData("PROVIDER_SAME_TEAM")
        k=(d,hi,ai)
        if k in provider:
            raise StaleLeagueData("PROVIDER_DUPLICATE_COMPLETED_FIXTURE")
        provider[k]=(hg,ag)
    if not set(snapshot).issubset(provider):
        raise StaleLeagueData("SOURCE_MISSING_ACCEPTED_OVERLAP_RESULTS")
    if any(provider[k]!=score for k,score in snapshot.items()):
        raise StaleLeagueData("SOURCE_CONFLICTS_WITH_ACCEPTED_SCORES")
    if set(provider)-set(snapshot):
        # Even a game BEFORE the last stored match may be absent: fail closed.
        raise StaleLeagueData("SOURCE_FOUND_UNRECORDED_OVERLAP_MATCHES")
    return {"schema":SCHEMA,
            "status":"BOUNDED_GAP_NO_MISSING_RESULTS_IN_PUBLIC_FEED_RESEARCH_ONLY",
            "source_network_called":True,
            "not_independent_federation_verified":True,
            "history_not_modified":True,
            "betting_authorized":False,
            "league":league,
            "age_days":age,
            "last_completed_date":latest.isoformat(),
            "target_date":target.isoformat(),
            "verified_at_utc":now.isoformat(),
            "provider_source_url":url,
            "provider_source_sha256":source_sha,
            "provider_completed_before_target":len(completed),
            "provider_last_result_date":provider_latest.isoformat(),
            "historical_overlap_matches_verified":len(snapshot),
            "next_unplayed_provider_fixtures":upcoming}

def review_gap(rows,league,target_date,*,now=None,fetcher=None,resolver=None):
    """Only call from a verified named fixture AFTER accepted snapshot SHA check."""
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise StaleLeagueData("AWARE_CLOCK_REQUIRED")
    now=now.astimezone(timezone.utc)
    try:
        target=date.fromisoformat(target_date)
        current=[date.fromisoformat(r["match_date"]) for r in rows
                 if r.get("league")==league and r.get("season")=="2026-2027"]
        if not current:
            raise StaleLeagueData("MISSING_CURRENT_SEASON")
        lag=(target-max(current)).days
    except (KeyError,ValueError,TypeError) as exc:
        raise StaleLeagueData("BAD_CURRENT_SEASON") from exc
    if lag<=MAX_DEFAULT_DAYS:
        if lag<=0: raise StaleLeagueData("FUTURE_OR_SAME_DAY_HISTORY")
        return {"schema":SCHEMA,"status":"WITHIN_NORMAL_TEN_DAY_LIMIT",
                "age_days":lag,"last_completed_date":max(current).isoformat(),
                "source_network_called":False}
    # Cache by league, local fixture day and latest snapshot date for a single
    # morning process, no duplication of public queries for same league.
    cache_key=(league,target_date,max(current).isoformat())
    cached=_CACHE.get(cache_key)
    if fetcher is None and resolver is None and cached is not None:
        observed,record=cached
        if 0 <= (now-observed).total_seconds()<=CACHE_MAX_AGE_SECONDS:
            return record
    if lag>MAX_RESEARCH_BREAK_DAYS:
        raise StaleLeagueData("GAP_EXCEEDS_LIMIT_REQUIRES_REFRESH")
    parsed,digest,url=_source(league,now=now,fetcher=fetcher)
    evidence=_compute(rows,league,target_date,now,parsed,digest,url,resolver=resolver)
    if fetcher is None and resolver is None:
        _CACHE[cache_key]=(now,evidence)
    return evidence
