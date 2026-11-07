"""Fresh official-source fixture batch gateway for 2.6.3 morning analyses.

Per league official page is fetched at most once per ten-minute window.
Only canonical IDs may match team names. A date-only or ambiguous official
observation NEVER becomes a confirmed kickoff. Existing live named-match
adapter is a fallback. Adjacent league fixtures are qualitative only;
missing European/cup schedules remain explicitly incomplete.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from official_page_lookup_263 import (
    SOURCES,is_approved_url,_default_fetch,parse_official_events,official_page_lookup)
from sabah_fixture_rotation_263 import COMPETITIONS

SCHEMA="SABAH_RESMI_FIKSTUR_KAYNAK_TARAMA_V1"
CACHE_SECONDS=600
class OfficialGatewayError(ValueError): pass

class OfficialFixtureGateway:
    def __init__(self,*,fetcher=None,resolve_id=None,gate_runner=None,clock=None):
        self.fetcher=fetcher or _default_fetch
        self.clock=clock or (lambda:datetime.now(timezone.utc))
        if gate_runner is None:
            from analyze_named_match_gate import run as gate_runner
        self.gate_runner=gate_runner
        if resolve_id is None:
            from identity import Registry
            from team_name_resolver import resolve as canonical
            registry=Registry("experiments/263/evidence/identity_index_263.json")
            # Preserve immutable 2026-27 membership gate used by named-match entry.
            from importlib import import_module
            identity=import_module("experiments.263.mackolik_identity_gate_263")
            identity._validate_identity_source(registry.data)
            memberships=identity._memberships(registry.data,"2026-2027")
            def resolve_id(league,name):
                club=canonical(registry,league,name)
                if club not in memberships.get(league,set()):
                    raise ValueError("NOT_IN_CURRENT_LEAGUE_IDENTITY_REGISTRY")
                return club
        self.resolve_id=resolve_id
        self.cache={}
        self.match_checks=[]

    def now(self):
        instant=self.clock()
        if instant.tzinfo is None:raise OfficialGatewayError("NAIVE_CLOCK_FORBIDDEN")
        return instant.astimezone(timezone.utc)

    def _get(self,league):
        if league not in SOURCES:raise OfficialGatewayError("UNSUPPORTED_LEAGUE")
        now=self.now()
        old=self.cache.get(league)
        if old is not None and (now-old["fetched_at"]).total_seconds()<CACHE_SECONDS:
            return old
        url=SOURCES[league][0]
        entry={"league":league,"source_url":url,"status":"NOT_VERIFIED",
               "fetched_at":now,"events":[],"html":None,"html_sha256":None,
               "reason":"UNAVAILABLE","effective_url":None}
        try:
            if not is_approved_url(url,league):
                raise OfficialGatewayError("SOURCE_NOT_APPROVED")
            effective,html=self.fetcher(url,league)
            if not is_approved_url(effective,league):
                raise OfficialGatewayError("REDIRECT_OUTSIDE_OFFICIAL_DOMAIN")
            if not isinstance(html,str) or not html or len(html)>2_000_000:
                raise OfficialGatewayError("INVALID_OFFICIAL_DOCUMENT")
            events=parse_official_events(league,html)
            entry.update(status="FETCHED_OFFICIAL_PAGE",reason=None,
                         effective_url=effective,events=events,html=html,
                         html_sha256=hashlib.sha256(html.encode("utf-8")).hexdigest())
        except (OSError,ValueError,TypeError,TimeoutError) as exc:
            entry["reason"]=type(exc).__name__+":"+str(exc)[:90]
        self.cache[league]=entry
        return entry

    def _same(self,league,left,right):
        try:
            return self.resolve_id(league,left)==self.resolve_id(league,right)
        except (KeyError,TypeError,ValueError):
            return False

    def lookup(self,league,home,away):
        """Call the existing official + canonical identity gate, never bypass it."""
        entry=self._get(league)
        evidence={"league":league,"requested_home":home,"requested_away":away,
                  "page_fetch_status":entry["status"],
                  "page_url":entry["effective_url"] or entry["source_url"],
                  "page_sha256":entry["html_sha256"],
                  "source_parser":SOURCES[league][2],
                  "candidate_events_seen":len(entry["events"]),
                  "page_fetch_failure":entry["reason"],
                  "selected_lookup":"NONE"}
        observation=None
        if entry["status"]=="FETCHED_OFFICIAL_PAGE":
            observation=official_page_lookup(
                league,home,away,now=self.now(),
                source_url=entry["effective_url"],html=entry["html"],
                same_team=lambda x,y:self._same(league,x,y))
            evidence["page_observation_status"]=observation.get("status")
            evidence["page_observation_reason"]=observation.get("reason")
            # An official annual Premier League list with provisional kickoff
            # must not be promoted to a fully verified date/time.
            if observation.get("status")=="VERIFIED_OFFICIAL_FIXTURE":
                checked=dict(observation)
                checked["source_origin"]="FETCHED_OFFICIAL_PAGE_BATCH_CACHE"
                gate=self.gate_runner(league,home,away,
                      lookup_override=lambda _home,_away:checked)
                if isinstance(gate,dict) and gate.get("status")=="VERIFIED":
                    evidence["selected_lookup"]="CACHED_OFFICIAL_PAGE_AND_CANONICAL_GATE"
                    self.match_checks.append(evidence)
                    return gate
                evidence["page_gate_rejected"]=gate.get("reason") if isinstance(gate,dict) else "INVALID_GATE"
        # The older September 2026 French TV bulletin conflicts with the
        # newer November official matchweek briefing on Saturday kickoffs.
        # Never silently recover FRA1 from its now-stale fallback adapter.
        if league=="FRA1":
            evidence["selected_lookup"]="BLOCKED_OLD_FRENCH_SCHEDULE"
            self.match_checks.append(evidence)
            return {"status":"NOT_VERIFIED",
                    "reason":"NEWER_FRA1_OFFICIAL_MATCHWEEK_PAGE_REQUIRED"}
        # Other old official league-specific adapters remain a verified
        # fallback where the cached page does not expose the match/time.
        gate=self.gate_runner(league,home,away)
        if isinstance(gate,dict) and gate.get("status")=="VERIFIED":
            evidence["selected_lookup"]="EXISTING_LIVE_NAMED_MATCH_GATE"
        else:
            evidence["selected_lookup"]="BLOCKED_UNVERIFIED"
        self.match_checks.append(evidence)
        return gate

    def latest_match_evidence(self,league,home,away):
        return next((dict(x) for x in reversed(self.match_checks)
                     if x["league"]==league and x["requested_home"]==home
                     and x["requested_away"]==away),None)

    def adjacent_for(self,gate):
        """Return only uniquely paired timed official *league* fixtures.

        This deliberately does NOT assert UEFA or domestic cup completeness.
        League schedules are insufficient to infer absence of rotation risk.
        """
        league=gate.get("league")
        if league not in self.cache:return []
        entry=self.cache[league]
        if entry["status"]!="FETCHED_OFFICIAL_PAGE":return []
        kickoff=datetime.fromisoformat(gate["kickoff_utc"].replace("Z","+00:00")).astimezone(timezone.utc)
        target={gate["home_id"],gate["away_id"]}
        candidates={}
        conflict=set()
        for e in entry["events"]:
            iso=e.get("kickoff_utc")
            if not iso or e.get("format")=="epl":continue
            try:
                t=datetime.fromisoformat(iso.replace("Z","+00:00"))
                if t.tzinfo is None:continue
                t=t.astimezone(timezone.utc)
                if not kickoff-timedelta(days=7)<=t<=kickoff+timedelta(days=10):continue
                home=self.resolve_id(league,e["home"])
                away=self.resolve_id(league,e["away"])
                if home==away:continue
            except (KeyError,TypeError,ValueError):
                continue
            pair=(home,away)
            if pair in candidates and candidates[pair][0]!=t:
                conflict.add(pair);continue
            candidates[pair]=(t,e)
        adjacent=[]
        for pair,(t,e) in candidates.items():
            if pair in conflict or t==kickoff:continue
            for team,other in ((pair[0],pair[1]),(pair[1],pair[0])):
                if team not in target:continue
                adjacent.append({
                    "team_id":team,"opponent":other,
                    "kickoff_utc":t.isoformat(),
                    "competition":"LIG",
                    "verification":"VERIFIED_OFFICIAL_ADAPTER",
                    "source_url":entry["effective_url"]})
        return adjacent

    def coverage(self):
        return {league:{"status":d["status"],"source_url":d["effective_url"] or d["source_url"],
                        "page_sha256":d["html_sha256"],"parsed_events":len(d["events"]),
                        "failure":d["reason"],
                        "all_competitions_covered":False,
                        "league_fixtures_complete":False}
                for league,d in sorted(self.cache.items())}
