import unittest
from datetime import datetime,timezone
from pathlib import Path
from named_match_coverage_263 import prepare_requested_match,report_coverage
from test_official_page_lookup_263 import DFL,KNVB,EPL,JSONLD
HERE=Path(__file__).parent
NOW=datetime(2026,11,1,12,tzinfo=timezone.utc)

def go(home,away,league,**kw):
    return prepare_requested_match(home,away,league=league,
        identity_index=HERE/'identity_index_263.json',
        reviewed_aliases=HERE/'team_aliases_reviewed.csv',now=NOW,**kw)

class GateTests(unittest.TestCase):
    def test_bundesliga_reviewed_mackolik_names_with_real_identity(self):
        r=go('B. Dortmund','Elversberg','GER1',html=DFL)
        self.assertEqual(r['status'],'SIMULATED_OFFICIAL_PAGE_ONLY',r)
        self.assertEqual(r['kickoff_status'],'CONFIRMED')
        self.assertFalse(r['ready_for_data_audit'])
        self.assertFalse(r['model_ran'])
    def test_netherlands_current_team_membership(self):
        r=go('Fortuna Sittard','Telstar','NED1',html=KNVB)
        self.assertEqual(r['status'],'SIMULATED_OFFICIAL_PAGE_ONLY',r)
    def test_england_date_only_goes_to_date_audit_in_real_observation(self):
        r=go('Arsenal','Hull','ENG1',html=EPL)
        self.assertEqual(r['status'],'SIMULATED_OFFICIAL_PAGE_ONLY',r)
        self.assertEqual(r['kickoff_status'],'NOT_ANNOUNCED')
        self.assertFalse(r['ready_for_data_audit'])
    def test_unmatched_club_does_not_guess(self):
        r=go('Unknown Club','Telstar','NED1',html=KNVB)
        self.assertEqual(r['status'],'REVIEW_REQUIRED')
    def test_unobserved_match_never_analyzed(self):
        r=go('B. Dortmund','Elversberg','GER1',html=EPL)
        self.assertEqual(r['status'],'NOT_VERIFIED')
        self.assertFalse(r['model_ran'])
    def test_actual_fetched_callback_simulation_does_not_claim_true_fixture(self):
        r=go('B. Dortmund','Elversberg','GER1',fetcher=lambda u:(u,DFL))
        self.assertEqual(r['status'],'SIMULATED_OFFICIAL_PAGE_ONLY')
    def test_reject_automatic_fixture_selection(self):
        r=go('','Elversberg','GER1',html=DFL)
        self.assertEqual(r['status'],'REJECTED')
    def test_coverage_safely_uncertain(self):
        x=report_coverage()
        self.assertEqual(x['league_count'],10)
        self.assertFalse(x['operational_coverage_10_of_10_proven'])

if __name__=='__main__':unittest.main()
