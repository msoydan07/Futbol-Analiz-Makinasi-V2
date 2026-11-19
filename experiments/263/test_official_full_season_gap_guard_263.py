import copy,unittest
from datetime import date,timedelta
from official_full_season_gap_guard_263 import (
    EXPECTED_TEAMS,OfficialGapBlocked,evaluate_full_fixture_set,fetch_official_full_window)

def season(league):
    n=EXPECTED_TEAMS[league]
    teams=[f'TEAM {i:02d}' for i in range(n)]
    return [{'home':h,'away':a,'match_date':(date(2026,8,8)+timedelta(days=i%280)).isoformat()}
            for i,(h,a) in enumerate((h,a) for h in teams for a in teams if h!=a)]

class SeasonWindowTests(unittest.TestCase):
    def test_01_all_10_leagues_complete_gap(self):
        for league in EXPECTED_TEAMS:
            with self.subTest(league=league):
                events=season(league)
                gap_start='2027-05-20';gap_end='2027-05-21'
                result=evaluate_full_fixture_set(league,gap_start,gap_end,events)
                self.assertEqual(result['status'],'OFFICIAL_FULL_SCHEDULE_HAS_NO_MATCH_IN_GAP')
                self.assertFalse(result['production_forecast_allowed'])

    def test_02_only_one_round_must_fail(self):
        with self.assertRaisesRegex(OfficialGapBlocked,'PARTIAL'):
            evaluate_full_fixture_set('ENG1','2026-11-09','2026-11-19',season('ENG1')[:10])

    def test_03_event_in_gap_blocks(self):
        e=season('ENG1');e[0]['match_date']='2026-11-12'
        out=evaluate_full_fixture_set('ENG1','2026-11-09','2026-11-19',e)
        self.assertFalse(out['calendar_gap_supported'])
        self.assertIn(['2026-11-12','team 00','team 01'],out['scheduled_in_gap'])
        self.assertGreaterEqual(len(out['scheduled_in_gap']),1)

    def test_04_duplicate_pairs_block(self):
        e=season('GER1');e[1]=copy.deepcopy(e[0])
        with self.assertRaisesRegex(OfficialGapBlocked,'DUPLICATE'):
            evaluate_full_fixture_set('GER1','2026-11-09','2026-11-19',e)

    def test_05_weak_date_span_blocks(self):
        e=season('ITA1')
        for item in e:item['match_date']='2026-11-01'
        with self.assertRaisesRegex(OfficialGapBlocked,'SPAN'):
            evaluate_full_fixture_set('ITA1','2026-11-09','2026-11-19',e)

    def test_06_incorrect_team_count_blocks(self):
        e=season('BEL1');e[0]['home']='UNKNOWN CLUB'
        with self.assertRaisesRegex(OfficialGapBlocked,'TEAM|ROUND_ROBIN'):
            evaluate_full_fixture_set('BEL1','2026-11-09','2026-11-19',e)

    def test_07_wrong_season_blocks(self):
        e=season('ESP1');e[0]['match_date']='2025-11-01'
        with self.assertRaisesRegex(OfficialGapBlocked,'OTHER_SEASON'):
            evaluate_full_fixture_set('ESP1','2026-11-09','2026-11-19',e)

    def test_08_fetch_rejects_wrong_official_host(self):
        import sys,types
        fake=types.ModuleType('official_page_lookup_263')
        fake.SOURCES={'ENG1':('https://www.premierleague.com/en/fixtures','premierleague.com','epl')}
        fake.is_approved_url=lambda url,league:url.startswith('https://www.premierleague.com/')
        fake._default_fetch=lambda url,league:(url,'<html>test</html>')
        fake.parse_official_events=lambda league,html:season('ENG1')
        before=sys.modules.get('official_page_lookup_263')
        sys.modules['official_page_lookup_263']=fake
        try:
            with self.assertRaisesRegex(OfficialGapBlocked,'REDIRECT'):
                fetch_official_full_window('ENG1','2026-11-09','2026-11-19',
                     fetcher=lambda u,l:('https://evil.example/test','<html>'+'x'*150+'</html>'))
        finally:
            if before is None:del sys.modules['official_page_lookup_263']
            else:sys.modules['official_page_lookup_263']=before

    def test_09_fetch_injected_full_page_nonproduction(self):
        import sys,types
        fake=types.ModuleType('official_page_lookup_263')
        fake.SOURCES={'ENG1':('https://www.premierleague.com/en/fixtures','premierleague.com','epl')}
        fake.is_approved_url=lambda url,league:url.startswith('https://www.premierleague.com/')
        fake._default_fetch=lambda url,league:(url,'<html>'+'x'*120+'</html>')
        fake.parse_official_events=lambda league,html:season('ENG1')
        before=sys.modules.get('official_page_lookup_263')
        sys.modules['official_page_lookup_263']=fake
        try:
            out=fetch_official_full_window('ENG1','2027-05-20','2027-05-21')
            self.assertTrue(out['calendar_gap_supported'])
            self.assertFalse(out['real_official_source_acceptance'])
            self.assertFalse(out['production_forecast_allowed'])
        finally:
            if before is None:del sys.modules['official_page_lookup_263']
            else:sys.modules['official_page_lookup_263']=before

if __name__=='__main__':unittest.main(verbosity=2)
