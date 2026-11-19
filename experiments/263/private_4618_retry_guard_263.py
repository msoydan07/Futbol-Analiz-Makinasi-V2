"""Append-only retry for same first PDF ONLY if zero immutable forecasts existed."""
from __future__ import annotations
import json
from pathlib import Path

class UnsafeRetry(ValueError):pass

def _has_seal(folder):
    if any((folder/'forecasts').glob('*/*.json')):return True
    old=folder/'source_session.json'
    if old.exists():
        try:
            r=json.loads(old.read_text(encoding='utf-8'))
            return bool(r.get('n_forecast') or any(
                (x.get('model_forecast_created') or x.get('model_forecast_sha256'))
                for x in r.get('rows',[]) if isinstance(x,dict)))
        except (TypeError,ValueError,KeyError) as exc:
            raise UnsafeRetry('UNREADABLE_PREVIOUS_SESSION_NO_RETRY') from exc
    return False

def select_attempt(root,pdf_sha,*,verify_completed,max_attempts=8):
    if (not isinstance(pdf_sha,str) or len(pdf_sha)!=64 or
        any(x not in '0123456789abcdef' for x in pdf_sha)):
        raise UnsafeRetry('VALID_SOURCE_PDF_SHA_REQUIRED')
    if not callable(verify_completed):raise UnsafeRetry('VERIFIED_COMPLETION_READER_REQUIRED')
    parent=Path(root);prefix=pdf_sha[:20]
    for i in range(1,max_attempts+1):
        folder=parent/(prefix if i==1 else prefix+'-retry-'+str(i))
        if not folder.exists():
            return {'action':'CREATE_NEW_ATTEMPT','folder':folder,'attempt':i}
        if not folder.is_dir():raise UnsafeRetry('ATTEMPT_PATH_NOT_DIRECTORY')
        if (folder/'completed_receipt.json').is_file():
            # Verifier must check source+report bytes and signed receipt hash.
            old=verify_completed(folder,pdf_sha)
            sealed=_has_seal(folder)
            if sealed:return {'action':'REUSE_SEALED','folder':folder,'attempt':i,'existing':old}
            if old.get('signed_four_model_forecasts',0):
                raise UnsafeRetry('SEALED_RECEIPT_MISSING_FORECAST_FILES')
            # No prior prediction exists: new append-only session is safe.
            continue
        if _has_seal(folder):
            raise UnsafeRetry('INCOMPLETE_SEALED_SESSION_NEVER_RETRY')
        # Preserve the no-seal previous attempt on disk and use a new folder.
    raise UnsafeRetry('UNSEALED_RETRY_LIMIT_REACHED_MANUAL_REVIEW')
