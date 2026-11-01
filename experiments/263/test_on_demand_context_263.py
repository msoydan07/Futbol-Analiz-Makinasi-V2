import unittest
from datetime import datetime, timezone, timedelta
from on_demand_context_263 import prepare_named_match

NOW = datetime(2026, 11, 1, 18, 0, tzinfo=timezone.utc)
HOME = 'club-home'; AWAY='club-away'

def fixture(league='TUR1', home='Home FC', away='Away FC', **kwargs):
    r={'status':'VERIFIED','league':league,'home_id':HOME,'away_id':AWAY,
       'kickoff_utc':(NOW+timedelta(days=1)).isoformat(),
       'source_url':'https://www.tff.org/default.aspx?pageID=28',
       'retrieved_at_utc':NOW.isoformat()}
    r.update(kwargs)
    return r

def accepted(_league,_home,_away,registry_path):
    return fixture()

class NamedFixtureContextTests(unittest.TestCase):
    def test_no_schedule_and_default_missing_lineups(self):
        r=prepare_named_match('TUR1','Home FC','Away FC',now=NOW,fixture_gate=accepted)
        self.assertEqual(r['status'],'READY_FOR_DATA_AUDIT')
        self.assertIs(r['fixture_list_required'],False)
        self.assertEqual(r['facts']['lineups']['status'],'NOT_CHECKED')
        self.assertFalse(r['lineups_missing_blocks_analysis'])
        self.assertFalse(r['analysis_completed'])
        self.assertEqual(r['fixture']['local_date'],'2026-11-02')

    def test_verification_failure_never_enters_analysis(self):
        def fail(*args,**kwargs):return {'status':'NOT_VERIFIED','reason':'not_found'}
        r=prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=fail)
        self.assertEqual(r['status'],'NOT_VERIFIED')
        self.assertNotIn('facts',r)

    def test_never_select_match_automatically(self):
        r=prepare_named_match('TUR1','','Away',now=NOW,fixture_gate=accepted)
        self.assertEqual(r['reason'],'named_match_required')

    def test_official_domain_gate(self):
        def fake(*a,**k):return fixture(source_url='https://tff.org.evil.example/match')
        r=prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=fake)
        self.assertEqual(r['status'],'NOT_VERIFIED')

    def test_stale_fixture_rejected(self):
        def old(*a,**k):return fixture(retrieved_at_utc=(NOW-timedelta(days=2)).isoformat())
        r=prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=old)
        self.assertEqual(r['status'],'NOT_VERIFIED')

    def test_kickoff_window_rejected(self):
        def old(*a,**k):return fixture(kickoff_utc=(NOW-timedelta(minutes=1)).isoformat())
        r=prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=old)
        self.assertEqual(r['status'],'NOT_VERIFIED')

    def test_checked_but_unpublished_lineup_does_not_block(self):
        evidence={'lineups':{'field':'lineups','status':'NOT_PUBLISHED','source_url':'https://www.tff.org/match',
                            'retrieved_at_utc':NOW.isoformat(),'home_id':HOME,'away_id':AWAY}}
        r=prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=accepted,observation_provider=lambda _fixture: evidence)
        self.assertEqual(r['facts']['lineups']['status'],'NOT_PUBLISHED_OFFICIAL_CHECK')
        self.assertFalse(r['lineups_missing_blocks_analysis'])

    def test_unverified_injuries_cannot_modify_math(self):
        evidence={'injuries_suspensions':{'field':'injuries_suspensions','status':'VERIFIED',
                 'source_url':'https://unknown.example/rumor','retrieved_at_utc':NOW.isoformat(),
                 'home_id':HOME,'away_id':AWAY,'details':{'out':['Player X']}}}
        r=prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=accepted,observation_provider=lambda _fixture: evidence)
        self.assertEqual(r['facts']['injuries_suspensions']['status'],'UNVERIFIED')
        self.assertFalse(r['facts']['injuries_suspensions']['math_effect'])
        self.assertFalse(r['external_context_modified_lambdas'])

    def test_verified_first_party_context_still_not_lambda_adjustment(self):
        evidence={'injuries_suspensions':{'field':'injuries_suspensions','status':'VERIFIED',
                 'source_url':'https://www.tff.org/bilgi','retrieved_at_utc':NOW.isoformat(),
                 'home_id':HOME,'away_id':AWAY,'details':{'confirmed':['Player X']}}}
        r=prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=accepted,observation_provider=lambda _fixture: evidence)
        self.assertEqual(r['facts']['injuries_suspensions']['status'],'VERIFIED_SOURCE_RECORD')
        self.assertFalse(r['external_context_modified_lambdas'])

    def test_wrong_match_evidence_quarantined(self):
        evidence={'lineups':{'field':'lineups','status':'VERIFIED',
                 'source_url':'https://www.tff.org/bilgi','retrieved_at_utc':NOW.isoformat(),
                 'home_id':'OTHER','away_id':AWAY,'details':{}}}
        r=prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=accepted,observation_provider=lambda _fixture: evidence)
        self.assertEqual(r['facts']['lineups']['reason'],'different_match_identity')

    def test_league_and_team_mismatch_in_gate_result(self):
        def bad(*a,**k):return fixture(league='ENG1')
        self.assertEqual(prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=bad)['status'],'NOT_VERIFIED')

    def test_incomplete_lineup_not_mislabeled_verified(self):
        obs={'lineups':{'field':'lineups','status':'VERIFIED',
             'source_url':'https://www.tff.org/bilgi','retrieved_at_utc':NOW.isoformat(),
             'home_id':HOME,'away_id':AWAY,'details':{'home_starting_xi':['A']}}}
        result=prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=accepted,observation_provider=lambda _fixture: obs)
        self.assertEqual(result['facts']['lineups']['status'],'UNVERIFIED')
        self.assertEqual(result['facts']['lineups']['reason'],'incomplete_or_repeated_starting_xi')

    def test_complete_lineup_11_each_accepted_as_record_not_model_effect(self):
        obs={'lineups':{'field':'lineups','status':'VERIFIED',
             'source_url':'https://www.tff.org/bilgi','retrieved_at_utc':NOW.isoformat(),
             'home_id':HOME,'away_id':AWAY,
             'details':{'home_starting_xi':[f'H{i}' for i in range(11)],
                        'away_starting_xi':[f'A{i}' for i in range(11)]}}}
        result=prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=accepted,observation_provider=lambda _fixture: obs)
        self.assertEqual(result['facts']['lineups']['status'],'VERIFIED_SOURCE_RECORD')
        self.assertFalse(result['facts']['lineups']['math_effect'])

    def test_raw_evidence_dictionary_rejected(self):
        r=prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=accepted,
            observation_provider={'lineups':{'status':'VERIFIED'}})
        self.assertEqual(r['status'],'REJECTED')

    def test_provider_failure_keeps_analysis_possible_and_evidence_unchecked(self):
        def broken(_fixture):raise RuntimeError('source unavailable')
        r=prepare_named_match('TUR1','Home','Away',now=NOW,fixture_gate=accepted,
                              observation_provider=broken)
        self.assertEqual(r['status'],'READY_FOR_DATA_AUDIT')
        self.assertEqual(r['facts']['lineups']['status'],'NOT_CHECKED')
        self.assertIn('official_context_adapter_failed',r['context_collection_error'])

    def test_utc_date_edge_does_not_claim_other_league_date(self):
        def kickoff(*a,**k):return fixture(league='ENG1',source_url='https://www.premierleague.com/matches',kickoff_utc='2026-11-01T23:30:00+00:00')
        r=prepare_named_match('ENG1','Home','Away',now=NOW,fixture_gate=kickoff)
        self.assertEqual(r['status'],'READY_FOR_DATA_AUDIT')
        self.assertEqual(r['fixture']['local_date'],'2026-11-01')

if __name__=='__main__':unittest.main()