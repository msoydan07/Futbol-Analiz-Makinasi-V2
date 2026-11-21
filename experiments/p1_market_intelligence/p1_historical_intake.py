"""Offline, consented historical odds CSV validation for independent P1 research.

Never downloads bookmaker content, never touches active 2.6.3 forecasts,
and does not certify timestamps or licensing just because a CSV says so.
"""
import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from p1_market import MARKETS, analyze_prices, score_observed, MarketDataError

SCHEMA = 'P1_HISTORICAL_ACCEPTANCE_RESEARCH_V1'
FIELDS = ('league','match_date','kickoff_utc','home','away','MS1','MSX','MS2',
          'UNDER_2.5','OVER_2.5','BTTS_YES','BTTS_NO','FTHG','FTAG','result_source')
ODDS_FIELDS = tuple(k for keys in MARKETS.values() for k in keys)
ALLOWED_LEAGUES = frozenset(('ENG1','ENG2','GER1','ESP1','ITA1','FRA1','NED1','TUR1','POR1','BEL1'))
MAX_MATCH_DAY = datetime(2026,11,21).date()


def when(s):
    if not isinstance(s,str) or not s.strip():
        raise ValueError('TIME_MISSING')
    d=datetime.fromisoformat(s.replace('Z','+00:00'))
    if d.tzinfo is None: raise ValueError('TIME_NOT_TIMEZONE_AWARE')
    return d.astimezone(timezone.utc)


def review_manifest(obj):
    if not isinstance(obj,dict): raise ValueError('MANIFEST_NOT_OBJECT')
    if obj.get('research_use_authorized') is not True:
        raise ValueError('RESEARCH_RIGHTS_NOT_CONFIRMED')
    if not isinstance(obj.get('rights_basis'),str) or len(obj['rights_basis'])<12:
        raise ValueError('MISSING_RIGHTS_BASIS')
    for k in ('source_name','source_url','bookmaker','price_phase'):
        if not isinstance(obj.get(k),str) or not obj[k]:
            raise ValueError('MANIFEST_FIELD_MISSING:'+k)
    if obj['price_phase'] not in ('OPENING','CLOSING','PDF_MORNING'):
        raise ValueError('UNKNOWN_PRICE_PHASE')
    if not obj['source_url'].startswith('https://'):
        raise ValueError('SOURCE_HTTPS_REQUIRED')
    if obj['bookmaker']=='iddaa.com' and obj.get('source_kind')!='USER_OWNED_IDDAA_PDF':
        raise ValueError('IDDAA_REQUIRES_OWN_PDF_ORIGINAL')
    return obj


def inspect(local_csv: Path, manifest: dict):
    manifest=review_manifest(manifest)
    audit=[]; accepted=[]; seen=set()
    sha=hashlib.sha256(local_csv.read_bytes()).hexdigest()
    with local_csv.open('r',encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        required=set(FIELDS)
        if not required.issubset(set(reader.fieldnames or ())):
            raise ValueError('CSV_REQUIRED_COLUMNS_MISSING:'+','.join(sorted(required-set(reader.fieldnames or ()))))
        for row_index,r in enumerate(reader,2):
            try:
                date=str(r['match_date']).strip()
                d=datetime.fromisoformat(date).date()
                ko=when(r['kickoff_utc'])
                if ko.date()<d or (ko.date()-d).days>1:
                    raise ValueError('MATCH_DATE_AND_KICKOFF_INCONSISTENT')
                identity=(r['league'].strip(),date,r['home'].strip().casefold(),r['away'].strip().casefold())
                if not all(identity) or identity in seen: raise ValueError('DUPLICATE_OR_EMPTY_IDENTITY')
                if identity[0] not in ALLOWED_LEAGUES: raise ValueError('OUT_OF_TEN_LEAGUES')
                if d > MAX_MATCH_DAY: raise ValueError('FUTURE_MATCH_RESULT_PROHIBITED')
                seen.add(identity)
                odds={key:float(r[key]) for key in ODDS_FIELDS}
                if any(not math.isfinite(v) or not (1<v<1000) for v in odds.values()):
                    raise ValueError('ODDS_OUTSIDE_RANGE')
                prices={g:{k:odds[k] for k in ks} for g,ks in MARKETS.items()}
                # An observed timestamp is not independent proof by itself.
                observed=r.get('observed_at_utc','').strip()
                if observed:
                    if when(observed)>=ko:raise ValueError('OBSERVED_AT_OR_AFTER_KICKOFF')
                    time_grade='SOURCE_TIMESTAMP_ASSERTION_NOT_INDEPENDENT_PROOF'
                else:
                    time_grade='SOURCE_CLASSIFIED_PREMATCH_UNTIMESTAMPED_RESEARCH_ONLY'
                goals=[int(r[k]) for k in ('FTHG','FTAG')]
                if any(x<0 for x in goals):raise ValueError('NEGATIVE_GOALS')
                if not r['result_source'].strip().startswith('https://'):
                    raise ValueError('FINAL_SCORE_SOURCE_MISSING')
                out=analyze_prices(prices)
                m0=score_observed(out['p0'],*goals)
                m1=score_observed(out['p1']['p1_probabilities'],*goals)
                accepted.append({'row':row_index,'identity':identity,'bookmaker':manifest['bookmaker'],
                    'match_date':date,'time_grade':time_grade,'price_phase':manifest['price_phase'],
                    'source_kind':('IDDAA_USER_PDF_RESEARCH' if manifest['bookmaker']=='iddaa.com' else 'NON_IDDAA_RESEARCH_ONLY'),
                    'p0_brier':m0['macro_brier'],'p1_brier':m1['macro_brier'],
                    'p0_logloss':m0['macro_log_loss'],'p1_logloss':m1['macro_log_loss'],
                    'max_coherence_residual_pp':out['p1']['max_residual_pp']})
            except (ValueError,KeyError,TypeError,MarketDataError,OverflowError) as e:
                audit.append({'row':row_index,'status':'REJECTED','reason':type(e).__name__+':'+str(e)})
    return {'schema':SCHEMA,'data_sha256':sha,'source_name':manifest['source_name'],
            'source_url':manifest['source_url'],'bookmaker':manifest['bookmaker'],
            'source_rights_attested_not_independently_enforced':True,
            'raw_bookmaker_prices_committed_to_github':False,
            'no_kickoff_timestamp_independent_verification':True,
            'n_accepted':len(accepted),'n_rejected':len(audit),'accepted':accepted,'rejected':audit,
            'results_are_research_only_not_blind_model_comparison':True}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--csv',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    report=inspect(a.csv,json.loads(a.manifest.read_text('utf-8')))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"RESEARCH accepted={report['n_accepted']} rejected={report['n_rejected']}")
if __name__=='__main__':main()
