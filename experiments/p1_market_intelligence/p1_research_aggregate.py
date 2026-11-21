"""Conservative paired P0/P1 diagnostics for accepted historical research rows.

Input is a p1_historical_intake.py JSON audit, NOT raw betting prices.
The routine never fetches sources, overwrites seals, nor promotes a model.
"""
import argparse
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

EXPECTED_SCHEMA = 'P1_HISTORICAL_ACCEPTANCE_RESEARCH_V1'
MIN_PAIRED_FOR_CI = 30
MIN_PAIRED_FOR_RESEARCH_REVIEW = 200

class AuditError(ValueError):
    pass


def _mean(values):
    return statistics.fmean(values)


def _paired_interval(diffs, draws=2000, seed=263):
    """Deterministic percentile bootstrap, paired by fixture (not by betting event)."""
    if len(diffs) < MIN_PAIRED_FOR_CI:
        return None
    rng = random.Random(seed)
    n = len(diffs)
    resamples = [sum(diffs[rng.randrange(n)] for _ in range(n))/n for _ in range(draws)]
    resamples.sort()
    return [resamples[int(0.025*(draws-1))], resamples[int(0.975*(draws-1))]]


def _fixture_key(row):
    ident = row.get('identity')
    if not isinstance(ident,(list,tuple)) or len(ident) != 4:
        raise AuditError('INVALID_FIXTURE_IDENTITY')
    if not all(isinstance(v,str) and v.strip() for v in ident):
        raise AuditError('EMPTY_FIXTURE_IDENTITY')
    return tuple(v.strip().casefold() for v in ident)


def _number(row, name):
    v = row.get(name)
    if isinstance(v, bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v < 0:
        raise AuditError('INVALID_SCORE:'+name)
    return float(v)


def _cohort(rows, label):
    if not rows:
        raise AuditError('EMPTY_COHORT')
    results = {'label':label,'n_fixtures':len(rows),'markets_are_three_dependent_groups':True,
               'source_time_is_independently_verified':False}
    for label_score,p0,p1 in (('brier','p0_brier','p1_brier'),
                              ('logloss','p0_logloss','p1_logloss')):
        l0=[_number(r,p0) for r in rows]
        l1=[_number(r,p1) for r in rows]
        differences=[b-a for a,b in zip(l0,l1)]
        results[label_score]={
            'p0':_mean(l0),'p1':_mean(l1),'delta_p1_minus_p0':_mean(differences),
            'paired_bootstrap_95pct':_paired_interval(differences),
            'lower_is_better':True}
    results['minimum_200_fixtures_for_descriptive_review']=len(rows)>=MIN_PAIRED_FOR_RESEARCH_REVIEW
    results['claim_of_superiority_allowed']=False  # time provenance and holdout not independently proven
    return results


def aggregate(audit):
    if not isinstance(audit,dict) or audit.get('schema')!=EXPECTED_SCHEMA:
        raise AuditError('UNSUPPORTED_INPUT_SCHEMA')
    if audit.get('n_accepted')!=len(audit.get('accepted',[])):
        raise AuditError('AUDIT_COUNT_MISMATCH')
    if not audit.get('results_are_research_only_not_blind_model_comparison'):
        raise AuditError('MISSING_RESEARCH_ONLY_SAFETY_MARKER')
    if audit.get('no_kickoff_timestamp_independent_verification') is not True:
        raise AuditError('UNSUPPORTED_TIME_ATTESTATION_CLAIM')
    rows = audit['accepted']
    if not rows:
        return {'schema':'P1_PAIRED_AGGREGATE_V1','n_fixtures':0,
                'source_name':audit.get('source_name'), 'status':'NO_ACCEPTED_ROWS',
                'production_promotion_allowed':False,'cohorts':[]}
    seen=set()
    groups=defaultdict(list)
    for r in rows:
        identity=_fixture_key(r)
        if identity in seen:
            raise AuditError('DUPLICATE_ACCEPTED_FIXTURE')
        seen.add(identity)
        if r.get('bookmaker') != audit.get('bookmaker'):
            raise AuditError('SOURCE_BOOKMAKER_MISMATCH')
        phase=r.get('price_phase')
        league=identity[0].upper()
        if phase not in ('OPENING','CLOSING','PDF_MORNING'):
            raise AuditError('INVALID_PRICE_PHASE')
        if r.get('time_grade') not in (
           'SOURCE_TIMESTAMP_ASSERTION_NOT_INDEPENDENT_PROOF',
           'SOURCE_CLASSIFIED_PREMATCH_UNTIMESTAMPED_RESEARCH_ONLY'):
            raise AuditError('UNSUPPORTED_TIME_GRADE')
        groups[(str(r['bookmaker']),str(phase),league)].append(r)
    records=[_cohort(v,{'bookmaker':k[0],'phase':k[1],'league':k[2]})
             for k,v in sorted(groups.items())]
    # Do not pool mixed opening and closing, or multiple leagues, into a claim of model quality.
    return {'schema':'P1_PAIRED_AGGREGATE_V1','source_name':audit.get('source_name'),
            'source_url':audit.get('source_url'),'source_csv_sha256':audit.get('data_sha256'),
            'n_fixtures':len(rows),'n_rejected':audit.get('n_rejected'),
            'status':'PAIRED_DESCRIPTIVE_ONLY',
            'production_promotion_allowed':False,
            'no_verified_independent_time_proof':True,
            'no_M4_C3_comparison_without_matched_frozen_preds':True,
            'cohorts':records}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--audit',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    arg=ap.parse_args()
    out=aggregate(json.loads(arg.audit.read_text(encoding='utf-8')))
    arg.output.parent.mkdir(parents=True,exist_ok=True)
    arg.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"P1 paired diagnostic n={out['n_fixtures']} cohorts={len(out['cohorts'])}")

if __name__ == '__main__':
    main()