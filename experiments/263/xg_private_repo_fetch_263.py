"""Read-only owner-private xG transport to a non-repository runner temp directory.

No raw private data, token, per-match provider xG, or sidecar contents are
printed, committed, cached, uploaded as Actions artifacts, or retained here.
Absence, revoked credentials, bad CSV, or wrong SHA keeps existing M4 unchanged.

Uses GitHub Contents metadata + Git Blob API because pinned CSV is >1MB;
Contents response by itself can omit base64 payload for larger files.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from m4_xg_operational_gate_263 import private_data_preflight, EXPECTED_SHA

PRIVATE_REPO = "msoydan07/Futbol-263-XG-Private"
PRIVATE_REF = "main"
PRIVATE_FILE = "FUTBOL_263_4618_XG_KILITLI_20261119(1).csv"
EXPECTED_SIZE = 2071704
MAX_BYTES = 4000000
READY = "PRIVATE_XG_SHA_AND_SCOPE_VERIFIED"
STATUS_SCHEMA = "263_XG_PRIVATE_REPO_BRIDGE_V1"


def _get_json(endpoint, token):
    """Only endpoints supplied by this fixed program, no user-defined URL."""
    req = Request("https://api.github.com" + endpoint, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "m4-xg-private-readonly-bridge",
    })
    with urlopen(req, timeout=20) as response:
        payload = response.read(7_000_001)
    if len(payload) > 7_000_000:
        raise ValueError("API_RESPONSE_OVERSIZE")
    return json.loads(payload)


def _git_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def _status(label, **extra):
    return {"schema": STATUS_SCHEMA, "status": label,
            "private_repo": PRIVATE_REPO,
            "private_data_in_public_checkout": False,
            "raw_xg_in_logs_or_artifacts": False,
            "official_m4_modified": False, **extra}


def retrieve(*, token, target, public_checkout, expected_sha=EXPECTED_SHA,
             expected_size=EXPECTED_SIZE, expected_rows=4618):
    """Return only non-sensitive readiness, never the bytes or token."""
    path = Path(target).resolve()
    checkout = Path(public_checkout).resolve()
    if path.is_relative_to(checkout):
        raise ValueError("PRIVATE_XG_TARGET_INSIDE_PUBLIC_CHECKOUT")
    if not token:
        return _status("PRIVATE_REPO_READ_TOKEN_NOT_CONFIGURED")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise ValueError("INVALID_LOCKED_XG_SHA")
    if path.exists():
        raise ValueError("PRIVATE_XG_TARGET_ALREADY_EXISTS")

    # Contents metadata gives the Git blob SHA even for files above 1 MiB.
    # Only constant stages and a numeric HTTP category are ever printed.
    stage = "CONTENTS_METADATA"
    try:
        metadata = _get_json(
            "/repos/" + PRIVATE_REPO + "/contents/" + PRIVATE_FILE + "?ref=" + PRIVATE_REF,
            token)
        if (metadata.get("type") != "file" or
            metadata.get("path") != PRIVATE_FILE or
            metadata.get("size") != expected_size or
            not re.fullmatch(r"[0-9a-f]{40}", str(metadata.get("sha", "")))):
            return _status("PRIVATE_REPO_XG_FILE_MISSING_OR_DIFFERENT_SIZE")

        blob_sha = metadata["sha"]
        stage = "GIT_BLOB"
        blob = _get_json("/repos/" + PRIVATE_REPO + "/git/blobs/" + blob_sha, token)
        if (blob.get("encoding") != "base64" or
            blob.get("sha") != blob_sha or
            blob.get("size") != expected_size):
            return _status("PRIVATE_REPO_BLOB_METADATA_MISMATCH")
        stage = "BLOB_DECODE"
        data = base64.b64decode(blob["content"], validate=False)
        if len(data) != expected_size or len(data) > MAX_BYTES:
            return _status("PRIVATE_REPO_XG_SIZE_INVALID")
        if _git_sha(data) != blob_sha:
            return _status("PRIVATE_REPO_BLOB_GIT_SHA_MISMATCH")
        if hashlib.sha256(data).hexdigest() != expected_sha:
            return _status("PRIVATE_REPO_XG_LOCKED_SHA_MISMATCH")

        stage = "LOCAL_SCOPE"
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=".xg-private-")
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            result = private_data_preflight(
                temp_path, checkout, expected_sha=expected_sha,
                expected_n=expected_rows)
            if result["status"] != "PRIVATE_XG_READABLE_IN_CHATGPT_ENVIRONMENT":
                return _status("PRIVATE_REPO_XG_SCHEMA_OR_SCOPE_REJECTED")
            os.replace(temp_path, path)
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
        return _status(READY, record_count=expected_rows,
                       dataset_sha256=expected_sha)
    except HTTPError as exc:
        # Only fixed stage and numeric HTTP category; never print private
        # request/response metadata, provider data, URL or token.
        safe_code = exc.code if exc.code in (400, 401, 403, 404, 409, 422, 429, 500, 502, 503) else 0
        return _status("PRIVATE_REPO_" + stage + "_HTTP_" + str(safe_code) + "_KEEP_M4")
    except URLError:
        return _status("PRIVATE_REPO_" + stage + "_NETWORK_UNAVAILABLE_KEEP_M4")
    except (OSError, ValueError, KeyError, TypeError,
            binascii.Error, json.JSONDecodeError):
        return _status("PRIVATE_REPO_" + stage + "_LOCAL_OR_FORMAT_ERROR_KEEP_M4")


def main():
    p = argparse.ArgumentParser(description="GitHub token-scoped read-only xG import")
    p.add_argument("--target", required=True)
    p.add_argument("--public-checkout", default=".")
    p.add_argument("--status-json", required=True)
    args = p.parse_args()
    status_path = Path(args.status_json).resolve()
    if status_path.is_relative_to(Path(args.public_checkout).resolve()):
        raise SystemExit("PRIVATE_STATUS_JSON_MUST_BE_OUTSIDE_CHECKOUT")
    state = retrieve(token=os.environ.get("XG_PRIVATE_REPO_READ_TOKEN", ""),
                     target=args.target, public_checkout=args.public_checkout)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    with status_path.open("x", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print("PRIVATE_XG_BRIDGE_STATUS=" + state["status"])


if __name__ == "__main__":
    main()
