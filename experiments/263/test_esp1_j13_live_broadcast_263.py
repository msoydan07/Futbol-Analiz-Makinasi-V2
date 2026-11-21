"""Live LaLiga 21-Nov J13 explicit fixture acceptance; no odds or forecasts."""
import unittest
from datetime import datetime,timezone
from official_page_lookup_263 import parse_official_events

def html(rows,round_="Jornada 13 | 2026/2027"):
    a=['<h1>'+round_+'</h1>']
    for date,clock,home,away in rows:
        for token in (date,clock,home,"VS",away):
            a.append('<div>'+token+'</div>')
    return ''.join(a)

SAMPLES=[
("SAB 21.11.2026","14:00","Deportivo Alavés","RC Deportivo"),
("SAB 21.11.2026","16:15","Rayo Vallecano","Valencia CF"),
("SAB 21.11.2026","18:30","Sevilla FC","Real Betis"),
("SAB 21.11.2026","21:00","Real Madrid","Celta")]

class LaLigaJ13(unittest.TestCase):
    def test_explicit_official_grid_preserves_four_fixtures_and_utc(self):
        o=parse_official_events("ESP1",html(SAMPLES),
                                 parser="laliga_broadcast_j13_nov2026")
        got={(x["home"],x["away"],x["kickoff_utc"]) for x in o}
        expected={
        ("Deportivo Alavés","RC Deportivo","2026-11-21T13:00:00+00:00"),
        ("Rayo Vallecano","Valencia CF","2026-11-21T15:15:00+00:00"),
        ("Sevilla FC","Real Betis","2026-11-21T17:30:00+00:00"),
        ("Real Madrid","Celta","2026-11-21T20:00:00+00:00")}
        self.assertEqual(got,expected)
    def test_wrong_round_or_time_does_not_promote_guess(self):
        self.assertEqual(parse_official_events("ESP1",html(SAMPLES,round_="Jornada 12 | 2026/2027"),parser="laliga_broadcast_j13_nov2026"),[])
        broken=[("SAB 21.11.2026","--:--","Deportivo Alavés","RC Deportivo")]
        self.assertEqual(parse_official_events("ESP1",html(broken),parser="laliga_broadcast_j13_nov2026"),[])
    def test_reversed_fixture_must_not_match(self):
        from official_page_lookup_263 import official_page_lookup,SOURCES
        now=datetime(2026,11,21,8,5,tzinfo=timezone.utc)
        actual=html(SAMPLES)
        yes=official_page_lookup("ESP1","Deportivo Alavés","RC Deportivo",
            now=now,html=actual,source_url=SOURCES["ESP1"][0],
            parser="laliga_broadcast_j13_nov2026",
            same_team=lambda x,y:x==y)
        self.assertEqual(yes["status"],"VERIFIED_OFFICIAL_FIXTURE")
        no=official_page_lookup("ESP1","RC Deportivo","Deportivo Alavés",
            now=now,html=actual,source_url=SOURCES["ESP1"][0],
            parser="laliga_broadcast_j13_nov2026",
            same_team=lambda x,y:x==y)
        self.assertNotEqual(no["status"],"VERIFIED_OFFICIAL_FIXTURE")
if __name__=="__main__":unittest.main()
