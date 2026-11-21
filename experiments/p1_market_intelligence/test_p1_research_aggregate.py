import copy
import unittest
from p1_research_aggregate import aggregate, AuditError, _paired_interval


def audit(n=4):
    rows=[]
    for i in range(n):
        rows.append({'identity':['ENG1','2025-05-%02d'%(i%28+1),'Home'+str(i),'Away'+str(i)],
              'bookmaker':'book', 'price_phase':'OPENING',
              'time_grade':'SOURCE_CLASSIFIED_PREMATCH_UNTIMESTAMPED_RESEARCH_ONLY',
              'p0_brier':0.6,'p1_brier':0.5,'p0_logloss':0.8,'p1_logloss':0.7})
    return {'schema':'P1_HISTORICAL_ACCEPTANCE_RESEARCH_V1',
            'n_accepted':n,'accepted':rows,'n_rejected':0,
            'bookmaker':'book','source_name':'synthetic','source_url':'https://example.org',
            'data_sha256':'123456',
            'results_are_research_only_not_blind_model_comparison':True,
            'no_kickoff_timestamp_independent_verification':True}

class AggregateTest(unittest.TestCase):
    def test_small_no_confidence(self):
        out=aggregate(audit())
        self.assertEqual(out['n_fixtures'],4)
        self.assertAlmostEqual(out['cohorts'][0]['brier']['delta_p1_minus_p0'],-.1)
        self.assertIsNone(out['cohorts'][0]['brier']['paired_bootstrap_95pct'])
        self.assertFalse(out['cohorts'][0]['claim_of_superiority_allowed'])
    def test_bootstrap_fixed_seed(self):
        self.assertEqual(_paired_interval([-.1]*40),[-.1,-.1])
    def test_reject_duplicate(self):
        obj=audit()
        obj['accepted'][1]['identity']=obj['accepted'][0]['identity']
        with self.assertRaisesRegex(AuditError,'DUPLICATE'):aggregate(obj)
    def test_reject_bookmaker_mismatch(self):
        obj=audit();obj['accepted'][0]['bookmaker']='book2'
        with self.assertRaisesRegex(AuditError,'MISMATCH'):aggregate(obj)
    def test_reject_no_time_grade(self):
        obj=audit();obj['accepted'][0]['time_grade']='INDEPENDENT_VERIFIED'
        with self.assertRaisesRegex(AuditError,'TIME_GRADE'):aggregate(obj)
    def test_reject_schema(self):
        obj=audit();obj['schema']='UNKNOWN'
        with self.assertRaisesRegex(AuditError,'SCHEMA'):aggregate(obj)
    def test_reject_malformed_score(self):
        obj=audit();obj['accepted'][0]['p0_brier']=float('nan')
        with self.assertRaisesRegex(AuditError,'INVALID_SCORE'):aggregate(obj)
    def test_separate_cohorts(self):
        obj=audit();obj['accepted'][0]['price_phase']='CLOSING'
        self.assertEqual(len(aggregate(obj)['cohorts']),2)
    def test_no_accepted(self):
        obj=audit(0);self.assertEqual(aggregate(obj)['status'],'NO_ACCEPTED_ROWS')

if __name__=='__main__':unittest.main()