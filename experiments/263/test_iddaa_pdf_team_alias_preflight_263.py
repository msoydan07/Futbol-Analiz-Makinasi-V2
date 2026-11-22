"""One coherent batch of read-only team label tests for user supplied iddaa PDF.

The 86 historical external labels are PINNACLE snapshots, NOT iddaa verified.
Twenty curated aliases came from those snapshots; four further observed
spellings are user-iddaa PDF labels (Nov 20 and 22). Test all 24.
"""
import json,unittest
from pathlib import Path
from iddaa_pdf_team_alias_preflight_263 import (
 ROOT,LEAGUES,KNOWN_EXTERNAL_VARIANTS,KNOWN_IDDAA_PDF_VARIANTS,index_registry,
 resolve_label,normal,match_pdf_row,preflight_batch
)

class IdDaaPdfTeamNameSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index,cls.names,cls.members=index_registry()

    def test_whole_signed_registry_all_10_leagues_no_normalized_collisions(self):
        self.assertEqual(len(self.names),215)
        self.assertEqual(set(self.index),set(LEAGUES))
        self.assertEqual(sum(len(v) for v in KNOWN_EXTERNAL_VARIANTS.values()),20)
        for league in LEAGUES:
            self.assertTrue(self.members[league])
            self.assertGreaterEqual(len(self.index[league]),len(self.members[league]))
            self.assertTrue(set(self.index[league].values()).issubset(self.members[league]))

    def test_all_24_curated_labels_exact_same_canonical_identity_no_collision(self):
        registry=json.loads((ROOT/"experiments/263/evidence/identity_index_263.json")
                            .read_text(encoding="utf-8"))
        self.assertEqual(len(registry["teams"]),215)
        self.assertEqual(sum(map(len,KNOWN_EXTERNAL_VARIANTS.values())),20)
        self.assertEqual(sum(map(len,KNOWN_IDDAA_PDF_VARIANTS.values())),4)
        self.assertEqual(KNOWN_IDDAA_PDF_VARIANTS,{
            "ESP1":{"Athletic Bilbao":"Athletic Club",
                    "Espanyol":"RCD Espanyol de Barcelona",
                    "Racing Santander":"R. Racing Club"},
            "BEL1":{"Standard Liege":"Standard de Liège"}})
        total=0
        for origin,collection in (("NOV8_EXTERNAL_SPELLING",KNOWN_EXTERNAL_VARIANTS),
                                  ("NOV20_USER_IDDAA_PDF",KNOWN_IDDAA_PDF_VARIANTS)):
            for league,pairs in collection.items():
                self.assertIn(league,LEAGUES)
                encountered=set()
                for label,canonical in pairs.items():
                    with self.subTest(source=origin,league=league,label=label):
                        normalized=normal(label)
                        self.assertTrue(normalized)
                        self.assertNotIn(normalized,encountered)
                        encountered.add(normalized)
                        alias=resolve_label(league,label,self.index)
                        source=resolve_label(league,canonical,self.index)
                        self.assertEqual(alias["status"],"MAPPED")
                        self.assertEqual(source["status"],"MAPPED")
                        self.assertEqual(alias["team_id"],source["team_id"])
                        self.assertIn(alias["team_id"],self.members[league])
                        t=registry["teams"][alias["team_id"]]
                        self.assertEqual(t["verification"],"FEDERATION_VERIFIED")
                        self.assertTrue(t["official_name_evidence_url"].startswith("https://"))
                        total+=1
        self.assertEqual(total,24)

    def test_iddaa_athletic_and_espanyol_are_distinct_clubs_not_swapped(self):
        athletic=resolve_label("ESP1","Athletic Bilbao",self.index)["team_id"]
        espanyol=resolve_label("ESP1","Espanyol",self.index)["team_id"]
        self.assertNotEqual(athletic,espanyol)
        self.assertEqual(athletic,resolve_label("ESP1","Athletic Club",self.index)["team_id"])
        self.assertEqual(espanyol,resolve_label("ESP1","RCD Espanyol de Barcelona",self.index)["team_id"])

    def test_real_archived_86_external_names_resolve_even_if_old_20_failed(self):
        # Only actual in-repo November 8 The Odds API/Pinnacle labels, not
        # a fabricated claim that the Iddaa bulletin already uses them.
        leagues=["BEL1","ENG1","ESP1","FRA1","GER1","ITA1","NED1","POR1","TUR1"]
        count=0;failed=[]
        for league in leagues:
            source=ROOT/"experiments/263/pinnacle_daily_snapshots/2026-11-08"/(league+".json")
            report=json.loads(source.read_text(encoding="utf-8"))
            games=report["source_bulk"]["leagues"][league]
            for match in games:
                for label in (match["home_team"],match["away_team"]):
                    count+=1
                    result=resolve_label(league,label,self.index)
                    if result["status"]!="MAPPED":
                        failed.append((league,label))
        self.assertEqual(count,86)
        self.assertEqual(failed,[])

    def test_observed_confusable_variants_link_to_original_same_team_id(self):
        pairs=[
          ("TUR1","Beşiktaş","Besiktas JK"),
          ("TUR1","Gençlerbirliği","Genclerbirligi SK"),
          ("TUR1","Rizespor","Çaykur Rizespor"),
          ("ENG1","Brighton","Brighton and Hove Albion"),
          ("ITA1","Inter","Inter Milan"),
          ("ITA1","Milan","AC Milan"),
          ("GER1","Leverkusen","Bayer Leverkusen"),
          ("POR1","SC Braga","Braga"),
        ]
        for league,old,external in pairs:
            with self.subTest(external=external):
                a=resolve_label(league,old,self.index)
                b=resolve_label(league,external,self.index)
                self.assertEqual(a["status"],"MAPPED")
                self.assertEqual(b["status"],"MAPPED")
                self.assertEqual(a["team_id"],b["team_id"])

    def test_short_truncated_and_unknown_are_never_guessed(self):
        self.assertEqual(resolve_label("ENG1","Brighton ...",self.index)["status"],
                         "TRUNCATED_PDF_TEAM_NAME")
        self.assertEqual(resolve_label("ENG1","Brighton …",self.index)["status"],
                         "TRUNCATED_PDF_TEAM_NAME")
        self.assertEqual(resolve_label("ITA1","Inter Friendly Youth",self.index)["status"],
                         "UNMAPPED_NAME_SINGLE_MATCH_ONLY")
        self.assertEqual(resolve_label("NO_LEAGUE","Inter Milan",self.index)["status"],
                         "NOT_IN_TEN_LEAGUES")

    def test_pdf_and_already_verified_single_official_fixture_join_once(self):
        home=resolve_label("TUR1","Besiktas JK",self.index)["team_id"]
        away=resolve_label("TUR1","Genclerbirligi SK",self.index)["team_id"]
        sample={"league":"TUR1","local_date":"2026-11-22",
                "local_time":"20:00","home":"Besiktas JK","away":"Genclerbirligi SK"}
        official=[{"league":"TUR1","local_date":"2026-11-22",
                   "local_time":"20:00","home_id":home,"away_id":away}]
        result=match_pdf_row(sample,official,self.index)
        self.assertEqual(result["status"],"MATCHED_TO_ONE_OFFICIAL_FIXTURE")
        self.assertFalse(result["odds_source_requires_second_bookmaker"])

    def test_reversed_teams_wrong_clock_or_duplicate_official_fixture_fail(self):
        home=resolve_label("TUR1","Besiktas JK",self.index)["team_id"]
        away=resolve_label("TUR1","Genclerbirligi SK",self.index)["team_id"]
        sample={"league":"TUR1","local_date":"2026-11-22",
                "local_time":"20:00","home":"Besiktas JK","away":"Genclerbirligi SK"}
        official=[{"league":"TUR1","local_date":"2026-11-22",
                   "local_time":"20:00","home_id":away,"away_id":home}]
        self.assertNotEqual(match_pdf_row(sample,official,self.index)["status"],
                            "MATCHED_TO_ONE_OFFICIAL_FIXTURE")
        official[0]["home_id"]=home
        official[0]["away_id"]=away
        official[0]["local_time"]="21:00"
        self.assertNotEqual(match_pdf_row(sample,official,self.index)["status"],
                            "MATCHED_TO_ONE_OFFICIAL_FIXTURE")
        official[0]["local_time"]="20:00"
        official.append(dict(official[0]))
        self.assertNotEqual(match_pdf_row(sample,official,self.index)["status"],
                            "MATCHED_TO_ONE_OFFICIAL_FIXTURE")

    def test_bad_single_row_does_not_stop_other_good_matches(self):
        h=resolve_label("ITA1","Inter",self.index)["team_id"]
        a=resolve_label("ITA1","Milan",self.index)["team_id"]
        good={"league":"ITA1","local_date":"2026-11-22",
              "local_time":"19:00","home":"Inter Milan","away":"AC Milan"}
        bad={**good,"home":"Inter Milan…"}
        official=[{"league":"ITA1","local_date":"2026-11-22",
                   "local_time":"19:00","home_id":h,"away_id":a}]
        r=preflight_batch([good,bad],official,self.index)
        self.assertEqual(r["n_input"],2)
        self.assertEqual(r["n_matched"],1)
        self.assertEqual(r["n_single_row_review"],1)
        self.assertTrue(r["all_other_matched_rows_continue"])
        self.assertEqual(r["price_api_calls"],0)
        self.assertFalse(r["modifies_existing_forecasts"])

if __name__=="__main__":unittest.main()
