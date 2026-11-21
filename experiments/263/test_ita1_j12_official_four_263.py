"""Exact official 21-Nov Serie A J12 parser acceptance, no forecasts."""
import unittest
from datetime import datetime,timezone
from official_page_lookup_263 import SOURCES,parse_official_events,official_page_lookup
TITLE="Quando si gioca? Anticipi e posticipi fino alla 12ª giornata"
PARA=("Dopo la sosta di metà novembre si torna in campo sabato 21 con la 12ª giornata: "
      "alle 15.00 giocano Como-Cagliari e Lazio-Lecce, alle 18.00 Parma-Roma "
      "e alle 20.45 Napoli-Torino. Domenica apre il programma Sassuolo-Genoa.")
def markup(body=PARA,title=TITLE):
    return "<h1>"+title+"</h1><p>"+body+"</p>"

class ExactJ12(unittest.TestCase):
    def test_four_named_official_slots_and_utc(self):
        events=parse_official_events("ITA1",markup(),parser="seriea_j12_2026_confirmed")
        self.assertEqual({(x["home"],x["away"],x["kickoff_utc"]) for x in events},{
            ("Como","Cagliari","2026-11-21T14:00:00+00:00"),
            ("Lazio","Lecce","2026-11-21T14:00:00+00:00"),
            ("Parma","Roma","2026-11-21T17:00:00+00:00"),
            ("Napoli","Torino","2026-11-21T19:45:00+00:00")})
    def test_no_old_round_or_partial_source(self):
        self.assertEqual(parse_official_events("ITA1",markup(title="Calendario 11ª giornata"),
            parser="seriea_j12_2026_confirmed"),[])
        self.assertEqual(parse_official_events("ITA1",
            markup(body=PARA.replace("Napoli-Torino","Napoli-Lazio")),
            parser="seriea_j12_2026_confirmed"),[])
    def test_strict_names_and_order(self):
        now=datetime(2026,11,21,9,tzinfo=timezone.utc)
        args=dict(now=now,html=markup(),source_url=SOURCES["ITA1"][0],
                 parser="seriea_j12_2026_confirmed",
                 same_team=lambda a,b:a==b)
        yes=official_page_lookup("ITA1","Como","Cagliari",**args)
        self.assertEqual(yes["status"],"VERIFIED_OFFICIAL_FIXTURE")
        no=official_page_lookup("ITA1","Cagliari","Como",**args)
        self.assertNotEqual(no["status"],"VERIFIED_OFFICIAL_FIXTURE")
if __name__=="__main__":unittest.main()
