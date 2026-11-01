"""Regression tests for Maçkolik-style names without changing canonical IDs."""
import tempfile,unittest
from pathlib import Path
from identity import Registry
from team_name_resolver import resolve

class TeamNames(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.registry=Registry(Path(self.temp.name)/"registry.json")
  self.k=self.registry.register_team("kasimpasa","KASIMPAŞA A.Ş.",aliases=("Kasimpasa",))
  self.b=self.registry.register_team("besiktas","BEŞİKTAŞ A.Ş.",aliases=("Besiktas",))
 def tearDown(self):self.temp.cleanup()
 def test_turkish_short_names(self):
  self.assertEqual(resolve(self.registry,"TUR1","Kasımpaşa"),self.k)
  self.assertEqual(resolve(self.registry,"TUR1","Beşiktaş"),self.b)
 def test_existing_ids_unchanged(self):
  self.assertEqual(resolve(self.registry,"TUR1","KASIMPAŞA A.Ş."),self.k)
 def test_unknown_team_not_guessed(self):
  with self.assertRaises(KeyError):resolve(self.registry,"TUR1","Unknown FC")
 def test_reviewed_external_alias(self):
  p=Path(self.temp.name)/"aliases.csv"
  p.write_text("league,source_name,registry_name,source\nTUR1,Kasimpasa SK,KASIMPAŞA A.Ş.,Mackolik\n",encoding="utf-8")
  self.assertEqual(resolve(self.registry,"TUR1","Kasimpasa SK",p),self.k)

if __name__=="__main__":unittest.main()
