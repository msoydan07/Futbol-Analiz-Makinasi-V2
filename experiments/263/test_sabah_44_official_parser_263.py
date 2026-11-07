"""Regressions from real official HTML diagnostic, 7 Nov 2026; no networks."""
import unittest
from official_page_lookup_263 import parse_official_events,official_page_lookup
from datetime import datetime,timezone
def table(headers,rows):
    return '<table><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr>'+''.join(
        '<tr>'+''.join('<td>'+str(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</table>'
DFL=table(['Matchday','Day | Date','Kick-off (CET)','Kick-off (UTC)','Home Team','Away Team','Match Type','Features'],[
 ['9','Sat | 07-Nov-2026','15:30','14:30','Borussia Dortmund','SV Elversberg','Silver',''],
 ['9','Sat | 07-Nov-2026','15:30','14:30','RB Leipzig','FC Augsburg','Silver',''],
 ['9','Sat | 07-Nov-2026','15:30','14:30','1. FSV Mainz 05','FC Bayern München','Gold',''],
 ['9','Sat | 07-Nov-2026','15:30','14:30','SC Paderborn 07','Eintracht Frankfurt','Silver',''],
 ['9','Sat | 07-Nov-2026','18:30','17:30','VfB Stuttgart','SV Werder Bremen','Gold','']])
LALIGA='''<h3>Jornada 12 | 2026/2027</h3><table><tr><th>FECHA</th><th>HORARIO</th><th>PARTIDO</th><th>OPERADOR</th></tr>'''
for h,tm,home,away in [('14:00','Málaga CF','R. Racing Club','x'),('16:15','RCD Espanyol de Barcelona','RC Deportivo','x'),('18:30','CA Osasuna','Athletic Club','x'),('21:00','Valencia CF','Real Madrid','x')]:
    LALIGA+=f'<tr><td>SAB 07.11.2026</td><td>{h}</td><td><p>{tm}</p><p>VS</p><p>{home}</p></td><td>DAZN</td></tr>'
LALIGA+='</table>'
class Official44ParserTests(unittest.TestCase):
    def test_dfl_five_exact_with_utc(self):
        x=parse_official_events("GER1",DFL)
        self.assertEqual(len(x),5)
        self.assertEqual(x[0]["home"],"Borussia Dortmund")
        self.assertEqual(x[0]["kickoff_utc"],"2026-11-07T14:30:00+00:00")
        self.assertEqual(x[-1]["kickoff_utc"],"2026-11-07T17:30:00+00:00")
    def test_dfl_without_header_cannot_fake_rows(self):
        self.assertEqual(parse_official_events("GER1",DFL.replace("Kick-off (UTC)","Time")),[])
    def test_laliga_four_full_dates(self):
        x=parse_official_events("ESP1",LALIGA)
        self.assertEqual(len(x),4)
        self.assertEqual(x[0]["kickoff_utc"],"2026-11-07T13:00:00+00:00")
        self.assertEqual(x[2]["kickoff_utc"],"2026-11-07T17:30:00+00:00")
        self.assertEqual(x[-1]["kickoff_utc"],"2026-11-07T20:00:00+00:00")
    def test_laliga_without_2026_27_header_fails_closed(self):
        self.assertEqual(parse_official_events("ESP1",LALIGA.replace("2026/2027","2025/2026")),[])
    def test_canonical_pair_order_required(self):
        m=official_page_lookup("ESP1","CA Osasuna","Athletic Club",
                source_url="https://www.laliga.com/iframes/external-consumer-broadcast",html=LALIGA,
                now=datetime(2026,11,7,9,0,tzinfo=timezone.utc),
                same_team=lambda a,b:a==b)
        self.assertEqual(m["status"],"VERIFIED_OFFICIAL_FIXTURE")
        wrong=official_page_lookup("ESP1","Athletic Club","CA Osasuna",
                source_url="https://www.laliga.com/iframes/external-consumer-broadcast",html=LALIGA,
                now=datetime(2026,11,7,9,0,tzinfo=timezone.utc),
                same_team=lambda a,b:a==b)
        self.assertNotEqual(wrong["status"],"VERIFIED_OFFICIAL_FIXTURE")
if __name__=="__main__":unittest.main()
