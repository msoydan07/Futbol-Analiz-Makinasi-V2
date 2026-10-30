"""Stable identity registry for clubs and fixtures. Python standard library only."""
from __future__ import annotations
import json
import re
import unicodedata
import uuid
from pathlib import Path

NAMESPACE = uuid.UUID("0c312c79-42d1-4ca9-8b1c-4c65b96ef6b2")
LEAGUES = frozenset(("ENG1", "ENG2", "GER1", "ESP1", "ITA1", "FRA1", "NED1", "TUR1", "POR1", "BEL1"))
SEASONS = frozenset(("2025-2026", "2026-2027"))


def normalize(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Nonempty name required")
    value = unicodedata.normalize("NFKC", name).casefold()
    value = "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", value).strip()


def stable_id(kind: str, key: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{kind}:{key}"))


class Registry:
    """Persist this registry JSON between runs; never regenerate team keys from display names."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {
            "teams": {}, "aliases": {}, "fixtures": {}, "external_fixtures": {}
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temp.replace(self.path)

    def register_team(self, canonical_key: str, display_name: str, aliases=()) -> str:
        """canonical_key is a manually curated immutable identifier, e.g. 'galatasaray-sk'."""
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", canonical_key):
            raise ValueError("Canonical key must be lowercase ASCII slug")
        tid = stable_id("team", canonical_key)
        existing = self.data["teams"].get(tid)
        if existing and existing["key"] != canonical_key:
            raise ValueError("Team identity conflict")
        names = (display_name, *aliases)
        normalized = [normalize(n) for n in names]
        for name in normalized:
            owner = self.data["aliases"].get(name)
            if owner and owner != tid:
                raise ValueError(f"Ambiguous alias: {name}")
        self.data["teams"][tid] = {"key": canonical_key, "name": display_name}
        for name in normalized:
            self.data["aliases"][name] = tid
        return tid

    def set_official_team_name(self, team_id: str, official_name: str,
                               federation: str, evidence_url: str) -> None:
        """Promote an evidenced federation name to canonical display name.

        Team ID/key never change; previous display name remains an alias.
        """
        if team_id not in self.data["teams"]:
            raise KeyError("Unknown team ID")
        if not federation.strip() or not evidence_url.startswith(("https://", "http://")):
            raise ValueError("Federation and official evidence URL required")
        official = official_name.strip()
        normalized = normalize(official)
        owner = self.data["aliases"].get(normalized)
        if owner and owner != team_id:
            raise ValueError("Official name conflicts with another team")
        team = self.data["teams"][team_id]
        previous = team["name"]
        self.data["aliases"][normalize(previous)] = team_id
        self.data["aliases"][normalized] = team_id
        team["name"] = official
        team["verification"] = "FEDERATION_VERIFIED"
        team["official_name_source"] = federation.strip()
        team["official_name_evidence_url"] = evidence_url

    def resolve_team(self, name: str) -> str:
        key = normalize(name)
        if key not in self.data["aliases"]:
            raise KeyError(f"Unmapped team: {name}; manual review required")
        return self.data["aliases"][key]

    def add_team_alias(self, team_id: str, alias: str, source: str) -> None:
        """Attach a verified source-specific name without creating another club."""
        if team_id not in self.data["teams"]:
            raise KeyError("Unknown team ID")
        if not source.strip():
            raise ValueError("Alias source required")
        normalized = normalize(alias)
        owner = self.data["aliases"].get(normalized)
        if owner and owner != team_id:
            raise ValueError(f"Alias already belongs to another club: {alias}")
        self.data["aliases"][normalized] = team_id
        self.data.setdefault("alias_evidence", {})[json.dumps([source.strip().casefold(), normalized], ensure_ascii=False)] = team_id

    def register_dated_fixture(self, league: str, season: str, home_id: str, away_id: str,
                               match_date: str) -> str:
        """Date is initial matching evidence, never the permanent fixture identity.

        One home/away league fixture per season is expected for these domestic
        competitions. Date corrections retain the same ID. Ambiguous matches fail.
        """
        import datetime
        if league not in LEAGUES or season not in SEASONS:
            raise ValueError("Unsupported league or season")
        if home_id == away_id or home_id not in self.data["teams"] or away_id not in self.data["teams"]:
            raise ValueError("Invalid participants")
        datetime.date.fromisoformat(match_date)
        match_key = json.dumps([league, season, home_id, away_id], ensure_ascii=False)
        matches = [(fid, item) for fid, item in self.data["fixtures"].items()
                   if item["match_key"] == match_key]
        if len(matches) > 1:
            raise ValueError("Ambiguous duplicate fixture; manual review required")
        if matches:
            fid, fixture = matches[0]
            fixture["match_date"] = match_date
            return fid
        fid = stable_id("dated-league-fixture", match_key)
        self.data["fixtures"][fid] = {
            "match_key": match_key, "league": league, "season": season,
            "home_id": home_id, "away_id": away_id, "match_date": match_date,
            "kickoff": None, "source": "internal", "external_id": None,
            "identity_basis": "LEAGUE_SEASON_HOME_AWAY_DATE_MATCHED"
        }
        return fid

    def link_fixture_source(self, fixture_id: str, source: str, external_id: str) -> str:
        """Explicitly link another provider ID to a verified existing fixture.

        Never infer fixture identity solely from teams/date: cup or replay
        matches can share participants. Manual/source-backed confirmation required.
        """
        if fixture_id not in self.data["fixtures"]:
            raise KeyError("Unknown canonical fixture")
        if not source.strip() or not str(external_id).strip():
            raise ValueError("Stable source fixture ID required")
        key = json.dumps([source.strip().casefold(), str(external_id).strip()], ensure_ascii=False)
        existing = self.data["external_fixtures"].get(key)
        if existing and existing != fixture_id:
            raise ValueError("Provider fixture ID already linked to another match")
        self.data["external_fixtures"][key] = fixture_id
        return fixture_id

    def register_fixture(self, league: str, season: str, home_id: str, away_id: str,
                         source: str, external_id: str, kickoff: str | None = None) -> str:
        """Source fixture ID is mandatory; kickoff is metadata and can change."""
        if league not in LEAGUES or season not in SEASONS:
            raise ValueError("Unsupported league or season")
        if home_id == away_id or home_id not in self.data["teams"] or away_id not in self.data["teams"]:
            raise ValueError("Invalid participants")
        if not source.strip() or not str(external_id).strip():
            raise ValueError("Stable source fixture ID required")
        external_key = json.dumps([source.strip().casefold(), str(external_id).strip()], ensure_ascii=False)
        match_key = json.dumps([league, season, home_id, away_id], ensure_ascii=False)
        existing_id = self.data["external_fixtures"].get(external_key)
        if existing_id:
            existing = self.data["fixtures"][existing_id]
            if existing["match_key"] != match_key:
                raise ValueError("Source fixture ID reused for different match")
            existing["kickoff"] = kickoff
            return existing_id
        fixture_id = stable_id("fixture", external_key)
        self.data["fixtures"][fixture_id] = {
            "match_key": match_key, "league": league, "season": season,
            "home_id": home_id, "away_id": away_id, "kickoff": kickoff,
            "source": source, "external_id": str(external_id)
        }
        self.data["external_fixtures"][external_key] = fixture_id
        return fixture_id
