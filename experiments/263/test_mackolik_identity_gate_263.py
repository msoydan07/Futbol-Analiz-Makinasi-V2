import unittest, tempfile, json, csv
from pathlib import Path
from datetime import datetime, timedelta, timezone
from mackolik_identity_gate_263 import prepare_from_mackolik_names, prepare_mackolik_analysis_entry, key, _reviewed

NOW=datetime(2026,11,1,15,0,tzinfo=timezone.utc)
REVIEWED_REAL=Path(__file__).resolve().parents[2]/'data'/'team_aliases_reviewed.csv'
if not REVIEWED_REAL.is_file():
    REVIEWED_REAL=Path(__file__).with_name('mackolik_reviewed_aliases.csv')

def names_observation(h,a,source='https://www.tff.org/default.aspx?pageID=600',**kwargs):
    obs={'status':'VERIFIED_OFFICIAL_FIXTURE','home':h,'away':a,
         'source_url':source,'retrieved_at_utc':NOW.isoformat(),
         'kickoff_utc':(NOW+timedelta(days=1)).isoformat()}
    obs.update(kwargs);return obs

class MatchGateTests(unittest.TestCase):
  def setUp(self):
    self.tmp=tempfile.TemporaryDirectory()
    self.addCleanup(self.tmp.cleanup)
    self.dir=Path(self.tmp.name)
    # Stored historical identity; no invented ID or display-name-based new identity.
    self.r={'teams':{'tid-b':{'name':'BEŞİKTAŞ A.Ş.','key':'besiktas'},
                     'tid-k':{'name':'KASIMPAŞA A.Ş.','key':'kasimpasa'},
                     'tid-x':{'name':'Arsenal','key':'arsenal'},
                     'tid-y':{'name':'Chelsea','key':'chelsea'},
                     'tid-dup':{'name':'Beşiktaş 2','key':'besiktas-2'}},
            'aliases':{'besiktas':'tid-b','beşiktaş a.ş.':'tid-b',
                       'kasimpasa':'tid-k','kasımpaşa a.ş.':'tid-k',
                       'arsenal':'tid-x','chelsea':'tid-y'},
            'fixtures':{'a':{'season':'2026-2027','league':'TUR1','home_id':'tid-b','away_id':'tid-k'},
                        'b':{'season':'2026-2027','league':'ENG1','home_id':'tid-x','away_id':'tid-y'}}}
    self.file=self.dir/'r.json';self.file.write_text(json.dumps(self.r,ensure_ascii=False),encoding='utf-8')
    self.alias=self.dir/'aliases.csv'
    self.alias.write_text('league,source_name,registry_name,source\n',encoding='utf-8')
  def go(self,home='Beşiktaş',away='Kasımpaşa',**kwargs):
    return prepare_from_mackolik_names(home,away,registry_path=self.file,reviewed_aliases_path=self.alias,now=NOW,**kwargs)
  def test_turkish_names_to_same_ids_and_verified(self):
    r=self.go(official_lookup=lambda h,a:names_observation(h,a))
    self.assertEqual((r['home_id'],r['away_id']),('tid-b','tid-k'))
    self.assertEqual((r['status'],r['kickoff_status']),('VERIFIED','CONFIRMED'))
    self.assertFalse(r['analysis_completed']);self.assertFalse(r['recommendation_eligible'])
  def test_source_input_not_verification(self):
    r=self.go(official_lookup=lambda h,a:{'status':'NOT_VERIFIED','reason':'no_official_match'})
    self.assertEqual(r['status'],'NOT_VERIFIED')
  def test_league_inferred_not_fixture_selected(self):
    r=self.go(official_lookup=lambda h,a:names_observation(h,a))
    self.assertEqual(r['league'],'TUR1')
  def test_league_mismatch_quarantined(self):
    r=self.go(league='ENG1',official_lookup=lambda h,a:names_observation(h,a))
    self.assertEqual(r['status'],'REVIEW_REQUIRED')
  def test_wrong_official_teams_rejected(self):
    r=self.go(official_lookup=lambda h,a:names_observation('Arsenal','Chelsea'))
    self.assertEqual(r['status'],'NOT_VERIFIED')
  def test_team_order_not_swapped(self):
    r=self.go(official_lookup=lambda h,a:names_observation('Kasımpaşa','Beşiktaş'))
    self.assertEqual(r['reason'],'official_participants_mismatch')
  def test_false_official_host(self):
    r=self.go(official_lookup=lambda h,a:names_observation(h,a,source='https://www.tff.org.evil.test/fixture'))
    self.assertEqual(r['status'],'NOT_VERIFIED')
  def test_stale_observation(self):
    r=self.go(official_lookup=lambda h,a:names_observation(h,a,retrieved_at_utc=(NOW-timedelta(days=2)).isoformat()))
    self.assertEqual(r['reason'],'official_observation_outdated')
  def test_date_only_time_pending(self):
    r=self.go(official_lookup=lambda h,a:names_observation(h,a,kickoff_utc=None,match_date='2026-11-03'))
    self.assertEqual(r['status'],'VERIFIED');self.assertEqual(r['kickoff_status'],'NOT_ANNOUNCED')
    self.assertEqual(r['analysis_date_cutoff_exclusive'],'2026-11-03')
  def test_date_only_invalid_date(self):
    r=self.go(official_lookup=lambda h,a:names_observation(h,a,kickoff_utc=None,match_date='garbage'))
    self.assertEqual(r['status'],'NOT_VERIFIED')
  def test_post_game_refused(self):
    r=self.go(official_lookup=lambda h,a:names_observation(h,a,kickoff_utc=(NOW-timedelta(minutes=1)).isoformat()))
    self.assertEqual(r['status'],'NOT_VERIFIED')
  def test_only_unique_registered_reviewed_alias(self):
    self.alias.write_text('league,source_name,registry_name,source\nTUR1,BJK,BEŞİKTAŞ A.Ş.,Maçkolik\n',encoding='utf-8')
    r=self.go(home='BJK',official_lookup=lambda h,a:names_observation(h,a))
    self.assertEqual(r['home_id'],'tid-b')
  def test_conflicting_reviewed_alias_is_not_auto_accepted(self):
    self.alias.write_text('league,source_name,registry_name,source\nTUR1,BJK,BEŞİKTAŞ A.Ş.,Maçkolik\nTUR1,BJK,KASIMPAŞA A.Ş.,Maçkolik\n',encoding='utf-8')
    r=self.go(home='BJK',official_lookup=lambda h,a:names_observation(h,a))
    self.assertEqual(r['status'],'REVIEW_REQUIRED')
  def test_unknown_not_fuzzy_guessed(self):
    r=self.go(home='Beşiktaş U19',official_lookup=lambda h,a:names_observation(h,a))
    self.assertEqual(r['status'],'REVIEW_REQUIRED')
  def test_official_adapter_prefers_original_then_fallback(self):
    def lookup(h,a):
        if h=='BEŞİKTAŞ A.Ş.':return names_observation(h,a)
        return {'status':'NOT_VERIFIED','reason':'not_equal'}
    r=self.go(official_lookup=lookup)
    self.assertEqual(r['status'],'VERIFIED');self.assertGreaterEqual(r['official_lookup_attempts'],2)
  def test_no_unbounded_fallback(self):
    count=[]
    def reject(h,a):count.append((h,a));return {'status':'NOT_VERIFIED'}
    r=self.go(official_lookup=reject)
    self.assertLessEqual(len(count),8);self.assertEqual(r['status'],'NOT_VERIFIED')
  def test_english_league_names(self):
    r=self.go(home='Arsenal',away='Chelsea',official_lookup=lambda h,a:names_observation(h,a,source='https://www.premierleague.com/fixtures'))
    self.assertEqual(r['league'],'ENG1')
  def test_identity_not_created(self):
    old=self.file.read_bytes()
    self.go(official_lookup=lambda h,a:names_observation(h,a))
    self.assertEqual(self.file.read_bytes(),old)
  def test_invalid_datetime(self):
    r=self.go(official_lookup=lambda h,a:names_observation(h,a,kickoff_utc='2026-11-02T15:00:00'))
    self.assertEqual(r['status'],'NOT_VERIFIED')
  def test_known_mackolik_variants_real_registry(self):
    full=Path(__file__).resolve().parent/'evidence'/'identity_index_263.json'
    reviewed=REVIEWED_REAL
    for home, away, league in [('Bayern Münih','B. Dortmund','GER1'),
                               ('PSG','Marsilya','FRA1'),
                               ('Galatasaray','Çaykur Rizespor','TUR1')]:
        r=prepare_from_mackolik_names(home,away,registry_path=full,
            reviewed_aliases_path=reviewed,now=NOW,
            official_lookup=lambda h,a:{'status':'NOT_VERIFIED','reason':'synthetic_no_match'})
        self.assertEqual(r['league'],league)
        self.assertEqual(r['status'],'NOT_VERIFIED')
        self.assertNotEqual(r['home_id'],r['away_id'])

  def test_mackolik_pair_requires_both_fallbacks(self):
    self.alias.write_text('league,source_name,registry_name,source\nTUR1,BJK,BEŞİKTAŞ A.Ş.,Maçkolik\nTUR1,KSP,KASIMPAŞA A.Ş.,Maçkolik\n',encoding='utf-8')
    def only_official(h,a):
        if h=='BEŞİKTAŞ A.Ş.' and a=='KASIMPAŞA A.Ş.':
            return names_observation(h,a)
        return {'status':'NOT_VERIFIED','reason':'unsupported_alias'}
    r=self.go(home='BJK',away='KSP',official_lookup=only_official)
    self.assertEqual(r['status'],'VERIFIED')
    self.assertLessEqual(r['official_lookup_attempts'],8)

  def test_complete_bridge_official_to_evidence(self):
    # Keep the already-existing 2.6.3 evidence gate rather than duplicating it.
    r=prepare_mackolik_analysis_entry('Beşiktaş','Kasımpaşa',
        registry_path=self.file,reviewed_aliases_path=self.alias, now=NOW,
        official_lookup=lambda h,a:names_observation(h,a))
    self.assertEqual(r['status'],'READY_FOR_DATA_AUDIT')
    self.assertFalse(r['fixture_list_required'])
    self.assertEqual(r['facts']['lineups']['status'],'NOT_CHECKED')
    self.assertEqual(r['mackolik_identity']['home_id'],'tid-b')

  def test_date_only_bridge_does_not_invent_time(self):
    r=prepare_mackolik_analysis_entry('Beşiktaş','Kasımpaşa',
        registry_path=self.file,reviewed_aliases_path=self.alias, now=NOW,
        official_lookup=lambda h,a:names_observation(h,a,kickoff_utc=None,match_date='2026-11-03'))
    self.assertEqual(r['status'],'READY_FOR_DATA_AUDIT')
    self.assertIsNone(r['kickoff_utc'])
    self.assertEqual(r['kickoff_status'],'NOT_ANNOUNCED')

  def test_index_215_teams_and_aliases_no_reissued_ids(self):
    index=Path(__file__).resolve().parent/'evidence'/'identity_index_263.json'
    original=index.read_bytes()
    j=json.loads(original)
    self.assertEqual(len(j['teams']),215)
    self.assertEqual(len(j['aliases']),370)
    r=prepare_from_mackolik_names('PSG','Marsilya',registry_path=index,
        reviewed_aliases_path=REVIEWED_REAL,now=NOW,
        official_lookup=lambda h,a:{'status':'NOT_VERIFIED'})
    self.assertEqual(r['league'],'FRA1')
    self.assertEqual(index.read_bytes(),original)

  def test_modified_identity_index_fails_closed(self):
    idx=Path(__file__).resolve().parent/'evidence'/'identity_index_263.json'
    j=json.loads(idx.read_bytes())
    j['aliases']['psg']='malicious-id'
    invalid=self.dir/'modified-index.json'
    invalid.write_text(json.dumps(j),encoding='utf-8')
    r=prepare_from_mackolik_names('PSG','Marsilya',registry_path=invalid,
         reviewed_aliases_path=REVIEWED_REAL,now=NOW,
         official_lookup=lambda h,a:names_observation(h,a))
    self.assertEqual(r['status'],'REVIEW_REQUIRED')
    self.assertEqual(r['reason'],'identity_index_payload_modified')

  def test_explicit_date_only_official_status_can_pass_data_gate(self):
    r=self.go(official_lookup=lambda h,a:names_observation(h,a,
      status='VERIFIED_OFFICIAL_FIXTURE_DATE_ONLY',kickoff_utc=None,match_date='2026-11-03'))
    self.assertEqual(r['status'],'VERIFIED')
    self.assertEqual(r['kickoff_status'],'NOT_ANNOUNCED')

  def test_date_only_status_with_kickoff_is_quarantined(self):
    r=self.go(official_lookup=lambda h,a:names_observation(h,a,
      status='VERIFIED_OFFICIAL_FIXTURE_DATE_ONLY',match_date='2026-11-03'))
    self.assertEqual(r['status'],'NOT_VERIFIED')
    self.assertEqual(r['reason'],'date_only_status_conflicts_with_kickoff')

  def test_french_existing_official_psg_club_adapter_allowed(self):
    r=prepare_from_mackolik_names('Arsenal','Chelsea',league='ENG1',registry_path=self.file,
      reviewed_aliases_path=self.alias,now=NOW,
      official_lookup=lambda h,a:names_observation(h,a,source='https://www.psg.fr/official'))
    # The PSG source cannot certify an English league fixture.
    self.assertEqual(r['status'],'NOT_VERIFIED')
    real=Path(__file__).resolve().parent/'evidence'/'identity_index_263.json'
    r=prepare_from_mackolik_names('PSG','Marsilya',league='FRA1',registry_path=real,
      reviewed_aliases_path=REVIEWED_REAL,now=NOW,
      official_lookup=lambda h,a:names_observation(h,a,source='https://www.psg.fr/en/schedule'))
    self.assertEqual(r['status'],'VERIFIED')

  def test_dutch_knvb_federation_adapter_allowed(self):
    real=Path(__file__).resolve().parent/'evidence'/'identity_index_263.json'
    r=prepare_from_mackolik_names('Ajax','PSV Eindhoven',league='NED1',registry_path=real,
      reviewed_aliases_path=REVIEWED_REAL,now=NOW,
      official_lookup=lambda h,a:names_observation(h,a,source='https://www.knvb.nl/competities/eredivisie/programma'))
    self.assertEqual(r['status'],'VERIFIED')

  def test_mackolik_string_not_scraped(self):
    self.assertEqual(key('İstanbul Başakşehir'),'istanbulbasaksehir')
    self.assertEqual(key('Beşiktaş'),'besiktas')

if __name__=='__main__':unittest.main()