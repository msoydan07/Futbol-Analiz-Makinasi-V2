"""Read-only 7-day workload evidence for one PDF-first official fixture.

This module does NOT fetch another URL, fabricate a missed match, verify a
competition by its domain alone, or change B/C2/C3/M4 probabilities. It can
only reuse the already fetched official *league* fixture payload.

UEFA and national cups require separate evidence which the current one-fetch
PDF-first adapter does not provide: mark those schedules INCOMPLETE.
"""
from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime,timedelta,timezone

from iddaa_pdf_team_alias_preflight_263 import resolve_label
from mackolik_identity_gate_263 import _official
from sabah_fixture_rotation_263 import rotation_from_official_inputs


SCHEMA="263_PDF_OFFICIAL_SAME_PAGE_ADJACENT_V1"
WINDOW="ANALYSIS_REQUEST_PLUS_MINUS_SEVEN_DAYS"


def _aware(value):
    if not isinstance(value,str):
        raise ValueError("WORKLOAD_EVENT_TIMESTAMP_REQUIRED")
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None:raise ValueError("WORKLOAD_EVENT_AWARE_TIMESTAMP_REQUIRED")
    return dt.astimezone(timezone.utc)


def page_sha(payload):
    if isinstance(payload,str):
        raw=payload.encode("utf-8")
    else:
        raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,
                       separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _canonical(league,label,index):
    mapped=resolve_label(league,label,index)
    if mapped.get("status")!="MAPPED":
        return None
    return mapped.get("team_id")


def collect_same_page(league,home_id,away_id,events,*,source_url,
                      retrieved_at_utc,source_payload,index):
    """Whitelist unique canonical league events from the exact fetched page.

    If two observations assign conflicting kickoffs to the same pair,
    remove both rather than presenting arbitrary rota/rest assumptions.
    The returned proof is informational; no source page means no data.
    """
    if not isinstance(events,list) or len(events)>500:
        raise ValueError("ADJACENT_SOURCE_EVENT_COUNT_INVALID")
    if not _official(source_url,league):
        raise ValueError("ADJACENT_SOURCE_NOT_OFFICIAL_FOR_LEAGUE")
    now=_aware(retrieved_at_utc)
    first,last=now-timedelta(days=7),now+timedelta(days=7)
    by_pair={}
    conflicts=set()
    for row in events:
        if not isinstance(row,dict) or row.get("format")=="epl":
            continue  # provisional annual league fixtures are not verified KO
        h=_canonical(league,row.get("home"),index)
        a=_canonical(league,row.get("away"),index)
        if h is None or a is None or h==a:
            continue
        # The requested fixture itself is NEVER an adjacent game. A league
        # round page necessarily contains that row; treating it as future
        # rotation would create a spurious zero-hour rest/extra-match alert.
        if {h,a}=={home_id,away_id}:
            continue
        try:dt=_aware(row.get("kickoff_utc"))
        except (ValueError,TypeError,OverflowError):
            continue
        if not (first<=dt<now or now<dt<=last):
            continue
        pair=(h,a)
        if pair in by_pair and by_pair[pair]!=dt:
            conflicts.add(pair)
        else:
            by_pair[pair]=dt
    adjacent=[]
    for (h,a),dt in sorted(by_pair.items(),key=lambda x:(x[1],x[0])):
        if (h,a) in conflicts:
            continue
        for team,opponent in ((h,a),(a,h)):
            if team not in (home_id,away_id):
                continue
            adjacent.append({
                "team_id":team,"opponent":opponent,
                "kickoff_utc":dt.isoformat(),"competition":"LIG",
                "verification":"VERIFIED_OFFICIAL_ADAPTER",
                "source_url":source_url
            })
    return {
        "schema":SCHEMA,"source":"SAME_FETCHED_OFFICIAL_LEAGUE_PAGE",
        "source_url":source_url,
        "source_payload_sha256":page_sha(source_payload),
        "retrieved_at_utc":now.isoformat(),
        "coverage":"PARTIAL_LEAGUE_EVENTS_ONLY",
        "uefa_and_cups_verified":False,
        "verified_adjacent_league_events":adjacent
    }


