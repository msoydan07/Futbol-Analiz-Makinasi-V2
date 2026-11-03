"""M4 research-only, locally private as-of xG snapshot intake.

No network fetch; no public artifact upload; no model calculation or promotion.
A local capture is NOT independent proof of provider publication time or licensing.
Always require a separately verifiable timestamp anchor and rights approval before
claiming production-grade historical as-of evidence.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import secrets
import stat
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "263_M4_PRIVATE_XG_SNAPSHOT_V1"
FIELDS = {"fixture_id", "league", "season", "match_date", "home_id", "away_id",
          "home_xg", "away_xg", "understat_source_url"}
MAX_INPUT_BYTES = 15_000_000

class SnapshotGateError(ValueError):
    pass


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise SnapshotGateError("utc_aware_datetime_required")
    return value.astimezone(timezone.utc)


def _url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    try:
        p = urlsplit(url)
        return p.scheme == "https" and bool(p.hostname) and p.username is None \
            and p.password is None and p.port in (None, 443)
    except ValueError:
        return False


def _rows(payload: bytes, observed: datetime) -> list[dict]:
    if not isinstance(payload, bytes) or not 0 < len(payload) <= MAX_INPUT_BYTES:
        raise SnapshotGateError("invalid_snapshot_payload_size")
    try:
        text = payload.decode("utf-8-sig")
        rdr = csv.DictReader(io.StringIO(text))
        if not FIELDS.issubset(rdr.fieldnames or ()):
            raise SnapshotGateError("missing_audited_xg_columns")
        rows = list(rdr)
    except UnicodeDecodeError as exc:
        raise SnapshotGateError("invalid_snapshot_encoding") from exc
    if not rows:
        raise SnapshotGateError("empty_xg_rows")
    seen = set()
    for r in rows:
        fid = r["fixture_id"]
        if not fid or fid in seen:
            raise SnapshotGateError("duplicate_or_missing_fixture_id")
        seen.add(fid)
        try:
            match_date = date.fromisoformat(r["match_date"])
        except (TypeError, ValueError) as exc:
            raise SnapshotGateError("invalid_match_date") from exc
        # Conservative day-only rule: no same-day or future observations.
        if match_date >= observed.date():
            raise SnapshotGateError("not_prior_date_snapshot_row")
        if not r["league"] or not r["home_id"] or not r["away_id"] or r["home_id"] == r["away_id"]:
            raise SnapshotGateError("invalid_identity_claim")
        if not _url(r["understat_source_url"]):
            raise SnapshotGateError("invalid_row_source_url")
        for key in ("home_xg", "away_xg"):
            try:
                n = float(r[key])
            except (ValueError, TypeError) as exc:
                raise SnapshotGateError("invalid_xg_number") from exc
            if not math.isfinite(n) or n < 0 or n > 15:
                raise SnapshotGateError("invalid_xg_range")
    return rows


def _private_dir(location: str | Path) -> Path:
    path = Path(location).expanduser().resolve()
    for p in (path, *path.parents):
        if (p / ".git").exists():
            raise SnapshotGateError("private_store_must_be_outside_git_checkout")
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    if not path.is_dir() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise SnapshotGateError("private_store_permissions_not_restricted")
    return path


def _write_once(path: Path, payload: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def capture_xg_snapshot(*, payload: bytes, private_store: str | Path,
                        provider: str, source_url: str, rights_evidence_ref: str,
                        synthetic_test: bool = False,
                        _test_clock: datetime | None = None) -> dict:
    """Store an audited CSV copy locally, append-only. Rights claim is NOT vetted.

    Provider retrieval must already have occurred legitimately upstream; this
    deliberately does not contact providers or publish their data to GitHub.
    """
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true" and not synthetic_test:
        raise SnapshotGateError("public_actions_raw_provider_storage_forbidden")
    if _test_clock is not None and not synthetic_test:
        raise SnapshotGateError("clock_override_not_allowed")
    now = _utc(_test_clock if _test_clock is not None else datetime.now(timezone.utc))
    if not provider or not _url(source_url):
        raise SnapshotGateError("source_provenance_missing")
    if not isinstance(rights_evidence_ref, str) or not rights_evidence_ref.strip():
        raise SnapshotGateError("rights_evidence_reference_required")
    rows = _rows(payload, now)
    store = _private_dir(private_store)
    ident = secrets.token_hex(16)
    raw = store / f"{ident}.csv"
    manifest_path = store / f"{ident}.json"
    manifest = {
        "schema": SCHEMA, "snapshot_id": ident, "provider": provider,
        "source_url": source_url, "source_observed_utc": now.isoformat(),
        "csv_sha256": hashlib.sha256(payload).hexdigest(), "row_count": len(rows),
        "rights_evidence_ref": rights_evidence_ref.strip(),
        "rights_status": "OPERATOR_REFERENCE_ONLY_NOT_INDEPENDENTLY_VERIFIED",
        "vintage_status": "LOCAL_OBSERVATION_NOT_EXTERNALLY_ANCHORED",
        "external_timestamp_anchor": None,
        "scope": "PRIVATE_RESEARCH_ONLY_NO_MODEL_INPUT", "retraining_performed": False,
    }
    try:
        _write_once(raw, payload)
        _write_once(manifest_path, (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode())
    except BaseException:
        raw.unlink(missing_ok=True)
        raise
    return manifest


def inspect_for_target(*, private_store: str | Path, snapshot_id: str,
                       target_kickoff_utc: datetime, league: str) -> dict:
    """Fail closed; report coverage only, never expose match-level provider data."""
    if len(snapshot_id) != 32 or any(c not in "0123456789abcdef" for c in snapshot_id):
        raise SnapshotGateError("bad_snapshot_id")
    target = _utc(target_kickoff_utc)
    store = _private_dir(private_store)
    manifest_path = store / f"{snapshot_id}.json"
    raw_path = store / f"{snapshot_id}.csv"
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    if m.get("schema") != SCHEMA or m.get("snapshot_id") != snapshot_id:
        raise SnapshotGateError("manifest_schema_mismatch")
    captured = _utc(datetime.fromisoformat(m["source_observed_utc"]))
    if captured >= target:
        raise SnapshotGateError("snapshot_not_observed_before_kickoff")
    payload = raw_path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != m.get("csv_sha256"):
        raise SnapshotGateError("snapshot_payload_hash_changed")
    rows = _rows(payload, captured)
    if len(rows) != m.get("row_count"):
        raise SnapshotGateError("snapshot_row_count_changed")
    # For date-only match inputs exclude the target calendar day entirely.
    eligible = sum(r["league"] == league and r["match_date"] < target.date().isoformat() for r in rows)
    return {
        "status": "LOCAL_ASOF_RESEARCH_CANDIDATE_EXTERNAL_PROOF_MISSING",
        "snapshot_id": snapshot_id,
        "source_observed_utc": captured.isoformat(),
        "target_kickoff_utc": target.isoformat(),
        "historical_same_league_rows_before_target_date": eligible,
        "raw_values_exported": False,
        "external_time_anchor_verified": False,
        "rights_independently_verified": False,
        "approved_for_live_model": False,
        "model_predictions_written": False,
    }
