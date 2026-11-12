"""Two pinned original SHA source-confirmation tests, no network in unit tests."""
import unittest
from datetime import datetime,timezone
from postmatch_csv_bridge_263 import ROOT,sealed,registered_names
from postmatch_tff_remaining_two_263 import PINS,url_for,parse_pinned,verify_two,Blocked
AFTER=datetime(2026,11,12,12,tzinfo=timezone.utc)
def html(pin,score=None,clock=None,home=None):
 cfg=PINS[pin];score=score if score is not None else cfg["score"]
 clock=clock or cfg["clock"]
 h=home if home is not None else ("ÇAYKUR RİZESPOR A.Ş." if cfg["id"]=="317877" else "BEŞİKTAŞ A.Ş.")
 a="ERZURUMSPOR FK" if cfg["id"]=="317877" else "GENÇLERBİRLİĞİ"
 return ("<html>Trendyol Süper Lig <p>"+h+"</p><b>"+str(score[0])+
   "</b><p>"+a+"</p><b>"+str(score[1])+"</b><span>8.11.2026 - "+
   clock+"</span></html>").encode("utf-8")
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.forecasts=sealed(ROOT);cls.registered=registered_names(ROOT)
 def test_both_real_preko_forecast_sha_and_exact_source_match(self):
  self.assertEqual(len(PINS),2)
  for pin,cfg in PINS.items():
   with self.subTest(pin=pin):
    got=verify_two(self.forecasts[pin],self.registered[pin],
      now=AFTER,fetcher=lambda url,p=pin:html(p))
    self.assertEqual(got["score"],cfg["score"])
    self.assertEqual(got["source_url"],url_for(pin))
    self.assertFalse(got["human_attestation_written"])
 def test_conflicting_result_blocked_not_promoted(self):
  for pin in PINS:
   with self.assertRaisesRegex(Blocked,"SCORE_CONFLICT"):
    parse_pinned(html(pin,score=[0,0]),pin)
 def test_wrong_date_and_wrong_teams_block(self):
  for pin in PINS:
   with self.assertRaisesRegex(Blocked,"WRONG_TFF_KICKOFF"):
    parse_pinned(html(pin,clock="23:58"),pin)
   with self.assertRaisesRegex(Blocked,"TFF_SCORE_NOT_UNIQUE"):
    parse_pinned(html(pin,home="WRONG CLUB"),pin)
 def test_bogus_identity_does_not_reuse_other_team_source(self):
  pin=next(iter(PINS))
  f=dict(self.forecasts[pin]);f["fixture"]=dict(f["fixture"])
  f["fixture"]["away_id"]="fake-id"
  with self.assertRaisesRegex(Blocked,"IDENTITY_MISMATCH"):
   verify_two(f,self.registered[pin],now=AFTER,fetcher=lambda url:html(pin))
  f=dict(self.forecasts[pin]);f["payload_sha256"]="0"*64
  with self.assertRaisesRegex(Blocked,"UNPINNED_SHA"):
   verify_two(f,self.registered[pin],now=AFTER)
 def test_missing_or_ambiguous_scores_rejected(self):
  pin=next(iter(PINS))
  with self.assertRaisesRegex(Blocked,"SCORE_NOT_UNIQUE"):
   parse_pinned("<html>Trendyol Süper Lig 8.11.2026 - 13:30</html>",pin)
  with self.assertRaisesRegex(Blocked,"SCORE_NOT_UNIQUE"):
   parse_pinned(html(pin)+html(pin,score=[1,2]),pin)
 def test_before_kickoff_or_final_whistle_rejected(self):
  for pin,cfg in PINS.items():
   with self.assertRaisesRegex(Blocked,"TOO_EARLY"):
    verify_two(self.forecasts[pin],self.registered[pin],
       now=datetime.fromisoformat(cfg["ko"]),fetcher=lambda url,p=pin:html(p))
if __name__=="__main__":unittest.main()

