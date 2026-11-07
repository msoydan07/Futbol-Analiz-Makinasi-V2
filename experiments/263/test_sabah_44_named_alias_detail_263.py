"""7 Nov alias + exact TFF official detail fallback, no fuzzy/retroactive gate."""
import unittest
from datetime import datetime,timezone
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway,NOV7_TFF_DETAIL,NOV7_ALIASES
NOW=datetime(2026,11,7,10,0,tzinfo=timezone.utc)
GATE={
    'status':'VERIFIED','league':'TUR1','home_id':'G','away_id':'B',
    'kickoff_utc':'2026-11-07T16:00:00+00:00',
    'source_url':NOV7_TFF_DETAIL,'retrieved_at_utc':NOW.isoformat()
}
def fake_runner(league,home,away,lookup_override=None):
    if lookup_override is None:return {'status':'NOT_VERIFIED','reason':'OLD_FALLBACK_MISSING'}
    entry=lookup_override(home,away)
    if entry.get('status')!='VERIFIED_OFFICIAL_FIXTURE':return {'status':'NOT_VERIFIED'}
    return {**GATE,'league':league,'home_id':home,'away_id':away,
            'source_url':entry['source_url'],'kickoff_utc':entry['kickoff_utc']}
PAGE='<title>GÖZTEPE A.Ş. İSTANBUL BAŞAKŞEHİR FK - Maç Detayları TFF</title><h2>TRENDYOL SÜPER LİG</h2><div>7.11.2026 - 19:00</div>'
def gateway(page=PAGE):
    def get(url,league):
        if url==NOV7_TFF_DETAIL:return url,page
        return url,'<h1>Round 11 Super Lig omitted this pair</h1>'
    names={'GÖZTEPE A.Ş.':'G','İSTANBUL BAŞAKŞEHİR FK':'B'}
    return OfficialFixtureGateway(fetcher=get,gate_runner=fake_runner,
        resolve_id=lambda l,n:names[n],clock=lambda:NOW)
class OfficialFallbackTests(unittest.TestCase):
    def test_named_alias_reviewed_only(self):
        self.assertEqual(NOV7_ALIASES['ESP1']['Racing Santander'],'R. Racing Club')
        self.assertEqual(NOV7_ALIASES['GER1']['Bayern München'],'FC Bayern München')
    def test_exact_tff_detail_verified_by_existing_gate(self):
        g=gateway();r=g.lookup('TUR1','Göztepe','Başakşehir')
        self.assertEqual(r['status'],'VERIFIED')
        self.assertEqual(r['kickoff_utc'],'2026-11-07T16:00:00+00:00')
        self.assertEqual(g.match_checks[-1]['selected_lookup'],'TFF_ONE_MATCH_OFFICIAL_DETAIL')
    def test_tff_wrong_date_no_promotion(self):
        g=gateway(PAGE.replace('7.11.2026 - 19:00','8.11.2026 - 19:00'))
        self.assertNotEqual(g.lookup('TUR1','Göztepe','Başakşehir')['status'],'VERIFIED')
    def test_tff_wrong_clubs_no_promotion(self):
        g=gateway(PAGE.replace('İSTANBUL BAŞAKŞEHİR FK','FENERBAHÇE SK'))
        self.assertNotEqual(g.lookup('TUR1','Göztepe','Başakşehir')['status'],'VERIFIED')
    def test_alias_not_in_same_league_not_used(self):
        g=gateway()
        self.assertNotEqual(g.lookup('TUR1','Amed SK','Göztepe')['status'],'VERIFIED')
if __name__=='__main__':unittest.main()
