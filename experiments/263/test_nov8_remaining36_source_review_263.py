"""One-pass 36 research-source ledger vs 40 original pregame SHA fixtures.
Never upgrades web-reviewed URLs to independent provider API attestations.
"""
import json,unittest
from urllib.parse import urlsplit
from postmatch_csv_bridge_263 import ROOT,Names,sealed,registered_names

MANIFEST=ROOT/"data/results_only_263/nov8_remaining36_source_review_20261112.json"
OLD=ROOT/"experiments/263/nov8_webreview_results_263.json"
THREE_TFF={"Çaykur Rizespor","Çorum FK","Beşiktaş"}
CLUBS={"trabzonspor.org.tr","liverpoolfc.com","afcb.co.uk","manutd.com",
"sscnapoli.it","acmilan.com","atalanta.it","inter.it","juventus.com",
"staderennais.com","kaagent.be","rusg.brussels","stvv.com"}
LEAGUES={"premierleague.com","bundesliga.com","laliga.com",
"ligue1.com","eredivisie.nl","ligaportugal.pt"}

class EvidenceLedger(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.doc=json.loads(MANIFEST.read_text())
  cls.old=json.loads(OLD.read_text())
  cls.seals=sealed(ROOT)
  cls.reg=registered_names(ROOT)
  cls.names=Names(ROOT)
 def test_exact_original_36_match_scores_no_postponed(self):
  previous={(x["league"],x["home"],x["away"]):x for x in self.old["rows"]
            if x["status"]=="FULL_TIME" and x["home"] not in THREE_TFF}
  self.assertEqual(len(previous),36)
  self.assertEqual(len(self.doc["rows"]),36)
  self.assertEqual(len(self.seals),40)
  seen=set()
  for row in self.doc["rows"]:
   k=(row["league"],row["home"],row["away"])
   self.assertIn(k,previous);self.assertNotIn(k,seen);seen.add(k)
   a=previous[k]
   self.assertEqual(row["date"],"2026-11-08")
   self.assertEqual(row["score"],[a["home_goals"],a["away_goals"]])
   self.assertEqual(row["original_research_url"],a["source_url"])
  self.assertEqual(seen,set(previous))
 def test_each_match_joins_exact_registered_original_sha(self):
  n=self.names
  keys={(x["league"],n.key(x["league"],x["home"]),n.key(x["league"],x["away"])):sha
        for sha,x in self.reg.items() if sha in self.seals}
  self.assertEqual(len(keys),40)
  for r in self.doc["rows"]:
   k=(r["league"],n.key(r["league"],r["home"]),n.key(r["league"],r["away"]))
   self.assertIn(k,keys)
   f=self.seals[keys[k]]
   self.assertEqual(f["fixture"]["match_local_date"],"2026-11-08")
   self.assertEqual(f["fixture"]["fixture_verification"],"VERIFIED_BY_LIVE_OFFICIAL_GATE")
 def test_source_grades_whitelist_and_not_federation_attestation(self):
  categories={"CLUB":0,"LEAGUE":0,"EXTERNAL_FEDERATION":0}
  for r in self.doc["rows"]:
   u=urlsplit(r["new_score_evidence_url"])
   self.assertEqual(u.scheme,"https")
   self.assertFalse(u.port or u.username or u.password)
   host=(u.hostname or "").removeprefix("www.").removeprefix("en.")
   typ=r["source_class"];self.assertIn(typ,categories);categories[typ]+=1
   if typ=="CLUB":self.assertIn(host,CLUBS)
   elif typ=="LEAGUE":self.assertIn(host,LEAGUES)
   else:
    self.assertEqual(host,"datencenter.dfb.de")
    self.assertEqual(r["home"],"Club Brugge")
   self.assertFalse(r["human_attestation"])
  self.assertEqual(categories,{"CLUB":13,"LEAGUE":22,"EXTERNAL_FEDERATION":1})
  self.assertEqual(self.doc["grading_counts"],categories)
 def test_late_match_remains_postponed_and_models_unchanged(self):
  p=[r for r in self.old["rows"] if r["status"]=="POSTPONED"]
  self.assertEqual(len(p),1)
  self.assertEqual((p[0]["home"],p[0]["away"]),("Estoril","Marítimo"))
  self.assertIsNone(p[0]["home_goals"]);self.assertIsNone(p[0]["away_goals"])
  self.assertFalse(self.doc["model_training_or_old_seals_edited"])
  self.assertEqual(self.doc["official_accepted_result_attestations_created"],0)

if __name__=="__main__":unittest.main()