def workload_for_pdf(observation,verified,league,home_id,away_id,now):
    """Produce one fail-closed, non-forecast rotation sidecar per verified row.

    No extra HTTP calls and no second bookmaker lookup; missing evidence is
    visibly UNKNOWN. The model's sealed probability fields are never touched.
    """
    gate={
        "status":"VERIFIED","league":league,
        "home_id":home_id,"away_id":away_id,
        "source_url":verified["source_url"],
        "kickoff_utc":verified["kickoff_utc"],
    }
    accepted=[]
    status="OFFICIAL_ADJACENT_LEAGUE_DATA_UNAVAILABLE"
    source_sha=None
    try:
        proof=observation.get("adjacent_league_evidence") if isinstance(observation,dict) else None
        if proof is not None:
            if not isinstance(proof,dict) or proof.get("schema")!=SCHEMA:
                raise ValueError("WORKLOAD_WRONG_ADJACENT_SCHEMA")
            if (proof.get("source")!="SAME_FETCHED_OFFICIAL_LEAGUE_PAGE"
                or proof.get("source_url")!=verified["source_url"]
                or not _official(proof["source_url"],league)
                or proof.get("retrieved_at_utc")!=verified["retrieved_at_utc"]
                or proof.get("uefa_and_cups_verified") is not False
                or proof.get("coverage")!="PARTIAL_LEAGUE_EVENTS_ONLY"):
                raise ValueError("WORKLOAD_PROVENANCE_DOES_NOT_MATCH_TARGET")
            digest=proof.get("source_payload_sha256")
            if not isinstance(digest,str) or re.fullmatch("[0-9a-f]{64}",digest) is None:
                raise ValueError("WORKLOAD_SOURCE_SHA_INVALID")
            event_rows=proof.get("verified_adjacent_league_events")
            if not isinstance(event_rows,list) or len(event_rows)>100:
                raise ValueError("WORKLOAD_ADJACENT_EVENT_LIST_INVALID")
            for event in event_rows:
                if not isinstance(event,dict):
                    raise ValueError("WORKLOAD_ADJACENT_EVENT_INVALID")
                if (event.get("competition")!="LIG"
                    or event.get("verification")!="VERIFIED_OFFICIAL_ADAPTER"
                    or event.get("source_url")!=verified["source_url"]
                    or event.get("team_id") not in (home_id,away_id)
                    or not isinstance(event.get("opponent"),str)
                    or event.get("opponent") in (home_id,away_id)):
                    raise ValueError("WORKLOAD_ADJACENT_EVENT_MISMATCH")
                _aware(event.get("kickoff_utc"))
            accepted=event_rows
            source_sha=digest
            status="VERIFIED_SAME_PAGE_LEAGUE_PARTIAL"
    except (KeyError,TypeError,ValueError,OverflowError):
        accepted=[]
        source_sha=None
        status="ADJACENT_SOURCE_REJECTED_DATA_INCOMPLETE"
    rotation=rotation_from_official_inputs(gate,accepted,now)
    return {
        "schema":"263_PDF_7DAY_WORKLOAD_V1",
        "status":status,
        "window_basis":rotation["window_basis"],
        "analysis_requested_at_utc":rotation["analysis_requested_at_utc"],
        "window_previous_utc":rotation["window_previous_utc"],
        "window_next_utc":rotation["window_next_utc"],
        "source_payload_sha256":source_sha,
        "league_schedule_complete":False,
        "uefa_and_cup_schedule_complete":False,
        "source_coverage_excludes_unverified_cups":True,
        "teams":rotation["teams"],
        "model_probabilities_changed":False,
        "new_odds_network_calls":0,
        "new_official_network_calls":0,
    }

