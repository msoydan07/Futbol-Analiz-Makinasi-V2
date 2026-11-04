"""Research-only full-match exposure policy; raw source snapshots are never rewritten.

Official awarded scores are retained in the immutable archive. A match that
did not run its normal scheduled duration is excluded from *full-match*
90-minute model fitting and empirical baseline rates, rather than imputed.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

POLICY_PATH=Path(__file__).resolve().parents[2]/"data/staged_263/2026_10_31_ned1_abandoned_awarded_exception.json"
REQUIRED={"league":"NED1","match_date":"2026-10-31","home_goals":"4","away_goals":"0","result":"H"}

def full_match_rows(rows):
    """Return (eligible rows, excluded IDs, policy SHA); fail closed on conflicting row."""
    raw=POLICY_PATH.read_bytes()
    policy=json.loads(raw)
    if (policy.get("schema")!="263_match_completion_exception_v1"
        or policy.get("completion")!="ABANDONED_AT_APPROX_MINUTE_81_RESULT_AWARDED_AS_FINAL"
        or policy.get("final_score_valid") is not True
        or policy.get("normal_full_match_exposure") is not False
        or policy.get("training_eligibility_enforced") is not True):
        raise ValueError("INCOMPLETE_MATCH_POLICY_NOT_ACTIVE")
    ident=policy.get("fixture_id")
    if not isinstance(ident,str) or len(ident)!=36:
        raise ValueError("INVALID_INCOMPLETE_MATCH_ID")
    matches=[row for row in rows if row.get("fixture_id")==ident]
    if len(matches)>1:
        raise ValueError("DUPLICATE_INCOMPLETE_MATCH")
    if matches:
        if any(str(matches[0].get(key))!=val for key,val in REQUIRED.items()):
            raise ValueError("INCOMPLETE_MATCH_SOURCE_MISMATCH")
    kept=[row for row in rows if row.get("fixture_id")!=ident]
    return kept, ([ident] if matches else []), hashlib.sha256(raw).hexdigest()
