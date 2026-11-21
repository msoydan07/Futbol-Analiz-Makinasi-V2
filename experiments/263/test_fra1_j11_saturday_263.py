"""Official Ligue 1 J11 Saturday schedule exact named/time acceptance."""
import unittest
from datetime import datetime,timezone
from official_page_lookup_263 import parse_official_events,official_page_lookup,SOURCES

NAMES=[
("OGC Nice","Paris Saint-Germain","17h15"),
("LOSC","Olympique Lyonnais","20h45"),
("RC Lens","Toulouse FC","20h45"),
("AS Monaco","AJ Auxerre","20h45"),
("RC Strasbourg Alsace","Stade Brestois 29","20h45")]

def article(*,corrupt=False):
    s="<h1>Programmations TV : J10 et J11</h1><h2>11e JOURNÉE DE LIGUE 1 McDONALD’S</h2>"
    s+="<p>Vendredi 20 novembre 2026 à 20h45 sur Ligue 1+</p><p>ESTAC Troyes – Havre AC</p>"
    s+="<p>Samedi 21 novembre 2026 à 17h15 sur Ligue 1+</p><p>OGC Nice – Paris Saint-Germain</p>"
    s+="<p>Samedi 21 novembre 2026 à 20h45 sur Ligue 1+</p>"
    for h,a,kick in NAMES[1:]:
        if corrupt and h=="LOSC":continue
        s+=f"<p>{h} – {a}</p>"
    s+="<p>Dimanche 22 novembre 2026 à 15h00 sur Ligue 1+</p><p>Paris FC – Angers SCO</p>"
    return s

class OfficialJ11(unittest.TestCase):
    def test_five_saturday_matches_true_utc(self):
        rows=parse_official_events("FRA1",article(),
                parser="lfp_j11_sat_nov2026_verified")
        got={(v['home'],v['away'],v['kickoff_utc']) for v in rows}
        target={(h,a, "2026-11-21T16:15:00+00:00" if t=="17h15" else
                          "2026-11-21T19:45:00+00:00")
               for h,a,t in NAMES}
        self.assertEqual(got,target)
        self.assertNotIn(("Paris FC","Angers SCO","2026-11-22T14:00:00+00:00"),got)
    def test_missing_fixture_not_added(self):
        rows=parse_official_events("FRA1",article(corrupt=True),
                parser="lfp_j11_sat_nov2026_verified")
        self.assertEqual(len(rows),4)
    def test_wrong_round_or_missing_explicit_kickoff_refused(self):
        t=article().replace("11e JOURNÉE DE LIGUE 1","12e JOURNÉE DE LIGUE 1")
        self.assertFalse(parse_official_events("FRA1",t,
                   parser="lfp_j11_sat_nov2026_verified"))
        t=article().replace("Samedi 21 novembre 2026 à 17h15",
                            "Samedi 21 novembre 2026")
        self.assertEqual(len(parse_official_events("FRA1",t,
                   parser="lfp_j11_sat_nov2026_verified")),4)
    def test_reversed_match_not_accepted(self):
        args=dict(now=datetime(2026,11,21,9,tzinfo=timezone.utc),
                html=article(),source_url=SOURCES['FRA1'][0],
                parser="lfp_j11_sat_nov2026_verified",
                same_team=lambda x,y:x==y)
        yes=official_page_lookup("FRA1","OGC Nice","Paris Saint-Germain",**args)
        self.assertEqual(yes['status'],"VERIFIED_OFFICIAL_FIXTURE")
        bad=official_page_lookup("FRA1","Paris Saint-Germain","OGC Nice",**args)
        self.assertNotEqual(bad['status'],"VERIFIED_OFFICIAL_FIXTURE")

if __name__=="__main__":unittest.main()
