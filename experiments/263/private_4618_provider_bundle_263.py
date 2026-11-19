"""Private source-byte bundle for 4,618 score research. Only SECONDARY results witness.

No odds fetching, no production admissions. The operator entrypoint calls
create_witnesses with its real network fetcher; injected fetches are test-only.
"""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from public_provider_2627_gap_audit_263 import SOURCES,BASE,fetch_source,witness_source
from private_4618_matchday_preflight_263 import verify_private_projection

SCHEMA='263_PRIVATE_4618_PROVIDER_BYTES_SESSION_V1'
class WitnessBlocked(ValueError):pass

def _hash(data):return hashlib.sha256(data).hexdigest()
def _canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def _utc(value):
    try:
        dt=(value if isinstance(value,datetime) else
            datetime.fromisoformat(str(value).replace('Z','+00:00')))
        if dt.tzinfo is None:raise ValueError('naive')
        return dt.astimezone(timezone.utc)
    except (ValueError,TypeError) as exc:raise WitnessBlocked('AWARE_TIMESTAMP_REQUIRED') from exc

def create_witnesses(*,legacy,projection,bulletin,destination,now=None,fetcher=None):
    """One HTTPS fetch per selected league, source bytes stored privately once.

    Individual failures remain per-league; no fake missing-fixture claim.
    """
    observed=_utc(now or datetime.now(timezone.utc))
    data=verify_private_projection(legacy,projection)
    if not isinstance(bulletin,dict) or not isinstance(bulletin.get('rows'),list):
        raise WitnessBlocked('PDF_BULLETIN_REQUIRED')
    leagues=sorted({r['league'] for r in bulletin['rows'] if isinstance(r,dict)
                    and r.get('league') in SOURCES})
    if not leagues:raise WitnessBlocked('NO_SUPPORTED_LEAGUE_IN_PDF')
    root=Path(destination)
    root.mkdir(parents=True,exist_ok=False)
    receipts={}
    day=observed.astimezone(ZoneInfo('Europe/Istanbul')).date().isoformat()
    for league in leagues:
        try:
            raw=fetch_source(league,fetcher=fetcher)
            # No completed result from today is safe to feed into a forecast
            # when only a match DATE (not exact outcome publication time) exists.
            parsed=witness_source(league,raw,data['latest_by_league'][league],day)
            with (root/(league+'.csv')).open('xb') as f:f.write(raw)
            receipts[league]={'status':'SECONDARY_BYTES_STORED_RESEARCH',
                              'size_bytes':len(raw),'sha256':_hash(raw),
                              'source_url':BASE+SOURCES[league]+'.csv',
                              'prior_completed_rows':parsed['prior_or_equal_frozen_rows'],
                              'observed_at_utc':observed.isoformat(),
                              'network_fetch_by_code':fetcher is None}
        except (OSError,ValueError,TypeError,UnicodeError) as exc:
            receipts[league]={'status':'SECONDARY_SOURCE_UNAVAILABLE',
                              'reason':(type(exc).__name__+':'+str(exc))[:180]}
    payload={'schema':SCHEMA,'created_at_utc':observed.isoformat(),
             'projection_sha256':data['private_score_projection_sha256'],
             'legacy_sha256':data['legacy_sha256'],'sources':receipts,
             'official_results_verified':False,'production_approved':False}
    payload['payload_sha256']=_hash(_canonical(payload))
    with (root/'manifest.json').open('x',encoding='utf-8') as f:
        json.dump(payload,f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write('\n')
    return payload

def inspect_witness(*,root,league,legacy,projection,target_day,now):
    """Revalidate immutable bytes, history SHA and fresh per-league result gap."""
    moment=_utc(now)
    data=verify_private_projection(legacy,projection)
    folder=Path(root)
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    signature=manifest.pop('payload_sha256',None)
    if (manifest.get('schema')!=SCHEMA or signature!=_hash(_canonical(manifest))
        or manifest.get('projection_sha256')!=data['private_score_projection_sha256']
        or manifest.get('legacy_sha256')!=data['legacy_sha256']):
        raise WitnessBlocked('MANIFEST_OR_DATA_SHA_INVALID')
    receipt=manifest['sources'].get(league)
    if not isinstance(receipt,dict) or receipt.get('status')!='SECONDARY_BYTES_STORED_RESEARCH':
        raise WitnessBlocked('LEAGUE_SECONDARY_SOURCE_UNAVAILABLE')
    if receipt.get('network_fetch_by_code') is not True:
        raise WitnessBlocked('SYNTHETIC_SOURCE_CANNOT_UNLOCK_FORECAST')
    observed=_utc(receipt['observed_at_utc'])
    if observed>moment or (moment-observed).total_seconds()>3600:
        raise WitnessBlocked('STALE_OR_FUTURE_SECONDARY_SOURCE')
    if receipt.get('source_url')!=BASE+SOURCES[league]+'.csv':
        raise WitnessBlocked('UNEXPECTED_SOURCE_URL')
    raw=(folder/(league+'.csv')).read_bytes()
    if _hash(raw)!=receipt.get('sha256') or len(raw)!=receipt.get('size_bytes'):
        raise WitnessBlocked('PROVIDER_BYTES_TAMPERED')
    report=witness_source(league,raw,data['latest_by_league'][league],target_day)
    if report['new_full_time_in_gap']:
        raise WitnessBlocked('COMPLETED_LEAGUE_RESULTS_NOT_IN_FROZEN_4618:'+str(len(report['new_full_time_in_gap'])))
    return {'status':'PROVIDER_BYTES_RECONCILED_RESEARCH_ONLY','league':league,
            'source_sha256':report['source_sha256'],
            'last_frozen':data['latest_by_league'][league],
            'target_day':target_day,'provider_report':report,
            'official_federation_verified':False,'production_forecast_allowed':False}
